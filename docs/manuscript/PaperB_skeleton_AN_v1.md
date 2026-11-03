# Paper B manuscript skeleton (AN_v1)

**Working title:** Living papers for agricultural greenhouse gas models [title TBD; ≤ journal title limit, check at submission]
**Target:** *Nature Food*, **Analysis** format
**Lead author:** Alex Neumann, University of Toronto (ORCID 0000-0003-1590-8516). Co-authors TBD.
**Status:** skeleton only. It contains no results. `[CITE?]` marks a reference that is not yet verified. `[RESULT?]` marks a number that ghgsim has not produced yet.

Ground rules for this manuscript:
- Comparisons with field data are **consistency checks, never validation**.
- No Holos MS2 (Saha et al.) data or results. No mention of the companion Ratna paper.
- Cool Farm Tool appears only as a closed-tool cautionary example.
- The paper is US-centred. Canada, UK, NZ, Ireland, Germany and Australia are inventory comparators.

---

## 0. Journal requirements (verified 2026-11-03)

Sources:
- Content types: https://www.nature.com/natfood/content
- Formatting: https://www.nature.com/natfood/submission-guidelines/aip-and-formatting
- Reporting standards, data and code: https://www.nature.com/natfood/editorial-policies/reporting-standards

| Item | Analysis requirement |
|---|---|
| Definition | "A new analysis of existing data or ... new data obtained in a comparative analysis that leads to novel and arresting conclusions of importance to a broad audience" |
| Main text | ≤ 3,000 words (excludes abstract, Methods, references, figure legends) |
| Abstract | 100–150 words, no references |
| Display items | ≤ 6 (figures and/or tables combined) |
| Structure | Introduction (no heading), Results, Discussion, Methods. Results and Methods may use subheadings; the **Discussion has no subheadings** |
| References | Guideline is ≤ 50. Methods-only references continue the numbering. Datasets and code with DOIs go in the reference list. URLs are cited in the text, not in the reference list |
| Figure legends | Count against the article word limit; brief title plus panel descriptions; avoid methodological detail; state centre values and error bars |
| Methods | Short bold subheadings |
| Data availability | Required statement covering primary and referenced datasets with accession codes or identifiers |
| Code availability | Required "Code availability" section when custom code is central. Code is shared with editors and reviewers and may be peer reviewed. Best practice is a DOI-minting deposit (Zenodo or Code Ocean) cited in the references, with a licence |
| Reporting summary | Required "where relevant" for research papers; it is published with the paper. Likely the ecology, evolution and environmental sciences form [confirm with editor or at submission] |
| Supplementary info | Allowed, as a single combined PDF; cite each item in sequence |
| Other | Peer reviewed; received and accepted dates |

Not verified yet: title length limit for Analyses, cover letter and presubmission enquiry expectations, and open-access APC. Check these on the submission system.

---

## 1. Word budget (main text ≤ 3,000)

| Section | Target words | Purpose |
|---|---|---|
| Abstract | 140 (100–150) | Problem, living-paper design, headline [RESULT?] numbers, implication |
| Introduction (no heading) | 450 | Ag GHG estimates change when model code or IPCC guidance changes; static papers go stale; closed tools (Cool Farm Tool as a cautionary example [CITE?]) cannot be re-run; agentic papers (Paper2Agent, Miao et al. 2026, *Nature* 658, doi:10.1038/s41586-026-11044-y) |
| Results 1: Living-paper architecture | 350 | Archived engine, version control, automatic recompute, dashboard and paper agent |
| Results 2: IPCC 2006 vs 2019 on stylized farms | 450 | Tier 1/2 deltas by source (enteric, manure CH4/N2O, soil N2O, residues, lime/urea) |
| Results 3: US county analysis | 550 | Census-driven county emissions; method-version deltas versus EPA inventory recalculations |
| Results 4: Maumee watershed case study | 350 | Watershed-scale effect of method choices |
| Results 5: Cross-engine and international context | 350 | ghgsim vs HESTIA CE / APSIM / GLEAM-X; recalculations in six national inventories |
| Discussion (no subheadings) | 500 | What living papers change for science and policy; limits; governance; field comparisons as consistency checks only |
| **Total main text** | **~3,000** | |
| Methods (outside limit; keep ~2,500–3,500) | | See section 3 |
| Figure legends (count to limit; keep ≤ ~250 total) | | Budgeted inside the sections above |

---

## 2. Display items (≤ 6)

| # | Item | Content | ghgsim source | Status |
|---|---|---|---|---|
| Fig. 1 | Living-paper architecture | Engine archive (DOI) → git → CI recompute triggers (code change, IPCC guideline change) → dashboard + paper agent | `src/ghgsim/core/{archive,manifest,provenance,registry}.py`; fork diagram `docs/figures/fork_diagram_AN_v6.mmd` | Schematic to draw; recompute CI, dashboard and agent not built |
| Fig. 2 | IPCC 2006 vs 2019 on stylized farms | Per-farm, per-source deltas (Tier 1/2), with Sankey insets | `data/stylized_farms_AN_v6.yaml`; `src/ghgsim/modules/ipcc2006/`, `ipcc2019/`; `src/ghgsim/report/emissions_sankey.py` | Engine exists; a clean IPCC-only 2006-vs-2019 run table is needed (current stylized delta files are Holos-fork outputs) |
| Fig. 3 | US county map of method-version deltas | Choropleth of Δ(2019−2006) county emissions; inset: sources driving Δ | `src/ghgsim/io/nass.py`, `io/usgs.py`; `scripts/fetch_nass_data.py`; county P/PE inputs (PR #20) | Partial: VT/DE runs only; national run not done |
| Fig. 4 | Recalculation dynamics | (a) EPA Inventory year-to-year recalculations of US ag CH4/N2O; (b) same for CA, UK, NZ, IE, DE, AU | Inventory-recalculation pipeline (planned) | Not started in repo |
| Fig. 5 | Maumee watershed case study | Watershed emissions under method versions; consistency check against GRACEnet / Global N2O DB fluxes where sites overlap | `data/benchmarks_manifest_AN_v4.json`; `scripts/fetch_benchmarks_AN_v1.py` | Benchmarks staged; Maumee runs not done |
| Table 1 | Engine and version matrix | ghgsim, HESTIA CE v7.1.0 (commit d63cd6b), APSIM NG 2026.11.8142.0 (commit d1dca5e), GLEAM-X [version?]; licence, openness, re-runnable Y/N; Cool Farm Tool as a closed comparator | `scripts/check_licenses.py`; `docs/BUBBLE_SETUP_AN_v2.md` | Partly filled; GLEAM-X not installed |

Supplementary (planned): Sobol and Monte Carlo sensitivity (`services/sobol.py`, `services/montecarlo.py`); coefficient trace (`data/coefficient_trace_AN_v9.csv`); full parameter tables (`data/ipcc_params_AN_v7.csv`); benchmark manifest; PE-formula sensitivity (PR #20).

---

## 3. Section skeleton

### Abstract (100–150 words, no references)
[Write last. No numbers until ghgsim produces them.]

### Introduction (no heading)
- Ag GHG estimates are model- and guideline-dependent; inventories are recalculated [CITE? EPA GHG Inventory; UNFCCC CRF recalculation tables].
- IPCC 2006 Guidelines and the 2019 Refinement [CITE? IPCC 2006 Vol. 4; IPCC 2019 Refinement Vol. 4].
- Static papers freeze one model version; closed tools cannot be audited (Cool Farm Tool as an example) [CITE?].
- Reproducibility and executable-paper precedents [CITE?]; paper agents (Miao et al. 2026, Nature, doi:10.1038/s41586-026-11044-y; verified).
- Contribution statement: the living-paper design and what it reveals.

### Results
1. **A living paper for agricultural GHG estimates.** Design, archive, triggers, dashboard, agent.
2. **Guideline version changes shift farm-level estimates.** Stylized farms, 2006 vs 2019, Tier 1/2.
3. **County-scale consequences in the United States.** USDA Census of Agriculture inputs [CITE? NASS Census 2022]; comparison with EPA inventory recalculations.
4. **A watershed view: the Maumee.** Case study; field-flux consistency checks (GRACEnet [CITE? Ag Data Commons doi]; Global N2O Database, EDI doi:10.6073/pasta/09a95cf44cd7835db002b0089ed5ffc3; Dorich et al. 2020 doi:10.1016/j.cosust.2020.04.006).
5. **Engines and national inventories.** HESTIA CE [CITE?], APSIM [CITE?], GLEAM-X [CITE?]; recalculation patterns for CA, UK, NZ, IE, DE, AU [CITE? each NIR].

### Discussion (no subheadings, ~500 words)
Implications for food-system policy and offset or credit claims; limits (Tier 1/2 scope, data gaps, field comparisons are consistency checks only); governance of living papers (versioning, DOIs, who triggers a recompute); next steps.

### Methods (bold subheadings)
- **ghgsim engine and version registry** (module graph, units, provenance, fork registry).
- **IPCC 2006 and 2019 implementations** (equations by source; parameter tables).
- **Stylized farms.**
- **US county inputs** (NASS Census, USGS county N, NOAA county climate and PE formulas).
- **EPA and national inventory recalculation data.**
- **External engines** (HESTIA CE, APSIM, GLEAM-X: versions, commits, run settings).
- **Maumee watershed set-up.**
- **Field-flux consistency checks** (GRACEnet, Global N2O DB; unit handling, N2O-N × 44/28).
- **Sensitivity analysis** (Sobol, Monte Carlo).
- **Living-paper infrastructure** (CI recompute triggers, archive DOIs, dashboard, paper agent).
- **Statistics.**

### Data availability
Referenced datasets: Global N2O DB (EDI, CC BY 4.0, doi above); GRACEnet (Ag Data Commons, CC0) [DOI?]; USDA NASS Census [URL]; EPA GHG Inventory [URL]; national inventory submissions [URLs]. Generated data: Zenodo deposit [DOI TBD].

### Code availability
ghgsim (github.com/gudaleon/ghgsim), archived on Zenodo [DOI TBD], with licence [state]. Shared with editors and reviewers at submission.

### Reporting summary
Prepare the Nature Portfolio Reporting Summary [confirm which form applies].

---

## 4. TODO: missing analyses and items

| # | Gap | Needed for | Notes |
|---|---|---|---|
| 1 | Clean IPCC 2006-vs-2019 Tier 1/2 runs on stylized farms (not Holos-fork deltas) | Fig. 2 | Engine modules exist |
| 2 | National US county run (all counties) | Fig. 3 | Only VT/DE so far; needs PR #20 P/PE merged and a PE-formula choice |
| 3 | EPA Inventory recalculation series (multiple editions) | Fig. 4a | Not in repo |
| 4 | Six-country inventory recalculation data (CRF/NIR) | Fig. 4b | Gathering started; not in repo |
| 5 | Maumee watershed runs | Fig. 5 | Outstanding |
| 6 | Field-flux consistency checks; N2O vs N2O-N confirmation | Fig. 5 | Email to the database team pending |
| 7 | HESTIA CE and APSIM comparison runs on matched farms | Table 1, Results 5 | Both installed on Bubble; no runs |
| 8 | GLEAM-X: obtain, install, pin version | Table 1 | Not started |
| 9 | Recompute CI (triggers on code and IPCC parameter changes) | Fig. 1 | Not built |
| 10 | Dashboard | Fig. 1 | Not built (`api/server.py` is a base) |
| 11 | Paper agent (MCP server, cf. Paper2Agent) | Fig. 1 | Not built |
| 12 | Zenodo archive DOI for engine and data | Code/Data availability | Not done |
| 13 | Verify all [CITE?] references; keep ≤ 50 | References | IPCC, EPA, NASS, HESTIA, APSIM, GLEAM-X, Cool Farm Tool, NIRs, executable-paper literature |
| 14 | Confirm Reporting Summary form and title limit | Submission | |
| 15 | DayCent / COMET-Farm: decide in or out of scope | Results 5 | DayCent access pending |
