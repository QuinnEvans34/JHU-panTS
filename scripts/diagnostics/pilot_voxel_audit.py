"""Explicit two-case diagnostic pilot; no discovery, training or eligibility decisions.

Requires --package pointing to a prior local diagnostic manifest evidence package.
Writes a new ignored evidence directory; never modifies sources or prior packages.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from uuid import uuid4

import yaml

from scripts.acquisition.download_pants import mounted
from scripts.diagnostics.audit_voxels import audit_pair, AUDIT_VERSION, Limits
from src.data.manifest_records import canonical, digest
from src.data.protected_identity import accepted_pants_members, pants_identity

REPO = Path(__file__).resolve().parents[2]
SELECTED = ['PanTS_00000001', 'PanTS_00000002']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    args = parser.parse_args()
    parent = REPO / 'outputs/prowl'
    package = args.package.resolve(strict=True)
    if not package.is_relative_to(parent.resolve(strict=True)):
        raise ValueError('Use an existing local diagnostic package')
    verification = json.loads((package / 'verification.json').read_bytes())
    for name in ('measurements.json', 'metadata.json', 'config.json'):
        if digest((package / name).read_bytes()) != verification['files'][name]:
            raise ValueError('Prior evidence hash mismatch')
    measured = json.loads((package / 'measurements.json').read_bytes())
    metadata = json.loads((package / 'metadata.json').read_bytes())
    config = json.loads((package / 'config.json').read_bytes())
    train = (REPO / 'outputs/splits/train.txt').read_bytes()
    approved = {i.study_id for i in accepted_pants_members(train, 'train')}
    if (sorted(measured) != SELECTED or sorted(r['source_study_id'] for r in metadata) != SELECTED
            or config['selected_ids'] != SELECTED or config['train_membership_sha256'] != digest(train)):
        raise ValueError('Pilot selection or metadata join changed')
    registry = yaml.safe_load((REPO / 'configs/local/roots.yaml').read_text())
    primary = registry['failure_domains']['external_primary']
    mount = Path(primary['mount_path'])
    device = mounted(mount, primary['volume_uuid'])
    def check():
        mounted(mount, primary['volume_uuid'], device)
    acquisition = Path(registry['roots']['pants_source']['acquisition_parent'])
    extraction = acquisition / 'extraction-3b1cd6110811-20260922'
    if not extraction.is_relative_to(mount) or extraction.resolve(strict=True) != extraction:
        raise ValueError('Expected canonical on-volume extraction root')
    destination = parent / ('voxel-pilot-' + str(uuid4()))
    if parent.resolve() != parent:
        raise ValueError('Noncanonical output parent')
    destination.mkdir(exist_ok=False)
    summaries = []
    for raw_id in SELECTED:
        identity = pants_identity(raw_id)
        if identity.study_id not in approved:
            raise ValueError('Study not in approved training membership')
        for structure in ('pancreas', 'lesion'):
            evidence = measured[raw_id]
            ct, mask = evidence['ct']['file'], evidence[structure]['file']
            if ct['root_alias'] != 'pants_slice' or mask['root_alias'] != 'pants_slice':
                raise ValueError('Unexpected diagnostic alias')
            start = time.monotonic()
            report = audit_pair({'pants_slice': extraction},
                                ct=('pants_slice', ct['uri']), mask=('pants_slice', mask['uri']),
                                study_ids=(identity.study_id, identity.study_id),
                                expected_values=None, limits=Limits(), check_root=check)
            for role, prior in (('ct', ct), ('mask', mask)):
                if report[role]['file'].get('content_sha256') != prior['content_sha256']:
                    raise ValueError('Pilot bytes differ from verified prior evidence')
            filename = raw_id + '-' + structure + '.json'
            with (destination / filename).open('xb') as stream:
                stream.write(canonical(report))
            if report['ct']['status'] != 'measured' or report['mask']['status'] != 'measured':
                raise RuntimeError('Audit stopped; report preserved, no completion receipt')
            summary = dict(study=raw_id, structure=structure, seconds=round(time.monotonic()-start, 3),
                           grid=report['grid'], mask=report['mask']['mask'],
                           nonfinite=report['mask']['voxels']['nonfinite'])
            summaries.append(summary)
            print(json.dumps(summary), flush=True)
    receipt = dict(created_at=datetime.now(timezone.utc).isoformat(), audit_version=AUDIT_VERSION,
                   audit_code_sha256=digest((REPO / 'scripts/diagnostics/audit_voxels.py').read_bytes()),
                   prior_package=str(package.relative_to(REPO)), expected_values_policy=None,
                   eligibility='not_assessed', summaries=summaries,
                   files={p.name:digest(p.read_bytes()) for p in sorted(destination.iterdir())})
    with (destination / 'receipt.json').open('xb') as stream:
        stream.write(canonical(receipt))
    print('Evidence package: ' + str(destination.relative_to(REPO)), flush=True)


if __name__ == '__main__':
    main()
