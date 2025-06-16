#!/usr/bin/env python3
import os
import csv
import re
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from scipy.stats import spearmanr, kendalltau
from sklearn.metrics import mean_squared_error, mean_absolute_error

# Bulk reference data (diamond 8-atom cells)
n_material_alpha_bulk = 8
n_material_beta_bulk = 8

# DFT bulk energies (replace with your actual values)
E_material_alpha_bulk_DFT = -43.36
E_material_beta_bulk_DFT = -34.24

# MLP bulk energies (replace with your actual values)
E_material_alpha_bulk_MLP = -43.29
E_material_beta_bulk_MLP = -34.15

def extract_energy_from_mace_outcar(filename):
    try:
        with open(filename, 'r') as f:
            for line in f:
                if line.startswith("MACE Energy:"):
                    match = re.search(r"([-+]?[0-9]*\.?[0-9]+)", line)
                    if match:
                        return float(match.group(1))
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    return None

def extract_energy_from_outcar(filename):
    pattern = r"energy\s+without entropy=\s+([-+]?[0-9]*\.?[0-9]+)"
    try:
        with open(filename, 'r') as f:
            for line in f:
                m = re.search(pattern, line.lstrip())
                if m:
                    return float(m.group(1))
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    return None

def extract_atom_counts_from_poscar(filename):
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
            counts = list(map(int, lines[6].split()))
            return counts[0], counts[1]  # n_material_alpha, n_material_beta
    except Exception as e:
        print(f"Error reading atom counts from {filename}: {e}")
    return None, None

# started format "Job started on: Wed 30 Apr 03:42:55 UTC 2025\n"
# ended format "Job ended on: Wed 30 Apr 03:44:37 UTC 2025\n"
def extract_compute_time_from_outfile(filename):
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
            start_time = None
            end_time = None
            for line in lines:
                line = line.strip()
                if line.startswith("Job started on:"):
                    start_time = line.split("Job started on:")[1].strip().replace("\\n", "")
                elif line.startswith("Job ended on:"):
                    end_time = line.split("Job ended on:")[1].strip().replace("\\n", "")
            if start_time and end_time:
                start_dt = datetime.strptime(start_time, "%a %d %b %H:%M:%S %Z %Y")
                end_dt = datetime.strptime(end_time, "%a %d %b %H:%M:%S %Z %Y")
                return (end_dt - start_dt).total_seconds()
    except Exception as e:
        print(f"Error reading compute time from {filename}: {e}")
    return None

def gather_results(base_dir="data/Si_Ge"):
    results = []
    if not os.path.exists(base_dir):
        print(f"Base directory {base_dir} not found.")
        return []

    for entry in os.listdir(base_dir):
        path = os.path.join(base_dir, entry)
        if not os.path.isdir(path):
            continue

        dft_outcar = os.path.join(path, "OUTCAR")
        mace_outcar = os.path.join(path, "OUTCAR_MLP_MACE")
        dft_poscar = os.path.join(path, "POSCAR")
        mace_poscar = os.path.join(path, "POSCAR_MLP_MACE")
        dft_contcar = os.path.join(path, "CONTCAR")
        mace_contcar = os.path.join(path, "CONTCAR_MLP_MACE")
        dft_outfile, mace_outfile = None, None
        # find file matching *DFTVasp.out and *MLPMACE.out
        # search for files with these patterns
        for file in os.listdir(path):
            if file.endswith("DFTVasp.out"):
                dft_outfile = os.path.join(path, file)
            elif file.endswith("MLPMACE.out"):
                mace_outfile = os.path.join(path, file)

        # check poscars are the same
        # compare POSCAR files to ensure they are the same
        dft_poscar_file_content = None
        mace_poscar_file_content = None
        try:
            with open(dft_poscar, 'r') as f:
                dft_poscar_file_content = f.read()
            with open(mace_poscar, 'r') as f:
                mace_poscar_file_content = f.read()
        except Exception as e:
            print(f"⚠️ Error reading POSCAR files for {entry}: {e}")
            continue

        # if dft_poscar_file_content != mace_poscar_file_content:
        #     print(f"⚠️ POSCAR mismatch in {entry}: DFT and MLP POSCAR files are different.")
        #     continue

        E_dft = extract_energy_from_outcar(dft_outcar)
        E_mlp = extract_energy_from_mace_outcar(mace_outcar)
        dft_n_material_alpha, dft_n_material_beta = extract_atom_counts_from_poscar(dft_contcar)
        mlp_n_material_alpha, mlp_n_material_beta = extract_atom_counts_from_poscar(mace_contcar)

        # if dft_n_material_alpha is None or dft_n_material_beta is None or mlp_n_material_alpha is None or mlp_n_material_beta is None:
        #     print(f"⚠️ Missing atom counts in {entry}: DFT ({dft_n_material_alpha}, {dft_n_material_beta}), MLP ({mlp_n_material_alpha}, {mlp_n_material_beta})")
        #     continue

        dft_n = dft_n_material_alpha + dft_n_material_beta if dft_n_material_alpha is not None and dft_n_material_beta is not None else None
        mlp_n = mlp_n_material_alpha + mlp_n_material_beta if mlp_n_material_alpha is not None and mlp_n_material_beta is not None else None

        # if dft_n != mlp_n:
        #     print(f"⚠️ Atom count mismatch in {entry}: DFT ({dft_n_material_alpha}, {dft_n_material_beta}), MLP ({mlp_n_material_alpha}, {mlp_n_material_beta})")
        #     continue

        n = dft_n if dft_n is not None else mlp_n if mlp_n is not None else None
        n_material_alpha = dft_n_material_alpha
        n_material_beta = dft_n_material_beta

        # for check in (E_dft, E_mlp, n, n_material_alpha, n_material_beta):
        #     if check is None or check == 0:
        #         print(f"⚠️ Missing data in {entry}: DFT energy {E_dft}, MLP energy {E_mlp}, n_material_alpha {n_material_alpha}, n_material_beta {n_material_beta}")
        #         continue


        dft_compute_time = extract_compute_time_from_outfile(dft_outfile)
        mlp_compute_time = extract_compute_time_from_outfile(mace_outfile)

        N = n_material_alpha + n_material_beta if n_material_alpha is not None and n_material_beta is not None else None
        ref_dft = ((n_material_alpha * (E_material_alpha_bulk_DFT / n_material_alpha_bulk)) + (n_material_beta * (E_material_beta_bulk_DFT / n_material_beta_bulk))) if n_material_alpha is not None and n_material_beta is not None else None
        ref_mlp = ((n_material_alpha * (E_material_alpha_bulk_MLP / n_material_alpha_bulk)) + (n_material_beta * (E_material_beta_bulk_MLP / n_material_beta_bulk))) if n_material_alpha is not None and n_material_beta is not None else None
        ΔE_dft = (E_dft - ref_dft) / N if E_dft is not None and ref_dft is not None else None
        ΔE_mlp = (E_mlp - ref_mlp) / N if E_mlp is not None and ref_mlp is not None else None

        # split poscar into lower and upper structures
        # bottom half is material_alpha and top half is material_beta
        # we

        # calculate strain energies
        # calculate compression

        # calculate tension

        # calculate shear

        # calculate total strain energy

        # calculate total strain energy per atom

        # calculate surface energy

        # calculate surface energy per angstrom^2 of lower_surface

        # calculate surface energy per angstrom^2 of upper_surface

        # calculate interface energy per angstrom^2


        material_alpha_percent = (n_material_alpha / N) * 100 if N else None

        # Function: RGB fill colour from material_alpha content (0–100%)
        def si_to_rgb(material_alpha_percent):
            if material_alpha_percent is None:
                return 0, 0, 0
            si_frac = material_alpha_percent / 100
            if si_frac >= 0.5:
                ratio = (si_frac - 0.5) * 2
                r = int(0 + ratio * 255)
                g = int(255 - ratio * 255)
                b = 0
            else:
                ratio = si_frac * 2
                r = int(127 * (1 - ratio) + 0 * ratio)
                g = int(0 * (1 - ratio) + 255 * ratio)
                b = int(255 * (1 - ratio) + 0 * ratio)
            return r / 255, g / 255, b / 255

        results.append({
            "interface": entry,
            "dft_energy": E_dft,
            "mlp_energy": E_mlp,
            "bulk_material_alpha_energy": E_material_alpha_bulk_DFT,
            "bulk_material_beta_energy": E_material_beta_bulk_DFT,
            "n_material_alpha": n_material_alpha,
            "n_material_beta": n_material_beta,
            "n": N,
            "material_alpha_percent": material_alpha_percent,
            "bulk_form": (E_material_alpha_bulk_DFT + E_material_beta_bulk_DFT) / (n_material_alpha_bulk + n_material_beta_bulk),
            "dft_form_Δ": ΔE_dft,
            "dft_rank": None,  # Placeholder for rank
            "dft_compute_time": dft_compute_time,
            "mlp_form_Δ": ΔE_mlp,
            "mlp_rank": None,  # Placeholder for rank
            "mlp_compute_time": mlp_compute_time,
            "mlp_n_times_faster": dft_compute_time / mlp_compute_time if dft_compute_time and mlp_compute_time else None,
            "dft_mlp_rank_distance": None,  # Placeholder for rank distance
            "fill_colour": si_to_rgb(material_alpha_percent),
            "line_colour": None,  # Placeholder for line colour
            "is_valid": ΔE_dft <= 1.0 if ΔE_dft is not None else False,
        })
    return results

def write_csv(results, filename):
    if not results:
        print("⚠ No results to write.")
        return
    keys = results[0].keys()
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)
    print(f"Results written to {filename}")

def plot_results(results, timestamp):
    sorted_results = sorted(results, key=lambda x: x["dft_form"])
    interfaces = [r["interface"] for r in sorted_results]
    dft_vals = [r["dft_form"] for r in sorted_results]
    mlp_vals = [r["mlp_form"] for r in sorted_results]

    fig, ax = plt.subplots(figsize=(14, 6))
    x = np.arange(len(interfaces))
    ax.bar(x - 0.2, dft_vals, width=0.4, label="DFT ΔE", alpha=0.7)
    ax.bar(x + 0.2, mlp_vals, width=0.4, label="MLP ΔE", alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(interfaces, rotation=45, ha="right")
    ax.set_ylabel("Formation Energy (eV/atom)")
    ax.set_title("Interface Formation Energies")
    ax.legend()

    plt.tight_layout()
    graph_dir = os.path.join("results", timestamp, "graphs")
    os.makedirs(graph_dir, exist_ok=True)
    plt.savefig(os.path.join(graph_dir, "interface_energy_comparison.png"), dpi=300)
    plt.show()
    print(f"Plot saved to {graph_dir}")

def compute_stats(results, timestamp, top_n=10):
    dft = [r["dft_form"] for r in results]
    mlp = [r["mlp_form"] for r in results]
    spearman, _ = spearmanr(dft, mlp)
    kendall, _ = kendalltau(dft, mlp)
    rmse = mean_squared_error(dft, mlp) ** 0.5
    mae = mean_absolute_error(dft, mlp)

    dft_top = set(r["interface"] for r in sorted(results, key=lambda r: r["dft_form"])[:top_n])
    mlp_top = set(r["interface"] for r in sorted(results, key=lambda r: r["mlp_form"])[:top_n])
    overlap = len(dft_top & mlp_top)

    out = os.path.join("results", timestamp, "summary.txt")
    with open(out, "w") as f:
        f.write("Rank Correlation\n----------------\n")
        f.write(f"Spearman ρ ≈ {spearman:.3f}\n")
        f.write(f"Kendall  τ ≈ {kendall:.3f}\n\n")
        f.write("Energy Error\n------------\n")
        f.write(f"RMSE ≈ {rmse:.3f} eV/interface\n")
        f.write(f"MAE  ≈ {mae:.3f} eV/interface\n\n")
        f.write("Top-10 Recovery\n----------------\n")
        f.write(f"{overlap}/10 overlap between DFT and MLP top-10\n")
    print(f"Summary stats written to {out}")

def main():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    outdir = os.path.join("results", timestamp)
    os.makedirs(outdir, exist_ok=True)

    results = gather_results()
    if not results:
        print("❌ No valid data found. Exiting.")
        return

    print(results[0])

    write_csv(results, os.path.join(outdir, "results.csv"))
    # plot_results(results, timestamp)
    # compute_stats(results, timestamp)

    # src = "data"
    # dst = os.path.join(outdir, "data")
    # if os.path.exists(src):
    #     try:
    #         shutil.copytree(src, dst)
    #         print(f"📦 Copied data snapshot to {dst}")
    #     except Exception as e:
    #         print(f"⚠ Could not copy data snapshot: {e}")

if __name__ == "__main__":
    main()
