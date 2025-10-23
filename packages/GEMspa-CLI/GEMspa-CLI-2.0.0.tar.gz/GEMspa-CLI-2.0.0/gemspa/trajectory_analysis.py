#!/usr/bin/env python3
# gemspa/trajectory_analysis.py  (flexible + TrackMate-aware)
import os, re, datetime
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from joblib import Parallel, delayed, parallel_backend
from multiprocessing import cpu_count

try:
    from .msd_diffusion import msd_diffusion, compute_track_msd, fit_linear_and_loglog
    from .rainbow_tracks import draw_rainbow_tracks
    from .utils.data_io import load_trajectory_csv, find_trackmate_spots_csv
    from .utils.plotting import plot_msd_linear, plot_msd_loglog, plot_histogram, plot_scatter
except ImportError:
    # Fallback for when running as standalone script
    try:
        from .msd_diffusion import msd_diffusion, compute_track_msd, fit_linear_and_loglog  # type: ignore
    except ImportError:
        # Create minimal fallback functions
        class msd_diffusion:  # type: ignore
            def __init__(self, save_dir="."): self.save_dir = save_dir
            def fit_msd(self, msd_vals, time_step=None): return 0.0, 1.0, 0.0
        def compute_track_msd(coords, max_lag): return np.zeros(max_lag)
        def fit_linear_and_loglog(tau, msd): return 0.0, 1.0, 0.0
    
    def draw_rainbow_tracks(*args, **kwargs): print("[rainbow] skipped")
    
    try:
        from utils.data_io import load_trajectory_csv, find_trackmate_spots_csv  # type: ignore
        from utils.plotting import plot_msd_linear, plot_msd_loglog, plot_histogram, plot_scatter  # type: ignore
    except ImportError:
        # Minimal fallback functions
        def load_trajectory_csv(file_path): return pd.read_csv(file_path)
        def find_trackmate_spots_csv(path): return None
        def plot_msd_linear(*args, **kwargs): pass
        def plot_msd_loglog(*args, **kwargs): pass
        def plot_histogram(*args, **kwargs): pass
        def plot_scatter(*args, **kwargs): pass

REQUIRED = ('track_id','frame','x','y')

class trajectory_analysis:
    def __init__(
        self,
        data_file,
        results_dir='.',
        condition=None,
        time_step=0.010,
        micron_per_px=0.11,
        ts_resolution=0.005,
        min_track_len_linfit=11,
        tlag_cutoff_linfit=10,
        make_rainbow_tracks=False,
        img_file_prefix='MAX_',
        rainbow_min_D=0.0,
        rainbow_max_D=2.0,
        rainbow_colormap='viridis',
        rainbow_scale=1.0,
        rainbow_dpi=200,
        n_jobs=1,
        threads_per_rep=None,
        log_file=None
    ):
        self.n_jobs = n_jobs
        self.threads_per_rep = threads_per_rep or max(1, cpu_count() // max(1, n_jobs))
        self.results_dir = results_dir
        os.makedirs(self.results_dir, exist_ok=True)

        # Use consolidated data loading
        df = load_trajectory_csv(str(data_file))
        df = df.sort_values(['track_id','frame']).copy()

        base = os.path.splitext(os.path.basename(data_file))[0]
        self.condition            = condition or re.sub(r'_[0-9]+$', '', base)
        self.time_step            = time_step
        self.micron_per_px        = micron_per_px
        self.ts_resolution        = ts_resolution
        self.min_track_len_linfit = min_track_len_linfit
        self.tlag_cutoff_linfit   = tlag_cutoff_linfit
        self.make_rainbow_tracks  = make_rainbow_tracks
        self.img_prefix           = img_file_prefix
        self.rainbow_min_D        = rainbow_min_D
        self.rainbow_max_D        = rainbow_max_D
        self.rainbow_colormap     = rainbow_colormap
        self.rainbow_scale        = rainbow_scale
        self.rainbow_dpi          = rainbow_dpi
        self.rainbow_line_width   = 0.1

        self.raw_df = df.copy()
        self.raw_df['condition'] = self.condition
        self.msd_processor = msd_diffusion(save_dir=self.results_dir)

        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log = open(os.path.join(self.results_dir, f"{base}_{ts}.log"), 'w')

    def _one_track(self, grp: pd.DataFrame):
        coords = grp[['x','y']].to_numpy() * self.micron_per_px
        L = min(self.tlag_cutoff_linfit, max(1, coords.shape[0]-1))
        return compute_track_msd(coords, L)

    def calculate_msd_and_diffusion(self):
        tracks = [g for _,g in self.raw_df.groupby('track_id') if len(g) >= self.min_track_len_linfit]
        if not tracks:
            raise RuntimeError(f"No tracks pass min length >= {self.min_track_len_linfit}")
        with parallel_backend('threading'):
            msd_list = Parallel(n_jobs=self.threads_per_rep)(delayed(self._one_track)(g) for g in tracks)
        L = min(len(v) for v in msd_list)
        tau = np.arange(1, L+1, dtype=float) * self.time_step
        msd_mat = np.vstack([v[:L] for v in msd_list])
        ens = np.nanmean(msd_mat, axis=0)
        # plots using consolidated plotting functions
        m = (tau>0) & np.isfinite(ens) & (ens>=0)
        D_est = ens[m][-1] / (4.0 * tau[m][-1]) if m.any() else 0.0
        alpha_est = np.polyfit(np.log10(tau[m & (ens>0)]), np.log10(ens[m & (ens>0)]), 1)[0] if np.count_nonzero(m & (ens>0)) >= 2 else 0.0
        
        plot_msd_linear(tau, ens, os.path.join(self.results_dir,'msd_vs_tau.png'), 
                       f'ens-avg MSD  D≈{D_est:.3g} μm²/s', D_est)
        plot_msd_loglog(tau, ens, os.path.join(self.results_dir,'msd_vs_tau_loglog.png'),
                       f'ens-avg log–log MSD  α≈{alpha_est:.3g}', alpha_est)
        # per-track results using consolidated fitting
        rows = []
        for grp, vec in zip(tracks, msd_list):
            Lt = len(vec)
            tau_t = np.arange(1, Lt+1, dtype=float) * self.time_step
            D_fit, alpha_fit, r2 = fit_linear_and_loglog(tau_t, vec)
            rows.append((int(grp['track_id'].iloc[0]), D_fit, alpha_fit, r2))

        # Save per-track table for downstream ensemble filtering
        self.results_df = pd.DataFrame(rows, columns=['track_id','D_fit','alpha_fit','r2_fit'])
        self.results_df.to_csv(os.path.join(self.results_dir, 'msd_results.csv'), index=False)


    def export_step_sizes(self, max_tlag=None):
        df = self.raw_df[['track_id','frame','x','y']].copy()
        df['x'] *= self.micron_per_px; df['y'] *= self.micron_per_px
        arr = df.sort_values(['track_id','frame']).to_numpy()
        self.msd_processor.set_track_data(arr)
        if max_tlag is not None: self.msd_processor.max_tlag_step_size = max_tlag
        self.msd_processor.step_sizes_and_angles()
        ss = self.msd_processor.save_step_sizes(file_name='all_data_step_sizes.txt')
        ss = ss.rename(columns={'t':'tlag'}); ss.insert(1,'group', self.condition)
        out = os.path.join(self.results_dir,'all_data_step_sizes.txt')
        ss.to_csv(out, sep='\t', index=False)

    def make_plot(self):
        if not hasattr(self, 'results_df') or self.results_df.empty:
            return
        d = self.results_df['D_fit']
        plot_histogram(d, os.path.join(self.results_dir,'D_fit_distribution.png'), 
                      f'D_fit ({self.condition})', 'D_fit (μm²/s)', log_scale=True)

    def make_scatter(self):
        if not hasattr(self, 'results_df') or self.results_df.empty:
            return
        d = self.results_df['D_fit'].replace({0: np.nan})
        plot_scatter(np.log10(d), self.results_df['alpha_fit'], 
                    os.path.join(self.results_dir,'alpha_vs_logD.png'),
                    f'α vs log D ({self.condition})', 'log10(D_fit)', 'alpha_fit')
