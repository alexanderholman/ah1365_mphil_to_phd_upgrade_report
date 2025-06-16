#!/usr/bin/env python3

from pathlib import Path

def read_species(poscar_path):
    """Reads the atomic species names from a POSCAR."""
    with poscar_path.open() as f:
        lines = f.readlines()

    if len(lines) < 6:
        raise ValueError("POSCAR file too short, missing species line.")

    species_line = lines[5].strip()
    species = species_line.split()
    return species

def main():
    base_dir = Path.cwd()
    poscar_path = base_dir / "POSCAR"
    common_potcars_dir = Path(__file__).resolve().parent.parent.parent / "common" / "POTCARS"
    output_potcar_path = base_dir / "POTCAR"

    if not poscar_path.exists():
        print("❌ POSCAR not found in current directory.")
        return

    # Read species list
    species_list = read_species(poscar_path)
    print(f"Detected species: {species_list}")

    potcar_contents = []

    for specie in species_list:
        specie_potcar_path = common_potcars_dir / specie / "POTCAR"
        if not specie_potcar_path.exists():
            print(f"❌ POTCAR for species '{specie}' not found in {specie_potcar_path}")
            return

        with specie_potcar_path.open() as f:
            potcar_contents.append(f.read())

    # Combine all POTCAR contents
    combined_potcar = "".join(potcar_contents)

    # Write final POTCAR
    with output_potcar_path.open("w") as fout:
        fout.write(combined_potcar)

    print(f"\n✅ Combined POTCAR written to {output_potcar_path}")

if __name__ == "__main__":
    main()
