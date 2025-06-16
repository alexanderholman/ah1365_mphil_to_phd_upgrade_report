#!/usr/bin/env python3
import os
import subprocess
import datetime
import shutil


def run_command(cmd, cwd=None):
    """Helper to run a command and check its status."""
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        print(f"Command {' '.join(cmd)} failed in {cwd if cwd else os.getcwd()}")
    return result.returncode


if __name__ == "__main__":
    # 1. Generate interfaces
    print("Step 1: Generating interfaces...")
    ret = run_command(["python", "generate-interfaces.py"])
    if ret != 0:
        print("Error during interface generation.")
        exit(ret)

    # 2. Run MACE calculations in each interface directory
    print("Step 2: Running MACE calculations in each interface directory...")
    data_dir = os.path.join("data", "Si_Ge")
    if os.path.exists(data_dir):
        for interface in os.listdir(data_dir):
            interface_path = os.path.join(data_dir, interface)
            if os.path.isdir(interface_path):
                print(f"Running MACE in {interface_path}...")
                ret = run_command(["python", "run-mace.py"], cwd=interface_path)
                if ret != 0:
                    print(f"MACE run failed for {interface}")
    else:
        print(f"Data directory {data_dir} not found.")

    # 3. (Optional) VASP DFT calculations (assumed to be run externally)
    print("Step 3: VASP DFT calculations should be run now.")
    data_dir = os.path.join("data", "Si_Ge")
    if os.path.exists(data_dir):
        for interface in os.listdir(data_dir):
            interface_path = os.path.join(data_dir, interface)
            if os.path.isdir(interface_path):
                print(f"Running MACE in {interface_path}...")
                ret = run_command(["vasp_std"], cwd=interface_path)
                if ret != 0:
                    print(f"MACE run failed for {interface}")
    else:
        print(f"Data directory {data_dir} not found.")

    # 4. Analyze results
    print("Step 4: Analyzing results...")
    ret = run_command(["python", "analyse-results.py"])
    if ret != 0:
        print("Error during analysis.")

    print("Workflow complete.")
