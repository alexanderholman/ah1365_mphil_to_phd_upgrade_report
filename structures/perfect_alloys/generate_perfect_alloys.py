# generate perfectly intermixed of C, Si, Ge, and Sn alloys for testing
from pathlib import Path
from ase.build import bulk
from ase.io import write

material_lattice_constants = {
    'C': 3.57,
    'Si': 5.43,
    'Ge': 5.66,
    'Sn': 6.49,
}

def generate_perfect_alloys(material_a, material_b):
    lattice_constant = (material_lattice_constants[material_a]+ material_lattice_constants[material_b]) / 2
    structure = bulk(material_a, 'diamond', a=lattice_constant, cubic=True)
    for i, atom in enumerate(structure):
        if i % 2 == 0:
            atom.symbol = material_a
        else:
            atom.symbol = material_b
    return structure

def generate_perfect_alloys_for_all_materials():
    materials = list(material_lattice_constants.keys())
    structures = []
    for i in range(len(materials)):
        for j in range(i + 1, len(materials)):
            material_a = materials[i]
            material_b = materials[j]
            if material_a == material_b:
                continue
            structure = generate_perfect_alloys(material_a, material_b)
            structures.append((material_a, material_b, structure))
    return structures

if __name__ == "__main__":
    structures = generate_perfect_alloys_for_all_materials()
    for material_a, material_b, structure in structures:
        name = f"{material_a}-{material_b}"
        dir = Path(name)
        dir.mkdir(parents=True, exist_ok=True)
        poscar_path = dir / "POSCAR"
        graphics_dir = dir / "graphics"
        graphics_dir.mkdir(parents=True, exist_ok=True)
        structure.write(poscar_path, format='vasp', direct=True)

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
            write(graphics_dir / f"alloy_a{angle[0]}_b{angle[1]}_c{angle[2]}.png", structure, rotation=rotation, scale=300)