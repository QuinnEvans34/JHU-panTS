"""Verify saved bounded audit evidence; never read scans or grant eligibility."""
import json
import math
from copy import deepcopy

from src.data.annotation_assessment import assess_purpose
from src.data.manifest_records import canonical, digest, file_reference
from src.data.protected_identity import accepted_pants_members


def require(condition, message):
    if not condition:
        raise ValueError(message)


def parse(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    result = json.loads(raw, object_pairs_hook=unique)
    canonical(result)  # Reject nonfinite JSON, including nested values.
    return result


def link_audits(*, receipt_bytes, expected_receipt_sha256, artifacts, train_bytes):
    """artifacts is a filename -> bytes map, never paths resolved by this function.

    A pinned receipt anchors the historical evidence chain, not fresh disk integrity.
    No clinical/source provenance, coverage or label mapping is inferred here.
    """
    require(digest(receipt_bytes) == expected_receipt_sha256, 'Receipt hash mismatch')
    receipt = parse(receipt_bytes)
    require(receipt['status'] == 'complete', 'Incomplete receipt')
    require(set(artifacts) == set(receipt['files']), 'Artifact set mismatch')
    decoded = {}
    for name, raw in artifacts.items():
        require(digest(raw) == receipt['files'][name], 'Artifact hash mismatch')
        decoded[name] = parse(raw)
    selection = decoded['selection.json']
    require(selection['train_sha256'] == digest(train_bytes), 'Training membership hash mismatch')
    training = {i.study_id for i in accepted_pants_members(train_bytes, 'train')}
    pairs = selection['pairs']
    require(set(artifacts) == {'selection.json'} | {f'pair-{i:02d}.json' for i in range(len(pairs))},
            'Pair inventory mismatch')
    require(len(pairs) == len(receipt['summaries']), 'Summary count mismatch')
    records, seen, sources = [], set(), {}
    for index, target in enumerate(pairs):
        study = 'pants:study:' + target['study']
        structure = target['structure']
        require(study in training, 'Non-training study')
        require((study, structure) not in seen, 'Duplicate pair')
        seen.add((study, structure))
        name = f'pair-{index:02d}.json'
        pair = decoded[name]
        require(pair['audit_version'] == 'voxel-audit-v1.1', 'Unsupported audit version')
        require(pair['grid']['compatible'] is True, 'Incompatible grids')
        for role in ('ct', 'mask'):
            volume = pair[role]
            require(volume['role'] == role, 'Wrong volume role')
            ref = volume['file']
            file_reference(ref)
            require(ref['uri'] == target[role], 'Selection URI mismatch')
            require(ref['root_alias'] == 'followup_source', 'Unexpected source alias')
            parts = ref['uri'].split('/')
            require(parts[1] == target['study'], 'Cross-study source')
            require(parts[-1] == ('ct.nii.gz' if role == 'ct' else structure + '.nii.gz'),
                    'Wrong structure file')
            require(receipt['source_hashes'].get(ref['uri']) == ref['content_sha256'],
                    'Source hash mismatch')
            require(ref['uri'] not in sources or sources[ref['uri']] == ref['content_sha256'],
                    'Repeated source changed')
            sources[ref['uri']] = ref['content_sha256']
            require(volume['status'] == 'measured' and volume['stop'] is None,
                    'Incomplete volume audit')
            voxels = volume['voxels']
            count = voxels['count']
            require(type(count) is int and count > 0 and count == volume['header']['voxels']
                    and count == math.prod(volume['header']['shape']), 'Voxel count mismatch')
            require(voxels['finite'] == count and not any(voxels['nonfinite'].values())
                    and voxels['stored_nonfinite'] == 0 and voxels['scaled_overflow_voxels'] == 0
                    and voxels['float64_precision_loss_risk'] is False, 'Unsafe voxel evidence')
        mask = pair['mask']
        interpretation = pair.get('unit_interpretation')
        if interpretation is not None:
            require(interpretation['study_id'] == study
                    and interpretation['ct_sha256'] == pair['ct']['file']['content_sha256']
                    and interpretation['mask_sha256'] == mask['file']['content_sha256'],
                    'Unit interpretation identity mismatch')
        observed = mask['mask']
        values, counts = observed['distinct_values'], observed['value_counts']
        require(observed['distinct_values_truncated'] is False and counts is not None,
                'Incomplete value inventory')
        require(len(values) == len(set(values)) and [row[0] for row in counts] == values,
                'Value inventory mismatch')
        require(all(type(n) is int and n > 0 for _, n in counts), 'Invalid value count')
        require(sum(n for _, n in counts) == mask['voxels']['count'], 'Value counts incomplete')
        foreground = sum(n for value, n in counts if value != 0)
        require(foreground == observed['nonzero_voxels']
                and observed['empty'] is (foreground == 0), 'Foreground summary mismatch')
        summary = receipt['summaries'][index]
        require(summary['study'] == target['study'] and summary['structure'] == structure
                and summary['mask'] == observed, 'Receipt summary mismatch')
        if structure not in ('pancreas', 'pancreatic_lesion'):
            continue  # Supporting liver/lung evidence verified, not relabeled pancreas.
        record = dict(schema_version='linked-audit-assessment-v1', study_id=study,
                      structure=structure, source=deepcopy(mask['file']),
                      ct_source=deepcopy(pair['ct']['file']), audit_sha256=receipt['files'][name],
                      receipt_sha256=expected_receipt_sha256,
                      semantic_value_counts=deepcopy(counts),
                      values_basis=mask['voxels']['values_basis'],
                      effective_scaling=deepcopy(mask['scaling']),
                      stored_range=[mask['voxels']['stored_min'], mask['voxels']['stored_max']],
                      complete_stored_value_set=None, mapping_status='unapproved',
                      spatial_units=mask['spatial_units'],
                      unit_interpretation=deepcopy(pair.get('unit_interpretation')),
                      allowed_uses=[], eligibility='not_granted')
        if structure == 'pancreas':
            record['purpose_assessments'] = [assess_purpose(
                study_id=study, source_sha256=mask['file']['content_sha256'],
                audit_sha256=receipt['files'][name], foreground_voxels=foreground,
                coverage='uncertain', coverage_evidence_sha256=None, purpose=purpose)
                for purpose in ('pancreas_present_localizer', 'anatomy_absent_robustness')]
        record['record_id'] = 'linked-assessment:' + digest(canonical(record))
        records.append(record)
    require(sources == receipt['source_hashes'], 'Source inventory mismatch')
    return sorted(records, key=lambda row: (row['study_id'], row['structure']))


def link_coverage_reference(record, *, evidence_bytes, expected_sha256, bone_bytes,
                            review_bytes):
    """Link the known case-78 visual review without adjudicating coverage."""
    require(record['study_id'] == 'pants:study:PanTS_00000078'
            and record['structure'] == 'pancreas', 'Wrong coverage review target')
    require(digest(evidence_bytes) == expected_sha256, 'Coverage evidence hash mismatch')
    evidence = parse(evidence_bytes)
    source = evidence['source']['file']
    require(all(source[key] == record['ct_source'][key]
                for key in ('uri', 'content_sha256', 'bytes')), 'Coverage CT mismatch')
    require(digest(bone_bytes) == evidence['views']['bone.png']['sha256'], 'Coverage image mismatch')
    result = deepcopy(record)
    result.pop('record_id')
    result['coverage_review_reference'] = dict(evidence_sha256=expected_sha256,
        bone_sha256=digest(bone_bytes), review_sha256=digest(review_bytes),
        status='provisional_review_not_adjudication', coverage_assessment='unchanged_uncertain')
    result['record_id'] = 'linked-assessment:' + digest(canonical(result))
    return result
