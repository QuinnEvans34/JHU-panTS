import hashlib

import nibabel as nib
import numpy as np
import pytest

from src.data.source_evidence import measure_nifti, resolve_file, evidence_issues, infer_mask_mm

pytestmark = pytest.mark.unit


def paired_evidence(tmp_path):
    fixture(tmp_path, 'mm')
    ct = measure_nifti({'sample_root': tmp_path}, 'sample_root', 'image.nii.gz')
    fixture(tmp_path, 'unknown')
    mask = measure_nifti({'sample_root': tmp_path}, 'sample_root', 'image.nii.gz')
    return mask, ct


def infer(mask, ct):
    return infer_mask_mm(mask, ct, mask_study_id='pants:study:PanTS_00000001',
                         ct_study_id='pants:study:PanTS_00000001')


def test_inference_preserves_original_and_links_hashes(tmp_path):
    mask, ct = paired_evidence(tmp_path)
    result = infer(mask, ct)
    assert result['geometry'] == ct['geometry']
    assert result['unit_interpretation']['ct_sha256'] == ct['file']['content_sha256']
    assert result['raw_header']['spatial_units'] == 'unknown'
    assert result['eligibility'] == 'not_assessed'
    assert mask['geometry'] is None and mask['issue_codes'] == ['unknown_spatial_units']


@pytest.mark.parametrize('fault', ['unknown_ct', 'shape', 'affine', 'transform', 'hash'])
def test_unsafe_unit_inference_rejected(tmp_path, fault):
    mask, ct = paired_evidence(tmp_path)
    if fault == 'unknown_ct': ct['raw_header']['spatial_units'] = 'unknown'
    if fault == 'shape': mask['raw_header']['shape'][0] += 1
    if fault == 'affine': mask['raw_header']['affine_native'][0][3] += 1
    if fault == 'transform': mask['raw_header']['sform_native'][0][3] += 1
    if fault == 'hash': mask['file']['content_sha256'] = ''
    with pytest.raises(ValueError): infer(mask, ct)


def test_different_study_pair_rejected(tmp_path):
    mask, ct = paired_evidence(tmp_path)
    with pytest.raises(ValueError, match='same-study'):
        infer_mask_mm(mask, ct, mask_study_id='pants:study:PanTS_00000002',
                      ct_study_id='pants:study:PanTS_00000001')


def fixture(tmp_path, unit='mm'):
    image = nib.Nifti1Image(np.zeros((3, 4, 5), dtype=np.int16), np.diag([1., 2., 3., 1.]))
    image.header.set_xyzt_units(unit)
    path = tmp_path / 'image.nii.gz'
    nib.save(image, path)
    return path


def test_measured_hash_and_geometry_without_voxel_access(tmp_path, monkeypatch):
    path = fixture(tmp_path)
    def forbidden(*args, **kwargs):
        raise AssertionError('Voxel loading is forbidden')
    monkeypatch.setattr(nib.arrayproxy.ArrayProxy, '__array__', forbidden)
    record = measure_nifti({'sample_root': tmp_path}, 'sample_root', path.name)
    assert record['file']['content_sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert record['file']['bytes'] == path.stat().st_size
    assert record['geometry']['shape_xyz'] == [3, 4, 5]
    assert record['geometry']['spacing_mm_xyz'] == [1., 2., 3.]
    assert record['eligibility'] == 'not_assessed'


@pytest.mark.parametrize('uri', ['../image.nii.gz', '/image.nii.gz', 'a\\b.nii.gz',
                                 'a/./b.nii.gz', 'a//b.nii.gz'])
def test_unsafe_paths_fail(tmp_path, uri):
    with pytest.raises(ValueError):
        resolve_file({'sample_root': tmp_path}, 'sample_root', uri)


def test_unapproved_root_fails(tmp_path):
    with pytest.raises(ValueError, match='Unapproved'):
        resolve_file({}, 'sample_root', 'image.nii.gz')


def test_symlink_refused(tmp_path):
    path = fixture(tmp_path)
    (tmp_path / 'link.nii.gz').symlink_to(path)
    with pytest.raises(ValueError, match='Symlink'):
        measure_nifti({'sample_root': tmp_path}, 'sample_root', 'link.nii.gz')


def test_unknown_units_are_unresolved(tmp_path):
    fixture(tmp_path, 'unknown')
    result = measure_nifti({'sample_root': tmp_path}, 'sample_root', 'image.nii.gz')
    assert result['geometry'] is None
    assert result['issue_codes'] == ['unknown_spatial_units']
    assert result['raw_header']['spacing_native'] == [1., 2., 3.]
    assert result['raw_header']['spatial_units'] == 'unknown'


def test_unresolved_evidence_creates_valid_blocking_issue(tmp_path):
    fixture(tmp_path, 'unknown')
    result = measure_nifti({'sample_root': tmp_path}, 'sample_root', 'image.nii.gz')
    records = evidence_issues(result, entity_type='study',
                              entity_id='pants:study:PanTS_00000001',
                              created_at='2026-09-28T00:00:00Z')
    assert len(records) == 1
    assert records[0]['disposition'] == 'quarantine'
    assert records[0]['severity'] == 'blocking'
    assert records[0]['evidence'][0]['reference'] == result['file']['content_sha256']


def test_meter_geometry_converts_to_mm(tmp_path):
    fixture(tmp_path, 'meter')
    result = measure_nifti({'sample_root': tmp_path}, 'sample_root', 'image.nii.gz')
    assert result['geometry']['spacing_mm_xyz'] == [1000., 2000., 3000.]


def test_changed_file_during_header_read_fails(tmp_path, monkeypatch):
    path = fixture(tmp_path)
    load = nib.load
    def changing(*args, **kwargs):
        image = load(*args, **kwargs)
        with path.open('ab') as stream:
            stream.write(b'changed')
        return image
    monkeypatch.setattr(nib, 'load', changing)
    with pytest.raises(ValueError, match='changed'):
        measure_nifti({'sample_root': tmp_path}, 'sample_root', path.name)
