import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Write a SLURM batch file for MLP MACE calculations")
    parser.add_argument('-r', '--read', type=str, required=False, default='SBATCH_MLP_MACE.tpl', help='Input tpl file to read from')
    parser.add_argument('-p', '--python-file', type=str, required=False, default='run_mace.py', help='Python file to run in the SBATCH script')
    parser.add_argument('-w', '--write', type=str, required=False, default='SBATCH_MLP_MACE', help='Output file to write to')
    parser.add_argument('--name', type=str, required=False, default='dft_calc', help='Name of the calculation, used in the SBATCH file')
    args = parser.parse_args()

    tpl_file = Path(args.read)
    if not tpl_file.exists():
        raise FileNotFoundError(f"Template file {args.read} does not exist.")
    tpl = tpl_file.read_text()
    file = Path(args.write)
    if not file.parent.exists():
        file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(tpl.format(name=args.name))

    python_file = Path(args.python_file)
    if not python_file.exists():
        raise FileNotFoundError(f"Python file {args.python_file} does not exist.")
    python_dest = file.parent / python_file.name
    if not python_dest.exists():
        python_dest.write_text(python_file.read_text())

if __name__ == '__main__':
    main()