import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

def linear_fit(x, a, b):
    return a * x + b

def plot_compute_times(df, output_dir, prefix):
    # Filter and group
    df_valid = df.dropna(subset=[
        "interface_electron_n",
        "interface_compute_time_per_electron_dft",
        "interface_compute_time_per_electron_mlp"
    ])

    grouped = df_valid.groupby("interface_electron_n").agg({
        "interface_compute_time_per_electron_dft": "mean",
        "interface_compute_time_per_electron_mlp": "mean"
    }).reset_index()

    # Fit lines
    x_vals = grouped["interface_electron_n"].values
    y_dft = grouped["interface_compute_time_per_electron_dft"].values
    y_mlp = grouped["interface_compute_time_per_electron_mlp"].values

    popt_dft, _ = curve_fit(linear_fit, x_vals, y_dft)
    popt_mlp, _ = curve_fit(linear_fit, x_vals, y_mlp)

    # Plot
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(x_vals, y_dft, label="DFT", marker="o")
    ax.plot(x_vals, y_mlp, label="MLP", marker="x")

    # Add trajectory lines with labels
    dft_trend = linear_fit(x_vals, *popt_dft)
    mlp_trend = linear_fit(x_vals, *popt_mlp)
    dft_trend_formula = f"y={popt_dft[0]:.3e}x+{popt_dft[1]:.3e}"
    mlp_trend_formula = f"y={popt_mlp[0]:.3e}x+{popt_mlp[1]:.3e}"
    print(f"DFT Trend: {dft_trend_formula}")
    print(f"MLP Trend: {mlp_trend_formula}")
    ax.plot(x_vals, dft_trend, linestyle="--", color="blue", label=f"DFT Trend ({dft_trend_formula})")
    ax.plot(x_vals, mlp_trend, linestyle="--", color="orange", label=f"MLP Trend ({mlp_trend_formula})")

    ax.set_xlabel("Number of Electrons (interface_electron_n)")
    ax.set_ylabel("Compute Time per Electron (s)")
    ax.set_title("Average Compute Time per Electron vs. Electron Count")
    ax.legend()
    ax.grid(True)

    fig.tight_layout()
    outpath = output_dir / f"{prefix}_compute_time_comparison.png"
    fig.savefig(outpath, dpi=300)

    print(f"✅ Saved plot: {outpath}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results', required=True, type=Path, help='results.csv file')
    parser.add_argument('--output-dir', type=Path, default=Path('plots'), help='Where to save output plots')
    args = parser.parse_args()

    df = pd.read_csv(args.results)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    prefix = args.results.stem

    plot_compute_times(df, args.output_dir, prefix)

if __name__ == '__main__':
    main()
