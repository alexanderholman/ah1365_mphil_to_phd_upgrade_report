#!/usr/bin/env python3

import os
import re
from pathlib import Path

def extract_miller_planes(struc_dat_path: Path):
    """Extract lower and upper Miller planes from a struc_dat.txt file."""
    lower_miller = upper_miller = None
    with struc_dat_path.open() as f:
        for line in f:
            if "Lower crystal Miller plane:" in line:
                lower_miller = ''.join(re.findall(r"-?\d+", line.strip()))
            if "Upper crystal Miller plane:" in line:
                upper_miller = ''.join(re.findall(r"-?\d+", line.strip()))
            if lower_miller and upper_miller:
                break
    return lower_miller, upper_miller

def main():
    base_dir = Path.cwd()
    common_dir = base_dir / "artemis_utilities" / "common"
    interface_dir = base_dir / "DINTERFACES"

    # Read common templates
    sbatch_template_path = common_dir / "SBATCH_MLP_MACE.tpl"
    run_mace_template_path = common_dir / "run-mace.py"

    if not sbatch_template_path.exists() or not run_mace_template_path.exists():
        print("❌ Missing common SBATCH template or run-mace.py!")
        return

    sbatch_template = sbatch_template_path.read_text()
    run_mace_script = run_mace_template_path.read_text()

    count = 0

    for dirpath, dirnames, filenames in os.walk(interface_dir):
        path = Path(dirpath)
        if "POSCAR" in filenames:
            # Find nearest struc_dat.txt upwards
            struc_dat = None
            for ancestor in path.parents:
                candidate = ancestor / "struc_dat.txt"
                if candidate.exists():
                    struc_dat = candidate
                    break
            if not struc_dat:
                print(f"⚠️ No struc_dat.txt found for {path}, skipping.")
                continue

            # Extract Miller indices
            lower, upper = extract_miller_planes(struc_dat)
            if not lower or not upper:
                print(f"⚠️ Could not extract Miller planes from {struc_dat}, skipping.")
                continue

            # Write customized SBATCH_MLP_MACE
            sbatch_file = path / "SBATCH_MLP_MACE"
            sbatch_file.write_text(sbatch_template.format(lm=lower, um=upper))

            # Write run-mace.py
            run_mace_dest = path / "run-mace.py"
            run_mace_dest.write_text(run_mace_script)
            run_mace_dest.chmod(0o755)

            print(f"✅ Set up SBATCH_MLP_MACE and run-mace in {path}")
            count += 1

    print(f"\n✅ Completed setup in {count} POSCAR folders.")

if __name__ == "__main__":
    main()
