"""Explicit v2 validator. Not a manifest migration, decoder or eligibility authority."""
import json
import math
import re

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from src.data.binary_label_policy import APPROVED_POLICY
from src.data.manifest_records import CONTRACTS, canonical, digest, file_reference


def validate_approved_binary_lineage(record, *, approval_bytes, implementation_bytes,
                                     trusted_approval_sha256, trusted_implementation_sha256):
    """Check D-259 lineage against independently reviewed pins; never grant allowed uses.

    The caller supplies retained evidence bytes and trusted hashes from its reviewed
    publication inputs, NOT hashes copied from the annotation being checked. Hashes
    establish byte identity, not permission: reviewing the approval's scope and the
    implementation remains the caller's responsibility. For this policy, the existing
    mapping.policy_sha256 records the exact binary_label_policy.py source bytes.

    No evidence is fetched, source array decoded, record changed or package published.
    This is separate from structural validation so historical/candidate records retain
    their original meaning. Eligibility, source applicability and other holds remain
    independent even when this check passes.
    """
    validate_annotation_v2(record)
    mapping = record['label_encoding']['mapping']
    if (record['source'] != 'pants' or mapping is None
            or mapping['status'] != 'approved' or mapping['policy_id'] != APPROVED_POLICY):
        raise ValueError('Explicit approved PanTS binary policy required')
    if mapping['absolute_tolerance'] != 1e-6 or mapping['relative_tolerance'] != 0:
        raise ValueError('Mapping differs from approved binary tolerance')
    for pin in (trusted_approval_sha256, trusted_implementation_sha256):
        if not isinstance(pin, str) or re.fullmatch(r'[0-9a-f]{64}', pin) is None:
            raise ValueError('Independently reviewed SHA-256 pins required')
    if not isinstance(approval_bytes, bytes) or not isinstance(implementation_bytes, bytes):
        raise ValueError('Retained approval and implementation bytes required')
    approval = mapping['approval_file']
    if (digest(approval_bytes) != trusted_approval_sha256
            or approval['content_sha256'] != trusted_approval_sha256
            or approval['bytes'] != len(approval_bytes)):
        raise ValueError('Approval evidence does not match reviewed identity/size')
    if (digest(implementation_bytes) != trusted_implementation_sha256
            or mapping['policy_sha256'] != trusted_implementation_sha256):
        raise ValueError('Implementation evidence does not match reviewed identity')


def validate_annotation_v2(record):
    """Validate shape and consistency; evidence file contents are NOT resolved here.

    Consumers must separately verify referenced hashes, source applicability and signed-off
    purpose-specific decisions. A syntactically approved record is not runtime permission.
    """
    old = json.loads((CONTRACTS/'annotation-record.schema.json').read_text())
    schema = json.loads((CONTRACTS/'annotation-record-v2.schema.json').read_text())
    registry = Registry().with_resource(old['$id'], Resource.from_contents(old))
    Draft202012Validator(schema, registry=registry, format_checker=FormatChecker()).validate(record)
    canonical(record)
    encoding, provenance = record['label_encoding'], record['provenance']
    mapping = encoding['mapping']
    references = [record['file'], encoding['audit_file'], *provenance['evidence_files']]
    if provenance['allowed_use_decision_file'] is not None:
        references.append(provenance['allowed_use_decision_file'])
    if mapping is not None and mapping['approval_file'] is not None:
        references.append(mapping['approval_file'])
    for reference in references:
        file_reference(reference)
    if any(not record[key].startswith(record['source'] + ':') for key in ('study_id', 'annotation_id')):
        raise ValueError('Inconsistent source namespace')
    if not record['source_snapshot_id'].startswith('snapshot:' + record['source'] + ':'):
        raise ValueError('Inconsistent snapshot source')
    if encoding['audit_source_sha256'] != record['file']['content_sha256']:
        raise ValueError('Audit source identity mismatch')
    values = [r['value'] for r in encoding['value_counts']]
    if len(set(values)) != len(values) or values != sorted(values):
        raise ValueError('Values must be unique and ordered')
    if sum(r['count'] for r in encoding['value_counts']) != encoding['voxel_count']:
        raise ValueError('Incomplete value counts')
    if any(type(r['count']) is not int for r in encoding['value_counts']) or type(encoding['voxel_count']) is not int:
        raise ValueError('Counts must be integers, not booleans or floats')
    low, high = encoding['stored_range']
    if low > high:
        raise ValueError('Invalid stored range')
    slope, intercept = (encoding['effective_scaling'][k] for k in ('slope', 'intercept'))
    if encoding['values_basis'] == 'stored':
        if (min(values), max(values)) != (low, high):
            raise ValueError('Stored range disagrees with observations')
    else:
        endpoints = sorted([low*slope + intercept, high*slope + intercept])
        if not all(math.isfinite(v) for v in endpoints) or not all(
                math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
                for a,b in zip(endpoints, [min(values), max(values)])):
            raise ValueError('Scaling endpoints disagree with observations')
    if mapping is not None:
        if mapping['status'] == 'approved' and mapping['approval_file'] is None:
            raise ValueError('Approved mapping requires decision evidence')
        if mapping['status'] == 'proposed' and mapping['approval_file'] is not None:
            raise ValueError('Proposed mapping cannot claim approval evidence')
        if mapping['status'] == 'approved':
            semantic = values if encoding['values_basis']=='nifti_scaled_semantic' else [v*slope+intercept for v in values]
            if any(not math.isfinite(v) or min(abs(v),abs(v-1)) > mapping['absolute_tolerance'] for v in semantic):
                raise ValueError('Approved binary mapping does not cover every observed value')
    if record['validation_status'] == 'project_verified' and provenance['scope'] != 'per_file_review':
        raise ValueError('Project verification requires per-file review')
    if record['method'] != 'unknown' or record['validation_status'] in ('source_asserted','project_verified'):
        if provenance['scope']=='unknown' or not provenance['evidence_files'] or provenance['release_applicability']!='confirmed':
            raise ValueError('Annotation provenance claim lacks applicable evidence')
    if record['status'] != 'eligible':
        if record['allowed_uses'] or not record['issue_ids']:
            raise ValueError('Unresolved/excluded annotation requires issues and no allowed uses')
    elif (not record['allowed_uses'] or record['validation_status'] in ('unverified','rejected')
          or record['method']=='unknown' or mapping is None or mapping['status']!='approved'
          or provenance['allowed_use_decision_file'] is None):
        raise ValueError('Eligibility lacks mapping, provenance or allowed-use decision')
