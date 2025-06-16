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
            # SBATCH_DFT_VASP
            sbatch_file = path / "SBATCH_DFT_VASP"
            if sbatch_file.exists() and sbatch_file.is_file():
                sbatch_file.unlink()
                sbatch_deleted += 1
                print(f"🗑️ Deleted {sbatch_file}")

    print("\n✅ Cleanup complete:")
    print(f"  - SBATCH_DFT_VASP files deleted: {sbatch_deleted}")

if __name__ == "__main__":
    main()
