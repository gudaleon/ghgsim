"""Build PaperB_draft_AN_v18 from v17 (new file; refuses to overwrite). Updates the Discussion limitations paragraph to FINDINGS v4-v9."""
import os, sys, docx
D = r"G:\My Drive\Papers_To_Publish\PaperB"
SRC, OUT = os.path.join(D, "PaperB_draft_AN_v17.docx"), os.path.join(D, "PaperB_draft_AN_v18.docx")
if os.path.exists(OUT): sys.exit("refusing to overwrite " + OUT)
OLD = ("The APSIM runs cover two soils of one county, borrow crop and organic-matter parameters from an example soil, "
       "represent tile drainage only through a steady-state drain equation that carried no water here, and simulate direct "
       "soil N2O only (no NH3 volatilisation or indirect N2O), so its agreement with the IPCC factors validates neither.")
NEW = ("The APSIM runs cover two Iowa soils, three Lake Erie soils, 95 US counties and 32 Ontario units; the Iowa runs borrow "
       "crop and organic-matter parameters from an example soil, and all simulate direct soil N2O only (no NH3 volatilisation "
       "or indirect N2O), so their agreement with the IPCC factors validates neither. Tile drainage is represented only through "
       "a steady-state drain equation in SWIM [55]. At the Iowa site, a weathered-till lower boundary still formed no water "
       "table, and unfractured till gave a drained emission factor of about 1.47%, a lower bound because the till there is "
       "fractured [56,57,59]. Undrained runs fail in SWIM at the Iowa and Lake Erie sites, so drainage effects are reported "
       "only over matched periods and remain a model limitation.")
d = docx.Document(SRC)
hits = [p for p in d.paragraphs if OLD in p.text]
assert len(hits) == 1, len(hits)
p = hits[0]; t = p.text.replace(OLD, NEW)
for r in p.runs[1:]: r._r.getparent().remove(r._r)
p.runs[0].text = t
d.save(OUT); print("ok")