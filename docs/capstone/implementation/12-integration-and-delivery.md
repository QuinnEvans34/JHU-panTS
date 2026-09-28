# Integration, stabilization, and delivery

**Status:** Approved design — P12-01 through P12-12 approved 2026-09-18; execution/release evidence pending  
**Owner:** Quinton Evans; implementation and verification through the component plans  
**Target weeks:** Incremental integration as components become ready; formal delivery stages in Weeks 8–10  
**Depends on:** Relevant component contracts/tests for each integration step; G1–G7 for the complete release candidate  
**Sources:** Approved proposal/appendix, master-plan G8/G9, Plans 06–11  
**Last reviewed:** 2026-09-18

## Outcome

PROWL will be assembled into a reproducible release candidate, evaluated end to end, stabilized
without scope expansion, and delivered with user/developer documentation, an honest results and
limitations record, and a rehearsed presentation.

## Why this belongs

Working components are not automatically a working system. This plan proves that the selected
model, data, literature evidence, interface, saved reviews, reports, and documentation describe the
same version of PROWL. It also defines what to do when a defect is found after evaluation or a live
demonstration fails, without overwriting evidence or consuming the protected weeks with new scope.

## Current state

- Plans 01–03 are Ready designs; Plans 04–10 have approved designs with execution prerequisites.
- Plan 11's lightweight living protocol is approved; Quinton owns outreach, and the actual expert
  role, appointment, session, and findings are pending. A radiologist is preferred, not confirmed.
- Existing pipeline/UI code and historical results are reusable foundation/context, not a completed
  capstone release. No prior trained model becomes a capstone candidate.
- No capstone release candidate, release schema implementation, full-system acceptance result,
  held-out capstone report, restore-tested release bundle, or submission is claimed here.
- Final report/presentation submission requirements and exact deadlines must be checked against the
  course instructions before packaging. This plan does not invent a required file format.

## Scope

- Version lock, end-to-end integration, held-out evaluation, defect triage, stabilization, packaging,
  documentation, rehearsal, presentation, and release integrity checks.

## Non-goals

- New features in Weeks 9–10.
- Shipping raw/licensed data, secrets, or unsupported clinical claims.
- Masking an incomplete component with a simulated demo presented as real.
- Deploying a multi-user clinical service, making a public release, contacting participants, or
  submitting work on Quinton's behalf without an explicit request.

## Approved decisions

| ID | Approved decision | Practical consequence |
|---|---|---|
| P12-01 | Integrate small contract-tested paths throughout development; Week 8 is full-system qualification, not the first connection of components. | Find incompatible boundaries early while preserving each branch's independent progress. |
| P12-02 | A release candidate names exact component/artifact/config/schema/code/environment versions; never resolve a scientific input through `latest`. | Reports, UI, models, evidence, and demo cannot silently use different versions. |
| P12-03 | Use relevant prerequisites for incremental work, but require G1–G7 and committed-requirement evidence for a complete candidate. | No unnecessary startup gate; no incomplete system labeled complete. |
| P12-04 | Freeze imaging and retrieval selection before their respective held-out evaluations; report the result without retuning against it. | A disappointing result is not permission to shop for a better test score. |
| P12-05 | Every defect fix declares which artifacts, tests, and claims it invalidates; corrected outputs receive new versions. | Preserve the original failure/result and rerun the affected evidence honestly. |
| P12-06 | Required test coverage must actually pass under Plan 09; missing prerequisites, quarantined failures, or unexplained skips cannot count as passes. | A green summary alone does not certify the release. |
| P12-07 | Include the actual Plan 11 session/fallback evidence and role limitations; implement only Quinton-approved bounded findings. | Outreach continues independently, but planning alone cannot satisfy stakeholder review. |
| P12-08 | Use explicit defect severity and release disposition; optional work can be deferred, but unmet committed scope requires escalation rather than silent removal. | Week 9 repairs and stabilizes; it does not add features or redefine success. |
| P12-09 | Separate the local reproducibility bundle from the sanitized submission package, both with declared inventories and hashes. | Raw imaging, restricted text, private notes, secrets, and accidental large payloads cannot leak through packaging. |
| P12-10 | Rehearse a local live path and a labeled fallback using the same validated release evidence. | A presentation can recover without pretending a recording, fixture, or static export proves live execution. |
| P12-11 | Before G8, pass clean setup, relevant reproduction recipes, and release-critical restore checks; before G9, lock the verified revision and evidence. | Recovery is tested before the protected buffer is exhausted. |
| P12-12 | Quinton reviews scope, limitations, unresolved defects, and the exact delivery inventory before release lock/submission. | Design approval is not authorization to tag/push/publish/upload/send the finished work. |

Quinton approved P12-01 through P12-12 on 2026-09-18. This completes design approval of all twelve
numbered plans, not implementation or release qualification. Scientific, privacy, licensing,
Week 9/10, and no-model-reuse boundaries remain unchanged.

## Week boundaries

- **Week 8:** integration, full testing, held-out evaluation, and documentation drafts.
- **Week 9:** protected buffer, defect correction, affected-test/evaluation reruns, release lock. No
  new scope.
- **Week 10:** package, rehearse, present, and submit. No new feature implementation.

Integration checks begin before Week 8 whenever their producers/consumers are ready. Select the
candidate early enough in Week 8 to freeze policies, run the declared held-out evaluations, and
complete the release matrix. Do not schedule planned new implementation in Week 9 as a way of
calling the same work a buffer. Week 10 cannot introduce a result-changing experiment/model.

## Inputs, outputs, and version contract

| Input | Owned by | Release evidence |
|---|---|---|
| Source, annotation, cohort, exclusion, and rights identities | Plans 02/03 | Verified immutable references and permitted control records |
| Workflow/configuration and terminal attempts | Plans 04/10 | Selected run manifests and independent artifact validation |
| Newly trained models, ROI/inference policy, predictions | Plan 05 | Exact localizer/segmenter/cascade and raw/derived prediction identities |
| Experiment decisions, metrics, and frozen selection | Plan 06 | Notebook links, selection manifest, prediction/evaluation evidence, limitations |
| Corpus, index, question set, retrieval/response policy | Plan 07 | Exact versions, development selection, held-out scores and citation/refusal evidence |
| Case packages, UI, review events | Plan 08 | Contract versions, UI/code revision, read-back evidence and immutable event snapshot |
| Test results and manual checks | Plan 09 | Complete run reports, fixture/environment identities, coverage and dispositions |
| Environment, roots, backups, restore records | Plan 10 | Portable configuration example, locks, recovery evidence and exclusion scan |
| Participant role, findings, approved revisions | Plan 11 | Sanitized session summary, role limitations, finding/test references |

The existing [artifact layout](../contracts/artifact-layout.md) provides
`<prowl_artifacts>/releases/<release_id>/`. A future versioned release schema must be implemented and
tested before publication; this Markdown table is not an executable validator. Its record should name:

- release ID/schema version, candidate/locked state, creation time, superseded release if any;
- exact Git commit, dependency/environment identities, config/schema versions;
- selected artifact IDs/hashes from every required row above, with root-independent references;
- immutable review snapshot identity, not a moving live event log;
- requirement-to-evidence coverage, gate outcomes, defect/limitation and exception records;
- package audience, permitted member list, exclusions, licenses, size and integrity inventory;
- restore/reproduction/rehearsal evidence and Quinton's sign-off reference.

Keep local root paths in ignored configuration, never in scientific identity or shared packages.
Payload hashes and manifest hashes use Plan 10 publication rules. Do not introduce a circular hash
by including an inventory's own checksum inside itself. Validate the declared inventory and publish
the completion record last; reject missing members, extra undeclared members, and path escapes.

## Release candidate contents

- Source code and documented environment.
- Configurations and schemas.
- Source/corpus/license/version registry without restricted data.
- Frozen cohort definitions/hashes.
- Selected new model lineage, inference configuration, and representative permitted artifacts.
- Evaluation report with autonomous/provided-region distinction and limitations.
- Retrieval/index manifest, question set, metrics, cited response/refusal examples.
- Integrated review interface and representative case packages.
- Test report, risk/ethics record, stakeholder findings.
- User guide, developer/reproduction guide, architecture/data-flow diagrams.
- Presentation/demo runbook and recovery path.

These are content requirements, not an instruction to copy all payloads into Git or a submission
archive. The local bundle can reference retained raw/source/model/index artifacts under approved
roots. The submission package includes only individually permitted material needed by its audience.
An externally included model or demo asset requires an explicit rights, size, and recipient review;
raw imaging and restricted text remain excluded. Do not add a report, model binary, or archive to
Git merely because it appears in the local release inventory.

## Integration sequence

### Incremental slices

1. **Synthetic contract path:** generated case package → static/FastAPI adapters → existing NiiVue
   interface. Verify transport parity, version checks, missing/error states, and no ground-truth
   requirement. This validates a boundary, not model performance.
2. **Durable review path:** package/prediction identity → action/reason → local writer → receipt →
   reload/history/revision. Inject failed writes and stale identities; browser state cannot count
   as a saved scientific review.
3. **Imaging path:** verified train/development source → tested preprocessing/localization/
   segmentation → source-space predictions → evaluation/case package → UI. Preserve failed-case
   records and denominators. Start small under the relevant Plan 04/05/06/09/10 gates.
4. **Evidence path:** permitted structured finding/question → pinned retrieval/response → source
   citation or refusal → UI. Test unavailable/insufficient evidence without breaking imaging/review.
5. **Combined representative path:** join exact imaging/evidence/package versions, exercise the
   approved Plan 11 tasks, record findings, and regression-test the approved revisions.
6. **Release qualification:** freeze selection, execute the full relevant test matrix and held-out
   protocols, assemble reports, verify portable setup/reproduction/restore, and evaluate G8.

Slices 2–4 may develop independently once their own boundaries are ready; they are not a demand to
finish the UI before imaging can begin. Relevant pure contracts/tests precede real artifact use.
Do not weaken the Plan 04 explanation/authorization gate to build orchestration through this plan.

### Candidate to delivery

1. Review the requirement matrix and choose one development-evidence-supported candidate.
2. Freeze the model, operating policy, metric implementation, retrieval policy, and respective
   holdout identities; record expected resources and the exact evaluation commands.
3. Execute the one-way held-out protocols; publish complete results, failures, and limitations.
4. Assemble the complete candidate inventory, test evidence, stakeholder outcomes, and draft guides.
5. Pass clean setup, reproduction/restore, exclusion scans, and the G8 review in Week 8.
6. During Week 9, handle documented overruns/defects only; apply the invalidation matrix below and
   recheck the complete affected gate. Preserve each earlier candidate and its failed evidence.
7. Before G9, confirm that required tests pass, release-critical backups restore, requirements have
   evidence, and Quinton accepts the explicit limitations and any permissible nonblocking defects.
8. Publish a new immutable locked local release inventory and verify its checksums. A future Git
   tag may identify the exact revision when requested; never silently move an existing tag.
9. In Week 10, verify packaging against course instructions, rehearse on the locked version, and
   prepare the exact delivery list for Quinton. Record actual submission only after it occurs.

## Held-out evaluation and correctness reruns

Follow [Plan 06's holdout protocol](../evaluation/PREDICTION-SETS-AND-HOLDOUTS.md) for imaging and Plan
07 for retrieval. Selection evidence must come from permitted development data. A poor held-out
score is reported as observed; it does not justify a new threshold/model/ranker chosen against it.

A correctness rerun must name the defect or interruption, original run/result, frozen intended
behavior, corrective code/config change, and affected descendants. Retain both old and corrected
evidence and explain why the rerun is not model selection. If the scientific design changes in
response to held-out findings, the same cohort is no longer untouched for that changed design; do
not claim restored test blindness. Escalate the interpretation/scope issue instead of relabeling it.

All experimental reruns receive entries in [`../../experiments.md`](../../experiments.md), including
failed/canceled attempts, before follow-up execution. The release report distinguishes a reproduced
fixed design from a newly selected design.

## Defect policy

- **Blocker:** invalid scientific result, leakage, wrong source/label, privacy/license issue, data loss,
  core flow impossible. Must fix before release.
- **High:** misleading UI/evidence, incorrect persistence, major reproducibility failure. Must fix
  when it affects a committed requirement; an optional affected capability may be disabled with
  explicit scope/test/limitation review.
- **Medium:** bounded failure with safe workaround. Fix if schedule permits; document otherwise.
- **Low:** cosmetic or optional refinement. Do not disturb release stability.

Any fix changing predictions, cohorts, preprocessing, metric code, or corpus/index content invalidates
the affected result and requires a versioned rerun.

Each defect record needs an ID, observed/expected behavior, reproduction steps, source evidence,
severity, affected requirements/artifact IDs, owner, proposed fix, invalidation scope, regression
test, schedule estimate, disposition, and closure evidence. `Fixed` requires a passing verification,
not only a code edit. No required failing test is waived by downgrading its defect label.

### Evidence invalidation matrix

| Change | Evidence to revisit | Required action |
|---|---|---|
| Training/cohort/annotation membership or initialization | Descendant training/models/predictions/evaluations | New identities and valid reruns; investigate leakage implications before any claim |
| Localization, preprocessing, inference, post-processing, or operating policy | Affected predictions, metrics, case packages, display/claim tests | Regenerate affected descendants; reassess held-out interpretation |
| Metric implementation only | Evaluations/reports and any development selection that depended on the metric | Validate golden cases, rescore retained compatible predictions, review selection; retrain only if genuinely necessary |
| Corpus/chunking/index/query/response policy | Retrieval/response evaluations, evidence packages, cited displays | New versions, relevant recall/grounding/refusal reruns, holdout-use audit |
| Review writer/schema or identity handling | Persistence/history/export and integration evidence | Contract migration/compatibility review and round-trip tests; never rewrite old review events |
| UI copy/layout only | Relevant interaction/accessibility/claim evidence | Targeted tests/manual checks; no scientific recomputation if inputs/meaning are unchanged |
| Environment/library change | Relevant numerical/runtime/compatibility evidence | Matched smoke and declared tolerance tests; expand reruns if behavior changes |
| Documentation/package-only correction | Links/inventory/claims/checksums | Verify against unchanged source evidence; publish a new package version |

Follow actual dependencies, not a blanket rerun of everything or a blanket reuse of stale evidence.
If a committed component cannot pass, stop the complete-release claim and discuss the scope/schedule
with Quinton and, when necessary, the instructor. Disclosure alone does not make it complete.

## Invariants

- Locked component versions are named in the release manifest.
- Any scientifically material fix triggers affected re-evaluation.
- The demonstration uses only validated release artifacts or a clearly labeled fallback.
- Historical/source artifacts remain unchanged.
- Week 9 and Week 10 contain no new product scope.
- No hard correctness, privacy, license, or data-integrity failure is accepted as a cosmetic issue.
- The release report describes actual stakeholder roles and actual execution; neither is inferred.
- A packaged fallback and a full validated capability are not interchangeable acceptance evidence.

## Test matrix

| Area | Release check |
|---|---|
| Environment | Clean setup and documented commands |
| Data/lineage | Source, cohort, config, model, corpus, and metric identities resolve |
| Workflow | Full source-to-review path and failure paths pass |
| Scientific | Locked held-out results reproduce within stated policy |
| Retrieval | Citation/refusal and frozen evaluation results resolve |
| UI | Representative cases and decision persistence pass |
| Package | No raw/restricted/secret data; checksums complete |
| Presentation | Timed live path and honest fallback rehearsed |

Additional negative controls: mixed component versions, stale review target, corrupt/missing package
member, unexpected extra file, incomplete publication, invalid source rights, wrong model ancestry,
unowned warning, missing required local-real test, and an attempt to tune after a test read. Each
must fail the relevant gate with a clear reason and without replacing existing complete artifacts.

## Test and rehearsal matrix

- Clean setup without private local assumptions.
- External drive/service unavailable recovery.
- Full source-to-review happy path.
- Localization/model failure path.
- False-positive and small-lesion explanation path.
- Relevant-evidence and insufficient-evidence paths.
- Review record save/reload/revision.
- Representative browser/screen/accessibility checks.
- Presentation offline/fixture fallback clearly labeled.
- Package scan for raw data, restricted text, secrets, and oversized artifacts.

Use Plan 09's actual test-run reports, counts, versions, and manual evidence. A selected required test
with missing prerequisites fails preflight; an explanatory skip is not a substitute for its pass.
Optional/unselected checks are disclosed separately. Do not obtain a green release by retaining only
successful reruns and discarding the original failure history.

## Documentation and demo runbook

Create the following Markdown guides incrementally under `docs/capstone/delivery/` during
implementation; they are planned artifacts, not files already completed by this design:

| Planned file | Must answer |
|---|---|
| `USER-GUIDE.md` | What PROWL does/does not do; load/inspect/evidence/review/reopen; warning and save-state meanings |
| `REPRODUCTION-GUIDE.md` | Environment setup, permitted source acquisition, local roots, exact frozen commands, expected evidence and tolerances |
| `RESULTS-AND-LIMITATIONS.md` | New versus reused foundation, autonomous/provided-region results, failure coverage, uncertainty, retrieval scores, role-limited stakeholder feedback |
| `RELEASE-CHECKLIST.md` | Exact candidate IDs, requirement/gate evidence, defects/dispositions, scans/restores/rehearsal and sign-off |
| `DEMO-RUNBOOK.md` | Startup preflight, release/case IDs, ordered tasks, timing, visible scope labels, failure response and closing claims |

Link existing architecture/contracts and the living experiment notebook rather than copy them into
competing sources of truth. Keep raw/identifiable participant notes outside these guides.

The main demo uses a prevalidated local case package from the locked release, shows prediction and
uncertainty, inspects cited evidence/refusal, records an action through the real writer, and reloads
the exact review history. Disclose precomputed inference. The demo does not depend on completing a
long training run, a fresh publisher download, or an external generative service on presentation day.

Rehearse one failure/refusal case, not just the attractive successful case. If live execution fails,
use a previously captured run/screenshot sequence or clearly labeled synthetic fixture from the
same documented version. A static review export is `exported—not recorded`; it cannot stand in for
G7 persistence evidence. Record what was actually demonstrated and what was not.

## Packaging and rollback

1. Build into a new scoped release-staging directory from an explicit allowlist, not a whole-repo
   archive or recursive copy of the artifact root.
2. Validate IDs, schemas, checksums, paths, source rights, claim wording, and each member's audience.
3. Scan for raw imaging, restricted article text, secrets, participant/contact details, local machine
   paths, historical initialization, caches, and unintended large files. A hit blocks publication.
4. Test setup and the bounded demo from the permitted package plus declared local prerequisites.
   Do not claim the code-only package is self-contained when licensed external inputs are required.
5. Verify release-critical backups using Plan 10 restore drills from independent copies, then publish
   the immutable local release and record package inventory/hash/size.
6. Quinton reviews the exact recipient/destination and delivery files before any upload or send.

If a candidate fails, retain it as failed/quarantined evidence and select the last independently
validated compatible candidate only when it still satisfies required scope. Record the rollback
explicitly; do not replace a published directory, reuse its release ID, or silently point a report at
different model/evidence bytes. No deletion of old releases is part of this plan.

## Failure modes and fallback

- Component misses G7: keep the gate open. Defer optional scope with a decision; if committed scope
  is affected, escalate rather than deliver a reduced system labeled complete.
- Held-out defect found late: quarantine result, fix, and use Week 9 rerun; reduce presentation scope.
- Live service/demo fails: use prevalidated local case packages and explain the boundary.
- Retrieval generator fails grounding gate: present retrieved passages/citations with refusal behavior.
- Time pressure: cut optional polish, uncommitted secondary analyses, and stretch—not required
  subgroup reporting, tests, lineage, or honesty.
- No stakeholder appointment: apply Plan 11's suitable-role/asynchronous fallback and disclose
  limitations; planning notes alone do not count as completed feedback.
- Blocker first appears in Week 10: preserve the locked evidence, stop using the affected capability,
  and ask Quinton for direction. Do not quietly add a new result-changing model or feature to delivery.

## Open decisions and readiness

| Item | Evidence / owner | Deadline and fallback |
|---|---|---|
| P12-01 through P12-12 | Approved by Quinton on 2026-09-18 | Complete as design decisions; execution evidence remains pending |
| Exact submission artifacts, duration, destination, and dates | Quinton checks course instructions | Before packaging/rehearsal; retain portable Markdown sources until formats are confirmed |
| Candidate model/operating policy and retrieval stack | Plans 06/07; D-205/D-208/D-202 evidence | Before respective selection freezes; no technology/model fixed here in advance |
| Participant/session and bounded revisions | Quinton / Plan 11 | Confirm/fallback by Week 5, review in Week 7; role limitation disclosed |
| Physical roots, backup target/budget, clean environments | Plan 10 | Before the relevant setup/acquisition/run; encryption is resolved by D-256 (keep unencrypted APFS); no release claims from a writable mount alone |
| Cross-plan G0 wording | September 18 prerequisite review; see `../IMPLEMENTATION-START.md` | Clarified: G0-design permits scoped foundation setup; full G0 also requires executable verification |

G1–G7 are prerequisites to a complete release candidate, not to drafting this plan or writing a
synthetic boundary test after its own prerequisites pass. D-201/D-202/D-205/D-208/D-210 remain
evidence-dependent under their owning plans; Plan 12 does not resolve them by assumption.

### Design readiness

- [x] Quinton approved P12-01 through P12-12 on 2026-09-18.
- [x] The focused twelve-plan prerequisite pass reconciles startup order and names the first
  implementation slice in [`../IMPLEMENTATION-START.md`](../IMPLEMENTATION-START.md). This is not
  a claim that every contract or executable prerequisite has been independently validated.
- [ ] Future release schema, validator, evidence owners, negative tests, and package audiences are
  precise before release-publisher implementation.
- [ ] No missing decision can silently change the scope of the next integration step.

## Acceptance gate

- [ ] Every committed requirement has verified evidence, or a separately approved scope amendment
  is recorded. Unmet requirements remain visible and prevent an unqualified completion claim.
- [ ] Full required release test matrix passes; no missing/failed required test is hidden by a skip.
- [ ] Held-out results trace to the locked model/cohort/config/metric versions.
- [ ] Retrieval results trace to the locked corpus/index/question versions.
- [ ] UI review decisions persist against immutable prediction versions.
- [ ] Actual stakeholder review/fallback evidence and limitations are recorded; approved revisions
  have verification evidence or a documented permissible deferral.
- [ ] Risk, ethics, license, and non-diagnostic reviews pass.
- [ ] No raw/restricted/secret data enters the package.
- [ ] Clean setup and timed demonstration have been rehearsed.
- [ ] Release-critical restore/reproduction checks pass and the exact permitted package is verified.
- [ ] Quinton has reviewed the candidate, limitations, unresolved nonblocking defects, and delivery inventory.
- [ ] Week 9 and Week 10 boundaries were preserved.

## Artifacts

- Release manifest/checksums and archive.
- Test/evaluation/retrieval/stakeholder reports.
- User and developer guides.
- Architecture and data-flow diagrams.
- Demo runbook, presentation, and retrospective.

The five planned Markdown guides above, a future versioned release schema/validator, and local
immutable `release.json`/checksum/evidence inventories implement this list. Their creation belongs to
implementation; no code, schema, candidate, scientific result, or submission is produced by design approval.

## Handoff

Design approval and the focused prerequisite review are recorded. Follow
[`../IMPLEMENTATION-START.md`](../IMPLEMENTATION-START.md), protect the planning/source work
through a reviewed Git checkpoint, and hold the first-experiment strategy session. Foundation setup
and early experiments follow their scoped prerequisites; Plan 04's walkthrough is complete (D-045); it still needs explicit coding authorization.

After actual delivery, record the exact submitted package/version, date, destination, and any known
limitations. Preserve the capstone evidence and historical artifacts. Future enhancements begin as
new versions, not edits to the submitted scientific record.
