#!/usr/bin/env python3
import os
import csv
from pathlib import Path
import numpy as np
import argparse
from scipy.stats import spearmanr, kendalltau
from sklearn.metrics import mean_squared_error, mean_absolute_error

def compute_stats(x, y):
    """Compute statistics between two arrays."""
    mask = ~np.isnan(x) & ~np.isnan(y)
    if np.sum(mask) < 2:
        return {"spearman": np.nan, "kendall": np.nan, "rmse": np.nan, "mae": np.nan}
    x = x[mask]
    y = y[mask]
    spearman_corr, _ = spearmanr(x, y)
    kendall_corr, _ = kendalltau(x, y)
    rmse = mean_squared_error(x, y) ** 0.5
    mae = mean_absolute_error(x, y)
    return {"spearman": spearman_corr, "kendall": kendall_corr, "rmse": rmse, "mae": mae}

def compute_top_n_overlap(list1, list2, top_n):
    """Return number of overlapping items in top-N of two ranked lists."""
    top1 = [x["name"] for x in sorted(list1, key=lambda r: r["val1"])[:top_n]]
    top2 = [x["name"] for x in sorted(list2, key=lambda r: r["val2"])[:top_n]]
    return len(set(top1).intersection(set(top2)))

def safe_float(x):
    try:
        return float(x)
    except:
        return np.nan

def main():
    parser = argparse.ArgumentParser(description="Compare interface formation energy rankings and errors")
    parser.add_argument('-r', '--read', type=str, default='results.csv', help="CSV file with interface formation rankings")
    parser.add_argument('-w', '--write', type=str, default='stats.csv', help="CSV file to write the statistics to")
    parser.add_argument('--dd-column', type=str, default='interface_E_form_delta_dft@dft', help="Column for DFT relaxation DFT energy")
    parser.add_argument('--dm-column', type=str, default='interface_E_form_delta_dft@mlp', help="Column for DFT relaxation MLP energy")
    parser.add_argument('--md-column', type=str, default='interface_E_form_delta_mlp@dft', help="Column for MLP relaxation DFT energy")
    parser.add_argument('--mm-column', type=str, default='interface_E_form_delta_mlp@mlp', help="Column for MLP relaxation MLP energy")
    parser.add_argument('--ddmm-comparable-column', type=str, default='is_comparable_dft@dft_mlp@mlp', help="Column indicating comparability for DFT vs MLP")
    parser.add_argument('--ddmm-rank-dft-column', type=str, default='dft@dft_vs_mlp@mlp_rank_dft', help="Column for DFT rank in DFT@DFT vs MLP@MLP comparison")
    parser.add_argument('--ddmm-rank-mlp-column', type=str, default='dft@dft_vs_mlp@mlp_rank_mlp', help="Column for MLP rank in DFT@DFT vs MLP@MLP comparison")
    parser.add_argument('--dddm-comparable-column', type=str, default='is_comparable_dft@dft_dft@mlp')
    parser.add_argument('--dddm-rank-dft-column', type=str, default='dft@dft_vs_dft@mlp_rank_dft', help="Column for DFT rank in DFT@DFT vs DFT@MLP comparison")
    parser.add_argument('--dddm-rank-mlp-column', type=str, default='dft@dft_vs_dft@mlp_rank_mlp', help="Column for MLP rank in DFT@DFT vs DFT@MLP comparison")
    parser.add_argument('--mdmm-comparable-column', type=str, default='is_comparable_mlp@dft_mlp@mlp')
    parser.add_argument('--mdmm-rank-dft-column', type=str, default='mlp@dft_vs_mlp@mlp_rank_dft', help="Column for DFT rank in MLP@DFT vs MLP@MLP comparison")
    parser.add_argument('--mdmm-rank-mlp-column', type=str, default='mlp@dft_vs_mlp@mlp_rank_mlp', help="Column for MLP rank in MLP@DFT vs MLP@MLP comparison")
    parser.add_argument('--is-broken-column', type=str, default='is_broken', help="Column indicating if the interface is broken")
    parser.add_argument('--top-n', type=int, default=10)
    args = parser.parse_args()

    if not Path(args.read).exists():
        raise FileNotFoundError(f"Results file {args.read} does not exist.")

    with open(args.read, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    all_stats = []
    comparison_stats = [
        {
            "comparison": args.ddmm_comparable_column,
            "energy": {
                "dft": args.dd_column,
                "mlp": args.mm_column
            },
            "rank": {
                "dft": args.ddmm_rank_dft_column,
                "mlp": args.ddmm_rank_mlp_column
            }
        },
        {
            "comparison": args.dddm_comparable_column,
            "energy": {
                "dft": args.dd_column,
                "mlp": args.dm_column
            },
            "rank": {
                "dft": args.dddm_rank_dft_column,
                "mlp": args.dddm_rank_mlp_column
            }
        },
        {
            "comparison": args.mdmm_comparable_column,
            "energy": {
                "dft": args.md_column,
                "mlp": args.mm_column
            },
            "rank": {
                "dft": args.mdmm_rank_dft_column,
                "mlp": args.mdmm_rank_mlp_column
            }
        },
    ]

    for comp in comparison_stats:
        comp_rows = [
            {
                "name": row["name"],
                "index": row.get("index", row.get("name", "")),
                "val1": safe_float(row.get(comp["energy"]["dft"])),
                "val2": safe_float(row.get(comp["energy"]["mlp"])),
                "rank1": safe_float(row.get(comp["rank"]["dft"])),
                "rank2": safe_float(row.get(comp["rank"]["mlp"])),
            }
            for row in rows
            if row.get(comp["comparison"], '').strip().lower() == 'true'
            and row.get(args.is_broken_column, '').strip() == 'False'
        ]

        x = np.array([r["val1"] for r in comp_rows])
        y = np.array([r["val2"] for r in comp_rows])

        if len(x) < 2:
            stats = {"spearman": np.nan, "kendall": np.nan, "rmse": np.nan, "mae": np.nan}
            overlap = np.nan
        else:
            stats = compute_stats(x, y)
            overlap = compute_top_n_overlap(comp_rows, comp_rows, args.top_n)

        all_stats.append({
            "comparison": comp["comparison"],
            "col1": comp["energy"]["dft"],
            "col2": comp["energy"]["mlp"],
            "n": len(comp_rows),
            "spearman": stats["spearman"],
            "kendall": stats["kendall"],
            "rmse": stats["rmse"],
            "mae": stats["mae"],
            f"top{args.top_n}_overlap": overlap,
        })

    if all_stats:
        with open(args.write, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_stats[0].keys())
            writer.writeheader()
            writer.writerows(all_stats)
        print(f"✅ Summary written to {args.write}")
    else:
        print("⚠️ No valid comparable data found. Output file not written.")

if __name__ == '__main__':
    main()
