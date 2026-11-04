"""Build PaperB_draft_AN_v20 (from v19) and PaperB_SI_AN_v12 (from SI v11) as new files; refuses to overwrite.
Adds 'in 2003' to the Parkin & Kaspar comparison and updates carry-over text to the sowing-year result (FINDINGS_AN_v11)."""
import os, sys, json, docx
from docx.text.paragraph import Paragraph
D = r"G:\My Drive\Papers_To_Publish\PaperB"
SM, SS = os.path.join(D, "PaperB_draft_AN_v19.docx"), os.path.join(D, "PaperB_SI_AN_v11.docx")
OM, OS_ = os.path.join(D, "PaperB_draft_AN_v20.docx"), os.path.join(D, "PaperB_SI_AN_v12.docx")
for o in (OM, OS_):
    if os.path.exists(o): sys.exit("refusing to overwrite " + o)
def one(doc, key):
    h = [p for p in doc.paragraphs if key in p.text]; assert len(h) == 1, (key, len(h)); return h[0]
def rep(p, old, new):
    t = p.text; assert t.count(old) == 1, old; t = t.replace(old, new)
    for r in p.runs[1:]: r._r.getparent().remove(r._r)
    p.runs[0].text = t
def after(p, text, style=None):
    n = docx.oxml.OxmlElement("w:p"); p._p.addnext(n); q = Paragraph(n, p._parent); q.style = style or p.style; q.add_run(text); return q
m = docx.Document(SM); head = [p.text for p in m.paragraphs[:9]]
p = one(m, "soybean years carried 42% of fertiliser-induced N2O")
rep(p, "Iowa soybean years emitted 2.2-2.7 against 7.6-10.2 kg N2O-N/ha/yr in corn years [63]",
       "Iowa soybean years emitted 2.2-2.7 against 7.6-10.2 kg N2O-N/ha/yr in corn years in 2003 [63]")
rep(p, "soybean years carried 42% of fertiliser-induced N2O",
       "soybean years carried 42% of fertiliser-induced N2O counted by calendar year, but 19% counted from sowing to sowing")
rep(p, "growing season (Supplementary Section S15).",
       "growing season (Supplementary Section S15). Counted from sowing to sowing, the soybean share falls from 0.30-0.51 to 0.15-0.19 at all Lake Erie sites,"
       " with emission factors within 0.04 percentage points, so most of the calendar-year carry-over is the winter after the maize; the remaining share is"
       " still not seen in the field (Supplementary Section S17).")
assert [q.text for q in m.paragraphs[:9]] == head
m.save(OM)
s = docx.Document(SS)
c = one(s, "Supplementary Table S12 | Brookston")
rep(c, "(see reading and Section S15).", "(see reading and Sections S15 and S17); counted from sowing to sowing the share is 0.19 in both cases.")
r = one(s, "so the share largely reflects the calendar-year boundary")
rep(r, "not the soybean crop.", "not the soybean crop. Counted from sowing to sowing, the share is 0.186 (tile_1956) and 0.188 (tile_2rod), with EF 3.33% and 3.24% (Section S17).")
J = json.load(open(r"D:\ghgsim\results\sowing_year_AN_v2\sowing_year_summary_AN_v2.json")); ts = s.tables[-1].style
def table(rows):
    t = s.add_table(rows=len(rows), cols=len(rows[0])); t.style = ts
    for i, row in enumerate(rows):
        for j, v in enumerate(row): t.cell(i, j).text = str(v)
s.add_paragraph("S17. Soybean share and emission factors on sowing-to-sowing crop years", style="Heading 2")
s.add_paragraph("Crop years run from one crop's onset (first day with crop N > 0, a few days after sowing) to the next; crop years over 400 days are dropped;"
 " fertilised minus 0 N; existing daily outputs, no new runs {scripts/sowing_year_recompute_AN_v2.py; results/sowing_year_AN_v2/; docs/FINDINGS_AN_v11.md}."
 " Failed runs are skipped.", style="First Paragraph")
s.add_paragraph("Supplementary Table S19 | Lake Erie soybean share and EF, calendar vs sowing-to-sowing years.", style="Body Text")
rows = [["Case", "Soybean share, calendar", "Soybean share, sowing year", "EF %, calendar", "EF %, sowing year"]]
for k, v in J["sites"].items():
    if "sowing_year_soy_share" in v:
        rows.append([k.replace("_AN_v3", "").replace("_AN_v1", "").replace("lake_erie_", ""), v["calendar_soy_share"], v["sowing_year_soy_share"], v["calendar_EF_pct"], v["sowing_year_EF_pct"]])
table(rows)
s.add_paragraph("Supplementary Table S20 | County EFs (continuous maize, 100 vs 0 kg N/ha), calendar vs sowing-to-sowing years.", style="Body Text")
rows = [["Region", "n", "Mean EF %, calendar", "Mean EF %, sowing year", "Median change %", "Spearman", "Top-10% overlap", "Median SD ratio"]]
for k, v in J["counties"].items():
    rows.append(["US" if k == "US" else "Ontario", v["n"], v["mean_cal_EF_pct"], v["mean_sow_EF_pct"], v["median_rel_change_pct"], v["spearman_cal_vs_sow"], v["top10pct_overlap"], v["median_sd_ratio_sow_over_cal"]])
table(rows)
s.add_paragraph("Reading: the Lake Erie soybean share falls from 0.30-0.51 to 0.15-0.19 while EFs move by at most 0.04 percentage points; the remaining share is still"
 " not seen in field data. US n = 97 units listed, 95 with complete crop years. County rankings are robust (Spearman 0.92-0.93). Large unit-level changes arise only"
 " where crops were not sown every year (different year sets). Among units with complete sowing records the median change is -0.5% (US) and +10.5% (Ontario);"
 " the Ontario shift is unexplained and flagged.", style="First Paragraph")
s.add_paragraph("S18. Changelog, v19 to v20 (SI v11 to v12)", style="Heading 2")
for t in ["Results (drainage subsection): 'in 2003' added to the Parkin & Kaspar comparison [63].",
          "Results (drainage subsection): soybean share reported both ways (42% calendar, 19% sowing to sowing at Brookston); sowing-year result for all Lake Erie sites added (0.15-0.19; EFs within 0.04 points).",
          "SI: Table S12 caption and reading updated with sowing-year shares; new S17 with Supplementary Tables S19-S20 (FINDINGS_AN_v11); this changelog S18.",
          "Title, abstract, Methods and Discussion unchanged; nothing trimmed; no new references."]:
    s.add_paragraph(t, style="First Paragraph")
s.save(OS_); print("ok")