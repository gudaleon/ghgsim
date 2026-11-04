# Decisions AN v24 - APSIM on a real US Corn Belt site; v14 review fixes

Supersedes nothing; DECISIONS_AN_v23.md is kept. Each item: choice, reason, how to reverse.

D24.1 Site. Point 42.020 N, 93.774 W, Boone County, Iowa (SSURGO survey area IA015), central Iowa Corn Belt. Reason: documented SSURGO map unit under row-crop maize country; point is reproducible. Reverse: change `SITE` in scripts/fetch_iowa_site_AN_v1.py and rerun.

D24.2 Soil from SSURGO (USDA-NRCS Soil Survey Staff, via Soil Data Access, survey version 9/8/2026). Map unit 2835012 "Webster clay loam, Bemis moraine, 0 to 2 percent slopes"; dominant component Webster (90%, Typic Endoaquolls, poorly drained, HSG C/D), 4 horizons to 200 cm. Mapping (no value invented): BD = dbthirdbar_r; DUL = wthirdbar_r/100; LL15 = wfifteenbar_r/100; SAT = wsatiated_r/100; KS = ksat_r x 86.4 mm/d; Carbon = om_r/1.724 (van Bemmelen); pH = ph1to1h2o_r; ParticleSize from claytotal/silttotal/sandtotal; horizons > 400 mm split into equal layers with the horizon's values; AirDry = LL15; maize LL = LL15. Reverse: edit the mapping in scripts/run_apsim_crop_AN_v2.py.

D24.3 Borrowed parameters. SSURGO has no APSIM crop/organic-matter parameters, so KL, XF, FBiom, FInert, SoilCNRatio, FOM, FOMCNRatio, SWCON, CN2Bare and initial NO3/NH4 are taken from the documented APSoil No. 900 (as shipped in Examples/Maize.apsimx), matched by layer mid-depth, with summer/winter dates swapped for the northern hemisphere. Listed in results/apsim_AN_v2/apsim_crop_manifest_AN_v2.json. This is a stated limitation, not a calibration.

D24.4 Weather from NASA POWER daily API v2.10.2 (community AG; T2M_MAX, T2M_MIN, PRECTOTCORR, ALLSKY_SFC_SW_DWN), 1991-01-01 to 2020-12-31, no fill values; written as an APSIM .met (tav 9.48, amp 30.43). POWER chosen over Daymet because one point API returns radiation and corrected precipitation together. Reverse: swap the fetch step.

D24.5 Management. Sowing window 19-Apr to 26-May from USDA NASS (2010) Agricultural Handbook 628 (Iowa corn: begins Apr 19, ends May 26); cultivar B_110 from the shipped example; 100 kg N/ha urea at sowing and a 0 N control as before. 2000 was not sown (the sowing rule never triggered); annual means and the EF use the 29 sown years, pulse statistics the full daily record.

D24.6 Main vs sensitivity. Iowa is the main APSIM run; the Australian runs (APSoil 900 with Dalby and Hamilton weather, results/apsim_vs_ghgsim_hestia_crop_AN_v1.csv) are kept unchanged as sensitivity cases. Consistency check, not validation.

D24.7 Drainage. Webster is poorly drained; no tile drainage or water table is modelled, which likely raises denitrification and N2O relative to a tiled field. Flagged for Alex (scope).

D24.8 Climate. Boone County is IPCC cool temperate moist; the stylized farm is warm temperate moist. Tier 1 EF1 depends only on wet/dry, so the IPCC comparator is unchanged.

D24.9 Review fixes (docs/REVIEW_v14_AN_v1.md): Table 1 moved to Supplementary Table S9 so display items = 6; APSIM/GLEAM/HESTIA paragraphs moved to a Results subsection after the inventories so figures are cited in order; main text trimmed to <= 3,000 words; stale commit, decision-log range and stylized-table provenance corrected; three references added (SSURGO, NASA POWER, NASS Handbook 628); placeholder author statements added and flagged. Reverse: use PaperB_draft_AN_v14.docx.