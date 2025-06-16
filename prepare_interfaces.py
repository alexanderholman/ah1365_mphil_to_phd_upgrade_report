from pathlib import Path

methods = ["dft_vasp", "mlp_mace"]

# Input slab root directory
base_dir = Path("./structures/interfaces")

poscar_paths = []

for item in base_dir.iterdir():
    if item.is_dir() and (item / "POSCAR").exists():
        poscar_paths.append(item)

for poscar_path in poscar_paths:
    poscar_dir = poscar_path
    poscar_dir_parts = poscar_dir.name.split("_")

    relaxations_dir = poscar_dir / "relaxations"

    if not relaxations_dir.exists():
        relaxations_dir.mkdir(parents=True)

        for method in methods:
            method_dir = relaxations_dir / method
            if not method_dir.exists():
                method_dir.mkdir(parents=True)
                (method_dir / "POSCAR").write_text((poscar_dir / "POSCAR").read_text())

                # run relaxation jobs