"""Build PaperB_draft_AN_v17 and PaperB_SI_AN_v10 from v16 / SI v9 (new files only; refuses to overwrite)."""
import os, sys, docx
from docx.shared import Inches
D = r"G:\My Drive\Papers_To_Publish\PaperB"
SRC_M, SRC_S = os.path.join(D, "PaperB_draft_AN_v16.docx"), os.path.join(D, "PaperB_SI_AN_v9.docx")
OUT_M, OUT_S = os.path.join(D, "PaperB_draft_AN_v17.docx"), os.path.join(D, "PaperB_SI_AN_v10.docx")
FIG = r"D:\ghgsim\docs\figures"
for o in (OUT_M, OUT_S):
    if os.path.exists(o): sys.exit("refusing to overwrite " + o)

M_METHODS = [
("Heading 3", "APSIM Lake Erie runs and SSURGO till boundary"),
("First Paragraph", "Three Lake Erie basin soils were run in APSIM Next Generation (same build as the Iowa runs [41,42]) with the SWIM3 soil water module [55]: Hoytville (Ohio), Berrien (Michigan) and Brookston (Ontario), maize-soybean rotation, 172 or 0 kg N/ha, NASA POWER weather 1991-2020 [44]. Below the 2 m profile, SWIM's gradient lower boundary sets the base flux to q = (1+gr)K, and gr was computed from SSURGO saturated conductivity [43] as gr = K_restrictive/K_layer - 1 (Hoytville Cd horizon 0.005 um/s over BC 0.92 um/s, gr = -0.99457). Brookston, whose CanSIS profile gave an unstable SWIM conductivity curve, used the nearest SSURGO densic-till analogue (Michigan survey area MI155, mukey 2393950, gr = -0.990909) as a stated proxy. Tile drains used the 1956 and 2-rod (about 10 m) spacings. Undrained runs that fail in SWIM are reported as failures, not replaced; drained and undrained cases are compared only over the matched period both completed. Brookston was also run with the cascading SoilWater module (no drains) {scripts/run_apsim_lake_erie_AN_v3.py; scripts/matched_lake_erie_AN_v3.py; scripts/run_apsim_brookston_ssurgo_AN_v1.py; scripts/run_apsim_brookston_soilwater_AN_v1.py; scripts/run_apsim_webster_drains_AN_v1.py; results/apsim_lake_erie_AN_v3/; results/apsim_brookston_ssurgo_AN_v1/}."),
("Body Text", "At the Iowa site, the 2 m seepage boundary produced no water table, so a till boundary was tested: weathered (fractured) till from Iowa pumping tests [56,57] and unfractured till at the typical till conductivity of 1e-9 m/s [59], the latter a lower-bound case because till below 2 m at the site is oxidised and fractured [57]. No intermediate till value was used, because none is cited. Ontario census units (32) were sown on the start dates of OMAFRA Publication 811 [60] with the APSIM MinESW sowing rule switched off; sensitivity to spreading potential evaporation over 24 h instead of 12 h (eo_durn) was run because it changed N2O by 14-16%. Soil parameters were not tuned."),
("Heading 3", "Pulse and averaging analysis"),
("First Paragraph", "Daily APSIM N2O for 95 US counties and 32 Ontario units was split into rain-triggered pulses (a day with 5, 10 or 20 mm rain plus the next 3 days) and the remainder, and annual totals from APSIM were set against totals from annual-factor methods applied to the same inputs: IPCC 2006 and 2019 Tier 1 factors and the Holos-style precipitation equation below. Agreement is reported as total relative error, Spearman rank correlation of totals, and the ratio of interannual standard deviations. Uncertainty is a county bootstrap (2,000 resamples, seed 20261104) {scripts/analyse_pulses_distortion_AN_v2.py; scripts/run_apsim_county_AN_v3.py}. These are consistency checks between models, not validation against measured fluxes."),
("Heading 3", "Holos CLI runs"),
("First Paragraph", "The Holos command-line interface (github.com/holos-aafc/Holos, commit c7683f71; source read, not copied) was run for Hoytville, Berrien, Parkhill and Brookston with a configuration-only fix so the farm files bind {scripts/holos_vs_apsim_lake_erie_AN_v4.py}. Its base factor is EF = exp(0.00558P - 7.701), with P the May-October precipitation [58], scaled by a texture factor (2.55 fine, 1 medium, 0.49 coarse) and topography and tillage terms. For the pulse analysis a Holos-style factor was computed from the same equation; the precipitation-over-evapotranspiration branch (holos_pe) was evaluated with the low-lying fraction set to 1 as an upper bound. Holos has no drainage term and no carry-over between crop years, so differences with APSIM are read as differences in structure."),
]
M_RESULTS = [
("Heading 3", "Drainage and soybean-year carry-over at Lake Erie sites"),
("First Paragraph", "With the SSURGO till boundary, drained Hoytville carried 71-98 mm/yr of tile flow and emitted 4.36-4.91 kg N2O-N/ha/yr at 172 kg N (1.64-1.82 at 0 N) (Supplementary Table S11). Over the short periods the undrained runs completed, drainage lowered N2O by 28-37% with fertiliser but raised it by 13-17% at 0 N; the records are short and the sign at 0 N is a caveat. Berrien drains carried almost no water. On the Brookston densic proxy, the emission factor was 3.20-3.30% (1.84-1.93% counting maize years only), soybean years carried 42% of fertiliser-induced N2O, and drainage lowered N2O by about 7-8% over the matched period; with SoilWater and no drains the factor was 0.97% (Supplementary Tables S12-S13). At the Iowa site, weathered till produced no water table, and unfractured till gave a drained factor of 1.47% (Supplementary Table S14). Undrained runs failed in SWIM at every site, a model limitation."),
("Heading 3", "Holos CLI versus APSIM"),
("First Paragraph", "Holos CLI factors were 3.01% at Hoytville, 0.37% at Berrien and Parkhill and 1.93% at Brookston, against APSIM 3.15-3.81%, 2.26-2.35% and 0.97% (Supplementary Table S15). Texture explained most of the Holos spread (fine/coarse ratio 5.2), climate came second (x1.56 and x0.64), topography changed factors by x0.84-1.30 and tillage by about 5%. The largest gaps, coarse Berrien and Brookston, fall where APSIM's drainage and soybean-year carry-over act and Holos has no matching term. These are consistency checks between two models."),
("Heading 3", "Rain pulses and distortion from annual factors"),
("First Paragraph", "In the US counties, the 3-day windows after 10 mm rain carried 55% of APSIM N2O on 16% of days; the share held at 5 and 20 mm thresholds (Supplementary Table S16, Supplementary Figs. S1-S3). Against APSIM totals, IPCC 2006 was -7% (Spearman 0.28), IPCC 2019 -45% (0.24) and the Holos-style factor +23% (0.46), and the Holos-style factor doubled interannual variability (SD ratio 2.08) (Supplementary Table S17, Supplementary Figs. S4-S6). In Ontario the Holos-style total was +6% (Spearman 0.60), and sowing on Publication 811 dates gave an APSIM factor of 0.52% against a Holos-style 0.52% (Spearman 0.63). The precipitation-over-evapotranspiration branch at its upper bound overestimated totals by 232% (US) and 172% (Ontario). Annual factors therefore match totals in some places while missing the year-to-year and county ranking that pulses drive."),
]
M_REFS = [
"Huth, N. I., Bristow, K. L. & Verburg, K. SWIM3: model use, calibration, and validation. Trans. ASABE 55, 1303-1313 (2012). https://doi.org/10.13031/2013.42243",
"Jones, L., Lemar, T. & Tsai, C.-T. Results of two pumping tests in Wisconsin age weathered till in Iowa. Groundwater 30, 529-538 (1992). https://doi.org/10.1111/j.1745-6584.1992.tb01529.x",
"Young, N. L., Simpkins, W. W., Reber, J. J. & Helmke, M. F. Estimation of the representative elementary volume of a fractured till: a field and groundwater modeling approach. Hydrogeol. J. 28, 781-793 (2020). https://doi.org/10.1007/s10040-019-02076-y",
"Rochette, P. et al. Soil nitrous oxide emissions from agricultural soils in Canada: exploring relationships with soil, crop and climatic variables. Agric. Ecosyst. Environ. 254, 69-81 (2018). https://doi.org/10.1016/j.agee.2017.10.021",
"Minnesota Pollution Control Agency. Aquifer hydraulic properties. Minnesota Stormwater Manual. https://stormwater.pca.state.mn.us/aquifer_hydraulic_properties (accessed 4 November 2026).",
"Ontario Ministry of Agriculture, Food and Agribusiness. Publication 811: Agronomy Guide for Field Crops. https://www.ontario.ca/page/agronomy-guide-field-crops (accessed 4 November 2026).",
"Agriculture and Agri-Food Canada. Canadian Soil Information Service (CanSIS). https://sis.agr.gc.ca/cansis/ (accessed 4 November 2026).",
]

def ins_before(anchor, items):
    for st, tx in items:
        anchor.insert_paragraph_before(tx, style=st)

m = docx.Document(SRC_M); P = m.paragraphs
title, abstract = P[0].text, P[5].text
assert P[26].text.strip().startswith("Discussion") and P[49].text.strip().startswith("Data availability"), (P[26].text, P[49].text)
refs_last = P[125]
datap = P[50]
ins_before(P[49], M_METHODS)
ins_before(P[26], M_RESULTS)
datap.add_run(" Lake Erie soils: SSURGO [43] and CanSIS [61]; Ontario planting dates: OMAFRA Publication 811 [60]; Holos CLI: commit c7683f71.")
a = refs_last
for r in M_REFS:
    np_ = docx.oxml.OxmlElement("w:p"); a._p.addnext(np_)
    from docx.text.paragraph import Paragraph
    a = Paragraph(np_, a._parent); a.style = refs_last.style; a.add_run(r)
assert m.paragraphs[0].text == title and abstract in [p.text for p in m.paragraphs[:12]]
m.save(OUT_M)

s = docx.Document(SRC_S); tstyle = s.tables[-1].style
def H(t): s.add_paragraph(t, style="Heading 2")
def T(t): s.add_paragraph(t, style="First Paragraph")
def C(t): s.add_paragraph(t, style="Body Text")
def TAB(rows):
    t = s.add_table(rows=len(rows), cols=len(rows[0])); t.style = tstyle
    for i, r in enumerate(rows):
        for j, v in enumerate(r): t.cell(i, j).text = str(v)
def FIGP(n, f, cap):
    s.add_picture(os.path.join(FIG, f), width=Inches(6)); C(f"Supplementary Fig. S{n} | {cap}")
H("S11. APSIM Lake Erie runs with the SSURGO till boundary")
T("Methods are in the main-text Methods. SWIM3 gradient lower boundary q = (1+gr)K with gr from SSURGO Ksat; no parameter tuned. Comparisons are consistency checks, not validation {results/apsim_lake_erie_AN_v3/; results/apsim_brookston_ssurgo_AN_v1/}.")
C("Supplementary Table S11 | Hoytville drained, SWIM3 with SSURGO till boundary (gr = -0.99457), 1991-2020.")
TAB([["Drain case","N2O-N 172 kg N (kg/ha/yr)","N2O-N 0 N (kg/ha/yr)","Tile flow (mm/yr)"],["tile_1956","4.36","1.64","97.6"],["tile_lt","4.91","1.82","70.7"]])
T("Undrained Hoytville failed in SWIM. Over the matched periods the undrained runs completed, drainage lowered N2O by 28-37% at 172 kg N and raised it by 13-17% at 0 N (short records). Berrien drains carried almost no water. eo_durn 24 h instead of 12 h: N2O +14-16%.")
C("Supplementary Table S12 | Brookston on the SSURGO densic proxy (MI155, mukey 2393950, gr = -0.990909).")
TAB([["Drain case","EF (%)","Maize-year-only EF (%)","Soybean-year share","Tile flow (mm/yr)"],["tile_1956","3.30","1.93","0.42","46"],["tile_2rod","3.20","1.84","0.42","54"]])
T("Undrained run failed on 9 December 1992; over the matched period drainage lowered N2O by about 7-8%. The CanSIS Brookston profile gave an unstable SWIM conductivity curve, hence the proxy.")
C("Supplementary Table S13 | Brookston with the SoilWater module (no drains).")
TAB([["Quantity","Value"],["EF (%)","0.97"],["Soybean-year share","0.30"],["Drainage (mm/yr)","231"]])
C("Supplementary Table S14 | Iowa (Webster) till boundary cases.")
TAB([["Till case","Source","Result"],["Weathered (fractured) till","Pumping tests [Jones et al. 1992; Young et al. 2020]","No water table forms"],["Unfractured till, Ksat 1e-9 m/s","Minnesota Stormwater Manual (lower bound)","Drained EF 1.47%"],["Undrained","-","Not run (SWIM undrained runs fail; no cited intermediate till value)"]])
H("S12. Holos CLI versus APSIM")
C("Supplementary Table S15 | Fertiliser-induced N2O emission factor (%), Holos CLI (commit c7683f71) and APSIM.")
TAB([["Site","Holos CLI EF (%)","APSIM EF (%)"],["Hoytville","3.008","3.15-3.81"],["Berrien","0.370","2.26-2.35"],["Parkhill","0.370","-"],["Brookston","1.925","0.97 (SoilWater); 3.20-3.30 (SWIM proxy)"]])
T("Holos factor decomposition: texture fine/coarse 5.2x; climate x1.56 and x0.64; topography x0.84-1.30; tillage about 5%. Holos has no drainage term and no soybean-year carry-over. Base equation: Rochette et al. 2018.")
H("S13. Rain pulses and annual-factor distortion")
C("Supplementary Table S16 | Share of APSIM N2O in the 3 days after rain, US counties (n = 95), 10 mm threshold (5 and 20 mm in Supplementary Figs. S2-S3).")
TAB([["Quantity","Value"],["N2O share in pulse windows","0.55"],["Share of days in pulse windows","0.16"]])
C("Supplementary Table S17 | Annual-factor totals against APSIM (bootstrap over counties, 2,000 resamples, seed 20261104).")
TAB([["Region","Method","Total error vs APSIM","Spearman of totals"],["US (95)","IPCC 2006","-7%","0.28"],["US (95)","IPCC 2019","-45%","0.24"],["US (95)","Holos-style","+23%","0.46"],["US (95)","holos_pe (f_lower = 1, bound)","+232%","-"],["Ontario (32)","Holos-style","+6%","0.60"],["Ontario (32)","holos_pe (f_lower = 1, bound)","+172%","-"]])
T("Interannual SD ratio, Holos-style vs APSIM (US): 2.08. Ontario with Publication 811 dates: APSIM EF 0.52%, Holos-style 0.52%, Spearman 0.63.")
FIGP(1, "pulse_share_by_group_AN_v1.png", "Pulse share of APSIM N2O by group, 10 mm threshold.")
FIGP(2, "pulse_share_by_group_thr5_AN_v1.png", "As Fig. S1, 5 mm threshold.")
FIGP(3, "pulse_share_by_group_thr20_AN_v1.png", "As Fig. S1, 20 mm threshold.")
FIGP(4, "county_distribution_by_method_AN_v1.png", "County totals by method against APSIM.")
FIGP(5, "hotspot_rank_apsim_vs_methods_AN_v1.png", "County ranks, APSIM against annual-factor methods.")
FIGP(6, "interannual_sd_apsim_vs_holos_AN_v1.png", "Interannual standard deviation, APSIM against Holos-style.")
H("S14. Changelog, v16 to v17 (SI v9 to v10)")
for c in ["Methods: added APSIM Lake Erie runs and SSURGO till boundary; pulse and averaging analysis; Holos CLI runs.",
          "Results: added three subsections from FINDINGS_AN_v4-v9 (drainage and carry-over; Holos CLI vs APSIM; pulses and distortion).",
          "Data availability: added SSURGO, CanSIS, OMAFRA Pub. 811 and Holos commit.",
          "References 55-61 added, each checked by DOI (Crossref) or by opening the URL on 4 November 2026.",
          "SI: new S11-S14, Supplementary Tables S11-S17 and Supplementary Figs. S1-S6. Title, abstract and existing text unchanged; nothing trimmed."]:
    T(c)
s.save(OUT_S)
print("ok")