#!/usr/bin/env python3

import numpy as np
from pathlib import Path
import argparse

def read_lattice_vectors(poscar_path, return_reciprocal=False):
    """
    Reads the lattice vectors from a POSCAR file and returns them.
    Optionally returns the reciprocal lattice vectors as well if
    return_reciprocal is True.

    Parameters
    ----------
    poscar_path : Path
        Path to the POSCAR file.
    return_reciprocal : bool
        If True, also return reciprocal lattice vectors.

    Returns
    -------
    lattice : ndarray of shape (3, 3)
        The direct lattice vectors (in rows).
    reciprocal_lattice : ndarray of shape (3, 3), optional
        The reciprocal lattice vectors (in rows),
        only returned if return_reciprocal=True.
    """
    with poscar_path.open() as f:
        lines = f.readlines()

    if len(lines) < 5:
        raise ValueError("POSCAR file too short, missing lattice vectors.")

    # 1) Parse the scale factor
    scale_factor = float(lines[1].strip())

    # 2) Parse the direct lattice vectors
    lattice = np.array([
        [float(x) for x in lines[2].split()],
        [float(x) for x in lines[3].split()],
        [float(x) for x in lines[4].split()]
    ])
    lattice *= scale_factor

    if return_reciprocal:
        # 3) Compute the reciprocal lattice vectors
        #    The standard definition is G = 2π * (M^-1)^T
        reciprocal_lattice = 2 * np.pi * np.linalg.inv(lattice).T
        return lattice, reciprocal_lattice
    else:
        return lattice


def generate_kpoints(reciprocal_lattice, kspacing):
    """
    Generates a k-point mesh based on reciprocal lattice vectors
    and a desired k-point spacing (kspacing).

    Parameters
    ----------
    reciprocal_lattice : ndarray of shape (3, 3)
        Reciprocal lattice vectors (each row is a vector).
    kspacing : float
        Desired spacing in reciprocal space units (e.g., 1/Å).

    Returns
    -------
    kpoints : list of int
        Number of k-points along each reciprocal lattice direction.
    """
    # Calculate the length of each reciprocal vector
    lengths = np.linalg.norm(reciprocal_lattice, axis=1)

    # Decide how many points to use along each direction
    # Usually: (# of divisions) ~ (|G| / desired spacing)
    # And ensure at least 1 in each direction.
    kpoints = np.maximum(np.round(lengths / kspacing).astype(int), 1)

    return kpoints.tolist()

def main():
    parser = argparse.ArgumentParser(description="Generate VASP KPOINTS file",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Optional kcenter and kspacing, default to Gamma and 0.2 Å⁻¹
    parser.add_argument("--kcenter", choices=["gamma", "monkhorst"], default="gamma",
                        help="Centering for the k-point grid (default: gamma)")
    parser.add_argument("--kspacing", type=float, default=0.2, help="Desired k-point spacing in Å⁻¹ (default: 0.2)")

    args, unknown = parser.parse_known_args()

    base_dir = Path.cwd()
    poscar_path = base_dir / "POSCAR"
    kpoints_output_path = base_dir / "KPOINTS"

    if not poscar_path.exists():
        print("❌ POSCAR not found in current directory.")
        return

    # Read lattice vectors
    direct_lattice, reciprocal_lattice = read_lattice_vectors(poscar_path, return_reciprocal=True)

    # Generate k-points
    kpoints_grid = generate_kpoints(reciprocal_lattice, args.kspacing)

    print(f"📐 Lattice vector lengths: {np.linalg.norm(direct_lattice, axis=1)}")
    print(f"📐 Reciprocal Lattice vector lengths: {np.linalg.norm(reciprocal_lattice, axis=1)}")
    print(f"🔢 KPOINTS grid: {kpoints_grid}")
    print(f"🎯 Centering: {args.kcenter}")

    # Write KPOINTS file
    with kpoints_output_path.open("w") as f:
        f.write("Automatic KPOINTS generated\n")
        f.write("0\n")
        if args.kcenter.lower() == "gamma":
            f.write("Gamma\n")
        else:
            f.write("Monkhorst-Pack\n")
        f.write(f"{int(kpoints_grid[0])} {int(kpoints_grid[1])} {int(kpoints_grid[2])}\n")
        f.write("0 0 0\n")

    print(f"\n✅ KPOINTS file written to {kpoints_output_path}")


if __name__ == "__main__":
    main()
