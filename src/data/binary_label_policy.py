"""Approved strict binary rule; not wired into a dataset or training consumer.

Input must be semantic values AFTER NIfTI scaling, never stored bytes. Explicit policy
choice is mandatory; acceptance says nothing about source provenance or eligibility.
"""
import numpy as np

PROPOSED_POLICY = 'pants-semantic-binary-atol1e-6-candidate-v1'
APPROVED_POLICY = 'pants-semantic-binary-atol1e-6-v1'


def decode_binary(values, *, policy):
    if policy not in (PROPOSED_POLICY, APPROVED_POLICY):
        raise ValueError('Explicit supported binary policy required')
    values = np.asarray(values)
    if values.dtype.kind not in 'biuf' or values.ndim != 3 or values.size == 0:
        raise ValueError('Nonempty 3D real semantic label array required')
    if not np.isfinite(values).all():
        raise ValueError('Nonfinite label value')
    # Absolute distance only. Do not apply relative tolerance, >0, clipping, or rounding
    # before checking that EVERY voxel belongs to one of the two permitted clusters.
    background = np.abs(values.astype(np.float64)) <= 1e-6
    foreground = np.abs(values.astype(np.float64) - 1.0) <= 1e-6
    if not np.all(background | foreground):
        raise ValueError('Values outside binary endpoint tolerance')
    decoded = foreground.astype(np.uint8)
    changed = int(np.count_nonzero(values != decoded))
    return decoded, dict(policy=policy, input_basis='nifti_scaled_semantic',
                         absolute_tolerance=1e-6, relative_tolerance=0,
                         voxel_count=int(values.size), foreground_voxels=int(decoded.sum()),
                         normalized_voxels=changed, eligibility='not_assessed')
