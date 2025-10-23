#!/usr/bin/env python3
# gemspa/ensemble_analysis.py

import os
import glob
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from textwrap import fill

from .step_size_analysis import (
    run_condition_step_kde,
    run_condition_step_kde_filtered,
)
try:
    from .utils.data_io import load_trajectory_csv, condition_from_filename, collect_condition_files
    from .utils.plotting import plot_msd_linear, plot_msd_loglog
    from .msd_diffusion import compute_track_msd, fit_linear_and_loglog
except ImportError:
    # Fallback for standalone execution
    from .utils.data_io import load_trajectory_csv, condition_from_filename, collect_condition_files  # type: ignore
    from .utils.plotting import plot_msd_linear, plot_msd_loglog  # type: ignore
    from .msd_diffusion import compute_track_msd, fit_linear_and_loglog  # type: ignore

# ------------------------------
# CSV loading / normalization (now using consolidated utilities)
# ------------------------------


# ------------------------------
# MSD computation / plotting
# ------------------------------
# MSD computation now uses consolidated functions from msd_diffusion.py


def _ensemble_msd_for_condition(
    work_dir,
    condition,
    micron_per_px,
    time_step,
    tlag_cutoff,
    min_track_len,
    only_track_ids=None,
):
    """
    Compute ensemble-averaged MSD for a condition (optionally restricting to selected track IDs).
    Returns (tau, ens_msd, (D, alpha)) or None if no usable tracks.
    """
    csvs = collect_condition_files(work_dir, condition)
    if not csvs:
        return None

    msds = []
    for f in csvs:
        try:
            df = load_trajectory_csv(f)
        except Exception:
            continue

        if only_track_ids is not None:
            stem = os.path.splitext(os.path.basename(f))[0]
            keep = only_track_ids.get(stem, None)
            if keep is not None and len(keep) > 0:
                df = df.copy()
                df["track_id"] = df["track_id"].astype(str)
                df = df[df["track_id"].isin(keep)]

        for _, g in df.groupby("track_id"):
            if len(g) < min_track_len:
                continue
            coords = g[["x", "y"]].to_numpy() * micron_per_px
            msd = compute_track_msd(coords, tlag_cutoff)
            if msd is not None and np.isfinite(msd).any():
                msds.append(msd)

    if not msds:
        return None

    L = min(len(v) for v in msds)
    if L < 1:
        return None

    msd_mat = np.vstack([v[:L] for v in msds])
    ens_msd = np.nanmean(msd_mat, axis=0)
    tau = np.arange(1, L + 1, dtype=float) * time_step
    D, alpha, _ = fit_linear_and_loglog(tau, ens_msd)
    return tau, ens_msd, (D, alpha)


def _load_filtered_track_ids(work_dir, condition, filt):
    """
    From each replicate's msd_results.csv, collect track IDs that pass D/α filters.
    Returns a dict keyed by BOTH "<cond>_<rep>" and "Traj_<cond>_<rep>" for robust matching.
    Track IDs are normalized to strings to avoid dtype mismatches.
    """
    d = {}
    rep_dirs = sorted(glob.glob(os.path.join(work_dir, f"{condition}_*"))) + sorted(
        glob.glob(os.path.join(work_dir, f"Traj_{condition}_*"))
    )
    for rd in rep_dirs:
        csvp = os.path.join(rd, "msd_results.csv")
        if not os.path.exists(csvp):
            continue
        df = pd.read_csv(csvp)
        if not {"D_fit", "alpha_fit", "track_id"}.issubset(df.columns):
            continue
        m = (df["D_fit"].between(filt["D_min"], filt["D_max"])) & (
            df["alpha_fit"].between(filt["alpha_min"], filt["alpha_max"])
        )
        keep = set(df.loc[m, "track_id"].astype(str).tolist())
        stem = os.path.basename(rd)  # e.g., "DMSO_001"
        d[stem] = keep
        d["Traj_" + stem] = keep  # e.g., "Traj_DMSO_001"
        print(f"[ensemble] filtered keep IDs for {stem}: {len(keep)}")
    return d


# ------------------------------
# Public API
# ------------------------------
def run_ensemble(
    work_dir,
    filter_D_min=0.001,
    filter_D_max=2.0,
    filter_alpha_min=0.0,
    filter_alpha_max=2.0,
    time_step=0.010,
    micron_per_px=0.11,
    tlag_cutoff=10,
    min_track_len=11,
    run_step_sizes=True,
):
    """
    Build grouped tables and ensemble MSD plots per condition.

    Outputs:
      - grouped_raw/msd_results.csv
      - grouped_filtered/msd_results.csv
      - grouped_raw/ensemble_msd_vs_tau_<condition>.png
      - grouped_raw/ensemble_msd_vs_tau_loglog_<condition>.png
      - grouped_filtered/ensemble_msd_vs_tau_<condition>.png
      - grouped_filtered/ensemble_msd_vs_tau_loglog_<condition>.png
      - grouped_raw/step_kde/step_kde_<condition>_(ensemble).png
      - grouped_filtered/step_kde/step_kde_<condition>_(filtered_ensemble).png
    """
    # Identify conditions from replicate folders already created by the per-file step
    rep_dirs = sorted([d for d in glob.glob(os.path.join(work_dir, "*")) if os.path.isdir(d)])
    conditions = {}
    for rd in rep_dirs:
        stem = os.path.basename(rd)
        cond = condition_from_filename(stem)
        conditions.setdefault(cond, []).append(rd)

    # Normalize filter bounds and package
    Dmin = -float("inf") if filter_D_min is None else filter_D_min
    Dmax = float("inf") if filter_D_max is None else filter_D_max
    alph_min = -float("inf") if filter_alpha_min is None else filter_alpha_min
    alph_max = float("inf") if filter_alpha_max is None else filter_alpha_max
    filt = dict(D_min=Dmin, D_max=Dmax, alpha_min=alph_min, alpha_max=alph_max)

    # Ensure grouped output dirs exist
    grouped_raw_dir = os.path.join(work_dir, "grouped_raw")
    grouped_filt_dir = os.path.join(work_dir, "grouped_filtered")
    os.makedirs(grouped_raw_dir, exist_ok=True)
    os.makedirs(grouped_filt_dir, exist_ok=True)

    all_raw_rows = []
    all_filt_rows = []

    for cond, _reps in conditions.items():
        # -------- Gather replicate rows (for grouped CSVs) --------
        rep_dirs_c = sorted(glob.glob(os.path.join(work_dir, f"{cond}_*"))) + sorted(
            glob.glob(os.path.join(work_dir, f"Traj_{cond}_*"))
        )
        for rd in rep_dirs_c:
            p = os.path.join(rd, "msd_results.csv")
            if not os.path.exists(p):
                continue
            df = pd.read_csv(p)
            if {"D_fit", "alpha_fit"}.issubset(df.columns):
                df["condition"] = cond
                all_raw_rows.append(df)
                m = (df["D_fit"].between(filt["D_min"], filt["D_max"])) & (
                    df["alpha_fit"].between(filt["alpha_min"], filt["alpha_max"])
                )
                all_filt_rows.append(df.loc[m].copy())

        # -------- RAW ensemble MSD --------
        res = _ensemble_msd_for_condition(
            work_dir,
            cond,
            micron_per_px,
            time_step,
            tlag_cutoff,
            min_track_len,
            only_track_ids=None,
        )
        if res is not None:
            tau, msd, (D, alpha) = res
            plot_msd_linear(
                tau,
                msd,
                os.path.join(grouped_raw_dir, f"ensemble_msd_vs_tau_{cond}.png"),
                f"ens-avg MSD (2d) — {cond}",
                D,
            )
            plot_msd_loglog(
                tau,
                msd,
                os.path.join(grouped_raw_dir, f"ensemble_msd_vs_tau_loglog_{cond}.png"),
                f"ens-avg log-log MSD (2d) — {cond}",
                alpha,
            )
        else:
            print(f"[ensemble] No usable tracks for RAW ensemble of {cond}; skipping MSD plots.")

        # Optional RAW step-size KDE
        if run_step_sizes:
            raw_step_dir = os.path.join(grouped_raw_dir, "step_kde")
            ok_raw, xlim, ymax = run_condition_step_kde(work_dir, cond, raw_step_dir)

        # -------- FILTERED ensemble MSD --------
        keep_ids = _load_filtered_track_ids(work_dir, cond, filt)
        res_f = _ensemble_msd_for_condition(
            work_dir,
            cond,
            micron_per_px,
            time_step,
            tlag_cutoff,
            min_track_len,
            only_track_ids=keep_ids,
        )
        if res_f is not None:
            tau_f, msd_f, (D_f, alpha_f) = res_f
            plot_msd_linear(
                tau_f,
                msd_f,
                os.path.join(grouped_filt_dir, f"ensemble_msd_vs_tau_{cond}.png"),
                f"ens-avg MSD (2d) — {cond} (filtered)",
                D_f,
            )
            plot_msd_loglog(
                tau_f,
                msd_f,
                os.path.join(grouped_filt_dir, f"ensemble_msd_vs_tau_loglog_{cond}.png"),
                f"ens-avg log-log MSD (2d) — {cond} (filtered)",
                alpha_f,
            )
        else:
            print(f"[ensemble] No usable tracks for FILTERED ensemble of {cond}; skipping MSD plots.")

        # Optional FILTERED step-size KDE (reuse RAW axes if available)
        if run_step_sizes:
            filt_step_dir = os.path.join(grouped_filt_dir, "step_kde")
            run_condition_step_kde_filtered(
                work_dir,
                cond,
                keep_ids_map=keep_ids,
                out_dir=filt_step_dir,
                micron_per_px=micron_per_px,
                tlag_cutoff=tlag_cutoff,
                min_track_len=max(2, min_track_len),
                xlim_hint=xlim if run_step_sizes and 'xlim' in locals() and ok_raw else None,
                ymax_hint=ymax if run_step_sizes and 'ymax' in locals() and ok_raw else None,
            )

    # -------- Write grouped tables once per run --------
    if all_raw_rows:
        gr = pd.concat(all_raw_rows, ignore_index=True)
        gr.to_csv(os.path.join(grouped_raw_dir, "msd_results.csv"), index=False)
    if all_filt_rows:
        gf = pd.concat(all_filt_rows, ignore_index=True)
        gf.to_csv(os.path.join(grouped_filt_dir, "msd_results.csv"), index=False)
