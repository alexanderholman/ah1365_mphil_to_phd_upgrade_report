import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import spearmanr, kendalltau
from sklearn.metrics import mean_squared_error, mean_absolute_error
from pathlib import Path
import numpy as np

def get_latest_timestamped_dir(base_dir: Path):
    timestamped_dirs = [d for d in base_dir.iterdir() if d.is_dir()]
    if not timestamped_dirs:
        return None
    return max(timestamped_dirs, key=lambda d: d.name)

# --- Locate and Verify Files ---
latest_results_dir = get_latest_timestamped_dir(Path("results"))
if latest_results_dir is None:
    raise FileNotFoundError("No timestamped directories found in 'results'.")

data_dir = latest_results_dir / "data"
if not data_dir.exists():
    raise FileNotFoundError(f"Data directory {data_dir} does not exist.")

poscar_dirs = list(data_dir.glob("**/POSCAR"))
if not poscar_dirs:
    raise FileNotFoundError("No POSCAR directories found in the data directory.")

graphs_dir = latest_results_dir / "graphs"
graphs_dir.mkdir(parents=True, exist_ok=True)

results_csv = latest_results_dir / "results.csv"
if not results_csv.exists():
    raise FileNotFoundError(f"Results CSV file {results_csv} does not exist.")

summary_file = latest_results_dir / "summary.txt"
if not summary_file.exists():
    raise FileNotFoundError(f"Summary file {summary_file} does not exist.")

# --- Load and Filter Data ---
df = pd.read_csv(results_csv)
df = df.dropna(subset=['dft_form', 'mlp_form'])

# Add %Si column if not present
if 'si_percent' not in df.columns:
    raise ValueError("Missing required 'si_percent' column in results.csv.")

df['valid'] = df['dft_form'] <= 1.0
df_valid = df[df['valid']].copy()

# --- Compute Metrics ---
spearman_rho, _ = spearmanr(df_valid['dft_form'], df_valid['mlp_form'])
kendall_tau, _ = kendalltau(df_valid['dft_form'], df_valid['mlp_form'])
rmse = np.sqrt(mean_squared_error(df_valid['dft_form'], df_valid['mlp_form']))
mae = mean_absolute_error(df_valid['dft_form'], df_valid['mlp_form'])

# --- Define Colour Map (Si%: Red → Green → Violet) ---
colour_map = LinearSegmentedColormap.from_list("SiGradient", ["red", "green", "violet"])

# --- Plot Setup ---
plt.figure(figsize=(14, 6))
sns.set(style="whitegrid")

# --- Spearman Rank Correlation Plot ---
plt.subplot(1, 2, 1)
dft_ranks = df_valid['dft_form'].rank()
mlp_ranks = df_valid['mlp_form'].rank()
sc1 = plt.scatter(x=dft_ranks, y=mlp_ranks, c=df_valid['si_percent'], cmap=colour_map, s=60)
plt.plot([min(dft_ranks), max(dft_ranks)],
         [min(dft_ranks), max(dft_ranks)],
         color='black', linestyle='--', label='Perfect Correlation (y = x)')
plt.title(f"Spearman Rank Correlation (ρ = {spearman_rho:.3f})")
plt.xlabel("DFT Rank")
plt.ylabel("MLP Rank")
plt.legend()
plt.annotate("Spearman assesses monotonicity\nbased on ranked positions",
             xy=(0.05, 0.95), xycoords='axes fraction', fontsize=10, ha='left', va='top')
cbar1 = plt.colorbar(sc1)
cbar1.set_label("Si Content (%)")

# --- Kendall Rank Correlation Plot: Axis-Swapped with Excluded Overlay ---
plt.subplot(1, 2, 2)
sc2 = plt.scatter(x=df_valid['mlp_form'], y=df_valid['dft_form'],
                  c=df_valid['si_percent'], cmap=colour_map, s=60)
ax = plt.gca()
ax.set_xlabel("MLP Formation Energy (eV/atom)")
ax.set_ylabel("DFT Formation Energy (eV/atom)")
ax.set_title(f"Kendall Rank Correlation (τ = {kendall_tau:.3f})")
ax.annotate("Kendall τ reflects ordinal consistency,\nnot magnitude agreement",
            xy=(0.05, 0.95), xycoords='axes fraction', fontsize=10, ha='left', va='top')

# Secondary y-axis for excluded points
ax2 = ax.twinx()
ax2.scatter(x=df[~df['valid']]['mlp_form'], y=df[~df['valid']]['dft_form'],
            color='grey', alpha=0.4, marker='x', label='Excluded (>1 eV)', s=60)
ax2.set_ylabel("Excluded DFT Energy (eV/atom)", color='grey')
ax2.tick_params(axis='y', colors='grey')
ax2.legend(loc='lower right')

cbar2 = plt.colorbar(sc2, ax=ax)
cbar2.set_label("Si Content (%)")

# --- Finalise and Save ---
plt.tight_layout()
figure_name = graphs_dir / "case1_spearman_kendall_coloured.png"
plt.savefig(figure_name, dpi=300)
plt.show()

# --- Append Summary ---
# with open(summary_file, 'a') as f:
#     f.write("\n--- Case Study 1 Correlation Summary ---\n")
#     f.write(f"Number of valid data points (DFT ≤ 1 eV): {len(df_valid)}\n")
#     f.write(f"Excluded points (> 1 eV): {len(df) - len(df_valid)}\n")
#     f.write(f"Spearman ρ (rank monotonicity): {spearman_rho:.4f}\n")
#     f.write(f"Kendall τ (ordinal agreement): {kendall_tau:.4f}\n")
#     f.write(f"RMSE: {rmse:.4f} eV/atom\n")
#     f.write(f"MAE: {mae:.4f} eV/atom\n")
