"""Pure, non-promoting annotation evidence. No file access or training integration.

Caller-supplied evidence is referenced, not independently attested by this module.
This sidecar does not replace the v1 annotation/manifest contracts.
"""
import math
import re

from src.data.manifest_records import canonical, digest

VERSION = 'annotation-assessment-v1'
PURPOSES = ('pancreas_present_localizer', 'anatomy_absent_robustness')
COVERAGE = ('present', 'absent', 'uncertain')


def _hash(value):
    if not isinstance(value, str) or re.fullmatch('[0-9a-f]{64}', value) is None:
        raise ValueError('SHA-256 evidence identity required')
    return value


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError('Finite numeric encoding value required')
    try:
        valid = math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError('Finite numeric encoding value required')
    return value


def encoding_evidence(*, source_sha256, audit_sha256, stored_values, slope, intercept):
    """Record an explicitly complete observed value set, not a label mapping.

    slope/intercept must be the effective scaling measured by the audit. A truncated
    or unknown value set must not call this helper. Raw NIfTI sentinel/invalid scaling
    must be resolved by the existing audit, never normalized here.
    """
    _hash(source_sha256)
    _hash(audit_sha256)
    if not isinstance(stored_values, (list, tuple)) or not 1 <= len(stored_values) <= 1024:
        raise ValueError('Bounded complete observed value set required')
    values = [_number(v) for v in stored_values]
    if len(set(values)) != len(values):
        raise ValueError('Duplicate stored value')
    slope, intercept = _number(slope), _number(intercept)
    if slope == 0:
        raise ValueError('Effective scaling must not have zero slope')
    pairs = [dict(stored=v, scaled=_number(v * slope + intercept)) for v in sorted(values)]
    return dict(source_sha256=source_sha256, audit_sha256=audit_sha256,
                value_basis='stored_and_nifti_scaled', observed_values=pairs,
                effective_slope=slope, effective_intercept=intercept,
                mapping_status='unapproved', canonical_values=None)


def assess_purpose(*, study_id, source_sha256, audit_sha256, foreground_voxels,
                   coverage, coverage_evidence_sha256, purpose):
    """Return content-addressed candidate/disposition; NEVER grant allowed uses.

    foreground_voxels is the PANCREAS mask count, never the lesion count.
    Coverage refers to pancreas visibility, not disease. An empty mask alone cannot
    establish coverage. Explicit present/absent claims require a separate evidence hash.
    Evidence existence, provenance, geometry and clinical validity remain caller gates.
    """
    if not isinstance(study_id, str) or re.fullmatch(
            r'[a-z][a-z0-9_-]{1,31}:study:[A-Za-z0-9._-]{1,160}', study_id) is None:
        raise ValueError('Valid study identity required')
    _hash(source_sha256)
    _hash(audit_sha256)
    if type(foreground_voxels) is not int or foreground_voxels < 0:
        raise ValueError('Nonnegative integer foreground count required')
    if coverage not in COVERAGE or purpose not in PURPOSES:
        raise ValueError('Explicit supported coverage and purpose required')
    if coverage != 'uncertain' or coverage_evidence_sha256 is not None:
        _hash(coverage_evidence_sha256)
    state, reason = 'unresolved', 'coverage_uncertain'
    if coverage == 'absent' and foreground_voxels:
        reason = 'coverage_and_foreground_conflict'
    elif coverage == 'present' and not foreground_voxels:
        reason = 'visible_anatomy_without_target'
    elif coverage == 'absent':
        state = 'candidate' if purpose == 'anatomy_absent_robustness' else 'out_of_purpose'
        reason = 'anatomy_absent'
    elif coverage == 'present':
        state = 'candidate' if purpose == 'pancreas_present_localizer' else 'out_of_purpose'
        reason = 'anatomy_present'
    record = dict(schema_version=VERSION, structure='pancreas', study_id=study_id, source_sha256=source_sha256,
                  audit_sha256=audit_sha256, foreground_voxels=foreground_voxels,
                  coverage=coverage, coverage_evidence_sha256=coverage_evidence_sha256,
                  purpose=purpose, disposition=state, reason=reason,
                  allowed_uses=[], eligibility='not_granted', preserve_source=True,
                  protected_membership='unchanged')
    return dict(record, assessment_id='assessment:' + digest(canonical(record)))
