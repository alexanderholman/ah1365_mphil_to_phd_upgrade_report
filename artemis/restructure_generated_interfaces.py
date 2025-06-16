# for each poscar path in a given directory:
import os
import json
from ase.io import read
from pathlib import Path
import argparse

def extract_shift_data(shift_data_path: Path, shift: int):
    try:
        with open(shift_data_path, 'r') as file:
            lines = file.readlines()
            line = lines[shift].strip()
            values = line.split('(')[1].split(')')[0].split(',')
            shift_values = [float(value.strip()) for value in values]
            return {
                'a': shift_values[0],
                'b': shift_values[1],
                'c': shift_values[2],
            }
    except IndexError:
        print(f"Error: Shift value {shift} is out of range for {shift_data_path}.")
        return None

def extract_struc_data(struc_data_path: Path):
    # read the struc.dat file and return the first line
    try:
        with open(struc_data_path, 'r') as file:
            lines = file.readlines()
            struc = {}
            lower_termination = False
            upper_termination = False
            termination_list = False
            for line in lines:
                line = line.strip()
                if line:
                    if line.startswith('Lower material primitive cell used:'):
                        struc['lower_material_primitive_cell_used'] = bool(line.split(':')[1].strip())
                    elif line.startswith('Upper material primitive cell used:'):
                        struc['upper_material_primitive_cell_used'] = bool(line.split(':')[1].strip())
                    elif line.startswith('vector mismatch'):
                        struc['vector_mismatch'] = float(line.split('=')[1].strip()) / 100.0
                    elif line.startswith(' angle mismatch'):
                        struc['angle_mismatch'] = float(line.split('=')[1].strip())
                    elif line.startswith('area mismatch'):
                        struc['area_mismatch'] = float(line.split('=')[1].strip()) / 100.0
                    elif line.startswith('Lower crystal Miller plane:'):
                        miller = [int(m) for m in line.split(':')[1].strip().split(' ') if m.isdigit()]
                        struc['lower_crystal_miller_plane'] = {
                            'h': int(miller[0]),
                            'k': int(miller[1]),
                            'l': int(miller[2]),
                        }
                        lower_termination = False
                        upper_termination = False
                        termination_list = False
                    elif line.startswith('Upper crystal Miller plane:'):
                        miller = [int(m) for m in line.split(':')[1].strip().split(' ') if m.isdigit()]
                        struc['upper_crystal_miller_plane'] = {
                            'h': int(miller[0]),
                            'k': int(miller[1]),
                            'l': int(miller[2]),
                        }
                        lower_termination = False
                        upper_termination = False
                        termination_list = False
                    elif line.startswith('Lower termination'):
                        lower_termination = True
                        upper_termination = False
                        struc['lower_termination'] = []
                        termination_list = True
                    elif line.startswith('Upper termination'):
                        upper_termination = True
                        lower_termination = False
                        struc['upper_termination'] = []
                        termination_list = True
                    elif termination_list:
                        parts = [p for p in line.split(' ') if p]
                        if parts[0].isdigit():
                            if lower_termination:
                                struc['lower_termination'].append({
                                    'term': int(parts[0]),
                                    'min_layer_loc': float(parts[1]),
                                    'max_layer_loc': float(parts[2]),
                                    'n_atoms': int(parts[3]),
                                })
                            elif upper_termination:
                                struc['upper_termination'].append({
                                    'term': int(parts[0]),
                                    'min_layer_loc': float(parts[1]),
                                    'max_layer_loc': float(parts[2]),
                                    'n_atoms': int(parts[3]),
                                })
            return struc
    except FileNotFoundError:
        print(f"Error: {struc_data_path} not found.")
        return None

def is_swap_poscar(poscar_path: Path):
    return poscar_path.parent.parent.name == "DSWAP"

def is_no_shift_poscar(poscar_path: Path):
    master_dir = poscar_path.parent.parent.parent.parent
    if not master_dir.name.startswith("DINTERFACE"):
        master_dir = master_dir.parent
    return master_dir.name.endswith("_NO_SHIFT")

def dshift_dir_path(poscar_path: Path):
    current_path = poscar_path
    while not current_path.name.startswith("DSHIFT"):
        current_path = current_path.parent
    return current_path

def master_dir_path(poscar_path: Path):
    current_path = poscar_path
    while not current_path.name.startswith("DINTERFACE"):
        current_path = current_path.parent
    return current_path

def base_dir_path(poscar_path: Path):
    master_dir = master_dir_path(poscar_path)
    return master_dir.parent

def extract_generation_file_paths(poscar_path: Path):
    lower_name = "lower.vasp"
    upper_name = "upper.vasp"
    base_dir = base_dir_path(poscar_path)
    lower_path = base_dir / lower_name
    upper_path = base_dir / upper_name
    generation_file_paths = {
        'lower_path': lower_path,
        'upper_path': upper_path,
        'param_in_path': base_dir / "default.param.in",
    }
    if is_no_shift_poscar(poscar_path):
        generation_file_paths['param_in_path'] = base_dir / "no_shift.param.in"
    return generation_file_paths

def extract_generated_file_paths(poscar_path: Path):
    settings_name = "settings.txt"
    shift_data_name = "shift_data.txt"
    struc_data_name = "struc_data.txt"
    dshift_dir_dir = dshift_dir_path(poscar_path)
    shift_data_path = dshift_dir_dir / shift_data_name
    struc_data_path = dshift_dir_dir.parent / struc_data_name
    master_dir = master_dir_path(poscar_path)
    settings_path = master_dir / settings_name
    base_dir = base_dir_path(poscar_path)
    generated_file_paths = {
        'artemis_output_path': base_dir / "artemis.default.out",
        'settings_path': settings_path,
        'struc_data_path': struc_data_path,
        'shift_data_path': shift_data_path,
    }
    if is_no_shift_poscar(poscar_path):
        generated_file_paths['artemis_output_path'] = base_dir / "artemis.no_shift.out"
    return generated_file_paths

# walk a object structure and when it encounters a PosixPath, convert it to a string
def convert_PosixPath_to_str(obj):
    if isinstance(obj, Path):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: convert_PosixPath_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_PosixPath_to_str(item) for item in obj]
    else:
        return obj

def process_poscar(poscar_path: Path, args: argparse.Namespace, restructured_interfaces_dir: Path):
    swap = None
    shift = int(poscar_path.parent.name.split("D")[1])
    interface = int(poscar_path.parent.parent.parent.name.split("D")[1])

    if is_swap_poscar(poscar_path):
        swap = int(poscar_path.parent.name.split("D")[1])
        shift = int(poscar_path.parent.parent.parent.name.split("D")[1])
        interface = int(poscar_path.parent.parent.parent.parent.parent.name.split("D")[1])

    data = {
        'name': None,
        'atoms': None,
        'artemis': {
            'path': poscar_path,
            'swap': swap,
            'shift': shift,
            'interface': interface,
            'generation_file_paths': extract_generation_file_paths(poscar_path),
            'generated_file_paths': extract_generated_file_paths(poscar_path),
        },
        'shift_data': None,
        'struc_data': None,
    }

    shift_data_path = data['artemis']['generated_file_paths']['shift_data_path']
    struc_data_path = data['artemis']['generated_file_paths']['struc_data_path']

    # extract shift values and structure data
    if not shift_data_path.exists():
        print(f"Error: {shift_data_path} does not exist.")
        exit(1)
    data['shift_data'] = extract_shift_data(shift_data_path, shift)

    if not struc_data_path.exists():
        print(f"Error: {struc_data_path} does not exist.")
        exit(1)
    data['struc_data'] = extract_struc_data(struc_data_path)

    # read the POSCAR file
    try:
        atoms = read(poscar_path, format='vasp')
        data['atoms'] = {
            'symbols': atoms.get_chemical_symbols(),
            'positions': atoms.get_positions().tolist(),
            'cell': atoms.get_cell().tolist(),
            'pbc': atoms.get_pbc().tolist(),
        }
    except Exception as e:
        print(f"Error reading {poscar_path}: {e}")
        return None

    # print(f"Extracted data for {poscar_path}")
    # print(data)
    # exit(0)

    # foreach symbol in atoms count the number of atoms in a count map
    symbol_count = {}
    for symbol in data['atoms']['symbols']:
        if symbol in symbol_count:
            symbol_count[symbol] += 1
        else:
            symbol_count[symbol] = 1

    # map symbol_count to a string "symbol:count" format
    total_atoms = sum(symbol_count.values())
    symbol_count_str = ''.join([f"{symbol}{count}" for symbol, count in symbol_count.items()])
    lower_crystal_miller_plane = data['struc_data'].get('lower_crystal_miller_plane', {})
    lower_crystal_miller_plane_str = f"{lower_crystal_miller_plane['h']}{lower_crystal_miller_plane['k']}{lower_crystal_miller_plane['l']}"
    upper_crystal_miller_plane = data['struc_data'].get('upper_crystal_miller_plane', {})
    upper_crystal_miller_plane_str = f"{upper_crystal_miller_plane['h']}{upper_crystal_miller_plane['k']}{upper_crystal_miller_plane['l']}"
    shift_data_str = f"a{data['shift_data']['a']}_b{data['shift_data']['b']}_c{data['shift_data']['c']}"
    postfix = f"interface{data['artemis']['interface']}shift{data['artemis']['shift']}"
    if data['artemis']['swap'] is not None:
        postfix += f"swap{data['artemis']['swap']}"

    poscar_name = f"{total_atoms}_{symbol_count_str}_{lower_crystal_miller_plane_str}_{upper_crystal_miller_plane_str}_{shift_data_str}_{postfix}"

    data['name'] = poscar_name

    print(f"Processing {poscar_path} with name {poscar_name}")

    # write the data to a json file in the restructured_interfaces_dir
    data_file_dir = restructured_interfaces_dir / poscar_name
    if not data_file_dir.exists():
        data_file_dir.mkdir(parents=True)
    data_file_path = data_file_dir / "poscar_data.json"
    if data_file_path.exists():
        print(f"Warning: {data_file_path} already exists. Overwriting.")

    # Convert PosixPath to str for JSON serialization
    data = convert_PosixPath_to_str(data)  # Convert PosixPath to str for JSON serialization
    with open(data_file_path, 'w') as data_file:
        json.dump(data, data_file, indent=4)
    print(f"Data written to {data_file_path}")

    # copy the POSCAR file to the data_file_dir
    poscar_dest_path = data_file_dir / "POSCAR"
    if poscar_dest_path.exists():
        print(f"Warning: {poscar_dest_path} already exists. Overwriting.")
    if not poscar_path.exists():
        print(f"Error: {poscar_path} does not exist.")
        return None

    os.system(f"cp {poscar_path} {poscar_dest_path}")

    artemis_file_dir = data_file_dir / "artemis"
    if not artemis_file_dir.exists():
        artemis_file_dir.mkdir(parents=True)

    # copy generation data files to the data_file_dir/generation_file_paths
    generation_file_paths_dir = artemis_file_dir / "generation_files"
    if not generation_file_paths_dir.exists():
        generation_file_paths_dir.mkdir(parents=True)

    for key, value in data['artemis']['generation_file_paths'].items():
        value = Path(value)
        if value.exists():
            dest_path = generation_file_paths_dir / value.name
            if key == "param_in_path":
                dest_path = generation_file_paths_dir / "param.in"
            if dest_path.exists():
                print(f"Warning: {dest_path} already exists. Overwriting.")
            try:
                os.system(f"cp {value} {dest_path}")
            except Exception as e:
                print(f"Error copying {value} to {dest_path}: {e}")
        else:
            print(f"Warning: {value} does not exist, skipping copy.")

    generated_files_dir = artemis_file_dir / "generated_files"
    if not generated_files_dir.exists():
        generated_files_dir.mkdir(parents=True)

    for key, value in data['artemis']['generated_file_paths'].items():
        value = Path(value)
        if value.exists():
            dest_path = generated_files_dir / value.name
            if key == "artemis_output_path":
                dest_path = generated_files_dir / "artemis.out"
            elif key == "settings_path":
                dest_path = generated_files_dir / "settings.txt"
            elif key == "struc_data_path":
                dest_path = generated_files_dir / "struc_data.txt"
            elif key == "shift_data_path":
                dest_path = generated_files_dir / "shift_data.txt"
            if dest_path.exists():
                print(f"Warning: {dest_path} already exists. Overwriting.")
            try:
                os.system(f"cp {value} {dest_path}")
            except Exception as e:
                print(f"Error copying {value} to {dest_path}: {e}")
        else:
            print(f"Warning: {value} does not exist, skipping copy.")
    return data

def main():
    parser = argparse.ArgumentParser(description="Split structure based on orientation (not species).")
    parser.add_argument('-g', '--generated-interfaces-dir', type=str, default='./generated_interfaces/', help='Directory containing generated interfaces with POSCAR files')
    parser.add_argument('-r', '--restructured-interfaces-dir', type=str, default='../structures/interfaces/', help='Directory to write restructured interfaces data')
    parser.add_argument('-s', '--search', type=str, default='**/POSCAR', help='Search pattern for POSCAR files, default is **/POSCAR')
    args = parser.parse_args()


    generated_interfaces_dir = Path(args.generated_interfaces_dir)
    restructured_interfaces_dir = Path(args.restructured_interfaces_dir)
    if not restructured_interfaces_dir.exists():
        restructured_interfaces_dir.mkdir(parents=True)
    if not generated_interfaces_dir.exists():
        print(f"Error: {generated_interfaces_dir} does not exist.")
        exit(1)

    poscar_paths = generated_interfaces_dir.glob(args.search)

    if not poscar_paths:
        print(f"Error: No POSCAR files found in {generated_interfaces_dir}.")
        exit(1)

    # Iterate over all POSCAR files found in the directory structure
    for poscar_path in poscar_paths:
        process_poscar(poscar_path, args, restructured_interfaces_dir)

if __name__ == "__main__":
    main()