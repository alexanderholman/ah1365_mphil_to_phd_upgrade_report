import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline
from collections import defaultdict

# Atomic numbers for sorting
atomic_numbers = {'C': 6, 'Si': 14, 'Ge': 32, 'Sn': 50}

# Load CSV
df = pd.read_csv("results.csv")
df_valid = df[df['is_broken'] == False].copy()

# Construct surface labels
def get_surface(material, miller):
    return f"{material}_{miller}"

df_valid['surface_lower'] = df_valid.apply(lambda row: get_surface(row['material_lower'], row['material_lower_miller_hkl']), axis=1)
df_valid['surface_upper'] = df_valid.apply(lambda row: get_surface(row['material_upper'], row['material_upper_miller_hkl']), axis=1)

# Map surface to row indices
surface_to_indices = defaultdict(list)
for idx, row in df_valid.iterrows():
    surface_to_indices[row['surface_lower']].append(idx)
    surface_to_indices[row['surface_upper']].append(idx)

# Calculate formation energy ranges per surface
surface_energy_ranges = []
for surface, indices in surface_to_indices.items():
    sub_df = df_valid.loc[indices]
    dft_vals = sub_df['interface_E_form_delta_dft@dft'].dropna()
    mlp_vals = sub_df['interface_E_form_delta_dft@mlp'].dropna()
    surface_energy_ranges.append({
        'surface': surface,
        'count': len(sub_df),
        'dft_min': dft_vals.min(),
        'dft_max': dft_vals.max(),
        'mlp_min': mlp_vals.min(),
        'mlp_max': mlp_vals.max(),
    })

df_ranges = pd.DataFrame(surface_energy_ranges).dropna()

# Sort surfaces
df_ranges['sort_key'] = df_ranges['surface'].apply(
    lambda s: (*map(int, s.split('_')[1].strip('()').split()), atomic_numbers.get(s.split('_')[0], 999))
)
df_ranges = df_ranges.sort_values('sort_key').reset_index(drop=True)

# Add helper columns
df_ranges['x'] = np.arange(len(df_ranges))
df_ranges['miller'] = df_ranges['surface'].apply(lambda s: s.split('_', 1)[1])
x_np = df_ranges['x'].to_numpy()
dft_mean_np = ((df_ranges['dft_min'] + df_ranges['dft_max']) / 2).to_numpy()
mlp_mean_np = ((df_ranges['mlp_min'] + df_ranges['mlp_max']) / 2).to_numpy()

# Smooth mean curves
x_dense_full = np.linspace(x_np.min(), x_np.max(), 300)
dft_mean_smooth = make_interp_spline(x_np, dft_mean_np, k=2)(x_dense_full)
mlp_mean_smooth = make_interp_spline(x_np, mlp_mean_np, k=2)(x_dense_full)

# Miller-averaged curves
miller_x = df_ranges.groupby('miller')['x'].mean()
miller_dft = df_ranges.groupby('miller')[['dft_min', 'dft_max']].mean().mean(axis=1)
miller_mlp = df_ranges.groupby('miller')[['mlp_min', 'mlp_max']].mean().mean(axis=1)

sorted_idx = np.argsort(miller_x.values)
x_sorted = miller_x.values[sorted_idx]
dft_sorted = miller_dft[miller_x.index].values[sorted_idx]
mlp_sorted = miller_mlp[miller_x.index].values[sorted_idx]

x_dense = np.linspace(x_sorted.min(), x_sorted.max(), 300)
dft_miller_smooth = make_interp_spline(x_sorted, dft_sorted, k=2)(x_dense)
mlp_miller_smooth = make_interp_spline(x_sorted, mlp_sorted, k=2)(x_dense)

# Format surface labels with zero-padded hkl
def format_label_padded(surface):
    symbol, hkl = surface.split('_', 1)
    hkl_parts = hkl.strip('()').split()
    hkl_padded = ''.join([f"{int(n):01d}" if n.startswith('-') else f"{int(n):03d}" for n in hkl_parts])
    return f"{symbol} ({hkl_padded})"

formatted_labels = df_ranges['surface'].apply(format_label_padded)

# Function: fill gradient under curve
def gradient_fill_under_curve(ax, x, y, base, color='blue', max_alpha=0.2, steps=10):
    for i in range(len(x)-1):
        y0 = y[i]
        y1 = y[i+1]
        for j in range(steps):
            alpha = max_alpha * (1 - j / steps)
            y0a = y0 - (y0 - base) * j / (2 * steps)
            y0b = y0 - (y0 - base) * (j + 1) / (2 * steps)
            y1a = y1 - (y1 - base) * j / (2 * steps)
            y1b = y1 - (y1 - base) * (j + 1) / (2 * steps)
            ax.fill([x[i], x[i+1], x[i+1], x[i]],
                    [y0a, y1a, y1b, y0b], color=color, alpha=alpha)

# Plotting
fig, ax1 = plt.subplots(figsize=(14, 6))
ax2 = ax1.twinx()

# Main and Miller lines
line1, = ax1.plot(x_dense_full, dft_mean_smooth, '-', color='tab:blue', label='DFT ΔE mean')
line2, = ax1.plot(x_dense, dft_miller_smooth, '--', color='tab:blue', alpha=0.7, label='DFT Miller avg')
line3, = ax2.plot(x_dense_full, mlp_mean_smooth, '-', color='tab:orange', label='MLP ΔE mean')
line4, = ax2.plot(x_dense, mlp_miller_smooth, '--', color='tab:orange', alpha=0.7, label='MLP Miller avg')

# Gradient fills
gradient_fill_under_curve(ax1, x_dense, dft_miller_smooth, ax1.get_ylim()[0], color='tab:blue')
gradient_fill_under_curve(ax2, x_dense, mlp_miller_smooth, ax2.get_ylim()[0], color='tab:orange')

# Labels and formatting
ax1.set_ylabel("DFT Formation Energy ΔE (eV)", color='black')
ax2.set_ylabel("MLP Formation Energy ΔE (eV)", color='black')
ax1.tick_params(axis='y', labelcolor='black')
ax2.tick_params(axis='y', labelcolor='black')
ax1.set_xticks(x_np)
ax1.set_xticklabels(formatted_labels, rotation=90, color='black')
ax1.set_title("Smoothed Mean Formation Energy by Surface", color='black')
ax1.tick_params(axis='x', labelcolor='black')

# Legend
ax1.legend([line1, line2, line3, line4],
           [line1.get_label(), line2.get_label(), line3.get_label(), line4.get_label()],
           loc='upper right', bbox_to_anchor=(0.85, 0.98), frameon=True)

plt.tight_layout()
plt.savefig("./plots/surface_vs_formation_energy.png", dpi=300)
plt.show()