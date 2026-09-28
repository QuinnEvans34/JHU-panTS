from copy import deepcopy
import json

import pytest
from jsonschema import Draft202012Validator, ValidationError

from src.data.annotation_contract_v2 import validate_annotation_v2, validate_approved_binary_lineage
from src.data.binary_label_policy import APPROVED_POLICY, PROPOSED_POLICY
from src.data.manifest_records import CONTRACTS, digest, validate_schema

pytestmark = pytest.mark.unit


def example():
    row = json.loads((CONTRACTS/'examples/annotation-record.example.json').read_text())
    ref = deepcopy(row['file'])
    ref.update(root_alias='diagnostic_evidence', uri='synthetic/audit.json',
               media_type='application/json', content_sha256='a'*64)
    row.update(schema_version='2.0.0', annotation_id=row['annotation_id']+'-encoding-v2',
               status='quarantined', method='unknown', validation_status='unverified', allowed_uses=[],
               issue_ids=['issue:11111111-1111-4111-8111-111111111111'])
    row['label_encoding'] = dict(representation='original_source', audit_file=ref,
        audit_source_sha256=row['file']['content_sha256'], values_basis='nifti_scaled_semantic',
        value_counts=[dict(value=0.,count=3),dict(value=1.0000000591389835,count=1)],
        voxel_count=4, stored_range=[-128,127],
        effective_scaling=dict(slope=0.003921568859368563,intercept=0.501960813999176), mapping=None)
    row['provenance'] = dict(scope='unknown',evidence_files=[],release_applicability='unresolved',
                             allowed_use_decision_file=None)
    return row


def approved():
    row=example(); evidence=deepcopy(row['label_encoding']['audit_file'])
    row.update(status='eligible',method='human_validated',validation_status='source_asserted',
               allowed_uses=['training_target'],issue_ids=[])
    row['provenance'].update(scope='publisher_protocol',evidence_files=[evidence],
        release_applicability='confirmed',allowed_use_decision_file=evidence)
    row['label_encoding']['mapping']=dict(status='approved',policy_id='synthetic-policy',
        policy_sha256='b'*64,input_basis='nifti_scaled_semantic',kind='binary_zero_one_endpoints',
        absolute_tolerance=1e-6,relative_tolerance=0,canonical_foreground=2,approval_file=evidence)
    return row


def test_schema_and_measured_encoding_valid_without_promotion():
    schema=json.loads((CONTRACTS/'annotation-record-v2.schema.json').read_text())
    Draft202012Validator.check_schema(schema)
    row=example(); before=deepcopy(row)
    validate_annotation_v2(row)
    assert row==before and row['allowed_uses']==[]


def test_explicit_versions_do_not_silently_interchange():
    old=json.loads((CONTRACTS/'examples/annotation-record.example.json').read_text())
    validate_schema('annotation-record',old)
    with pytest.raises(ValidationError): validate_annotation_v2(old)
    with pytest.raises(ValidationError): validate_schema('annotation-record',example())


def test_syntactically_approved_record_requires_separate_evidence_resolution():
    validate_annotation_v2(approved())  # No source IO, permission grant or actual approval.


@pytest.mark.parametrize('fault', ['hash','sum','duplicates','range','scale','source','snapshot',
    'nan','zero_slope','legacy_field','extra','issue','allowed','project_claim','source_claim',
    'missing_approval','unverified','missing_use_decision','intermediate','float_count',
    'bad_path','proposed_with_approval','unmapped_eligible'])
def test_rejects_inconsistent_or_unsupported_claims(fault):
    row=approved() if fault in ('missing_approval','unverified','missing_use_decision','intermediate',
        'proposed_with_approval','unmapped_eligible') else example()
    enc=row['label_encoding']; prov=row['provenance']
    if fault=='hash': enc['audit_source_sha256']='f'*64
    if fault=='sum': enc['voxel_count']=5
    if fault=='duplicates': enc['value_counts'][1]['value']=0
    if fault=='range': enc['stored_range']=[127,-128]
    if fault=='scale': enc['effective_scaling']['intercept']=1
    if fault=='source': row['source']='panorama'
    if fault=='snapshot': row['source_snapshot_id']='snapshot:panorama:123456789abc'
    if fault=='nan': enc['value_counts'][0]['value']=float('nan')
    if fault=='zero_slope': enc['effective_scaling']['slope']=0
    if fault=='legacy_field': enc['source_values']=[1]
    if fault=='extra': row['diagnosis']='negative'
    if fault=='issue': row['issue_ids']=[]
    if fault=='allowed': row['allowed_uses']=['training_target']
    if fault=='project_claim': row['validation_status']='project_verified'
    if fault=='source_claim': row['method']='human_manual'
    if fault=='missing_approval': enc['mapping']['approval_file']=None
    if fault=='unverified': row['validation_status']='unverified'
    if fault=='missing_use_decision': prov['allowed_use_decision_file']=None
    if fault=='intermediate':
        enc.update(stored_range=[0,.5],effective_scaling=dict(slope=1,intercept=0))
        enc['value_counts'][1]['value']=.5
    if fault=='float_count': enc['value_counts'][0]['count']=3.0
    if fault=='bad_path': enc['audit_file']['uri']='safe/../escape.json'
    if fault=='proposed_with_approval': enc['mapping']['status']='proposed'
    if fault=='unmapped_eligible': enc['mapping']=None
    with pytest.raises((ValueError,ValidationError)): validate_annotation_v2(row)


def test_binary_and_empty_original_source_are_representable():
    for values, counts in [([0,1],[3,1]),([0],[4])]:
        row=example(); enc=row['label_encoding']
        enc.update(values_basis='stored',stored_range=[min(values),max(values)],
            effective_scaling=dict(slope=1,intercept=0),
            value_counts=[dict(value=v,count=n) for v,n in zip(values,counts)])
        validate_annotation_v2(row)
        assert row['allowed_uses']==[]


def lineage_example():
    row = example()
    approval_bytes = b'Synthetic reviewed D-259 approval evidence'
    implementation_bytes = b'Synthetic reviewed decoder source'
    ref = deepcopy(row['label_encoding']['audit_file'])
    ref.update(uri='synthetic/approval.md', media_type='text/markdown',
               bytes=len(approval_bytes), content_sha256=digest(approval_bytes))
    row['label_encoding']['mapping'] = dict(
        status='approved', policy_id=APPROVED_POLICY,
        policy_sha256=digest(implementation_bytes), input_basis='nifti_scaled_semantic',
        kind='binary_zero_one_endpoints', absolute_tolerance=1e-6, relative_tolerance=0,
        canonical_foreground=2, approval_file=ref)
    evidence = dict(approval_bytes=approval_bytes, implementation_bytes=implementation_bytes,
                    trusted_approval_sha256=digest(approval_bytes),
                    trusted_implementation_sha256=digest(implementation_bytes))
    return row, evidence


@pytest.mark.parametrize('empty', [False, True])
def test_approved_lineage_preserves_record_and_quarantine(empty):
    row, evidence = lineage_example()
    if empty:
        row['label_encoding'].update(value_counts=[dict(value=0, count=4)],
            stored_range=[0, 0], effective_scaling=dict(slope=1, intercept=0))
    before = deepcopy(row)
    evidence_before = deepcopy(evidence)
    validate_approved_binary_lineage(row, **evidence)
    assert row == before and evidence == evidence_before
    assert row['status'] == 'quarantined' and row['allowed_uses'] == []
    assert row['issue_ids'] and row['provenance']['allowed_use_decision_file'] is None


@pytest.mark.parametrize('fault', [
    'candidate', 'unknown_policy', 'proposed', 'no_mapping', 'missing_approval',
    'approval_hash', 'approval_size', 'approval_bytes', 'self_consistent_wrong_approval',
    'implementation_hash', 'implementation_bytes', 'self_consistent_wrong_implementation',
    'looser_tolerance', 'tighter_tolerance', 'relative_tolerance',
    'missing_approval_bytes', 'missing_implementation_bytes', 'invalid_approval_pin',
    'invalid_implementation_pin', 'wrong_source', 'allowed_use_promotion'])
def test_lineage_rejects_unreviewed_or_inconsistent_claims_without_mutation(fault):
    row, evidence = lineage_example()
    mapping = row['label_encoding']['mapping']
    if fault == 'candidate': mapping['policy_id'] = PROPOSED_POLICY
    if fault == 'unknown_policy': mapping['policy_id'] = 'unreviewed-policy'
    if fault == 'proposed':
        mapping.update(status='proposed', approval_file=None)
    if fault == 'no_mapping': row['label_encoding']['mapping'] = None
    if fault == 'missing_approval': mapping['approval_file'] = None
    if fault == 'approval_hash': mapping['approval_file']['content_sha256'] = 'f'*64
    if fault == 'approval_size': mapping['approval_file']['bytes'] += 1
    if fault in ('approval_bytes', 'self_consistent_wrong_approval'):
        evidence['approval_bytes'] = b'Unreviewed replacement approval'
        if fault == 'self_consistent_wrong_approval':
            mapping['approval_file'].update(content_sha256=digest(evidence['approval_bytes']),
                                            bytes=len(evidence['approval_bytes']))
    if fault == 'implementation_hash': mapping['policy_sha256'] = 'f'*64
    if fault in ('implementation_bytes', 'self_consistent_wrong_implementation'):
        evidence['implementation_bytes'] = b'Unreviewed replacement code'
        if fault == 'self_consistent_wrong_implementation':
            mapping['policy_sha256'] = digest(evidence['implementation_bytes'])
    if fault == 'looser_tolerance': mapping['absolute_tolerance'] = 1e-5
    if fault == 'tighter_tolerance': mapping['absolute_tolerance'] = 1e-7
    if fault == 'relative_tolerance': mapping['relative_tolerance'] = 1e-6
    if fault == 'missing_approval_bytes': evidence['approval_bytes'] = None
    if fault == 'missing_implementation_bytes': evidence['implementation_bytes'] = None
    if fault == 'invalid_approval_pin': evidence['trusted_approval_sha256'] = None
    if fault == 'invalid_implementation_pin': evidence['trusted_implementation_sha256'] = 'invalid'
    if fault == 'wrong_source':
        row['source'] = 'panorama'
        for key in ('study_id', 'annotation_id', 'source_snapshot_id'):
            row[key] = row[key].replace('pants:', 'panorama:')
    if fault == 'allowed_use_promotion': row['allowed_uses'] = ['training_target']
    before = deepcopy(row)
    with pytest.raises((ValueError, ValidationError)):
        validate_approved_binary_lineage(row, **evidence)
    assert row == before


def test_candidate_stays_structurally_replayable_but_is_not_approved_lineage():
    row, evidence = lineage_example()
    row['label_encoding']['mapping'].update(
        policy_id=PROPOSED_POLICY, status='proposed', approval_file=None)
    validate_annotation_v2(row)
    with pytest.raises(ValueError, match='Explicit approved'):
        validate_approved_binary_lineage(row, **evidence)


def test_current_d259_evidence_fits_existing_contract_without_schema_change():
    # Reviewed pins are independent of the annotation. Updates require evidence review.
    approval_pin = '3929e0e359d1aa1d4a5cc5a0066285699821ed648bbe87bfdcbc2bc2bead6de3'
    implementation_pin = 'ecdbe3e887c4b791f1079e81dcb22d804fda2e8c4b661c341ae422d90e6f4407'
    repo = CONTRACTS.parents[2]
    approval_path = 'docs/capstone/data/BINARY-DECODING-APPROVAL-2026-09-28.md'
    approval_bytes = (repo/approval_path).read_bytes()
    implementation_bytes = (repo/'src/data/binary_label_policy.py').read_bytes()
    row, _ = lineage_example()
    row['label_encoding']['mapping'].update(policy_sha256=implementation_pin,
        approval_file=dict(root_alias='repository_evidence', uri=approval_path,
                           media_type='text/markdown', bytes=len(approval_bytes),
                           content_sha256=approval_pin))
    before = deepcopy(row)
    validate_approved_binary_lineage(row, approval_bytes=approval_bytes,
        implementation_bytes=implementation_bytes, trusted_approval_sha256=approval_pin,
        trusted_implementation_sha256=implementation_pin)
    assert row == before and row['allowed_uses'] == []
