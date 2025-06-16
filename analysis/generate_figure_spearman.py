import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.lines as mlines

MARKERS = {
    'dft@dft_vs_mlp@mlp': 'o',
    'dft@dft_vs_dft@mlp': 's',
    'mlp@dft_vs_mlp@mlp': 'D'
}

COMPARISONS = [
    'dft@dft_vs_mlp@mlp',
    'dft@dft_vs_dft@mlp',
    'mlp@dft_vs_mlp@mlp',
]

MODES = ['valid', 'invalid', 'both', 'all']

def normalise_rgb(row, prefix):
    val = row.get(prefix, '')
    if isinstance(val, str) and val.startswith('('):
        try:
            return eval(val)
        except Exception:
            pass
    return (0.5, 0.5, 0.5)  # fallback to grey if invalid

def get_filtered_data(df, flag_col, broken_col):
    return df[(df[flag_col].astype(str).str.lower() == 'true') &
              (df[broken_col].astype(str).str.lower() != 'true')].copy()

def marker_legend(used_comparisons):
    return [mlines.Line2D([], [], color='black', marker=MARKERS[cmp], linestyle='None', label=label)
            for cmp, label in zip(COMPARISONS, ['dft@dft vs mlp@mlp', 'dft@dft vs dft@mlp', 'mlp@dft vs mlp@mlp'])
            if cmp in used_comparisons]

def plot_spearman(df, comparison, rank_dft_col, rank_mlp_col, flag_col, broken_col, output_dir, mode, prefix):
    dist_col = comparison + '_rank_dist'
    df = get_filtered_data(df, flag_col, broken_col)
    if df.empty:
        print(f"⚠️ No valid data for comparison '{comparison}'")
        return

    modes_to_run = MODES[:-1] if mode == 'all' else [mode]

    for current_mode in modes_to_run:
        mode_df = df.copy()
        if current_mode == 'valid':
            mode_df = mode_df[mode_df['is_valid'].astype(str).str.lower() == 'true']
        elif current_mode == 'invalid':
            mode_df = mode_df[mode_df['is_valid'].astype(str).str.lower() != 'true']

        if mode_df.empty:
            print(f"⚠️ No data after applying mode '{current_mode}' for comparison '{comparison}'")
            continue

        minv = min(mode_df[rank_dft_col].min(), mode_df[rank_mlp_col].min())
        maxv = max(mode_df[rank_dft_col].max(), mode_df[rank_mlp_col].max())

        fig, ax1 = plt.subplots(figsize=(7, 6))

        if current_mode in ['valid', 'both']:
            df_valid = mode_df[mode_df['is_valid'].astype(str).str.lower() == 'true'] if current_mode == 'both' else mode_df
            for _, row in df_valid.iterrows():
                fc = normalise_rgb(row, 'fill_colour')
                ec = normalise_rgb(row, f'{comparison}_line_colour')
                line_col = normalise_rgb(row, f'{dist_col}_line') if f'{dist_col}_line_rgb_r' in row else ec
                ax1.scatter(row[rank_dft_col], row[rank_mlp_col],
                            marker=MARKERS.get(comparison, 'o'),
                            s=60, facecolor=fc, edgecolor=line_col, linewidths=0.8, alpha=0.9)

        if current_mode in ['invalid', 'both']:
            df_invalid = mode_df[mode_df['is_valid'].astype(str).str.lower() != 'true'] if current_mode == 'both' else mode_df
            ax2 = ax1.twinx() if current_mode == 'both' else ax1
            for _, row in df_invalid.iterrows():
                fc = normalise_rgb(row, 'fill_colour')
                ec = normalise_rgb(row, f"{comparison}_line_colour")
                line_col = normalise_rgb(row, f'{dist_col}_line') if f'{dist_col}_line_rgb_r' in row else ec
                ax2.scatter(row[rank_dft_col], row[rank_mlp_col],
                            marker=MARKERS.get(comparison, 'o'),
                            s=60, facecolor=fc, edgecolor=line_col, linewidths=0.8,
                            alpha=0.5)
            if current_mode == 'both':
                ax2.set_ylabel("MLP Rank (invalid)", color='grey')
                ax2.tick_params(axis='y', colors='grey')
                ax2.plot([minv, maxv], [minv, maxv], 'k--', lw=1, label='y = x (invalid)')

        ax1.plot([minv, maxv], [minv, maxv], 'k--', lw=1, label='y = x')
        ax1.set_title(f"Spearman Rank – {comparison} [{current_mode}]")
        ax1.set_xlabel("DFT Rank")
        ax1.set_ylabel("MLP Rank")
        used_comparisons = [comparison]
        ax1.legend(handles=marker_legend(used_comparisons) + [ax1.lines[0]], loc='best')

        fig.tight_layout()
        outname = f"{prefix}_spearman_{comparison.replace('@', '_')}_{current_mode}.png"
        outpath = output_dir / outname
        fig.savefig(outpath, dpi=300)
        plt.close()
        print(f"✅ Saved {outpath}")

def combine_all_comparisons(df, comparisons, output_dir, mode, broken_col, prefix):
    modes_to_run = MODES[:-1] if mode == 'all' else [mode]

    for current_mode in modes_to_run:
        combined_df = pd.DataFrame()
        for comp in comparisons:
            rank_dft = f'{comp}_rank_dft'
            rank_mlp = f'{comp}_rank_mlp'
            flag_col = f'is_comparable_{comp.replace("_vs_", "_")}'
            temp = get_filtered_data(df, flag_col, broken_col)
            temp = temp.copy()
            temp['comparison'] = comp
            temp['marker'] = MARKERS.get(comp, 'o')
            temp['rank_dft'] = temp[rank_dft]
            temp['rank_mlp'] = temp[rank_mlp]
            combined_df = pd.concat([combined_df, temp], ignore_index=True)

        if current_mode == 'valid':
            combined_df = combined_df[combined_df['is_valid'].astype(str).str.lower() == 'true']
        elif current_mode == 'invalid':
            combined_df = combined_df[combined_df['is_valid'].astype(str).str.lower() != 'true']

        if combined_df.empty:
            print(f"⚠️ No data for combined comparison [{current_mode}]")
            continue

        minv = min(combined_df['rank_dft'].min(), combined_df['rank_mlp'].min())
        maxv = max(combined_df['rank_dft'].max(), combined_df['rank_mlp'].max())

        fig, ax1 = plt.subplots(figsize=(7, 6))
        used_comparisons = set(combined_df['comparison'].unique())

        if current_mode in ['valid', 'both']:
            df_valid = combined_df[combined_df['is_valid'].astype(str).str.lower() == 'true'] if current_mode == 'both' else combined_df
            for _, row in df_valid.iterrows():
                fc = normalise_rgb(row, 'fill_colour')
                ec = normalise_rgb(row, f"{row['comparison']}_line_colour")
                ax1.scatter(row['rank_dft'], row['rank_mlp'],
                            marker=row['marker'],
                            s=60, facecolor=fc, edgecolor=ec, linewidths=0.8, alpha=0.9)

        if current_mode in ['invalid', 'both']:
            df_invalid = combined_df[combined_df['is_valid'].astype(str).str.lower() != 'true'] if current_mode == 'both' else combined_df
            ax2 = ax1.twinx() if current_mode == 'both' else ax1
            for _, row in df_invalid.iterrows():
                fc = normalise_rgb(row, 'fill_colour')
                ec = normalise_rgb(row, f"{row['comparison']}_line_colour")
                ax2.scatter(row['rank_dft'], row['rank_mlp'],
                            marker=row['marker'],
                            s=60, facecolor=fc, edgecolor=ec, linewidths=0.8, alpha=0.5)
            if current_mode == 'both':
                ax2.set_ylabel("MLP Rank (invalid)", color='grey')
                ax2.tick_params(axis='y', colors='grey')
                ax2.plot([minv, maxv], [minv, maxv], 'k--', lw=1, label='y = x (invalid)')

        ax1.plot([minv, maxv], [minv, maxv], 'k--', lw=1, label='y = x')
        ax1.set_title(f"Spearman Rank – All Comparisons [{current_mode}]")
        ax1.set_xlabel("DFT Rank")
        ax1.set_ylabel("MLP Rank")
        ax1.legend(handles=marker_legend(used_comparisons) + [ax1.lines[0]], loc='best')

        fig.tight_layout()
        outpath = output_dir / f"{prefix}_spearman_all_comparisons_{current_mode}.png"
        fig.savefig(outpath, dpi=300)
        plt.close()
        print(f"✅ Saved {outpath}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results', required=True, type=Path, help='results.csv file')
    parser.add_argument('--output-dir', type=Path, default=Path('plots'), help='Directory to store figures')
    parser.add_argument('--comparison', type=str, default=None, help='Single comparison key or leave blank to run all')
    parser.add_argument('--rank-dft-column', type=str, help='DFT rank column override')
    parser.add_argument('--rank-mlp-column', type=str, help='MLP rank column override')
    parser.add_argument('--comparable-column', type=str, default=None, help='Column to filter comparable points')
    parser.add_argument('--is-broken-column', type=str, default='is_broken', help='Column indicating broken entries')
    parser.add_argument('--mode', type=str, choices=MODES, default='both', help='Which entries to show')
    args = parser.parse_args()

    df = pd.read_csv(args.results)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    prefix = args.results.stem

    targets = [args.comparison] if args.comparison else COMPARISONS
    for comp in targets:
        rank_dft = args.rank_dft_column or f'{comp}_rank_dft'
        rank_mlp = args.rank_mlp_column or f'{comp}_rank_mlp'
        flag_col = args.comparable_column or f'is_comparable_{comp.replace("_vs_", "_")}'
        plot_spearman(df, comp, rank_dft, rank_mlp, flag_col, args.is_broken_column, args.output_dir, args.mode, prefix)

    if args.comparison is None:
        combine_all_comparisons(df, COMPARISONS, args.output_dir, args.mode, args.is_broken_column, prefix)

if __name__ == '__main__':
    main()
