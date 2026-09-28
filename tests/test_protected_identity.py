import pytest

from src.data.protected_identity import (
    accepted_pants_members, pants_identity, panorama_identity,
    panorama_ct_study, validate_role_assignments,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize('raw', ['PanTS_00000000', 'PanTS_00009902', '../PanTS_00000001',
                                  'PanTS_1', 'PanTS_00000001 ', None])
def test_pants_invalid_ids_fail(raw):
    with pytest.raises(ValueError):
        pants_identity(raw)


def test_pants_boundary_and_honest_fallback():
    assert pants_identity('PanTS_00009000').source_partition == 'publisher_train'
    identity = pants_identity('PanTS_00009001')
    assert identity.source_partition == 'publisher_test'
    assert identity.identity_assurance == 'unverified_unique'


@pytest.mark.parametrize('role', ['train', 'validation'])
def test_test_partition_cannot_be_development(role):
    with pytest.raises(ValueError, match='Publisher test'):
        validate_role_assignments([(pants_identity('PanTS_00009001'), role)])


def test_duplicate_rows_are_not_silently_deduplicated():
    row = (pants_identity('PanTS_00000001'), 'train')
    with pytest.raises(ValueError, match='Duplicate'):
        validate_role_assignments([row, row])


def test_repeated_patient_must_stay_in_one_role():
    a = panorama_identity('100000_00001', '100000')
    b = panorama_identity('100000_00002', '100000')
    assert validate_role_assignments([(a, 'train'), (b, 'train')])['train'] == 2
    with pytest.raises(ValueError, match='Subject crosses'):
        validate_role_assignments([(a, 'train'), (b, 'validation')])


def test_panorama_patient_identity_comes_from_explicit_metadata():
    assert panorama_identity('100000_00001', '100001').subject_id == 'panorama:subject:100001'
    with pytest.raises(ValueError, match='Explicit'):
        panorama_identity('100000_00001', None)


@pytest.mark.parametrize('name', ['100000_00001_0001.nii.gz', '100000_00001.nii.gz',
                                   '../100000_00001_0000.nii.gz'])
def test_unreviewed_channels_and_paths_fail(name):
    with pytest.raises(ValueError):
        panorama_ct_study(name)


def test_pinned_channel_join():
    assert panorama_ct_study('100000_00001_0000.nii.gz') == '100000_00001'


@pytest.mark.parametrize('role', ['train', 'validation', 'test', 'development'])
def test_arbitrary_legacy_input_denied(role):
    with pytest.raises(ValueError):
        accepted_pants_members(b'PanTS_00000001\n', role)
