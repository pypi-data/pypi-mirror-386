#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced grouped analysis (TrackMate/GEMspa-compatible)

- Pools by condition across 1+ input folders.
- Uses the same filtering parameters as GEMspa core:
    * minlen                  (minimum frames per track)
    * lag                     (tlag_cutoff used for MSD calculation)
    * filter_D_min/max        (μm^2/s)
    * filter_alpha_min/max    (dimensionless)
- Outputs into: <work_dir>/grouped_advanced_analysis

Per-track metrics saved:
    track_id, condition, D_fit, alpha_fit, r2_fit, vacf_lag1, confinement_idx,
    hull_area_um2, tortuosity, n_frames

Figures:
    - Box/violin plots of D_fit and alpha_fit by condition
    - VACF distributions (hist + mean curve)
    - Convex-hull area vs tortuosity scatter (per condition and pooled)

NOTE: Coordinates in the input Traj_*.csv are in PIXELS; we scale by micron_per_px.
"""

from __future__ import annotations
import os, re, math, json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Use consolidated MSD functions
try:
    from .msd_diffusion import msd_diffusion, compute_track_msd, fit_linear_and_loglog
    from .utils.data_io import load_trajectory_csv, condition_from_filename
    from .utils.plotting import plot_boxplot, plot_scatter, save_figure
except ImportError:
    from .msd_diffusion import msd_diffusion, compute_track_msd, fit_linear_and_loglog  # type: ignore
    from .utils.data_io import load_trajectory_csv, condition_from_filename  # type: ignore
    from .utils.plotting import plot_boxplot, plot_scatter, save_figure  # type: ignore

# ------------------------- utils -------------------------

REQUIRED = ("track_id", "frame", "x", "y")

def _find_traj_csvs(root: str) -> list[str]:
    p = Path(root)
    if p.is_file() and p.name.startswith("Traj_") and p.suffix.lower()==".csv":
        return [str(p)]
    out = []
    for f in p.rglob("Traj_*.csv"):
        out.append(str(f))
    return sorted(out)

def _infer_condition_from_name(fname: str) -> str:
    """Extract condition name from filename, removing date codes and replicate numbers."""
    return condition_from_filename(fname)

def _read_and_validate(traj_csv: str) -> pd.DataFrame:
    """Use consolidated data loading."""
    return load_trajectory_csv(traj_csv)

# Use consolidated MSD computation

def _velocities(px_xy_um: np.ndarray, dt: float) -> np.ndarray:
    v = np.diff(px_xy_um, axis=0) / max(dt, 1e-12)
    return v

def _vacf(v: np.ndarray, max_lag: int) -> np.ndarray:
    """velocity autocorrelation for lags 0..max_lag (2D dot)."""
    n = v.shape[0]
    max_lag = min(max_lag, n-1) if n>1 else 0
    ac = np.zeros(max_lag+1, dtype=float)
    if n <= 1:
        return ac
    v0 = v - v.mean(axis=0, keepdims=True)
    denom = (v0*v0).sum(axis=1).mean() + 1e-12
    ac[0] = 1.0
    for k in range(1, max_lag+1):
        dots = (v0[:-k]*v0[k:]).sum(axis=1)
        ac[k] = dots.mean()/denom
    return ac

def _radius_of_gyration(px_xy_um: np.ndarray) -> float:
    c = px_xy_um.mean(axis=0)
    dif = px_xy_um - c
    return float(np.sqrt(((dif**2).sum(axis=1).mean())))

def _convex_hull_area(px_xy_um: np.ndarray) -> float:
    # Monotone chain in 2D
    pts = px_xy_um.astype(float)
    if len(pts) < 3:
        return 0.0
    pts = pts[np.lexsort((pts[:,1], pts[:,0]))]
    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in pts[::-1]:
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = np.array(lower[:-1] + upper[:-1])
    # polygon area (shoelace)
    x = hull[:,0]; y = hull[:,1]
    return float(0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))

def _tortuosity(px_xy_um: np.ndarray) -> float:
    seg = np.sqrt(((np.diff(px_xy_um,axis=0))**2).sum(axis=1))
    L = float(seg.sum())
    disp = float(np.linalg.norm(px_xy_um[-1] - px_xy_um[0]))
    return float(L / max(disp, 1e-12))

def _condition_key_from_file(f: str) -> str:
    return _infer_condition_from_name(f)

# ------------------------- core -------------------------

def run_advanced_group_analysis(
    inputs: list[str],
    outdir: str,
    px: float,
    dt: float,
    lag: int,
    minlen: int,
    filter_D_min: Optional[float] = None,
    filter_D_max: Optional[float] = None,
    filter_alpha_min: Optional[float] = None,
    filter_alpha_max: Optional[float] = None,
) -> None:
    """
    Entrypoint used by gemspa-cli.
    """
    Path(outdir).mkdir(parents=True, exist_ok=True)
    fig_dir = Path(outdir) / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    msd_proc = msd_diffusion(save_dir=outdir)

    # Collect files
    files: list[str] = []
    for root in inputs:
        files.extend(_find_traj_csvs(root))
    if not files:
        print("[Advanced Group Analysis] No Traj_*.csv found in provided inputs; nothing to do.")
        return

    # Pool by condition
    per_condition_rows: dict[str, list[dict]] = defaultdict(list)

    for f in files:
        cond = _condition_key_from_file(f)
        df = _read_and_validate(f)

        # group by track
        for tid, g in df.groupby("track_id", sort=False):
            if len(g) < max(2, int(minlen)):
                continue
            # pixel→μm coords
            xy_um = g[["x","y"]].to_numpy(dtype=float) * float(px)

            # --- MSD (lags 1..L) in μm², L capped by 'lag' and track length
            L = min(int(lag), max(1, xy_um.shape[0]-1))
            msd_vec = compute_track_msd(xy_um, L)

            # time axis (s)
            tau = (np.arange(1, L+1, dtype=float)) * float(dt)
            
            # Use consolidated fitting
            D_fit, alpha_fit, r2_fit = fit_linear_and_loglog(tau, msd_vec)

            # Apply GEMspa-like filters if specified
            if (filter_D_min is not None and not (D_fit >= filter_D_min)) or \
               (filter_D_max is not None and not (D_fit <= filter_D_max)) or \
               (filter_alpha_min is not None and not (alpha_fit >= filter_alpha_min)) or \
               (filter_alpha_max is not None and not (alpha_fit <= filter_alpha_max)):
                continue

            # Kinematics
            v = _velocities(xy_um, float(dt))
            vacf = _vacf(v, max_lag=min(25, max(1, len(v)-1)))  # cap at 25 lags for plots
            vacf_lag1 = float(vacf[1]) if vacf.size > 1 else np.nan

            # Geometry metrics
            rg = _radius_of_gyration(xy_um)
            max_disp = np.max(np.sqrt(((xy_um - xy_um[0])**2).sum(axis=1))) if len(xy_um)>0 else 0.0
            confinement_idx = float(rg / max(max_disp, 1e-12))
            hull_area = _convex_hull_area(xy_um)
            tort = _tortuosity(xy_um)

            per_condition_rows[cond].append({
                "track_id": int(tid),
                "condition": cond,
                "D_fit": float(D_fit),
                "alpha_fit": float(alpha_fit),
                "r2_fit": float(r2_fit),
                "vacf_lag1": vacf_lag1,
                "confinement_idx": confinement_idx,
                "hull_area_um2": float(hull_area),
                "tortuosity": float(tort),
                "n_frames": int(len(g)),
            })

    # Write per-condition CSVs + pooled CSV
    all_rows = []
    for cond, rows in per_condition_rows.items():
        if not rows:
            continue
        cdf = pd.DataFrame(rows)
        cdf.to_csv(Path(outdir) / f"{cond}_advanced_metrics.csv", index=False)
        all_rows.extend(rows)
    if not all_rows:
        print("[Advanced Group Analysis] No tracks survived filters; no outputs.")
        return
    all_df = pd.DataFrame(all_rows)
    all_df.to_csv(Path(outdir) / "all_conditions_advanced_metrics.csv", index=False)

    # --------- Figures ---------
    def _box_or_violin(ax, data_by_cond: dict[str, np.ndarray], title: str, ylabel: str, violin=True):
        keys = sorted(data_by_cond.keys())
        data = [data_by_cond[k] for k in keys]
        if violin:
            ax.violinplot(data, showmeans=True, showextrema=False)
        else:
            ax.boxplot(data, notch=True, showfliers=False)
        ax.set_xticks(range(1,len(keys)+1)); ax.set_xticklabels(keys, rotation=30, ha="right")
        ax.set_title(title); ax.set_ylabel(ylabel)

    # D_fit by condition
    d_by = {c: all_df.query("condition == @c")["D_fit"].to_numpy() for c in sorted(per_condition_rows.keys()) if len(per_condition_rows[c])}
    if d_by:
        plot_boxplot(d_by, str(Path(fig_dir)/"D_fit_by_condition.png"), 
                    "Diffusion coefficient (D_fit)", "μm²/s", violin=True)

    # alpha by condition
    a_by = {c: all_df.query("condition == @c")["alpha_fit"].to_numpy() for c in sorted(per_condition_rows.keys()) if len(per_condition_rows[c])}
    if a_by:
        plot_boxplot(a_by, str(Path(fig_dir)/"alpha_by_condition.png"), 
                    "Anomalous exponent (alpha_fit)", "α", violin=True)

    # VACF lag-1 histogram per condition (grid)
    conds = [c for c in sorted(per_condition_rows.keys()) if len(per_condition_rows[c])]
    if conds:
        n = len(conds); ncols = min(3, n); nrows = int(np.ceil(n / ncols))
        fig, axs = plt.subplots(nrows, ncols, figsize=(4*ncols, 3.2*nrows), squeeze=False)
        for i,c in enumerate(conds):
            ax = axs[i//ncols, i % ncols]
            x = all_df.query("condition == @c")["vacf_lag1"].dropna().to_numpy()
            if len(x):
                ax.hist(x, bins=30, edgecolor="black")
            ax.set_title(f"{c}  (VACF lag-1)")
        fig.tight_layout(); fig.savefig(Path(fig_dir)/"VACF_lag1_hist_by_condition.png", dpi=300); plt.close(fig)

    # Hull area vs tortuosity scatter (pooled)
    fig, ax = plt.subplots(figsize=(7,5))
    for c in conds:
        sub = all_df.query("condition == @c")
        ax.scatter(sub["hull_area_um2"], sub["tortuosity"], label=c, alpha=0.6, s=18)
    ax.set_xlabel("Convex hull area (μm²)"); ax.set_ylabel("Tortuosity (L/disp)")
    ax.legend(frameon=False)
    save_figure(fig, str(Path(fig_dir)/"hull_area_vs_tortuosity.png"))

    # Save parameters used
    params = dict(
        micron_per_px=float(px),
        time_step=float(dt),
        tlag_cutoff=int(lag),
        min_track_len=int(minlen),
        filter_D_min=(None if filter_D_min is None else float(filter_D_min)),
        filter_D_max=(None if filter_D_max is None else float(filter_D_max)),
        filter_alpha_min=(None if filter_alpha_min is None else float(filter_alpha_min)),
        filter_alpha_max=(None if filter_alpha_max is None else float(filter_alpha_max)),
    )
    pd.Series(params).to_csv(Path(outdir)/"params_log.csv", header=False)
    with open(Path(outdir)/"params_log.json","w") as f:
        json.dump(params, f, indent=2)

    # Split metrics by condition
    _split_metrics_by_condition(all_df, outdir)
    
    print(f"[Advanced Group Analysis] Wrote advanced metrics to: {outdir}")
    print(f"[Advanced Group Analysis] Figures → {fig_dir}")

def _split_metrics_by_condition(df: pd.DataFrame, outdir: str) -> None:
    """Split metrics by condition into per-parameter CSVs."""
    from pathlib import Path
    
    DEFAULT_PARAMS = [
        "D_fit", "alpha_fit", "r2_fit", "vacf_lag1",
        "confinement_idx", "hull_area_um2", "tortuosity", "n_frames"
    ]
    
    ALIASES = {
        "frames": ["n_frames","frames","num_frames"],
        "alpha": ["alpha","alpha_fit","alpha_hat","alpha^","alpha^2","alpha2"],
        "d_fit": ["d_fit","d","d_um2_per_s","diffusion","diffusion_coefficient","d_um2_per_s"],
        "r2_fit": ["r2_fit","r2","r_squared","rsq","r^2"],
        "confinement_idx": ["confinement_idx","confinement_index","conf_index"],
        "hull_area_um2": ["hull_area_um2","hull_area","convex_hull_area_um2","hull_area (um^2)"],
        "tortuosity": ["tortuosity","tort","path_tortuosity"],
        "vacf_lag1": ["vacf_lag1","vacf_lag_1","vacf1","vacf_lag=1"]
    }
    
    def find_actual_col(requested: str, columns: list) -> str:
        req_lower = requested.lower()
        for c in columns:
            if c.lower() == req_lower:
                return c
        if req_lower in ALIASES:
            for alias in ALIASES[req_lower]:
                for c in columns:
                    if c.lower() == alias.lower():
                        return c
        for c in columns:
            if req_lower in c.lower():
                return c
        return None
    
    def build_out_table(df: pd.DataFrame, cond_col: str, value_col: str) -> pd.DataFrame:
        series = df[[cond_col, value_col]].dropna()
        grouped = series.groupby(cond_col)[value_col].apply(list)
        max_len = max((len(v) for v in grouped.values), default=0)
        data = {str(cond): (vals + [np.nan]*(max_len - len(vals))) for cond, vals in grouped.items()}
        out_df = pd.DataFrame(data)
        cols = list(out_df.columns)
        if any(c.lower() == "vector" for c in cols):
            vector = [c for c in cols if c.lower() == "vector"][0]
            others = sorted([c for c in cols if c != vector], key=lambda x: x.lower())
            out_df = out_df[[vector] + others]
        else:
            out_df = out_df[sorted(cols, key=lambda x: x.lower())]
        return out_df
    
    # Find condition column
    cond_col = None
    for c in df.columns:
        if "condition" in c.lower():
            cond_col = c
            break
    if cond_col is None:
        print("[Advanced Group Analysis] No condition column found for splitting metrics")
        return
    
    df[cond_col] = df[cond_col].astype(str)
    
    # Convert numeric columns
    for c in df.columns:
        if not pd.api.types.is_numeric_dtype(df[c]):
            coerced = pd.to_numeric(df[c], errors="coerce")
            if coerced.notna().sum() > 0:
                df[c] = coerced
    
    columns = df.columns.tolist()
    actual_map = {p: find_actual_col(p, columns) for p in DEFAULT_PARAMS}
    
    out_dir = Path(outdir) / "split_metrics_by_condition"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    for req, actual in actual_map.items():
        if actual is None:
            results[req] = "(not created)"
            continue
        if not pd.api.types.is_numeric_dtype(df[actual]):
            df[actual] = pd.to_numeric(df[actual], errors="coerce")
        if df[actual].notna().sum() == 0:
            results[req] = "(not created)"
            continue
        out_df = build_out_table(df, cond_col, actual)
        out_path = out_dir / f"{req.replace('/', '-').replace(' ', '_')}.csv"
        out_df.to_csv(out_path, index=False)
        results[req] = str(out_path)
    
    # Create index file
    idx_rows = []
    for req in DEFAULT_PARAMS:
        idx_rows.append({
            "requested_parameter": req,
            "matched_column": actual_map.get(req),
            "output_csv": results.get(req, "(not created)")
        })
    pd.DataFrame(idx_rows).to_csv(out_dir / "_index.csv", index=False)
    
    print(f"[Advanced Group Analysis] Split metrics by condition → {out_dir}")

# ------------------------- CLI shim (optional) -------------------------

def _cli():
    import argparse
    ap = argparse.ArgumentParser(description="Advanced grouped analysis")
    ap.add_argument("work_dir", help="Folder containing Traj_*.csv (can be many).")
    ap.add_argument("--outdir", default=None, help="Output directory (default: <work_dir>/grouped_advanced_analysis)")
    ap.add_argument("--px", type=float, required=True, help="micron per pixel")
    ap.add_argument("--dt", type=float, required=True, help="time step (s)")
    ap.add_argument("--lag", type=int, default=3, help="tlag cutoff for MSD")
    ap.add_argument("--minlen", type=int, default=3, help="minimum frames per track")
    ap.add_argument("--filter-D-min", type=float, default=None)
    ap.add_argument("--filter-D-max", type=float, default=None)
    ap.add_argument("--filter-alpha-min", type=float, default=None)
    ap.add_argument("--filter-alpha-max", type=float, default=None)
    args = ap.parse_args()

    outdir = args.outdir or os.path.join(args.work_dir, "grouped_advanced_analysis")
    run_advanced_group_analysis(
        inputs=[args.work_dir],
        outdir=outdir,
        px=args.px,
        dt=args.dt,
        lag=args.lag,
        minlen=args.minlen,
        filter_D_min=args.filter_D_min,
        filter_D_max=args.filter_D_max,
        filter_alpha_min=args.filter_alpha_min,
        filter_alpha_max=args.filter_alpha_max,
    )

if __name__ == "__main__":
    _cli()
