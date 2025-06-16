#!/usr/bin/env python3

import os
from pathlib import Path

def main():
    base_dir = Path.cwd()
    interface_dir = base_dir / "DINTERFACES"

    if not interface_dir.exists():
        print("❌ DINTERFACES/ not found!")
        return

    sbatch_deleted = 0
    run_mace_deleted = 0

    for dirpath, dirnames, filenames in os.walk(interface_dir):
        path = Path(dirpath)

        if "POSCAR" in filenames:
            # SBATCH_MLP_MACE
            sbatch_file = path / "SBATCH_MLP_MACE"
            if sbatch_file.exists() and sbatch_file.is_file():
                sbatch_file.unlink()
                sbatch_deleted += 1
                print(f"🗑️ Deleted {sbatch_file}")

            # run-mace.py
            run_mace_file = path / "run-mace.py"
            if run_mace_file.exists() and run_mace_file.is_file():
                run_mace_file.unlink()
                run_mace_deleted += 1
                print(f"🗑️ Deleted {run_mace_file}")

    print("\n✅ Cleanup complete:")
    print(f"  - SBATCH_MLP_MACE files deleted: {sbatch_deleted}")
    print(f"  - run-mace.py files deleted: {run_mace_deleted}")

if __name__ == "__main__":
    main()
