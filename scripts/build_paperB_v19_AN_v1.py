"""Build PaperB_draft_AN_v19 (from v18) and PaperB_SI_AN_v11 (from SI v10) as new files; refuses to overwrite.
Adds the soybean carry-over caveat (FINDINGS_AN_v10, DECISIONS D27) and LITCHECK_AN_v1 caveats."""
import os, sys, json, copy, docx
from docx.text.paragraph import Paragraph
D = r"G:\My Drive\Papers_To_Publish\PaperB"
SM, SS = os.path.join(D, "PaperB_draft_AN_v18.docx"), os.path.join(D, "PaperB_SI_AN_v10.docx")
OM, OS_ = os.path.join(D, "PaperB_draft_AN_v19.docx"), os.path.join(D, "PaperB_SI_AN_v11.docx")
for o in (OM, OS_):
    if os.path.exists(o): sys.exit("refusing to overwrite " + o)
def after(p, text, style=None):
    n = docx.oxml.OxmlElement("w:p"); p._p.addnext(n); q = Paragraph(n, p._parent)
    q.style = style or p.style; q.add_run(text); return q
def one(doc, key):
    h = [p for p in doc.paragraphs if key in p.text]; assert len(h) == 1, (key, len(h)); return h[0]

m = docx.Document(SM); title = m.paragraphs[0].text; abstract = [p.text for p in m.paragraphs[:9]]
one(m, "soybean years carried 42% of fertiliser-induced N2O").add_run(
 " The soybean-year share is a model result that field data contradict: the previous corn's N had no effect on soybean-phase N2O in Minnesota [62],"
 " and Iowa soybean years emitted 2.2-2.7 against 7.6-10.2 kg N2O-N/ha/yr in corn years [63]. In APSIM, 72-85% of the extra soybean-year N2O falls in"
 " January-April, before sowing, as residual nitrate from the fertilised maize is denitrified; only 5-11% of fertiliser-induced N2O falls in the soybean"
 " growing season (Supplementary Section S15). The 13-17% increase with drainage at 0 N comes from short, partly failed SWIM records, and no field study"
 " we found reports it, so we flag it as a possible artifact; in the field, drainage lowered N2O only in wet periods (undrained soil emitted 1.8 times"
 " more than drained [64]).")
one(m, "Texture explained most of the Holos spread").add_run(
 " Field data show texture effects that are real but continuous and season-dependent [65], so the step at a class boundary reflects the method rather than the soils.")
one(m, "carried 55% of APSIM N2O on 16% of days").add_run(
 " Field eddy-covariance records show a similar concentration (peak events up to 51% of annual N2O in under 7% of the time [66]), but also large"
 " freeze-thaw emissions (30-90% of annual in Ontario [67]) that a rain-triggered definition does not capture, so the pulse shares are a lower bound on episodic emission.")
REFS = [
 "Fabrizzi, K. P., Fernández, F. G., Venterea, R. T. & Naeve, S. L. Nitrous oxide emissions from soybean in response to drained and undrained soils and previous corn nitrogen management. J. Environ. Qual. 53, 407-417 (2024). https://doi.org/10.1002/jeq2.20566",
 "Parkin, T. B. & Kaspar, T. C. Nitrous oxide emissions from corn-soybean systems in the Midwest. J. Environ. Qual. 35, 1496-1506 (2006). https://doi.org/10.2134/jeq2005.0183",
 "Fernández, F. G., Venterea, R. T. & Fabrizzi, K. P. Corn nitrogen management influences nitrous oxide emissions in drained and undrained soils. J. Environ. Qual. 45, 1847-1855 (2016). https://doi.org/10.2134/jeq2016.06.0237",
 "Skiba, U. & Ball, B. C. The effect of soil texture and soil drainage on emissions of nitric oxide and nitrous oxide. Soil Use Manage. 18, 56-60 (2002). https://doi.org/10.1111/j.1475-2743.2002.tb00050.x",
 "Molodovskaya, M. et al. Temporal variability of nitrous oxide from fertilized croplands: hot moment analysis. Soil Sci. Soc. Am. J. 76, 1728-1740 (2012). https://doi.org/10.2136/sssaj2012.0039",
 "Wagner-Riddle, C. et al. Intensive measurement of nitrous oxide emissions from a corn-soybean-wheat rotation under two contrasting management systems over 5 years. Glob. Change Biol. 13, 1722-1736 (2007). https://doi.org/10.1111/j.1365-2486.2007.01388.x",
]
a = one(m, "Canadian Soil Information Service")
for r in REFS: a = after(a, r)
assert m.paragraphs[0].text == title and [p.text for p in m.paragraphs[:9]] == abstract
m.save(OM)

s = docx.Document(SS)
one(s, "Supplementary Table S12 | Brookston").add_run(" Caveat: the soybean-year share is a model result that field data contradict (see reading and Section S15).")
after(one(s, "Undrained run failed on 9 December 1992"),
 "Caveat: field studies found no effect of the previous corn's N on soybean-phase N2O (Fabrizzi et al. 2024, doi:10.1002/jeq2.20566) and soybean-year"
 " emissions well below corn years (Parkin & Kaspar 2006, doi:10.2134/jeq2005.0183). In APSIM, 72-73% of the extra soybean-year N2O at Brookston falls in"
 " January-April, before sowing (Section S15), so the share largely reflects the calendar-year boundary and residual nitrate, not the soybean crop.")
J = json.load(open(r"D:\ghgsim\results\soy_carryover_AN_v1\soy_carryover_summary_AN_v1.json"))
tstyle = s.tables[-1].style
s.add_paragraph("S15. Diagnosis of soybean-year N2O carry-over in APSIM", style="Heading 2")
s.add_paragraph("Existing daily APSIM outputs, 172 N minus 0 N, 1991-2020 (15 soybean years per case); maize odd and soybean even calendar years. APSIM does not tag N2O"
 " by source pool, so pools are attributed by their differences and daily correlation with the N2O difference; soybean N fixation is not output and soybean N is a proxy"
 " {scripts/diagnose_soy_carryover_AN_v1.py; results/soy_carryover_AN_v1/; docs/FINDINGS_AN_v10.md}. Model result contradicted by field data (DECISIONS D27.1).", style="First Paragraph")
s.add_paragraph("Supplementary Table S18 | Extra soybean-year N2O by season and N-pool indicators (kg N/ha unless stated).", style="Body Text")
cols = [("Extra N2O, soybean yr", "dN2O_soy_kgha_yr"), ("Jan-Apr", "dN2O_soy_JanApr"), ("Thaw days", "dN2O_soy_thaw_days"), ("May-Sep", "dN2O_soy_MaySep"),
        ("Oct-Dec", "dN2O_soy_OctDec"), ("dNO3 1 Jan", "dNO3_Jan1_kgha"), ("dNO3 at sowing", "dNO3_soy_sowing_May11_kgha"), ("d net mineralisation", "dMinN_soy_kgha_yr"),
        ("dN2", "dN2_soy_kgha_yr"), ("d soybean N", "dSoyN_max_kgha"), ("r(dN2O,dNO3)", "corr_daily_dN2O_dNO3_soy")]
t = s.add_table(rows=len(J) + 1, cols=len(cols) + 1); t.style = tstyle
t.cell(0, 0).text = "Case"
for j, (h, _) in enumerate(cols): t.cell(0, j + 1).text = h
for i, (case, v) in enumerate(J.items()):
    t.cell(i + 1, 0).text = case
    for j, (_, k) in enumerate(cols): t.cell(i + 1, j + 1).text = str(v[k])
s.add_paragraph("Reading: 72-85% of the extra soybean-year N2O falls in January-April, before soybean sowing, and tracks residual nitrate (r 0.56-0.67), with extra N2"
 " losses of 13-18 kg/ha; mineralisation is a secondary source for the May-June tail and soybean N barely differs. Only 5-11% of fertiliser-induced N2O falls in the"
 " soybean growing season, the window field soybean-phase studies measure.", style="First Paragraph")
s.add_paragraph("S16. Changelog, v18 to v19 (SI v10 to v11)", style="Heading 2")
for c in ["Results (drainage subsection): soybean-year share caveated as a model result contradicted by field data [62,63]; APSIM diagnosis summarised; 0 N drainage increase flagged as a possible artifact [64].",
          "Results (Holos subsection): texture step noted as a method feature; field texture effects are continuous and season-dependent [65].",
          "Results (pulse subsection): pulse shares stated as a lower bound because freeze-thaw emission is missed [66,67].",
          "References 62-67 added, each verified by DOI on Crossref (LITCHECK_AN_v1).",
          "SI: Table S12 caption and reading caveated; new S15 with Supplementary Table S18 (FINDINGS_AN_v10); this changelog S16.",
          "Title, abstract, Methods and Discussion unchanged; nothing trimmed."]:
    s.add_paragraph(c, style="First Paragraph")
s.save(OS_); print("ok")