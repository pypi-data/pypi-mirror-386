#!/usr/bin/env python3
"""
analyze_steps_and_tracks.py (clean, parallelized)

- Heatmaps of step size vs brightness (auto-detect TrackMate vs steps tables)
  * TrackMate: X/Y multiplied by 1000 before distance, then divide step back (precision fix)
  * Default brightness column: MEAN_INTENSITY_CH1 (override with --brightness-col)
  * Uniform axes & LUT across figures; count cap with red-saturation overlay
  * Per-file PNGs + pooled PNG + per-file grid PDF + pooled-only PDF
  * Optional datecode stripping for labels: "HK1-220706_4" -> "HK1_4"

- Track overlays (segments colored by step size)
  * Requires TrackMate CSVs
  * Precision fix as above
  * Uniform axes & LUT; per-file PNGs + pooled PNG + combined PDF
  * Invert LUT only for tracks via --invert-lut-tracks
  * Filter short tracks via --min-track-length (default 10)

- Parallel per-file processing via --workers (default: CPU count)
"""

import argparse
import glob
import math
import os
from typing import List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.collections import LineCollection


# --------------------- Helpers ---------------------
def _find_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    cols = list(df.columns)
    low = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand in cols:
            return cand
        if cand.lower() in low:
            return low[cand.lower()]
        for c in cols:
            if cand.lower() in c.lower():
                return c
    return None


def strip_datecode(name: str) -> str:
    """Remove hyphenated 4–8 digit date code before underscore or end, e.g. HK1-220706_4 -> HK1_4."""
    return re.sub(r'-(\d{4,8})(?=(_|$))', '', name)


def detect_mode(csv_path: str) -> str:
    """Return 'trackmate' for spots-in-tracks stats; 'steps' for steps_vs_brightness tables."""
    df = pd.read_csv(csv_path, nrows=20, low_memory=False)
    cols = [c.lower() for c in df.columns]
    if any(("position_x" in c) or ("position y" in c) for c in cols):
        return "trackmate"
    if any(("step_size" in c) for c in cols) and any(("brightness" in c) for c in cols):
        return "steps"
    raise ValueError(f"Could not detect data type for {os.path.basename(csv_path)}")


# --------------------- Core transforms ---------------------
def compute_steps_from_trackmate(df: pd.DataFrame,
                                 brightness_override: Optional[str] = None,
                                 x_override: Optional[str] = None,
                                 y_override: Optional[str] = None) -> pd.DataFrame:
    """TrackMate spots-> per-step table: columns [step_size, brightness]."""
    x_col = x_override or _find_col(df, ["POSITION_X", "X", "POSITION X", "X_POS"])
    y_col = y_override or _find_col(df, ["POSITION_Y", "Y", "POSITION Y", "Y_POS"])
    track_col = _find_col(df, ["TRACK_ID", "TRACKID", "TRACK"])
    frame_col = _find_col(df, ["FRAME", "POSITION_T", "T", "TIME"])

    # prefer override; else MEAN_INTENSITY_CH1; else common fallbacks
    bright_col = None
    if brightness_override:
        if brightness_override in df.columns:
            bright_col = brightness_override
        else:
            bright_col = _find_col(df, [brightness_override])
    if bright_col is None:
        bright_col = _find_col(df, ["MEAN_INTENSITY_CH1", "MEAN_INTENSITY", "INTENSITY", "MEDIAN_INTENSITY", "QUALITY"])

    if not all([x_col, y_col, track_col, bright_col]):
        raise ValueError("Missing columns (need POSITION_X/Y, TRACK_ID, and a brightness column).")

    df[x_col] = pd.to_numeric(df[x_col], errors="coerce")
    df[y_col] = pd.to_numeric(df[y_col], errors="coerce")
    df[bright_col] = pd.to_numeric(df[bright_col], errors="coerce")

    rows = []
    for tid, g in df.groupby(track_col, dropna=True):
        g = g.copy()
        if frame_col and frame_col in g.columns:
            g = g.sort_values(frame_col, kind="mergesort")
        if len(g) < 2:
            continue

        x = g[x_col].to_numpy(dtype=float)
        y = g[y_col].to_numpy(dtype=float)
        b = g[bright_col].to_numpy(dtype=float)

        # precision fix (units remain pixels)
        x1000 = x * 1000.0
        y1000 = y * 1000.0
        dx = x1000[1:] - x1000[:-1]
        dy = y1000[1:] - y1000[:-1]
        step_px = np.sqrt(dx*dx + dy*dy) / 1000.0

        step_brightness = 0.5 * (b[1:] + b[:-1])
        rows.append(pd.DataFrame({"step_size": step_px, "brightness": step_brightness}))

    if not rows:
        return pd.DataFrame(columns=["step_size", "brightness"])
    return pd.concat(rows, ignore_index=True)


def load_steps_table(path: str) -> pd.DataFrame:
    """Load steps_vs_brightness CSV -> columns [step_size, brightness]."""
    df = pd.read_csv(path, low_memory=False)
    step_col = _find_col(df, ["step_size", "STEP_SIZE"])
    bright_col = _find_col(df, ["brightness", "BRIGHTNESS"])
    if not step_col or not bright_col:
        raise ValueError(f"{os.path.basename(path)} is not a steps_vs_brightness table.")
    out = df[[step_col, bright_col]].copy()
    out.columns = ["step_size", "brightness"]
    return out


# --------------------- Plotting ---------------------
def build_hist2d(df: pd.DataFrame, stepsize_max: float, ymin: float, ymax: float, bins_x: int, bins_y: int):
    x = df["step_size"].to_numpy()
    y = df["brightness"].to_numpy()
    H, _, _ = np.histogram2d(x, y, bins=[bins_x, bins_y], range=[[0, stepsize_max], [ymin, ymax]])
    return H


def plot_heatmap_matrix(H: np.ndarray, stepsize_max: float, ymin: float, ymax: float, vmax_cap: int, title: str, out_png: str, units_label: str = "pixels"):
    Hc = np.clip(H, 0, vmax_cap)
    plt.figure(figsize=(6, 5))
    plt.imshow(Hc.T, origin="lower", aspect="auto",
               extent=[0, stepsize_max, ymin, ymax],
               cmap="viridis", norm=Normalize(vmin=0, vmax=vmax_cap))
    sat = Hc.T >= (vmax_cap - 1e-9)
    if np.any(sat):
        overlay = np.zeros((*sat.shape, 4))
        overlay[sat] = [1, 0, 0, 1]
        plt.imshow(overlay, origin="lower", aspect="auto",
                   extent=[0, stepsize_max, ymin, ymax])
    plt.colorbar(label=f"Counts (cap={vmax_cap}; red=saturated)")
    plt.xlabel(f"Step size ({units_label})")
    plt.ylabel("Brightness (a.u.)")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_png, dpi=600)
    plt.close()


def segments_from_trackmate(df: pd.DataFrame, min_track_length: int = 10) -> Tuple[np.ndarray, np.ndarray]:
    """Return segments (N,2,2) and per-segment step sizes (pixels), keep tracks with >= min_track_length points."""
    x_col = _find_col(df, ["POSITION_X", "X", "POSITION X", "X_POS"])
    y_col = _find_col(df, ["POSITION_Y", "Y", "POSITION Y", "Y_POS"])
    track_col = _find_col(df, ["TRACK_ID", "TRACKID", "TRACK"])
    frame_col = _find_col(df, ["FRAME", "POSITION_T", "T", "TIME"])
    if not all([x_col, y_col, track_col]):
        raise ValueError("Missing columns for overlays (POSITION_X/Y, TRACK_ID).")

    df[x_col] = pd.to_numeric(df[x_col], errors="coerce")
    df[y_col] = pd.to_numeric(df[y_col], errors="coerce")

    segs, vals = [], []
    for tid, g in df.groupby(track_col, dropna=True):
        g = g.copy()
        if frame_col and frame_col in g.columns:
            g = g.sort_values(frame_col, kind="mergesort")
        if len(g) < max(2, int(min_track_length)):
            continue

        x = g[x_col].to_numpy(dtype=float)
        y = g[y_col].to_numpy(dtype=float)

        x1000 = x * 1000.0
        y1000 = y * 1000.0
        dx = x1000[1:] - x1000[:-1]
        dy = y1000[1:] - y1000[:-1]
        step_px = np.sqrt(dx*dx + dy*dy) / 1000.0

        p0 = np.stack([x[:-1], y[:-1]], axis=1)
        p1 = np.stack([x[1:],  y[1:]],  axis=1)
        segs.extend(np.stack([p0, p1], axis=1))
        vals.extend(step_px)

    segs = np.asarray(segs) if segs else np.empty((0,2,2), dtype=float)
    vals = np.asarray(vals) if vals else np.empty((0,), dtype=float)
    return segs, vals


def plot_tracks_per_file(perfile, xmin: float, xmax: float, ymin: float, ymax: float,
                         stepsize_max: float, line_width: float, outdir: str, cmap_name: str, units_label: str = "pixels"):
    norm = Normalize(vmin=0.0, vmax=max(stepsize_max, 1e-6))
    pngs = []
    for f, (segs, vals) in perfile.items():
        base = os.path.splitext(os.path.basename(f))[0]
        base = strip_datecode(base)
        safe = base.replace(" ", "_")
        out_png = os.path.join(outdir, f"overlay_{safe}.png")

        plt.figure(figsize=(7, 7))
        ax = plt.gca()
        vals_clamped = np.clip(vals, norm.vmin, norm.vmax)
        lc = LineCollection(segs, array=vals_clamped, cmap=cmap_name, norm=norm, linewidths=line_width)
        ax.add_collection(lc)
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.set_aspect("equal", adjustable="box")
        cbar = plt.colorbar(lc)
        cbar.set_label(f"Step size ({units_label})")
        ax.set_title(base)
        plt.tight_layout()
        plt.savefig(out_png, dpi=600)
        plt.close()
        pngs.append((f, out_png))

    pooled_png = os.path.join(outdir, "overlay_all.png")
    plt.figure(figsize=(7, 7))
    ax = plt.gca()
    for segs, vals in perfile.values():
        vals_clamped = np.clip(vals, norm.vmin, norm.vmax)
        lc = LineCollection(segs, array=vals_clamped, cmap=cmap_name, norm=norm, linewidths=line_width*0.8)
        ax.add_collection(lc)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_aspect("equal", adjustable="box")
    cbar = plt.colorbar(lc)
    cbar.set_label(f"Step size ({units_label})")
    ax.set_title("All movies (step-size colored tracks)")
    plt.tight_layout()
    plt.savefig(pooled_png, dpi=600)
    plt.close()

    # combined PDF grid
    import matplotlib.backends.backend_pdf as backend_pdf
    n = len(pngs)
    ncols = int(math.ceil(math.sqrt(n)))
    nrows = int(math.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(4*ncols, 4*nrows))
    axes = np.array(axes).ravel()
    for ax, (fname, path) in zip(axes, pngs):
        img = plt.imread(path)
        ax.imshow(img)
        ax.axis("off")
        ax.set_title(os.path.basename(fname), fontsize=8)
    for ax in axes[len(pngs):]:
        ax.axis("off")
    plt.tight_layout()
    pdf_path = os.path.join(outdir, "tracks_stepsize_combined.pdf")
    pp = backend_pdf.PdfPages(pdf_path)
    pp.savefig(fig, dpi=600)
    pp.close()
    plt.close()
    print(f"[OK] Wrote {pdf_path}")


# --------------------- Package Integration ---------------------
def run_steps_tracks_analysis(work_dir: str, mode: str = "both", stepsize_max: float = 3.0,
                             bins_x: int = 150, bins_y: int = 150, count_cap: int = 300,
                             line_width: float = 0.7, min_track_length: int = 10,
                             brightness_col: str = "MEAN_INTENSITY_CH1", invert_lut_tracks: bool = False,
                             strip_datecodes: bool = True, filter_D_min: float = None,
                             filter_D_max: float = None, filter_alpha_min: float = None,
                             filter_alpha_max: float = None):
    """
    Run steps and tracks analysis with unified filtering.
    
    This function integrates with the GEMspa package's filtering system
    and processes TrackMate CSV files with the same filters as the rest of the pipeline.
    """
    import glob
    from .utils.data_io import load_trajectory_csv, condition_from_filename
    
    # Find all Traj_*.csv files
    files = sorted(glob.glob(os.path.join(work_dir, "Traj_*.csv")))
    if not files:
        print("[Steps & Tracks Analysis] No Traj_*.csv files found")
        return
    
    print(f"[Steps & Tracks Analysis] Found {len(files)} trajectory files")
    
    # Apply filtering if specified
    if any(f is not None for f in [filter_D_min, filter_D_max, filter_alpha_min, filter_alpha_max]):
        print("[Steps & Tracks Analysis] Applying filtering...")
        filtered_files = []
        for f in files:
            try:
                df = load_trajectory_csv(f)
                # Apply the same filtering logic as the rest of the package
                if filter_D_min is not None:
                    df = df[df.get('D_fit', 0) >= filter_D_min]
                if filter_D_max is not None:
                    df = df[df.get('D_fit', float('inf')) <= filter_D_max]
                if filter_alpha_min is not None:
                    df = df[df.get('alpha_fit', 0) >= filter_alpha_min]
                if filter_alpha_max is not None:
                    df = df[df.get('alpha_fit', float('inf')) <= filter_alpha_max]
                
                if len(df) > 0:
                    filtered_files.append(f)
            except Exception as e:
                print(f"[Steps & Tracks Analysis] Warning: Could not filter {os.path.basename(f)}: {e}")
                filtered_files.append(f)
        
        files = filtered_files
        print(f"[Steps & Tracks Analysis] {len(files)} files passed filtering")
    
    if not files:
        print("[Steps & Tracks Analysis] No files passed filtering")
        return
    
    # Run the analysis
    _run_analysis(files, work_dir, mode, stepsize_max, bins_x, bins_y, count_cap,
                  line_width, min_track_length, brightness_col, invert_lut_tracks, strip_datecodes)

def _run_analysis(files: list, work_dir: str, mode: str, stepsize_max: float,
                  bins_x: int, bins_y: int, count_cap: int, line_width: float,
                  min_track_length: int, brightness_col: str, invert_lut_tracks: bool,
                  strip_datecodes: bool):
    """Internal function to run the actual analysis."""
    try:
        detected_mode = detect_mode(files[0])
    except Exception as e:
        print(f"[Steps & Tracks Analysis] Error detecting mode: {e}")
        return
    
    print(f"[Steps & Tracks Analysis] Detected mode: {detected_mode}")
    
    # Heatmaps
    if mode in ("both", "heatmaps"):
        _run_heatmaps(files, work_dir, detected_mode, stepsize_max, bins_x, bins_y, 
                     count_cap, brightness_col, strip_datecodes)
    
    # Track overlays
    if mode in ("both", "tracks"):
        _run_track_overlays(files, work_dir, detected_mode, stepsize_max, line_width,
                           min_track_length, invert_lut_tracks, strip_datecodes)

def _run_heatmaps(files: list, work_dir: str, detected_mode: str, stepsize_max: float,
                  bins_x: int, bins_y: int, count_cap: int, brightness_col: str, strip_datecodes: bool):
    """Run heatmap analysis."""
    outdir_hm = os.path.join(work_dir, "brightness_stepsize")
    os.makedirs(outdir_hm, exist_ok=True)
    
    parts = []
    
    def _hm_worker(fpath: str):
        try:
            if detected_mode == "trackmate":
                df_raw = pd.read_csv(fpath, low_memory=False)
                part = compute_steps_from_trackmate(df_raw, brightness_override=brightness_col)
            else:
                part = load_steps_table(fpath)
            if part is not None and not part.empty:
                bn = os.path.splitext(os.path.basename(fpath))[0]
                if strip_datecodes:
                    bn = strip_datecode(bn)
                part["source_file"] = bn
                return part
        except Exception as e:
            print(f"[Steps & Tracks Analysis] Heatmap skip {os.path.basename(fpath)}: {e}")
        return None
    
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as ex:
        futs = [ex.submit(_hm_worker, f) for f in files]
        for fut in as_completed(futs):
            res = fut.result()
            if res is not None:
                parts.append(res)
    
    if not parts:
        print("[Steps & Tracks Analysis] No data for heatmaps.")
        return
    
    combined = pd.concat(parts, ignore_index=True).dropna()
    combined = combined[combined["step_size"] < stepsize_max]
    all_csv = os.path.join(outdir_hm, "steps_vs_brightness_all.csv")
    combined.to_csv(all_csv, index=False)
    print(f"[Steps & Tracks Analysis] Wrote {all_csv} ({len(combined)} rows)")
    
    ymin, ymax = float(combined["brightness"].min()), float(combined["brightness"].max())
    
    global_vmax = 0
    for fname, df in combined.groupby("source_file"):
        H = build_hist2d(df, stepsize_max, ymin, ymax, bins_x, bins_y)
        global_vmax = max(global_vmax, int(H.max()))
    global_vmax = min(max(global_vmax, 1), int(count_cap))
    print(f"[Steps & Tracks Analysis] Heatmap global vmax (capped): {global_vmax}")
    
    for fname, df in combined.groupby("source_file"):
        safe = fname.replace(" ", "_")
        out_png = os.path.join(outdir_hm, f"heatmap_{safe}.png")
        H = build_hist2d(df, stepsize_max, ymin, ymax, bins_x, bins_y)
        plot_heatmap_matrix(H, stepsize_max, ymin, ymax, global_vmax, title=fname, out_png=out_png)
        df.to_csv(os.path.join(outdir_hm, f"steps_vs_brightness_{safe}.csv"), index=False)
    
    # Pooled heatmap
    H_all = build_hist2d(combined, stepsize_max, ymin, ymax, bins_x, bins_y)
    pooled_png = os.path.join(outdir_hm, "heatmap_all.png")
    plot_heatmap_matrix(H_all, stepsize_max, ymin, ymax, global_vmax, title="All combined", out_png=pooled_png)
    
    print(f"[Steps & Tracks Analysis] Heatmaps → {outdir_hm}")

def _run_track_overlays(files: list, work_dir: str, detected_mode: str, stepsize_max: float,
                       line_width: float, min_track_length: int, invert_lut_tracks: bool, strip_datecodes: bool):
    """Run track overlay analysis."""
    if detected_mode != "trackmate":
        print("[Steps & Tracks Analysis] Track overlays require TrackMate CSVs; skipping.")
        return
    
    outdir_tr = os.path.join(work_dir, "tracks_stepsize_map")
    os.makedirs(outdir_tr, exist_ok=True)
    
    perfile = {}
    xmin = ymin = float("inf")
    xmax = ymax = float("-inf")
    
    def _track_worker(fpath: str):
        try:
            df_raw = pd.read_csv(fpath, low_memory=False)
            segs, vals = segments_from_trackmate(df_raw, min_track_length=min_track_length)
            if segs.size == 0:
                return (fpath, None, None, None)
            x_all = segs[:, :, 0].ravel()
            y_all = segs[:, :, 1].ravel()
            bounds = (float(np.nanmin(x_all)), float(np.nanmax(x_all)),
                      float(np.nanmin(y_all)), float(np.nanmax(y_all)))
            return (fpath, segs, vals, bounds)
        except Exception as e:
            print(f"[Steps & Tracks Analysis] Tracks skip {os.path.basename(fpath)}: {e}")
            return (fpath, None, None, None)
    
    results = []
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as ex:
        futs = [ex.submit(_track_worker, f) for f in files]
        for fut in as_completed(futs):
            results.append(fut.result())
    
    for f, segs, vals, bounds in results:
        if segs is None:
            continue
        perfile[f] = (segs, vals)
        xmin = min(xmin, bounds[0])
        xmax = max(xmax, bounds[1])
        ymin = min(ymin, bounds[2])
        ymax = max(ymax, bounds[3])
    
    if not perfile:
        print("[Steps & Tracks Analysis] No data for track overlays.")
        return
    
    cmap_name = "viridis_r" if invert_lut_tracks else "viridis"
    print(f"[Steps & Tracks Analysis] Track overlays colormap: {'inverted' if invert_lut_tracks else 'normal'} ({cmap_name})")
    plot_tracks_per_file(perfile, xmin, xmax, ymin, ymax, stepsize_max, line_width, outdir_tr, cmap_name)
    
    print(f"[Steps & Tracks Analysis] Track overlays → {outdir_tr}")

# --------------------- Main ---------------------
def main():
    ap = argparse.ArgumentParser(description="Generate heatmaps and/or step-size-colored track overlays.")
    ap.add_argument("input_dir")
    ap.add_argument("--pattern", default="*.csv")
    ap.add_argument("--make", choices=["both", "heatmaps", "tracks"], default="both")
    # Heatmap params
    ap.add_argument("--stepsize-max", type=float, default=3.0, help="Max step size for plots/LUT (pixels).")
    ap.add_argument("--bins-x", type=int, default=150)
    ap.add_argument("--bins-y", type=int, default=150)
    ap.add_argument("--count-cap", type=int, default=300)
    ap.add_argument("--units-label", default="pixels")
    # Track overlays
    ap.add_argument("--line-width", type=float, default=0.7)
    ap.add_argument("--invert-lut-tracks", action="store_true")
    ap.add_argument("--min-track-length", type=int, default=10)
    # Column overrides
    ap.add_argument("--brightness-col", default="MEAN_INTENSITY_CH1")
    ap.add_argument("--x-col", default=None)
    ap.add_argument("--y-col", default=None)
    # Filename/datecode handling
    ap.add_argument("--strip-datecodes", action="store_true", default=True)
    # Parallelism
    ap.add_argument("--workers", type=int, default=None, help="Max parallel worker threads (default: CPU count).")
    args = ap.parse_args()

    workers = args.workers or os.cpu_count() or 4
    workers = max(1, int(workers))

    indir = os.path.abspath(args.input_dir)
    if not os.path.isdir(indir):
        raise SystemExit(f"Input dir not found: {indir}")
    files = sorted(glob.glob(os.path.join(indir, args.pattern)))
    if not files:
        raise SystemExit(f"No files found matching {args.pattern} in {indir}")

    try:
        mode = detect_mode(files[0])
    except Exception as e:
        raise SystemExit(str(e))
    print(f"[INFO] Detected mode: {mode}")

    # ---------------- Heatmaps ----------------
    if args.make in ("both", "heatmaps"):
        outdir_hm = os.path.join(indir, "brightness_stepsize")
        os.makedirs(outdir_hm, exist_ok=True)

        parts = []

        def _hm_worker(fpath: str):
            try:
                if mode == "trackmate":
                    df_raw = pd.read_csv(fpath, low_memory=False)
                    part = compute_steps_from_trackmate(df_raw,
                                                        brightness_override=args.brightness_col,
                                                        x_override=args.x_col,
                                                        y_override=args.y_col)
                else:
                    part = load_steps_table(fpath)
                if part is not None and not part.empty:
                    bn = os.path.splitext(os.path.basename(fpath))[0]
                    if args.strip_datecodes:
                        bn = strip_datecode(bn)
                    part["source_file"] = bn
                    return part
            except Exception as e:
                print(f"[WARN] Heatmap skip {os.path.basename(fpath)}: {e}")
            return None

        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(_hm_worker, f) for f in files]
            for fut in as_completed(futs):
                res = fut.result()
                if res is not None:
                    parts.append(res)

        if not parts:
            print("[INFO] No data for heatmaps.")
        else:
            combined = pd.concat(parts, ignore_index=True).dropna()
            combined = combined[combined["step_size"] < args.stepsize_max]
            all_csv = os.path.join(outdir_hm, "steps_vs_brightness_all.csv")
            combined.to_csv(all_csv, index=False)
            print(f"[OK] Wrote {all_csv} ({len(combined)} rows)")

            ymin, ymax = float(combined["brightness"].min()), float(combined["brightness"].max())

            global_vmax = 0
            for fname, df in combined.groupby("source_file"):
                H = build_hist2d(df, args.stepsize_max, ymin, ymax, args.bins_x, args.bins_y)
                global_vmax = max(global_vmax, int(H.max()))
            global_vmax = min(max(global_vmax, 1), int(args.count_cap))
            print(f"[INFO] Heatmap global vmax (capped): {global_vmax}")

            pngs = []
            for fname, df in combined.groupby("source_file"):
                safe = fname.replace(" ", "_")
                out_png = os.path.join(outdir_hm, f"heatmap_{safe}.png")
                H = build_hist2d(df, args.stepsize_max, ymin, ymax, args.bins_x, args.bins_y)
                plot_heatmap_matrix(H, args.stepsize_max, ymin, ymax, global_vmax, title=fname, out_png=out_png, units_label=args.units_label)
                df.to_csv(os.path.join(outdir_hm, f"steps_vs_brightness_{safe}.csv"), index=False)
                pngs.append((fname, out_png))

            # pooled heatmap (PNG + pooled-only PDF)
            H_all = build_hist2d(combined, args.stepsize_max, ymin, ymax, args.bins_x, args.bins_y)
            pooled_png = os.path.join(outdir_hm, "heatmap_all.png")
            plot_heatmap_matrix(H_all, args.stepsize_max, ymin, ymax, global_vmax, title="All combined",
                                out_png=pooled_png, units_label=args.units_label)

            import matplotlib.backends.backend_pdf as backend_pdf
            fig = plt.figure(figsize=(6,5))
            ax = fig.add_subplot(111)
            Hc = np.clip(H_all, 0, global_vmax)
            im = ax.imshow(Hc.T, origin="lower", aspect="auto",
                           extent=[0, args.stepsize_max, ymin, ymax],
                           cmap="viridis", norm=Normalize(vmin=0, vmax=global_vmax))
            sat = Hc.T >= (global_vmax - 1e-9)
            if np.any(sat):
                overlay = np.zeros((*sat.shape, 4))
                overlay[sat] = [1, 0, 0, 1]
                ax.imshow(overlay, origin="lower", aspect="auto",
                          extent=[0, args.stepsize_max, ymin, ymax])
            cbar = fig.colorbar(im, ax=ax)
            cbar.set_label(f"Counts (cap={global_vmax}; red=saturated)")
            ax.set_xlabel(f"Step size ({args.units_label})")
            ax.set_ylabel("Brightness (a.u.)")
            ax.set_title("All combined")
            fig.tight_layout()
            pooled_pdf = os.path.join(outdir_hm, "heatmap_all_only.pdf")
            pp = backend_pdf.PdfPages(pooled_pdf)
            pp.savefig(fig, dpi=600)
            pp.close()
            plt.close(fig)
            print(f"[OK] Wrote {pooled_pdf}")

            # combined PDF grid of per-file heatmaps
            n = len(pngs)
            if n > 0:
                ncols = int(math.ceil(math.sqrt(n)))
                nrows = int(math.ceil(n / ncols))
                fig, axes = plt.subplots(nrows, ncols, figsize=(4*ncols, 4*nrows))
                axes = np.array(axes).ravel()
                for ax, (fname, path) in zip(axes, pngs):
                    img = plt.imread(path)
                    ax.imshow(img)
                    ax.axis("off")
                    ax.set_title(os.path.basename(fname), fontsize=8)
                for ax in axes[len(pngs):]:
                    ax.axis("off")
                plt.tight_layout()
                grid_pdf_path = os.path.join(outdir_hm, "heatmaps_combined.pdf")
                pp = backend_pdf.PdfPages(grid_pdf_path)
                pp.savefig(fig, dpi=600)
                pp.close()
                plt.close()
                print(f"[OK] Wrote {grid_pdf_path}")

    # ---------------- Track overlays ----------------
    if args.make in ("both", "tracks"):
        outdir_tr = os.path.join(indir, "tracks_stepsize_map")
        os.makedirs(outdir_tr, exist_ok=True)

        if mode != "trackmate":
            print("[INFO] Track overlays require TrackMate CSVs; skipping tracks because inputs look like steps tables.")
        else:
            perfile = {}
            xmin = ymin = float("inf")
            xmax = ymax = float("-inf")

            def _track_worker(fpath: str):
                try:
                    df_raw = pd.read_csv(fpath, low_memory=False)
                    segs, vals = segments_from_trackmate(df_raw, min_track_length=args.min_track_length)
                    if segs.size == 0:
                        return (fpath, None, None, None)
                    x_all = segs[:, :, 0].ravel()
                    y_all = segs[:, :, 1].ravel()
                    bounds = (float(np.nanmin(x_all)), float(np.nanmax(x_all)),
                              float(np.nanmin(y_all)), float(np.nanmax(y_all)))
                    return (fpath, segs, vals, bounds)
                except Exception as e:
                    print(f"[WARN] Tracks skip {os.path.basename(fpath)}: {e}")
                    return (fpath, None, None, None)

            results = []
            with ThreadPoolExecutor(max_workers=workers) as ex:
                futs = [ex.submit(_track_worker, f) for f in files]
                for fut in as_completed(futs):
                    results.append(fut.result())

            for f, segs, vals, bounds in results:
                if segs is None:
                    print(f"[INFO] No segments in {os.path.basename(f)} after min-track-length filtering")
                    continue
                perfile[f] = (segs, vals)
                xmin = min(xmin, bounds[0])
                xmax = max(xmax, bounds[1])
                ymin = min(ymin, bounds[2])
                ymax = max(ymax, bounds[3])

            if not perfile:
                print("[INFO] No data for track overlays.")
            else:
                cmap_name = "viridis_r" if args.invert_lut_tracks else "viridis"
                print(f"[INFO] Track overlays colormap: {'inverted' if args.invert_lut_tracks else 'normal'} ({cmap_name}); min-track-length = {args.min_track_length}")
                plot_tracks_per_file(perfile, xmin, xmax, ymin, ymax,
                                     stepsize_max=args.stepsize_max,
                                     line_width=args.line_width,
                                     outdir=outdir_tr,
                                     cmap_name=cmap_name,
                                     units_label=args.units_label)


if __name__ == "__main__":
    main()
