import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Write a SLURM batch file for DFT VASP calculations")
    parser.add_argument('-r', '--read', type=str, required=False, default='SBATCH_DFT_VASP.tpl', help='Input tpl file to read from')
    parser.add_argument('-w', '--write', type=str, required=False, default='SBATCH_DFT_VASP', help='Output file to write to')
    parser.add_argument('--name', type=str, required=False, default='dft_calc', help='Name of the calculation, used in the SBATCH file')
    args = parser.parse_args()

    tpl_file = Path(args.read)
    tpl = tpl_file.read_text()
    file = Path(args.write)
    file.write_text(tpl.format(name=args.name))

if __name__ == '__main__':
    main()