#!/usr/bin/env python3
import argparse

# Setup scripts
from scripts.calculate.nbands import main as calculate_nbands_main
from scripts.generate.potcar import main as generate_potcar_main
from scripts.generate.incar import main as generate_incar_main
from scripts.generate.kpoints import main as generate_kpoints_main

def main():
    parser = argparse.ArgumentParser(description="VASP Utilities Manager")
    # Generate scripts
    parser.add_argument("--generate-potcar", action="store_true", help="Generate POTCAR from POSCAR")
    parser.add_argument("--generate-incar", action="store_true", help="Generate INCAR from POSCAR and nbands.txt")
    parser.add_argument("--generate-kpoints", action="store_true", help="Generate KPOINTS from POSCAR")
    # Calculate scripts
    parser.add_argument("--calculate-nbands", action="store_true", help="Calculate minimum number of bands from POSCAR and POTCAR")
    # Full run
    parser.add_argument("--all", action="store_true", help="Full run: full setup + submit jobs")

    args = parser.parse_args()

    # Generate scripts
    if args.generate_potcar:
        generate_potcar_main()
    if args.generate_incar:
        generate_incar_main()
    if args.generate_kpoints:
        generate_kpoints_main()

    # Calculate scripts
    if args.calculate_nbands:
        calculate_nbands_main()

    # Run all in order
    if args.all:
        generate_potcar_main()
        calculate_nbands_main()
        generate_incar_main()
        generate_kpoints_main()

    if not any(vars(args).values()):
        parser.print_help()

if __name__ == "__main__":
    main()
