#!/usr/bin/env python3
import os
import sys
from ase.io import read
from ase.visualize import view
from ase.optimize import FIRE
from mace.calculators import mace_mp


def run_mace_calculation(poscar_path):
    """
    Dummy function to simulate a MACE calculation.
    Replace this with the actual MACE workflow.
    """
    energy = None
    try:
        macemp = mace_mp(model="large", dispersion=True, default_dtype="float64")
        structure = read(poscar_path, format='vasp')
        view(structure)
        structure.set_pbc(True)
        structure.calc = macemp
        opt = FIRE(structure)
        opt.run(fmax=0.01)
        energy = structure.get_potential_energy()
    except Exception as e:
        print(f"Error reading {poscar_path}: {e}")
        sys.exit(1)
    return energy


if __name__ == "__main__":
    poscar_file = "POSCAR"
    if not os.path.exists(poscar_file):
        print("POSCAR file not found in the current directory.")
        sys.exit(1)

    energy = run_mace_calculation(poscar_file)
    # Write the dummy energy to MACE_OUTCAR
    with open("MACE_OUTCAR", "w") as f:
        f.write(f"MACE Energy: {energy:.6f} eV\n")

    print(f"MACE calculation complete. Energy written to MACE_OUTCAR: {energy:.6f} eV")
