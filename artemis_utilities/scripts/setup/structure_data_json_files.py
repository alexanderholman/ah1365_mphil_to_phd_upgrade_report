#!/usr/bin/env python3

import os
from pathlib import Path

def main():
    base_dir = Path.cwd()
    common_dir = base_dir / "artemis_utilities" / "common"
    interface_dir = base_dir / "DINTERFACES"

    concat_script_path = common_dir / "concat_artemis_data.py"

    if not concat_script_path.exists():
        print("❌ Missing concat_artemis_data.py in artemis_utilities/common/")
        return

    count = 0

    for dirpath, dirnames, filenames in os.walk(interface_dir):
        path = Path(dirpath)
        if "POSCAR" in filenames:
            concat_dest = path / "concat_artemis_data.py"

            # Write the concat_artemis_data.py into each POSCAR folder
            concat_dest.write_text(concat_script_path.read_text())
            concat_dest.chmod(0o755)

            print(f"✅ Copied concat_artemis_data.py into {path}")
            count += 1

    print(f"\n✅ Setup complete: {count} POSCAR folders updated.")

if __name__ == "__main__":
    main()
