"""Fill USDA NASS Census county cow inventories withheld as (D).

Fork F011 `withheld_fill`:
  "sizeclass"     (default) state residual R = state total - disclosed counties, allocated to withheld
                  counties in proportion to a size-class estimate e_w = sum_c [inv_c if disclosed else
                  ops_c * m_c], with m_c the state class mean head/operation (else class midpoint; open
                  top class 1.5 x lower bound = ASSUMPTION). Constrained: fills sum exactly to R.
  "prior_census"  USGS approach (Falcone 2021, OFR 2020-1153; Falcone & LaMotte 2016): use the county's most
                  recent disclosed value from earlier censuses (2017, 2012, ... up to 6 periods); else NaN.
                  Not constrained to the state total.
  "none"          leave withheld counties as NaN (treated as 0 head).
Every filled value carries `fill_method` and `fill_provenance`."""
import re
import numpy as np, pandas as pd

SRC22 = "USDA NASS 2022 Census of Agriculture (Quick Stats bulk qs.census2022.txt.gz)"
ANIMALS = {"milk": "MILK", "beef": "BEEF"}

def _num(s):
    return pd.to_numeric(s.astype(str).str.replace(",", "").str.strip(), errors="coerce")

def class_range(label):
    m = re.search(r"\(([\d,]+) (?:TO ([\d,]+)|OR MORE) HEAD\)", label or "")
    if not m:
        return None
    lo = float(m.group(1).replace(",", ""))
    hi = float(m.group(2).replace(",", "")) if m.group(2) else np.inf
    return lo, hi

def finest_classes(labels):
    """Drop classes that contain another listed class (e.g. '500 OR MORE' when '500 TO 999' exists)."""
    rs = {l: class_range(l) for l in labels if class_range(l)}
    return [l for l, (lo, hi) in rs.items()
            if not any(o != l and lo <= r[0] and r[1] <= hi and r != (lo, hi) for o, r in rs.items())]

def class_midpoint(lo, hi):
    return 1.5 * lo if np.isinf(hi) else (lo + hi) / 2.0

def prepare(sizeclass_df):
    d = sizeclass_df.copy()
    d["v"] = _num(d.VALUE)
    d["animal"] = np.where(d.SHORT_DESC.str.contains("MILK"), "milk", "beef")
    d["kind"] = np.where(d.SHORT_DESC.str.contains("OPERATIONS"), "ops", "inv")
    d["fips"] = d.STATE_FIPS_CODE.astype(str).str.zfill(2) + d.COUNTY_CODE.fillna("").astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(3)
    return d

def fill_state_sizeclass(d, st, an, mask=frozenset()):
    """Returns (filled DataFrame for withheld counties, disclosed inventory Series) or None."""
    s = d[(d.STATE_ALPHA == st) & (d.animal == an)]
    tot = s[(s.AGG_LEVEL_DESC == "STATE") & (s.DOMAIN_DESC == "TOTAL") & (s.kind == "inv")].v
    if tot.empty or pd.isna(tot.iloc[0]):
        return None
    tot = float(tot.iloc[0])
    sc = s[(s.AGG_LEVEL_DESC == "STATE") & (s.DOMAIN_DESC != "TOTAL")].pivot_table(
        index="DOMAINCAT_DESC", columns="kind", values="v", aggfunc="first").reindex(columns=["inv", "ops"])
    c = s[s.AGG_LEVEL_DESC == "COUNTY"]
    ct = c[c.DOMAIN_DESC == "TOTAL"].pivot_table(index="fips", columns="kind", values="v", aggfunc="first", dropna=False).reindex(columns=["inv", "ops"])
    names = c.drop_duplicates("fips").set_index("fips").COUNTY_NAME
    inv = ct.inv.copy()
    inv[[m for m in mask if m in inv.index]] = np.nan
    withheld = list(inv[inv.isna()].index)
    R = tot - inv.dropna().sum()
    cls = c[c.DOMAIN_DESC != "TOTAL"]
    est, meth = {}, {}
    for f in withheld:
        cc = cls[cls.fips == f].pivot_table(index="DOMAINCAT_DESC", columns="kind", values="v", aggfunc="first").reindex(columns=["inv", "ops"])
        if cc.ops.notna().any():
            e, used = 0.0, set()
            for lab in finest_classes(list(cc.index)):
                ops, iv = cc.ops.get(lab), (np.nan if f in mask else cc.inv.get(lab))
                if pd.notna(iv):
                    e += iv; used.add("disclosed_class")
                elif pd.notna(ops):
                    if lab in sc.index and pd.notna(sc.inv.get(lab)) and (sc.ops.get(lab) or 0) > 0:
                        e += ops * sc.inv[lab] / sc.ops[lab]; used.add("state_class_mean")
                    else:
                        e += ops * class_midpoint(*class_range(lab)); used.add("class_midpoint")
            est[f], meth[f] = e, "sizeclass[" + ",".join(sorted(used)) + "]"
        else:
            est[f], meth[f] = np.nan, ("ops_x_mean" if pd.notna(ct.ops.get(f)) else "no_ops_data")
    known = {k: v for k, v in est.items() if pd.notna(v)}
    pool_ops = sum((ct.ops.get(k) or 0) for k in known)
    mean_op = (sum(known.values()) / pool_ops) if pool_ops else (tot / ct.ops.sum() if ct.ops.sum() else np.nan)
    for f in est:
        if pd.isna(est[f]) and pd.notna(ct.ops.get(f)):
            est[f] = ct.ops[f] * mean_op
    S = sum(v for v in est.values() if pd.notna(v))
    k = R / S if S > 0 else np.nan
    rows = [{"STATE_ALPHA": st, "fips": f, "COUNTY_NAME": names.get(f), "animal": an, "ops": ct.ops.get(f),
             "raw_estimate": e, "filled_head": (max(e * k, 0.0) if pd.notna(e) and pd.notna(k) else np.nan),
             "scale_to_state": k, "fill_method": "F011:sizeclass/" + meth[f], "flag": "FILLED_ESTIMATE",
             "fill_provenance": SRC22 + "; state-residual allocation (livingghg.gapfill)"} for f, e in est.items()]
    return pd.DataFrame(rows), inv.dropna()

def fill_all_sizeclass(d):
    out = []
    for st in sorted(d[d.AGG_LEVEL_DESC == "STATE"].STATE_ALPHA.unique()):
        for an in ANIMALS:
            r = fill_state_sizeclass(d, st, an)
            if r is not None and len(r[0]):
                out.append(r[0])
    return pd.concat(out, ignore_index=True)

def fill_prior_census(withheld, prior_df, max_periods=6):
    """withheld: DataFrame with fips, animal. prior_df: NASS county rows (YEAR, ..., SHORT_DESC, VALUE) for earlier censuses."""
    p = prior_df.copy()
    p = p[p.AGG_LEVEL_DESC == "COUNTY"]
    p["v"] = _num(p.VALUE)
    p["animal"] = np.where(p.SHORT_DESC.str.contains("MILK"), "milk", "beef")
    p["fips"] = p.STATE_FIPS_CODE.astype(str).str.zfill(2) + p.COUNTY_CODE.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(3)
    p["YEAR"] = p.YEAR.astype(int)
    years = sorted(p.YEAR.unique(), reverse=True)[:max_periods]
    look = {(r.fips, r.animal, r.YEAR): r.v for r in p.itertuples() if pd.notna(r.v)}
    vals, meth = [], []
    for r in withheld.itertuples():
        hit = next(((look[(r.fips, r.animal, y)], y) for y in years if (r.fips, r.animal, y) in look), None)
        vals.append(hit[0] if hit else np.nan)
        meth.append(f"F011:prior_census/{hit[1]}" if hit else "F011:prior_census/none_found")
    o = withheld[["STATE_ALPHA", "fips", "COUNTY_NAME", "animal"]].copy()
    o["filled_head"], o["fill_method"], o["flag"] = vals, meth, "FILLED_ESTIMATE"
    o["fill_provenance"] = "USDA NASS Census of Agriculture " + ",".join(map(str, years)) + " (Quick Stats bulk files); method of Falcone (2021) USGS OFR 2020-1153"
    return o

def validate_sizeclass(d, frac=0.2, seed=1, min_disclosed=5):
    """Mask a fraction of disclosed counties (and their class inventories), refill, compare."""
    rs = np.random.default_rng(seed); recs = []
    for st in sorted(d[d.AGG_LEVEL_DESC == "STATE"].STATE_ALPHA.unique()):
        for an in ANIMALS:
            base = fill_state_sizeclass(d, st, an)
            if base is None:
                continue
            disc = base[1]; disc = disc[disc > 0]
            if len(disc) < min_disclosed:
                continue
            m = frozenset(rs.choice(disc.index, max(1, int(frac * len(disc))), replace=False))
            r, _ = fill_state_sizeclass(d, st, an, m)
            r = r[r.fips.isin(m)].copy(); r["true"] = r.fips.map(disc)
            recs.append(r)
    v = pd.concat(recs, ignore_index=True)
    out = {}
    for an, g in v.groupby("animal"):
        e = (g.filled_head - g.true)
        out[an] = {"n": int(len(g)), "median_abs_pct_err": float(np.nanmedian(np.abs(e / g.true)) * 100),
                   "head_weighted_abs_pct_err": float(e.abs().sum() / g.true.sum() * 100)}
    return v, out
