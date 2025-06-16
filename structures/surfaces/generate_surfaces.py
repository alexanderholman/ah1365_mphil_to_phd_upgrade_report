import os
import json
from ase.build import bulk, surface
from ase.io import read, write
from pathlib import Path

from scipy.optimize import direct

SPECIES = GROUP4 = [
    "C",
    "Si",
    "Ge",
    "Sn",
]

LATTICE_CONSTANTS = {
    "C": 3.5668,
    "Si": 5.4310,
    "Ge": 5.6578,
    "Sn": 6.4892,
}

BULKS = {s: bulk(s, crystalstructure='diamond', a=LATTICE_CONSTANTS[s], cubic=True) for s in SPECIES}

def build_thick_slab(bulk, miller, min_thickness=20, vacuum=20, max_layers=100):
    miller = tuple(miller)
    layers = 3  # initial guess

    while layers <= max_layers:
        slab = surface(bulk, miller, layers=layers)
        z_extent = max(slab.positions[:, 2]) - min(slab.positions[:, 2])
        if z_extent >= min_thickness:
            break
        layers += 1

    if layers > max_layers:
        raise ValueError(f"Could not reach desired thickness {min_thickness} Å with {max_layers} layers.")

    slab.center(vacuum=vacuum, axis=2)
    return slab, z_extent, layers

generate_surfaces_dir = Path("./structures/surfaces")
if not generate_surfaces_dir.exists():
    generate_surfaces_dir.mkdir(parents=True)

species_miller_pairs = {}

poscar_paths = list(Path("../common/structures/interfaces").rglob("POSCAR"))

print(f"Found {len(poscar_paths)} POSCAR files in common/structures/interfaces/**/POSCAR")

# find every surface in common/structures/interfaces/**/POSCAR
for poscar_path in poscar_paths:
    base_dir_path = poscar_path.parent
    artemis_path = base_dir_path / "artemis"
    generated_files_dir_path = artemis_path / "generated_files"
    generation_files_dir_path = artemis_path / "generation_files"
    lower_path = generation_files_dir_path / "lower.vasp"
    upper_path = generation_files_dir_path / "upper.vasp"
    poscar_data_json_path = base_dir_path / "poscar_data.json"
    # read json file to get the species and miller indices
    if not poscar_data_json_path.exists():
        continue
    poscar_data = json.load(open(poscar_data_json_path))
    lower_structure = read(lower_path)
    lower_miller = poscar_data['struc_data']['lower_crystal_miller_plane']
    lower_key = f"{lower_structure.get_chemical_symbols()[0]}{lower_miller['h']}{lower_miller['k']}{lower_miller['l']}"
    if lower_key not in species_miller_pairs:
        species_miller_pairs[lower_key] = (lower_structure, lower_miller)
    upper_structure = read(upper_path)
    upper_miller = poscar_data['struc_data']['upper_crystal_miller_plane']
    upper_key = f"{upper_structure.get_chemical_symbols()[0]}{upper_miller['h']}{upper_miller['k']}{upper_miller['l']}"
    if upper_key not in species_miller_pairs:
        species_miller_pairs[upper_key] = (upper_structure, upper_miller)

print(f"Found {len(species_miller_pairs)} unique species and miller pairs in common/structures/interfaces/**/POSCAR")

for key, (structure, miller) in species_miller_pairs.items():
    bulk, h, k, l = structure, miller['h'], miller['k'], miller['l']
    slab, slab_z, n_layers = build_thick_slab(bulk, (h, k, l))
    species = bulk.get_chemical_symbols()[0]
    n = len(slab)
    print(f"Built {species} slab on {miller} with {n_layers} layers, thickness = {slab_z:.2f} Å")
    dir = Path(f"./structures/surfaces/{n}_{species}{n}_{h}{k}{l}/")
    if not os.path.exists(dir):
        os.makedirs(dir, exist_ok=True)
    path = dir / "slab.vasp"
    write(path, slab, format='vasp', direct=True)
    graphic_dir = dir / "graphics"
    if not os.path.exists(graphic_dir):
        os.makedirs(graphic_dir, exist_ok=True)
    # Generate images for each pair with different rotations
    angles = [
        [-90, 0, 0],
        [90, 0, 0],
        [0, 90, 0],
        [0, -90, 0],
        [0, 0, 90],
        [0, 0, -90],
        [-45, -45, -45],
        [45, 45, 45],
    ]
    for angle in angles:
        rotation = f"{angle[0]}x,{angle[1]}y,{angle[2]}z"
        write(graphic_dir / f"slab_a{angle[0]}_b{angle[1]}_c{angle[2]}.png", slab, rotation=rotation, scale=300)