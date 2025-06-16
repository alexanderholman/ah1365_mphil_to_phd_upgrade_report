import json
import numpy as np
from pathlib import Path
from ase.io import read, write
import argparse

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def get_interface_bounds(struc_data):
    bottom_max = max(layer["max_layer_loc"] for layer in struc_data["lower_termination"])
    top_min = min(layer["min_layer_loc"] for layer in struc_data["upper_termination"])
    return bottom_max, top_min

def classify_atoms(atoms, bottom_max, top_min):
    cell = atoms.get_cell()
    c_length = cell[2, 2]  # Assumes z stacking

    positions = atoms.get_positions()
    z_frac = positions[:, 2] / c_length

    bottom_idx = np.where(z_frac < bottom_max)[0]
    top_idx = np.where(z_frac > top_min)[0]
    interface_idx = np.where((z_frac >= bottom_max) & (z_frac <= top_min))[0]

    return bottom_idx, interface_idx, top_idx

def main():
    parser = argparse.ArgumentParser(description="Split structure based on orientation (not species).")
    parser.add_argument('-p', '--poscar', type=str, default='POSCAR', help='Input POSCAR or VASP file')
    parser.add_argument('-j', '--json', type=str, default='poscar_data.json', help='JSON file with orientation data')
    parser.add_argument('--bottom', type=str, default='bottom.vasp', help='Output file for bottom slab')
    parser.add_argument('--interface', type=str, default='interface.vasp', help='Output file for interface region')
    parser.add_argument('--top', type=str, default='top.vasp', help='Output file for top slab')

    args = parser.parse_args()

    atoms = read(args.poscar)
    data = load_json(args.json)
    struc_data = data["struc_data"]

    bottom_max, top_min = get_interface_bounds(struc_data)

    bottom_idx, interface_idx, top_idx = classify_atoms(atoms, bottom_max, top_min)

    bottom_atoms = atoms[bottom_idx]
    interface_atoms = atoms[interface_idx]
    top_atoms = atoms[top_idx]

    write(args.bottom, bottom_atoms, format='vasp', direct=True)
    if len(interface_atoms):
        write(args.interface, interface_atoms, format='vasp', direct=True)
    write(args.top, top_atoms, format='vasp', direct=True)

    print(f"Split complete.\nBottom atoms: {len(bottom_idx)}\nInterface atoms: {len(interface_idx)}\nTop atoms: {len(top_idx)}")

if __name__ == "__main__":
    main()
