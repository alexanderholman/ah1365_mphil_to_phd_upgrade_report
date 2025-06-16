import argparse
import re
from ase.io import read
from datetime import datetime
from pathlib import Path
import json


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


def a_to_rgb(material_a_percent):
    if material_a_percent is None:
        return 0, 0, 0
    si_frac = material_a_percent / 100
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
    args = parser.parse_args()

    data_dir = Path("../structures/perfect_alloys/")
    if not data_dir.exists():
        print(f"Data directory {data_dir} does not exist.")
        return

    perfect_alloy_dirs = list(data_dir.glob("*/"))
    perfect_alloy_dirs_count = len(perfect_alloy_dirs)

    print(f"Found {perfect_alloy_dirs_count} perfect_alloy directories in {data_dir}")

    results = []

    for perfect_alloy_dir in perfect_alloy_dirs:
        if perfect_alloy_dir.exists():
            name = perfect_alloy_dir.name
            poscar_filename = "POSCAR"
            poscar_path = perfect_alloy_dir / poscar_filename
            if not poscar_path.exists():
                print(f"POSCAR file {poscar_path} does not exist, skipping.")
                continue
            perfect_alloy_structure = read(poscar_path)
            if not perfect_alloy_structure:
                print(f"Failed to read structure from {poscar_path}, skipping.")
                continue
            dft_dft_outcar_filename = "OUTCAR"
            dft_dft_outcar_path = perfect_alloy_dir / dft_dft_outcar_filename
            # if not dft_dft_outcar_path.exists():
            #     print(f"OUTCAR file {dft_dft_outcar_path} does not exist, skipping.")
            #     continue
            dft_mlp_outcar_filename = "OUTCAR_DFT_MLP_MACE"
            dft_mlp_outcar_path = perfect_alloy_dir / dft_mlp_outcar_filename
            # if not dft_mlp_outcar_path.exists():
            #     print(f"OUTCAR_DFT_MLP_MACE file {dft_mlp_outcar_path} does not exist, skipping.")
            #     continue
            dft_outfile_filename = "DFTVasp.out"
            dft_outfile_path = perfect_alloy_dir / dft_outfile_filename
            # if not dft_outfile_path.exists():
            #     print(f"DFTVasp.out file {dft_outfile_path} does not exist, skipping.")
            #     continue
            dft_contcar_filename = "CONTCAR"
            dft_contcar_path = perfect_alloy_dir / dft_contcar_filename
            # if not dft_contcar_path.exists():
            #     print(f"CONTCAR file {dft_contcar_path} does not exist, skipping.")
            #     continue
            mlp_mlp_outcar_filename = "OUTCAR_MLP_MACE"
            mlp_mlp_outcar_path = perfect_alloy_dir / mlp_mlp_outcar_filename
            # if not mlp_outcar_path.exists():
            #     print(f"OUTCAR_MLP_MACE file {mlp_outcar_path} does not exist, skipping.")
            #     continue
            mlp_dft_outcar_filename = "OUTCAR_MLP_MACE_DFT"
            mlp_dft_outcar_path = perfect_alloy_dir / mlp_dft_outcar_filename
            # if not mlp_dft_outcar_path.exists():
            #     print(f"OUTCAR_MLP_MACE_DFT file {mlp_dft_outcar_path} does not exist, skipping.")
            #     continue
            mlp_outfile_filename = "MLPMACE.out"
            mlp_outfile_path = perfect_alloy_dir / mlp_outfile_filename
            # if not mlp_outfile_path.exists():
            #     print(f"MLPMACE.out file {mlp_outfile_path} does not exist, skipping.")
            #     continue
            mlp_contcar_filename = "CONTCAR_MLP_MACE"
            mlp_contcar_path = perfect_alloy_dir / mlp_contcar_filename
            # if not mlp_contcar_path.exists():
            #     print(f"CONTCAR_MLP_MACE file {mlp_contcar_path} does not exist, skipping.")
            #     continue
            struct_data_filename = "struc_data.txt"
            struct_data_dir = perfect_alloy_dir / "artemis/generated_files/"
            struct_data_path = struct_data_dir / struct_data_filename
            # if not struct_data_path.exists():
            #     print(f"struc_data.txt file {struct_data_path} does not exist, skipping.")
            #     continue

            poscar_data_json_filename = "poscar_data.json"
            poscar_data_json_path = perfect_alloy_dir / poscar_data_json_filename
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

            perfect_alloy_electron_n = None
            nelect_filename = "nelect.txt"
            nelect_path = perfect_alloy_dir / nelect_filename
            if not nelect_path.exists():
                print(f"nelect file {nelect_path} does not exist, skipping.")
                continue
            try:
                with open(nelect_path, 'r') as f:
                    perfect_alloy_electron_n = int(f.read().strip())
            except Exception as e:
                print(f"Error reading electron number from {nelect_path}: {e}")
                continue

            material_a = perfect_alloy_structure[0].symbol
            material_b = perfect_alloy_structure[1].symbol

            a_filename = "POSCAR"
            a_dir = perfect_alloy_dir / f"../../bulks/{material_a}/"
            a_path = a_dir / a_filename
            if not a_path.exists():
                print(f"Lower file {a_path} does not exist, skipping.")
                continue
            b_filename = "POSCAR"
            b_dir = perfect_alloy_dir / f"../../bulks/{material_b}/"
            b_path = b_dir / b_filename
            if not b_path.exists():
                print(f"B file {b_path} does not exist, skipping.")
                continue

            a_structure = read(a_path)
            if not a_structure:
                print(f"Failed to read a structure from {a_path}, skipping.")
                continue

            material_a_bulk_atoms = bulks[material_a]['structure']
            material_a_bulk_n = len(material_a_bulk_atoms)
            material_a_bulk_E_dft = bulks[material_a]['E_dft']
            material_a_bulk_E_mlp = bulks[material_a]['E_mlp']

            b_structure = read(b_path)
            if not b_structure:
                print(f"Failed to read b structure from {b_path}, skipping.")
                continue

            material_b_bulk_atoms = bulks[material_b]['structure']
            material_b_bulk_n = len(material_b_bulk_atoms)
            material_b_bulk_E_dft = bulks[material_b]['E_dft']
            material_b_bulk_E_mlp = bulks[material_b]['E_mlp']

            perfect_alloy_atoms_n = len(perfect_alloy_structure)

            material_a_n = 0

            for atom in perfect_alloy_structure:
                if atom.symbol == material_a:
                    material_a_n += 1

            material_a_percent = (material_a_n / perfect_alloy_atoms_n) * 100 if perfect_alloy_atoms_n else None

            dft_nodes = 4
            mlp_nodes = 1

            perfect_alloy_E_dft_dft = None
            perfect_alloy_E_form_delta_dft_dft = None
            perfect_alloy_E_dft_mlp = None
            perfect_alloy_E_form_delta_dft_mlp = None
            perfect_alloy_E_bulk_form_dft = None
            perfect_alloy_compute_time_per_electron_dft = None
            perfect_alloy_E_mlp_mlp = None
            perfect_alloy_E_form_delta_mlp_mlp = None
            perfect_alloy_E_mlp_dft = None
            perfect_alloy_E_form_delta_mlp_dft = None
            perfect_alloy_E_bulk_form_mlp = None
            perfect_alloy_compute_time_per_electron_mlp = None
            mlp_n_times_faster = None
            fill_colour = None
            is_valid = False

            if dft_dft_outcar_path.exists():
                perfect_alloy_E_dft_dft = extract_energy_from_outcar(dft_dft_outcar_path)
                perfect_alloy_E_bulk_form_dft = (material_a_bulk_E_dft + material_b_bulk_E_dft) / (material_a_bulk_n + material_b_bulk_n)
                perfect_alloy_E_form_delta_dft_dft = (perfect_alloy_E_bulk_form_dft - ((material_a_bulk_n * (material_a_bulk_E_dft / material_a_bulk_n)) + (material_b_bulk_n * (material_b_bulk_E_dft / material_b_bulk_n)))) / perfect_alloy_atoms_n
                perfect_alloy_compute_time_dft = extract_compute_time_from_outfile(dft_outfile_path)
                perfect_alloy_compute_time_per_electron_dft = perfect_alloy_compute_time_dft * dft_nodes / perfect_alloy_electron_n if perfect_alloy_compute_time_dft else None
                if dft_mlp_outcar_path.exists():
                    perfect_alloy_E_dft_mlp = extract_energy_from_mace_outcar(dft_mlp_outcar_path)

            if mlp_mlp_outcar_path.exists():
                perfect_alloy_E_mlp_mlp = extract_energy_from_mace_outcar(mlp_mlp_outcar_path)
                perfect_alloy_E_bulk_form_mlp = (material_a_bulk_E_mlp + material_b_bulk_E_mlp) / (material_a_bulk_n + material_b_bulk_n)
                perfect_alloy_E_form_delta_mlp_mlp = (perfect_alloy_E_bulk_form_mlp - ((material_a_bulk_n * (material_a_bulk_E_mlp / material_a_bulk_n)) + (material_b_bulk_n * (material_b_bulk_E_mlp / material_b_bulk_n)))) / perfect_alloy_atoms_n
                perfect_alloy_compute_time_mlp = extract_compute_time_from_outfile(mlp_outfile_path)
                perfect_alloy_compute_time_per_electron_mlp = perfect_alloy_compute_time_mlp * mlp_nodes / perfect_alloy_electron_n if perfect_alloy_compute_time_mlp else None
                if mlp_dft_outcar_path.exists():
                    perfect_alloy_E_mlp_dft = extract_energy_from_mace_outcar(mlp_dft_outcar_path)

            if perfect_alloy_E_dft_mlp is not None and perfect_alloy_E_bulk_form_mlp is not None:
                perfect_alloy_E_form_delta_dft_mlp = (perfect_alloy_E_bulk_form_mlp - ((material_a_bulk_n * (material_a_bulk_E_mlp / material_a_bulk_n)) + (material_b_bulk_n * (material_b_bulk_E_mlp / material_b_bulk_n)))) / perfect_alloy_atoms_n

            if dft_dft_outcar_path.exists() and mlp_mlp_outcar_path.exists() and perfect_alloy_compute_time_per_electron_dft is not None and perfect_alloy_compute_time_per_electron_mlp is not None:
                mlp_n_times_faster = perfect_alloy_compute_time_per_electron_dft / perfect_alloy_compute_time_per_electron_mlp
                fill_colour = a_to_rgb(material_a_percent)
                is_valid = perfect_alloy_E_form_delta_dft_dft < 1.0

            results.append({
                "name": name,
                "material_a_percent": material_a_percent,
                "material_a_bulk_n": material_a_bulk_n,
                "material_a_bulk_E_dft": material_a_bulk_E_dft,
                "material_a_bulk_E_mlp": material_a_bulk_E_mlp,
                "material_b": material_b,
                "material_b_bulk_n": material_b_bulk_n,
                "material_b_bulk_E_dft": material_b_bulk_E_dft,
                "material_b_bulk_E_mlp": material_b_bulk_E_mlp,
                "perfect_alloy_atoms_n": perfect_alloy_atoms_n,
                "perfect_alloy_electron_n": perfect_alloy_electron_n,
                "perfect_alloy_E_dft@dft": perfect_alloy_E_dft_dft,
                "perfect_alloy_E_dft@mlp": perfect_alloy_E_dft_mlp,
                "perfect_alloy_E_bulk_form_dft": perfect_alloy_E_bulk_form_dft,
                "perfect_alloy_E_form_delta_dft@dft": perfect_alloy_E_form_delta_dft_dft,
                "perfect_alloy_E_form_delta_dft@mlp": perfect_alloy_E_form_delta_dft_mlp,
                "perfect_alloy_compute_nodes_dft": dft_nodes,
                "perfect_alloy_compute_time_seconds": None, # todo
                "perfect_alloy_compute_time_per_electron_dft": perfect_alloy_compute_time_per_electron_dft,
                "perfect_alloy_E_mlp@mlp": perfect_alloy_E_mlp_mlp,
                "perfect_alloy_E_mlp@dft": None, # todo
                "perfect_alloy_E_bulk_form_mlp": perfect_alloy_E_bulk_form_mlp,
                "perfect_alloy_E_form_delta_mlp@mlp": perfect_alloy_E_form_delta_mlp_mlp,
                "perfect_alloy_E_form_delta_mlp@dft": None, # todo
                "perfect_alloy_compute_nodes_mlp": mlp_nodes,
                "perfect_alloy_compute_time_seconds_mlp": None, # todo
                "perfect_alloy_compute_time_per_electron_mlp": perfect_alloy_compute_time_per_electron_mlp,
                "mlp_n_times_faster": mlp_n_times_faster,
                "dft_mlp_rank_distance": None,
                # todo: add more fields
                # todo: interfacial energies
                # todo: strain energies, compression, tension, shear (shift), torsion (angle)
                # todo: error dft - mlp
                # todo: quartile deviation
                # todo: calculate surface energy
                # todo: calculate surface energy per angstrom^2 of a_surface
                # todo: calculate surface energy per angstrom^2 of b_surface
                # todo: calculate perfect_alloy energy per angstrom^2
                "fill_colour": fill_colour,
                "line_colour": None,
                "is_valid": is_valid,
                "is_comparable": perfect_alloy_E_form_delta_dft_dft is not None and perfect_alloy_E_form_delta_mlp_mlp is not None,
                "is_comparable_dft@dft_mlp@mlp": perfect_alloy_E_form_delta_dft_dft is not None and perfect_alloy_E_form_delta_mlp_mlp is not None,
                "dft@dft_vs_mlp@mlp_rank_dft": None,
                "dft@dft_vs_mlp@mlp_rank_mlp": None,
                "dft@dft_vs_mlp@mlp_rank_distance": None,
                "dft@dft_vs_mlp@mlp_line_colour": None,
                "is_comparable_dft@dft_dft@mlp": perfect_alloy_E_form_delta_dft_dft is not None and perfect_alloy_E_form_delta_dft_mlp is not None,
                "dft@dft_vs_dft@mlp_rank_dft": None,
                "dft@dft_vs_dft@mlp_rank_mlp": None,
                "dft@dft_vs_dft@mlp_rank_distance": None,
                "dft@dft_vs_dft@mlp_line_colour": None,
                "is_comparable_mlp@dft_mlp@mlp": perfect_alloy_E_form_delta_mlp_dft is not None and perfect_alloy_E_form_delta_mlp_mlp is not None,
                "mlp@dft_vs_mlp@mlp_rank_dft": None,
                "mlp@dft_vs_mlp@mlp_rank_mlp": None,
                "mlp@dft_vs_mlp@mlp_rank_distance": None,
                "mlp@dft_vs_mlp@mlp_line_colour": None,
                "is_broken": False
            })



    comparables = [
        {
            "comparable": "is_comparable_dft@dft_mlp@mlp",
            "energy": {
                "dft": "perfect_alloy_E_form_delta_dft@dft",
                "mlp": "perfect_alloy_E_form_delta_mlp@mlp",
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
                "dft": "perfect_alloy_E_form_delta_dft@dft",
                "mlp": "perfect_alloy_E_form_delta_dft@mlp",
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
                "dft": "perfect_alloy_E_form_delta_mlp@dft",
                "mlp": "perfect_alloy_E_form_delta_mlp@mlp",
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
        comparable_results = [result for result in results if result[comparable["comparable"]]]
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

    import csv
    output_file = Path("results_perfect_alloys.csv")
    with output_file.open('w', newline='') as csvfile:
        fieldnames = results[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)

if __name__ == '__main__':
    main()