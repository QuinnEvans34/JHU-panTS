# Approved capstone source records

**Recorded:** 2026-09-07  
**Purpose:** Prevent an older proposal, appendix, or Markdown draft from becoming the accidental
source of truth.

| Role | Preserved filename | Bytes | SHA-256 |
|---|---|---:|---|
| Approved proposal | `Evans_Quinton_PROWL_Capstone_Proposal_v3.8.docx` | 19,211 | `00546c805f0f49df2bf11cf452dc29171ede49e6931f23f5186562e39e613612` |
| Approved technical appendix | `Evans_Quinton_PROWL_Capstone_Technical_Appendix_v3.1.docx` | 576,033 | `6c26f2ae2652c32c0fa444cc10bc608ae4a81aab5c7970c294ce4f031f2b64e3` |

These files currently remain at the repository root. They will not be overwritten, renamed `final`,
or deleted. Any later approved revision must receive a new filename, a new hash record, and an
explicit source-hierarchy update.

## Governing interpretation

- The proposal governs project purpose, committed scope, prior/new boundary, and the approved
  10-week schedule.
- The appendix governs detailed technical boundaries, data facts, evaluation expectations,
  retrieval behavior, risk/fallback framing, and licensing.
- The appendix's file-first implementation boundary means relational persistence, managed vector
  services, cloud persistence, and a particular model architecture remain optional until justified.
- Historical Markdown and proposal drafts provide evidence but cannot silently expand or narrow the
  approved commitment.

## Integrity recheck

From the repository root:

```bash
shasum -a 256 \
  Evans_Quinton_PROWL_Capstone_Proposal_v3.8.docx \
  Evans_Quinton_PROWL_Capstone_Technical_Appendix_v3.1.docx
```

If a hash changes, stop and determine whether the source was intentionally revised. Do not update
this record simply to make the check pass.
