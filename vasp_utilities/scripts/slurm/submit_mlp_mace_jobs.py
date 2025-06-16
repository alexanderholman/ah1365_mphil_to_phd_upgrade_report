import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
import sys

# Set base paths
base_dir = Path.cwd()
src_dir = base_dir / "DINTERFACES"
run_base_dir = base_dir / "DRUN_MLP_MACE"
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
dest_dir = run_base_dir / timestamp

def copy_structure():
    if not src_dir.exists():
        print("DINTERFACES does not exist.")
        sys.exit(1)

    print(f"Creating destination path: {dest_dir}")
    dest_dir.mkdir(parents=True, exist_ok=True)

    print(f"Copying DINTERFACES to {dest_dir}")
    subprocess.run(["rsync", "-a", "--info=progress2", str(src_dir) + "/", str(dest_dir)], check=True)

def find_and_run_sbatch(path: Path):
    for root, dirs, files in os.walk(path):
        root_path = Path(root)
        if "POSCAR" in files:
            has_output = any(f.endswith("MLPMACE.out") for f in files)
            if not has_output:
                sbatch_file = root_path / "SBATCH_MLP_MACE"
                if sbatch_file.exists():
                    print(f"Submitting job in {root_path}")
                    try:
                        result = subprocess.run(["sbatch", "SBATCH_MLP_MACE"], cwd=root_path, capture_output=True, text=True)
                        if result.returncode != 0:
                            print(f"❌ sbatch failed in {root_path}")
                            print(result.stderr)
                            sys.exit(1)
                    except Exception as e:
                        print(f"❌ Error running sbatch in {root_path}: {e}")
                        sys.exit(1)
                else:
                    print(f"⚠️ No SBATCH_MLP_MACE file in {root_path}, skipping.")
            else:
                print(f"✅ Output exists in {root_path}, skipping.")
        else:
            continue

def main():
    copy_structure()
    print("Starting job submission...")
    find_and_run_sbatch(dest_dir)
    print("Done.")

if __name__ == "__main__":
    main()
