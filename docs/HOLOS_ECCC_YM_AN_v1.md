# ECCC NIR check of Holos dairy Ym 5.6%

**Version:** AN_v1  
**Date:** 2026-11-01  
**Parameter:** `HOLOS.Ym.dairy_lactating|canada` = 5.6% GE  
**Rule:** cite the exact table and page if the 5.6% value is found; otherwise leave it **UNVERIFIED**.

---

## Verdict

The Holos **point value 5.6% is UNVERIFIED**. No ECCC NIR table or page independently read in this phase lists dairy Ym = 5.6%.

What **was** independently read is a **range**, not the Holos midpoint:

> Weighted provincial Ym values varied between **5.5% and 5.7%**.

and later in the same section:

> Ym for dairy cows is varied over time and by province, averaging **5.5%–5.7%** of GE, while a fixed Ym of 6.5% is used for dry dairy cows and dairy heifers.

Holos’ CSV footnote that 5.6% is the midpoint of a 5.5–5.7% range is **consistent with that text**. The midpoint itself is a Holos choice, not a published table cell.

---

## Sources actually opened

### ECCC 2024 NIR Part 2 (1990–2022) — independently read

- Title: *National Inventory Report 1990–2022: Greenhouse Gas Sources and Sinks in Canada*, Part 2, 2024 edition.
- Suggested citation in the file: Environment and Climate Change Canada. 2024.
- URL opened: https://unfccc.int/sites/default/files/resource/2024NIR%20-%20Part%202.pdf
- Agriculture methodology is **Annex 3.4**, not Annex 3.3.
- Annex 3.3 in this edition is **Industrial Processes and Product Use** (tables A3.3–1 … A3.3–4). It is not enteric fermentation.
- Dairy Ym discussion: **Annex 3.4, section A3.4.2.1** (“Enteric CH4 Emission Factors for Cattle”).
- The 5.5–5.7% sentences sit immediately before **Table A3.4–10**.
- Table of contents: Table A3.4–10 at **p. 117** (that table is **dry matter intake**, not Ym). Table A3.4–11 at **p. 118** is enteric **emission factors** (kg CH4 head⁻¹ yr⁻¹), not Ym percent.
- There is **no Table A3.3–10** dairy Ym table in this edition.

### ECCC 2025 NIR Part 2 (1990–2023) — independently read

- URL opened: https://unfccc.int/sites/default/files/resource/2025NIR%20-%20Part%202.pdf
- Same Annex 3.4.2.1 wording: provincial dairy-cow Ym 5.5%–5.7% of GE; dry cows and heifers 6.5%.
- Still no table cell equal to 5.6%.

### ECCC 2022 NIR (Holos citation year) — not opened

Holos cites “ECCC (2022)” / NIR 1990–2020 Part 2  
(`https://publications.gc.ca/collections/collection_2022/eccc/En81-4-2020-2-eng.pdf` in `HOLOS_CODE_AUDIT_AN_v1.md`).

That 2022 PDF was **not independently opened** this run: publications.gc.ca returned an archive interstitial; the same host and UNFCCC file URLs returned HTML/WAF pages from this environment’s curl. AN_v1’s “Annex 3.3, Table A3.3–10” citation is therefore **not confirmed**, and in the 2024/2025 editions that table number is the wrong annex.

---

## What AN_v1 got wrong (do not overwrite AN_v1)

`docs/HOLOS_CODE_AUDIT_AN_v1.md` finding 7 stated Annex 3.3 Table A3.3–10 as the dairy Ym table and labelled confidence HIGH. In the 2024 and 2025 Part 2 files:

- Annex 3.3 = IPPU
- Table A3.4–10 = DMI
- Dairy Ym is **running text** in A3.4.2.1, as a **range**

That AN_v1 table/page citation remains **unverified** against the 2022 edition and is **incorrect** for the 2024/2025 editions that were read.

---

## Parameter file

`data/holos_params_canada_AN_v4.csv` (v3 not overwritten):

- value still 5.6% GE (Holos midpoint; used by `HOLOS.YM.dairy` default)
- status **UNVERIFIED**
- dist bounds 5.5–5.7 match the independently read ECCC range
- notes record the 2024/2025 text and the missing 2022 PDF

Fork registry `data/holos_forks_AN_v2.json` (v1 not overwritten) uses the same UNVERIFIED wording for the Canada option. IPCC 2006 Table 10.12 p. 10.30 dairy Ym 6.5% remains **VERIFIED**.
