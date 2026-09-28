import pytest

from src.data.annotation_assessment import assess_purpose, encoding_evidence

pytestmark = pytest.mark.unit


def encoding(**overrides):
    args = dict(source_sha256='a'*64, audit_sha256='b'*64, stored_values=[-128, 127],
                slope=0.003921568859368563, intercept=0.501960813999176)
    return encoding_evidence(**(args | overrides))


def assess(**overrides):
    args = dict(study_id='pants:study:PanTS_00000078', source_sha256='a'*64,
                audit_sha256='b'*64, foreground_voxels=0, coverage='absent',
                coverage_evidence_sha256='c'*64, purpose='pancreas_present_localizer')
    return assess_purpose(**(args | overrides))


def test_preserves_measured_scaling_without_claiming_canonical_source_one():
    result = encoding()
    assert result['observed_values'] == [dict(stored=-128, scaled=0.0),
                                         dict(stored=127, scaled=1.0000000591389835)]
    assert result['canonical_values'] is None
    assert result['mapping_status'] == 'unapproved'
    assert encoding(stored_values=[127, -128]) == result


@pytest.mark.parametrize('override', [dict(slope=0), dict(slope=float('inf')),
    dict(intercept=float('nan')), dict(stored_values=[]), dict(stored_values=[0, 0]),
    dict(stored_values=[True]), dict(stored_values=[float('inf')]),
    dict(source_sha256='missing'), dict(audit_sha256=None),
    dict(stored_values=[1e308], slope=1e308)])
def test_invalid_encoding_fails(override):
    with pytest.raises(ValueError): encoding(**override)


@pytest.mark.parametrize('coverage,count,purpose,state,reason', [
    ('absent', 0, 'pancreas_present_localizer', 'out_of_purpose', 'anatomy_absent'),
    ('absent', 0, 'anatomy_absent_robustness', 'candidate', 'anatomy_absent'),
    ('present', 10, 'pancreas_present_localizer', 'candidate', 'anatomy_present'),
    ('present', 10, 'anatomy_absent_robustness', 'out_of_purpose', 'anatomy_present'),
    ('present', 0, 'pancreas_present_localizer', 'unresolved', 'visible_anatomy_without_target'),
    ('absent', 10, 'anatomy_absent_robustness', 'unresolved', 'coverage_and_foreground_conflict'),
    ('uncertain', 0, 'anatomy_absent_robustness', 'unresolved', 'coverage_uncertain'),
    ('uncertain', 10, 'pancreas_present_localizer', 'unresolved', 'coverage_uncertain'),
])
def test_purpose_matrix_never_promotes(coverage, count, purpose, state, reason):
    result = assess(coverage=coverage, foreground_voxels=count, purpose=purpose)
    assert (result['disposition'], result['reason']) == (state, reason)
    assert result['allowed_uses'] == []
    assert result['eligibility'] == 'not_granted'
    assert result['preserve_source'] is True
    assert result['protected_membership'] == 'unchanged'
    assert 'diagnosis' not in result


@pytest.mark.parametrize('override', [dict(coverage='negative'), dict(purpose='cancer_negative'),
    dict(foreground_voxels=-1), dict(foreground_voxels=True), dict(foreground_voxels=1.5),
    dict(coverage_evidence_sha256=None), dict(study_id='78')])
def test_invalid_assessment_fails(override):
    with pytest.raises(ValueError): assess(**override)


def test_uncertain_coverage_can_lack_review_but_cannot_become_negative():
    assert assess(coverage='uncertain', coverage_evidence_sha256=None)['disposition'] == 'unresolved'


def test_identity_stable_and_evidence_purpose_sensitive():
    result = assess()
    assert result == assess()
    assert result['assessment_id'] != assess(audit_sha256='d'*64)['assessment_id']
    assert result['assessment_id'] != assess(purpose='anatomy_absent_robustness')['assessment_id']
