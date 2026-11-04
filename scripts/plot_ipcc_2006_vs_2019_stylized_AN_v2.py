"""Figure for data/ipcc_2006_vs_2019_stylized_AN_v2.csv (AN_v2).

Usage: python scripts/plot_ipcc_2006_vs_2019_stylized_AN_v2.py
Writes docs/figures/ipcc_2006_vs_2019_stylized_AN_v2.png. NaN cells are left blank.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "ipcc_2006_vs_2019_stylized_AN_v2.csv"
PNG = ROOT / "docs" / "figures" / "ipcc_2006_vs_2019_stylized_AN_v2.png"
SOURCES = ["enteric_CH4", "manure_CH4", "manure_N2O", "soil_N2O"]
COLORS = {"enteric_CH4": "#4c72b0", "manure_CH4": "#dd8452", "manure_N2O": "#55a868", "soil_N2O": "#c44e52"}


def main() -> None:
    df = pd.read_csv(CSV)
    farms = list(dict.fromkeys(df["farm_id"]))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 9), sharey=True)
    y = range(len(farms))
    for ax, col, title in ((ax1, "ipcc2006_tCO2e", "IPCC 2006"), (ax2, "ipcc2019_tCO2e", "IPCC 2019 Refinement")):
        left = [0.0] * len(farms)
        for src in SOURCES:
            vals = [df[(df.farm_id == f) & (df.source == src)][col].iloc[0] for f in farms]
            vals = [0.0 if pd.isna(v) else float(v) for v in vals]
            ax.barh(list(y), vals, left=left, color=COLORS[src], label=src.replace("_", " "))
            left = [a + b for a, b in zip(left, vals)]
        ax.set_title(title)
        ax.set_xlabel("t CO2e / yr (AR5 GWP100)")
    ax1.set_yticks(list(y))
    ax1.set_yticklabels(farms)
    ax1.invert_yaxis()
    ax2.legend(loc="lower right")
    fig.suptitle("Stylized farms: IPCC 2006 vs 2019 Tier 1/2 (ghgsim IPCC modules; beef liquid manure N2O not computable, shown as 0)")
    fig.tight_layout()
    PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(PNG, dpi=150)
    print(f"wrote {PNG}")


if __name__ == "__main__":
    main()
