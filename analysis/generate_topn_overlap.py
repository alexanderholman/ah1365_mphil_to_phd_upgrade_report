import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

COMPARISONS = [
    {'comparison': 'dft@dft_vs_mlp@mlp', 'dft': 'dft@dft_vs_mlp@mlp_rank_dft', 'mlp': 'dft@dft_vs_mlp@mlp_rank_mlp'},
    {'comparison': 'dft@dft_vs_dft@mlp', 'dft': 'dft@dft_vs_dft@mlp_rank_dft', 'mlp': 'dft@dft_vs_dft@mlp_rank_mlp'},
    {'comparison': 'mlp@dft_vs_mlp@mlp', 'dft': 'mlp@dft_vs_mlp@mlp_rank_dft', 'mlp': 'mlp@dft_vs_mlp@mlp_rank_mlp'},
]

def compute_topn_overlap(df, dft_col, mlp_col, n):
    df_valid = df[['name', dft_col, mlp_col]].dropna()
    if len(df_valid) < n:
        return None  # skip if not enough data
    dft_top_names = df_valid.nsmallest(n, dft_col)['name'].tolist()
    mlp_top_names = df_valid.nsmallest(n, mlp_col)['name'].tolist()
    overlaps = set(dft_top_names).intersection(set(mlp_top_names))
    overlap = len(overlaps)
    return overlap / n if n > 0 else 0.0

def plot_topn_overlaps(df, topns, output_dir, prefix):
    df = df[df['is_broken'].astype(str).str.lower() != 'true']

    data = []
    for comp in COMPARISONS:
        label = comp['comparison']
        dft_col = comp['dft']
        mlp_col = comp['mlp']
        for n in topns:
            score = compute_topn_overlap(df, dft_col, mlp_col, n)
            if score is not None:
                data.append({'comparison': label, 'topn': n, 'overlap': score})

    df_plot = pd.DataFrame(data)
    if df_plot.empty:
        print("⚠️ No valid comparisons available. No plot will be created.")
        return

    comparisons = [c['comparison'] for c in COMPARISONS if c['comparison'] in df_plot['comparison'].values]
    topns_present = sorted(df_plot['topn'].unique())
    x = np.arange(len(comparisons))
    bar_width = 1 / (len(topns_present) + 1)
    fig, ax = plt.subplots(figsize=(9, 6))

    for i, n in enumerate(topns_present):
        subset = df_plot[df_plot['topn'] == n]
        if subset.empty:
            continue
        offsets = x + (i - (len(topns_present) - 1) / 2) * bar_width
        ax.bar(offsets, subset['overlap'], width=bar_width, label=f"Top-{n}", alpha=0.85)

    ax.set_ylabel("Top-N Overlap Fraction")
    ax.set_xlabel("Comparison")
    ax.set_ylim(0, 1.05)
    ax.set_xticks(x)
    ax.set_xticklabels(comparisons, rotation=15)
    ax.set_title("Top-N Agreement Between DFT and MLP Rankings")
    ax.legend(title="N")

    fig.tight_layout()
    outpath = output_dir / f"{prefix}_topn_overlap.png"
    fig.savefig(outpath, dpi=300)

    print(f"✅ Saved plot: {outpath}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results', required=True, type=Path, help='results.csv file')
    parser.add_argument('--output-dir', type=Path, default=Path('plots'), help='Where to save output plots')
    parser.add_argument('--topns', type=int, nargs='+', default=[5, 10, 20], help='Top-N values to check for overlap')
    args = parser.parse_args()

    df = pd.read_csv(args.results)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    prefix = args.results.stem

    plot_topn_overlaps(df, args.topns, args.output_dir, prefix)

if __name__ == '__main__':
    main()
