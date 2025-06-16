import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from scipy.stats import kendalltau

COMPARISONS = [
    {
        'comparison': 'dft@dft_vs_mlp@mlp',
        'dft': 'interface_E_form_delta_dft@dft',
        'mlp': 'interface_E_form_delta_mlp@mlp',
    },
    {
        'comparison': 'dft@dft_vs_dft@mlp',
        'dft': 'interface_E_form_delta_dft@dft',
        'mlp': 'interface_E_form_delta_dft@mlp',
    },
    {
        'comparison': 'mlp@dft_vs_mlp@mlp',
        'dft': 'interface_E_form_delta_mlp@dft',
        'mlp': 'interface_E_form_delta_mlp@mlp',
    },
]

MODES = ['valid', 'invalid', 'both', 'all']

MARKERS = {
    'dft@dft_vs_mlp@mlp': 'o',
    'dft@dft_vs_dft@mlp': 's',
    'mlp@dft_vs_mlp@mlp': 'D'
}

def normalise_rgb(row, prefix):
    val = row.get(prefix, '')
    if isinstance(val, str) and val.startswith('('):
        try:
            return eval(val)
        except Exception:
            pass
    return (0.5, 0.5, 0.5)

def get_filtered_data(df, flag_col, broken_col):
    return df[(df[flag_col].astype(str).str.lower() == 'true') &
              (df[broken_col].astype(str).str.lower() != 'true')].copy()

def marker_legend(comps):
    return [
        mlines.Line2D([], [], color='black', marker=MARKERS[c['comparison']], linestyle='None', label=c['comparison'])
        for c in comps
    ]

def plot_kendall(df, comp_dict, flag_col, broken_col, output_dir, mode, prefix):
    comparison = comp_dict['comparison']
    mlp_col = comp_dict['mlp']
    dft_col = comp_dict['dft']

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
            print(f"⚠️ No data for mode '{current_mode}' in '{comparison}'")
            continue

        x_vals = mode_df[mlp_col]
        y_vals = mode_df[dft_col]
        kendall_tau, _ = kendalltau(x_vals, y_vals)

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_aspect('auto')

        for _, row in mode_df.iterrows():
            fc = normalise_rgb(row, 'fill_colour')
            ec = normalise_rgb(row, f"{comparison}_line_colour")
            ax.scatter(row[mlp_col], row[dft_col],
                       marker=MARKERS.get(comparison, 'o'),
                       s=60, facecolor=fc, edgecolor=ec, linewidths=0.8,
                       alpha=0.9 if row['is_valid'] else 0.5)

        ax.set_xlabel("MLP-evaluated Formation Energy (eV/atom)")
        ax.set_ylabel("DFT-evaluated Formation Energy (eV/atom)")
        ax.set_title(f"Kendall τ = {kendall_tau:.3f} – {comparison} [{current_mode}]")
        ax.annotate("Kendall τ reflects ordinal consistency,\nnot magnitude agreement",
                    xy=(0.05, 0.95), xycoords='axes fraction', fontsize=10, ha='left', va='top')
        ax.legend(handles=marker_legend([comp_dict]), loc='best')

        fig.tight_layout()
        outpath = output_dir / f"{prefix}_kendall_{comparison}_{current_mode}.png"
        fig.savefig(outpath, dpi=300)
        plt.close()
        print(f"✅ Saved {outpath}")

def combine_all_comparisons(df, comp_list, broken_col, output_dir, mode, prefix):
    modes_to_run = MODES[:-1] if mode == 'all' else [mode]

    for current_mode in modes_to_run:
        combined_df = pd.DataFrame()
        for comp in comp_list:
            flag_col = f"is_comparable_{comp['comparison'].replace('_vs_', '_')}"
            temp = get_filtered_data(df, flag_col, broken_col)
            if temp.empty:
                continue
            temp = temp.copy()
            temp['comparison'] = comp['comparison']
            temp['marker'] = MARKERS[comp['comparison']]
            temp['x'] = temp[comp['mlp']]
            temp['y'] = temp[comp['dft']]
            combined_df = pd.concat([combined_df, temp], ignore_index=True)

        if current_mode == 'valid':
            combined_df = combined_df[combined_df['is_valid'].astype(str).str.lower() == 'true']
        elif current_mode == 'invalid':
            combined_df = combined_df[combined_df['is_valid'].astype(str).str.lower() != 'true']

        if combined_df.empty:
            print(f"⚠️ No combined data for mode '{current_mode}'")
            continue

        kendall_tau, _ = kendalltau(combined_df['x'], combined_df['y'])

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_aspect('auto')

        for _, row in combined_df.iterrows():
            fc = normalise_rgb(row, 'fill_colour')
            ec = normalise_rgb(row, f"{row['comparison']}_line_colour")
            ax.scatter(row['x'], row['y'],
                       marker=row['marker'],
                       s=60, facecolor=fc, edgecolor=ec, linewidths=0.8,
                       alpha=0.9 if row['is_valid'] else 0.5)

        ax.set_xlabel("MLP-evaluated Formation Energy (eV/atom)")
        ax.set_ylabel("DFT-evaluated Formation Energy (eV/atom)")
        ax.set_title(f"Kendall τ = {kendall_tau:.3f} – All Comparisons [{current_mode}]")
        ax.annotate("Kendall τ reflects ordinal consistency,\nnot magnitude agreement",
                    xy=(0.05, 0.95), xycoords='axes fraction', fontsize=10, ha='left', va='top')
        ax.legend(handles=marker_legend(comp_list), loc='best')

        fig.tight_layout()
        outpath = output_dir / f"{prefix}_kendall_all_comparisons_{current_mode}.png"
        fig.savefig(outpath, dpi=300)
        plt.close()
        print(f"✅ Saved {outpath}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results', required=True, type=Path, help='results.csv file')
    parser.add_argument('--output-dir', type=Path, default=Path('plots'), help='Where to save plots')
    parser.add_argument('--comparison', type=str, default=None, help='Which comparison key to run (or "all")')
    parser.add_argument('--is-broken-column', type=str, default='is_broken', help='Column for broken entries')
    parser.add_argument('--mode', type=str, choices=MODES, default='both', help='Which points to show')
    args = parser.parse_args()

    df = pd.read_csv(args.results)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    prefix = args.results.stem

    selected = COMPARISONS if args.comparison in (None, 'all') else [
        c for c in COMPARISONS if c['comparison'] == args.comparison
    ]

    for comp in selected:
        flag_col = f"is_comparable_{comp['comparison'].replace('_vs_', '_')}"
        plot_kendall(df, comp, flag_col, args.is_broken_column, args.output_dir, args.mode, prefix)

    if args.comparison in (None, 'all'):
        combine_all_comparisons(df, COMPARISONS, args.is_broken_column, args.output_dir, args.mode, prefix)

if __name__ == '__main__':
    main()