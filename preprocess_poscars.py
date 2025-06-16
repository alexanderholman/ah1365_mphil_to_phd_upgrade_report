from ase.io import read, write
import numpy as np

import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Write a SLURM batch file for DFT VASP calculations")
    parser.add_argument('-r', '--read', type=str, required=False, default='POSCAR', help='Input file to read from')
    parser.add_argument('-t', '--write-top', type=str, required=False, default='top.vasp', help='Output file for top material')
    parser.add_argument('-b', '--write-bottom', type=str, required=False, default='bottom.vasp', help='Output file for bottom material')
    parser.add_argument('-i', '--write-interface', type=str, required=False, default='interface.vasp', help='Output file for interface region')
    args = parser.parse_args()

    read_from = Path(args.read)
    if not read_from.exists():
        raise FileNotFoundError(f"Template file {args.read} does not exist.")

    write_to_top = Path(args.write_top)
    if not write_to_top.parent.exists():
        write_to_top.parent.mkdir(parents=True, exist_ok=True)

    write_to_bottom = Path(args.write_bottom)
    if not write_to_bottom.parent.exists():
        write_to_bottom.parent.mkdir(parents=True, exist_ok=True)

    write_to_interface = Path(args.write_interface)
    if not write_to_interface.parent.exists():
        write_to_interface.parent.mkdir(parents=True, exist_ok=True)


    # -----------------------------
    # 1) Read POSCAR and sort by z
    # -----------------------------
    atoms = read(read_from)  # ASE can read POSCAR files

    positions = atoms.get_positions()
    z_coords = positions[:, 2]
    sorted_indices = np.argsort(z_coords)

    # Reorder the atoms by ascending z
    atoms_sorted = atoms[sorted_indices]

    # After sorting, the bottom is at the start, top at the end
    z_sorted = atoms_sorted.get_positions()[:, 2]

    # ---------------------------------------------
    # 2) Identify which atoms are "A" vs "B" by symbol
    # ---------------------------------------------
    # Let's assume, for example, that your interface is made of
    #   - material A (e.g. "Al") and
    #   - material B (e.g. "Cu").
    # If you have more elements, you might group them by sets, or by tags.
    symbol_array = np.array([atom.symbol for atom in atoms_sorted])

    # Define functions to identify bottom and top materials
    # get first atom from atoms_sorted and use its symbol to define bottom
    # get last atom from atoms_sorted and use its symbol to define top
    bottom_species = atoms_sorted[0].symbol
    top_species = atoms_sorted[-1].symbol

    def is_bottom_material(sym):
        """Return True if symbol belongs to bottom material (A)."""
        return (sym == bottom_species)  # <--- Example


    def is_top_material(sym):
        """Return True if symbol belongs to top material (B)."""
        return (sym == top_species)  # <--- Example


    bottom_mask = np.array([is_bottom_material(sym) for sym in symbol_array])
    top_mask = np.array([is_top_material(sym) for sym in symbol_array])

    # -----------------------------------------------
    # 3) Find highest bottom and lowest top in z-space
    # -----------------------------------------------
    #   highest_bottom_z = max z among atoms that belong to bottom material
    #   lowest_top_z     = min z among atoms that belong to top material
    z_bottom = z_sorted[bottom_mask]
    z_top = z_sorted[top_mask]

    if len(z_bottom) == 0 or len(z_top) == 0:
        raise ValueError("Could not find bottom or top material in the structure!")

    highest_bottom_z = z_bottom.max()
    lowest_top_z = z_top.min()

    # -----------------------------------------------------------
    # 4) Determine if there's an overlap:
    #    If highest_bottom_z >= lowest_top_z, we have an interface region
    # -----------------------------------------------------------
    if highest_bottom_z < lowest_top_z:
        # No overlap -> effectively 2 regions: bottom & top
        print("No thick interface region found. Splitting into 2 parts.")

        # bottom part: all atoms with z <= highest_bottom_z
        # top part:    all atoms with z >= lowest_top_z
        # Everything in between is either vacuum or an abrupt boundary

        bottom_indices = [i for i, z in enumerate(z_sorted) if z <= highest_bottom_z]
        top_indices = [i for i, z in enumerate(z_sorted) if z >= lowest_top_z]

        bottom_atoms = atoms_sorted[bottom_indices]
        top_atoms = atoms_sorted[top_indices]

        # Write them out or keep them in memory
        write(write_to_bottom, bottom_atoms, format="vasp")
        write(write_to_top, top_atoms, format="vasp")

    else:
        # We have an interface region
        print("Thick interface region found. Splitting into 3 parts.")

        # Bottom region: z < highest_bottom_z, but only those atoms from the bottom material
        # Interface region: any atoms whose z is in [lowest_top_z, highest_bottom_z] OR
        #   any atoms from top/bottom material that "intrude" into that range
        # Top region: z > lowest_top_z, from top material

        bottom_indices = []
        interface_indices = []
        top_indices = []

        for i, atom in enumerate(atoms_sorted):
            z_val = z_sorted[i]
            sym = atom.symbol
            # belongs to bottom
            if is_bottom_material(sym) and z_val < highest_bottom_z:
                bottom_indices.append(i)
            # belongs to top
            elif is_top_material(sym) and z_val > lowest_top_z:
                top_indices.append(i)
            else:
                # everything else is interface
                interface_indices.append(i)

        bottom_atoms = atoms_sorted[bottom_indices]
        interface_atoms = atoms_sorted[interface_indices]
        top_atoms = atoms_sorted[top_indices]

        # Write them out or keep them in memory
        write(write_to_bottom, bottom_atoms, format="vasp", direct=True)
        write(write_to_interface, interface_atoms, format="vasp", direct=True)
        write(write_to_top, top_atoms, format="vasp", direct=True)

if __name__ == '__main__':
    main()