# PROWL data and cohort design

**Status:** Approved Plan 02 design baseline  
**Owner:** Quinton Evans

This directory holds the source-independent data design. PANORAMA-specific label decoding,
exclusions, annotation eligibility, and image fingerprinting remain in Plan 03.

## Documents

| Document | Purpose |
|---|---|
| [`CURRENT-INVENTORY.md`](CURRENT-INVENTORY.md) | Audited facts and known hazards in the files that exist now |
| [`DATA-DICTIONARY.md`](DATA-DICTIONARY.md) | Meaning and minimum fields for Plan 02 records |
| [`COHORT-PROTOCOL.md`](COHORT-PROTOCOL.md) | Parentage, grouping, deterministic selection, protection, and freezing rules |
| [`PANORAMA-INVENTORY.md`](PANORAMA-INVENTORY.md) | Current local PANORAMA evidence, counts, anomalies, and source gaps |
| [`PANORAMA-MAPPING.md`](PANORAMA-MAPPING.md) | Plan 03 identity, target, voxel, provenance, and annotation-use rules |
| [`DUPLICATE-PROTOCOL.md`](DUPLICATE-PROTOCOL.md) | Layered declared/exact/approximate cross-source duplicate controls |

The generic data/cohort implementation lives in
[`../implementation/02-data-and-cohorts.md`](../implementation/02-data-and-cohorts.md). PANORAMA
source integration and its pending design recommendations live in
[`../implementation/03-panorama-integration.md`](../implementation/03-panorama-integration.md).
