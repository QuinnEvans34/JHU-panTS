import json

import pytest

from scripts.diagnostics.inventory_sources import (collisions, digest, infer_shape, inventory,
                                                   logical_stem, mask, walk)

UNIT = pytest.mark.unit
COMPONENT = pytest.mark.component


def build(root, tree):
    for relative, size in tree.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'x' * size)
    return root


@pytest.fixture
def pants_labels(tmp_path):
    """Directory per case, several segmentation files inside — the PanTS label shape."""
    root = tmp_path / 'labels'
    tree = {}
    for i in range(1, 21):
        case = f'PanTS_{i:08d}'
        tree[f'{case}/combined_labels.nii.gz'] = 900 + i
        tree[f'{case}/segmentations/pancreas.nii.gz'] = 400 + i
        tree[f'{case}/segmentations/liver.nii.gz'] = 500 + i
    return build(root, tree)


@pytest.fixture
def panorama_ct(tmp_path):
    """Flat files, one per case — the PANORAMA batch shape."""
    root = tmp_path / 'batch'
    return build(root, {f'{100000 + i}_00001_0000.nii.gz': 700 + i for i in range(1, 16)})


# --- shape inference --------------------------------------------------------------------------

@UNIT
@pytest.mark.parametrize('name,expected', [
    ('PanTS_00000001.nii.gz', 'PanTS_00000001'),
    ('combined_labels.nii.gz', 'combined_labels'),
    ('metadata.xlsx', 'metadata'),
    ('noextension', 'noextension'),
    ('.hidden', '.hidden'),
])
def test_logical_stem(name, expected):
    assert logical_stem(name) == expected


@UNIT
def test_mask_groups_identifiers_by_shape():
    assert mask('PanTS_00000001') == mask('PanTS_00009901') == 'PanTS_#'
    assert mask('100001_00001_0000') == '#_#_#'


@COMPONENT
def test_directory_per_case_is_detected(pants_labels):
    entries, *_ = walk(pants_labels)
    shape, ids = infer_shape(pants_labels, entries)
    assert shape == 'directory_per_case' and len(ids) == 20


@COMPONENT
def test_file_per_case_is_detected(panorama_ct):
    entries, *_ = walk(panorama_ct)
    shape, ids = infer_shape(panorama_ct, entries)
    assert shape == 'file_per_case' and len(ids) == 15


# --- structural reporting ---------------------------------------------------------------------

@COMPONENT
def test_structures_collapse_to_the_layout_fingerprint(pants_labels):
    report = inventory('pants-labels', pants_labels)
    assert report['cases'] == 20 and report['files'] == 60
    assert report['structures']['PanTS_#/combined_labels.nii.gz']['count'] == 20
    assert report['structures']['PanTS_#/segmentations/pancreas.nii.gz']['count'] == 20
    assert report['identifier_patterns'] == {'PanTS_#': 20}
    assert report['incomplete_cases']['count'] == 0


@COMPONENT
def test_incomplete_cases_are_surfaced(pants_labels):
    (pants_labels / 'PanTS_00000007' / 'segmentations' / 'pancreas.nii.gz').unlink()
    (pants_labels / 'PanTS_00000013' / 'combined_labels.nii.gz').unlink()
    report = inventory('pants-labels', pants_labels)
    assert report['incomplete_cases']['count'] == 2
    assert set(report['incomplete_cases']['sample']) == {'PanTS_00000007', 'PanTS_00000013'}
    assert report['complete_combination']['cases'] == 18


@COMPONENT
def test_zero_byte_files_are_flagged(pants_labels):
    # The previous project found these were genuine source defects, not a reader bug.
    (pants_labels / 'PanTS_00000004' / 'combined_labels.nii.gz').write_bytes(b'')
    report = inventory('pants-labels', pants_labels)
    assert report['zero_byte_files']['count'] == 1
    assert 'PanTS_00000004/combined_labels.nii.gz' in report['zero_byte_files']['sample']


@COMPONENT
def test_oversized_case_is_flagged_as_an_outlier(pants_labels):
    (pants_labels / 'PanTS_00000009' / 'combined_labels.nii.gz').write_bytes(b'x' * 500_000)
    report = inventory('pants-labels', pants_labels)
    assert any(o['case'] == 'PanTS_00000009' and o['median_ratio'] >= 10
               for o in report['size_outliers'])


@COMPONENT
def test_symlinks_are_reported_not_followed(tmp_path, pants_labels):
    target = tmp_path / 'outside.nii.gz'
    target.write_bytes(b'x' * 50)
    (pants_labels / 'PanTS_00000001' / 'sneaky.nii.gz').symlink_to(target)
    report = inventory('pants-labels', pants_labels)
    assert report['symlinks']['count'] == 1
    assert report['files'] == 60, 'a symlink must not be counted as a regular file'


@COMPONENT
def test_empty_tree_reports_nothing_rather_than_guessing(tmp_path):
    empty = tmp_path / 'empty'
    empty.mkdir()
    report = inventory('nothing', empty)
    assert report['files'] == 0 and 'shape' not in report


# --- cross-source identity ----------------------------------------------------------------------

@COMPONENT
def test_disjoint_identifiers_report_zero_overlap(pants_labels, panorama_ct):
    reports = [inventory('pants', pants_labels), inventory('panorama', panorama_ct)]
    overlap = collisions(reports)[0]
    assert overlap['shared'] == 0
    assert overlap['left_only'] == 20 and overlap['right_only'] == 15


@COMPONENT
def test_colliding_identifiers_are_detected(tmp_path):
    """The failure this exists to prevent: two sources using one identifier namespace."""
    a = build(tmp_path / 'a', {f'CASE_{i:04d}/image.nii.gz': 100 for i in range(1, 11)})
    b = build(tmp_path / 'b', {f'CASE_{i:04d}/image.nii.gz': 100 for i in range(6, 16)})
    overlap = collisions([inventory('source-a', a), inventory('source-b', b)])[0]
    assert overlap['shared'] == 5
    assert overlap['sample'][0] == 'CASE_0006'


# --- output -----------------------------------------------------------------------------------

@COMPONENT
def test_digest_states_what_it_does_not_establish(pants_labels, panorama_ct):
    reports = [inventory('pants', pants_labels), inventory('panorama', panorama_ct)]
    text = digest(reports, collisions(reports))
    assert 'PanTS_#/segmentations/pancreas.nii.gz' in text
    assert 'directory_per_case' in text and 'file_per_case' in text
    for disclaimer in ('no geometry, label semantics', 'does **not** prove the same subject',
                       'does not prove subject disjointness'):
        assert disclaimer in text


@COMPONENT
def test_record_is_json_serialisable(pants_labels):
    json.dumps(inventory('pants-labels', pants_labels))


@COMPONENT
def test_digest_names_defects_and_agrees_with_itself(pants_labels):
    (pants_labels / 'PanTS_00000004' / 'combined_labels.nii.gz').write_bytes(b'')
    (pants_labels / 'PanTS_00000007' / 'segmentations' / 'pancreas.nii.gz').unlink()
    (pants_labels / 'PanTS_00000009' / 'combined_labels.nii.gz').write_bytes(b'x' * 500_000)
    report = inventory('pants-labels', pants_labels)
    text = digest([report], [])
    assert '1 case differ' in text and '1 cases' not in text, 'singular must not read as plural'
    assert 'PanTS_00000007' in text and 'PanTS_00000004' in text and 'PanTS_00000009' in text


# --- shape confidence: the PANORAMA-labels lesson -----------------------------------------------

from scripts.diagnostics.inventory_sources import assess, strip_wrapper  # noqa: E402


@pytest.fixture
def panorama_labels(tmp_path):
    """The real PANORAMA label archive shape, observed 2026-09-22.

    Everything sits under one repository-named folder, and the real cases live inside two
    category directories rather than at the top level.
    """
    root = tmp_path / 'extracted'
    wrapper = 'panorama_labels-bf1d6ba3230f6b093e7ea959a4bf5e2eba2e3665'
    tree = {f'{wrapper}/automatic_labels/{100000 + i}_{i:05d}.nii.gz': 520_000 for i in range(1, 51)}
    tree.update({f'{wrapper}/manual_labels/{100000 + i}_{i:05d}.nii.gz': 202_000
                 for i in range(1, 16)})
    tree[f'{wrapper}/clinical_information.xlsx'] = 114_329
    tree[f'{wrapper}/README.md'] = 4_220
    tree[f'{wrapper}/LICENSE.txt'] = 19_917
    tree[f'{wrapper}/.gitattributes'] = 66
    return build(root, tree)


@COMPONENT
def test_wrapper_directory_is_stripped_and_named(panorama_labels):
    working, skipped = strip_wrapper(panorama_labels)
    assert skipped == ['panorama_labels-bf1d6ba3230f6b093e7ea959a4bf5e2eba2e3665']
    assert (working / 'automatic_labels').is_dir()


@COMPONENT
def test_category_directories_are_flagged_as_low_confidence(panorama_labels):
    """Regression for the first real run: the tool reported '1 case' named after the archive.

    After stripping the wrapper it would otherwise report six 'cases' -- two category
    directories plus four loose files -- which is still the wrong level. It must say so.
    """
    report = inventory('panorama-labels', panorama_labels)
    assert report['shape_confidence'] == 'low'
    assert report['shape_concerns']
    assert report['wrapper_directories'] == [
        'panorama_labels-bf1d6ba3230f6b093e7ea959a4bf5e2eba2e3665']
    # The structural fingerprint stays correct and useful even when the case level is wrong.
    assert report['structures']['automatic_labels/#_#.nii.gz']['count'] == 50
    assert report['structures']['manual_labels/#_#.nii.gz']['count'] == 15
    text = digest([report], [])
    assert 'Low confidence in the inferred case level' in text
    assert 'Re-run with `--source` pointed at' in text


@COMPONENT
def test_pointing_at_the_real_case_level_gives_confidence(panorama_labels):
    inner = panorama_labels / 'panorama_labels-bf1d6ba3230f6b093e7ea959a4bf5e2eba2e3665'
    report = inventory('panorama-automatic', inner / 'automatic_labels')
    assert report['shape_confidence'] == 'ok'
    assert report['shape'] == 'file_per_case' and report['cases'] == 50


@COMPONENT
def test_label_class_overlap_answers_which_cases_have_both(panorama_labels):
    """Automatic and manual labels as two sources: the shared count is the answer Plan 03 needs."""
    inner = panorama_labels / 'panorama_labels-bf1d6ba3230f6b093e7ea959a4bf5e2eba2e3665'
    reports = [inventory('automatic', inner / 'automatic_labels'),
               inventory('manual', inner / 'manual_labels')]
    overlap = collisions(reports)[0]
    assert overlap['shared'] == 15 and overlap['left_only'] == 35 and overlap['right_only'] == 0


@UNIT
def test_healthy_inference_is_not_flagged(pants_labels):
    assert inventory('pants-labels', pants_labels)['shape_confidence'] == 'ok'


@UNIT
def test_assess_flags_a_single_candidate():
    assert assess({'only'}, {'only': 1}, {'only': 2242})


# --- merged sources: nine archive shards are one logical source ---------------------------------

@pytest.fixture
def sharded_images(tmp_path):
    """Mirrors PanTSMini_ImageTr_*: one directory per shard, disjoint case ranges."""
    roots = []
    for shard in range(3):
        root = tmp_path / f'shard_{shard}'
        build(root, {f'PanTS_{shard * 10 + i:08d}/ct.nii.gz': 1000 + i for i in range(1, 11)})
        roots.append(root)
    return roots


@COMPONENT
def test_shards_merge_into_one_source(sharded_images):
    report = inventory('pants-images', sharded_images)
    assert report['cases'] == 30 and report['files'] == 30
    assert report['structures']['PanTS_#/ct.nii.gz']['count'] == 30
    assert len(report['roots']) == 3
    assert report['duplicated_across_roots']['count'] == 0
    assert report['shape_confidence'] == 'ok'


@COMPONENT
def test_a_case_in_two_shards_is_reported_as_a_source_defect(sharded_images):
    """Shards should be disjoint. A case in two of them is a duplicate in the data itself."""
    build(sharded_images[1], {'PanTS_00000005/ct.nii.gz': 1234})
    report = inventory('pants-images', sharded_images)
    assert report['duplicated_across_roots']['count'] == 1
    assert report['duplicated_across_roots']['sample'] == ['PanTS_00000005']
    text = digest([report], [])
    assert 'appear in more than one of this source' in text
    assert 'duplicate in the source, not a merge artefact' in text


@COMPONENT
def test_merged_source_compares_against_another_source(sharded_images, tmp_path):
    labels = build(tmp_path / 'labels',
                   {f'PanTS_{i:08d}/seg.nii.gz': 500 for i in range(1, 26)})
    reports = [inventory('images', sharded_images), inventory('labels', [labels])]
    overlap = collisions(reports)[0]
    # 30 image cases, 25 label cases, overlapping where the ranges coincide.
    assert overlap['shared'] + overlap['left_only'] == 30
    assert overlap['shared'] + overlap['right_only'] == 25


@UNIT
def test_a_single_path_still_works_unwrapped(pants_labels):
    assert inventory('pants-labels', pants_labels)['cases'] == 20


# --- per-structure sizing: what it can and cannot tell us --------------------------------------

@pytest.fixture
def realistic_labels(tmp_path):
    """Proportioned like the real PanTS label tree observed on 2026-09-27.

    Medians there are ~130 KB per segmentation and ~820 KB for combined_labels. Crucially, a
    small field-of-view scan produces a small file for EVERY structure, because a compressed
    NIfTI's size tracks its voxel grid rather than how full the mask is.
    """
    root = tmp_path / 'labels'
    tree = {}
    for i in range(1, 31):
        case = f'PanTS_{i:08d}'
        tree[f'{case}/combined_labels.nii.gz'] = 819_623 + i * 100
        for organ, median in (('pancreas', 143_444), ('liver', 233_783), ('spleen', 156_439),
                              ('pancreatic_lesion', 128_442), ('prostate', 129_808)):
            tree[f'{case}/segmentations/{organ}.nii.gz'] = median + i * 50
    return build(root, tree)


@pytest.fixture
def single_structure(tmp_path):
    """One file per case, like PanTSMini_ImageTr and the PANORAMA batches."""
    return build(tmp_path / 'images', {f'PanTS_{i:08d}/ct.nii.gz': 34_406_388 for i in range(1, 21)})


TINY = 1_827


@COMPONENT
def test_a_small_scan_is_reported_as_a_scan_not_a_defect(realistic_labels):
    """The September 27 finding: near-identical counts across all 29 structures were one
    population of small scans, not 29 independent defects."""
    for path in (realistic_labels / 'PanTS_00000011').rglob('*.nii.gz'):
        path.write_bytes(b'x' * TINY)
    pops = inventory('pants-labels', realistic_labels)['size_populations']
    assert pops['small_grid']['count'] == 1
    assert pops['small_grid']['sample'] == ['PanTS_00000011']
    assert pops['structure_specific']['count'] == 0


@COMPONENT
def test_an_isolated_structure_names_which_one(realistic_labels):
    """The actionable part. Knowing 101 cases are anomalous is useless without knowing where."""
    (realistic_labels / 'PanTS_00000007' / 'segmentations' / 'pancreas.nii.gz').write_bytes(b'x' * TINY)
    pops = inventory('pants-labels', realistic_labels)['size_populations']
    assert pops['small_grid']['count'] == 0
    entry = pops['structure_specific']['sample'][0]
    assert entry['case'] == 'PanTS_00000007'
    assert entry['structures'] == ['pancreas.nii.gz']

    text = digest([inventory('pants-labels', realistic_labels)], [])
    assert 'Which structures the structure-specific cases are anomalous in' in text
    assert '`pancreas.nii.gz` | 1' in text


@COMPONENT
def test_the_populations_partition_the_flagged_cases(realistic_labels):
    """Every flagged case lands in exactly one bucket, so the numbers can be reconciled."""
    for path in (realistic_labels / 'PanTS_00000011').rglob('*.nii.gz'):
        path.write_bytes(b'x' * TINY)
    (realistic_labels / 'PanTS_00000007' / 'segmentations' / 'liver.nii.gz').write_bytes(b'x' * TINY)
    for organ in ('pancreas', 'liver', 'spleen'):
        (realistic_labels / 'PanTS_00000019' / 'segmentations' / f'{organ}.nii.gz').write_bytes(b'x' * TINY)

    pops = inventory('pants-labels', realistic_labels)['size_populations']
    assert pops['small_grid']['count'] == 1
    assert pops['structure_specific']['count'] == 1
    assert pops['intermediate']['count'] == 1, 'three-of-six is neither a small scan nor one bad file'


@COMPONENT
def test_one_structure_per_case_refuses_to_invent_a_distinction(single_structure):
    """Regression for the September 27 output, where a single-structure source reported the
    same 213 cases as both 'small scans' and 'structure-specific defects'. With one structure
    the two populations are identical, so the tool must decline rather than double-count."""
    (single_structure / 'PanTS_00000004' / 'ct.nii.gz').write_bytes(b'x' * 1000)
    pops = inventory('pants-images', single_structure)['size_populations']
    assert 'unavailable' in pops
    assert 'small_grid' not in pops and 'structure_specific' not in pops

    text = digest([inventory('pants-images', single_structure)], [])
    assert 'indistinguishable' in text
    assert 'small scans, not defects' not in text


@COMPONENT
def test_an_oversized_file_is_still_found(realistic_labels):
    (realistic_labels / 'PanTS_00000013' / 'combined_labels.nii.gz').write_bytes(b'x' * 20_000_000)
    flagged = inventory('pants-labels', realistic_labels)['per_structure_outliers']
    entry = flagged['PanTS_#/combined_labels.nii.gz']['large_for_structure']
    assert entry['count'] == 1 and entry['sample'][0]['case'] == 'PanTS_00000013'


@COMPONENT
def test_healthy_structures_are_not_flagged(realistic_labels):
    assert inventory('pants-labels', realistic_labels).get('per_structure_outliers') == {}


@COMPONENT
def test_digest_refuses_to_claim_it_can_detect_an_empty_mask(realistic_labels):
    """The first version said a near-empty file meant an absent structure. That is false:
    file size tracks the grid, not the content."""
    for path in (realistic_labels / 'PanTS_00000011').rglob('*.nii.gz'):
        path.write_bytes(b'x' * TINY)
    text = digest([inventory('pants-labels', realistic_labels)], [])
    assert 'measures grid size, not mask content' in text
    assert 'An empty mask cannot be detected from file size' in text
    assert 'requires reading voxels, which this tool does not do' in text
