#!/usr/bin/env python3

from pathlib import Path
import re
import math

def read_atom_numbers(poscar_path):
    """Reads the atom counts from a POSCAR."""
    with poscar_path.open() as f:
        lines = f.readlines()

    if len(lines) < 7:
        raise ValueError("POSCAR file too short, missing atom numbers line.")

    atom_nums_line = lines[6].strip()
    atom_nums = [int(x) for x in atom_nums_line.split()]
    return atom_nums

def read_zvals(potcar_path):
    """Reads the ZVALs from the POTCAR."""
    zvals = []
    with potcar_path.open() as f:
        for line in f:
            if "ZVAL" in line:
                match = re.search(r"ZVAL\s*=\s*([\d\.]+)", line)
                if match:
                    zvals.append(float(match.group(1)))
    return zvals

def main():
    base_dir = Path.cwd()
    poscar_path = base_dir / "POSCAR"
    potcar_path = base_dir / "POTCAR"
    nbands_output_path = base_dir / "nbands.txt"
    nelect_output_path = base_dir / "nelect.txt"

    if not poscar_path.exists() or not potcar_path.exists():
        print("❌ POSCAR or POTCAR not found in current directory.")
        return

    # Read atom counts
    atom_nums = read_atom_numbers(poscar_path)
    # Read ZVALs
    zvals = read_zvals(potcar_path)

    if len(atom_nums) != len(zvals):
        print(f"❌ Mismatch: {len(atom_nums)} atom types vs {len(zvals)} ZVALs.")
        return

    total_valence = 0
    for num_atoms, zval in zip(atom_nums, zvals):
        total_valence += num_atoms * zval

    total_valence = int(round(total_valence))

    # Calculate minimum bands
    min_bands = total_valence // 2
    if total_valence % 2 != 0:
        min_bands += 1

    # Add 20% extra
    nbands = int(math.ceil(min_bands * 1.2))

    # Print results
    print(f"the total number of valence electrons is:     {total_valence}")
    print(f"your minimum possible amount of bands is:     {min_bands}")
    print(f"a standard number of bands is (NBND+20%):     {nbands}")

    # Write NBANDS to nbands.txt
    with nbands_output_path.open("w") as fout:
        fout.write(f"{nbands}\n")

    print(f"\n✅ NBANDS value ({nbands}) written to {nbands_output_path}")

    # Write NBANDS to nbands.txt
    with nelect_output_path.open("w") as fout:
        fout.write(f"{total_valence}\n")

    print(f"✅ NELECT value ({total_valence}) written to {nelect_output_path}")

    return nbands

if __name__ == "__main__":
    main()
