#!/usr/bin/env python3

import re
from pathlib import Path

def extract_nbands():
    """Optional: Try to read NBANDS from nbands.txt if it exists."""
    nbands_file = Path.cwd() / "nbands.txt"
    if nbands_file.exists():
        try:
            with nbands_file.open() as f:
                nbands = int(f.read().strip())
                return nbands
        except Exception:
            pass
    return 48  # Default fallback NBANDS if no file is found

def extract_nelect():
    """Optional: Try to read NELECT from nelect.txt if it exists."""
    nelect_file = Path.cwd() / "nelect.txt"
    if nelect_file.exists():
        try:
            with nelect_file.open() as f:
                nelect = int(f.read().strip())
                return nelect
        except Exception:
            pass
    return 48  # Default fallback NBANDS if no file is found

def main():
    poscar_path = Path.cwd() / "POSCAR"
    incar_template_path = Path(__file__).resolve().parent.parent.parent / "common" / "INCAR.tpl"
    output_incar_path = Path.cwd() / "INCAR"

    if not poscar_path.exists():
        print("❌ POSCAR not found in current directory.")
        return
    if not incar_template_path.exists():
        print("❌ INCAR.tpl not found in vasp_utilities/common/.")
        return

    nbands = extract_nbands()
    nelect = extract_nelect()

    # Read INCAR template
    incar_template = incar_template_path.read_text()

    # Replace placeholders
    incar_final = incar_template.format(NBANDS=nbands, NELECT=nelect)

    # Write final INCAR
    with output_incar_path.open("w") as fout:
        fout.write(incar_final)

    print(f"✅ Generated INCAR with {nbands=}, {nelect=}")

if __name__ == "__main__":
    main()
