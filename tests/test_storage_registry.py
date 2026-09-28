"""Setup registry shape tests only; no drive access or production resolver claim."""
from copy import deepcopy
import json
from pathlib import Path

from jsonschema import Draft202012Validator
import pytest
import yaml

pytestmark = pytest.mark.contract
CONFIG = Path(__file__).resolve().parents[1] / "configs/local"


def registry_and_validator():
    data = yaml.safe_load((CONFIG / "roots.example.yaml").read_text())
    schema = json.loads((CONFIG / "roots.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    validator.validate(data)
    return deepcopy(data), validator


def test_setup_example_is_valid():
    registry_and_validator()


def test_setup_does_not_enable_scientific_runs():
    data, validator = registry_and_validator()
    data["scientific_runs_enabled"] = True
    assert list(validator.iter_errors(data))


def test_unverified_source_cannot_have_an_active_path():
    data, validator = registry_and_validator()
    data["roots"]["pants_source"]["path"] = "/example/unverified"
    assert list(validator.iter_errors(data))


def test_backup_cannot_claim_primary_failure_domain():
    data, validator = registry_and_validator()
    data["roots"]["prowl_backup"]["failure_domain"] = "external_primary"
    assert list(validator.iter_errors(data))


@pytest.mark.parametrize(("field", "value"), [
    ("cap_bytes", 21474836481), ("minimum_free_bytes", 0), ("automatic_deletion", True),
])
def test_backup_policy_cannot_be_silently_relaxed(field, value):
    data, validator = registry_and_validator()
    data["roots"]["prowl_backup"][field] = value
    assert list(validator.iter_errors(data))


def test_existing_setup_registry_without_literature_aliases_remains_valid():
    data, validator = registry_and_validator()
    del data['roots']['literature_source']
    del data['roots']['prowl_literature_db']
    validator.validate(data)


@pytest.mark.parametrize('alias', ['literature_source', 'prowl_literature_db'])
@pytest.mark.parametrize(('field', 'value'), [
    ('path', '/example/active'), ('access', 'controlled_write'),
    ('failure_domain', 'internal_backup'), ('role', 'artifact'),
])
def test_literature_planning_aliases_cannot_activate_or_claim_independent_storage(alias, field, value):
    data, validator = registry_and_validator()
    data['roots'][alias][field] = value
    assert list(validator.iter_errors(data))
