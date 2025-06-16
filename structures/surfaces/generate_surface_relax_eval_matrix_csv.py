import pandas as pd
from pathlib import Path
import json
from ase.io import read

# Define relaxation and evaluation flavours
methods = ["dft_vasp", "mlp_mace"]
relax_eval_pairs = [(r, e) for r in methods for e in methods]

# Input slab root directory
base_dir = Path("./structures/surfaces")
output_csv = Path("./surface_energy_matrix.csv")

print(f"Generating surface energy matrix CSV from slabs in {base_dir}")

# find all directories containing slab.vasp files
if not base_dir.exists():
    raise FileNotFoundError(f"Base directory {base_dir} does not exist.")

if not base_dir.is_dir():
    raise NotADirectoryError(f"Base directory {base_dir} is not a directory.")

slabs_paths = []

records = []

# foreach folder in base_dir, check if it contains a slab.vasp and if so, add it to slabs_paths
for item in base_dir.iterdir():
    if item.is_dir() and (item / "slab.vasp").exists():
        slabs_paths.append(item)

for slabs_path in slabs_paths:
    slab_dir = slabs_path
    slab_dir_parts = slab_dir.name.split("_")

    n = int(slab_dir_parts[0])
    species = slab_dir_parts[1][:-len(str(n))]
    h = int(slab_dir_parts[2][0])
    k = int(slab_dir_parts[2][1])
    l = int(slab_dir_parts[2][2])

    atoms = read(slabs_path/"slab.vasp")
    thickness_A = atoms.get_cell()[2, 2]  # Assuming z-axis is the thickness direction
    area_A2 = atoms.get_volume() / thickness_A  # Area = Volume / Thickness

    row = {
        "species": species,
        "miller_h": h,
        "miller_k": k,
        "miller_l": l,
        "n_atoms": n,
        "thickness_A": thickness_A,
        "area_A2": area_A2
    }

    # Add blank fields for each relaxation/evaluation pair
    for relax, eval in relax_eval_pairs:
        row[f"E_{relax}_{eval}"] = ""
        row[f"gamma_{relax}_{eval}"] = ""

    records.append(row)

# Write to CSV
df = pd.DataFrame(records)
output_csv.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(output_csv, index=False)
