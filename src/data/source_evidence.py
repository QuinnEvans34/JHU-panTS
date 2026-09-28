"""Read-only file/header evidence for explicitly approved inventory roots.

Roots here are scoped diagnostic inputs, not activated production source aliases.
No voxel interpretation, cohort publication or eligibility decision occurs here.
"""
import hashlib
from copy import deepcopy
import os
from pathlib import Path
import re
import stat
from uuid import uuid4

import nibabel as nib
import numpy as np

from src.data.manifest_records import file_reference, validate_schema


def raw_header(image):
    """Retain native numeric evidence without asserting physical units."""
    return dict(shape=list(image.shape),
                spacing_native=[float(v) for v in image.header.get_zooms()],
                affine_native=np.asarray(image.affine).tolist(),
                spatial_units=image.header.get_xyzt_units()[0],
                qform_native=image.get_qform().tolist(),
                sform_native=image.get_sform().tolist(),
                qform_code=int(image.header['qform_code']),
                sform_code=int(image.header['sform_code']))


def infer_mask_mm(mask, ct, *, mask_study_id, ct_study_id):
    """Approved paired-CT inference; return new evidence, never edit measurements.

    Study IDs must come from the validated source join, not a guessed filename match.
    Resolves only units, not anatomical alignment, annotation validity or eligibility.
    Existing issue artifacts must be retained and superseded by the publishing adapter.
    """
    if (mask_study_id != ct_study_id or not isinstance(ct_study_id, str)
            or not re.fullmatch(r'[a-z][a-z0-9_-]{1,31}:study:[A-Za-z0-9._-]{1,160}', ct_study_id)):
        raise ValueError('Validated same-study pairing required')
    for record in (mask, ct):
        if not re.fullmatch(r'[0-9a-f]{64}', record['file']['content_sha256']):
            raise ValueError('Measured paired file hashes required')
    raw, reference = mask['raw_header'], ct['raw_header']
    if (raw['spatial_units'] != 'unknown' or mask['issue_codes'] != ['unknown_spatial_units']
            or reference['spatial_units'] != 'mm' or ct['issue_codes'] or ct['geometry'] is None):
        raise ValueError('Requires unknown-unit mask and clean explicitly-mm CT')
    if raw['shape'] != reference['shape'] or len(raw['shape']) != 3:
        raise ValueError('Paired shapes disagree')
    for key in ('spacing_native', 'affine_native'):
        a, b = np.asarray(raw[key], dtype=float), np.asarray(reference[key], dtype=float)
        if a.shape != b.shape or not np.isfinite(a).all() or not np.allclose(a, b, rtol=0, atol=1e-5):
            raise ValueError('Paired geometry disagrees')
    affine = np.asarray(raw['affine_native'], dtype=float)
    if affine.shape != (4, 4) or not (raw['qform_code'] or raw['sform_code']):
        raise ValueError('Coded transform required')
    for prefix in ('qform', 'sform'):
        if raw[prefix + '_code']:
            transform = np.asarray(raw[prefix + '_native'], dtype=float)
            if (transform.shape != (4, 4) or not np.isfinite(transform).all()
                    or not np.allclose(transform, affine, rtol=0, atol=1e-4)):
                raise ValueError('Mask coded transforms disagree')
    result = deepcopy(mask)
    result['geometry'] = deepcopy(ct['geometry'])
    result['issue_codes'] = []
    result['unit_interpretation'] = dict(
        policy='paired-explicit-mm-ct-v1', method='inferred_from_paired_ct',
        study_id=ct_study_id, mask_sha256=mask['file']['content_sha256'],
        ct_sha256=ct['file']['content_sha256'], original_units='unknown', interpreted_units='mm',
        resolved_issue_codes=['unknown_spatial_units'])
    result['eligibility'] = 'not_assessed'
    return result


def evidence_issues(evidence, *, entity_type, entity_id, created_at):
    """Create new append-only blocking issue records; never infer a resolution."""
    records = []
    for code in evidence['issue_codes']:
        record = dict(schema_version='1.0.0', issue_id='issue:' + str(uuid4()),
                      rule_code=code.upper(), entity_type=entity_type, entity_id=entity_id,
                      severity='blocking', disposition='quarantine',
                      message=f'Header evidence unresolved: {code}; no automatic repair.',
                      evidence=[dict(kind='file_hash', reference=evidence['file']['content_sha256']),
                                dict(kind='validator_output', reference='source_evidence:header-v1:' + code)],
                      created_at=created_at)
        validate_schema('data-issue', record)
        records.append(record)
    return records


def resolve_file(roots, alias, uri):
    if not re.fullmatch(r'[a-z][a-z0-9_-]{1,63}', alias) or alias not in roots:
        raise ValueError('Unapproved evidence root alias')
    file_reference({'uri': uri})
    root = Path(roots[alias])
    if not root.is_absolute() or root.resolve(strict=True) != root or not root.is_dir():
        raise ValueError('Evidence root must be an existing canonical directory')
    current = root
    for part in uri.split('/'):
        current = current / part
        info = current.lstat()
        if stat.S_ISLNK(info.st_mode):
            raise ValueError('Symlink in evidence path')
    if not stat.S_ISREG(info.st_mode):
        raise ValueError('Evidence must be a regular file')
    return current


def identity(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def header_geometry(image):
    """Return millimetre geometry or explicit issues, without loading voxel arrays."""
    issues = []
    shape = image.shape
    if len(shape) != 3 or any(n <= 0 for n in shape):
        return None, ['unsupported_image_dimensions']
    unit = image.header.get_xyzt_units()[0]
    scale = {'mm': 1.0, 'meter': 1000.0, 'micron': 0.001}.get(unit)
    if scale is None:
        return None, ['unknown_spatial_units']
    affine = np.array(image.affine, dtype=float, copy=True)
    spacing = np.asarray(image.header.get_zooms()[:3], dtype=float) * scale
    affine[:3, :] *= scale
    if (not np.isfinite(affine).all() or not np.isfinite(spacing).all()
            or np.any(spacing <= 0) or abs(np.linalg.det(affine[:3, :3])) < 1e-12
            or not np.allclose(affine[3], [0, 0, 0, 1])):
        return None, ['invalid_geometry']
    qform, qcode = image.get_qform(coded=True)
    sform, scode = image.get_sform(coded=True)
    if not qcode and not scode:
        issues.append('uncoded_spatial_transform')
    if qcode and scode and not np.allclose(qform, sform, rtol=1e-5, atol=1e-4 / scale):
        issues.append('qform_sform_disagreement')
    if not np.allclose(np.linalg.norm(affine[:3, :3], axis=0), spacing, rtol=1e-4, atol=1e-5):
        issues.append('affine_spacing_disagreement')
    return dict(shape_xyz=list(shape), spacing_mm_xyz=spacing.tolist(),
                affine_ras=affine.reshape(-1).tolist()), issues


def measure_nifti(roots, alias, uri, check_root=lambda: None):
    """Hash exact file bytes and read header only; refuse observed concurrent changes.

    check_root is a caller-supplied mount/UUID check for real external data. Tests may
    omit it for temporary local fixtures. Parent replacement by hostile concurrent
    writers is not supported; use the project's exclusive-writer operating boundary.
    """
    check_root()
    path = resolve_file(roots, alias, uri)
    if not uri.endswith(('.nii', '.nii.gz')):
        raise ValueError('NIfTI file required')
    before = identity(path.lstat())
    sha = hashlib.sha256()
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    with os.fdopen(os.open(path, flags), 'rb') as stream:
        if identity(os.fstat(stream.fileno())) != before:
            raise ValueError('File changed before evidence read')
        read = 0
        while chunk := stream.read(1024 * 1024):
            sha.update(chunk)
            read += len(chunk)
        if identity(os.fstat(stream.fileno())) != before or read != before[2]:
            raise ValueError('File changed during evidence read')
    image = nib.load(str(path), mmap=True)
    geometry, issues = header_geometry(image)
    check_root()
    if resolve_file(roots, alias, uri) != path or identity(path.lstat()) != before:
        raise ValueError('File changed during header read')
    return dict(file=dict(root_alias=alias, uri=uri,
                          media_type='application/gzip' if uri.endswith('.gz') else 'application/x-nifti',
                          bytes=read, content_sha256=sha.hexdigest()),
                geometry=geometry, raw_header=raw_header(image), issue_codes=issues,
                evidence_scope='file_hash_and_header_only', eligibility='not_assessed')
