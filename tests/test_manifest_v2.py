from copy import deepcopy
import json
import pytest
from jsonschema import ValidationError

from test_manifest_records import inputs
from test_annotation_contract_v2 import example
from src.data.manifest_records import assemble_manifest, canonical, digest, validate_schema
from src.data.manifest_records_v2 import assemble_manifest_v2
from src.data.annotation_v2_records import quarantined_annotation

pytestmark = pytest.mark.unit


def args():
    result=inputs(); row=example()
    result['annotations']=[row]
    result['studies'][0]['annotation_ids']=[row['annotation_id']]
    result['issues']=[dict(schema_version='1.0.0',issue_id=row['issue_ids'][0],
        rule_code='QUALIFICATION_PENDING',entity_type='annotation',entity_id=row['annotation_id'],
        severity='blocking',disposition='quarantine',message='Synthetic pending evidence',
        evidence=[dict(kind='validator_output',reference='synthetic')],created_at=result['created_at'])]
    return result


def test_v2_repeatability_input_preservation_and_declared_versions():
    data=args(); before=deepcopy(data)
    files=assemble_manifest_v2(**data)
    assert files==assemble_manifest_v2(**data) and data==before
    control=json.loads(files['manifest.json'])
    assert control['schema_version']=='2.0.0'
    assert control['record_schema_versions']['annotation']=='2.0.0'
    assert control['status']=='quarantined'
    for collection in ('subjects','studies','annotations','issues'):
        ref=control['records'][collection]
        assert digest(files[ref['uri']])==ref['content_sha256']
    with pytest.raises(ValidationError): validate_schema('manifest',control)


def test_no_implicit_annotation_migration():
    with pytest.raises(ValidationError): assemble_manifest_v2(**inputs())
    with pytest.raises(ValidationError): assemble_manifest(**args())


@pytest.mark.parametrize('fault',['missing_study','missing_annotation','wrong_issue','dangling_issue',
    'source','duplicate','test_disguise','missing_issue'])
def test_topology_rejection(fault):
    data=args()
    if fault=='missing_study': data['studies']=[]
    if fault=='missing_annotation': data['annotations']=[]
    if fault=='wrong_issue': data['issues'][0]['entity_id']=data['studies'][0]['study_id']
    if fault=='dangling_issue': data['issues'][0]['entity_id']='pants:annotation:missing'
    if fault=='source': data['annotations'][0]['source_snapshot_id']='snapshot:pants:'+'f'*64
    if fault=='duplicate': data['annotations']*=2
    if fault=='test_disguise': data['studies'][0]['source_partition']='publisher_train'
    if fault=='missing_issue': data['issues']=[]
    with pytest.raises(ValueError): assemble_manifest_v2(**data)


def linked():
    row=example(); enc=row['label_encoding']
    value=dict(study_id=row['study_id'],structure='pancreatic_lesion', source=row['file'],
        eligibility='not_granted',allowed_uses=[],audit_sha256=enc['audit_file']['content_sha256'],
        semantic_value_counts=[[r['value'],r['count']] for r in enc['value_counts']],
        values_basis='scaled',stored_range=enc['stored_range'],
        effective_scaling=dict(slope=enc['effective_scaling']['slope'],inter=enc['effective_scaling']['intercept']))
    value['record_id']='linked-assessment:'+digest(canonical(value))
    return value


def convert(value):
    row=example()
    return quarantined_annotation(value,snapshot_id=row['source_snapshot_id'],
        audit_file=row['label_encoding']['audit_file'],issue_id=row['issue_ids'][0])


def test_convert_retains_fractional_evidence_and_no_permissions():
    value=linked(); before=deepcopy(value); row=convert(value)
    assert value==before
    assert row['label_encoding']['value_counts'][1]['value']==1.0000000591389835
    assert row['label_encoding']['mapping'] is None
    assert row['status']=='quarantined' and row['allowed_uses']==[]
    assert row['method']=='unknown' and row['validation_status']=='unverified'


def test_modified_linked_record_rejected():
    value=linked(); value['stored_range']=[0,1]
    with pytest.raises(ValueError): convert(value)


def test_timestamp_is_not_scientific_identity_but_encoding_is():
    data=args(); first=json.loads(assemble_manifest_v2(**data)['manifest.json'])
    data['created_at']='2026-09-29T00:00:00Z'
    assert json.loads(assemble_manifest_v2(**data)['manifest.json'])['manifest_id']==first['manifest_id']
    data['annotations'][0]['label_encoding']['audit_file']['uri']='new/audit.json'
    assert json.loads(assemble_manifest_v2(**data)['manifest.json'])['manifest_id']!=first['manifest_id']
