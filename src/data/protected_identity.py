"""Plan 02 identity/migration guards, not a frozen cohort loader or eligibility gate."""
from dataclasses import dataclass
import hashlib
import re


BASE_INPUTS = {
    'train': (7200, 'bfc827ac52346e4636ed3a58581d5f55a9f1e80983bbfd6228c928babd519fc8'),
    'validation': (1800, '57549ba515b4d4f3297556a12e8e7c7df43a1f06de0c2f8296b4e5f16c87d2b1'),
    'test': (901, '7a323774be8c4459024f6e26113b84a4f892f52c954f42c3d033234e1e7b338e'),
}


@dataclass(frozen=True)
class Identity:
    """Internal discovery identity only; not a substitute for study/subject schemas."""
    source: str
    study_id: str
    subject_id: str
    source_partition: str
    identity_method: str
    identity_assurance: str


def pants_identity(raw_id):
    if not isinstance(raw_id, str) or not re.fullmatch(r'PanTS_[0-9]{8}', raw_id):
        raise ValueError('Invalid pinned PanTS identifier')
    number = int(raw_id[6:])
    if not 1 <= number <= 9901:
        raise ValueError('PanTS identifier outside pinned source range')
    return Identity('pants', f'pants:study:{raw_id}', f'pants:subject:{raw_id}',
                    'publisher_train' if number <= 9000 else 'publisher_test',
                    'study_as_subject_fallback', 'unverified_unique')


def panorama_identity(study_id, patient_id):
    # Require the explicit metadata patient key, never derive it from the study name.
    if not isinstance(study_id, str) or not re.fullmatch(r'[0-9]{6}_[0-9]{5}', study_id):
        raise ValueError('Invalid PANORAMA study identifier')
    if not isinstance(patient_id, str) or not re.fullmatch(r'[0-9]{6}', patient_id):
        raise ValueError('Explicit PANORAMA patient identifier required')
    return Identity('panorama', f'panorama:study:{study_id}',
                    f'panorama:subject:{patient_id}', 'unspecified',
                    'source_subject_id', 'direct_metadata')


def panorama_ct_study(filename):
    """Pinned single-channel release only; reject future channels for explicit review."""
    if not isinstance(filename, str):
        raise ValueError('Invalid PANORAMA CT filename')
    match = re.fullmatch(r'([0-9]{6}_[0-9]{5})_0000\.nii\.gz', filename)
    if not match:
        raise ValueError('Expected pinned PANORAMA channel 0000 filename')
    return match.group(1)


def validate_role_assignments(assignments):
    """Reject duplicate studies, cross-role subjects, and publisher-test misuse.

    Callers supply identities from the source adapters. This is a local identity guard,
    not full cohort validation: duplicate protection groups, eligibility, ancestry,
    snapshot/hash verification and annotation permissions remain separate gates.
    """
    studies, subjects = set(), {}
    counts = {role: 0 for role in BASE_INPUTS}
    for identity, role in assignments:
        if role not in counts:
            raise ValueError('Unknown protected role')
        if identity.study_id in studies:
            raise ValueError('Duplicate study assignment')
        studies.add(identity.study_id)
        if identity.source_partition == 'publisher_test' and role != 'test':
            raise ValueError('Publisher test study must retain test role')
        previous = subjects.setdefault(identity.subject_id, role)
        if previous != role:
            raise ValueError('Subject crosses protected roles')
        counts[role] += 1
    return counts


def accepted_pants_members(raw_bytes, role):
    """Only exact approved base-file bytes may enter the compatibility migration."""
    if role not in BASE_INPUTS:
        raise ValueError('Unregistered migration role')
    count, digest = BASE_INPUTS[role]
    if hashlib.sha256(raw_bytes).hexdigest() != digest:
        raise ValueError('Unregistered or changed legacy membership bytes')
    ids = raw_bytes.decode('utf-8').splitlines()
    if len(ids) != count or len(set(ids)) != count:
        raise ValueError('Incorrect or duplicate legacy membership')
    identities = tuple(pants_identity(raw_id) for raw_id in ids)
    validate_role_assignments((identity, role) for identity in identities)
    return identities
