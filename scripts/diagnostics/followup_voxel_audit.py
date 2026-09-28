"""One bounded, preselected diagnostic audit. Not the Plan 04 workflow runner.

Run with --run from the repository's supported Python environment. Source reads only;
new ignored output package, no cohort/eligibility decisions or production root activation.
"""
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from uuid import uuid4

import yaml

from scripts.acquisition.download_pants import mounted
from scripts.diagnostics.audit_voxels import audit_pair, Limits, AUDIT_VERSION
from src.data.manifest_records import canonical, digest
from src.data.pants_metadata import read_metadata
from src.data.protected_identity import accepted_pants_members, pants_identity
from src.data.source_evidence import resolve_file, identity

REPO = Path(__file__).resolve().parents[2]
INVENTORY_SHA = 'b8f561d2fdf7506673f6e29da75c6c879b96dae0ba7cb88add9f1649caca25e5'
EXPECTED = ['PanTS_00000003', 'PanTS_00000026', 'PanTS_00000031',
            'PanTS_00000078', 'PanTS_00000266']
EXTRAS = {'PanTS_00000078': 'liver', 'PanTS_00000266': 'lung_left'}
MAX_REPORT = 1024**2
MAX_OUTPUT = 20 * 1024**2


def select_cases(train, metadata, flags):
    if len(train) != len(set(train)) or len(flags) != len({f['case'] for f in flags}):
        raise ValueError('Duplicate input identity')
    for raw in train:
        if pants_identity(raw).source_partition != 'publisher_train':
            raise ValueError('Non-training identity')
        if raw not in metadata:
            raise ValueError('Missing metadata')
    positive = sorted(i for i in train if metadata[i]['source_tumor_status'] == 'positive')[:3]
    flagged = sorted(f['case'] for f in flags if f['case'] in train and f['case'] not in positive)[:2]
    if len(positive) != 3 or len(flagged) != 2:
        raise ValueError('Selection shortage; no substitution')
    return positive + flagged


def pair_plan(ids):
    if ids != EXPECTED:
        raise ValueError('Selection differs from approved bounded plan')
    pairs = []
    for raw in ids:
        structures = ['pancreas', 'pancreatic_lesion'] + ([EXTRAS[raw]] if raw in EXTRAS else [])
        for structure in structures:
            pairs.append(dict(study=raw, structure=structure,
                              ct=f'PanTSMini_ImageTr_00000001_00001000/{raw}/ct.nii.gz',
                              mask=f'PanTSMini_Label/{raw}/segmentations/{structure}.nii.gz'))
    return pairs


class Package:
    def __init__(self, path, max_bytes=MAX_OUTPUT):
        self.path, self.max_bytes, self.used = path, max_bytes, 0
        if path.parent.resolve(strict=True) != path.parent:
            raise ValueError('Noncanonical output parent')
        path.mkdir(exist_ok=False)
        self.hashes = {}

    def write(self, name, value):
        if Path(name).name != name or not name.endswith('.json'):
            raise ValueError('Unsafe artifact name')
        payload = canonical(value)
        if self.used + len(payload) > self.max_bytes:
            raise ValueError('Output budget exceeded')
        with (self.path / name).open('xb') as stream:
            stream.write(payload)
        self.used += len(payload)
        self.hashes[name] = digest(payload)


def child(command, request, timeout):
    if timeout <= 0:
        raise TimeoutError('Overall deadline exceeded')
    # Only our fixed worker command is used in production. It caps its own serialized
    # response before stdout. subprocess.run kills/reaps it on timeout; no child jobs.
    result = subprocess.run(command, input=canonical(request), capture_output=True,
                            timeout=timeout, cwd=REPO)
    if result.returncode:
        raise RuntimeError('Audit worker failed; exit=' + str(result.returncode))
    if len(result.stdout) > MAX_REPORT:
        raise ValueError('Worker response exceeds cap')
    return json.loads(result.stdout)


def worker(request):
    mount = Path(request['mount'])
    def check():
        mounted(mount, request['uuid'], request['device'])
    check()
    root = Path(request['root'])
    if not root.is_relative_to(mount):
        raise ValueError('Source not on expected mount')
    roots = {'followup_source': root}
    for uri, before in request['identities'].items():
        if list(identity(resolve_file(roots, 'followup_source', uri).stat())) != before:
            raise ValueError('Preflight source identity changed')
    pair = request['pair']
    study = pants_identity(pair['study']).study_id
    report = audit_pair(roots, ct=('followup_source', pair['ct']),
                        mask=('followup_source', pair['mask']), study_ids=(study, study),
                        expected_values=None, limits=Limits(), check_root=check)
    for uri, before in request['identities'].items():
        if list(identity(resolve_file(roots, 'followup_source', uri).stat())) != before:
            raise ValueError('Preflight source identity changed')
    payload = canonical(report)
    if len(payload) > MAX_REPORT:
        raise ValueError('Report cap exceeded')
    sys.stdout.buffer.write(payload)


def execute(package, pairs, request_base, identities, run_child=child, seconds=900):
    deadline = time.monotonic() + seconds
    hashes = {}
    summaries = []
    try:
        for index, pair in enumerate(pairs):
            start = time.monotonic()
            request = dict(request_base, pair=pair,
                           identities={uri: identities[uri] for uri in (pair['ct'], pair['mask'])})
            report = run_child([sys.executable, '-m', 'scripts.diagnostics.followup_voxel_audit', '--worker'],
                               request, min(120, deadline - start))
            if time.monotonic() > deadline:
                raise TimeoutError('Overall deadline exceeded')
            # Preserve stopped reports before withholding the successful receipt.
            package.write(f'pair-{index:02d}.json', report)
            for role in ('ct', 'mask'):
                record = report[role]
                if record['status'] != 'measured':
                    raise ValueError('Audit stopped: ' + str(record.get('stop')))
                if record['file']['uri'] != pair[role]:
                    raise ValueError('Worker returned different file')
                sha = record['file']['content_sha256']
                if hashes.setdefault(pair[role], sha) != sha:
                    raise ValueError('Repeated source hash changed')
            summary = dict(study=pair['study'], structure=pair['structure'],
                           elapsed_seconds=round(time.monotonic()-start, 3),
                           grid=report['grid'], mask=report['mask']['mask'],
                           ct_nonfinite=report['ct']['voxels']['nonfinite'],
                           mask_nonfinite=report['mask']['voxels']['nonfinite'])
            summaries.append(summary)
            print(json.dumps(summary), flush=True)
        package.write('receipt.json', dict(status='complete', eligibility='not_assessed',
                      files=dict(package.hashes), source_hashes=hashes, summaries=summaries))
    except Exception as exc:
        # Leave space reserved by report/selection limits; no success receipt on failure.
        package.write('failure.json', dict(status='stopped', error_type=type(exc).__name__,
                      completed_pairs=len(summaries), files=dict(package.hashes)))
        raise


def main():
    started = time.monotonic()
    registry = yaml.safe_load((REPO / 'configs/local/roots.yaml').read_text())
    primary = registry['failure_domains']['external_primary']
    mount = Path(primary['mount_path']); device = mounted(mount, primary['volume_uuid'])
    inv_raw = (REPO / 'outputs/prowl/inventory-2026-09-27/full-v4.json').read_bytes()
    if digest(inv_raw) != INVENTORY_SHA:
        raise ValueError('Inventory changed')
    flags = next(s for s in json.loads(inv_raw)['sources'] if s['source']=='pants-labels')['size_populations']['structure_specific']['sample']
    acquisition = json.loads((REPO / 'docs/capstone/data/acquisition-2026-09-19.json').read_bytes())['pants']
    pin = next(f for f in acquisition['files'] if f['name']=='metadata.xlsx')
    source_parent = Path(registry['roots']['pants_source']['acquisition_parent'])
    if not source_parent.is_relative_to(mount) or source_parent.resolve(strict=True) != source_parent:
        raise ValueError('Expected source parent')
    metadata = read_metadata((source_parent / 'acquisition-3b1cd6110811/metadata.xlsx').read_bytes(), pin['sha256'])
    train_raw = (REPO / 'outputs/splits/train.txt').read_bytes()
    train = [i.study_id.split(':')[-1] for i in accepted_pants_members(train_raw, 'train')]
    ids = select_cases(train, metadata, flags)
    pairs = pair_plan(ids)
    for raw, structure in EXTRAS.items():
        flag = next(f for f in flags if f['case']==raw)
        if flag['structures'] != [structure + '.nii.gz']:
            raise ValueError('Flag reason changed')
    root = source_parent / 'extraction-3b1cd6110811-20260922'
    identities = {uri:list(identity(resolve_file({'followup_source':root}, 'followup_source', uri).stat()))
                  for uri in sorted({p[r] for p in pairs for r in ('ct','mask')})}
    mounted(mount, primary['volume_uuid'], device)
    parent = REPO / 'outputs/prowl'
    if shutil.disk_usage(parent).free < 100 * 1024**3:
        raise ValueError('Internal free space below 100 GiB floor')
    package = Package(parent / ('voxel-followup-' + str(uuid4())))
    code_paths = [Path(__file__), REPO/'scripts/diagnostics/audit_voxels.py',
                  REPO/'src/data/source_evidence.py', REPO/'src/data/protected_identity.py',
                  REPO/'src/data/pants_metadata.py', REPO/'src/data/manifest_records.py',
                  REPO/'scripts/acquisition/download_pants.py']
    selection = dict(created_at=datetime.now(timezone.utc).isoformat(), ids=ids, pairs=pairs,
                     reasons={i:dict(source_tumor_status=metadata[i]['source_tumor_status'],
                                     metadata_row=metadata[i]['evidence']['row'],
                                     selection='positive_source_flag' if i not in EXTRAS else 'retained_size_flag',
                                     flagged_structure=EXTRAS.get(i)) for i in ids},
                     train_sha256=digest(train_raw), metadata_sha256=pin['sha256'], inventory_sha256=INVENTORY_SHA,
                     stat_identities=identities, audit_version=AUDIT_VERSION,
                     limits=asdict(Limits()), pair_seconds=120, overall_seconds=900, output_bytes=MAX_OUTPUT,
                     code_hashes={str(p.relative_to(REPO)):digest(p.read_bytes()) for p in code_paths})
    if len(canonical(selection)) > MAX_REPORT:
        raise ValueError('Selection cap exceeded')
    package.write('selection.json', selection)
    print('Evidence package: ' + str(package.path.relative_to(REPO)), flush=True)
    execute(package, pairs, dict(mount=str(mount), uuid=primary['volume_uuid'], device=device, root=str(root)),
            identities, seconds=900-(time.monotonic()-started))


if __name__ == '__main__':
    if sys.argv[1:] == ['--worker']:
        worker(json.loads(sys.stdin.buffer.read(MAX_REPORT)))
    elif sys.argv[1:] == ['--run']:
        main()
    else:
        raise SystemExit('Use --run for the fixed five-case follow-up')
