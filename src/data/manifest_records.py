"""Schema-checked, deterministic in-memory manifest assembly. No source activation."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path, PurePosixPath

from jsonschema import Draft202012Validator, FormatChecker

from src.data.protected_identity import pants_identity

CONTRACTS = Path(__file__).resolve().parents[2] / 'docs/capstone/contracts'
KINDS = {'subjects': ('subject-record', 'subject_id'),
         'studies': ('study-record', 'study_id'),
         'annotations': ('annotation-record', 'annotation_id'),
         'issues': ('data-issue', 'issue_id')}


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def validate_schema(kind, record):
    schema = json.loads((CONTRACTS / f'{kind}.schema.json').read_text())
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(record)
    canonical(record)  # Reject NaN/Infinity, including in geometry.


def file_reference(reference):
    uri = reference['uri']
    if ('\\' in uri or any(ord(c) < 32 for c in uri) or ':' in uri
            or PurePosixPath(uri).is_absolute()
            or any(p in ('', '.', '..') for p in uri.split('/'))):
        raise ValueError('Unsafe source relative URI')


def assemble_manifest(*, name, created_at, build, snapshots, subjects, studies,
                      annotations, issues):
    """Return canonical package bytes from measured, supplied records.

    Does not measure images, infer annotation eligibility, publish files, freeze cohorts,
    or independently attest caller-provided evidence. All callers must retain evidence.
    """
    rows = deepcopy(dict(subjects=subjects, studies=studies,
                         annotations=annotations, issues=issues))
    if build['dirty'] and not build.get('diff_sha256'):
        raise ValueError('Dirty build requires recorded diff identity')
    indexed = {}
    snapshot_map = {}
    for snapshot in snapshots:
        validate_schema('source-snapshot', snapshot)
        key = snapshot['source_snapshot_id']
        if key in snapshot_map:
            raise ValueError('Duplicate snapshot')
        snapshot_map[key] = snapshot
    if not snapshot_map:
        raise ValueError('Source snapshot required')
    for collection, (kind, key) in KINDS.items():
        indexed[collection] = {}
        for record in rows[collection]:
            validate_schema(kind, record)
            if record[key] in indexed[collection]:
                raise ValueError(f'Duplicate {collection} identity')
            indexed[collection][record[key]] = record
            if collection != 'issues':
                source = record['source']
                snapshot = snapshot_map.get(record['source_snapshot_id'])
                if snapshot is None or snapshot['source_key'] != source:
                    raise ValueError('Missing or inconsistent source snapshot')
                if not record[key].startswith(source + ':'):
                    raise ValueError('Inconsistent source namespace')
    for collection in ('subjects', 'studies', 'annotations'):
        for record in rows[collection]:
            if any(i not in indexed['issues'] for i in record['issue_ids']):
                raise ValueError('Unresolved issue reference')
    for study in rows['studies']:
        subject = indexed['subjects'].get(study['subject_id'])
        if subject is None or any(subject[k] != study[k] for k in ('source', 'source_snapshot_id')):
            raise ValueError('Missing or inconsistent subject')
        if study['source'] == 'pants':
            identity = pants_identity(study['source_study_id'])
            if (study['study_id'], study['subject_id'], study['source_partition']) != (
                    identity.study_id, identity.subject_id, identity.source_partition):
                raise ValueError('PanTS identity/partition mismatch')
        file_reference(study['image'])
        targets = [t['target'] for t in study['target_statuses']]
        if len(set(targets)) != len(targets):
            raise ValueError('Duplicate target status')
        expected = {a['annotation_id'] for a in rows['annotations'] if a['study_id'] == study['study_id']}
        if set(study['annotation_ids']) != expected:
            raise ValueError('Annotation links disagree')
    for annotation in rows['annotations']:
        study = indexed['studies'].get(annotation['study_id'])
        if study is None or any(study[k] != annotation[k] for k in ('source', 'source_snapshot_id')):
            raise ValueError('Missing or inconsistent annotation study')
        file_reference(annotation['file'])
    files, references = {}, {}
    for collection, (_, key) in KINDS.items():
        payload = b''.join(canonical(r) for r in sorted(rows[collection], key=lambda r: r[key]))
        filename = collection + '.jsonl'
        files[filename] = payload
        references[collection] = dict(uri=filename, content_sha256=digest(payload),
                                      bytes=len(payload), count=len(rows[collection]))
    blocking = sum(i['severity'] == 'blocking' and i['disposition'] != 'resolved_by_new_artifact'
                   for i in rows['issues'])
    ready = (bool(studies) and all(s['status'] == 'complete' for s in snapshots) and not blocking
             and all(s['status'] in ('reconciled', 'eligible', 'excluded') for s in studies)
             and not any(r['status'] == 'quarantined'
                         for c in ('subjects', 'annotations') for r in rows[c]))
    counts = Counter(s['status'] for s in studies)
    derivation = digest(canonical(dict(records=references,
                                       snapshots={k: digest(canonical(v)) for k, v in snapshot_map.items()},
                                       config=build['config_sha256'],
                                       component=build['component_version'],
                                       git_commit=build['git_commit'],
                                       diff_sha256=build.get('diff_sha256'))))
    control = dict(schema_version='1.0.0', manifest_id=f'manifest:{name}:{derivation}',
                   derivation_sha256=derivation, created_at=created_at,
                   source_snapshot_ids=sorted(snapshot_map),
                   record_schema_versions=dict(subject='1.0.0', study='1.0.0',
                                               annotation='1.0.0', issue='1.0.0'),
                   records=references, build=deepcopy(build),
                   reconciliation=dict(discovered=len(studies),
                                       reconciled=counts['reconciled'] + counts['eligible'],
                                       eligible=counts['eligible'], excluded=counts['excluded'],
                                       quarantined=counts['quarantined'], blocking_issue_count=blocking),
                   status='complete' if ready else 'quarantined')
    validate_schema('manifest', control)
    files['manifest.json'] = canonical(control)
    return files
