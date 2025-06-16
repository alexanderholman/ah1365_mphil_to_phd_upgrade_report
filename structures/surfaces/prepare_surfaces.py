from pathlib import Path

methods = ["dft_vasp", "mlp_mace"]

# Input slab root directory
base_dir = Path("./structures/surfaces")

slabs_paths = []

for item in base_dir.iterdir():
    if item.is_dir() and (item / "slab.vasp").exists():
        slabs_paths.append(item)

for slabs_path in slabs_paths:
    slab_dir = slabs_path
    slab_dir_parts = slab_dir.name.split("_")

    relaxations_dir = slab_dir / "relaxations"

    if not relaxations_dir.exists():
        relaxations_dir.mkdir(parents=True)

        for method in methods:
            method_dir = relaxations_dir / method
            if not method_dir.exists():
                method_dir.mkdir(parents=True)
                (method_dir / "POSCAR").write_text((slab_dir / "slab.vasp").read_text())

                # run relaxation jobs