import os
import subprocess
from ase import Atoms
from ase.io import write
from ase.build import bulk

SPECIES = GROUP4 = [
    "C",
    "Si",
    "Ge",
    "Sn",
]

LATTICE_CONSTANTS = {
    "C": 3.5668,
    "Si": 5.4310,
    "Ge": 5.6578,
    "Sn": 6.4892,
}

BULKS = {s: bulk(s, crystalstructure='diamond', a=LATTICE_CONSTANTS[s], cubic=True) for s in SPECIES}

LOWER_UPPER_BULK_PAIRS = []

class BulkPair:
    def __init__(self, lower: Atoms, upper: Atoms):
        lower_symbol = lower.get_chemical_formula()
        upper_symbol = upper.get_chemical_formula()
        self.name = f"{lower_symbol}{upper_symbol}"
        self.lower = lower
        self.upper = upper
        print(f"Created BulkPair: {self.name} with lower {lower_symbol} and upper {upper_symbol}")

    # write as vasp files direct = true
    def save(self, path: str):
        write(f"{path}/lower.vasp", self.lower, format='vasp', direct=True)
        write(f"{path}/upper.vasp", self.upper, format='vasp', direct=True)

    def __repr__(self):
        return f"BulkPair({self.lower}, {self.upper})"

pairs = set([])

for lower in BULKS.values():
    for upper in BULKS.values():
        bulk_pair = BulkPair(lower, upper)
        if bulk_pair.name not in pairs:
            pairs.add(bulk_pair.name)
            LOWER_UPPER_BULK_PAIRS.append(bulk_pair)

for pair in LOWER_UPPER_BULK_PAIRS:
    # Save each pair to a directory named after the pair
    pair_path = f"./generated_interfaces/{pair.name}"
    graphics_dir = f"{pair_path}/graphics"
    os.makedirs(pair_path, exist_ok=True)
    os.makedirs(graphics_dir, exist_ok=True)
    pair.save(pair_path)

    # Generate images for each pair with different rotations
    angles = [
        [-90, 0, 0],
        [90, 0, 0],
        [0, 90, 0],
        [0, -90, 0],
        [0, 0, 90],
        [0, 0, -90],
        [-45, -45, -45],
        [45, 45, 45],
    ]
    for angle in angles:
        rotation = f"{angle[0]}x,{angle[1]}y,{angle[2]}z"
        write(f"{graphics_dir}/upper_a{angle[0]}_b{angle[1]}_c{angle[2]}.png", pair.upper, rotation=rotation, scale=300)
        write(f"{graphics_dir}/lower_a{angle[0]}_b{angle[1]}_c{angle[2]}.png", pair.lower, rotation=rotation, scale=300)

    # Copy param.in to the pair directory
    param_in_name = "param.in"

    default_param_in_path = f"./{param_in_name}/default"
    if os.path.exists(default_param_in_path):
        with open(default_param_in_path, 'r') as f:
            param_content = f.read()
        with open(f"{pair_path}/default.{param_in_name}", 'w') as f:
            f.write(param_content)
    else:
        print(f"Warning: {default_param_in_path} does not exist. Skipping copy.")

    no_shift_param_in_path = f"./{param_in_name}/no_shift"
    if os.path.exists(no_shift_param_in_path):
        with open(no_shift_param_in_path, 'r') as f:
            param_content = f.read()
        with open(f"{pair_path}/no_shift.{param_in_name}", 'w') as f:
            f.write(param_content)
    else:
        print(f"Warning: {no_shift_param_in_path} does not exist. Skipping copy.")
        
    # Copy run.sh to the pair directory
    run_sh_name = "run.sh"
    run_sh_path = f"./{run_sh_name}"
    if os.path.exists(run_sh_path):
        with open(run_sh_path, 'r') as f:
            run_content = f.read()
        with open(f"{pair_path}/{run_sh_name}", 'w') as f:
            f.write(run_content)
        # Ensure the script is executable
        os.chmod(f"{pair_path}/{run_sh_name}", 0o755)
        print(f"Copied run.sh to {pair_path}/{run_sh_name}")
    else:
        print(f"Warning: {run_sh_path} does not exist. Skipping copy.")
        
    # execute the run.sh script in the pair directory in a new thread
    print(f"Executing run.sh for {pair.name} in {pair_path}")

    # Change to the pair directory and execute run.sh
    original_dir = os.getcwd()
    os.chdir(pair_path)
    p = subprocess.Popen(['./run.sh'])
    print(f"Executed run.sh for {pair.name} in {pair_path}, pid: {p.pid}")
    os.chdir(original_dir)
