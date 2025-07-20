import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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
        'dft_mean': dft_vals.mean(),
        'mlp_mean': mlp_vals.mean(),
    })

df_ranges = pd.DataFrame(surface_energy_ranges).dropna()

# Sort surfaces
df_ranges['sort_key'] = df_ranges['surface'].apply(
    lambda s: (*map(int, s.split('_')[1].strip('()').split()), atomic_numbers.get(s.split('_')[0], 999))
)
df_ranges = df_ranges.sort_values('sort_key').reset_index(drop=True)

# Format x-axis labels
def format_label(surface):
    symbol, hkl = surface.split('_', 1)
    hkl_padded = ''.join([f"{int(n):01d}" if n.startswith('-') else f"{int(n):03d}" for n in hkl.strip('()').split()])
    return f"{symbol} ({hkl_padded})"

labels = df_ranges['surface'].apply(format_label)
x = np.arange(len(labels))

# Plot bar chart
width = 0.4
fig, ax = plt.subplots(figsize=(14, 6))
ax.bar(x - width/2, df_ranges['dft_mean'], width=width, label='DFT ΔE', color='tab:blue')
ax.bar(x + width/2, df_ranges['mlp_mean'], width=width, label='MLP ΔE', color='tab:orange')

# Formatting
ax.set_ylabel("Mean Formation Energy ΔE (eV)", color='black')
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=90, color='black')
ax.set_title("Mean Interface Formation Energy by Surface", color='black')
ax.legend()

plt.tight_layout()
plt.savefig("./plots/surface_vs_formation_energy_bar.png", dpi=300)
plt.show()