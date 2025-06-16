from pathlib import Path

pairs_to_find = [
    ("C", "Ge"),
    ("C", "Si"),
    ("C", "Sn"),
    ("Ge", "C"),
    ("Ge", "Si"),
    ("Ge", "Sn"),
    ("Si", "C"),
    ("Si", "Ge"),
    ("Si", "Sn"),
    ("Sn", "C"),
    ("Sn", "Ge"),
    ("Sn", "Si"),
]

interface_dir = Path(__file__).parent.parent / "interfaces"
interface_per_species_dir = Path(__file__).parent

for dir in interface_dir.iterdir():
    dir_parts = dir.name.split("_")
    if len(dir_parts) < 2:
        continue
    species_part = dir_parts[1]
    # format = {species_a}{number_a}{species_b}{number_b}
    # check for species_part for 2 numbers
    # split by numbers
    species_parts = []
    #for char in species_part if char is different type than the previous one then add it to species_parts
    species_parts_index = 0
    previous_char = None
    for i, char in enumerate(species_part):
        if previous_char is None:
            species_parts.append(char)
        elif char.isalpha() == previous_char.isalpha() or char.isdigit() == previous_char.isdigit():
            species_parts[species_parts_index] += char
        elif char.isalpha() != previous_char.isalpha() or char.isdigit() != previous_char.isdigit():
            species_parts_index += 1
            species_parts.append(char)
        previous_char = char
    if len(species_parts) == 4:
        species_a = species_parts[0]
        number_a = species_parts[1]
        species_b = species_parts[2]
        number_b = species_parts[3]
    else:
        continue

    if (species_a, species_b) in pairs_to_find:
        new_dir = interface_per_species_dir / f"{species_a}-{species_b}"
        if not new_dir.exists():
            new_dir.mkdir(parents=True)
        # copy from interface_dir/{dir.name} to {new_dir}/{dir.name}
        copy_from = interface_dir / dir.name
        copy_from = copy_from.relative_to(copy_from.parent.parent)
        copy_from = Path('../../') / copy_from
        copy_to = new_dir / dir.name
        if not copy_to.exists():
            copy_to.symlink_to(copy_from)
            print(f"Created symlink: {copy_to} -> {copy_from}")
        else:
            print(f"Symlink already exists: {copy_to}, skipping.")

