#!/usr/bin/env python3

import os
from pathlib import Path

def main():
    base_dir = Path.cwd()
    interface_dir = base_dir / "DINTERFACES"

    if not interface_dir.exists():
        print("❌ No DINTERFACES/ directory found!")
        return

    concat_deleted = 0
    poscar_json_deleted = 0

    for dirpath, dirnames, filenames in os.walk(interface_dir):
        path = Path(dirpath)

        # Delete concat_artemis_data.py if found
        concat_file = path / "concat_artemis_data.py"
        if concat_file.exists() and concat_file.is_file():
            concat_file.unlink()
            concat_deleted += 1
            print(f"🗑️ Deleted {concat_file}")

        # Delete poscar_data.json if found
        poscar_json = path / "poscar_data.json"
        if poscar_json.exists() and poscar_json.is_file():
            poscar_json.unlink()
            poscar_json_deleted += 1
            print(f"🗑️ Deleted {poscar_json}")

    print("\n✅ Cleanup complete:")
    print(f"  - concat_artemis_data.py files deleted: {concat_deleted}")
    print(f"  - poscar_data.json files deleted: {poscar_json_deleted}")

if __name__ == "__main__":
    main()
