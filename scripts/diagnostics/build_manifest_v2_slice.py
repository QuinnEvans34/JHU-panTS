"""Fixed saved-evidence diagnostic package; no source-drive access or promotion."""
from datetime import datetime, timezone
from pathlib import Path
import subprocess
from uuid import uuid4

from src.data.audit_assessment_link import parse
from src.data.annotation_v2_records import quarantined_annotation
from src.data.manifest_records import canonical, digest
from src.data.manifest_records_v2 import assemble_manifest_v2
from src.data.protected_identity import accepted_pants_members, pants_identity

REPO=Path(__file__).resolve().parents[2]
LINKED='outputs/prowl/annotation-assessments-6277e6f8-17e2-4f6f-b929-285c6e87af81'
AUDIT='outputs/prowl/voxel-followup-140effff-129c-4ff8-b455-70a2119707a1'
RECEIPT_SHA='af44d20ce661610f7df723050bf442cae863c2e782553030783976b4f32fe309'


def main():
    reads={}
    def read(relative):
        path=REPO/relative
        if not path.is_relative_to(REPO) or path.resolve()!=path or not path.is_file() or path.stat().st_size>10*1024*1024:
            raise ValueError('Unsafe, missing or oversized saved evidence')
        raw=path.read_bytes()
        if len(raw)>10*1024*1024: raise ValueError('Input size limit')
        reads[relative]=raw
        return raw
    receipt_raw=read(LINKED+'/receipt.json')
    if digest(receipt_raw)!=RECEIPT_SHA: raise ValueError('Linked receipt changed')
    receipt=parse(receipt_raw)
    for name,sha in receipt['input_hashes'].items():
        if digest(read(name))!=sha: raise ValueError('Prior evidence changed: '+name)
    linked_raw=read(LINKED+'/assessments.jsonl')
    if digest(linked_raw)!=receipt['output_sha256']: raise ValueError('Linked output changed')
    linked=[parse(line) for line in linked_raw.splitlines()]
    training={r.study_id for r in accepted_pants_members(read('outputs/splits/train.txt'),'train')}
    ids=sorted({r['study_id'] for r in linked})
    expected_ids=['pants:study:PanTS_'+f'{i:08d}' for i in (3,26,31,78,266)]
    if ids!=expected_ids: raise ValueError('Fixed study selection changed')
    if len(linked)!=10 or len(ids)!=5 or not set(ids)<=training: raise ValueError('Diagnostic scope changed')
    if len({(r['study_id'],r['structure']) for r in linked})!=10: raise ValueError('Duplicate annotation')
    audits={}
    evidence={}
    for i in range(12):
        name=f'pair-{i:02d}.json'; raw=read(AUDIT+'/'+name)
        audits[digest(raw)]=(name,raw,parse(raw)); evidence[name]=raw
    selected={}
    for row in linked:
        for role in ('source','ct_source'):
            ref=row[role]
            if ref['uri'] in selected and selected[ref['uri']]!=ref: raise ValueError('Conflicting source reference')
            selected[ref['uri']]=ref
    inventory=canonical([selected[k] for k in sorted(selected)])
    snapshot_id='snapshot:pants:'+digest(inventory)
    now=datetime.now(timezone.utc).isoformat()
    selection=parse(read(AUDIT+'/selection.json'))
    snapshot=dict(schema_version='1.0.0',source_snapshot_id=snapshot_id,source_key='pants',
        source_version=dict(version_status='partially_known',release=None,archive_version=None,
                            commit='3b1cd61108116b58ea5c1ddb3512c1847d965f96'),
        retrieved_at=selection['created_at'],
        license=dict(name='Unreconciled publisher terms; no redistribution clearance',
            evidence_uri='https://huggingface.co/datasets/BodyMaps/PanTSMini',
            restrictions=['source_terms_apply','redistribution_limited'],citation_required=True),
        root_alias='followup_source',inventory=dict(uri='selected-files.json',content_sha256=digest(inventory),
            file_count=len(selected),assurance='selected_local_sha256'),status='partial',
        derivation_sha256=digest(inventory),notes='Historical audit evidence only, no current source remeasurement. '
        'Diagnostic root alias not activated; selected-files.json is package-relative. retrieved_at is prior audit time.')
    issues=[]
    def issue(entity,kind,code,message,reference):
        result=dict(schema_version='1.0.0',issue_id='issue:'+str(uuid4()),rule_code=code,
            entity_type=kind,entity_id=entity,severity='blocking',disposition='quarantine',
            message=message,evidence=[dict(kind='validator_output',reference=reference)],created_at=now)
        issues.append(result)
        return result['issue_id']
    subjects=[]; studies=[]; annotations=[]
    for study_id in ids:
        raw_id=study_id.split(':')[-1]
        identity=pants_identity(raw_id)
        rows=[r for r in linked if r['study_id']==study_id]
        subject_issue=issue(identity.subject_id,'subject','IDENTITY_UNVERIFIED',
            'Study-as-subject grouping has not established biological uniqueness.','protected_identity')
        common=dict(schema_version='1.0.0',source='pants',source_snapshot_id=snapshot_id)
        subjects.append(dict(common,subject_id=identity.subject_id,source_subject_id=raw_id,
            identity_method=identity.identity_method,identity_assurance=identity.identity_assurance,
            status='quarantined',issue_ids=[subject_issue]))
        annotation_ids=[]
        for row in rows:
            name,raw,pair=audits[row['audit_sha256']]
            if row['source']!=pair['mask']['file'] or row['ct_source']!=pair['ct']['file']:
                raise ValueError('Linked source disagrees with retained audit')
            audit_ref=dict(root_alias='manifest_evidence',uri=name,media_type='application/json',
                           bytes=len(raw),content_sha256=digest(raw))
            issue_id='issue:'+str(uuid4())
            annotation=quarantined_annotation(row,snapshot_id=snapshot_id,audit_file=audit_ref,issue_id=issue_id)
            issues.append(dict(schema_version='1.0.0',issue_id=issue_id,rule_code='ANNOTATION_USE_PENDING',
                entity_type='annotation',entity_id=annotation['annotation_id'],severity='blocking',
                disposition='quarantine',message='Source/release provenance, rights, mapping approval and '
                'purpose-specific target use remain unresolved; measured encoding is not permission.',
                evidence=[dict(kind='validator_output',reference='linked-assessments.jsonl:'+row['record_id'])],created_at=now))
            annotations.append(annotation); annotation_ids.append(annotation['annotation_id'])
        pending=issue(study_id,'study','STUDY_QUALIFICATION_PENDING',
            'Coverage disposition, geometry/units, identity and target qualification remain pending. '
            'Retain case 78; provisional review is not a clinical negative.','linked-assessments.jsonl:'+study_id)
        ct=audits[rows[0]['audit_sha256']][2]['ct']
        studies.append(dict(common,study_id=study_id,subject_id=identity.subject_id,
            source_study_id=raw_id,source_partition=identity.source_partition,
            modality='CT',image=ct['file'],geometry=ct['geometry'],
            acquisition={k:None for k in ('study_date','study_year','contrast_phase','scanner','manufacturer','site')},
            target_statuses=[dict(target='pancreatic_lesion',status='unknown',method='unavailable',reference_id=None)],
            annotation_ids=annotation_ids,status='quarantined',issue_ids=[pending]))
    code_names=['scripts/diagnostics/build_manifest_v2_slice.py','src/data/annotation_v2_records.py',
        'src/data/manifest_records_v2.py','src/data/manifest_records.py','src/data/annotation_contract_v2.py',
        'src/data/protected_identity.py','src/data/audit_assessment_link.py']
    code_names += ['docs/capstone/contracts/'+n+'.schema.json' for n in
        ('manifest-v2','annotation-record-v2','annotation-record','subject-record','study-record','data-issue','source-snapshot')]
    code={name:digest(read(name)) for name in code_names}
    config=dict(linked_receipt_sha256=RECEIPT_SHA,mode='quarantined_original_encoding_v2')
    build=dict(run_id='run:'+str(uuid4()),component_version='diagnostic-v2-manifest-v1',
        config_sha256=digest(canonical(config)),git_commit=subprocess.check_output(
            ['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),dirty=True,diff_sha256=digest(canonical(code)))
    inputs=dict(name='pants-diagnostic-v2',created_at=now,build=build,snapshots=[snapshot],
                subjects=subjects,studies=studies,annotations=annotations,issues=issues)
    files=assemble_manifest_v2(**inputs)
    if parse(files['manifest.json'])['status']!='quarantined': raise ValueError('Unexpected promotion')
    persisted=canonical(inputs)
    if assemble_manifest_v2(**parse(persisted))!=files: raise ValueError('Replay mismatch')
    evidence.update({'assembly-inputs.json':persisted,'selected-files.json':inventory,
        'source-snapshot.json':canonical(snapshot),'linked-assessments.jsonl':linked_raw,
        'code-identity.json':canonical(code),'config.json':canonical(config),
        'input-hashes.json':canonical({name:digest(raw) for name,raw in reads.items()}),
        'root-bindings.json':canonical(dict(manifest_evidence='this package directory',
            followup_source='diagnostic historical source alias; not activated for consumers'))})
    for name,raw in reads.items():
        if (REPO/name).read_bytes()!=raw: raise ValueError('Input changed during assembly')
    parent=REPO/'outputs/prowl'
    if parent.resolve()!=parent or not parent.is_dir(): raise ValueError('Unsafe output parent')
    destination=parent/('manifest-v2-slice-'+str(uuid4())); destination.mkdir(exist_ok=False)
    all_files=evidence|files
    for name,raw in all_files.items():
        with (destination/name).open('xb') as stream: stream.write(raw)
    if assemble_manifest_v2(**parse((destination/'assembly-inputs.json').read_bytes()))!=files:
        raise ValueError('Disk replay mismatch')
    hashes={name:digest((destination/name).read_bytes()) for name in all_files}
    if any(hashes[name]!=digest(raw) for name,raw in all_files.items()): raise ValueError('Disk hash mismatch')
    with (destination/'verification.json').open('xb') as stream:
        stream.write(canonical(dict(status='quarantined',replay_equal=True,files=hashes,
            source_remeasured=False,training_authorized=False)))
    print(destination)
    print('5 studies, 10 quarantined v2 annotations; no eligibility granted')


if __name__=='__main__': main()
