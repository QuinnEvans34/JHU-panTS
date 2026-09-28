from copy import deepcopy
import json

import pytest

from scripts.diagnostics.build_manifest_slice import records, publish
from src.data.manifest_records import CONTRACTS, assemble_manifest, digest

pytestmark = pytest.mark.unit


def fixture():
    example = lambda n: json.loads((CONTRACTS / 'examples' / (n + '.example.json')).read_bytes())
    snapshot = example('source-snapshot')
    image = example('study-record')['image']
    measured = {'PanTS_00000001': {k: dict(file=deepcopy(image), geometry=None,
                 issue_codes=['unknown_spatial_units']) for k in ('ct', 'pancreas', 'lesion')}}
    metadata = [dict(source_study_id='PanTS_00000001', source_tumor_status='negative')]
    args = dict(name='diagnostic', created_at='2026-09-28T00:00:00Z',
                build=example('manifest')['build'], snapshots=[snapshot])
    args.update(records(metadata, measured, snapshot['source_snapshot_id'], args['created_at']))
    return args, measured


def test_no_guessed_annotation_or_negative_target():
    args, _ = fixture()
    assert args['annotations'] == []
    assert args['studies'][0]['target_statuses'][0]['status'] == 'unknown'
    result = json.loads(assemble_manifest(**args)['manifest.json'])
    assert result['status'] == 'quarantined'
    assert result['reconciliation']['eligible'] == 0
    assert result['reconciliation']['blocking_issue_count'] == 5


def test_persisted_replay_and_hashes(tmp_path):
    args, measured = fixture()
    before = deepcopy(args)
    destination = tmp_path / 'new'
    publish(destination, args, {'measurements.json': measured})
    replay = assemble_manifest(**json.loads((destination / 'assembly-inputs.json').read_bytes()))
    assert all((destination / name).read_bytes() == value for name, value in replay.items())
    receipt = json.loads((destination / 'verification.json').read_bytes())
    assert receipt['replay_equal']
    assert all(digest((destination / name).read_bytes()) == sha for name, sha in receipt['files'].items())
    assert args == before


def test_existing_package_never_overwritten(tmp_path):
    args, measured = fixture()
    destination = tmp_path / 'new'
    publish(destination, args, {'measurements.json': measured})
    before = {p.name: p.read_bytes() for p in destination.iterdir()}
    with pytest.raises(FileExistsError):
        publish(destination, args, {})
    assert before == {p.name: p.read_bytes() for p in destination.iterdir()}


@pytest.mark.parametrize('filename', ['../escape.json', 'manifest.json'])
def test_unsafe_or_colliding_evidence_rejected(tmp_path, filename):
    args, _ = fixture()
    with pytest.raises(ValueError):
        publish(tmp_path / 'new', args, {filename: {}})
    assert not (tmp_path / 'new/verification.json').exists()


def test_publisher_test_not_admitted():
    with pytest.raises(ValueError, match='training'):
        records([dict(source_study_id='PanTS_00009001')], {}, 'unused', 'unused')


def test_unit_findings_preserved_not_repaired():
    args, _ = fixture()
    findings = [i for i in args['issues'] if i['rule_code'] == 'UNKNOWN_SPATIAL_UNITS']
    assert len(findings) == 3
    assert all(i['disposition'] == 'quarantine' for i in findings)
    assert args['studies'][0]['geometry'] is None
