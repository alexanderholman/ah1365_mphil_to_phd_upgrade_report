#!/usr/bin/env python3
import argparse
import re
from ase.io import read
from datetime import datetime
from pathlib import Path
import json
import numpy as np
import pandas as pd
import csv

def is_contcar_broken(path):
    """
    Returns True if the CONTCAR file contains 'nan' or invalid coordinates.
    """
    try:
        with open(path, 'r') as f:
            lines = f.readlines()

        # Atom counts: sum all entries on line 6
        atom_counts = list(map(int, lines[6].strip().split()))
        total_atoms = sum(atom_counts)

        # Coordinates start 2 lines after atom counts
        coord_start = 8
        coord_lines = lines[coord_start:coord_start + total_atoms]

        for line in coord_lines:
            parts = line.strip().split()
            if len(parts) < 3:
                return True  # incomplete line
            try:
                coords = [float(p) for p in parts[:3]]
                if any(np.isnan(coords)):
                    return True
            except ValueError:
                return True  # non-numeric values
        return False

    except Exception as e:
        #print(f"Error reading {path}: {e}")
        return None  # fail-safe: assume broken

def extract_energy_from_mace_outcar(filename):
    try:
        with open(filename, 'r') as f:
            for line in f:
                if line.startswith("MACE Energy:"):
                    match = re.search(r"([-+]?[0-9]*\.?[0-9]+)", line)
                    if match:
                        return float(match.group(1))
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    return None

def extract_energy_from_outcar(filename):
    pattern = r"energy\s+without entropy=\s+([-+]?[0-9]*\.?[0-9]+)"
    try:
        with open(filename, 'r') as f:
            for line in f:
                m = re.search(pattern, line.lstrip())
                if m:
                    return float(m.group(1))
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    return None

def extract_compute_time_from_outfile(filename):
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
            start_time = None
            end_time = None
            for line in lines:
                line = line.strip()
                if line.startswith("Job started on:"):
                    start_time = line.split("Job started on:")[1].strip().replace("\\n", "")
                elif line.startswith("Job ended on:"):
                    end_time = line.split("Job ended on:")[1].strip().replace("\\n", "")
            if start_time and end_time:
                possible_formates = [
                    '%u', # e.g. "Mon 01 Jan 00:00:00 AM UTC 2023"
                    '%a %d %b %H:%M:%S %Z %Y',  # e.g. "Mon 01 Jan 00:00:00 UTC 2023"
                    '%a %d %b %H:%M:%S %p %Z %Y',  # e.g. "Mon 01 Jan 00:00:00 AM UTC 2023"
                ]
                for fmt in possible_formates:
                    try:
                        start_dt = datetime.strptime(start_time, fmt)
                        end_dt = datetime.strptime(end_time, fmt)
                        return (end_dt - start_dt).total_seconds()
                    except ValueError:
                        continue
    except Exception as e:
        print(f"Error reading compute time from {filename}: {e}")
    return None

def extract_mismatch_from_struc_data(filename):
    vector_mismatch = None
    angle_mismatch = None
    area_mismatch = None
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if line.startswith("vector mismatch"): # e.g. " vector mismatch (%) = .000000000"
                    vector_mismatch = float(line.split('=')[1])
                elif line.startswith("angle mismatch"):
                    angle_mismatch = float(line.split('=')[1])
                elif line.startswith("area mismatch"):
                    area_mismatch = float(line.split('=')[1])
    except Exception as e:
        print(f"Error reading mismatch data from {filename}: {e}")
    return vector_mismatch, angle_mismatch, area_mismatch

def extract_is_primitive_cell_from_struc_data(filename):
    material_lower_primitive_cell = None
    material_upper_primitive_cell = None
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if line.startswith("Lower material primitive cell used:"): # e.g. "Lower material primitive cell used: F" or "Lower material primitive cell used: T"
                    material_lower_primitive_cell = line.split(':')[1].strip().lower() == 't'
                elif line.startswith("Upper material primitive cell used:"): # e.g. "Upper material primitive cell used: F" or "Upper material primitive cell used: T"
                    material_upper_primitive_cell = line.split(':')[1].strip().lower() == 't'
    except Exception as e:
        print(f"Error reading primitive cell data from {filename}: {e}")
    return material_lower_primitive_cell, material_upper_primitive_cell


def lower_to_rgb(material_lower_percent):
    if material_lower_percent is None:
        return 0, 0, 0
    si_frac = material_lower_percent / 100
    if si_frac >= 0.5:
        ratio = (si_frac - 0.5) * 2
        r = int(0 + ratio * 255)
        g = int(255 - ratio * 255)
        b = 0
    else:
        ratio = si_frac * 2
        r = int(127 * (1 - ratio) + 0 * ratio)
        g = int(0 * (1 - ratio) + 255 * ratio)
        b = int(255 * (1 - ratio) + 0 * ratio)
    return r / 255, g / 255, b / 255

def rankdiff_to_rgb(rank_diff, diff_min, diff_max):
    if rank_diff < 0:
        ratio = (rank_diff - diff_min) / abs(diff_min)
        r = int(127 * (1 - ratio))
        g = int(255 * ratio)
        b = int(255 * (1 - ratio))
    elif rank_diff > 0:
        ratio = rank_diff / diff_max
        r = int(255 * ratio)
        g = int(255 * (1 - ratio))
        b = 0
    else:
        r, g, b = 0, 255, 0
    return r / 255, g / 255, b / 255

bulks = {
    "C": {
        "structure": None,
        "E_dft": None,
        "E_mlp": None,
    },
    "Si": {
        "structure": None,
        "E_dft": None,
        "E_mlp": None,
    },
    "Ge": {
        "structure": None,
        "E_dft": None,
        "E_mlp": None,
    },
    "Sn": {
        "structure": None,
        "E_dft": None,
        "E_mlp": None,
    },
}

for name in bulks.keys():
    bulk_dir = Path(f"../structures/bulks/{name}/")
    print(f"Loading on bulk {name} from {bulk_dir}.")
    if not bulk_dir.exists():
        print(f"Bulk directory {bulk_dir} does not exist, skipping.")
        continue
    bulk_poscar = bulk_dir / "POSCAR"
    if not bulk_poscar.exists():
        print(f"POSCAR file {bulk_poscar} does not exist, skipping.")
        continue
    bulks[name]['structure'] = read(bulk_poscar)
    dft_outcar = bulk_dir / "OUTCAR"
    if dft_outcar.exists():
        bulks[name]['E_dft'] = extract_energy_from_outcar(dft_outcar)
    mlp_outcar = bulk_dir / "OUTCAR_MLP_MACE"
    if mlp_outcar.exists():
        bulks[name]['E_mlp'] = extract_energy_from_mace_outcar(mlp_outcar)

def main():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('-r', '--read', type=str, required=False, default='SBATCH_DFT_VASP.tpl', help='Input tpl file to read from')
    parser.add_argument('-l', '--lower', type=str, required=False, default=None, help='Filter results by lower material (e.g. Si, Ge, Sn)')
    parser.add_argument('-u', '--upper', type=str, required=False, default=None, help='Filter results by upper material (e.g. Si, Ge, Sn)')
    args = parser.parse_args()

    data_dir = Path("../structures/interfaces/")
    if not data_dir.exists():
        print(f"Data directory {data_dir} does not exist.")
        return

    interface_dirs = list(data_dir.glob("*/"))
    interface_dirs_count = len(interface_dirs)

    print(f"Found {interface_dirs_count} interface directories in {data_dir}")

    results = []

    for interface_dir in interface_dirs:
        if interface_dir.exists():
            name = interface_dir.name
            poscar_filename = "POSCAR"
            poscar_path = interface_dir / poscar_filename
            if not poscar_path.exists():
                print(f"POSCAR file {poscar_path} does not exist, skipping.")
                continue
            dft_dft_outcar_filename = "OUTCAR"
            dft_dft_outcar_path = interface_dir / dft_dft_outcar_filename
            # if not dft_dft_outcar_path.exists():
            #     print(f"OUTCAR file {dft_dft_outcar_path} does not exist, skipping.")
            #     continue
            dft_mlp_outcar_filename = "OUTCAR_DFT_MLP_MACE"
            dft_mlp_outcar_path = interface_dir / dft_mlp_outcar_filename
            # if not dft_mlp_outcar_path.exists():
            #     print(f"OUTCAR_DFT_MLP_MACE file {dft_mlp_outcar_path} does not exist, skipping.")
            #     continue
            dft_outfile_filename = "DFTVasp.out"
            dft_outfile_path = interface_dir / dft_outfile_filename
            # if not dft_outfile_path.exists():
            #     print(f"DFTVasp.out file {dft_outfile_path} does not exist, skipping.")
            #     continue
            dft_contcar_filename = "CONTCAR"
            dft_contcar_path = interface_dir / dft_contcar_filename
            # if not dft_contcar_path.exists():
            #     print(f"CONTCAR file {dft_contcar_path} does not exist, skipping.")
            #     continue
            mlp_mlp_outcar_filename = "OUTCAR_MLP_MACE"
            mlp_mlp_outcar_path = interface_dir / mlp_mlp_outcar_filename
            # if not mlp_outcar_path.exists():
            #     print(f"OUTCAR_MLP_MACE file {mlp_outcar_path} does not exist, skipping.")
            #     continue
            mlp_dft_outcar_filename = "OUTCAR_MLP_MACE_DFT"
            mlp_dft_outcar_path = interface_dir / mlp_dft_outcar_filename
            # if not mlp_dft_outcar_path.exists():
            #     print(f"OUTCAR_MLP_MACE_DFT file {mlp_dft_outcar_path} does not exist, skipping.")
            #     continue
            mlp_outfile_filename = "MLPMACE.out"
            mlp_outfile_path = interface_dir / mlp_outfile_filename
            # if not mlp_outfile_path.exists():
            #     print(f"MLPMACE.out file {mlp_outfile_path} does not exist, skipping.")
            #     continue
            mlp_contcar_filename = "CONTCAR_MLP_MACE"
            mlp_contcar_path = interface_dir / mlp_contcar_filename
            # if not mlp_contcar_path.exists():
            #     print(f"CONTCAR_MLP_MACE file {mlp_contcar_path} does not exist, skipping.")
            #     continue
            struct_data_filename = "struc_data.txt"
            struct_data_dir = interface_dir / "artemis/generated_files/"
            struct_data_path = struct_data_dir / struct_data_filename
            # if not struct_data_path.exists():
            #     print(f"struc_data.txt file {struct_data_path} does not exist, skipping.")
            #     continue

            poscar_data_json_filename = "poscar_data.json"
            poscar_data_json_path = interface_dir / poscar_data_json_filename
            # if not poscar_data_json_path.exists():
            #     print(f"poscar_data.json file {poscar_data_json_path} does not exist, skipping.")
            #     continue
            poscar_data = None
            if poscar_data_json_path.exists():
                try:
                    with open(poscar_data_json_path, 'r') as f:
                        poscar_data = json.load(f)
                except Exception as e:
                    print(f"Error reading {poscar_data_json_path}: {e}")
                    continue

            interface_electron_n = None
            nelect_filename = "nelect.txt"
            nelect_path = interface_dir / nelect_filename
            if not nelect_path.exists():
                print(f"nelect file {nelect_path} does not exist, skipping.")
                continue
            try:
                with open(nelect_path, 'r') as f:
                    interface_electron_n = int(f.read().strip())
            except Exception as e:
                print(f"Error reading electron number from {nelect_path}: {e}")
                continue

            lower_filename = "lower.vasp"
            lower_dir = interface_dir / "artemis/generation_files/"
            lower_path = lower_dir / lower_filename
            if not lower_path.exists():
                print(f"Lower file {lower_path} does not exist, skipping.")
                continue
            upper_filename = "upper.vasp"
            upper_dir = interface_dir / "artemis/generation_files/"
            upper_path = upper_dir / upper_filename
            if not upper_path.exists():
                print(f"Upper file {upper_path} does not exist, skipping.")
                continue

            lower_structure = read(lower_path)
            if not lower_structure:
                print(f"Failed to read lower structure from {lower_path}, skipping.")
                continue

            material_lower = lower_structure[0].symbol
            material_lower_n = len(lower_structure)
            material_lower_bulk_atoms = bulks[material_lower]['structure']
            material_lower_bulk_n = len(material_lower_bulk_atoms)
            material_lower_bulk_E_dft = bulks[material_lower]['E_dft']
            material_lower_bulk_E_mlp = bulks[material_lower]['E_mlp']

            upper_structure = read(upper_path)
            if not upper_structure:
                print(f"Failed to read upper structure from {upper_path}, skipping.")
                continue

            material_upper = upper_structure[0].symbol
            material_upper_n = len(upper_structure)
            material_upper_bulk_atoms = bulks[material_upper]['structure']
            material_upper_bulk_n = len(material_upper_bulk_atoms)
            material_upper_bulk_E_dft = bulks[material_upper]['E_dft']
            material_upper_bulk_E_mlp = bulks[material_upper]['E_mlp']

            interface_structure = read(poscar_path)
            if not interface_structure:
                print(f"Failed to read structure from {poscar_path}, skipping.")
                continue
            interface_atoms_n = len(interface_structure)

            material_lower_percent = (material_lower_n / interface_atoms_n) * 100 if interface_atoms_n else None

            dft_nodes = 4
            mlp_nodes = 1

            interface_E_dft_dft = None
            interface_E_form_delta_dft_dft = None
            interface_E_dft_mlp = None
            interface_E_form_delta_dft_mlp = None
            interface_E_bulk_form_dft = None
            interface_compute_time_per_electron_dft = None
            interface_E_mlp_mlp = None
            interface_E_form_delta_mlp_mlp = None
            interface_E_mlp_dft = None
            interface_E_form_delta_mlp_dft = None
            interface_E_bulk_form_mlp = None
            interface_compute_time_per_electron_mlp = None
            mlp_n_times_faster = None
            fill_colour = None
            is_valid = False

            if dft_dft_outcar_path.exists():
                interface_E_dft_dft = extract_energy_from_outcar(dft_dft_outcar_path)
                interface_E_bulk_form_dft = (material_lower_bulk_E_dft + material_upper_bulk_E_dft) / (material_lower_bulk_n + material_upper_bulk_n)
                interface_E_form_delta_dft_dft = (interface_E_dft_dft - (material_lower_n * material_lower_bulk_E_dft / material_lower_bulk_n) - (material_upper_n * material_upper_bulk_E_dft / material_upper_bulk_n)) / interface_atoms_n
                interface_compute_time_dft = extract_compute_time_from_outfile(dft_outfile_path)
                interface_compute_time_per_electron_dft = interface_compute_time_dft * dft_nodes / interface_electron_n if interface_compute_time_dft else None
                if dft_mlp_outcar_path.exists():
                    interface_E_dft_mlp = extract_energy_from_mace_outcar(dft_mlp_outcar_path)

            if mlp_mlp_outcar_path.exists():
                interface_E_mlp_mlp = extract_energy_from_mace_outcar(mlp_mlp_outcar_path)
                interface_E_bulk_form_mlp = (material_lower_bulk_E_mlp + material_upper_bulk_E_mlp) / (material_lower_bulk_n + material_upper_bulk_n)
                interface_E_form_delta_mlp_mlp = (interface_E_mlp_mlp - (material_lower_n * material_lower_bulk_E_mlp / material_lower_bulk_n) - (material_upper_n * material_upper_bulk_E_mlp / material_upper_bulk_n)) / interface_atoms_n
                interface_compute_time_mlp = extract_compute_time_from_outfile(mlp_outfile_path)
                interface_compute_time_per_electron_mlp = interface_compute_time_mlp * mlp_nodes / interface_electron_n if interface_compute_time_mlp else None
                if mlp_dft_outcar_path.exists():
                    interface_E_mlp_dft = extract_energy_from_mace_outcar(mlp_dft_outcar_path)

            if interface_E_dft_mlp is not None and interface_E_bulk_form_mlp is not None:
                interface_E_form_delta_dft_mlp = (interface_E_dft_mlp - (material_lower_n * material_lower_bulk_E_mlp / material_lower_bulk_n) - (material_upper_n * material_upper_bulk_E_mlp / material_upper_bulk_n)) / interface_atoms_n

            if dft_dft_outcar_path.exists() and mlp_mlp_outcar_path.exists() and interface_compute_time_per_electron_dft is not None and interface_compute_time_per_electron_mlp is not None:
                mlp_n_times_faster = interface_compute_time_per_electron_dft / interface_compute_time_per_electron_mlp
                fill_colour = lower_to_rgb(material_lower_percent)
                is_valid = interface_E_form_delta_dft_dft < 1.0


            # example name: 24_Ge24_001_001_a0.0_b0.0_c0.0_interface7shift1
            # explode on underscore
            name_parts = name.split('_')
            name_system_size = name_parts[0]  # e.g. "24"
            name_chemical_symbol = name_parts[1]  # e.g. "Ge24" or "Si24Ge24"
            name_lower_miller = name_parts[2] # e.g. "001"
            name_upper_miller = name_parts[3] # e.g. "001"
            name_shift_a = name_parts[4]  # e.g. "a0.0"
            name_shift_b = name_parts[5]  # e.g. "b0.0"
            name_shift_c = name_parts[6]  # e.g. "c0.0"
            name_interface_shift_swap = name_parts[7]  # e.g. "interface7shift1"

            interface_number = None
            shift_number = None
            swap_number = None
            if poscar_data.get('artemis'):
                if poscar_data.get('artemis').get('interface'):
                    interface_number = poscar_data.get('artemis').get('interface')
                if poscar_data.get('artemis').get('shift'):
                    shift_number = poscar_data.get('artemis').get('shift')
                if poscar_data.get('artemis').get('swap'):
                    swap_number = poscar_data.get('artemis').get('swap')
            else:
                match = re.match(r'interface(\d+)(?:shift(\d+))?(?:swap(\d+))?', name_interface_shift_swap)
                if match:
                    interface_number = int(match.group(1))
                    shift_number = int(match.group(2)) if match.group(2) else None
                    swap_number = int(match.group(3)) if match.group(3) else None

            material_lower_primitive_cell = None
            material_lower_termination_min_layer_loc = None
            material_lower_termination_max_layer_loc = None
            material_lower_termination_n_atoms = None
            material_lower_miller_hkl = None
            material_lower_miller_h = None
            material_lower_miller_k = None
            material_lower_miller_l = None

            material_upper_primitive_cell = None
            material_upper_termination_min_layer_loc = None
            material_upper_termination_max_layer_loc = None
            material_upper_termination_n_atoms = None
            material_upper_miller_hkl = None
            material_upper_miller_h = None
            material_upper_miller_k = None
            material_upper_miller_l = None

            material_shift_a = None
            material_shift_b = None
            material_shift_c = None
            is_shift = None

            material_vector_mismatch_ = None
            material_angle_mismatch_ = None
            material_area_mismatch_ = None

            if poscar_data and poscar_data.get('struc_data'):
                material_lower_primitive_cell, material_upper_primitive_cell = extract_is_primitive_cell_from_struc_data(struct_data_path)

                # material_lower_primitive_cell = poscar_data.get('struc_data').get('lower_material_primitive_cell_used', None)
                material_lower_termination_min_layer_loc = poscar_data.get('struc_data').get('lower_termination')[0].get('min_layer_loc', None)
                material_lower_termination_max_layer_loc = poscar_data.get('struc_data').get('lower_termination')[0].get('max_layer_loc', None)
                material_lower_termination_n_atoms = poscar_data.get('struc_data').get('lower_termination')[0].get('n_atoms', None)
                material_lower_miller_h = poscar_data.get('struc_data').get('lower_crystal_miller_plane').get('h', None)
                material_lower_miller_k = poscar_data.get('struc_data').get('lower_crystal_miller_plane').get('k', None)
                material_lower_miller_l = poscar_data.get('struc_data').get('lower_crystal_miller_plane').get('l', None)
                material_lower_miller_hkl = f"{material_lower_miller_h}{material_lower_miller_k}{material_lower_miller_l}" if material_lower_miller_h is not None and material_lower_miller_k is not None and material_lower_miller_l is not None else None

                # material_upper_primitive_cell = poscar_data.get('struc_data').get('upper_material_primitive_cell_used', None)
                material_upper_termination_min_layer_loc = poscar_data.get('struc_data').get('upper_termination')[0].get('min_layer_loc', None)
                material_upper_termination_max_layer_loc = poscar_data.get('struc_data').get('upper_termination')[0].get('max_layer_loc', None)
                material_upper_termination_n_atoms = poscar_data.get('struc_data').get('upper_termination')[0].get('n_atoms', None)
                material_upper_miller_h = poscar_data.get('struc_data').get('upper_crystal_miller_plane').get('h', None)
                material_upper_miller_k = poscar_data.get('struc_data').get('upper_crystal_miller_plane').get('k', None)
                material_upper_miller_l = poscar_data.get('struc_data').get('upper_crystal_miller_plane').get('l', None)
                material_upper_miller_hkl = f"{material_upper_miller_h}{material_upper_miller_k}{material_upper_miller_l}" if material_upper_miller_h is not None and material_upper_miller_k is not None and material_upper_miller_l is not None else None

                material_shift_a = poscar_data.get('shift_data').get('a', None)
                material_shift_b = poscar_data.get('shift_data').get('b', None)
                material_shift_c = poscar_data.get('shift_data').get('c', None)

                is_shift = (material_shift_a + material_shift_b + material_shift_c) > 0.0 if material_shift_a is not None and material_shift_b is not None and material_shift_c is not None else None

                material_vector_mismatch_ = poscar_data.get('struc_data').get('vector_mismatch', None)
                material_angle_mismatch_ = poscar_data.get('struc_data').get('angle_mismatch', None)
                material_area_mismatch_ = poscar_data.get('struc_data').get('area_mismatch', None)

                if material_vector_mismatch_ is None or material_angle_mismatch_ is None or material_area_mismatch_ is None:
                    material_vector_mismatch_, material_angle_mismatch_, material_area_mismatch_ = extract_mismatch_from_struc_data(struct_data_path)


            is_swap = swap_number is not None

            result = {
                "name": name,
                "interface_number": interface_number,
                "shift_number": shift_number,
                "swap_number": shift_number,
                "material_lower": material_lower,
                "material_lower_primitive_cell": material_lower_primitive_cell,
                "material_lower_percent": material_lower_percent,
                "material_lower_bulk_n": material_lower_bulk_n,
                "material_lower_bulk_E_dft": material_lower_bulk_E_dft,
                "material_lower_bulk_E_mlp": material_lower_bulk_E_mlp,
                "material_lower_termination_min_layer_loc": material_lower_termination_min_layer_loc,
                "material_lower_termination_max_layer_loc": material_lower_termination_max_layer_loc,
                "material_lower_termination_n_atoms": material_lower_termination_n_atoms,
                "material_lower_miller_hkl": material_lower_miller_hkl,
                "material_lower_miller_h": material_lower_miller_h,
                "material_lower_miller_k": material_lower_miller_k,
                "material_lower_miller_l": material_lower_miller_l,
                "material_upper": material_upper,
                "material_upper_primitive_cell": material_upper_primitive_cell,
                "material_upper_bulk_n": material_upper_bulk_n,
                "material_upper_bulk_E_dft": material_upper_bulk_E_dft,
                "material_upper_bulk_E_mlp": material_upper_bulk_E_mlp,
                "material_upper_termination_min_layer_loc": material_upper_termination_min_layer_loc,
                "material_upper_termination_max_layer_loc": material_upper_termination_max_layer_loc,
                "material_upper_termination_n_atoms": material_upper_termination_n_atoms,
                "material_upper_miller_hkl": material_upper_miller_hkl,
                "material_upper_miller_h": material_upper_miller_h,
                "material_upper_miller_k": material_upper_miller_k,
                "material_upper_miller_l": material_upper_miller_l,
                "material_shift_a": material_shift_a,
                "material_shift_b": material_shift_b,
                "material_shift_c": material_shift_c,
                "material_vector_mismatch_%": material_vector_mismatch_,
                "material_angle_mismatch_°": material_angle_mismatch_,
                "material_area_mismatch_%": material_area_mismatch_,
                "interface_atoms_n": interface_atoms_n,
                "interface_electron_n": interface_electron_n,
                "interface_E_dft@dft": interface_E_dft_dft,
                "interface_E_dft@mlp": interface_E_dft_mlp,
                "interface_E_bulk_form_dft": interface_E_bulk_form_dft,
                "interface_E_form_delta_dft@dft": interface_E_form_delta_dft_dft,
                "interface_E_form_delta_dft@mlp": interface_E_form_delta_dft_mlp,
                "interface_compute_nodes_dft": dft_nodes,
                "interface_compute_time_seconds": None, # todo
                "interface_compute_time_per_electron_dft": interface_compute_time_per_electron_dft,
                "interface_E_mlp@mlp": interface_E_mlp_mlp,
                "interface_E_mlp@dft": None, # todo
                "interface_E_bulk_form_mlp": interface_E_bulk_form_mlp,
                "interface_E_form_delta_mlp@mlp": interface_E_form_delta_mlp_mlp,
                "interface_E_form_delta_mlp@dft": None, # todo
                "interface_compute_nodes_mlp": mlp_nodes,
                "interface_compute_time_seconds_mlp": None, # todo
                "interface_compute_time_per_electron_mlp": interface_compute_time_per_electron_mlp,
                "mlp_n_times_faster": mlp_n_times_faster,
                "dft_mlp_rank_distance": None,
                # todo: add more fields
                # todo: interfacial energies
                # todo: strain energies, compression, tension, shear (shift), torsion (angle)
                # todo: error dft - mlp
                # todo: quartile deviation
                # todo: calculate surface energy
                # todo: calculate surface energy per angstrom^2 of lower_surface
                # todo: calculate surface energy per angstrom^2 of upper_surface
                # todo: calculate interface energy per angstrom^2
                "fill_colour": fill_colour,
                "is_shift": is_shift,
                "is_swap": is_swap,
                "is_valid": is_valid,
                "is_comparable_dft@dft_mlp@mlp": interface_E_form_delta_dft_dft is not None and interface_E_form_delta_mlp_mlp is not None,
                "dft@dft_vs_mlp@mlp_rank_dft": None,
                "dft@dft_vs_mlp@mlp_rank_mlp": None,
                "dft@dft_vs_mlp@mlp_rank_distance": None,
                "dft@dft_vs_mlp@mlp_line_colour": None,
                "is_comparable_dft@dft_dft@mlp": interface_E_form_delta_dft_dft is not None and interface_E_form_delta_dft_mlp is not None,
                "dft@dft_vs_dft@mlp_rank_dft": None,
                "dft@dft_vs_dft@mlp_rank_mlp": None,
                "dft@dft_vs_dft@mlp_rank_distance": None,
                "dft@dft_vs_dft@mlp_line_colour": None,
                "is_comparable_mlp@dft_mlp@mlp": interface_E_form_delta_mlp_dft is not None and interface_E_form_delta_mlp_mlp is not None,
                "mlp@dft_vs_mlp@mlp_rank_dft": None,
                "mlp@dft_vs_mlp@mlp_rank_mlp": None,
                "mlp@dft_vs_mlp@mlp_rank_distance": None,
                "mlp@dft_vs_mlp@mlp_line_colour": None,
                "is_broken": is_contcar_broken(mlp_contcar_path)
            }
            results.append(result)

    write_name = "results"

    if args.lower:
        results = [result for result in results if result['material_lower'] == args.lower]
        write_name += f"_lower_{args.lower}"

    if args.upper:
        results = [result for result in results if result['material_upper'] == args.upper]
        write_name += f"_upper_{args.upper}"

    write_name += ".csv"

    comparables = [
        {
            "comparable": "is_comparable_dft@dft_mlp@mlp",
            "energy": {
                "dft": "interface_E_form_delta_dft@dft",
                "mlp": "interface_E_form_delta_mlp@mlp",
            },
            "rank": {
                "dft": "dft@dft_vs_mlp@mlp_rank_dft",
                "mlp": "dft@dft_vs_mlp@mlp_rank_mlp",
            },
            "distance": "dft@dft_vs_mlp@mlp_rank_distance",
            "line_colour": "dft@dft_vs_mlp@mlp_line_colour",
        },
        {
            "comparable": "is_comparable_dft@dft_dft@mlp",
            "energy": {
                "dft": "interface_E_form_delta_dft@dft",
                "mlp": "interface_E_form_delta_dft@mlp",
            },
            "rank": {
                "dft": "dft@dft_vs_dft@mlp_rank_dft",
                "mlp": "dft@dft_vs_dft@mlp_rank_mlp",
            },
            "distance": "dft@dft_vs_dft@mlp_rank_distance",
            "line_colour": "dft@dft_vs_dft@mlp_line_colour",
        },
        {
            "comparable": "is_comparable_mlp@dft_mlp@mlp",
            "energy": {
                "dft": "interface_E_form_delta_mlp@dft",
                "mlp": "interface_E_form_delta_mlp@mlp",
            },
            "rank": {
                "dft": "mlp@dft_vs_mlp@mlp_rank_dft",
                "mlp": "mlp@dft_vs_mlp@mlp_rank_mlp",
            },
            "distance": "mlp@dft_vs_mlp@mlp_rank_distance",
            "line_colour": "mlp@dft_vs_mlp@mlp_line_colour",
        }
    ]

    for comparable in comparables:
        comparable_results = [result for result in results if result[comparable["comparable"]] and not result["is_broken"]]
        dft_rank_name_map = {}
        dft_ranks = sorted(comparable_results, key=lambda x: x[comparable["energy"]["dft"]])
        for i, result in enumerate(dft_ranks):
            rank = i + 1
            name = result['name']
            if name not in dft_rank_name_map:
                dft_rank_name_map[name] = rank
        mlp_rank_name_map = {}
        mlp_ranks = sorted(comparable_results, key=lambda x: x[comparable["energy"]["mlp"]])
        for i, result in enumerate(mlp_ranks):
            rank = i + 1
            name = result['name']
            if name not in mlp_rank_name_map:
                mlp_rank_name_map[name] = rank

        for result in comparable_results:
            name = result['name']
            if name in dft_rank_name_map:
                result[comparable["rank"]["dft"]] = dft_rank_name_map[name]
            if name in mlp_rank_name_map:
                result[comparable["rank"]["mlp"]] = mlp_rank_name_map[name]
            if name in dft_rank_name_map and name in mlp_rank_name_map:
                rank_diff = max(dft_rank_name_map[name], mlp_rank_name_map[name]) - min(dft_rank_name_map[name], mlp_rank_name_map[name])
                result[comparable["distance"]] = rank_diff
                diff_min = min(dft_rank_name_map[name], mlp_rank_name_map[name])
                diff_max = max(dft_rank_name_map[name], mlp_rank_name_map[name])
                result[comparable["line_colour"]] = rankdiff_to_rgb(rank_diff, diff_min, diff_max)

    print(f"Writing results to {write_name}")
    print(f"Total results: {len(results)}")

    import csv
    output_file = Path(write_name)
    with output_file.open('w', newline='') as csvfile:
        fieldnames = results[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)

if __name__ == '__main__':
    main()