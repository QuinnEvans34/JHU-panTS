"""Bounded voxel audit of explicit CT/mask NIfTI files. Measurement, never eligibility.

Answers what a header or a file size cannot: how many voxels are finite, what values a mask
actually stores, whether it is empty, and whether a CT/mask pair shares one voxel grid. Builds
on the read-only evidence adapter in src/data/source_evidence.py for hashing, safe path
resolution and header geometry, and reuses its approved paired-explicit-mm-CT unit rule
unchanged.

Boundaries, all deliberate:
  * explicit (root alias, relative URI) inputs only; no discovery, recursion or default roots;
  * voxel payloads are streamed in bounded chunks from the same file descriptor whose identity
    matches the hashed file; nibabel's ArrayProxy is never used to load voxel data;
  * no resampling, reorientation, casting to integer types or threshold-based relabelling;
  * a measurement is not an exclusion, a label mapping, a diagnosis or an eligibility result.

Design: docs/capstone/data/VOXEL-AUDIT-DESIGN.md. Run with --demo for a fixture-only example.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import gzip
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import zlib

import nibabel as nib
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.data.source_evidence import identity, infer_mask_mm, measure_nifti, resolve_file  # noqa: E402

AUDIT_VERSION = 'voxel-audit-v1.1'

# Tolerances are absolute and chosen to match the existing evidence adapter, so the audit can
# never accept a pairing that infer_mask_mm would refuse.
PAIR_ATOL = 1e-5        # shape/spacing/affine agreement between paired files (infer_mask_mm)
TRANSFORM_ATOL = 1e-4   # coded qform/sform agreement within one file (infer_mask_mm)

# Working-memory accounting, in bytes per voxel held in one chunk beyond the stored bytes
# themselves. Measured with tracemalloc on adversarial synthetic inputs (every value distinct,
# float64, scaled, with and without non-finite values) and rounded up; the tests re-measure.
#   CT:   a float64 scaled copy, finite flags and a finite-only copy for min/max.
#   mask: the above plus np.unique's flatten/sort copy, flags, index and count arrays.
#   pair: the gathered within-mask CT values and selection flags.
CT_WORKING_BYTES_PER_VOXEL = 32
MASK_WORKING_BYTES_PER_VOXEL = 64
PAIR_WORKING_BYTES_PER_VOXEL = 16
NIFTI1_HEADER_BYTES = 348
MIN_VOX_OFFSET = 352
TRAILING_CAP = 16 * 1024**2

# Header problems that make a file's grid ambiguous. A pair containing one is never compared
# voxel-for-voxel, because there is no trustworthy statement of where its voxels are.
AMBIGUOUS_GRID = {'qform_sform_disagreement', 'invalid_geometry', 'unsupported_image_dimensions',
                  'uncoded_spatial_transform', 'affine_spacing_disagreement'}


class AuditStop(Exception):
    """A preserved, coded reason the audit could not produce a measurement."""

    def __init__(self, code, detail):
        super().__init__(f'{code}: {detail}')
        self.code, self.detail = code, detail


@dataclass(frozen=True)
class Limits:
    """Checked against the declared header before any voxel byte is read."""
    max_voxels: int = 1_000_000_000
    max_axis: int = 4096
    working_bytes: int = 256 * 1024**2
    max_distinct: int = 1024
    max_listed: int = 64


# --- header -------------------------------------------------------------------------------------

def _scaling(header):
    """Independent statement of NIfTI-1 scaling, stricter than nibabel.

    scl_slope of 0 or NaN means unscaled (NIfTI-1 and nibabel agree). A finite nonzero slope with
    a finite intercept scales. Anything else stops: nibabel raises for a non-finite intercept but
    silently treats an infinite slope as unscaled, which would misreport every value in the file.
    """
    slope, inter = float(header['scl_slope']), float(header['scl_inter'])
    if slope == 0.0 or math.isnan(slope):
        return dict(active=False, slope=None, inter=None, header_slope_finite=not math.isnan(slope))
    if math.isfinite(slope) and math.isfinite(inter):
        return dict(active=not (slope == 1.0 and inter == 0.0), slope=slope, inter=inter,
                    header_slope_finite=True)
    raise AuditStop('invalid_scaling', 'non-finite scl_slope or scl_inter with a nonzero slope')


def _parse_header(stream, limits):
    try:
        header = nib.Nifti1Header.from_fileobj(stream, check=False)
    except Exception as exc:  # nibabel raises several types for malformed headers
        raise AuditStop('malformed_header', type(exc).__name__) from None
    if int(header['sizeof_hdr']) != NIFTI1_HEADER_BYTES or bytes(header['magic']) != b'n+1\x00':
        raise AuditStop('unsupported_format', 'single-file NIfTI-1 (n+1) only')
    dim = [int(v) for v in header['dim']]
    if not 1 <= dim[0] <= 7:
        raise AuditStop('malformed_header', f'dim[0]={dim[0]}')
    shape = tuple(dim[1:1 + dim[0]])
    if len(shape) != 3:
        raise AuditStop('unsupported_dimensions', f'{len(shape)}D image; 3D only')
    if any(n <= 0 for n in shape):
        raise AuditStop('malformed_header', 'non-positive dimension')
    try:
        dtype = header.get_data_dtype()
    except Exception as exc:
        raise AuditStop('unsupported_datatype', type(exc).__name__) from None
    if dtype.fields or dtype.kind not in 'iuf' or dtype.itemsize > 8:
        raise AuditStop('unsupported_datatype', f'{dtype.str}; real integer or float up to 64-bit only')
    offset = float(header['vox_offset'])
    if not math.isfinite(offset) or offset != int(offset) or offset < MIN_VOX_OFFSET:
        raise AuditStop('malformed_header', f'vox_offset={offset}')
    voxels = shape[0] * shape[1] * shape[2]  # Python ints: no overflow
    if max(shape) > limits.max_axis or voxels > limits.max_voxels:
        raise AuditStop('limit_exceeded', f'declared shape {list(shape)} exceeds configured limits')
    return dict(format='nifti1', shape=list(shape), stored_dtype=dtype.str, itemsize=dtype.itemsize,
                vox_offset=int(offset), voxels=voxels, scaling=_scaling(header)), dtype


# --- streaming ----------------------------------------------------------------------------------

def _open_payload(path):
    """Open without following symlinks. Test seam: tests wrap the stream to observe reads."""
    raw = os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb')
    stream = gzip.GzipFile(fileobj=raw, mode='rb') if path.name.endswith('.gz') else raw
    return raw, stream


class _Reader:
    """Reads one file's voxel payload in fixed chunks from the hashed file's descriptor."""

    def __init__(self, path, before, limits):
        self.path, self.before, self.limits = path, before, limits
        self.raw, self.stream = _open_payload(path)
        try:
            if identity(os.fstat(self.raw.fileno())) != before:
                raise AuditStop('file_mutated', 'opened file differs from the hashed file')
            self.header, self.dtype = _parse_header(self.stream, limits)
            self.compressed = path.name.endswith('.gz')  # the same rule _open_payload applies
            end = self.header['vox_offset'] + self.header['voxels'] * self.dtype.itemsize
            if not self.compressed:
                size = before[2]
                if size < end:
                    raise AuditStop('payload_truncated',
                                    f'file holds {size} bytes; header requires {end}')
                self.trailing = size - end
            else:
                self.trailing = None
            self._guard(lambda: self.stream.seek(self.header['vox_offset']))
            self.remaining = self.header['voxels']
            self.buffer = None
        except BaseException:
            self.close()
            raise

    def _guard(self, action):
        try:
            return action()
        except (EOFError, gzip.BadGzipFile, zlib.error) as exc:
            raise AuditStop('corrupt_payload', type(exc).__name__) from None
        except OSError as exc:
            raise AuditStop('io_error', exc.strerror or type(exc).__name__) from None

    def read(self, count):
        """Return the next `count` stored values as a view into a reused buffer."""
        width = count * self.dtype.itemsize
        if self.buffer is None or len(self.buffer) < width:
            self.buffer = bytearray(width)
        view, got = memoryview(self.buffer)[:width], 0
        while got < width:
            step = self._guard(lambda: self.stream.readinto(view[got:]))
            if not step:
                raise AuditStop('payload_truncated',
                                f'stream ended {width - got} bytes before the declared payload')
            got += step
        self.remaining -= count
        return np.frombuffer(self.buffer, dtype=self.dtype, count=count)

    def finish(self, check_root):
        """Drain to EOF so gzip verifies its CRC and length, then confirm the file is unchanged."""
        if self.compressed:
            extra = 0
            while chunk := self._guard(lambda: self.stream.read(1024 * 1024)):
                extra += len(chunk)
                if extra > TRAILING_CAP:
                    raise AuditStop('excess_trailing_payload', f'more than {TRAILING_CAP} bytes')
            self.trailing = extra
        if (identity(os.fstat(self.raw.fileno())) != self.before
                or identity(self.path.lstat()) != self.before):
            raise AuditStop('file_mutated', 'file changed while its voxels were read')
        try:
            check_root()
        except Exception as exc:  # caller-supplied; e.g. mounted() raises RuntimeError
            raise AuditStop('root_check_failed', type(exc).__name__) from None

    def close(self):
        for handle in (getattr(self, 'stream', None), getattr(self, 'raw', None)):
            if handle is not None:
                handle.close()


# --- accumulation -------------------------------------------------------------------------------

def _python(value):
    return int(value) if isinstance(value, (np.integer, int)) else float(value)


class _Values:
    """Counts every voxel exactly once: finite, NaN, +Inf or -Inf. Never silently drops one."""

    def __init__(self, dtype, scaling):
        self.dtype, self.scaling = dtype, scaling
        self.count = self.finite = self.nan = self.posinf = self.neginf = 0
        self.scaled_overflow = 0
        self.stored_min = self.stored_max = self.min = self.max = None
        self.stored_nonfinite = 0

    def semantic(self, stored):
        """Values a consumer reads. Promotion to float64 is explicit; nothing is cast to int."""
        if not self.scaling['active']:
            return stored
        values = stored.astype(np.float64)
        with np.errstate(over='ignore', invalid='ignore'):
            values *= self.scaling['slope']
            values += self.scaling['inter']
        return values

    @staticmethod
    def _extend(low, high, values):
        if values.size == 0:
            return low, high
        lo, hi = _python(values.min()), _python(values.max())
        return (lo if low is None else min(low, lo)), (hi if high is None else max(high, hi))

    @staticmethod
    def _finite_only(values, finite, n_finite):
        return values if n_finite == values.size else values[finite]

    def update(self, stored):
        self.count += stored.size
        if stored.dtype.kind == 'f':
            stored_finite = np.isfinite(stored)
            n_stored = int(np.count_nonzero(stored_finite))
            self.stored_nonfinite += stored.size - n_stored
            self.stored_min, self.stored_max = self._extend(
                self.stored_min, self.stored_max, self._finite_only(stored, stored_finite, n_stored))
        else:
            stored_finite = None
            self.stored_min, self.stored_max = self._extend(self.stored_min, self.stored_max, stored)
        values = self.semantic(stored)
        if values.dtype.kind != 'f':
            self.finite += values.size
            self.min, self.max = self.stored_min, self.stored_max
            return values, None
        finite = np.isfinite(values)
        n_finite = int(np.count_nonzero(finite))
        self.finite += n_finite
        if n_finite != values.size:
            bad = values[~finite]
            self.nan += int(np.count_nonzero(np.isnan(bad)))
            self.posinf += int(np.count_nonzero(bad == np.inf))
            self.neginf += int(np.count_nonzero(bad == -np.inf))
            if stored_finite is None:
                self.scaled_overflow += int(values.size - n_finite)
            else:
                self.scaled_overflow += int(np.count_nonzero(stored_finite & ~finite))
        self.min, self.max = self._extend(self.min, self.max,
                                          self._finite_only(values, finite, n_finite))
        return values, (None if n_finite == values.size else finite)

    def record(self):
        nonfinite = self.nan + self.posinf + self.neginf
        assert self.finite + nonfinite == self.count, 'voxel accounting must be exhaustive'
        wide = self.dtype.kind in 'iu' and self.dtype.itemsize == 8
        precision_risk = wide and self.scaling['active'] and any(
            v is not None and abs(v) > 2**53 for v in (self.stored_min, self.stored_max))
        return dict(count=self.count, finite=self.finite,
                    nonfinite=dict(nan=self.nan, posinf=self.posinf, neginf=self.neginf),
                    stored_min=self.stored_min, stored_max=self.stored_max,
                    stored_nonfinite=self.stored_nonfinite, min=self.min, max=self.max,
                    values_basis='scaled' if self.scaling['active'] else 'stored',
                    scaled_overflow_voxels=self.scaled_overflow,
                    float64_precision_loss_risk=bool(precision_risk))


class _Mask:
    """Label-value accounting on the semantic values. Expected values are caller policy."""

    def __init__(self, expected, limits):
        self.limits = limits
        self.expected = None if expected is None else np.asarray(sorted(expected), dtype=np.float64)
        self.nonzero = self.negative = self.nonintegral = 0
        self.counts, self.truncated = {}, False
        self.unexpected_voxels = None if expected is None else 0
        self.unexpected, self.unexpected_truncated = set(), False

    def update(self, values, finite):
        """finite is None when every value in the chunk is finite (see _Values.update)."""
        x = values if finite is None else values[finite]
        if x.size == 0:
            return
        # Every statistic is derived from the sorted distinct values, so no further full-size
        # temporaries exist beyond np.unique's own working arrays.
        vals, cnts = np.unique(x, return_counts=True)
        del x
        self.nonzero += int(cnts[vals != 0].sum())
        self.negative += int(cnts[vals < 0].sum())
        if vals.dtype.kind == 'f':
            self.nonintegral += int(cnts[vals != np.floor(vals)].sum())
        if self.expected is not None:
            bad = ~np.isin(np.asarray(vals, dtype=np.float64), self.expected)
            self.unexpected_voxels += int(cnts[bad].sum())
            candidates = vals[bad]
            if self.unexpected:
                candidates = candidates[~np.isin(candidates, list(self.unexpected))]
            room = self.limits.max_listed - len(self.unexpected)
            if candidates.size > room:
                self.unexpected_truncated = True
            self.unexpected.update(candidates[:room].tolist())
        # vals is sorted, so the (at most max_distinct) known values are located by binary
        # search instead of a full-size set-membership pass.
        seen = np.zeros(vals.size, dtype=bool)
        if self.counts:
            known = np.fromiter(self.counts, dtype=vals.dtype, count=len(self.counts))
            where = np.searchsorted(vals, known)
            hit = where < vals.size
            hit[hit] = vals[where[hit]] == known[hit]
            for index in where[hit].tolist():
                seen[index] = True
                self.counts[vals[index].item()] += int(cnts[index])
        room = self.limits.max_distinct - len(self.counts)
        for index in range(vals.size):
            if room == 0:
                if not seen[index:].all():
                    self.truncated = True
                break
            if not seen[index]:
                self.counts[vals[index].item()] = int(cnts[index])
                room -= 1

    def record(self, values_record, volume):
        nonfinite = sum(values_record['nonfinite'].values())
        return dict(nonzero_voxels=self.nonzero,
                    empty=(self.nonzero == 0) if nonfinite == 0 else None,
                    negative_voxels=self.negative, nonintegral_voxels=self.nonintegral,
                    distinct_values=sorted(self.counts), distinct_values_truncated=self.truncated,
                    value_counts=[[v, self.counts[v]] for v in sorted(self.counts)],
                    expected_values=None if self.expected is None else
                    [_python(v) for v in self.expected.tolist()],
                    unexpected_value_voxels=self.unexpected_voxels,
                    unexpected_values=None if self.expected is None else sorted(self.unexpected),
                    unexpected_values_truncated=self.unexpected_truncated,
                    volume=volume)


class _WithinMask:
    """CT values at the mask's nonzero voxels. Only ever run on a verified shared grid."""

    def __init__(self):
        self.voxels = self.finite = self.nonfinite = 0
        self.min = self.max = None
        self.partials = []

    def update(self, ct_values, mask_values, mask_finite):
        selected = mask_values != 0 if mask_finite is None else (mask_finite & (mask_values != 0))
        gathered = ct_values[selected]
        self.voxels += gathered.size
        if gathered.dtype.kind == 'f':
            ok = np.isfinite(gathered)
            self.nonfinite += int(gathered.size - np.count_nonzero(ok))
            gathered = gathered[ok]
        self.finite += gathered.size
        if gathered.size:
            self.min = _python(gathered.min()) if self.min is None else min(self.min, _python(gathered.min()))
            self.max = _python(gathered.max()) if self.max is None else max(self.max, _python(gathered.max()))
            self.partials.append(float(gathered.sum(dtype=np.float64)))

    def record(self):
        mean = math.fsum(self.partials) / self.finite if self.finite else None
        return dict(mask_nonzero_voxels=self.voxels, ct_finite=self.finite,
                    ct_nonfinite=self.nonfinite, ct_min=self.min, ct_max=self.max, ct_mean=mean,
                    note='Descriptive only. No threshold, alignment verdict or diagnosis is derived.')


# --- geometry -----------------------------------------------------------------------------------

def _native_transform_issues(evidence):
    """Coded-transform agreement on native values for unknown-unit files only.

    header_geometry returns early for unknown units, so it never checks qform/sform agreement
    on exactly the files that most need it. This applies infer_mask_mm's own test (rtol=0,
    atol=1e-4 on native values) and nothing else; files with known units keep the adapter's
    verdict unchanged.
    """
    issues = set()
    if 'unknown_spatial_units' not in evidence['issue_codes']:
        return issues
    raw = evidence['raw_header']
    affine = np.asarray(raw['affine_native'], dtype=float)
    if not raw['qform_code'] and not raw['sform_code']:
        issues.add('uncoded_spatial_transform')
    for prefix in ('qform', 'sform'):
        if raw[prefix + '_code']:
            transform = np.asarray(raw[prefix + '_native'], dtype=float)
            if (transform.shape != (4, 4) or not np.isfinite(transform).all()
                    or not np.allclose(transform, affine, rtol=0, atol=TRANSFORM_ATOL)):
                issues.add('qform_sform_disagreement')
    return issues


def _affine_source(raw):
    return 'sform' if raw['sform_code'] else 'qform' if raw['qform_code'] else 'fallback_zooms'


def _grid(ct, mask):
    """Compare two evidence records' grids. Never resamples, reorients or reshapes."""
    ct_raw, mask_raw = ct['raw_header'], mask['raw_header']
    blocking = sorted((set(ct['issue_codes']) | _native_transform_issues(ct)) & AMBIGUOUS_GRID)
    blocking_mask = sorted((set(mask['issue_codes']) | _native_transform_issues(mask)) & AMBIGUOUS_GRID)
    both_mm = ct['geometry'] is not None and mask['geometry'] is not None
    if both_mm:
        basis = 'mm'
        a = np.asarray(ct['geometry']['affine_ras'], dtype=float)
        b = np.asarray(mask['geometry']['affine_ras'], dtype=float)
        sa = np.asarray(ct['geometry']['spacing_mm_xyz'], dtype=float)
        sb = np.asarray(mask['geometry']['spacing_mm_xyz'], dtype=float)
    else:
        basis = 'native'
        a = np.asarray(ct_raw['affine_native'], dtype=float).ravel()
        b = np.asarray(mask_raw['affine_native'], dtype=float).ravel()
        sa = np.asarray(ct_raw['spacing_native'][:3], dtype=float)
        sb = np.asarray(mask_raw['spacing_native'][:3], dtype=float)
    shape_equal = ct_raw['shape'] == mask_raw['shape']
    comparable = a.shape == b.shape and np.isfinite(a).all() and np.isfinite(b).all()
    affine_diff = float(np.max(np.abs(a - b))) if comparable else None
    spacing_diff = (float(np.max(np.abs(sa - sb)))
                    if sa.shape == sb.shape and np.isfinite(sa).all() and np.isfinite(sb).all() else None)
    issues = []
    if not shape_equal:
        issues.append(dict(code='shape_mismatch', severity='blocking',
                           detail=f"{ct_raw['shape']} vs {mask_raw['shape']}"))
    if affine_diff is None or affine_diff > PAIR_ATOL:
        issues.append(dict(code='affine_mismatch', severity='blocking',
                           detail=f'max |difference| {affine_diff} exceeds {PAIR_ATOL} ({basis})'))
    if spacing_diff is None or spacing_diff > PAIR_ATOL:
        issues.append(dict(code='spacing_mismatch', severity='blocking',
                           detail=f'max |difference| {spacing_diff} exceeds {PAIR_ATOL} ({basis})'))
    for role, codes in (('ct', blocking), ('mask', blocking_mask)):
        for code in codes:
            issues.append(dict(code=f'{role}_{code}', severity='blocking',
                               detail='grid is ambiguous, so voxel correspondence cannot be verified'))
    return dict(compatible=not issues, basis=basis, shape_equal=shape_equal,
                max_abs_affine_difference=affine_diff, max_abs_spacing_difference=spacing_diff,
                tolerance=PAIR_ATOL, units=[ct_raw['spatial_units'], mask_raw['spatial_units']],
                affine_sources=[_affine_source(ct_raw), _affine_source(mask_raw)], issues=issues)


def _volume(nonzero, nonfinite, geometry, basis, reason):
    if geometry is None:
        return dict(available=False, mm3=None, voxel_mm3=None, basis=None, reason=reason)
    matrix = np.asarray(geometry['affine_ras'], dtype=float).reshape(4, 4)[:3, :3]
    voxel = float(abs(np.linalg.det(matrix)))
    if nonfinite:
        return dict(available=False, mm3=None, voxel_mm3=voxel, basis=basis,
                    reason='nonfinite_mask_values: occupancy is ambiguous')
    return dict(available=True, mm3=nonzero * voxel, voxel_mm3=voxel, basis=basis, reason=None)


# --- orchestration ------------------------------------------------------------------------------

def _chunk_voxels(targets, limits):
    """Largest chunk whose estimated working set fits limits.working_bytes."""
    per = sum(t.reader.dtype.itemsize + (MASK_WORKING_BYTES_PER_VOXEL if t.role == 'mask'
                                          else CT_WORKING_BYTES_PER_VOXEL) for t in targets)
    per += PAIR_WORKING_BYTES_PER_VOXEL if len(targets) == 2 else 0
    chunk = limits.working_bytes // per
    if chunk < 1:
        raise AuditStop('limit_exceeded', f'working budget {limits.working_bytes} B is below one voxel')
    return chunk


def _evidence(roots, alias, uri, check_root):
    """Hash and header via the shared adapter, pinned to one file identity."""
    try:
        check_root()
        path = resolve_file(roots, alias, uri)
        before = identity(path.lstat())
        evidence = measure_nifti(roots, alias, uri, check_root)
        if identity(path.lstat()) != before:
            raise AuditStop('file_mutated', 'file changed while it was hashed')
    except AuditStop:
        raise
    except ValueError as exc:  # the adapter's messages are fixed strings without paths
        raise AuditStop('evidence_refused', str(exc)) from None
    except (EOFError, gzip.BadGzipFile, zlib.error) as exc:
        raise AuditStop('corrupt_payload', type(exc).__name__) from None
    except OSError as exc:
        raise AuditStop('unavailable_prerequisite', exc.strerror or type(exc).__name__) from None
    except Exception as exc:  # nibabel header errors (e.g. HeaderDataError) during nib.load
        raise AuditStop('evidence_refused', type(exc).__name__) from None
    return path, before, evidence


def _base(role, alias, uri, evidence=None):
    raw = None if evidence is None else evidence['raw_header']
    # Stopped and measured records share one key set; measurements stay None until complete.
    record = dict(header=None, scaling=None, voxels=None, issues=[], trailing_payload_bytes=None,
                  limits=None, **({'mask': None} if role == 'mask' else {}))
    return dict(record, audit_version=AUDIT_VERSION, role=role, status='measured', stop=None,
                file=evidence['file'] if evidence else dict(root_alias=alias, uri=uri),
                geometry=None if evidence is None else evidence['geometry'],
                header_issues=[] if evidence is None else sorted(
                    set(evidence['issue_codes']) | _native_transform_issues(evidence)),
                affine_source=None if raw is None else _affine_source(raw),
                spatial_units=None if raw is None else raw['spatial_units'],
                eligibility='not_assessed')


def _stopped(record, stop):
    record.update(status='stopped', stop=dict(code=stop.code, detail=stop.detail))
    return record


class _Target:
    def __init__(self, role, roots, alias, uri, expected, limits, check_root):
        if role not in ('ct', 'mask'):
            raise ValueError('role must be "ct" or "mask"')
        if role == 'ct' and expected is not None:
            raise ValueError('CT intensities are not label classes; expected_values is mask-only')
        if expected is not None:
            expected = [float(v) for v in expected]
            if not all(math.isfinite(v) for v in expected):
                raise ValueError('expected_values must be finite numbers')
        self.role, self.expected, self.limits, self.check_root = role, expected, limits, check_root
        self.record = _base(role, alias, uri)
        self.reader = self.values = self.mask = None
        try:
            self.path, self.before, self.evidence = _evidence(roots, alias, uri, check_root)
            self.record = _base(role, alias, uri, self.evidence)
            self.reader = _Reader(self.path, self.before, limits)
        except AuditStop as stop:
            self.evidence = getattr(self, 'evidence', None)
            _stopped(self.record, stop)
            return
        self.values = _Values(self.reader.dtype, self.reader.header['scaling'])
        self.mask = _Mask(expected, limits) if role == 'mask' else None

    @property
    def ok(self):
        return self.record['status'] == 'measured'

    def consume(self, stored):
        values, finite = self.values.update(stored)
        if self.mask is not None:
            self.mask.update(values, finite)
        return values, finite

    def finish(self, chunk, volume_context=None):
        """volume_context=(geometry, basis, reason) from a pair; None means use this file's header."""
        if not self.ok:
            return self.record
        try:
            self.reader.finish(self.check_root)
        except AuditStop as stop:
            self.reader.close()
            return _stopped(self.record, stop)
        self.reader.close()
        header = dict(self.reader.header)
        scaling = header.pop('scaling')
        header.pop('itemsize')
        values = self.values.record()
        issues = []
        if scaling['active'] and self.role == 'mask':
            issues.append(dict(code='scaled_label_values', severity='warning',
                               detail='mask semantics are reported on scaled values'))
        if self.reader.trailing:
            issues.append(dict(code='trailing_payload_bytes', severity='warning',
                               detail=f'{self.reader.trailing} bytes after the declared payload'))
        if values['scaled_overflow_voxels']:
            issues.append(dict(code='scaled_overflow', severity='warning',
                               detail='finite stored values became non-finite after scaling'))
        self.record.update(header=header, scaling=scaling, voxels=values,
                           trailing_payload_bytes=self.reader.trailing, issues=issues,
                           limits=dict(asdict(self.limits), chunk_voxels=chunk))
        if self.mask is not None:
            nonfinite = sum(values['nonfinite'].values())
            if nonfinite:
                issues.append(dict(code='nonfinite_mask_values', severity='warning',
                                   detail='emptiness and volume are not determined'))
            if volume_context is None:
                geometry = self.record['geometry']
                basis = 'header_mm' if geometry is not None else None
                reason = None if geometry is not None else ', '.join(self.record['header_issues']) or 'no_geometry'
            else:
                geometry, basis, reason = volume_context
            ambiguous = sorted(set(self.record['header_issues']) & AMBIGUOUS_GRID)
            if ambiguous:
                geometry, basis, reason = None, None, 'ambiguous_geometry: ' + ', '.join(ambiguous)
            self.record['mask'] = self.mask.record(
                values, _volume(self.mask.nonzero, nonfinite, geometry, basis, reason))
        return self.record

    def abort(self, stop):
        if self.reader is not None:
            self.reader.close()
        if self.ok:
            _stopped(self.record, stop)


def _drive(targets, chunk, within=None):
    """Read aligned chunks from every target until each declared payload is consumed."""
    remaining = targets[0].reader.remaining
    while remaining:
        count = min(chunk, remaining)
        results = []
        for target in targets:
            try:
                results.append(target.consume(target.reader.read(count)))
            except AuditStop as stop:
                target.abort(stop)
                for other in targets:
                    if other is not target:
                        other.abort(AuditStop('aborted_with_pair', f'paired {target.role} stopped'))
                return False
        if within is not None:
            (ct_values, _), (mask_values, mask_finite) = results
            within.update(ct_values, mask_values, mask_finite)
        remaining -= count
    return True


def audit_volume(roots, alias, uri, *, role, expected_values=None, limits=Limits(),
                 check_root=lambda: None):
    """Audit one explicit file. Returns a JSON-serialisable record; stops are preserved, not raised."""
    target = _Target(role, roots, alias, uri, expected_values, limits, check_root)
    if not target.ok:
        return target.record
    try:
        chunk = _chunk_voxels([target], limits)
    except AuditStop as stop:
        target.abort(stop)
        return target.record
    _drive([target], chunk)
    return target.finish(chunk)


def audit_pair(roots, *, ct, mask, expected_values=None, study_ids=None, limits=Limits(),
               check_root=lambda: None):
    """Audit an explicit CT/mask pair given as (root alias, relative URI) tuples.

    study_ids=(mask_study_id, ct_study_id) must come from a validated source join. It is used
    only to invoke the approved paired-explicit-mm-CT rule for an unknown-unit mask's volume.
    """
    ct_t = _Target('ct', roots, *ct, None, limits, check_root)
    mask_t = _Target('mask', roots, *mask, expected_values, limits, check_root)
    result = dict(audit_version=AUDIT_VERSION, grid=None, within_mask_ct=None,
                  within_mask_unavailable_reason=None, unit_interpretation=None,
                  eligibility='not_assessed')

    volume_context = None
    if ct_t.evidence is not None and mask_t.evidence is not None:
        result['grid'] = _grid(ct_t.evidence, mask_t.evidence)
        geometry = mask_t.evidence['geometry']
        basis = 'header_mm' if geometry is not None else None
        reason = None
        if geometry is None:
            reason = ', '.join(mask_t.record['header_issues']) or 'no_geometry'
            if study_ids is not None and 'unknown_spatial_units' in mask_t.evidence['issue_codes']:
                try:
                    inferred = infer_mask_mm(mask_t.evidence, ct_t.evidence,
                                             mask_study_id=study_ids[0], ct_study_id=study_ids[1])
                    geometry = inferred['geometry']
                    basis = 'inferred_mm:' + inferred['unit_interpretation']['policy']
                    reason = None
                    result['unit_interpretation'] = inferred['unit_interpretation']
                except ValueError as exc:
                    reason = f'unknown_spatial_units; paired inference refused: {exc}'
            elif 'unknown_spatial_units' in mask_t.evidence['issue_codes']:
                reason = 'unknown_spatial_units; no validated study pairing supplied'
        volume_context = (geometry, basis, reason)

    within = None
    live = [t for t in (ct_t, mask_t) if t.ok]
    compatible = (result['grid'] is not None and result['grid']['compatible']
                  and len(live) == 2 and ct_t.reader.header['voxels'] == mask_t.reader.header['voxels'])
    if compatible:
        try:
            chunk = _chunk_voxels([ct_t, mask_t], limits)
        except AuditStop as stop:
            ct_t.abort(stop)
            mask_t.abort(stop)
            chunk = None
        if chunk is not None:
            within = _WithinMask()
            if not _drive([ct_t, mask_t], chunk, within):
                within = None
                result['within_mask_unavailable_reason'] = 'a paired file stopped during reading'
    else:
        result['within_mask_unavailable_reason'] = (
            'grid not verified as shared' if result['grid'] is not None else 'evidence unavailable')
        chunk = None
        for target in live:
            try:
                own = _chunk_voxels([target], limits)
            except AuditStop as stop:
                target.abort(stop)
                continue
            _drive([target], own)
            target.chunk = own
    result['ct'] = ct_t.finish(chunk or getattr(ct_t, 'chunk', None))
    if result['unit_interpretation'] is not None and not ct_t.ok:
        volume_context = (None, None, 'paired CT failed integrity checks')
    result['mask'] = mask_t.finish(chunk or getattr(mask_t, 'chunk', None), volume_context)
    if ct_t.ok and mask_t.ok:
        if within is not None:
            result['within_mask_ct'] = within.record()
    else:
        result['unit_interpretation'] = None
        result['within_mask_unavailable_reason'] = 'a paired file failed reading or final integrity checks'
    return result


# --- fixture-only demonstration -----------------------------------------------------------------

def demo():
    """Audit a synthetic pair in a temporary directory. Touches no real data or registered root."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        affine = np.diag([0.75, 0.75, 2.0, 1.0])
        ct = np.full((8, 8, 6), -1000, dtype=np.int16)
        ct[2:6, 2:6, 1:5] = 40
        mask = np.zeros((8, 8, 6), dtype=np.uint8)
        mask[3:5, 3:5, 2:4] = 1
        for name, data in (('ct.nii.gz', ct), ('pancreas.nii.gz', mask)):
            image = nib.Nifti1Image(data, affine)
            image.header.set_xyzt_units('mm')
            nib.save(image, root / name)
        report = audit_pair({'demo_root': root}, ct=('demo_root', 'ct.nii.gz'),
                            mask=('demo_root', 'pancreas.nii.gz'), expected_values=[0, 1])
    return report


if __name__ == '__main__':
    if sys.argv[1:] != ['--demo']:
        sys.stderr.write('usage: python -m scripts.diagnostics.audit_voxels --demo\n'
                         'Real-data audits are not runnable from this CLI in this packet.\n')
        raise SystemExit(2)
    print(json.dumps(demo(), indent=1, sort_keys=True, allow_nan=False))
