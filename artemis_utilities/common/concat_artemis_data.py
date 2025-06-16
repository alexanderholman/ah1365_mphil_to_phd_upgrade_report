#!/usr/bin/env python3
"""
concat_artemis_data.py
----------------------
Place this script next to a POSCAR in a D# folder. When run, it will:
1) Detect whether we're in DSHIFT or DSWAP structure.
2) Find shift_vals.txt and struc_dat.txt via relative paths.
3) Parse their contents.
4) Produce poscar_data.json summarizing the info.

For DSHIFT:
  shift_vals_path = "../shift_vals.txt"
  struc_dat_path  = "../../struc_dat.txt"

For DSWAP:
  shift_vals_path = "../../../shift_vals.txt"
  struc_dat_path  = "../../../../struc_dat.txt"
"""

import os
import json
import re

def find_environment():
    """
    Determine if we're in DSHIFT or DSWAP and construct
    the correct relative paths for shift_vals.txt / struc_dat.txt.
    """

    cwd = os.getcwd()                     # e.g. ".../DSHIFT/D01"
    dir_name = os.path.basename(cwd)      # e.g. "D01"
    parent_dir = os.path.dirname(cwd)     # e.g. ".../DSHIFT"
    parent_name = os.path.basename(parent_dir)  # "DSHIFT" or "DSWAP" or something else

    is_swap = False
    shift_vals_rel = None
    struc_dat_rel  = None

    # CASE A: If we're *inside* a D# subdirectory, whose parent is DSHIFT
    if parent_name == "DSHIFT":
        is_swap = False
        # For DSHIFT:
        #   shift_vals => ../shift_vals.txt
        #   struc_dat  => ../../struc_dat.txt
        shift_vals_rel = os.path.join("..", "shift_vals.txt")
        struc_dat_rel  = os.path.join("..", "..", "struc_dat.txt")

    # CASE B: If we're *inside* a D# subdirectory, whose parent is DSWAP
    elif parent_name == "DSWAP":
        is_swap = True
        # For DSWAP:
        #   shift_vals => ../../../shift_vals.txt
        #   struc_dat  => ../../../../struc_dat.txt
        # Because we assume: POSCAR is in DSWAP/Dnn
        # up 1 => DSWAP
        # up 2 => parent of DSWAP
        # up 3 => shift_vals.txt
        # up 4 => struc_dat.txt
        shift_vals_rel = os.path.join("..", "..", "..", "shift_vals.txt")
        struc_dat_rel  = os.path.join("..", "..", "..", "..", "struc_dat.txt")

    # CASE C: If the current directory itself is DSHIFT
    elif dir_name == "DSHIFT":
        is_swap = False
        # shift_vals => shift_vals.txt
        # struc_dat  => ../struc_dat.txt
        shift_vals_rel = "shift_vals.txt"
        struc_dat_rel  = os.path.join("..", "struc_dat.txt")

    # CASE D: If the current directory itself is DSWAP
    elif dir_name == "DSWAP":
        is_swap = True
        # shift_vals => shift_vals.txt
        # struc_dat  => ../struc_dat.txt
        # (If you prefer different logic here, adjust as needed.)
        shift_vals_rel = "shift_vals.txt"
        struc_dat_rel  = os.path.join("..", "struc_dat.txt")

    # Otherwise, we might not be in a recognized structure
    return {
        "is_swap": is_swap,
        "shift_vals_relpath": shift_vals_rel,
        "struc_dat_relpath": struc_dat_rel
    }

def parse_shift_vals(filepath, target_interface_num):
    """
    Parse a shift_vals.txt file and return only the shift matching
    the current D## folder number.
    """
    result = None
    if not filepath or not os.path.isfile(filepath):
        return result

    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = re.match(r"(\S+)\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^,]+)\s*\)", line)
            if match:
                interface_num = match.group(1)
                if interface_num.zfill(2) == target_interface_num.zfill(2):
                    a_val = float(match.group(2).strip())
                    b_val = float(match.group(3).strip())
                    c_val = float(match.group(4).strip())
                    result = {
                        "interface_num": interface_num,
                        "shift_a": a_val,
                        "shift_b": b_val,
                        "shift_c": c_val
                    }
                    break
    return result

def parse_struc_dat(filepath):
    """
    Parse a struc_dat.txt of the form:

       Lower material primitive cell used: F
       Upper material primitive cell used: F

       Lattice match:
           a   b   c      a   b   c
           1  -1   0      1   1   0
          ...
       vector mismatch (%) = 3.284671533
       angle mismatch (°)  = .000000000
       area mismatch (%)   = .576260498

       Lower crystal Miller plane:   1   1   4
       ...
    """
    info = {}
    if not filepath or not os.path.isfile(filepath):
        return info

    with open(filepath, "r") as f:
        lines = f.readlines()

    for line in lines:
        line_str = line.strip()
        # vector mismatch
        if "vector mismatch (%)" in line_str:
            parts = line_str.split("=")
            valstr = parts[1].strip() if len(parts)>1 else ""
            try:
                info["vector_mismatch_percent"] = float(valstr)
            except ValueError:
                pass
        # angle mismatch
        elif "angle mismatch (°)" in line_str:
            parts = line_str.split("=")
            valstr = parts[1].strip() if len(parts)>1 else ""
            try:
                info["angle_mismatch_deg"] = float(valstr)
            except ValueError:
                pass
        # area mismatch
        elif "area mismatch (%)" in line_str:
            parts = line_str.split("=")
            valstr = parts[1].strip() if len(parts)>1 else ""
            try:
                info["area_mismatch_percent"] = float(valstr)
            except ValueError:
                pass
        # Lower crystal Miller plane
        elif "Lower crystal Miller plane:" in line_str:
            # e.g. "Lower crystal Miller plane: 1  1  4"
            parts = line_str.split(":")
            plane_str = parts[1].strip() if len(parts)>1 else ""
            coords = plane_str.split()
            if len(coords) == 3:
                try:
                    info["lower_miller_plane"] = [int(x) for x in coords]
                except:
                    pass
        # Upper crystal Miller plane
        elif "Upper crystal Miller plane:" in line_str:
            parts = line_str.split(":")
            plane_str = parts[1].strip() if len(parts)>1 else ""
            coords = plane_str.split()
            if len(coords) == 3:
                try:
                    info["upper_miller_plane"] = [int(x) for x in coords]
                except:
                    pass

    return info

def main():
    # 1) Figure out environment & relative paths
    env = find_environment()
    is_swap = env["is_swap"]
    shift_vals_rel = env["shift_vals_relpath"]
    struc_dat_rel = env["struc_dat_relpath"]

    cwd = os.getcwd()
    current_dir = os.path.basename(cwd)
    parent_dir = os.path.basename(os.path.dirname(cwd))

    if is_swap:
        # We're inside a DSWAP/D##
        shift_folder = os.path.basename(os.path.dirname(os.path.dirname(cwd)))  # up two levels
        shift_interface_num = shift_folder.lstrip("D").zfill(2)  # "D04" -> "04"
        swap_interface_num = current_dir.lstrip("D").zfill(2)    # "D03" -> "03"
    else:
        # Normal DSHIFT/D##
        shift_interface_num = current_dir.lstrip("D").zfill(2)
        swap_interface_num = None

    # 2) Parse the files if available
    shift_data = parse_shift_vals(shift_vals_rel, shift_interface_num) if shift_vals_rel else None
    struct_data = parse_struc_dat(struc_dat_rel) if struc_dat_rel else {}

    # 3) Build output dictionary
    result = {
        "is_swap": is_swap,
        "shift_vals_path": shift_vals_rel,
        "struc_dat_path": struc_dat_rel,
        "shift_data": shift_data,
        "struct_data": struct_data
    }

    if swap_interface_num is not None:
        result["swap_number"] = swap_interface_num

    # 4) Write poscar_data.json
    out_filename = "poscar_data.json"
    with open(out_filename, "w") as fout:
        json.dump(result, fout, indent=2)

    print(f"Created {out_filename}. Key info:")
    print(f"  is_swap = {is_swap}")
    print(f"  shift_vals_path = {shift_vals_rel}")
    print(f"  struc_dat_path  = {struc_dat_rel}")
    if shift_data:
        print(f"  shift_data = {shift_data}")
    else:
        print(f"  ⚠️ No shift data found for interface {shift_interface_num}")
    if swap_interface_num:
        print(f"  swap_number = {swap_interface_num}")


if __name__ == "__main__":
    main()
