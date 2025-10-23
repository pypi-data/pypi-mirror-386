#!/usr/bin/env python3
"""
Shared data I/O utilities for GEMspa.
Consolidates CSV loading, TrackMate processing, and column normalization.
"""
import os
import re
import glob
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd

# TrackMate file patterns
TRACKMATE_PATTERNS = [
    "Spots in tracks statistics.csv",
    "spots in tracks statistics.csv", 
    "All spots statistics.csv",
    "all spots statistics.csv",
]

def find_trackmate_spots_csv(path: str) -> Optional[str]:
    """Find TrackMate spots CSV file in directory or return path if it's a CSV."""
    p = Path(path)
    if p.is_file() and p.suffix.lower() == ".csv":
        return str(p)
    if p.is_dir():
        for name in TRACKMATE_PATTERNS:
            cand = p / name
            if cand.exists():
                return str(cand)
        # Fallback: look for any CSV with plausible columns
        for cand in p.glob("*.csv"):
            try:
                df = pd.read_csv(str(cand), sep=None, engine="python")
            except Exception:
                continue
            low = [c.lower().strip() for c in df.columns]
            if (any(c in low for c in ("position_x", "x", "x [µm]", "x [um]")) and
                any(c in low for c in ("position_y", "y", "y [µm]", "y [um]")) and
                any(c in low for c in ("frame", "spot_frame")) and
                any(c in low for c in ("track_id", "track id", "trajectory"))):
                return str(cand)
    return None

def _find_column(df: pd.DataFrame, *candidates: str) -> Optional[str]:
    """Find first matching column (case-insensitive)."""
    cols_lower = {c.lower(): c for c in df.columns}
    for candidate in candidates:
        if candidate in cols_lower:
            return cols_lower[candidate]
    return None

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names to standard format (track_id, frame, x, y).
    Preserves all other columns as-is.
    """
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    
    # Remove duplicate columns first to avoid issues
    df = df.loc[:, ~df.columns.duplicated()].copy()
    
    # Find required columns
    x_col = _find_column(df, "position_x", "x", "x [µm]", "x [um]", "x (pixel)", "x (µm)", "x (um)")
    y_col = _find_column(df, "position_y", "y", "y [µm]", "y [um]", "y (pixel)", "y (µm)", "y (um)")
    f_col = _find_column(df, "frame", "spot_frame", "t", "frame index", "frame_index", "frame id", "frameid")
    t_col = _find_column(df, "track_id", "track id", "trajectory", "trackindex", "track_index", "id_track")
    
    # Validate required columns
    missing = []
    if not x_col: missing.append("x")
    if not y_col: missing.append("y") 
    if not f_col: missing.append("frame")
    if not t_col: missing.append("track_id")
    
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Rename to standard names
    rename_map = {}
    if x_col != "x": rename_map[x_col] = "x"
    if y_col != "y": rename_map[y_col] = "y"
    if f_col != "frame": rename_map[f_col] = "frame"
    if t_col != "track_id": rename_map[t_col] = "track_id"
    
    if rename_map:
        df = df.rename(columns=rename_map)
    
    # Convert to numeric and clean - only if needed
    for col in ["x", "y", "frame", "track_id"]:
        if col in df.columns:
            # Check if already numeric
            if pd.api.types.is_numeric_dtype(df[col]):
                continue
            # Convert to numeric if not already
            try:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            except Exception as e:
                print(f"Warning: Could not convert column {col} to numeric: {e}")
                continue
    
    df = df.dropna(subset=["x", "y", "frame", "track_id"]).copy()
    df["frame"] = df["frame"].astype("int64")
    df["track_id"] = df["track_id"].astype("int64")
    
    return df

def clean_trackmate_csv(csv_path: str) -> pd.DataFrame:
    """Load and clean TrackMate CSV to GEMspa format."""
    try:
        df = pd.read_csv(csv_path, sep=None, engine="python")
    except Exception:
        df = pd.read_csv(csv_path)
    
    return normalize_columns(df)

def load_trajectory_csv(file_path: str) -> pd.DataFrame:
    """
    Load trajectory CSV with automatic TrackMate detection and cleaning.
    Returns DataFrame with normalized columns (track_id, frame, x, y) plus extras.
    """
    # Load the CSV file
    try:
        df = pd.read_csv(file_path, sep=None, engine="python")
    except Exception:
        df = pd.read_csv(file_path)
    
    # Check if columns are already normalized (case-insensitive)
    required_cols = {"track_id", "frame", "x", "y"}
    cols_lower = {c.lower() for c in df.columns}
    
    if required_cols.issubset(cols_lower):
        # Already has normalized columns, just clean them
        return normalize_columns(df)
    else:
        # Try TrackMate cleaning
        return clean_trackmate_csv(file_path)

def condition_from_filename(filename: str) -> str:
    """Extract condition name from filename, removing date codes and replicate numbers."""
    base = os.path.splitext(os.path.basename(filename))[0]
    # Remove Traj_ prefix if present
    if base.startswith("Traj_"):
        base = base[5:]
    
    # Remove date codes (YYYYMMDD_ or YYMMDD_ at the beginning)
    base = re.sub(r"^[0-9]{6,8}_", "", base)
    
    # Remove trailing numbers (replicate)
    base = re.sub(r"_[0-9]+$", "", base)
    
    return base

def collect_condition_files(work_dir: str, condition: str) -> List[str]:
    """Collect all CSV files for a given condition."""
    patterns = [
        os.path.join(work_dir, f"Traj_{condition}_*.csv"),
        os.path.join(work_dir, f"{condition}_*.csv"),
        os.path.join(work_dir, f"{condition}_*", f"Traj_{condition}_*.csv"),
        os.path.join(work_dir, f"{condition}_*", f"{condition}_*.csv"),
    ]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(pattern))
    return sorted(set(files))
