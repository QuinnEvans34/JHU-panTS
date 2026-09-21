"""Offline shape/format controls for existing Plan 01/02 contracts, not runtime conformance."""
import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker


pytestmark = pytest.mark.contract
ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "docs" / "capstone" / "contracts"
FIXTURES = Path(__file__).parent / "fixtures" / "contracts"
# Explicit scope: no Plan 04 run-manifest implementation before its walkthrough.
CONTRACT_NAMES = (
    "annotation-record", "case-package", "cohort-member", "cohort", "data-issue",
    "manifest", "review-event", "source-snapshot", "study-record", "subject-record",
)


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validator(name):
    schema = load_json(CONTRACTS / f"{name}.schema.json")
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def control(name):
    fixture = FIXTURES / f"{name}.synthetic.json"
    if not fixture.exists():
        fixture = CONTRACTS / "examples" / f"{name}.example.json"
    value = load_json(fixture)
    validator(name).validate(value)
    return value


@pytest.mark.parametrize("name", CONTRACT_NAMES)
def test_existing_contract_schema_and_example(name):
    validator(name).validate(load_json(CONTRACTS / "examples" / f"{name}.example.json"))


@pytest.mark.parametrize("name", ["cohort", "review-event"])
def test_hand_authored_positive_control(name):
    control(name)


@pytest.mark.parametrize(("name", "field", "invalid"), [
    pytest.param("cohort", "protected_role", "validation", id="training-cannot-be-validation"),
    pytest.param("cohort", "protected_role", "test", id="training-cannot-be-test"),
    pytest.param("cohort", "parent_cohort_ids", [], id="training-needs-parent"),
    pytest.param("cohort", "parent_cohort_ids", ["cohort:synthetic-parent:v1"] * 2,
                 id="duplicate-parent"),
    pytest.param("cohort", "manifest_ids", ["manifest:synthetic:bbbbbbbbbbbb"] * 2,
                 id="duplicate-manifest"),
    pytest.param("cohort", "members", None, id="frozen-needs-members"),
    pytest.param("cohort", "derivation_sha256", "short", id="full-derivation-hash"),
    pytest.param("subject-record", "identity_assurance", "direct_metadata",
                 id="fallback-not-proven-unique"),
    pytest.param("review-event", "recorded_at", "not-a-timestamp", id="format-checking-enabled"),
    pytest.param("review-event", "revision", 2, id="correction-needs-prior-event"),
    pytest.param("review-event", "action", "diagnose", id="review-not-diagnosis"),
])
def test_invalid_single_field_is_rejected(name, field, invalid):
    value = deepcopy(control(name))
    value[field] = invalid
    assert list(validator(name).iter_errors(value)), f"Accepted invalid {name}.{field}"


@pytest.mark.parametrize(("name", "field"), [
    ("case-package", "derivation_sha256"),
    ("review-event", "prediction_id"),
])
def test_identity_cannot_be_omitted(name, field):
    value = deepcopy(control(name))
    del value[field]
    assert list(validator(name).iter_errors(value)), f"Accepted missing {name}.{field}"


@pytest.mark.parametrize("uri", [
    "/private/synthetic.nii.gz", "C:/synthetic.nii.gz", "file:///synthetic.nii.gz",
    "../synthetic.nii.gz", "files/../synthetic.nii.gz",
])
def test_source_resource_rejects_absolute_or_parent_path(uri):
    value = deepcopy(control("study-record"))
    value["image"]["uri"] = uri
    assert list(validator("study-record").iter_errors(value)), f"Accepted unsafe path {uri}"


@pytest.mark.parametrize(("path", "invalid"), [
    (("schema_version",), "2.0.0"),
    (("prediction", "prediction_mode"), "diagnostic"),
    (("prediction", "status"), "success"),
    (("prediction", "inference_config_sha256"), "abc"),
    (("prediction", "localization", "confidence"), 1.01),
    (("prediction", "localization", "box_voxel_xyzxyz"), [0, 0, 0, 10, 10]),
    (("study", "ct", "bytes"), -1),
    (("study", "ct", "shape"), [512, 512, 0]),
    (("study", "spacing_mm"), [1, 0, 1]),
    (("measurements", "lesion_count"), 1.5),
    (("measurements", "lesion_volume_mm3"), -1),
    (("measurements", "review_score"), -0.01),
    (("measurements", "review_score"), 1.01),
    (("structured_finding", "measurement_source"), "clinical_diagnosis"),
    (("lineage", "code_commit"), "not-a-commit"),
])
def test_case_package_rejects_malformed_nested_value(path, invalid):
    value = deepcopy(control("case-package"))
    parent = value
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = invalid
    errors = list(validator("case-package").iter_errors(value))
    assert errors, f"Accepted malformed {path}"


@pytest.mark.parametrize("status", ["completed", "completed_with_warnings"])
def test_completed_prediction_requires_both_masks(status):
    value = deepcopy(control("case-package"))
    value["prediction"]["status"] = status
    validator("case-package").validate(value)
    for missing in ("pancreas_mask", "lesion_mask"):
        broken = deepcopy(value)
        del broken["prediction"]["files"][missing]
        assert list(validator("case-package").iter_errors(broken))
    del value["prediction"]["files"]
    assert list(validator("case-package").iter_errors(value))


def test_failed_prediction_can_explicitly_have_no_outputs():
    value = deepcopy(control("case-package"))
    value["prediction"]["status"] = "failed"
    value["prediction"]["failure_code"] = "SYNTHETIC_FAILURE"
    del value["prediction"]["files"]
    value["measurements"] = None
    value["structured_finding"] = None
    validator("case-package").validate(value)


@pytest.mark.parametrize("transport", ["static_export", "fastapi"])
def test_review_correction_contract_is_transport_neutral(transport):
    value = deepcopy(control("review-event"))
    value["client"]["transport"] = transport
    value["revision"] = 2
    value["supersedes_review_event_id"] = value["review_event_id"]
    value["review_event_id"] = "review:aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
    value["action"] = "edit_required"
    value["reason_codes"] = ["boundary_correction"]
    value["corrected_mask"] = None  # Review does not require browser voxel editing.
    validator("review-event").validate(value)
    value["supersedes_review_event_id"] = None
    assert list(validator("review-event").iter_errors(value))


@pytest.mark.parametrize("reasons", [[], ["missed_lesion"] * 2, ["diagnosis_confirmed"]])
def test_review_reason_codes_are_nonempty_unique_and_bounded(reasons):
    value = deepcopy(control("review-event"))
    value["reason_codes"] = reasons
    assert list(validator("review-event").iter_errors(value))


@pytest.mark.parametrize("name", ["case-package", "review-event"])
def test_unknown_top_level_fields_are_rejected(name):
    value = deepcopy(control(name))
    value["unexpected_field"] = True
    assert list(validator(name).iter_errors(value))
