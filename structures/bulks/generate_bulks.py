# generate bulks of C, Si, Ge, and Sn for testing
from pathlib import Path
from ase.build import bulk
from ase.io import write

material_lattice_constants = {
    'C': 3.57,
    'Si': 5.43,
    'Ge': 5.66,
    'Sn': 6.49,
}

if __name__ == "__main__":
    # foreach material_lattice_constant, generate a bulk structure
    for material, lattice_constant in material_lattice_constants.items():
        name = f"{material}"
        dir = Path(name)
        dir.mkdir(parents=True, exist_ok=True)
        poscar_path = dir / "POSCAR"
        graphics_dir = dir / "graphics"
        graphics_dir.mkdir(parents=True, exist_ok=True)
        structure = bulk(material, 'diamond', a=lattice_constant, cubic=True)
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