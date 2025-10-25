# stats_dashboard.py
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import polars as pl

from stats_metrics import stats_metrics_for_display

__all__ = ["StatsDashboard", "StatsManifest"]


@dataclass
class StatsManifest:
    lags: Sequence[int] = tuple(range(0, 6))
    horizons: Sequence[int] = (1, 5, 10, 20)
    title: str = "Statistics — IC Diagnostics"
    output_dir: str = "output/stats_dashboard"


class StatsDashboard:
    """
    Lightweight, fast dashboard for prediction/target diagnostics:
      - IC/R²/t-stat grid by (lag, horizon) with sortable table
      - Heatmaps (IC, t) per model
      - Summary metrics table (IC_avg, IC_abs_max, t_abs_max, R2_avg, N_total)

    Compute: Polars-lazy
    Render: Pandas/Matplotlib only
    """

    def __init__(
        self,
        pred_target_lf: pl.LazyFrame,
        *,
        manifest: Optional[StatsManifest] = None,
        date_col: str = "date",
        name_col: str = "name",
        pred_col: str = "pred",
        target_col: str = "y",
    ) -> None:
        self.m = manifest or StatsManifest()
        self.date_col = date_col
        self.name_col = name_col
        self.pred_col = pred_col
        self.target_col = target_col
        os.makedirs(self.m.output_dir, exist_ok=True)

        # ---- compute core tables (lazy -> eager once)
        ic_df, summary_df = stats_metrics_for_display(
            pred_target_lf,
            lags=self.m.lags,
            horizons=self.m.horizons,
            date_col=self.date_col,
            name_col=self.name_col,
            pred_col=self.pred_col,
            target_col=self.target_col,
        )
        self.ic_long_pl = ic_df
        self.summary_pl = summary_df

        # Matplotlib figures
        self.fig_dir = os.path.join(self.m.output_dir, "figures")
        os.makedirs(self.fig_dir, exist_ok=True)

        self._build_figures()
        self._write_html()

    # ---------- helpers ----------
    def _save_fig(self, fig, fname: str) -> Optional[str]:
        try:
            path = os.path.join(self.fig_dir, fname)
            fig.savefig(path, dpi=144, bbox_inches="tight")
            plt.close(fig)
            return path
        except Exception:
            return None

    # ---------- figures ----------
    def _heatmap(self, Z: np.ndarray, xticks: List[int], yticks: List[int], title: str):
        fig = plt.figure(figsize=(6.2, 4.4))
        ax = fig.add_subplot(111)
        im = ax.imshow(Z, aspect="auto")
        ax.set_xticks(range(len(xticks)), [str(x) for x in xticks])
        ax.set_yticks(range(len(yticks)), [str(y) for y in yticks])
        ax.set_xlabel("Horizon")
        ax.set_ylabel("Lag")
        ax.set_title(title)
        cbar = fig.colorbar(im, ax=ax, shrink=0.85)
        return fig

    def _ic_line(self, x: List[int], y: List[float], title: str):
        fig = plt.figure(figsize=(6.2, 3.2))
        ax = fig.add_subplot(111)
        ax.plot(x, y, marker="o")
        ax.set_xlabel("Lag")
        ax.set_ylabel("IC")
        ax.set_title(title)
        return fig

    def _build_figures(self) -> None:
        self.fig_paths: Dict[str, Dict[str, str]] = {}
        pdf = self.ic_long_pl.to_pandas()
        if pdf.empty:
            return
        names = list(pd.Series(pdf["name"]).dropna().unique())

        L = list(self.m.lags)
        H = list(self.m.horizons)

        for name in names:
            sub = pdf[pdf["name"] == name]
            # IC heatmap lag x horizon
            grid_ic = np.full((len(L), len(H)), np.nan)
            grid_t  = np.full((len(L), len(H)), np.nan)
            for i, lag in enumerate(L):
                for j, hor in enumerate(H):
                    r = sub[(sub["lag"] == lag) & (sub["horizon"] == hor)]
                    if not r.empty:
                        grid_ic[i, j] = float(r["IC"].iloc[0]) if pd.notna(r["IC"].iloc[0]) else np.nan
                        grid_t[i, j]  = float(r["t"].iloc[0]) if pd.notna(r["t"].iloc[0]) else np.nan

            fp1 = self._save_fig(self._heatmap(grid_ic, H, L, f"{name} — IC (lag vs horizon)"), f"ic_heat_{name}.png")
            fp2 = self._save_fig(self._heatmap(grid_t,  H, L, f"{name} — t-stat (lag vs horizon)"), f"t_heat_{name}.png")

            # IC vs lag at shortest horizon (first)
            hor0 = H[0]
            ic_line = [float(sub[(sub["lag"] == lag) & (sub["horizon"] == hor0)]["IC"].iloc[0]) if not sub[(sub["lag"] == lag) & (sub["horizon"] == hor0)].empty else np.nan for lag in L]
            fp3 = self._save_fig(self._ic_line(L, ic_line, f"{name} — IC vs Lag (horizon={hor0})"), f"ic_line_{name}.png")

            self.fig_paths[name] = {}
            if fp1: self.fig_paths[name]["ic_heat"] = fp1
            if fp2: self.fig_paths[name]["t_heat"]  = fp2
            if fp3: self.fig_paths[name]["ic_line"] = fp3

    # ---------- HTML ----------
    def _sortable_table_js(self) -> str:
        return """
<script>
(function(){
  function cmp(a,b,desc){
    const na = parseFloat(a), nb = parseFloat(b);
    const isNa = isNaN(na), isNb = isNaN(nb);
    if (!isNa && !isNb){ return desc ? nb - na : na - nb; }
    return desc ? (''+b).localeCompare(''+a) : (''+a).localeCompare(''+b);
  }
  document.querySelectorAll('table.sortable thead th').forEach(th=>{
    th.addEventListener('click', ()=>{
      const table = th.closest('table');
      const idx = Array.from(th.parentNode.children).indexOf(th);
      const desc = th.dataset.desc === '1' ? false : true;
      th.dataset.desc = desc ? '1' : '0';
      const rows = Array.from(table.querySelectorAll('tbody tr'));
      rows.sort((r1,r2)=>cmp(r1.children[idx].innerText, r2.children[idx].innerText, desc));
      const tb = table.querySelector('tbody');
      rows.forEach(r=>tb.appendChild(r));
    });
  });
})();
</script>
"""

    def _write_html(self) -> None:
        # build tables (render-only)
        ic_pdf = self.ic_long_pl.to_pandas()
        sum_pdf = self.summary_pl.to_pandas()

        # pretty
        def fmt(x, pct=False):
            if pd.isna(x): return "-"
            if isinstance(x, (int, float, np.floating)):
                return f"{x*100:.2f}%" if pct else f"{x:.3f}"
            return str(x)

        # summary table
        if not sum_pdf.empty:
            disp = sum_pdf.copy()
            disp.columns = ["Model","IC (avg)","|IC|(max)","|t|(max)","R²(avg)","N(total)"]
            disp["IC (avg)"]  = disp["IC (avg)"].map(lambda v: fmt(v, False))
            disp["|IC|(max)"] = disp["|IC|(max)"].map(lambda v: fmt(v, False))
            disp["|t|(max)"]  = disp["|t|(max)"].map(lambda v: fmt(v, False))
            disp["R²(avg)"]   = disp["R²(avg)"].map(lambda v: fmt(v, False))
            disp["N(total)"]  = disp["N(total)"].map(lambda v: int(v) if pd.notna(v) else "-")
            summary_html = disp.to_html(border=0, escape=False, index=False, classes=["summary"])
        else:
            summary_html = "<div style='color:#888;'>No summary.</div>"

        # IC long — sortable
        long_html_blocks: List[str] = []
        if not ic_pdf.empty:
            cols = ["Model","Lag","Horizon","IC","t","R²","N"]
            disp = ic_pdf.rename(columns={"name":"Model","lag":"Lag","horizon":"Horizon","IC":"IC","t":"t","R2":"R²","N":"N"})[cols].copy()
            for c in ["IC","t","R²"]:
                disp[c] = disp[c].map(lambda v: fmt(v, False))
            disp["N"] = disp["N"].map(lambda v: int(v) if pd.notna(v) else "-")

            # split by model
            for model, g in disp.groupby("Model"):
                html = g.to_html(border=0, escape=False, index=False, classes=["sortable"])
                long_html_blocks.append(f"<h4>IC Diagnostics — {model}</h4>{html}")
        else:
            long_html_blocks.append("<div style='color:#888;'>No IC diagnostics.</div>")

        # figures grid
        fig_rows: List[str] = []
        for model, fmap in self.fig_paths.items():
            tiles = []
            if "ic_heat" in fmap:
                tiles.append(f"<div class='thumb'><div class='cap'>IC Heatmap — {model}</div><img src='{os.path.relpath(fmap['ic_heat'], self.m.output_dir)}'/></div>")
            if "t_heat" in fmap:
                tiles.append(f"<div class='thumb'><div class='cap'>t-stat Heatmap — {model}</div><img src='{os.path.relpath(fmap['t_heat'], self.m.output_dir)}'/></div>")
            if "ic_line" in fmap:
                tiles.append(f"<div class='thumb'><div class='cap'>IC vs Lag — {model}</div><img src='{os.path.relpath(fmap['ic_line'], self.m.output_dir)}'/></div>")
            if tiles:
                fig_rows.append(f"<div class='fig-row'>{''.join(tiles)}</div>")

        figures_html = "\n".join(fig_rows) if fig_rows else "<div style='padding:8px;color:#888;'>No figures.</div>"

        css = r"""
<style>
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;margin:0;background:#fff}
.page{padding:16px}
h1{font-size:20px;margin:0 0 8px 0}
h3{font-size:14px;margin:12px 0 6px 0}
h4{font-size:13px;margin:10px 0 6px 0}
.fig-row{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:8px 0 18px 0}
.thumb{border:1px solid #e4e4e4;border-radius:6px;background:#fff;padding:6px}
.thumb .cap{font-size:12px;font-weight:600;margin:0 0 6px 0;color:#333}
.thumb img{width:100%;height:auto;display:block}
table{font-size:12px;border-collapse:collapse;background:#fff}
table thead th{background:#f6f6f6;padding:6px 10px;text-align:right}
table thead th:first-child{text-align:left}
table tbody td{padding:6px 10px;text-align:right}
table tbody td:first-child{text-align:left}
</style>
"""
        js = self._sortable_table_js()

        html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>{self.m.title}</title>
{css}
</head>
<body>
<div class="page">
  <h1>{self.m.title}</h1>

  <h3>Summary</h3>
  {summary_html}

  <h3>Diagnostics</h3>
  {"".join(long_html_blocks)}

  <h3>Figures</h3>
  {figures_html}
</div>
{js}
</body>
</html>
"""
        self.html_path = os.path.join(self.m.output_dir, "stats_dashboard.html")
        with open(self.html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[stats] written: {self.html_path}")