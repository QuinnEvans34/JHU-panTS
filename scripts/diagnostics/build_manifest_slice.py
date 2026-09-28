"""Bounded training-only evidence package; never a training/cohort publisher.

Run from repository root with python -m scripts.diagnostics.build_manifest_slice.
Mask evidence is retained but annotation records await verified label encoding.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from uuid import uuid4

import yaml

from scripts.acquisition.download_pants import mounted
from src.data.manifest_records import assemble_manifest, canonical, digest
from src.data.pants_metadata import read_metadata, join_studies
from src.data.protected_identity import accepted_pants_members, pants_identity
from src.data.source_evidence import measure_nifti, evidence_issues, infer_mask_mm

REPO = Path(__file__).resolve().parents[2]


def issue(entity, kind, code, message, reference, created_at):
    return dict(schema_version='1.0.0', issue_id='issue:' + str(uuid4()),
                rule_code=code, entity_type=kind, entity_id=entity,
                severity='blocking', disposition='quarantine', message=message,
                evidence=[dict(kind='validator_output', reference=reference)],
                created_at=created_at)


def records(metadata, measurements, snapshot_id, created_at):
    """Create issues once; persist these inputs before any repeat assembly."""
    subjects, studies, issues = [], [], []
    for row in metadata:
        raw_id = row['source_study_id']
        identity = pants_identity(raw_id)
        if identity.source_partition != 'publisher_train':
            raise ValueError('This diagnostic only supports publisher training cases')
        evidence = measurements[raw_id]
        pending = issue(identity.study_id, 'study', 'QUALIFICATION_PENDING',
                        'Voxel audit, annotation encoding/provenance and eligibility are not verified. '
                        'Mask evidence is retained separately; no annotation use is authorized.',
                        'measurements.json:' + raw_id, created_at)
        identity_issue = issue(identity.subject_id, 'subject', 'IDENTITY_UNVERIFIED',
                               'Study-as-subject grouping does not establish biological uniqueness.',
                               'protected_identity:study_as_subject_fallback', created_at)
        local = [pending]
        for value in evidence.values():
            local.extend(evidence_issues(value, entity_type='study',
                                        entity_id=identity.study_id, created_at=created_at))
        issues.extend([identity_issue, *local])
        common = dict(schema_version='1.0.0', source='pants', source_snapshot_id=snapshot_id)
        subjects.append(dict(common, subject_id=identity.subject_id, source_subject_id=raw_id,
                             identity_method=identity.identity_method,
                             identity_assurance=identity.identity_assurance,
                             status='quarantined', issue_ids=[identity_issue['issue_id']]))
        # Source tumour flag remains in metadata evidence, not a verified lesion target.
        studies.append(dict(common, study_id=identity.study_id, subject_id=identity.subject_id,
                            source_study_id=raw_id, source_partition=identity.source_partition,
                            modality='CT', image=evidence['ct']['file'], geometry=evidence['ct']['geometry'],
                            acquisition={k: None for k in ('study_date', 'study_year', 'contrast_phase',
                                                          'scanner', 'manufacturer', 'site')},
                            target_statuses=[dict(target='pancreatic_lesion', status='unknown',
                                                  method='unavailable', reference_id=None)],
                            annotation_ids=[], status='quarantined',
                            issue_ids=[i['issue_id'] for i in local]))
    return dict(subjects=subjects, studies=studies, annotations=[], issues=issues)


def publish(destination, inputs, evidence):
    """New directory only; persist inputs then prove exact deterministic replay.

    A failed write leaves an incomplete directory without verification.json. This is
    a local diagnostic writer, not atomic production publication or crash durability.
    """
    files = assemble_manifest(**inputs)
    destination.mkdir(parents=False, exist_ok=False)
    for name, value in dict(evidence, **{'assembly-inputs.json': inputs}).items():
        if Path(name).name != name or not name.endswith('.json') or name in files:
            raise ValueError('Unsafe or colliding evidence filename')
        with (destination / name).open('xb') as stream:
            stream.write(canonical(value))
    persisted = json.loads((destination / 'assembly-inputs.json').read_bytes())
    if assemble_manifest(**persisted) != files:
        raise ValueError('Persisted-input replay mismatch')
    for name, payload in files.items():
        with (destination / name).open('xb') as stream:
            stream.write(payload)
    hashes = {p.name: digest(p.read_bytes()) for p in sorted(destination.iterdir())}
    with (destination / 'verification.json').open('xb') as stream:
        stream.write(canonical(dict(replay_equal=True, status='quarantined', files=hashes,
                                    limitation='No annotation qualification, cohort freeze or training')))
    return json.loads(files['manifest.json'])


def main():
    registry = yaml.safe_load((REPO / 'configs/local/roots.yaml').read_text())
    primary = registry['failure_domains']['external_primary']
    mount = Path(primary['mount_path'])
    device = mounted(mount, primary['volume_uuid'])
    def check():
        mounted(mount, primary['volume_uuid'], device)
    inventory = json.loads((REPO / 'docs/capstone/data/acquisition-2026-09-19.json').read_bytes())
    revision = inventory['pants']['huggingface_revision']
    parent = Path(registry['roots']['pants_source']['acquisition_parent'])
    if not parent.is_relative_to(mount) or parent.resolve(strict=True) != parent:
        raise ValueError('Expected canonical on-volume acquisition parent')
    extraction = parent / ('extraction-' + revision[:12] + '-20260922')
    metadata_path = parent / ('acquisition-' + revision[:12]) / 'metadata.xlsx'
    pin = next(f for f in inventory['pants']['files'] if f['name'] == 'metadata.xlsx')
    base = (REPO / 'outputs/splits/train.txt').read_bytes()
    ids = sorted(i.study_id.split(':')[-1] for i in accepted_pants_members(base, 'train'))[:2]
    if ids != ['PanTS_00000001', 'PanTS_00000002']:
        raise ValueError('Diagnostic scope changed')
    metadata = join_studies(read_metadata(metadata_path.read_bytes(), pin['sha256']), ids)
    check()
    measured = {}
    for raw_id in ids:
        paths = dict(ct=f'PanTSMini_ImageTr_00000001_00001000/{raw_id}/ct.nii.gz',
                     pancreas=f'PanTSMini_Label/{raw_id}/segmentations/pancreas.nii.gz',
                     lesion=f'PanTSMini_Label/{raw_id}/segmentations/pancreatic_lesion.nii.gz')
        measured[raw_id] = {k: measure_nifti({'pants_slice': extraction}, 'pants_slice', uri, check)
                            for k, uri in paths.items()}
    now = datetime.now(timezone.utc).isoformat()
    selected = [v['file'] for study in measured.values() for v in study.values()]
    inventory_hash = digest(canonical(selected))
    snapshot_id = 'snapshot:pants:' + inventory_hash
    snapshot = dict(schema_version='1.0.0', source_snapshot_id=snapshot_id, source_key='pants',
                    source_version=dict(version_status='partially_known', release=None,
                                        archive_version=None, commit=revision), retrieved_at=now,
                    license=dict(name='Unreconciled publisher terms; no redistribution clearance',
                                 evidence_uri='https://huggingface.co/datasets/BodyMaps/PanTSMini',
                                 restrictions=['source_terms_apply', 'redistribution_limited'], citation_required=True),
                    root_alias='pants_slice', inventory=dict(uri='selected-files.json',
                        content_sha256=inventory_hash, file_count=6, assurance='selected_local_sha256'),
                    status='partial', derivation_sha256=inventory_hash,
                    notes='Diagnostic alias only, not an activated production root. Inventory is package-relative; '
                          'six selected files, not full source coverage. retrieved_at is verification time.')
    record_inputs = records(metadata, measured, snapshot_id, now)
    # Retain interpretation separately; original unit issues remain open in this slice.
    study_id = pants_identity(ids[0]).study_id
    interpreted = infer_mask_mm(measured[ids[0]]['pancreas'], measured[ids[0]]['ct'],
                               mask_study_id=study_id, ct_study_id=study_id)
    code_paths = [Path(__file__).relative_to(REPO), *[Path('src/data') / (n + '.py') for n in
                  ('pants_metadata', 'protected_identity', 'source_evidence', 'manifest_records')],
                  Path('scripts/acquisition/download_pants.py'),
                  *sorted(Path('docs/capstone/contracts').glob('*.schema.json'))]
    code = {str(p): digest((REPO / p).read_bytes()) for p in code_paths}
    config = dict(selected_ids=ids, train_membership_sha256=digest(base),
                  metadata_sha256=pin['sha256'], annotation_policy='defer_until_verified_encoding')
    run = str(uuid4())
    build = dict(run_id='run:' + run, component_version='diagnostic-pants-slice-v1',
                 config_sha256=digest(canonical(config)),
                 git_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip(),
                 dirty=True, diff_sha256=digest(canonical(code)))
    inputs = dict(name='pants-diagnostic', created_at=now, build=build, snapshots=[snapshot], **record_inputs)
    output_parent = REPO / 'outputs/prowl'
    output_parent.mkdir(exist_ok=True)
    if output_parent.resolve() != output_parent:
        raise ValueError('Output root must not be a symlink')
    destination = output_parent / ('manifest-slice-' + run)
    control = publish(destination, inputs, {'measurements.json': measured, 'metadata.json': metadata,
                        'selected-files.json': selected, 'source-snapshot.json': snapshot,
                        'unit-interpretation.json': interpreted, 'code-identity.json': code, 'config.json': config})
    print(json.dumps(dict(package=str(destination.relative_to(REPO)), status=control['status'],
                          counts=control['reconciliation'], replay_equal=True)))


if __name__ == '__main__':
    main()
