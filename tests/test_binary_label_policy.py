import numpy as np
import pytest

from src.data.binary_label_policy import decode_binary, PROPOSED_POLICY, APPROVED_POLICY

pytestmark = pytest.mark.unit


def decode(values):
    return decode_binary(values, policy=PROPOSED_POLICY)


def test_real_observed_scaling_reproduced_without_source_files():
    stored = np.array([-128, 127], dtype=np.int8).reshape(1,1,2)
    scaled = stored.astype(np.float64) * 0.003921568859368563 + 0.501960813999176
    before = scaled.copy()
    result, evidence = decode(scaled)
    assert result.tolist() == [[[0,1]]]
    assert np.array_equal(before, scaled)
    assert evidence['normalized_voxels'] == 1
    assert evidence['eligibility'] == 'not_assessed'


@pytest.mark.parametrize('value', [0,1,1e-6,-1e-6,1-0.9e-6,1+0.9e-6])
def test_binary_endpoints_and_near_endpoints(value):
    result,_=decode(np.full((1,1,1),value))
    assert result.item() == int(value > .5)


@pytest.mark.parametrize('value', [1.01e-6,-1.01e-6,1-1.01e-6,1+1.01e-6,.5,2,-128,127,np.nan,np.inf,-np.inf])
def test_ambiguous_or_raw_storage_values_rejected(value):
    with pytest.raises(ValueError): decode(np.array([[[value]]]))


def test_one_invalid_voxel_rejects_whole_array():
    with pytest.raises(ValueError): decode(np.array([[[0,1,.2]]]))


@pytest.mark.parametrize('values',[np.array([]),np.zeros((2,2)),np.zeros((1,1,1,1)),np.array([[['1']]]),np.ones((1,1,1),complex)])
def test_shape_and_type_rejection(values):
    with pytest.raises(ValueError): decode(values)


def test_policy_must_be_explicit():
    with pytest.raises(ValueError): decode_binary(np.zeros((1,1,1)),policy='unapproved')
    with pytest.raises(TypeError): decode_binary(np.zeros((1,1,1)))


def test_empty_foreground_is_not_missing_or_clinical_negative():
    result,evidence=decode(np.zeros((2,2,2)))
    assert evidence['foreground_voxels']==0
    assert 'diagnosis' not in evidence
    assert result.dtype==np.uint8


@pytest.mark.parametrize('values',[np.array([[[0.,1.0000000591389835]]]),np.zeros((1,1,2))])
def test_approved_policy_same_math_distinct_identity_and_no_permission(values):
    before=values.copy()
    old,old_evidence=decode_binary(values,policy=PROPOSED_POLICY)
    new,evidence=decode_binary(values,policy=APPROVED_POLICY)
    assert np.array_equal(old,new) and np.array_equal(values,before)
    assert evidence['policy']==APPROVED_POLICY!=old_evidence['policy']
    assert evidence['eligibility']=='not_assessed'
    assert not np.shares_memory(new,values)


@pytest.mark.parametrize('value',[.5,2,-128,np.nan,np.inf,1+1.01e-6])
def test_approval_does_not_relax_rejection(value):
    with pytest.raises(ValueError): decode_binary(np.array([[[value]]]),policy=APPROVED_POLICY)
