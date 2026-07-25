"""Tests for the test-cohort builder + MLflow registration (M4A1 §2/§1).
    python tests/test_deploy_extras.py
The cohort tests are dependency-light (pandas); the register test mocks mlflow and imports
register_to_mlflow lazily (it pulls torch) so it runs on the Mac.
"""
import sys
import tempfile
import unittest.mock as m
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd

from scripts.make_test_cohorts import build_cohorts, write_ids


def _man():
    return pd.DataFrame({"case_id": ["a", "b", "c", "d"], "has_lesion": [True, False, True, False]})


def test_build_cohorts_counts_and_disjoint():
    pos, neg = build_cohorts(_man(), {"a", "b", "c", "d"})
    assert pos == ["a", "c"] and neg == ["b", "d"]
    assert not (set(pos) & set(neg))


def test_build_cohorts_limit():
    pos, neg = build_cohorts(_man(), {"a", "b", "c", "d"}, n_pos=1, n_neg=1)
    assert pos == ["a"] and neg == ["b"]


def test_build_cohorts_empty_raises():
    man = pd.DataFrame({"case_id": ["a", "b"], "has_lesion": [False, False]})   # no positives
    raised = False
    try:
        build_cohorts(man, {"a", "b"})
    except AssertionError as e:
        raised = "empty" in str(e).lower()
    assert raised, "expected empty-cohort rejection"


def test_build_cohorts_rejects_duplicate_manifest_ids():
    man = pd.DataFrame({"case_id": ["a", "a", "b"], "has_lesion": [True, True, False]})
    raised = False
    try:
        build_cohorts(man, {"a", "b"})
    except AssertionError as e:
        raised = "duplicate" in str(e).lower()
    assert raised, "expected duplicate case_id rejection"


def test_build_cohorts_rejects_missing_test_id():
    man = pd.DataFrame({"case_id": ["a"], "has_lesion": [True]})
    raised = False
    try:
        build_cohorts(man, {"a", "MISSING"})     # MISSING has no manifest row
    except AssertionError as e:
        raised = "absent" in str(e).lower()
    assert raised, "expected missing-id rejection (real membership check, not a tautology)"


def test_build_cohorts_expected_count_mismatch():
    man = pd.DataFrame({"case_id": ["a", "b", "c"], "has_lesion": [True, False, False]})
    raised = False
    try:
        build_cohorts(man, {"a", "b", "c"}, expected_pos=99)   # only 1 positive exists
    except AssertionError as e:
        raised = "expected" in str(e).lower()
    assert raised, "expected count-mismatch rejection"


def test_write_ids_refuse_overwrite():
    d = Path(tempfile.mkdtemp())
    p = d / "test_pos.txt"
    write_ids(p, ["a", "b"])
    write_ids(p, ["a", "b"])                 # identical -> allowed
    try:
        write_ids(p, ["a", "c"])             # different -> refuse
        raise AssertionError("expected SystemExit on non-identical overwrite")
    except SystemExit:
        pass


def test_register_mlflow_args():
    """Mac-only (imports torch via register_model). Mocks mlflow; asserts the registration calls."""
    mlflow = m.MagicMock()
    info = m.MagicMock(); info.registered_model_version = "3"
    mlflow.pytorch.log_model.return_value = info
    mlflow.start_run.return_value.__enter__.return_value.info.run_id = "run123"
    with m.patch.dict(sys.modules, {"mlflow": mlflow, "mlflow.pytorch": mlflow.pytorch}):
        from scripts.register_model import register_to_mlflow, MODEL_NAME
        cfg = {"mlflow": {}, "model": {"out_channels": 3}}
        version, run_id = register_to_mlflow(model=object(), cfg=cfg, ckpt_path="x.pt",
                                             ckpt_sha="deadbeef", step=100, meta={}, params={"roi": 128})
    assert version == "3" and run_id == "run123"
    mlflow.pytorch.log_model.assert_called_once()
    kw = mlflow.pytorch.log_model.call_args.kwargs
    assert kw.get("registered_model_name") == MODEL_NAME
    assert kw.get("serialization_format") == "pickle"    # MLflow 3.x: avoid PT2 input_example requirement
    mlflow.log_dict.assert_any_call(cfg, "resolved_config.json")


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    fails = []
    for fn in fns:
        try:
            fn(); print(f"  PASS  {fn.__name__}")
        except Exception as e:
            fails.append(fn.__name__); print(f"  FAIL  {fn.__name__}: {e}")
    print(f"\n{len(fns) - len(fails)}/{len(fns)} passed.")
    if fails:
        sys.exit(1)   # fail closed so CI cannot report a false pass


if __name__ == "__main__":
    _run_all()
