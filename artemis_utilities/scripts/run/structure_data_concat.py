#!/usr/bin/env python3
import subprocess
import os
from pathlib import Path

def main():
    base_dir = Path.cwd()
    interface_dir = base_dir / "DINTERFACES"

    poscar_folders = []

    # Find all POSCAR directories
    for dirpath, dirnames, filenames in os.walk(interface_dir):
        path = Path(dirpath)
        if "POSCAR" in filenames and "concat_artemis_data.py" in filenames:
            poscar_folders.append(path)

    print(f"Found {len(poscar_folders)} POSCAR folders with concat_artemis_data.py")

    for folder in poscar_folders:
        print(f"🚀 Running concat_artemis_data.py in {folder}")
        subprocess.run(["python3", "concat_artemis_data.py"], cwd=folder)

    print("\n✅ All poscar_data.json files generated.")

if __name__ == "__main__":
    main()
