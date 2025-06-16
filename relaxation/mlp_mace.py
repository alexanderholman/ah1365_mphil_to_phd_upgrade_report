#!/usr/bin/env python3
from pathlib import Path

from ase.io import read, write
from ase.optimize import FIRE
from mace.calculators import mace_mp
import argparse

def main():
    parser = argparse.ArgumentParser(description="Relax `read` file with ASE MACE to `write` file")
    parser.add_argument('-r', '--read', type=str, required=False, default='POSCAR', help='Input file to read from')
    parser.add_argument('-w', '--write', type=str, required=False, default='CONTCAR', help='Output file to write to')
    parser.add_argument('-f', '--format', type=str, required=False, default='vasp', help='File format to read')
    parser.add_argument('-d', '--direct', type=bool, required=False, default=True, help='Write in direct coordinates')
    parser.add_argument('-m', '--model', type=str, required=False, default='../models/2024-01-07-mace-128-L2_epoch-199.model', help='Model file to use')
    parser.add_argument('--fmax', type=float, required=False, default=0.01, help='Maximum force allowed in the optimization')
    parser.add_argument('--dispersion', type=bool, required=False, default=True, help='Use dispersion correction')
    parser.add_argument('--dtype', type=str, required=False, default='float64', help='Data type to use')
    parser.add_argument('--pbc', type=bool, required=False, default=True, help='Use periodic boundary conditions')
    parser.add_argument('-v', '--verbose', type=bool, required=False, default=False, help='Verbose output')
    parser.add_argument('--debug', type=bool, required=False, default=False, help='Debug output')
    args = parser.parse_args()

    if args.debug:
        print(args)

    model = Path(args.model)
    if not model.exists():
        raise FileNotFoundError(f"Model file {args.model} does not exist.")
    read_from = Path(args.read)
    if not read_from.exists():
        raise FileNotFoundError(f"Input file {args.read} does not exist.")
    mlp = mace_mp(model, dispersion=args.dispersion, default_dtype=args.dtype)
    structure = read(read_from, format=args.format)
    structure.set_pbc(args.pbc)
    structure.calc = mlp
    opt = FIRE(structure)
    opt.run(fmax=args.fmax)
    write_to = Path(args.write)
    if not write_to.parent.exists():
        write_to.parent.mkdir(parents=True, exist_ok=True)
    write(write_to, structure, direct=args.direct, format=args.format)

if __name__ == '__main__':
    main()
