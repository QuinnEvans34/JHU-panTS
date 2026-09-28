# Proposed scoped Git checkpoint — September 28, 2026

Historical initial inventory. The subsequent [review](GIT-CHECKPOINT-REVIEW-2026-09-28.md)
and its exact candidate manifest supersede this inventory for approval. Later P1/P3 log
entries and Codex's documentation updates changed several hashes below; retain this snapshot.

Status: scope prepared for discussion; **not authorized, staged, committed or pushed**.

## Recommendation

Include the seven approved Plan 07 planning documents together with the shared reconciliation,
September data/acquisition code, tests and evidence notes. Review the exact file contents and
cross-file dependencies before staging. Do not use `git add .` or sweep in unrelated files.
A checkpoint preserves work; it does not promote data eligibility or authorize a run.

The checkout is on the Mac's internal APFS filesystem, not the external data drive.
A local commit provides version history on that same device. An authorized push would provide
a remote copy; remote availability, repository visibility and the publish diff still need review.
Configured origin is `github.com/QuinnEvans34/JHU-panTS.git`; no network/push was performed here.
Current HEAD is `f4d7109b466fc12854be4a86c9893750399a0672` on `main`.

Exclude root proposal DOCX copies, historical draft PDFs/DOCX, `MedFormerPanTS/`,
unreviewed assets/images, loose `pubmed_samples.xml`, `panorama_manual_ids.txt`, unrelated
proposal/demo scripts, ignored local roots/secrets, raw data, model weights and run outputs.
These remain preserved locally. No deletion or cleanup is proposed.

## Review still required before publication

- Review every candidate diff, including pre-existing uncommitted work, for correctness,
  credentials/personal content, licensed source material and accidental data inclusion.
- Check referenced source/test/document dependencies and inspect ignored-file boundaries.
- Confirm destination and visibility, then obtain explicit commit/push authorization.
- Stage only reviewed paths, inspect staged diff, verify tests against that exact snapshot,
  then commit and, if authorized, push and verify the remote commit.

The inventory below is a candidate scope, not a claim that all historical changes were reviewed.
It captures file bytes now; re-inventory if Claude or Codex changes them before checkpointing.
This scope note and the integration handoff/checkpoint updates should also be included.

## Candidate inventory

110 changed/untracked files plus this scope note; 1,124,061 bytes excluding this note. SHA-256 identifies this inventory snapshot only.

| Path | Bytes | SHA-256 |
|---|---:|---|
| `AGENTS.md` | 47575 | `2bf706721e27ba9db4e75fd8f22ce1282f3b23d77e29195532ecb2f07ac6d599` |
| `configs/local/roots.example.yaml` | 1967 | `2fac7e4696da0601313794416c3c38928add9e14309bd5343ac8bb2250c8d9d1` |
| `configs/local/roots.schema.json` | 3752 | `89c44a791273b043898eb04d6749e868caae11e965317b1dba2c41166afbb6cf` |
| `docs/capstone/CODEX-HANDOFF-2026-09-28.md` | 9405 | `2e82a8955ce390713aafcef6880d839e79c59fd69784db8b3f36ba1dbd23031d` |
| `docs/capstone/DECISIONS.md` | 57337 | `04ba0dff9af23fdc0842ae15f6d2dbe96bb3c81444f6d0e9d667b3a62afd5d82` |
| `docs/capstone/IMPLEMENTATION-START.md` | 19570 | `dc6607fada90a7288b8210e981606e5ddf6aeab032181b7183a68c2c09144c9a` |
| `docs/capstone/README.md` | 13193 | `49ef1574dced41fe2e651a4a137f5f29ba5c1ec965c4106e2185554eb275ea39` |
| `docs/capstone/contracts/VALIDATION.md` | 2645 | `7d2dc6fba51b064dbdbfe0ae992d9c9e2cc0d8bbaa772a843a7ee9eddb5f9fc7` |
| `docs/capstone/contracts/annotation-record-v2.schema.json` | 4703 | `215e18b3537a17bc63ecb4006a75da9f4e7c286c2553b2722876ccaa4afd79f4` |
| `docs/capstone/contracts/manifest-v2.schema.json` | 5261 | `dfcdbfe789d90477ccdd6b18535ceeeb8ff03cea914b266b5531573ced1bee06` |
| `docs/capstone/data/ANNOTATION-ASSESSMENT-2026-09-28.md` | 3865 | `fd4ad07fafa10ee4cc80d6f31db98b0267fb0940818c8bbfedda9ce0fc4751db` |
| `docs/capstone/data/ANNOTATION-CONTRACT-V2-2026-09-28.md` | 5242 | `6a88cfea60d3bba6758f2800ba646bc4719f40e9f1dc44fa11f8602b501b1da1` |
| `docs/capstone/data/BINARY-DECODING-APPROVAL-2026-09-28.md` | 2217 | `3929e0e359d1aa1d4a5cc5a0066285699821ed648bbe87bfdcbc2bc2bead6de3` |
| `docs/capstone/data/BINARY-POLICY-LINEAGE-2026-09-28.md` | 6146 | `5d58c9dcd761d5380a32b2f67ab11f9555723b89c9b7c169d3b177754718196c` |
| `docs/capstone/data/CASE78-COVERAGE-REVIEW-2026-09-28.md` | 3174 | `d5ac2b95a4b60f523ea4b75a25863d2b2473f314fe2c3df910f79ec30d43dbdc` |
| `docs/capstone/data/LAYOUT-INVENTORY-2026-09-22.md` | 4901 | `4a32da51b3c2cba15a4be154f771985f077fe44581fdfda716f9c649eccd6f33` |
| `docs/capstone/data/LINKED-ASSESSMENTS-2026-09-28.md` | 4474 | `85bad8ac02923398c3bc4472f954467be9623965b99f1ab32ff36eee591fb091` |
| `docs/capstone/data/MANIFEST-ASSEMBLY-2026-09-28.md` | 3527 | `3e0e2d76e457fac3e8b6913dbccfa2cdc45079aacfc6dbab44282faef3f366db` |
| `docs/capstone/data/MANIFEST-SLICE-2026-09-28.md` | 5030 | `40db8702b104ba01b70e4ec9a2d180d6380f52a5eec74194526f97715d089961` |
| `docs/capstone/data/MANIFEST-V2-SLICE-2026-09-28.md` | 4991 | `976f5804ec56a84b3930f2df36b057b9ccaef9172902d89b58a5596e29d99dcf` |
| `docs/capstone/data/METADATA-ADAPTER-2026-09-28.md` | 2698 | `4f7ac1a72d6880506f1279089963d5718e3c5fa525088816f24d4f9cd971779c` |
| `docs/capstone/data/OBSERVED-LAYOUT-2026-09-28.md` | 11973 | `29a5c783c920bcd0e6c407df447a7647dcbd2e916d7265d7e74ec4a9cf92b774` |
| `docs/capstone/data/PANTS-ANNOTATION-REVIEW-2026-09-28.md` | 6683 | `9d95e327160d6f6dc82e94abc73b53537779572fa48bc82b3e1a7576ffe2345a` |
| `docs/capstone/data/PANTS-SOURCE-USE-REVIEW-2026-09-28.md` | 5842 | `4da0024993134d17552fd999b4fd1f45c3e436d814f2f4ae7922abfc9b57e5b0` |
| `docs/capstone/data/PLAN-02-IMPLEMENTATION-2026-09-28.md` | 3399 | `3b93146f1bcbe701128722a25572114d1d716c0b12518ff59044bc7b8b5b3440` |
| `docs/capstone/data/PURPOSE-ELIGIBILITY-DECISIONS-2026-09-28.md` | 5680 | `fc6d258b7767e9d03f28d1a6e990fe325db08f84043ce06314702d1e24ed66f2` |
| `docs/capstone/data/SOURCE-EVIDENCE-2026-09-28.md` | 3778 | `acf8ef82b16d25b8ab1fa418b682fda67c97f54ae004370cd12175dc440a30ba` |
| `docs/capstone/data/SPATIAL-UNITS-REVIEW-2026-09-28.md` | 4401 | `04a24b3e5d0ecce50f916f8fb3116ab9df7e7b6e20a987f9628b7f06aa1d57d2` |
| `docs/capstone/data/UNIT-EVIDENCE-INVESTIGATION-2026-09-28.md` | 9733 | `44685e6a4760174bba166369100ab3c1c5d818b6b39747ed4783916ce46d7ac8` |
| `docs/capstone/data/VOXEL-AUDIT-CLAUDE-HANDOFF.md` | 11925 | `9e0456859d67570136235709cd1ae07834172bc4cc5baf2bf7e07b3fe3478e07` |
| `docs/capstone/data/VOXEL-AUDIT-CODEX-REVIEW-2026-09-28.md` | 6526 | `936dda94d85b8226efec536c4828f3cf11cf00dbeee437958a54244b1a38ebd1` |
| `docs/capstone/data/VOXEL-AUDIT-DESIGN.md` | 12567 | `69b98ae6cfcffedc36a319aa04919292f80c9108d0b7e43267894da44685b963` |
| `docs/capstone/data/VOXEL-FOLLOWUP-PLAN-2026-09-28.md` | 7295 | `881afc2ef9ea7102e2bbc8468ca811ed696247336b1ca441be7f1b93c61be11f` |
| `docs/capstone/data/VOXEL-FOLLOWUP-RESULTS-2026-09-28.md` | 5993 | `0eb3d44dc252a39a25f92b87a7cf7a588978aa9cb5055048762fd73bf0c479ab` |
| `docs/capstone/data/VOXEL-PILOT-2026-09-28.md` | 3009 | `dd179b371dc9093854c8fa16d1b67c8998522f1bc8899fa3b257c75edc856399` |
| `docs/capstone/implementation/02-data-and-cohorts.md` | 18905 | `478f637ae97f9cdad979c76b01e35bcbec01c78db05f8b46cf612983f604fd81` |
| `docs/capstone/implementation/07-literature-retrieval.md` | 40219 | `d596d9fa18c6185b93a3c8b5ab21aa361e3a58f7d44b80e59fc0b71e5fb7d7b6` |
| `docs/capstone/implementation/10-reproducibility-and-operations.md` | 47846 | `1517a0057aec45939cae0b4a3e776062c15152fb0fbd0de86641bf3909bf4187` |
| `docs/capstone/implementation/12-integration-and-delivery.md` | 28741 | `994aed7e34d48f19122d5f885ea2e1ef8e6b5e8d82eea992c76fc89482aebffb` |
| `docs/capstone/operations/BACKUP-RETENTION-AND-RECOVERY.md` | 13876 | `285047aad7a171405ea704a1361df22392bb37ce0e4ad7157658521d90a0053f` |
| `docs/capstone/operations/CLAUDE-PLAN07-FOUNDATION-PACKET-2026-09-28.md` | 14454 | `5ba792c45bf109978101b26c24151d392edf47a53621eb92a2423a38ab080546` |
| `docs/capstone/operations/CLAUDE-PLAN07-P3-PACKET-2026-09-28.md` | 10064 | `46fc390c0c443c283991aef4c0d40d38c56443e28ea5bd445b1e65ba8f333dc4` |
| `docs/capstone/operations/CLAUDE-VOXEL-AUDIT-HANDOFF-2026-09-28.md` | 8032 | `eb1611ed23d7f8d16f7e70759ca070b4c11d3f76b4812bd645aec5c39f5365fc` |
| `docs/capstone/operations/CURRENT-CHECKPOINT.md` | 8638 | `74d60a6120d52fa1527a2ca0a251920c545d29f13b0da8fafa9ccbabfe7f8930` |
| `docs/capstone/operations/DATA-ACQUISITION-QUEUE.md` | 8228 | `38b3d4150755cc1fa210a49305841a02f831e81804a4dc5c285bb383729d4da1` |
| `docs/capstone/operations/DRIVE-PREP-2026-09-21.md` | 5918 | `bc6496d7839e2575d20479c8b0a191951ca5c6e2e23506802d515552a17283d8` |
| `docs/capstone/operations/EXTRACTION-BUDGET-2026-09-22.md` | 3705 | `d12d12ac67caa3c293fa3db531c8c7531ff4c0b50784831478e2865b530afdcb` |
| `docs/capstone/operations/EXTRACTION-DESIGN-2026-09-22.md` | 14373 | `db690596a6887c71e144d35a4d720ea2407dc8e08ee90523d93b2a3ef75a5bfd` |
| `docs/capstone/operations/EXTRACTION-REVIEW-2026-09-28.md` | 9692 | `a1792ed5815db10309631d3996442361778839cd3cb54d5a71836c32c4e95940` |
| `docs/capstone/operations/EXTRACTION-RUN-2026-09-22.md` | 8018 | `384fd9efbdd2b9ceb09c3178e6374c98e8ed4ac540d2e5d6d3636911389c54d8` |
| `docs/capstone/operations/FIRST-EXPERIMENT-READINESS-2026-09-28.md` | 9674 | `2b95fb6ce9d27675832b07b5e84d05ad8098aaec0d5e4e9aa697d3533083362d` |
| `docs/capstone/operations/PLAN07-CODEX-DECISION-RESPONSE-2026-09-28.md` | 14232 | `c5abac5436d1477259132466830595ee4aa976047ac6d658773c524eb09ffda7` |
| `docs/capstone/operations/PLAN07-INTEGRATION-HANDOFF-2026-09-28.md` | 4836 | `d80d3093fc99dabd7317683e515f6d3dffe2b9dc13f200bd12634c0e8f9b7b11` |
| `docs/capstone/operations/POSTGRES-PGVECTOR-DECISION-2026-09-28.md` | 3557 | `e792de0ea0e418ca2378ac67f6b44fbc93764b75163b7d47c7369017fcbb0461` |
| `docs/capstone/operations/STORAGE-ROOTS-AND-ARTIFACTS.md` | 13032 | `1cf218a2457c624de3b5212cb0ce5205528e106b53b01ed53167933992723d22` |
| `docs/capstone/operations/TEAM-STATUS-2026-09-28.md` | 9348 | `4bbaee15da7aa00ffa6808c09dc587a00828c92be57f2726b023cbe321dc997a` |
| `docs/capstone/operations/TODAY-2026-09-28.md` | 14149 | `14953f313af52a111c1575956568e18a7e0b67cc1016133b18c724d68e605c7b` |
| `docs/capstone/retrieval/CORPUS-AND-RIGHTS.md` | 10706 | `6e31487428db7bc790fa9a598f2c17c61ff98137ea26824e2890f02f462cde0f` |
| `docs/capstone/retrieval/QUERY-AND-RETRIEVAL.md` | 7407 | `5bd35e1822d694d98a7176527fba23776a24fa2d307318b0347d7ad7d0ef1b33` |
| `docs/capstone/retrieval/QUESTION-SET-AND-EVALUATION.md` | 11443 | `7ada29f1560a96c85da8460551c2b4693ee0510baf56a58621525a6b935f428b` |
| `docs/capstone/retrieval/README.md` | 4122 | `f41e1808e565e032dfd394bceea9ea57bfc9518d42eba625c6b1325783f1f693` |
| `docs/capstone/retrieval/TOOL-SELECTION.md` | 9200 | `26b5439227ac000ddd705d0eb99c0124648135101d0a7775aabf450f92c23f74` |
| `docs/capstone/retrieval/planning/ACQUISITION-PLAN.md` | 12545 | `39e3752005907483d60667603a520ab549f9219dcb17d213f9c6de4f9e99fd2d` |
| `docs/capstone/retrieval/planning/INFORMATION-NEEDS.md` | 8006 | `5e9764cc94c6d06db4b9b84ec766128aaa6c1d3599fe18f04c8e8d8e9f1a0721` |
| `docs/capstone/retrieval/planning/PHASES.md` | 20393 | `b4abe42d9d1b43504087175ab8f168356fd16356e6868402713ada862d1da4ca` |
| `docs/capstone/retrieval/planning/RUNNING-LOG.md` | 25772 | `0697c30751b5f00734d3cd1b84d7250e22d1043a965bce973716ca5cb3e131b7` |
| `docs/capstone/retrieval/planning/SCOPE.md` | 33944 | `ca9a0de192cf5d6b241c17ca1796f02b7c39b006e2e9d872afc1c3b767861672` |
| `docs/capstone/retrieval/planning/SEARCH-AND-SELECTION.md` | 12194 | `bcddbb4b78ba6ab50be059936ecb606fb145b9a1db81f1ab58761edd30c0728c` |
| `docs/capstone/retrieval/planning/SEED-SET.md` | 5214 | `39ee09bc8327c6bccc9f15f859ebf041345bde68385d4a3639134aa6f8f66d81` |
| `docs/capstone/weeks/WEEK-01.md` | 9660 | `f398ea54458556e727bb9d35c1c7104bc7569eca7f27a842466cd6a49a7727c2` |
| `scripts/acquisition/extract_sources.py` | 18650 | `f5f98af94cd232e29ba7f283c132540eaceb1888c43c367190d4ff0555bbd4f2` |
| `scripts/acquisition/member_safety.py` | 3642 | `68f53a4ec8e8e777321667a7344edc3076674dd5c05b2ea8f319cd2b5dcb8902` |
| `scripts/diagnostics/audit_voxels.py` | 37156 | `f18a1a129a0fa24660241b5cb8770d2ac6807768799dd153004775eea25d1353` |
| `scripts/diagnostics/build_manifest_slice.py` | 10736 | `adde7757aeb5cd010bb6ef9880367e2f44b328dcfbf9347cfaa9fc1d0d481575` |
| `scripts/diagnostics/build_manifest_v2_slice.py` | 10302 | `d25db22f0c786edf007261723e8cc9f19283b247b4187d1a4ca21562f125b3c6` |
| `scripts/diagnostics/check_case78_coverage.py` | 4647 | `1ef1ebb86be8d127be2c089e4d3e1e41c9a48fa94f2dfb38ca3b23f66c5bd573` |
| `scripts/diagnostics/followup_voxel_audit.py` | 11444 | `9f38010c63128a569e81950dc7c5667e6b1e7afe0bcc6a745e1751d8708e835b` |
| `scripts/diagnostics/inventory_sources.py` | 23904 | `193cb2e751646dfe1f79ea28830c55026985294b67a11da42579d0d6473e7141` |
| `scripts/diagnostics/link_annotation_assessments.py` | 3427 | `8cafad84d271b124e1101f83495a62cefd5cf89f41aa362ba7999e70e5d2b709` |
| `scripts/diagnostics/pilot_voxel_audit.py` | 5378 | `7434cd329c9f9f7f1c972c0fc936d1e0360241528e997c3b214654bf41045874` |
| `scripts/diagnostics/scan_pants_archives.py` | 7513 | `e47e71073fcb30f6e394e8c3fc4acce350db6ffe442dc3f0576469bf1f4456a8` |
| `src/data/annotation_assessment.py` | 4670 | `a755f72813e2eb90dc6a8b6fd495eacc8190885235fc45fc0fbd7b18b64293ca` |
| `src/data/annotation_contract_v2.py` | 7461 | `47939ed9e02638bd91672bbb331640220354331d92442f0c50a52946729724e7` |
| `src/data/annotation_v2_records.py` | 2544 | `4f33bf17ee0fcaf677c79eda3a0023011e4257369c1f2232397a25887dcf3d8e` |
| `src/data/audit_assessment_link.py` | 8547 | `e79132dd466a973862e2d008a0ca606f0a7cd539732923a7cc3e8892647d7d6e` |
| `src/data/binary_label_policy.py` | 1666 | `ecdbe3e887c4b791f1079e81dcb22d804fda2e8c4b661c341ae422d90e6f4407` |
| `src/data/manifest_records.py` | 7187 | `090dabfc1fd7ea5879bed4d8fcc77e4b465bef210ee0652d2a6fb18daf10d5e7` |
| `src/data/manifest_records_v2.py` | 7564 | `b2697d9479bcfb6210a9e49a252e95d05fd18bdf72ccd3b857a88d9a4a67a4d1` |
| `src/data/pants_metadata.py` | 6320 | `b809e77cc97253a2ace927bbddca1dc9be5d480b1c83419ad77b7bb1ca55b4eb` |
| `src/data/protected_identity.py` | 4096 | `833dc2dcb2d08d355810dca23232d220d458fcb1c837cd402bbd77b8c8e5b755` |
| `src/data/source_evidence.py` | 8732 | `54fe5b2c5fe56696149be57ba3bd2f498e73c3144b88f90472b809306ef8433c` |
| `tests/fixtures/contracts/README.md` | 1171 | `b7f3735ad4394d543476d0ad85c94774035b531b8580b8298ba3cdb26a01f7fd` |
| `tests/test_annotation_assessment.py` | 3604 | `c616e3ee4546a90556f236b86f57f4cf7bb8d8b52704c6da035b382a7b844cc8` |
| `tests/test_annotation_contract_v2.py` | 12043 | `8eb91dfd2f981b210b9635fe2927e9bcea14cde238d26c206916e5129921a737` |
| `tests/test_archive_scan.py` | 3081 | `5343274521b39bde619df4f8968ee4e270234b51169bf491a9787b1e80173d43` |
| `tests/test_audit_assessment_link.py` | 6093 | `0567c97ce170538dbc23546c3b42a2fe5744ef04ebde8a3c81a7f775e9131d5a` |
| `tests/test_binary_label_policy.py` | 2696 | `6a352d9e77241294356d5514aaeac6de6e3a151df589c0188b216f593ac863a4` |
| `tests/test_case78_coverage.py` | 958 | `54521e03f2591384d62994aef455a7467faae39780eb361dcc9780dbc0fafd93` |
| `tests/test_extraction.py` | 17238 | `68b3756e561ab079b4d455545de030a3c43846e40c72db389ec6188b5655a3c2` |
| `tests/test_followup_voxel_audit.py` | 4533 | `8368f85b355e049d2dcbbf2ea452aa69f2420aadf7609ac95cc1e5549ba294c7` |
| `tests/test_inventory.py` | 17848 | `d4f25f94aa877f481e620510569e73ebc0d9b37ca42e6f314a7559f77283a3ed` |
| `tests/test_manifest_records.py` | 3424 | `444ec366e9b5bdaf78a261ae7e92d6c0f99928740362cdf334ec26a1ab6d5459` |
| `tests/test_manifest_slice.py` | 3249 | `6fbafdcd3955a045979e7965ffef3dd2237b511241af91b1fb138ab845f7a31a` |
| `tests/test_manifest_v2.py` | 4566 | `b1921dbc7af7cf6744f769bdee3fbf0d0b1a8e5f19d5b90269280b300522b039` |
| `tests/test_member_safety.py` | 6172 | `3eb755632441096debd88c12293a190634fa9d32a3de668bdceab3672d41c3bd` |
| `tests/test_pants_metadata.py` | 4679 | `4dc2143ffbb809e2227116843b3fcdbc5a4cd29e18244f5e9b3bec45fa707e1b` |
| `tests/test_protected_identity.py` | 2470 | `bbd6a1a462920556ccb83ff5ece2440d2a03f485a28e164fad179e69e8dcce18` |
| `tests/test_source_evidence.py` | 5333 | `7143f39c27706c259d9b1bc06398ce7bd2b12e99c4bde984df4fad879f481bb2` |
| `tests/test_storage_registry.py` | 2425 | `57f48e1a9430431ab535d6261b47f5fd56a45215999f5f36f74914cc17e6f748` |
| `tests/test_voxel_audit.py` | 36272 | `b5829217402b8667cbf43b5e3e37106535bfa6b4fc72fd7a73b0cb916e18694b` |
