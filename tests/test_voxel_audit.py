"""Voxel audit kernel: synthetic fixtures only, built at runtime under pytest tmp_path.

Fixtures are written byte-for-byte (348-byte header, 4-byte extension flag, Fortran-order
payload) so expected values are computed by hand from the arrays below, not by the audit or by
nibabel's array reader. No real data, registered roots or external drives are touched.
"""
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tracemalloc

import nibabel as nib
import numpy as np
import pytest

from scripts.diagnostics import audit_voxels as av
from scripts.diagnostics.audit_voxels import Limits, audit_pair, audit_volume

REPO = Path(__file__).resolve().parents[1]
ALIAS = 'synthetic_root'
STUDY = 'pants:study:PanTS_00000001'
SPACING = (0.75, 0.875, 2.5)          # exact in float32; voxel volume 1.640625 mm^3
VOXEL_MM3 = 0.75 * 0.875 * 2.5
SHAPE = (6, 5, 4)
N = 6 * 5 * 4


def affine_for(spacing=SPACING, shift=(0.0, 0.0, 0.0), flip_x=False):
    a = np.diag([*spacing, 1.0])
    if flip_x:
        a[0, 0] = -a[0, 0]
    a[:3, 3] = shift
    return a


def write_nifti(path, stored, *, affine=None, units='mm', slope=float('nan'), inter=0.0,
                qcode=1, scode=1, qform=None, dims=None, trailing=b'', cut=0, big_endian=False):
    """Write a single-file NIfTI-1 by hand and return its path."""
    stored = np.asarray(stored)
    affine = affine_for() if affine is None else affine
    header = nib.Nifti1Header()
    header.set_data_dtype(stored.dtype)
    header.set_data_shape(stored.shape if dims is None else dims)
    header.set_zooms(tuple(float(np.linalg.norm(affine[:3, i])) for i in range(3))
                     + (1.0,) * (len(stored.shape if dims is None else dims) - 3))
    header.set_qform(affine if qform is None else qform, code=qcode)
    header.set_sform(affine, code=scode)
    header.set_xyzt_units(xyz=units)
    header['scl_slope'], header['scl_inter'] = slope, inter
    header['vox_offset'] = 352
    payload = np.asfortranarray(stored)
    if big_endian:
        header = header.as_byteswapped('>')
        payload = payload.astype(payload.dtype.newbyteorder('>'))
    body = header.binaryblock + b'\0' * 4 + payload.tobytes(order='F') + trailing
    body = body[:len(body) - cut]
    path = Path(path)
    path.write_bytes(gzip.compress(body, mtime=0) if path.name.endswith('.gz') else body)
    return path


def roots(tmp_path):
    return {ALIAS: tmp_path.resolve()}


def vol(tmp_path, name, **kw):
    return audit_volume(roots(tmp_path), ALIAS, name, **kw)


def pair(tmp_path, ct, mask, **kw):
    return audit_pair(roots(tmp_path), ct=(ALIAS, ct), mask=(ALIAS, mask), **kw)


def mask_array(points, value=1, dtype=np.uint8):
    m = np.zeros(SHAPE, dtype=dtype)
    for p in points:
        m[p] = value
    return m


def ct_array():
    return (np.arange(N, dtype=np.int16).reshape(SHAPE, order='F') - 1000).astype(np.int16)


def noisy():
    """Poorly compressible payload, so gzip damage lands well after the header."""
    return np.random.default_rng(1).integers(-1000, 1000, (32, 32, 16)).astype(np.int16)


def gzip_of(tmp_path, stored):
    raw = write_nifti(tmp_path / 'plain.nii', stored)
    blob = gzip.compress(raw.read_bytes(), mtime=0)
    raw.unlink()
    return bytearray(blob)


POINTS = [(0, 0, 0), (1, 2, 3), (5, 4, 3), (2, 2, 2), (3, 1, 0), (4, 4, 1), (0, 3, 2)]


def stop_code(record):
    assert record['status'] == 'stopped', record
    return record['stop']['code']


# --- 1. emptiness and exact counts ---------------------------------------------------------------

@pytest.mark.unit
def test_empty_mask_is_empty_with_zero_volume(tmp_path):
    write_nifti(tmp_path / 'm.nii.gz', np.zeros(SHAPE, np.uint8))
    m = vol(tmp_path, 'm.nii.gz', role='mask')['mask']
    assert m['empty'] is True and m['nonzero_voxels'] == 0
    assert m['value_counts'] == [[0, N]] and m['volume']['mm3'] == 0.0


@pytest.mark.unit
def test_nonempty_mask_exact_count(tmp_path):
    write_nifti(tmp_path / 'm.nii', mask_array(POINTS))
    r = vol(tmp_path, 'm.nii', role='mask')
    assert r['status'] == 'measured' and r['voxels']['count'] == N
    m = r['mask']
    assert m['empty'] is False and m['nonzero_voxels'] == 7
    assert m['value_counts'] == [[0, N - 7], [1, 7]] and m['distinct_values'] == [0, 1]


# --- 2. physical volume from anisotropic geometry ----------------------------------------------

@pytest.mark.unit
@pytest.mark.parametrize('units, scale', [('mm', 1.0), ('meter', 1e-3), ('micron', 1e3)])
def test_anisotropic_volume_is_hand_computed(tmp_path, units, scale):
    spacing = tuple(s * scale for s in SPACING)
    write_nifti(tmp_path / 'm.nii', mask_array(POINTS), affine=affine_for(spacing), units=units)
    volume = vol(tmp_path, 'm.nii', role='mask')['mask']['volume']
    assert volume['available'] is True and volume['basis'] == 'header_mm'
    assert volume['voxel_mm3'] == pytest.approx(VOXEL_MM3, rel=1e-6)
    assert volume['mm3'] == pytest.approx(7 * VOXEL_MM3, rel=1e-6)


@pytest.mark.unit
def test_flipped_axis_volume_uses_absolute_determinant(tmp_path):
    write_nifti(tmp_path / 'm.nii', mask_array(POINTS), affine=affine_for(flip_x=True))
    volume = vol(tmp_path, 'm.nii', role='mask')['mask']['volume']
    assert volume['mm3'] == pytest.approx(7 * VOXEL_MM3, rel=1e-9)


# --- 3. unknown units ---------------------------------------------------------------------------

@pytest.mark.unit
def test_unknown_units_count_available_volume_unavailable(tmp_path):
    write_nifti(tmp_path / 'm.nii', mask_array(POINTS), units='unknown')
    r = vol(tmp_path, 'm.nii', role='mask')
    assert r['mask']['nonzero_voxels'] == 7 and r['geometry'] is None
    assert r['mask']['volume'] == dict(available=False, mm3=None, voxel_mm3=None, basis=None,
                                       reason='unknown_spatial_units')


@pytest.mark.component
def test_unknown_unit_mask_uses_approved_paired_rule_only_with_study_ids(tmp_path):
    write_nifti(tmp_path / 'ct.nii.gz', ct_array())
    write_nifti(tmp_path / 'm.nii.gz', mask_array(POINTS), units='unknown')
    without = pair(tmp_path, 'ct.nii.gz', 'm.nii.gz')
    assert without['mask']['mask']['volume']['available'] is False
    assert 'no validated study pairing' in without['mask']['mask']['volume']['reason']
    assert without['unit_interpretation'] is None

    wrong = pair(tmp_path, 'ct.nii.gz', 'm.nii.gz', study_ids=(STUDY, 'pants:study:PanTS_00000002'))
    assert 'paired inference refused' in wrong['mask']['mask']['volume']['reason']

    inferred = pair(tmp_path, 'ct.nii.gz', 'm.nii.gz', study_ids=(STUDY, STUDY))
    volume = inferred['mask']['mask']['volume']
    assert volume['basis'] == 'inferred_mm:paired-explicit-mm-ct-v1'
    assert volume['mm3'] == pytest.approx(7 * VOXEL_MM3, rel=1e-9)
    assert inferred['unit_interpretation']['original_units'] == 'unknown'
    assert inferred['mask']['spatial_units'] == 'unknown'  # the original header is not rewritten
    assert inferred['grid']['compatible'] is True and inferred['grid']['basis'] == 'native'


@pytest.mark.unit
def test_unknown_units_with_only_sform_coded_is_comparable(tmp_path):
    # Mirrors the observed qform_code=0 / sform_code=2 header shape.
    write_nifti(tmp_path / 'ct.nii', ct_array(), units='unknown', qcode=0, scode=2)
    write_nifti(tmp_path / 'm.nii', mask_array(POINTS), units='unknown', qcode=0, scode=2)
    r = pair(tmp_path, 'ct.nii', 'm.nii')
    assert r['grid']['compatible'] is True and r['grid']['affine_sources'] == ['sform', 'sform']
    assert r['within_mask_ct'] is not None


# --- 4. grid comparison --------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.parametrize('mask_affine, code', [
    (affine_for(shift=(0.5, 0.0, 0.0)), 'affine_mismatch'),
    (affine_for(flip_x=True), 'affine_mismatch'),
])
def test_same_shape_different_affine_blocks_voxel_pairing(tmp_path, mask_affine, code):
    write_nifti(tmp_path / 'ct.nii', ct_array())
    write_nifti(tmp_path / 'm.nii', mask_array(POINTS), affine=mask_affine)
    r = pair(tmp_path, 'ct.nii', 'm.nii')
    assert r['grid']['compatible'] is False and r['grid']['shape_equal'] is True
    assert code in {i['code'] for i in r['grid']['issues']}
    assert r['within_mask_ct'] is None and r['within_mask_unavailable_reason'] == 'grid not verified as shared'
    assert r['mask']['mask']['nonzero_voxels'] == 7  # files are still measured independently


@pytest.mark.unit
def test_different_shapes_block_voxel_pairing(tmp_path):
    write_nifti(tmp_path / 'ct.nii', np.zeros((6, 5, 5), np.int16))
    write_nifti(tmp_path / 'm.nii', mask_array(POINTS))
    r = pair(tmp_path, 'ct.nii', 'm.nii')
    assert 'shape_mismatch' in {i['code'] for i in r['grid']['issues']}
    assert r['within_mask_ct'] is None and r['ct']['status'] == r['mask']['status'] == 'measured'


@pytest.mark.unit
@pytest.mark.parametrize('delta, compatible', [(4e-6, True), (4e-5, False)])
def test_pair_tolerance_boundary(tmp_path, delta, compatible):
    write_nifti(tmp_path / 'ct.nii', ct_array(), affine=affine_for(shift=(-100.0, 0, 0)))
    write_nifti(tmp_path / 'm.nii', mask_array(POINTS), affine=affine_for(shift=(-100.0 + delta, 0, 0)))
    r = pair(tmp_path, 'ct.nii', 'm.nii')
    assert r['grid']['compatible'] is compatible
    assert (r['within_mask_ct'] is not None) is compatible


@pytest.mark.unit
@pytest.mark.parametrize('units', ['mm', 'unknown'])
def test_qform_sform_disagreement_blocks_pairing(tmp_path, units):
    # For unknown units the adapter skips this check; the audit applies infer_mask_mm's test.
    write_nifti(tmp_path / 'ct.nii', ct_array(), units=units)
    write_nifti(tmp_path / 'm.nii', mask_array(POINTS), units=units,
                qform=affine_for(shift=(1.0, 0, 0)), qcode=1, scode=1)
    r = pair(tmp_path, 'ct.nii', 'm.nii')
    assert 'qform_sform_disagreement' in r['mask']['header_issues']
    assert 'mask_qform_sform_disagreement' in {i['code'] for i in r['grid']['issues']}
    assert r['within_mask_ct'] is None


@pytest.mark.unit
def test_uncoded_transforms_block_pairing(tmp_path):
    write_nifti(tmp_path / 'ct.nii', ct_array(), qcode=0, scode=0)
    write_nifti(tmp_path / 'm.nii', mask_array(POINTS), qcode=0, scode=0)
    r = pair(tmp_path, 'ct.nii', 'm.nii')
    codes = {i['code'] for i in r['grid']['issues']}
    assert {'ct_uncoded_spatial_transform', 'mask_uncoded_spatial_transform'} <= codes
    assert r['grid']['affine_sources'] == ['fallback_zooms', 'fallback_zooms']


@pytest.mark.component
def test_within_mask_ct_values_hand_computed(tmp_path):
    ct = ct_array()
    write_nifti(tmp_path / 'ct.nii.gz', ct)
    write_nifti(tmp_path / 'm.nii.gz', mask_array(POINTS))
    expected = [int(ct[p]) for p in POINTS]
    w = pair(tmp_path, 'ct.nii.gz', 'm.nii.gz')['within_mask_ct']
    assert w['mask_nonzero_voxels'] == 7 and w['ct_finite'] == 7 and w['ct_nonfinite'] == 0
    assert (w['ct_min'], w['ct_max']) == (min(expected), max(expected))
    assert w['ct_mean'] == pytest.approx(sum(expected) / 7, rel=1e-12)
    assert 'No threshold' in w['note']


# --- 5. label values -----------------------------------------------------------------------------

@pytest.mark.unit
def test_multiple_allowed_labels_plus_unexpected_value(tmp_path):
    m = mask_array(POINTS[:3], 1)
    m[POINTS[3]] = 2
    m[POINTS[4]] = m[POINTS[5]] = 7
    write_nifti(tmp_path / 'm.nii', m)
    r = vol(tmp_path, 'm.nii', role='mask', expected_values=[0, 1, 2])['mask']
    assert r['value_counts'] == [[0, N - 6], [1, 3], [2, 1], [7, 2]]
    assert r['unexpected_value_voxels'] == 2 and r['unexpected_values'] == [7]
    assert r['nonzero_voxels'] == 6 and r['negative_voxels'] == 0


@pytest.mark.unit
def test_fractional_and_negative_labels_are_counted_not_rounded(tmp_path):
    m = np.zeros(SHAPE, np.float32)
    m[POINTS[0]] = m[POINTS[1]] = 0.5
    m[POINTS[2]] = -1.0
    m[POINTS[3]] = 1.0
    write_nifti(tmp_path / 'm.nii', m)
    r = vol(tmp_path, 'm.nii', role='mask', expected_values=[0, 1])['mask']
    assert r['nonintegral_voxels'] == 2 and r['negative_voxels'] == 1 and r['nonzero_voxels'] == 4
    assert r['unexpected_value_voxels'] == 3 and r['unexpected_values'] == [-1.0, 0.5]


@pytest.mark.unit
def test_expected_values_are_caller_policy_not_default(tmp_path):
    write_nifti(tmp_path / 'm.nii', mask_array(POINTS, 3))
    r = vol(tmp_path, 'm.nii', role='mask')['mask']
    assert r['expected_values'] is None and r['unexpected_value_voxels'] is None
    with pytest.raises(ValueError):
        vol(tmp_path, 'm.nii', role='ct', expected_values=[0, 1])
    with pytest.raises(ValueError):
        vol(tmp_path, 'm.nii', role='mask', expected_values=[0, float('nan')])
    with pytest.raises(ValueError):
        vol(tmp_path, 'm.nii', role='label')


@pytest.mark.unit
def test_distinct_value_cap_truncates_listing_but_not_counts(tmp_path):
    m = np.arange(N, dtype=np.int16).reshape(SHAPE) % 10   # values 0..9, 12 voxels each
    write_nifti(tmp_path / 'm.nii', m)
    r = vol(tmp_path, 'm.nii', role='mask', expected_values=[0, 1],
            limits=Limits(max_distinct=4, max_listed=3, working_bytes=2000))
    mk = r['mask']
    assert mk['distinct_values_truncated'] is True and len(mk['distinct_values']) == 4
    assert all(count == 12 for _, count in mk['value_counts'])   # listed counts stay exact
    assert mk['nonzero_voxels'] == N - 12                        # totals ignore the listing cap
    assert mk['unexpected_value_voxels'] == 8 * 12
    assert len(mk['unexpected_values']) == 3 and mk['unexpected_values_truncated'] is True


# --- 6. non-finite values -----------------------------------------------------------------------

@pytest.mark.unit
def test_nonfinite_mask_values_are_counted_and_block_emptiness(tmp_path):
    m = np.zeros(SHAPE, np.float32)
    m[POINTS[0]] = m[POINTS[1]] = np.nan
    m[POINTS[2]] = np.inf
    m[POINTS[3]] = -np.inf
    m[POINTS[4]] = 1.0
    write_nifti(tmp_path / 'm.nii.gz', m)
    r = vol(tmp_path, 'm.nii.gz', role='mask')
    v = r['voxels']
    assert v['count'] == N and v['finite'] == N - 4
    assert v['nonfinite'] == dict(nan=2, posinf=1, neginf=1)
    assert r['mask']['empty'] is None and r['mask']['nonzero_voxels'] == 1
    assert r['mask']['volume']['available'] is False
    assert 'nonfinite_mask_values' in {i['code'] for i in r['issues']}
    json.dumps(r, allow_nan=False)


@pytest.mark.unit
def test_nonfinite_ct_values_inside_mask_are_reported_not_dropped(tmp_path):
    ct = ct_array().astype(np.float32)
    ct[POINTS[0]] = np.nan
    ct[POINTS[1]] = -np.inf
    write_nifti(tmp_path / 'ct.nii', ct)
    write_nifti(tmp_path / 'm.nii', mask_array(POINTS))
    w = pair(tmp_path, 'ct.nii', 'm.nii')['within_mask_ct']
    kept = [float(ct[p]) for p in POINTS[2:]]
    assert w['mask_nonzero_voxels'] == 7 and w['ct_finite'] == 5 and w['ct_nonfinite'] == 2
    assert w['ct_mean'] == pytest.approx(sum(kept) / 5)


@pytest.mark.unit
def test_scaling_overflow_is_reported(tmp_path):
    write_nifti(tmp_path / 'ct.nii', np.full(SHAPE, 1e300), slope=1e10)   # scl_slope is float32
    r = vol(tmp_path, 'ct.nii', role='ct')
    assert r['voxels']['nonfinite']['posinf'] == N and r['voxels']['scaled_overflow_voxels'] == N
    assert 'scaled_overflow' in {i['code'] for i in r['issues']}


# --- 7. scaling, compression, byte order -------------------------------------------------------

@pytest.mark.unit
def test_slope_intercept_applied_in_float64(tmp_path):
    stored = np.zeros(SHAPE, np.int16)
    stored[0, 0, 0], stored[1, 1, 1] = -4, 400
    write_nifti(tmp_path / 'ct.nii', stored, slope=2.5, inter=-1024.0)
    r = vol(tmp_path, 'ct.nii', role='ct')
    assert r['scaling'] == dict(active=True, slope=2.5, inter=-1024.0, header_slope_finite=True)
    v = r['voxels']
    assert (v['stored_min'], v['stored_max']) == (-4, 400)
    assert (v['min'], v['max']) == (-1034.0, -24.0) and v['values_basis'] == 'scaled'


@pytest.mark.unit
@pytest.mark.parametrize('slope', [0.0, float('nan')])
def test_zero_or_nan_slope_means_unscaled(tmp_path, slope):
    write_nifti(tmp_path / 'ct.nii', ct_array(), slope=slope, inter=5.0)
    r = vol(tmp_path, 'ct.nii', role='ct')
    assert r['scaling']['active'] is False and r['voxels']['values_basis'] == 'stored'
    assert r['voxels']['min'] == -1000


@pytest.mark.unit
def test_infinite_slope_stops_instead_of_silently_unscaled(tmp_path):
    write_nifti(tmp_path / 'ct.nii', ct_array(), slope=float('inf'))
    assert stop_code(vol(tmp_path, 'ct.nii', role='ct')) == 'invalid_scaling'


@pytest.mark.unit
def test_nonfinite_intercept_is_refused(tmp_path):
    write_nifti(tmp_path / 'ct.nii', ct_array(), slope=2.0, inter=float('nan'))
    assert stop_code(vol(tmp_path, 'ct.nii', role='ct')) in {'evidence_refused', 'invalid_scaling'}


@pytest.mark.unit
def test_scaled_mask_is_measured_on_scaled_values_with_warning(tmp_path):
    write_nifti(tmp_path / 'm.nii', mask_array(POINTS), slope=0.5)
    r = vol(tmp_path, 'm.nii', role='mask', expected_values=[0, 1])
    assert r['mask']['distinct_values'] == [0.0, 0.5] and r['mask']['nonintegral_voxels'] == 7
    assert 'scaled_label_values' in {i['code'] for i in r['issues']}


@pytest.mark.unit
@pytest.mark.parametrize('big_endian', [False, True])
def test_compressed_and_uncompressed_measure_identically(tmp_path, big_endian):
    m = mask_array(POINTS, dtype=np.int16)
    write_nifti(tmp_path / 'a.nii', m, big_endian=big_endian)
    write_nifti(tmp_path / 'b.nii.gz', m, big_endian=big_endian)
    a, b = vol(tmp_path, 'a.nii', role='mask'), vol(tmp_path, 'b.nii.gz', role='mask')
    assert a['file']['media_type'] == 'application/x-nifti' and b['file']['media_type'] == 'application/gzip'
    for key in ('voxels', 'mask', 'scaling', 'header'):
        assert a[key] == b[key]
    assert a['mask']['nonzero_voxels'] == 7 and a['header']['stored_dtype'][0] == ('>' if big_endian else '<')


@pytest.mark.unit
def test_int64_precision_risk_flagged_when_scaled(tmp_path):
    m = np.zeros(SHAPE, np.int64)
    m[0, 0, 0] = 2**60
    write_nifti(tmp_path / 'ct.nii', m, slope=1.0, inter=1.0)
    assert vol(tmp_path, 'ct.nii', role='ct')['voxels']['float64_precision_loss_risk'] is True


# --- 8. corrupt, truncated, unsupported and oversized inputs ----------------------------------

@pytest.mark.failure_injection
def test_truncated_uncompressed_payload_stops_before_reading(tmp_path, monkeypatch):
    reads = instrument_reads(monkeypatch)
    write_nifti(tmp_path / 'ct.nii', ct_array(), cut=3)
    assert stop_code(vol(tmp_path, 'ct.nii', role='ct')) == 'payload_truncated'
    assert reads == []


@pytest.mark.failure_injection
def test_truncated_gzip_payload_stops(tmp_path):
    blob = gzip_of(tmp_path, noisy())
    (tmp_path / 'ct.nii.gz').write_bytes(bytes(blob[:len(blob) // 2]))
    assert stop_code(vol(tmp_path, 'ct.nii.gz', role='ct')) == 'corrupt_payload'


@pytest.mark.failure_injection
def test_gzip_damaged_inside_header_region_is_refused_by_adapter(tmp_path):
    blob = gzip_of(tmp_path, ct_array())      # tiny stream: nibabel's header read hits the cut
    (tmp_path / 'ct.nii.gz').write_bytes(bytes(blob[:-20]))
    assert stop_code(vol(tmp_path, 'ct.nii.gz', role='ct')) == 'evidence_refused'


@pytest.mark.failure_injection
def test_gzip_crc_corruption_is_detected_after_payload(tmp_path):
    blob = gzip_of(tmp_path, noisy())
    blob[-8] ^= 0xFF                                    # first byte of the CRC32 trailer
    (tmp_path / 'ct.nii.gz').write_bytes(bytes(blob))
    assert stop_code(vol(tmp_path, 'ct.nii.gz', role='ct')) == 'corrupt_payload'


@pytest.mark.unit
def test_trailing_bytes_are_counted_as_warning(tmp_path):
    write_nifti(tmp_path / 'ct.nii', ct_array(), trailing=b'\x01' * 9)
    write_nifti(tmp_path / 'ct.nii.gz', ct_array(), trailing=b'\x01' * 9)
    for name in ('ct.nii', 'ct.nii.gz'):
        r = vol(tmp_path, name, role='ct')
        assert r['status'] == 'measured' and r['trailing_payload_bytes'] == 9
        assert 'trailing_payload_bytes' in {i['code'] for i in r['issues']}


@pytest.mark.unit
@pytest.mark.parametrize('stored', [np.zeros((6, 5, 4, 2), np.int16), np.zeros((6, 5, 4, 1), np.int16)])
def test_non_3d_input_stops(tmp_path, stored):
    write_nifti(tmp_path / 'ct.nii', stored)
    assert stop_code(vol(tmp_path, 'ct.nii', role='ct')) == 'unsupported_dimensions'


@pytest.mark.unit
def test_complex_datatype_stops(tmp_path):
    write_nifti(tmp_path / 'ct.nii', np.zeros(SHAPE, np.complex64))
    assert stop_code(vol(tmp_path, 'ct.nii', role='ct')) == 'unsupported_datatype'


@pytest.mark.unit
@pytest.mark.parametrize('limits', [Limits(max_axis=5), Limits(max_voxels=N - 1)])
def test_declared_oversized_shape_stops_before_any_payload_read(tmp_path, monkeypatch, limits):
    reads = instrument_reads(monkeypatch)
    write_nifti(tmp_path / 'ct.nii', ct_array())
    assert stop_code(vol(tmp_path, 'ct.nii', role='ct', limits=limits)) == 'limit_exceeded'
    assert reads == []                                                # no voxel payload read


@pytest.mark.unit
def test_declared_huge_shape_with_tiny_file_stops_on_limits(tmp_path):
    # Header declares 4096 x 4096 x 4096; only a few payload bytes exist.
    write_nifti(tmp_path / 'ct.nii', np.zeros((2, 2, 2), np.int16), dims=(4096, 4096, 4096))
    assert stop_code(vol(tmp_path, 'ct.nii', role='ct')) == 'limit_exceeded'


@pytest.mark.failure_injection
def test_paired_stop_aborts_partner_and_withholds_within_mask(tmp_path):
    blob = gzip_of(tmp_path, noisy())
    (tmp_path / 'ct.nii.gz').write_bytes(bytes(blob[:len(blob) // 2]))
    write_nifti(tmp_path / 'm.nii', np.zeros((32, 32, 16), np.uint8))
    r = pair(tmp_path, 'ct.nii.gz', 'm.nii')
    assert r['grid']['compatible'] is True                 # the stop happened during lockstep reads
    assert r['ct']['status'] == 'stopped' and stop_code(r['mask']) == 'aborted_with_pair'
    assert r['within_mask_ct'] is None and r['within_mask_unavailable_reason']


@pytest.mark.unit
def test_unapproved_alias_and_symlink_are_refused(tmp_path):
    write_nifti(tmp_path / 'ct.nii', ct_array())
    os.symlink(tmp_path / 'ct.nii', tmp_path / 'link.nii')
    assert stop_code(audit_volume(roots(tmp_path), 'other_root', 'ct.nii', role='ct')) == 'evidence_refused'
    r = vol(tmp_path, 'link.nii', role='ct')
    assert stop_code(r) == 'evidence_refused' and 'Symlink' in r['stop']['detail']


# --- 9. no proxy loading; bounded slabs and memory -------------------------------------------

def instrument_reads(monkeypatch):
    """Record (kind, size) for every voxel-payload read issued through the audit's open seam.

    Reads that start before byte 352 belong to the header parse and are not recorded.
    """
    reads = []
    real_open = av._open_payload

    class Spy:
        def __init__(self, inner):
            self.inner = inner

        def readinto(self, view):
            if self.inner.tell() >= 352:
                reads.append(('readinto', len(view)))
            return self.inner.readinto(view)

        def read(self, size=-1):
            if self.inner.tell() >= 352:
                reads.append(('read', size))
            return self.inner.read(size)

        def __getattr__(self, name):
            return getattr(self.inner, name)

    def spying_open(path):
        raw, stream = real_open(path)
        return raw, Spy(stream)

    monkeypatch.setattr(av, '_open_payload', spying_open)
    return reads


@pytest.fixture
def forbid_full_array(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError('full-array or proxy voxel access is forbidden')
    for owner, name in [(nib.arrayproxy.ArrayProxy, '__array__'),
                        (nib.arrayproxy.ArrayProxy, '__getitem__'),
                        (nib.arrayproxy.ArrayProxy, 'get_unscaled'),
                        (nib.arrayproxy.ArrayProxy, '_get_scaled'),
                        (nib.arrayproxy.ArrayProxy, '_get_unscaled'),
                        (nib.dataobj_images.DataobjImage, 'get_fdata'),
                        (nib.Nifti1Header, 'data_from_fileobj')]:
        monkeypatch.setattr(owner, name, refuse)


@pytest.mark.component
def test_no_proxy_or_full_array_access(tmp_path, forbid_full_array):
    write_nifti(tmp_path / 'ct.nii.gz', ct_array(), slope=1.5, inter=-3.0)
    write_nifti(tmp_path / 'm.nii', mask_array(POINTS))
    r = pair(tmp_path, 'ct.nii.gz', 'm.nii', expected_values=[0, 1])
    assert r['ct']['status'] == r['mask']['status'] == 'measured'
    assert r['within_mask_ct']['mask_nonzero_voxels'] == 7


@pytest.mark.component
@pytest.mark.parametrize('ct_name', ['ct.nii', 'ct.nii.gz'])
def test_payload_reads_are_bounded_by_the_chunk(tmp_path, monkeypatch, ct_name):
    reads = instrument_reads(monkeypatch)
    write_nifti(tmp_path / ct_name, ct_array())
    write_nifti(tmp_path / 'm.nii', mask_array(POINTS))
    r = pair(tmp_path, ct_name, 'm.nii', limits=Limits(working_bytes=1000))
    chunk = r['ct']['limits']['chunk_voxels']
    assert chunk == 1000 // ((2 + av.CT_WORKING_BYTES_PER_VOXEL) + (1 + av.MASK_WORKING_BYTES_PER_VOXEL)
                             + av.PAIR_WORKING_BYTES_PER_VOXEL)
    payload = [n for kind, n in reads if kind == 'readinto']
    assert payload and max(payload) <= chunk * 2               # int16 CT is the widest file
    assert sum(payload) >= N * 2 + N * 1                        # every declared byte was read
    assert len(payload) >= 2 * math.ceil(N / chunk)             # lockstep chunks, not one slurp
    drains = [n for kind, n in reads if kind == 'read']
    assert all(0 < n <= 1024 * 1024 for n in drains)            # gzip drain is bounded too


@pytest.mark.component
def test_chunk_size_does_not_change_measurements(tmp_path):
    rng = np.random.default_rng(7)
    ct = rng.normal(40, 300, SHAPE).astype(np.float32)
    ct[0, 0, 0] = np.nan
    m = rng.integers(0, 4, SHAPE).astype(np.uint8)
    write_nifti(tmp_path / 'ct.nii.gz', ct, slope=1.25, inter=-7.0)
    write_nifti(tmp_path / 'm.nii', m)
    results = []
    for working in (500, 4000, 256 * 1024**2):
        r = pair(tmp_path, 'ct.nii.gz', 'm.nii', expected_values=[0, 1, 2], limits=Limits(working_bytes=working))
        for role in ('ct', 'mask'):
            r[role].pop('limits')
        results.append(r)
    w0 = results[0].pop('within_mask_ct')
    for other in results[1:]:
        w = other.pop('within_mask_ct')
        assert w['ct_mean'] == pytest.approx(w0['ct_mean'], rel=1e-12)
        assert {k: v for k, v in w.items() if k != 'ct_mean'} == {k: v for k, v in w0.items() if k != 'ct_mean'}
        assert other == results[0]


@pytest.mark.component
def test_traced_memory_stays_within_working_budget(tmp_path):
    # Adversarial for the accounting: float64, scaled, every value distinct, some non-finite.
    rng = np.random.default_rng(3)
    shape = (64, 64, 40)
    data = rng.random(shape) * 1e6
    data[::5] = np.nan
    write_nifti(tmp_path / 'ct.nii', data, slope=2.0, inter=1.0)
    write_nifti(tmp_path / 'm.nii', data, slope=2.0, inter=1.0)
    budget = 4 * 1024**2
    fixed = 2 * 1024**2        # adapter's 1 MiB hashing reads, gzip/drain buffers, headers
    tracemalloc.start()
    try:
        base = tracemalloc.get_traced_memory()[0]
        r = pair(tmp_path, 'ct.nii', 'm.nii', limits=Limits(working_bytes=budget))
        peak = tracemalloc.get_traced_memory()[1] - base
    finally:
        tracemalloc.stop()
    assert r['within_mask_ct'] is not None
    assert r['ct']['limits']['chunk_voxels'] < data.size / 2   # several chunks were needed
    assert peak <= budget + fixed


@pytest.mark.unit
def test_working_budget_below_one_voxel_stops(tmp_path):
    write_nifti(tmp_path / 'ct.nii', ct_array())
    assert stop_code(vol(tmp_path, 'ct.nii', role='ct', limits=Limits(working_bytes=10))) == 'limit_exceeded'


# --- 10. inputs unchanged, determinism, mutation ---------------------------------------------

def fingerprint(path):
    info = path.stat()
    return hashlib.sha256(path.read_bytes()).hexdigest(), info.st_size, info.st_mtime_ns


@pytest.mark.contract
def test_inputs_unchanged_and_output_deterministic(tmp_path):
    ct, m = write_nifti(tmp_path / 'ct.nii.gz', ct_array()), write_nifti(tmp_path / 'm.nii', mask_array(POINTS))
    before = {p.name: fingerprint(p) for p in (ct, m)}
    header_before = nib.load(ct).header.binaryblock
    first = pair(tmp_path, 'ct.nii.gz', 'm.nii', expected_values=[0, 1])
    second = pair(tmp_path, 'ct.nii.gz', 'm.nii', expected_values=[0, 1])
    assert json.dumps(first, sort_keys=True, allow_nan=False) == json.dumps(second, sort_keys=True, allow_nan=False)
    assert {p.name: fingerprint(p) for p in (ct, m)} == before
    assert nib.load(ct).header.binaryblock == header_before
    assert sorted(p.name for p in tmp_path.iterdir()) == ['ct.nii.gz', 'm.nii']
    assert first['ct']['file']['content_sha256'] == before['ct.nii.gz'][0]


@pytest.mark.failure_injection
def test_file_modified_during_read_is_rejected(tmp_path, monkeypatch):
    path = write_nifti(tmp_path / 'ct.nii', ct_array())
    real_open = av._open_payload

    def touching_open(p):
        raw, stream = real_open(p)
        os.utime(path, ns=(1, 1))                       # metadata change after the hash
        return raw, stream

    monkeypatch.setattr(av, '_open_payload', touching_open)
    assert stop_code(vol(tmp_path, 'ct.nii', role='ct')) == 'file_mutated'


@pytest.mark.failure_injection
def test_file_replaced_during_read_is_rejected(tmp_path, monkeypatch):
    path = write_nifti(tmp_path / 'ct.nii', ct_array())
    write_nifti(tmp_path / 'other.nii', ct_array())
    real_open = av._open_payload
    state = {'swapped': False}

    class Swapper:
        def __init__(self, inner):
            self.inner = inner

        def readinto(self, view):
            if not state['swapped']:
                os.replace(tmp_path / 'other.nii', path)
                state['swapped'] = True
            return self.inner.readinto(view)

        def __getattr__(self, name):
            return getattr(self.inner, name)

    monkeypatch.setattr(av, '_open_payload', lambda p: (lambda r, s: (r, Swapper(s)))(*real_open(p)))
    assert stop_code(vol(tmp_path, 'ct.nii', role='ct')) == 'file_mutated'


@pytest.mark.failure_injection
@pytest.mark.parametrize('error', [OSError, RuntimeError, ValueError])
def test_root_check_failure_after_read_is_a_coded_stop(tmp_path, error):
    write_nifti(tmp_path / 'ct.nii', ct_array())
    calls = []

    def check_root():
        calls.append(1)
        if len(calls) > 3:                             # passes during evidence, fails at finish
            raise error('volume went away')

    assert stop_code(vol(tmp_path, 'ct.nii', role='ct', check_root=check_root)) == 'root_check_failed'


# --- output contract ---------------------------------------------------------------------------

FORBIDDEN_KEYS = {'diagnosis', 'eligible', 'excluded', 'exclusion', 'has_lesion', 'label_map',
                  'lesion_negative', 'split'}


def all_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from all_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from all_keys(item)


@pytest.mark.contract
def test_output_is_strict_json_without_paths_or_eligibility_claims(tmp_path):
    m = np.zeros(SHAPE, np.float32)
    m[POINTS[0]] = np.nan
    write_nifti(tmp_path / 'ct.nii', ct_array())
    write_nifti(tmp_path / 'm.nii.gz', m)
    r = pair(tmp_path, 'ct.nii', 'm.nii.gz', expected_values=[0, 1])
    text = json.dumps(r, allow_nan=False)
    assert str(tmp_path) not in text and str(tmp_path.resolve()) not in text
    assert r['eligibility'] == r['ct']['eligibility'] == r['mask']['eligibility'] == 'not_assessed'
    assert not FORBIDDEN_KEYS & set(all_keys(r))


@pytest.mark.contract
def test_stopped_and_measured_records_share_one_key_set(tmp_path):
    write_nifti(tmp_path / 'good.nii', mask_array(POINTS))
    write_nifti(tmp_path / 'bad.nii', mask_array(POINTS), cut=5)
    good, bad = vol(tmp_path, 'good.nii', role='mask'), vol(tmp_path, 'bad.nii', role='mask')
    assert set(good) == set(bad) and bad['voxels'] is None and bad['mask'] is None


@pytest.mark.contract
def test_cli_runs_only_the_fixture_demo():
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    module = 'scripts.diagnostics.audit_voxels'
    refused = subprocess.run([sys.executable, '-m', module, '/Volumes/anything'], cwd=REPO, env=env,
                             capture_output=True, text=True, timeout=120)
    assert refused.returncode == 2 and 'not runnable' in refused.stderr
    demo = subprocess.run([sys.executable, '-m', module, '--demo'], cwd=REPO, env=env,
                          capture_output=True, text=True, timeout=120)
    assert demo.returncode == 0, demo.stderr
    report = json.loads(demo.stdout)
    assert report['grid']['compatible'] is True and report['mask']['mask']['nonzero_voxels'] == 8


@pytest.mark.failure_injection
@pytest.mark.parametrize('partner', ['ct', 'mask'])
@pytest.mark.parametrize('code', ['root_check_failed', 'corrupt_payload', 'file_mutated'])
def test_final_integrity_failure_withholds_pair_results(tmp_path, monkeypatch, partner, code):
    write_nifti(tmp_path / 'ct.nii', ct_array())
    write_nifti(tmp_path / 'mask.nii', mask_array(POINTS), units='unknown')
    original = av._Reader.finish
    def failing_finish(self, check_root):
        original(self, check_root)
        if self.path.name == partner + '.nii':
            raise av.AuditStop(code, 'injected late failure')
    monkeypatch.setattr(av._Reader, 'finish', failing_finish)
    r = pair(tmp_path, 'ct.nii', 'mask.nii', study_ids=(STUDY, STUDY))
    assert stop_code(r[partner]) == code
    assert r['within_mask_ct'] is None
    assert r['within_mask_unavailable_reason']
    assert r['unit_interpretation'] is None
    if partner == 'ct':
        assert r['mask']['status'] == 'measured'
        assert r['mask']['mask']['nonzero_voxels'] == 7
        assert r['mask']['mask']['volume']['available'] is False


@pytest.mark.failure_injection
@pytest.mark.parametrize('fail_at', [7, 8])
def test_final_root_callback_failure_withholds_pair(tmp_path, fail_at):
    write_nifti(tmp_path / 'ct.nii', ct_array())
    write_nifti(tmp_path / 'mask.nii', mask_array(POINTS))
    calls = []
    def check():
        calls.append(1)
        if len(calls) == fail_at:
            raise RuntimeError('injected root loss')
    r = pair(tmp_path, 'ct.nii', 'mask.nii', check_root=check)
    assert r['within_mask_ct'] is None
    assert stop_code(r['ct' if fail_at == 7 else 'mask']) == 'root_check_failed'


@pytest.mark.unit
@pytest.mark.parametrize('paired', [False, True])
@pytest.mark.parametrize('fault', ['different_scale', 'different_origin', 'uncoded'])
def test_ambiguous_geometry_withholds_volume(tmp_path, paired, fault):
    options = {'qform': affine_for(spacing=(1.5, .875, 2.5))}
    if fault == 'different_origin':
        options = {'qform': affine_for(shift=(10, 0, 0))}
    if fault == 'uncoded':
        options = {'qcode': 0, 'scode': 0}
    write_nifti(tmp_path / 'mask.nii', mask_array(POINTS), **options)
    if paired:
        write_nifti(tmp_path / 'ct.nii', ct_array())
        r = pair(tmp_path, 'ct.nii', 'mask.nii')['mask']
    else:
        r = vol(tmp_path, 'mask.nii', role='mask')
    assert r['mask']['nonzero_voxels'] == 7
    assert r['mask']['volume']['available'] is False
    assert r['mask']['volume']['mm3'] is None
    assert 'ambiguous_geometry' in r['mask']['volume']['reason']


@pytest.mark.unit
def test_demo_resolves_temporary_directory_alias(tmp_path, monkeypatch):
    real = tmp_path / 'real'
    real.mkdir()
    alias = tmp_path / 'alias'
    alias.symlink_to(real, target_is_directory=True)
    class AliasTemporaryDirectory:
        def __enter__(self): return str(alias)
        def __exit__(self, *args): pass
    monkeypatch.setattr(av.tempfile, 'TemporaryDirectory', AliasTemporaryDirectory)
    r = av.demo()
    assert r['grid']['compatible']
    assert r['mask']['mask']['nonzero_voxels'] == 8
