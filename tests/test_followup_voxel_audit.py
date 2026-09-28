import json
import subprocess
import sys

import pytest

from scripts.diagnostics.followup_voxel_audit import (
    EXPECTED, Package, child, execute, pair_plan, select_cases,
)

pytestmark = pytest.mark.unit


def inputs():
    train = EXPECTED.copy()
    meta = {i:dict(source_tumor_status='positive' if n<3 else 'negative') for n,i in enumerate(train)}
    flags = [dict(case=i) for i in train[3:]]
    return train, meta, flags


def test_exact_selection_and_paths():
    train, meta, flags = inputs()
    selected = select_cases(list(reversed(train)), meta, list(reversed(flags)))
    assert selected == EXPECTED
    pairs = pair_plan(selected)
    assert len(pairs) == 12
    assert len({p[r] for p in pairs for r in ('ct','mask')}) == 17
    assert pairs[-1]['mask'].endswith('PanTS_00000266/segmentations/lung_left.nii.gz')


@pytest.mark.parametrize('fault', ['duplicate_train','duplicate_flag','missing_metadata','test','shortage'])
def test_bad_selection_rejected(fault):
    train, meta, flags = inputs()
    if fault == 'duplicate_train': train.append(train[0])
    if fault == 'duplicate_flag': flags.append(flags[0])
    if fault == 'missing_metadata': del meta[train[0]]
    if fault == 'test': train.append('PanTS_00009001')
    if fault == 'shortage': flags.pop()
    with pytest.raises(ValueError): select_cases(train, meta, flags)


def test_validation_not_selected():
    train, meta, flags = inputs()
    meta['PanTS_00000001'] = dict(source_tumor_status='positive')
    flags.insert(0, dict(case='PanTS_00000001'))
    assert select_cases(train, meta, flags) == EXPECTED
    with pytest.raises(ValueError): pair_plan(EXPECTED[:-1])


def test_package_refuses_overwrite_and_budget(tmp_path):
    path = tmp_path.resolve()/'new'
    p = Package(path, max_bytes=30)
    p.write('one.json', {})
    with pytest.raises(FileExistsError): p.write('one.json', {})
    with pytest.raises(FileExistsError): Package(path)
    with pytest.raises(ValueError): p.write('../bad.json', {})
    with pytest.raises(ValueError): p.write('large.json', 'x'*40)
    assert (path/'one.json').read_bytes() == b'{}\n'
    assert not (path/'large.json').exists()


def test_actual_subprocess_timeout():
    with pytest.raises(subprocess.TimeoutExpired):
        child([sys.executable,'-c','import time; time.sleep(10)'], {}, .05)
    with pytest.raises(TimeoutError): child([], {}, 0)


@pytest.mark.parametrize('failure', ['timeout','stopped','changed_hash','deadline'])
def test_execution_failure_no_success_receipt(tmp_path, failure):
    p = Package(tmp_path.resolve()/'new')
    pair = dict(study='synthetic',structure='pancreas',ct='ct.nii',mask='mask.nii')
    calls = []
    def fake(command, request, timeout):
        calls.append(1)
        if failure == 'timeout': raise subprocess.TimeoutExpired(command, timeout)
        records = {role:dict(status='measured',file=dict(uri=pair[role],content_sha256='a'*64),
                            voxels=dict(nonfinite={})) for role in ('ct','mask')}
        records['mask']['mask'] = {}
        if failure == 'stopped': records['mask'].update(status='stopped', stop={'code':'corrupt_payload'})
        if failure == 'changed_hash' and len(calls)>1:
            records['ct']['file']['content_sha256'] = 'b'*64
        return dict(records, grid={})
    if failure == 'deadline':
        # The real child refuses a nonpositive remaining deadline before launching.
        fake = child
    with pytest.raises((ValueError, subprocess.TimeoutExpired, TimeoutError)):
        execute(p, [pair,pair], {}, {'ct.nii':[], 'mask.nii':[]}, run_child=fake,
                seconds=-1 if failure=='deadline' else 10)
    assert (p.path/'failure.json').exists()
    assert not (p.path/'receipt.json').exists()


def test_success_hashes_preserved(tmp_path):
    p = Package(tmp_path.resolve()/'new')
    pair = dict(study='synthetic',structure='pancreas',ct='ct.nii',mask='mask.nii')
    def fake(*args):
        return dict(grid={},ct=dict(status='measured',file=dict(uri='ct.nii',content_sha256='a'*64),
                                   voxels=dict(nonfinite={})),
                    mask=dict(status='measured',file=dict(uri='mask.nii',content_sha256='b'*64),
                              voxels=dict(nonfinite={}),mask={}))
    execute(p,[pair],{}, {'ct.nii':[], 'mask.nii':[]},run_child=fake)
    receipt=json.loads((p.path/'receipt.json').read_bytes())
    assert receipt['status']=='complete' and receipt['source_hashes']['ct.nii']=='a'*64
    assert 'pair-00.json' in receipt['files']
