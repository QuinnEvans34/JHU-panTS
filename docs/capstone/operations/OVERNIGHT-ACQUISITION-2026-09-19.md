# Overnight acquisition — September 19, 2026

**Authority:** Quinton asked to arrange overnight downloads without starting each archive manually.  
**Status at 22:03 MDT:** PanTS and PANORAMA queues running; literature not started.  
**Boundary:** Original archives only; no CT extraction, source activation, model training, corpus
indexing, paid service, remote upload, or Plan 04 implementation.

## What is downloading

| Queue | Contents / size | Observed state |
|---|---|---|
| PanTS | Metadata, labels, nine training CT archives, one opaque publisher-test archive; 361,265,775,573 bytes | Existing process continues; metadata verified, label archive in progress |
| PANORAMA | Four CT ZIP batches; 194,181,682,590 bytes; plus pinned label ZIP, 91,426,460 bytes | Label ZIP verified against all 2,242 Git blobs; CT batch 1 downloading, batches 2–4 follow |
| Literature for evidence assistant | In-scope PubMed records/abstracts and individually permitted PMC text | Not queued: search/cutoff, contact configuration, rights fixtures and acquisition checks remain |
| Model/embedding assets | Exact selected upstream initialization and embedding/generation assets, if required | Not queued: select/pin under owning plans; do not reuse historical trained models or choose weights merely to fill the overnight queue |

The combined imaging transfer total is **555,538,884,623 bytes** (about 556 GB decimal), including
the now-measured label ZIP. The remaining free space is sufficient for these archives with the
512 GiB acquisition reserve. Expanded CT storage, temporary extraction, caches and later outputs
still require the separate extraction budget. Do not promise a morning completion time: server,
network, hashing and drive speed vary.

## Automatic behavior and limits

- Two finite standalone download processes, one per dataset. Each advances its own files without
  further clicks; no third large concurrent transfer is started.
- PanTS retains its original tested script, inventory and live process unchanged.
- PANORAMA CT transfers resume only with a valid HTTP Range response; exact publisher sizes/MD5
  must pass before a final filename appears. Each receipt also records a local SHA-256.
- PANORAMA labels use a fixed Git commit archive. The queue verifies every expanded member's size
  and Git blob hash against the pinned repository tree, detects missing/extra/unsafe members, and
  reads ZIP members without extracting them. There is no publisher archive SHA-256; the recorded
  archive digest is local. Non-range partial label ZIP attempts are preserved separately, not deleted
  or blindly appended. Labels completed in this attempt.
- The PANORAMA queue retries transient network/server/rate failures up to six attempts per file,
  honors numeric `Retry-After`, then records that file deferred and moves to the next independent
  file. An integrity, wrong-drive, or low-space error stops the queue for review.
- Partials are retained. Neither script deletes archives, repairs a drive, activates a source alias,
  nor makes a corpus or training-readiness claim.
- `caffeinate -i -w <pid>` is attached to each observed download process to prevent idle sleep only
  while it runs. No permanent energy setting was changed. Keep the Mac plugged in, lid open,
  external drive connected, network available, and Codex running. Do not restart the Mac tonight.
- These are running processes, not scheduled automatic restarts after reboot and not a recurring
  monitoring/notification automation. An interruption may require the documented resume command.

## Verification and live evidence

New `tests/test_panorama_acquisition.py` adds 14 offline checks for MD5/SHA-256, Git member identity,
unsafe/missing members, size limits, retry classification and inventory totals. The full fast suite
passed **101 tests**, with two existing upstream PyTorch deprecation warnings. Evidence:
`outputs/prowl/testing/foundation-2026-09-19/overnight-acquisition-01.xml` (ignored).

The exact inventory used by both processes is
[`../data/acquisition-2026-09-19.json`](../data/acquisition-2026-09-19.json), SHA-256
`4bf8c3b26d4a50b71a4194c3a904d4ae9da9ddac1792feb0b2408c29b793a870`.
Its `downloads_started: false` field describes the earlier inventory checkpoint, not live status;
the file is preserved unchanged while those processes run.

Local live receipts, relative to the external `PROWL/` workspace:

- `sources/pants/acquisition-3b1cd6110811/attempt-20260920T033958365521Z.jsonl`
- `sources/panorama/acquisition-2026-09-19-bf1d6ba3230f/attempt-20260920T040200886554Z.jsonl`

The PANORAMA label archive SHA-256 is
`f6b0399d9a01572779ac62ff0652348913d67913f8373110f133da40e30787d7`.
Pinned Git tree response SHA-256 is
`c0844d913f88de0380ac1147ca7229767aa567a27d3e034b51ab65c482e39306`.
The local `label-tree-20260920T040200886554Z.json` retains publisher member evidence.
Archive integrity does **not** establish eligible/manual/automatic case counts, correct geometry,
target semantics, duplicate handling, or protected cohort membership; Plan 03 still owns those checks.

Observed process IDs were PanTS 69510 and PANORAMA 73993. They are session-specific clues only;
check actual commands/receipts before signaling or restarting any process.

## Resume safely

Check that the corresponding process is no longer running before either command. Each command
rechecks the expected mounted APFS UUID and refuses a second writer via its acquisition lock.
Run from the repository in the existing `.venv-prowl`; leave original inventories and archives intact.

```sh
.venv-prowl/bin/python scripts/acquisition/download_pants.py \
  --inventory docs/capstone/data/acquisition-2026-09-19.json \
  --roots configs/local/roots.yaml

.venv-prowl/bin/python -m scripts.acquisition.download_panorama \
  --inventory docs/capstone/data/acquisition-2026-09-19.json \
  --roots configs/local/roots.yaml
```

## Literature follow-up, not an overnight bulk scrape

The approved Plan 07 already fixes the high-level topic: CT pancreas/lesion annotation and review,
including relevant AI limitations. It does not yet contain an executable frozen search protocol or
rights-tested acquisition implementation. Prepare those next, with no patient data in requests:

1. Version exact PubMed search strings, cutoff, inclusion/exclusion rules and bounded initial scope.
2. Configure NCBI tool/contact identification locally (Quinton was asked for a contact email; do not
   guess one or commit it). An API key is optional at the standard low request rate.
3. Add and pass batching/rate/retry, source identity, retraction/notice and fail-closed rights tests.
4. Use approved NCBI services to acquire records and only full-text representations with applicable
   permissions. Preserve per-representation rights evidence before indexing/display/release.
5. Keep downloaded text off Git and independent of imaging; do not download all of PubMed/PMC.

Current primary guidance: [NCBI E-utilities usage](https://www.ncbi.nlm.nih.gov/books/NBK25497/)
and [PMC OAI-PMH/content retrieval policy](https://pmc.ncbi.nlm.nih.gov/tools/oai/). Public availability
does not eliminate per-article copyright/reuse restrictions. Existing `pubmed_samples.xml` remains
historical exploratory material, not a newly approved corpus. This follow-up does not waive Plan 04's
explanation/authorization gate or select a vector database/model.

## Morning handoff

Read both receipt logs and inspect processes/partial sizes first. Confirm completed files by receipt
and bytes/hashes; do not infer success from elapsed time. Review any deferred/stopped file before
resuming. Then inventory safe CT archive members and expanded sizes, budget extraction, and reconcile
sources with Plans 02/03. The Node/UI foundation and reviewed Git checkpoint can proceed alongside.
