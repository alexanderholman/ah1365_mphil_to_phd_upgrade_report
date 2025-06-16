#!/usr/bin/env python3
import os
import numpy as np
from ase.build import bulk, surface, stack
from ase.io import write


def canonical_miller(miller):
    """
    For a cubic crystal, symmetry makes (h,k,l) equivalent to any permutation
    of the absolute values. Sorting the absolute values (in descending order)
    gives a canonical form.
    """
    h, k, l = sorted(map(abs, miller), reverse=True)
    return (h, k, l)


def generate_unique_millers(max_index=2):
    """
    Generate unique Miller indices (excluding (0,0,0)) up to a given maximum absolute value.
    """
    millers = set()
    for h in range(-max_index, max_index + 1):
        for k in range(-max_index, max_index + 1):
            for l in range(-max_index, max_index + 1):
                if (h, k, l) == (0, 0, 0):
                    continue
                can = canonical_miller((h, k, l))
                millers.add(can)
    return sorted(list(millers))


def generate_slabs(material, miller_list, layers=5, vacuum=0.0):
    """
    Generate slabs for a given material (Si or Ge) using the diamond-cubic structure.
    """
    if material == 'Si':
        a = 5.43
    elif material == 'Ge':
        a = 5.658
    else:
        raise ValueError("Material not supported. Choose 'Si' or 'Ge'.")

    bulk_structure = bulk(material, 'diamond', a=a)
    slabs = {}
    for miller in miller_list:
        try:
            slab = surface(bulk_structure, miller, layers, vacuum)
            slab.center(vacuum=vacuum, axis=2)
            slabs[miller] = slab
        except Exception as e:
            print(f"Could not generate slab for {material} with Miller index {miller}: {e}")
    return slabs


def join_slabs(slab1, slab2, distance=2.0):
    """
    Join two slabs along the z-axis with a specified separation distance.
    """
    return stack(slab1, slab2, axis=2, distance=distance)


def create_interface_directories(si_slabs, ge_slabs, base_dir=os.path.join("data", "Si_Ge")):
    """
    For each matching Miller index, create a directory (e.g. Si_1_0_0-Ge_1_0_0) under data/Si_Ge,
    write the POSCAR, and create symlinks to common INCAR, KPOINTS, POTCAR, and run_mace.py.
    Relative symlink paths are used so that VASP can find the common files.
    """
    os.makedirs(base_dir, exist_ok=True)

    # Symlink targets (assumed to be in common/)
    incar_target = os.path.join("..", "..", "..", "common", "INCARS", "semiconductors-cheap", "INCAR")
    kpoints_target = os.path.join("..", "..", "..", "common", "KPOINTS", "cheap", "KPOINTS")
    potcar_target = os.path.join("..", "..", "..", "common", "POTCARS", "SiGe", "POTCAR")
    run_mace_target = os.path.join("..", "..", "..", "common", "run-mace.py")
    sbatch_target = os.path.join("..", "..", "..", "common", "SBATCH")

    # Pair slabs for matching Miller indices
    for miller in si_slabs.keys():
        if miller in ge_slabs:
            # Directory name, e.g., Si_1_0_0-Ge_1_0_0
            dirname = os.path.join(base_dir,
                                   f"Si_{miller[0]}_{miller[1]}_{miller[2]}-Ge_{miller[0]}_{miller[1]}_{miller[2]}")
            os.makedirs(dirname, exist_ok=True)

            # Create the interface by joining the slabs
            try:
                interface = join_slabs(si_slabs[miller], ge_slabs[miller], distance=2.0)
            except Exception as e:
                print(f"Could not join slabs for Miller index {miller}: {e}")
                continue

            # Write POSCAR in the interface directory
            poscar_path = os.path.join(dirname, "POSCAR")
            write(poscar_path, interface, format='vasp')
            print(f"Wrote POSCAR to {poscar_path}")

            # Create symlinks for required common VASP input files and run_mace.py
            symlinks = {
                "INCAR": incar_target,
                "KPOINTS": kpoints_target,
                "POTCAR": potcar_target,
                "run-mace.py": run_mace_target,
                "SBATCH": sbatch_target,
            }
            for link_name, target in symlinks.items():
                link_path = os.path.join(dirname, link_name)
                # Remove existing file or symlink if it exists
                if os.path.lexists(link_path):
                    os.remove(link_path)
                try:
                    os.symlink(target, link_path)
                    print(f"Created symlink {link_path} -> {target}")
                except Exception as e:
                    print(f"Failed to create symlink {link_path}: {e}")


if __name__ == "__main__":
    # Generate unique Miller indices for cubic symmetry
    unique_millers = generate_unique_millers(max_index=2)
    print("Unique Miller indices:", unique_millers)

    # Generate slabs for Si and Ge
    si_slabs = generate_slabs('Si', unique_millers)
    ge_slabs = generate_slabs('Ge', unique_millers)

    # Create interface directories under data/Si_Ge
    create_interface_directories(si_slabs, ge_slabs)

    print("\nInterface generation complete. Interfaces are stored in data/Si_Ge/")
