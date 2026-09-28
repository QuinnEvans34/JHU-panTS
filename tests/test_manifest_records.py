import json
from copy import deepcopy

import pytest

from src.data.manifest_records import CONTRACTS, assemble_manifest

pytestmark = pytest.mark.unit


def example(name):
    return json.loads((CONTRACTS / 'examples' / f'{name}.example.json').read_text())


def inputs():
    study = example('study-record')
    # Historical example ID 9005 is in the pinned publisher-test range.
    study['source_partition'] = 'publisher_test'
    annotation = example('annotation-record')
    study['annotation_ids'] = [annotation['annotation_id']]
    return dict(name='synthetic', created_at='2026-09-28T00:00:00Z',
                build=example('manifest')['build'], snapshots=[example('source-snapshot')],
                subjects=[example('subject-record')], studies=[study],
                annotations=[annotation], issues=[])


def test_manifest_repeatability_and_counts():
    args = inputs()
    before = deepcopy(args)
    first = assemble_manifest(**args)
    assert first == assemble_manifest(**args)
    assert args == before
    control = json.loads(first['manifest.json'])
    assert control['records']['studies']['count'] == 1


@pytest.mark.parametrize('collection', ['subjects', 'studies', 'annotations'])
def test_duplicate_record_fails(collection):
    args = inputs()
    args[collection] *= 2
    with pytest.raises(ValueError, match='Duplicate'):
        assemble_manifest(**args)


def test_missing_subject_fails():
    args = inputs(); args['subjects'] = []
    with pytest.raises(ValueError, match='subject'):
        assemble_manifest(**args)


def test_partition_cannot_disguise_publisher_test():
    args = inputs(); args['studies'][0]['source_partition'] = 'publisher_train'
    with pytest.raises(ValueError, match='partition'):
        assemble_manifest(**args)


def test_missing_annotation_fails():
    args = inputs(); args['annotations'] = []
    with pytest.raises(ValueError, match='Annotation links'):
        assemble_manifest(**args)


def test_discovered_manifest_not_complete():
    args = inputs(); args['studies'][0].update(status='discovered', geometry=None)
    assert json.loads(assemble_manifest(**args)['manifest.json'])['status'] == 'quarantined'


def test_duplicate_target_fails():
    args = inputs(); args['studies'][0]['target_statuses'] *= 2
    with pytest.raises(ValueError, match='Duplicate target'):
        assemble_manifest(**args)


def test_backslash_path_fails():
    args = inputs(); args['studies'][0]['image']['uri'] = 'folder\\file.nii.gz'
    with pytest.raises(ValueError, match='Unsafe'):
        assemble_manifest(**args)


def test_dirty_build_requires_diff_hash():
    args = inputs(); args['build']['dirty'] = True
    with pytest.raises(ValueError, match='diff identity'):
        assemble_manifest(**args)


def test_timestamp_does_not_change_scientific_identity():
    args = inputs()
    first = json.loads(assemble_manifest(**args)['manifest.json'])
    args['created_at'] = '2026-09-29T00:00:00Z'
    second = json.loads(assemble_manifest(**args)['manifest.json'])
    assert first['manifest_id'] == second['manifest_id']


def test_snapshot_evidence_changes_derivation():
    args = inputs()
    first = json.loads(assemble_manifest(**args)['manifest.json'])
    args['snapshots'][0]['inventory']['content_sha256'] = 'f' * 64
    second = json.loads(assemble_manifest(**args)['manifest.json'])
    assert first['manifest_id'] != second['manifest_id']
