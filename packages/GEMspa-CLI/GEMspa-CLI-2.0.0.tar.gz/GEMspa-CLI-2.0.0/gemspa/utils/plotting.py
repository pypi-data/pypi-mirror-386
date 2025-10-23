#!/usr/bin/env python3
"""
Shared plotting utilities for GEMspa.
Consolidates common plotting functions with consistent styling.
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import LogLocator, LogFormatter
from scipy.stats import ks_2samp
from typing import Optional, Tuple, Dict, Any, List

# Default styling
plt.rcParams.setdefault("font.size", 12)
DEFAULT_DPI = 300
DEFAULT_FIGSIZE = (8, 6)

def save_figure(fig, output_path: str, dpi: int = DEFAULT_DPI, bbox_inches: str = "tight") -> None:
    """Save figure with consistent settings."""
    fig.savefig(output_path, dpi=dpi, bbox_inches=bbox_inches)
    plt.close(fig)

def plot_histogram(data: np.ndarray, output_path: str, title: str, xlabel: str, 
                  bins: int = 30, log_scale: bool = False, density: bool = True,
                  figsize: Tuple[int, int] = DEFAULT_FIGSIZE) -> None:
    """Plot histogram with consistent styling."""
    fig, ax = plt.subplots(figsize=figsize)
    
    if log_scale:
        # Use log-spaced bins for log scale
        if np.all(data > 0):
            bins = np.logspace(np.log10(data.min()), np.log10(data.max()), bins)
        ax.set_xscale('log')
    
    ax.hist(data, bins=bins, density=density, edgecolor='black', alpha=0.7)
    ax.set_xlabel(xlabel)
    ax.set_ylabel('Density' if density else 'Count')
    ax.set_title(title)
    
    if log_scale:
        ax.yaxis.set_major_locator(LogLocator(base=10))
        ax.yaxis.set_major_formatter(LogFormatter(base=10))
    
    fig.tight_layout()
    save_figure(fig, output_path)

def plot_boxplot(data_dict: Dict[str, np.ndarray], output_path: str, title: str, 
                 ylabel: str, violin: bool = False, figsize: Tuple[int, int] = DEFAULT_FIGSIZE) -> None:
    """Plot boxplot or violin plot with consistent styling."""
    fig, ax = plt.subplots(figsize=figsize)
    
    keys = sorted(data_dict.keys())
    data = [data_dict[k] for k in keys]
    
    if violin:
        parts = ax.violinplot(data, showmeans=True, showextrema=False)
    else:
        parts = ax.boxplot(data, notch=True, showfliers=False)
    
    ax.set_xticks(range(1, len(keys) + 1))
    ax.set_xticklabels(keys, rotation=30, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    
    fig.tight_layout()
    save_figure(fig, output_path)

def plot_scatter(x: np.ndarray, y: np.ndarray, output_path: str, title: str,
                xlabel: str, ylabel: str, alpha: float = 0.6, 
                figsize: Tuple[int, int] = DEFAULT_FIGSIZE) -> None:
    """Plot scatter plot with consistent styling."""
    fig, ax = plt.subplots(figsize=figsize)
    ax.scatter(x, y, alpha=alpha)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    fig.tight_layout()
    save_figure(fig, output_path)

def plot_ks_comparison(data_a: np.ndarray, data_b: np.ndarray, output_path: str,
                      title: str, xlabel: str = "Value", figsize: Tuple[int, int] = DEFAULT_FIGSIZE) -> None:
    """Plot KS test comparison between two datasets."""
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot histograms
    ax.hist(data_a, bins=30, alpha=0.5, label="Group A", density=True)
    ax.hist(data_b, bins=30, alpha=0.5, label="Group B", density=True)
    
    # Add KS test result
    try:
        ks_stat, p_value = ks_2samp(data_a, data_b)
        ax.text(0.02, 0.98, f"KS p-value: {p_value:.2e}", 
                transform=ax.transAxes, va="top", ha="left",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    except Exception:
        pass
    
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Density")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    save_figure(fig, output_path)

def plot_msd_linear(tau: np.ndarray, msd: np.ndarray, output_path: str, 
                   title: str, D_est: Optional[float] = None, 
                   figsize: Tuple[int, int] = DEFAULT_FIGSIZE) -> None:
    """Plot MSD vs tau (linear scale)."""
    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(tau, msd, 'o', ms=3)
    ax.set_xlabel('τ (s)')
    ax.set_ylabel('MSD (μm²)')
    
    if D_est is not None:
        ax.set_title(f'{title}\nD ≈ {D_est:.3g} μm²/s')
    else:
        ax.set_title(title)
    
    fig.tight_layout()
    save_figure(fig, output_path)

def plot_msd_loglog(tau: np.ndarray, msd: np.ndarray, output_path: str,
                   title: str, alpha_est: Optional[float] = None,
                   figsize: Tuple[int, int] = DEFAULT_FIGSIZE) -> None:
    """Plot MSD vs tau (log-log scale)."""
    fig, ax = plt.subplots(figsize=figsize)
    
    # Only plot positive values
    mask = (tau > 0) & (msd > 0)
    if mask.any():
        ax.plot(np.log10(tau[mask]), msd[mask], 'o', ms=3)
        ax.set_yscale('log')
        ax.set_xlabel('log₁₀ τ (s)')
        ax.set_ylabel('MSD (μm²)')
        
        if alpha_est is not None:
            ax.set_title(f'{title}\nα ≈ {alpha_est:.3g}')
        else:
            ax.set_title(title)
    
    fig.tight_layout()
    save_figure(fig, output_path)

def plot_step_kde(df: pd.DataFrame, output_path: str, title: str,
                 xlim: Optional[Tuple[float, float]] = None,
                 ylim: Optional[Tuple[float, float]] = None,
                 figsize: Tuple[int, int] = (10, 7)) -> Tuple[Tuple, float]:
    """
    Plot KDE for step sizes by group and tau.
    Returns (xlim_used, ymax_used) for consistent axes.
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Default limits
    if xlim is None:
        xlim = (0.0, 3.0)
    if ylim is None:
        ylim = (1e-05, None)
    
    groups = df['group'].unique() if 'group' in df.columns else ['default']
    taus = sorted(df['tlag'].unique()) if 'tlag' in df.columns else [1]
    
    palette = sns.color_palette("colorblind", n_colors=len(taus))
    colors = dict(zip(taus, palette))
    
    plotted = False
    for tau in taus:
        if 'group' in df.columns and 'tlag' in df.columns:
            sub_df = df[(df['group'] == groups[0]) & (df['tlag'] == tau)]
        else:
            sub_df = df
        
        vals = sub_df['step_size'].to_numpy()
        vals = vals[np.isfinite(vals)]
        
        if vals.size < 3 or np.allclose(vals, vals[0]):
            continue
        
        sns.kdeplot(
            x=vals,
            fill=False,
            bw_method="silverman",
            bw_adjust=1.2,
            warn_singular=False,
            common_norm=False,
            color=colors[tau],
            label=f"τ={int(tau)}",
            ax=ax
        )
        plotted = True
    
    if not plotted:
        plt.close(fig)
        return (0, 0), 0.0
    
    ax.set_xlabel("Step Size (μm)")
    ax.set_yscale("log")
    ax.yaxis.set_major_locator(LogLocator(base=10))
    ax.yaxis.set_major_formatter(LogFormatter(base=10))
    ax.set_ylabel("Density (log₁₀)")
    ax.set_title(title)
    ax.legend(loc="upper right", fontsize=9)
    
    if xlim is not None:
        ax.set_xlim(xlim)
    if ylim is not None:
        if ylim[1] is None:
            ax.set_ylim(bottom=ylim[0])
        else:
            ax.set_ylim(ylim)
    
    fig.tight_layout()
    save_figure(fig, output_path)
    
    # Return actual limits used
    return ax.get_xlim(), ax.get_ylim()[1]
