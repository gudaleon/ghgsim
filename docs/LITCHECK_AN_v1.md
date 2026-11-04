# LITCHECK_AN_v1 - Field-literature check of FINDINGS_AN_v4-v9

Purpose: test whether each key model finding is a real effect seen in field data or a model artifact. Model comparisons are consistency checks, not validation. Every paper below was verified by DOI on Crossref (api.crossref.org/works/{doi}) on 4 Nov 2026. Magnitudes are quoted only from abstracts read on that date (Crossref/OpenAlex); papers whose abstract could not be read are cited for scope only, with no numbers.

Verdict scale: supported / mixed / contradicted. "Artifact flag" = the model number probably reflects model structure rather than a field effect.

## 1. Rain-triggered N2O pulses (APSIM: about 55% of annual N2O in 3-day post-rain windows on 16% of days; top 5% of days give 57%)

Verdict: **supported in kind; magnitude plausible.** Artifact flag: partial (missing freeze-thaw).

- Molodovskaya et al. 2012, SSSAJ 76, 1728-1740, doi:10.2136/sssaj2012.0039. Eddy covariance, NY dairy cropland, 2006-2009: peak events contributed up to 51% of cumulative annual N2O in <7% of observation time; largest were multiday peaks after summer rain and at spring thaw.
- Parkin 2008, JEQ 37, 1390-1395, doi:10.2134/jeq2007.0333. Automated chambers, Iowa corn/soybean: pronounced day-to-day variation; sampling every 21 d gave cumulative estimates within +60%/-40%, every 3 d within +/-10%.
- Krichels & Yang 2019, JGR Biogeosci. 124, 3618-3634, doi:10.1029/2019JG005224. Large rains (>30 mm) caused hot moments only in early summer, not in cool spring or at peak crop growth: rain does not consistently trigger pulses.
- Wagner-Riddle et al. 2007, Glob. Change Biol. 13, 1722-1736, doi:10.1111/j.1365-2486.2007.01388.x. Ontario corn-soybean-wheat, 5 years: non-growing-season (Nov-Apr) emissions were 30-90% of annual, mostly during thaw. Wagner-Riddle et al. 2017, Nat. Geosci. 10, 279-283, doi:10.1038/ngeo2907 (freeze-thaw emissions globally important; scope only).

Reading: our 55%/57% concentration is similar to the field 51% in <7% of time. But the field record shows thaw pulses, which a rain-only pulse definition does not capture and APSIM may under-represent. In Ontario especially, the "rain pulse" share should be read as a lower bound on episodic emission, and the rain trigger as season-dependent.

## 2. N2O carry-over into the soybean year (APSIM soybean-year share of fertiliser-induced N2O 0.30-0.42)

Verdict: **contradicted at the one site that tested it directly.** Artifact flag: **yes, likely.**

- Fabrizzi et al. 2024, JEQ 53, 407-417, doi:10.1002/jeq2.20566. Minnesota, drained and undrained: previous-corn N management (0 N vs 135 kg N/ha) had **no effect** on soybean-phase N2O; corn phase 1.83 vs soybean 0.80 kg N/ha.
- Parkin & Kaspar 2006, JEQ 35, 1496-1506, doi:10.2134/jeq2005.0183. Iowa, 2003: soybean 2.2-2.7 vs corn 7.6-10.2 kg N2O-N/ha/yr. Soybean years emit substantially, but this paper does not separate fertiliser carry-over from background.

Reading: field soybean years do emit N2O, but no measurable share is attributable to the previous corn's fertiliser in the only direct test found. An APSIM fertiliser-induced share of 30-42% in soybean years probably reflects simulated residual nitrate and mineralisation carried across years. Treat as a model result pending field tests; do not present it as a field effect. One study is not conclusive.

## 3. Tile drainage lowers N2O (our runs: -7% to -37% with N over matched periods; +13% to +17% at 0 N at Hoytville)

Verdict: **direction supported, effect episodic; 0 N increase not supported.** Artifact flag: on the 0 N sign and on short matched periods.

- Fernández, Venterea & Fabrizzi 2016, JEQ 45, 1847-1855, doi:10.2134/jeq2016.06.0237. Minnesota corn: undrained soil emitted 1.8x more N2O than drained (2.36 vs 1.29 kg N/ha, i.e. drained about 45% lower), but only in periods of excess moisture; no effect when rain was well distributed.
- Fabrizzi et al. 2024 (above): drainage reduced soybean N2O in one of three seasons.

Reading: our 7-37% reduction is in the same direction and below the field 45% average. Field effects depend on wet periods, matching our short matched-period caveat. No field paper found reports drainage raising N2O at 0 N; that sign comes from short, partly failed SWIM records and should be flagged as a possible artifact.

## 4. Annual IPCC/Holos factors flatten the county skew and miss hotspots

Verdict: **mixed; field support is indirect.** Artifact flag: the county skew itself is model-derived.

- Shcherbak, Millar & Robertson 2014, PNAS 111, 9199-9204, doi:10.1073/pnas.1322434111. 78 studies, 233 site-years: N2O rises faster than linearly with N input; higher rate of change in soils with C >1.5% and pH <7. Linear (IPCC-type) factors therefore compress differences between sites.
- Groffman et al. 2009, Biogeochemistry 93, 49-77, doi:10.1007/s10533-008-9277-5. Hot spots and hot moments are hard to represent in models (scope only).
- Krichels & Yang 2019 (above): topographic depressions were not consistent N2O hot spots.
- Jarecki, Hatfield & Barbour 2015, JEQ 44, 431-441, doi:10.2134/jeq2014.03.0100. Process model (DNDC), not field data: Iowa county N2O 2.2 to 4.7 kg N/ha/yr, about a 2x spread, 1.93% of fertiliser N.

Reading: field meta-analysis supports the mechanism (nonlinear, site-dependent response that linear factors smooth out). But "hotspot counties" are defined by APSIM, and field evidence says hot spots are not stable in place. The ranking result is a model-to-model consistency check, not a field-confirmed effect.

## 5. Holos texture-class step (fine/coarse ratio 5.2 in the Holos CLI runs)

Verdict: **mixed.** Artifact flag: **yes, for the discrete step size.**

- Rochette et al. 2018, Agric. Ecosyst. Environ. 254, 69-81, doi:10.1016/j.agee.2017.10.021. Canadian data relating N2O to soil, crop and climate; the source of the Holos precipitation equation (abstract not readable on 4 Nov 2026; no magnitude quoted here).
- Skiba & Ball 2002, Soil Use Manage. 18, 56-60, doi:10.1111/j.1475-2743.2002.tb00050.x. 13 soils under one crop and climate: N2O varied over two orders of magnitude; the soil with maximum emissions switched seasonally (sandy free-draining in spring, poorly drained clay in autumn); texture effects "not consistent", best predicted by bulk density plus clay content.

Reading: texture and drainage class do matter in the field, so a texture effect is real. But field evidence shows a continuous, season- and drainage-dependent effect, not a fixed three-class multiplier. A 5.2x jump at a class boundary (Berrien/Parkhill 0.37% vs Hoytville 3.01%) is a structural feature of the method, so treat it as a method artifact at class edges.

## Summary

| # | Finding | Field verdict | Artifact flag |
|---|---|---|---|
| 1 | Rain pulses, ~55% in 3 d | Supported (51% in <7% of time) | Partial: freeze-thaw pulses missing; rain trigger season-dependent |
| 2 | Soybean-year carry-over 30-42% | Contradicted (no previous-N effect, 1 site) | Yes, likely |
| 3 | Drainage lowers N2O 7-37% | Direction supported (field ~45%, wet periods only) | 0 N increase and short records |
| 4 | Annual factors flatten skew / miss hotspots | Mixed, indirect (nonlinear response) | County skew is model-derived |
| 5 | Holos texture step 5.2x | Mixed (texture matters, not as a step) | Yes, step size |

Not used: Grossel et al. 2016 (doi:10.1016/j.agee.2016.06.015) and Abbasi et al. 2020 (doi:10.1016/j.geoderma.2020.114473) are relevant to drainage and verified on Crossref, but their abstracts could not be read, so they are listed only for follow-up. No manuscript text was changed.