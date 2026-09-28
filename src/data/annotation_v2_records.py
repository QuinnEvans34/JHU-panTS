"""Convert verified linked evidence to quarantined original-source v2 records only."""
from copy import deepcopy

from src.data.annotation_contract_v2 import validate_annotation_v2
from src.data.manifest_records import canonical, digest


def quarantined_annotation(linked, *, snapshot_id, audit_file, issue_id):
    body = deepcopy(linked)
    identity = body.pop('record_id')
    if identity != 'linked-assessment:' + digest(canonical(body)):
        raise ValueError('Linked record identity mismatch')
    if linked['eligibility'] != 'not_granted' or linked['allowed_uses']:
        raise ValueError('Expected non-promoting diagnostic record')
    if audit_file['content_sha256'] != linked['audit_sha256']:
        raise ValueError('Wrong audit file reference')
    if linked['structure'] not in ('pancreas', 'pancreatic_lesion'):
        raise ValueError('Unsupported annotation structure')
    study = linked['study_id']
    if not study.startswith('pants:study:'):
        raise ValueError('PanTS-only diagnostic conversion')
    raw_id = study.split(':')[-1]
    annotation_id = 'pants:annotation:' + raw_id + '-' + linked['structure'] + '-v2-' + digest(canonical(linked))[:16]
    record = dict(schema_version='2.0.0', annotation_id=annotation_id, study_id=study,
        source_snapshot_id=snapshot_id, source='pants',
        structure='pancreas' if linked['structure']=='pancreas' else 'lesion',
        source_structure=linked['structure'], file=deepcopy(linked['source']),
        annotation_version='diagnostic-original-encoding-v2', method='unknown',
        validation_status='unverified', allowed_uses=[], status='quarantined', issue_ids=[issue_id],
        label_encoding=dict(representation='original_source', audit_file=deepcopy(audit_file),
            audit_source_sha256=linked['source']['content_sha256'],
            values_basis={'stored':'stored','scaled':'nifti_scaled_semantic'}[linked['values_basis']],
            value_counts=[dict(value=v,count=n) for v,n in linked['semantic_value_counts']],
            voxel_count=sum(n for _,n in linked['semantic_value_counts']),
            stored_range=deepcopy(linked['stored_range']),
            effective_scaling=dict(slope=linked['effective_scaling']['slope'],
                                   intercept=linked['effective_scaling']['inter']), mapping=None),
        provenance=dict(scope='unknown', evidence_files=[], release_applicability='unresolved',
                        allowed_use_decision_file=None))
    validate_annotation_v2(record)
    return record
