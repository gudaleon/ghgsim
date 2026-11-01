"""Versioned IPCC parameter tables with provenance. UNVERIFIED rows are excluded unless allow_unverified=True."""
from importlib.resources import files
import pandas as pd

GUIDELINES = ("IPCC2006", "IPCC2019")

class ParamTable:
    def __init__(self, path=None):
        path = path or files("livingghg") / "data" / "ipcc_params_AN_v2.csv"
        self.df = pd.read_csv(path)

    def get(self, guideline, factor, disagg="all", field="default", allow_unverified=False):
        d = self.df
        rows = d[(d.factor == factor) & (d.disaggregation == disagg) & d.guideline.isin([guideline, "BOTH"])]
        if rows.empty:
            raise KeyError(f"{guideline}/{factor}/{disagg} not in table")
        r = rows.iloc[0]
        if r.status != "VERIFIED" and not allow_unverified:
            raise ValueError(f"{factor}/{disagg} is {r.status}; excluded from default runs")
        return float(r[field])

    def unverified(self):
        return self.df[self.df.status != "VERIFIED"]
