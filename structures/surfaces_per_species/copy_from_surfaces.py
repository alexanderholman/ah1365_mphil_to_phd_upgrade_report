from pathlib import Path

to_find = [
    "C",
    "Ge",
    "Si",
    "Sn",
]

surface_dir = Path(__file__).parent.parent / "surfaces"
surface_per_species_dir = Path(__file__).parent

for dir in surface_dir.iterdir():
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
    if len(species_parts) == 2:
        species_a = species_parts[0]
        number_a = species_parts[1]
    else:
        continue

    if (species_a) in to_find:
        new_dir = surface_per_species_dir / f"{species_a}"
        if not new_dir.exists():
            new_dir.mkdir(parents=True)
        # copy from surface_dir/{dir.name} to {new_dir}/{dir.name}
        copy_from = surface_dir / dir.name
        copy_from = copy_from.relative_to(copy_from.parent.parent)
        copy_from = Path('../../') / copy_from
        copy_to = new_dir / dir.name
        print(f"Copying {copy_from} to {copy_to}")
        if not copy_to.exists():
            copy_to.symlink_to(copy_from)
            print(f"Created symlink: {copy_to} -> {copy_from}")
        else:
            print(f"Symlink already exists: {copy_to} -> {copy_from}, skipping.")

