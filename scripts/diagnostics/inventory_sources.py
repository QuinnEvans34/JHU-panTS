"""Read-only structural inventory of extracted source trees. Observation, not validation.

Answers the questions Plans 02 and 03 must be written against: what shape is the data, what do
the identifiers look like, which cases are incomplete, and do identifiers collide across sources.
It reads directory entries and file sizes only — never file contents, never voxels, never
headers. It makes no claim about geometry, label semantics, patient uniqueness, or eligibility,
and it does not enable a source alias.

Output is aggregated by structural pattern rather than listed per file, so a 287,128-file tree
still produces a small record. Write results under ignored outputs/, never into Git.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import statistics

# Suffixes that form one logical extension, longest first so .nii.gz wins over .gz.
COMPOUND = ('.nii.gz', '.tar.gz', '.seg.nrrd')
DIGITS = re.compile(r'\d+')
SAMPLE = 5
# An all-zero mask still compresses to a small but non-zero file, so a zero-byte test cannot see
# it. Thresholds are relative to each structure's own median, not an absolute byte count.
SMALL = 0.1
LARGE = 10
BROAD = 0.8        # small in >=80% of structures: the scan is small, not the mask
NARROW_MAX = 2     # small in <=2 structures: the structure is anomalous, not the scan
MIN_STRUCTURES = 3  # below this the two populations are indistinguishable


def utc():
    return datetime.now(timezone.utc).isoformat()


def emit(event, **values):
    print(json.dumps(dict(at=utc(), event=event, **values)), flush=True)


def logical_stem(name):
    """Strip one logical extension: 'PanTS_00000001.nii.gz' -> 'PanTS_00000001'."""
    lowered = name.lower()
    for suffix in COMPOUND:
        if lowered.endswith(suffix):
            return name[:-len(suffix)]
    return name.rsplit('.', 1)[0] if '.' in name[1:] else name


def mask(text):
    """Collapse digit runs so identifiers group by shape: 'PanTS_00000001' -> 'PanTS_#'."""
    return DIGITS.sub('#', text)


def plural(count, singular, suffix='s'):
    return f'{count:,} {singular}{"" if count == 1 else suffix}'


def describe(values):
    if not values:
        return None
    ordered = sorted(values)
    return dict(count=len(ordered), total=sum(ordered), min=ordered[0], max=ordered[-1],
                median=int(statistics.median(ordered)),
                mean=round(statistics.fmean(ordered), 1))


def walk(root):
    """Collect (case, relative path parts, size) for every regular file under root."""
    entries, symlinks, empty, unreadable = [], [], [], []
    root = root.resolve()
    for current, directories, files in os.walk(root, followlinks=False):
        base = Path(current)
        directories[:] = [d for d in directories if not (base / d).is_symlink()]
        for name in files:
            item = base / name
            if item.is_symlink():
                symlinks.append(str(item.relative_to(root)))
                continue
            try:
                size = item.stat().st_size
            except OSError as exc:
                unreadable.append(dict(path=str(item.relative_to(root)), error=exc.strerror))
                continue
            parts = item.relative_to(root).parts
            entries.append((parts, size))
            if size == 0:
                empty.append(str(item.relative_to(root)))
    return entries, symlinks, empty, unreadable


def strip_wrapper(root):
    """Descend through single-entry directories.

    Archives frequently nest everything under one folder named for the repository or release,
    so the real cases sit a level or two below the extraction root. Returns the working root
    and the components skipped, which the report names rather than hides.
    """
    skipped = []
    current = root
    while True:
        try:
            children = [c for c in current.iterdir() if not c.name.startswith('._')]
        except OSError:
            break
        if len(children) != 1 or not children[0].is_dir() or children[0].is_symlink():
            break
        skipped.append(children[0].name)
        current = children[0]
    return current, skipped


def infer_shape(_root, entries):
    """Directory-per-case or file-per-case, decided from evidence rather than assumed."""
    top_dirs = {parts[0] for parts, _ in entries if len(parts) > 1}
    top_files = {parts[0] for parts, _ in entries if len(parts) == 1}
    if len(top_dirs) >= len(top_files):
        return 'directory_per_case', top_dirs
    return 'file_per_case', {logical_stem(name) for name in top_files}


def assess(identifiers, patterns, per_case_files):
    """Flag an inference that probably did not find cases at all.

    Case identifiers should be numerous and share few shapes. One 'case', a distinct pattern for
    nearly every entry, or one entry holding almost all the files means the level is wrong --
    typically category directories such as automatic_labels/ and manual_labels/ that hold the
    real cases one level down. Reported rather than silently accepted.
    """
    reasons = []
    count = len(identifiers)
    if count <= 1:
        reasons.append('only one candidate identifier was found')
    elif len(patterns) > max(1, count // 2):
        reasons.append(f'{len(patterns)} distinct identifier shapes across {count} candidates')
    values = sorted(per_case_files.values())
    if len(values) > 1 and values[len(values) // 2] and values[-1] / values[len(values) // 2] > 100:
        reasons.append('one candidate holds over 100x the median file count')
    return reasons


def inventory(name, roots):
    """Inventory one logical source. Several directories may be merged under one name --
    nine archive shards of the same training set are one source, not nine."""
    if isinstance(roots, (str, Path)):
        roots = [roots]
    entries, symlinks, empty, unreadable, skipped, origin = [], [], [], [], [], {}
    for root in roots:
        working, stripped = strip_wrapper(Path(root))
        skipped.extend(stripped)
        found, links, blanks, bad = walk(working)
        for parts, size in found:
            origin.setdefault(parts[0], set()).add(str(root))
        entries.extend(found)
        symlinks.extend(links)
        empty.extend(blanks)
        unreadable.extend(bad)
    if not entries:
        return dict(source=name, roots=[str(r) for r in roots], files=0,
                    note='No regular files found; nothing to infer.')

    # A case present under two merged roots is a real defect, not a merge artefact.
    straddling = sorted(k for k, v in origin.items() if len(v) > 1)

    shape, identifiers = infer_shape(None, entries)
    per_case_bytes, per_case_files = Counter(), Counter()
    structures, structure_bytes = Counter(), defaultdict(list)
    structure_members = defaultdict(list)
    case_shapes = defaultdict(set)

    for parts, size in entries:
        if shape == 'directory_per_case' or len(parts) > 1:
            case = parts[0]
        else:
            case = logical_stem(parts[0])
        # The fingerprint masks digits in every component, so it never depends on the case
        # inference being right. Identifiers differ only in their digits, so real cases still
        # collapse to one row: PanTS_00000001/... and PanTS_00009901/... share PanTS_#/...
        structure = '/'.join(mask(part) for part in parts)
        structures[structure] += 1
        structure_bytes[structure].append(size)
        structure_members[structure].append((case, size))
        case_shapes[case].add(structure)
        per_case_bytes[case] += size
        per_case_files[case] += 1

    # Which combinations of files do cases actually have? Reveals incompleteness compactly.
    combinations = Counter(frozenset(v) for v in case_shapes.values())
    majority, majority_count = combinations.most_common(1)[0]
    incomplete = sorted(case for case, shapes in case_shapes.items() if shapes != majority)

    # Per-case totals hide a single bad file among many. A corrupt or empty mask is one file
    # of twenty-nine, which moves the case total by a few percent and never trips a case-level
    # threshold. Comparing each file against the median for ITS OWN structure finds it.
    per_structure, small_in = {}, defaultdict(list)
    for structure, members in structure_members.items():
        ordered = sorted(size for _, size in members)
        middle = ordered[len(ordered) // 2] or 1
        small = sorted((s, c) for c, s in members if s / middle <= SMALL)
        large = sorted(((s, c) for c, s in members if s / middle >= LARGE), reverse=True)
        for _, case in small:
            small_in[case].append(structure)
        if small or large:
            per_structure[structure] = dict(
                median=middle,
                small_for_structure=dict(
                    count=len(small),
                    sample=[dict(case=c, bytes=s, median_ratio=round(s / middle, 4))
                            for s, c in small[:20]]),
                large_for_structure=dict(
                    count=len(large),
                    sample=[dict(case=c, bytes=s, median_ratio=round(s / middle, 2))
                            for s, c in large[:20]]))

    # The discriminating measurement. A compressed NIfTI's size is dominated by its grid, not by
    # how much of the mask is filled, so a case with a small field of view is small in EVERY
    # structure at once. Those are small scans, not defects. A case small in only one or two
    # structures is the shape worth investigating -- the anomaly is the structure, not the scan.
    total_structures = len(structure_members)
    # The split only means anything when a case has several structures to be compared across.
    # With one structure per case, "small in most of them" and "small in one of them" are the
    # same set, and reporting both invents a distinction that does not exist.
    if total_structures >= MIN_STRUCTURES:
        widespread = sorted(c for c, v in small_in.items() if len(v) >= total_structures * BROAD)
        isolated = sorted((len(v), c, v) for c, v in small_in.items() if len(v) <= NARROW_MAX)
        middle = len(small_in) - len(widespread) - len(isolated)
        populations = dict(
            structures=total_structures,
            small_grid=dict(count=len(widespread), sample=widespread[:20],
                            note='Small in at least 80% of this case\'s structures at once: a '
                                 'small field of view, not a per-structure defect.'),
            structure_specific=dict(
                count=len(isolated),
                sample=[dict(case=c, structures_affected=n,
                             structures=[x.split('/')[-1] for x in v]) for n, c, v in isolated[:50]],
                note='Small in one or two structures while the rest of the case is normal. This '
                     'is the shape a real per-structure defect takes. Confirming it requires '
                     'reading voxels, which this tool does not do.'),
            intermediate=dict(count=middle,
                              note='Small in between three structures and 80% of them. Neither '
                                   'clearly a small scan nor clearly one bad structure.'))
    else:
        populations = dict(
            structures=total_structures,
            unavailable='A case here has too few structures to distinguish a small scan from a '
                        ' single bad structure. Both would look identical. Use the per-structure '
                        'table above and treat the flagged cases as unexplained.')

    sizes = list(per_case_bytes.values())
    spread = describe(sizes)
    outliers = []
    if spread and len(sizes) > 2 and spread['median']:
        for case, total in per_case_bytes.most_common():
            ratio = total / spread['median']
            if ratio >= 10 or ratio <= 0.1:
                outliers.append(dict(case=case, bytes=total, median_ratio=round(ratio, 2)))
            if len(outliers) >= 50:
                break

    patterns = dict(Counter(mask(i) for i in identifiers).most_common(10))
    concerns = assess(identifiers, patterns, per_case_files)

    return dict(
        source=name, roots=[str(r) for r in roots], shape=shape,
        wrapper_directories=sorted(set(skipped)),
        duplicated_across_roots=dict(count=len(straddling), sample=straddling[:20]),
        shape_confidence='low' if concerns else 'ok', shape_concerns=concerns,
        files=len(entries), cases=len(identifiers),
        bytes=sum(size for _, size in entries),
        identifier_patterns=patterns,
        identifier_sample=sorted(identifiers)[:SAMPLE],
        structures={s: dict(count=c, bytes=describe(structure_bytes[s]))
                    for s, c in structures.most_common(30)},
        per_structure_outliers=per_structure,
        size_populations=populations,
        per_case_files=describe(list(per_case_files.values())),
        per_case_bytes=spread,
        complete_combination=dict(files=sorted(majority), cases=majority_count),
        incomplete_cases=dict(count=len(incomplete), sample=incomplete[:20]),
        zero_byte_files=dict(count=len(empty), sample=empty[:20]),
        symlinks=dict(count=len(symlinks), sample=symlinks[:20]),
        unreadable=unreadable[:20],
        size_outliers=outliers,
        identifiers=sorted(identifiers),
    )


def collisions(reports):
    """Identifier overlap between sources. A collision means a naive merge mixes subjects."""
    found = []
    named = [(r['source'], set(r.get('identifiers', []))) for r in reports if r.get('identifiers')]
    for i, (left, a) in enumerate(named):
        for right, b in named[i + 1:]:
            shared = a & b
            found.append(dict(sources=[left, right], shared=len(shared),
                              sample=sorted(shared)[:20],
                              left_only=len(a - b), right_only=len(b - a)))
    return found


def digest(reports, overlaps):
    lines = ['# Observed source layout', '', f'Generated {utc()} by `inventory_sources.py`.',
             'Structural observation only: no file contents, headers or voxels were read. This',
             'establishes no geometry, label semantics, patient uniqueness or eligibility claim.',
             '', '## Sources', '',
             '| Source | Shape | Cases | Files | Bytes | Incomplete |', '|---|---|---:|---:|---:|---:|']
    for r in reports:
        if not r.get('files'):
            lines.append(f"| {r['source']} | — | 0 | 0 | 0 | — |")
            continue
        shape = r['shape'] + (' ⚠' if r.get('shape_confidence') == 'low' else '')
        lines.append(f"| {r['source']} | {shape} | {r['cases']:,} | {r['files']:,} | "
                     f"{r['bytes']:,} | {r['incomplete_cases']['count']:,} |")
    for r in reports:
        if not r.get('files'):
            continue
        lines += ['', f"## {r['source']}", '']
        if r.get('wrapper_directories'):
            lines += [f"Descended through wrapper director"
                      f"{'y' if len(r['wrapper_directories']) == 1 else 'ies'}: "
                      f"`{'/'.join(r['wrapper_directories'])}`", '']
        if r.get('shape_confidence') == 'low':
            lines += ['> **Low confidence in the inferred case level.** '
                      + '; '.join(r['shape_concerns']).capitalize() + '.',
                      '> The rows below are still an accurate structural fingerprint, but the '
                      '"cases" column is probably counting something else — commonly category '
                      'directories holding the real cases. Re-run with `--source` pointed at '
                      'the directory that actually contains them.', '']
        lines += [f"Identifier patterns: `{'`, `'.join(r['identifier_patterns'])}`  ",
                  f"Examples: `{'`, `'.join(r['identifier_sample'])}`", '',
                  '| Path within case | Files | Median bytes |', '|---|---:|---:|']
        for structure, detail in r['structures'].items():
            median = detail['bytes']['median'] if detail['bytes'] else 0
            lines.append(f"| `{structure}` | {detail['count']:,} | {median:,} |")
        if r['incomplete_cases']['count']:
            names = '`, `'.join(r['incomplete_cases']['sample'][:8])
            lines += ['', f"**{plural(r['incomplete_cases']['count'], 'case')} differ from the "
                          f"majority file set.** Sample: `{names}`"]
        if r.get('duplicated_across_roots', {}).get('count'):
            names = '`, `'.join(r['duplicated_across_roots']['sample'][:8])
            lines += ['', f"> **{plural(r['duplicated_across_roots']['count'], 'case')} appear in "
                          f"more than one of this source's directories.** That is a duplicate in "
                          f"the source, not a merge artefact. Sample: `{names}`"]
        if r['zero_byte_files']['count']:
            names = '`, `'.join(r['zero_byte_files']['sample'][:5])
            lines += ['', f"**{plural(r['zero_byte_files']['count'], 'zero-byte file')}.** The "
                          f"previous project found these were genuine source defects, not a "
                          f"reader bug. Sample: `{names}`"]
        flagged = r.get('per_structure_outliers') or {}
        if flagged:
            pops = r.get('size_populations', {})
            lines += ['', '### Files unusually sized within their own structure', '',
                      '**This measures grid size, not mask content.** A compressed NIfTI\'s size '
                      'is dominated by its voxel dimensions, so an all-zero mask on a large grid '
                      'and a filled mask on the same grid are comparable, while a small '
                      'field-of-view scan is small in every structure at once. **An empty mask '
                      'cannot be detected from file size. That requires reading voxels, which '
                      'this tool does not do.**', '',
                      '']
            if pops.get('unavailable'):
                lines += [f"> Each case here has {plural(pops.get('structures', 0), 'structure')}, "
                          f"so a small scan and a single bad structure are indistinguishable. "
                          f"{pops['unavailable']}", '']
            else:
                lines += [
                    f"- **{plural(pops['small_grid']['count'], 'case')}** small across at least "
                    f"80% of their {pops['structures']} structures — small scans, not defects.",
                    f"- **{plural(pops['structure_specific']['count'], 'case')}** small in one or "
                    f"two structures while the rest of the case looks normal. That is the shape a "
                    f"real per-structure defect takes, and the only group worth voxel inspection.",
                    f"- **{plural(pops['intermediate']['count'], 'case')}** in between, explained "
                    f"by neither.", '']
            lines += ['| Path within case | Median bytes | Small (<=0.1x) | Large (>=10x) |',
                      '|---|---:|---:|---:|']
            for structure, detail in sorted(
                    flagged.items(),
                    key=lambda kv: -(kv[1]['small_for_structure']['count']
                                     + kv[1]['large_for_structure']['count'])):
                lines.append(f"| `{structure}` | {detail['median']:,} | "
                             f"{detail['small_for_structure']['count']:,} | "
                             f"{detail['large_for_structure']['count']:,} |")
            specific = (pops.get('structure_specific') or {}).get('sample') or []
            if specific:
                affected = Counter(s for x in specific for s in x['structures'])
                lines += ['', 'Which structures the structure-specific cases are anomalous in '
                              '(from the sample):', '',
                          '| Structure | Cases |', '|---|---:|']
                for structure, n in affected.most_common(12):
                    lines.append(f'| `{structure}` | {n} |')
                named = ', '.join(f"`{x['case']}` ({'`, `'.join(x['structures'])})"
                                  for x in specific[:5])
                lines += ['', f'Examples: {named}']
        if r['size_outliers']:
            names = ', '.join(f"`{o['case']}` ({o['median_ratio']}x)"
                              for o in r['size_outliers'][:5])
            lines += ['', f"**{plural(len(r['size_outliers']), 'case')} at 10x or 0.1x the median "
                          f"case size.** {names}"]
    lines += ['', '## Identifier overlap between sources', '',
              '| Sources | Shared | Left only | Right only |', '|---|---:|---:|---:|']
    for o in overlaps:
        lines.append(f"| {o['sources'][0]} vs {o['sources'][1]} | {o['shared']:,} | "
                     f"{o['left_only']:,} | {o['right_only']:,} |")
    lines += ['', 'A non-zero shared count does **not** prove the same subject; it proves the',
              'identifiers cannot be merged into one namespace without a disambiguation rule.',
              'Plan 02 owns that rule. A zero count does not prove subject disjointness either.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--source', action='append', required=True, metavar='NAME=PATH',
                        help='Extracted tree to inventory; repeatable.')
    parser.add_argument('--out', type=Path, required=True, help='JSON record destination.')
    parser.add_argument('--summary', type=Path, help='Optional Markdown digest destination.')
    args = parser.parse_args()

    grouped = {}
    for item in args.source:
        if '=' not in item:
            raise ValueError(f'Expected NAME=PATH, got {item!r}')
        name, _, raw = item.partition('=')
        root = Path(raw)
        if not root.is_dir():
            raise ValueError(f'{name}: not a directory: {root}')
        grouped.setdefault(name, []).append(root)

    reports = []
    emit('inventory_started', sources=len(grouped),
         directories=sum(len(v) for v in grouped.values()))
    for name, roots in grouped.items():
        report = inventory(name, roots)
        reports.append(report)
        emit('source_inventoried', source=name, directories=len(roots),
             files=report.get('files'),
             cases=report.get('cases'), shape=report.get('shape'),
             shape_confidence=report.get('shape_confidence'))
        if report.get('shape_concerns'):
            emit('shape_uncertain', source=name, concerns=report['shape_concerns'],
                 note='The case level is probably wrong; point --source one level deeper.')

    overlaps = collisions(reports)
    for overlap in overlaps:
        if overlap['shared']:
            emit('identifier_overlap', sources=overlap['sources'], shared=overlap['shared'])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(dict(generated=utc(), sources=reports, overlaps=overlaps),
                                   indent=1))
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(digest(reports, overlaps))
    emit('inventory_complete', sources=len(reports), record=str(args.out),
         sources_reconciled=False, cohorts_registered=False)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        emit('inventory_cancelled')
        raise SystemExit(130)
    except Exception as exc:
        emit('inventory_failed', error_type=type(exc).__name__, message=str(exc))
        raise
