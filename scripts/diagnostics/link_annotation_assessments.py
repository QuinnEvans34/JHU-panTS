"""Fixed local saved-evidence replay. No external-drive or scan reads."""
from pathlib import Path
from uuid import uuid4

from src.data.audit_assessment_link import link_audits, link_coverage_reference
from src.data.manifest_records import canonical, digest

REPO = Path(__file__).resolve().parents[2]
AUDIT = 'outputs/prowl/voxel-followup-140effff-129c-4ff8-b455-70a2119707a1'
COVERAGE = 'outputs/prowl/case78-coverage-c48e03d8-9d04-477e-8792-3a9c413128ed'
RECEIPT_SHA = '575acdd7e71861a6400bcafb89547b53c1859ed810619ec571b4b9f9f1f82d98'
COVERAGE_SHA = 'b0afbccb8fde6fd5561525d5fffcc7d1f1907b20b2388123684dbcd2e32fcb1c'


def main():
    inputs = {}
    def read(relative):
        path = REPO / relative
        if path.resolve() != path or not path.is_file() or path.stat().st_size > 10*1024*1024:
            raise ValueError('Noncanonical, missing or oversized local evidence')
        data = path.read_bytes()
        if len(data) > 10*1024*1024:
            raise ValueError('Evidence exceeds size limit')
        inputs[relative] = data
        return data
    receipt = read(AUDIT + '/receipt.json')
    # Fixed names, not untrusted receipt-controlled filesystem paths.
    artifacts = {name: read(AUDIT + '/' + name)
                 for name in ['selection.json'] + [f'pair-{i:02d}.json' for i in range(12)]}
    records = link_audits(receipt_bytes=receipt, expected_receipt_sha256=RECEIPT_SHA,
                         artifacts=artifacts, train_bytes=read('outputs/splits/train.txt'))
    evidence = read(COVERAGE + '/evidence.json')
    bone = read(COVERAGE + '/bone.png')
    review = read('docs/capstone/data/CASE78-COVERAGE-REVIEW-2026-09-28.md')
    records = [link_coverage_reference(row, evidence_bytes=evidence,
                    expected_sha256=COVERAGE_SHA, bone_bytes=bone, review_bytes=review)
               if row['study_id'] == 'pants:study:PanTS_00000078' and row['structure']=='pancreas'
               else row for row in records]
    payload = b''.join(canonical(row) for row in records)
    code = {name: digest(read(name)) for name in (
        'scripts/diagnostics/link_annotation_assessments.py', 'src/data/audit_assessment_link.py',
        'src/data/annotation_assessment.py', 'src/data/manifest_records.py',
        'src/data/protected_identity.py')}
    for relative, data in inputs.items():
        if (REPO / relative).read_bytes() != data:
            raise ValueError('Input changed during replay')
    parent = REPO / 'outputs/prowl'
    if parent.resolve() != parent or not parent.is_dir():
        raise ValueError('Noncanonical output parent')
    destination = parent / ('annotation-assessments-' + str(uuid4()))
    destination.mkdir(exist_ok=False)
    with (destination/'assessments.jsonl').open('xb') as stream:
        stream.write(payload)
    control = dict(status='diagnostic_complete_not_eligible', records=len(records),
        input_hashes={name:digest(raw) for name,raw in inputs.items()}, code_hashes=code,
        output_sha256=digest(payload), eligibility='not_granted',
        source_files_remeasured=False, protected_membership='unchanged')
    # Completion marker is last; failed writes never yield a completed package.
    with (destination/'receipt.json').open('xb') as stream:
        stream.write(canonical(control))
    print(destination)
    print(f'{len(records)} diagnostic records; no eligibility granted')


if __name__ == '__main__':
    main()
