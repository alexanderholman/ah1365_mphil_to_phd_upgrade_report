from ase.io import read, write
import numpy as np
from ase import Atoms

def cut_stack(supercell_file, lower_species, upper_species, miller_lower, miller_upper):
    # Load supercell structure
    supercell = read(supercell_file)

    positions = supercell.get_positions()
    symbols = np.array(supercell.get_chemical_symbols())
    cell = supercell.get_cell()

    # Determine split plane normal from Miller indices
    normal_lower = np.array(miller_lower) @ np.linalg.inv(cell).T
    normal_upper = np.array(miller_upper) @ np.linalg.inv(cell).T

    # Normalize the normals
    normal_lower /= np.linalg.norm(normal_lower)
    normal_upper /= np.linalg.norm(normal_upper)

    # Compute centroid of positions to find splitting plane
    centroid = positions.mean(axis=0)

    # Determine projection along interface normal (average of two normals)
    interface_normal = (normal_lower + normal_upper) / 2
    interface_normal /= np.linalg.norm(interface_normal)

    # Project positions onto interface normal
    projections = positions @ interface_normal
    centroid_proj = centroid @ interface_normal

    # Split atoms into lower and upper based on projection
    lower_indices = []
    upper_indices = []

    for idx, (proj, symbol) in enumerate(zip(projections, symbols)):
        if symbol == lower_species or (symbol != upper_species and proj <= centroid_proj):
            lower_indices.append(idx)
        elif symbol == upper_species or (symbol != lower_species and proj > centroid_proj):
            upper_indices.append(idx)

    # Create lower and upper ASE Atoms objects
    lower_atoms = Atoms(symbols=symbols[lower_indices],
                        positions=positions[lower_indices],
                        pbc=True)

    upper_atoms = Atoms(symbols=symbols[upper_indices],
                        positions=positions[upper_indices],
                        pbc=True)

    # Reset original lattice
    lower_atoms.set_cell(cell)
    upper_atoms.set_cell(cell)

    # Write out the separated cells
    write('lower.vasp', lower_atoms, format='vasp', direct=True)
    write('upper.vasp', upper_atoms, format='vasp', direct=True)


# Example usage:
if __name__ == "__main__":
    cut_stack(
        supercell_file='POSCAR',
        lower_species='Si',
        upper_species='Ge',
        miller_lower=[0, 0, 1],
        miller_upper=[0, 0, 1]
    )
