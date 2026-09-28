"""One definition of an unsafe archive member, shared by extraction tooling.

Issue keys match `scripts/diagnostics/scan_pants_archives.py` so the read-only scan and the
extractor cannot disagree about what is unsafe. This module may be STRICTER than that scan
(`name_too_long` matters only when writing); it must never be more permissive. The superset
property is asserted by `tests/test_member_safety.py`.

Classification is pure and aggregate-only: callers keep member names in memory and never log them.
"""
from __future__ import annotations

from collections import Counter
from pathlib import PurePosixPath
import re
import stat
import unicodedata

# APFS rejects a path component longer than 255 bytes. A tar/zip member can carry one.
MAX_COMPONENT_BYTES = 255
DRIVE_LETTER = re.compile(r'^[A-Za-z]:')
ZIP_UNIX = 3


def collision_key(name):
    """Fold a member name to the identity APFS would collide on."""
    return unicodedata.normalize('NFD', str(PurePosixPath(name))).casefold()


def path_issues(name):
    """Issues decidable from the member name alone."""
    found = set()
    parts = PurePosixPath(name).parts
    if (not name or name.startswith('/') or '\\' in name or '..' in parts
            or DRIVE_LETTER.match(name) or any(ord(c) < 32 for c in name)):
        found.add('unsafe_path')
    if any(len(part.encode('utf-8')) > MAX_COMPONENT_BYTES for part in parts):
        found.add('name_too_long')
    return found


class Inspector:
    """Accumulates member classifications so cross-member conflicts can be reported."""

    def __init__(self, max_members=2_000_000):
        self.seen = {}
        self.max_members = max_members

    def inspect(self, name, *, is_file, is_dir, size, is_sparse=False):
        """Classify one member. Returns the set of issue keys; empty means safe to write."""
        found = path_issues(name)
        key = collision_key(name)
        if key in self.seen:
            found.add('duplicate_or_case_unicode_collision')
        self.seen[key] = is_dir
        if len(self.seen) > self.max_members:
            raise ValueError('Member-count resource ceiling exceeded')
        if not (is_file or is_dir):
            found.add('link_or_special_entry')
        if is_sparse:
            found.add('sparse_entry')
        if size < 0:
            found.add('negative_size')
        return found

    def structural_issues(self):
        """Conflicts only visible once every member has been inspected."""
        found = Counter()
        for key in self.seen:
            for parent in PurePosixPath(key).parents:
                if str(parent) in self.seen and not self.seen[str(parent)]:
                    found['file_as_parent'] += 1
        return found


def from_tar(member):
    """Adapt a tarfile.TarInfo to inspect() keywords."""
    return dict(name=member.name, is_file=member.isfile(), is_dir=member.isdir(),
                size=member.size, is_sparse=member.sparse is not None)


def from_zip(info):
    """Adapt a zipfile.ZipInfo to inspect() keywords.

    zipfile exposes no issym(); a Unix-created symlink is only visible in the high bits of
    external_attr. Without this check a symlink extracts as an ordinary file holding its target
    path, which is a silent semantic substitution rather than a refusal.
    """
    is_dir = info.is_dir()
    mode = info.external_attr >> 16
    regular = True
    if info.create_system == ZIP_UNIX and stat.S_IFMT(mode):
        regular = stat.S_ISREG(mode) or stat.S_ISDIR(mode)
    return dict(name=info.filename, is_file=not is_dir and regular, is_dir=is_dir,
                size=info.file_size, is_sparse=False)
