import numpy as np

def read_multiple_xyz(filepath):
    """Read multiple molecules from a single xyz file."""
    with open(filepath, 'r') as file:
        lines = file.readlines()

    molecules = []
    i = 0
    while i < len(lines):
        num_atoms = int(lines[i].strip())  # Number of atoms for this molecule
        comment = lines[i + 1].strip()  # Comment line
        atoms = []
        coordinates = []
        for line in lines[i + 2:i + 2 + num_atoms]:
            parts = line.split()
            atoms.append(parts[0])  # Atom symbol
            coordinates.append([float(x) for x in parts[1:4]])  # Coordinates
        molecules.append((atoms, np.array(coordinates), comment))
        i += 2 + num_atoms  # Move to the next molecule

    return molecules

def write_multiple_xyz(filepath, molecules):
    """Write multiple molecules back into a single xyz file."""
    with open(filepath, 'w') as file:
        for atoms, coordinates, comment in molecules:
            file.write(f"{len(atoms)}\n")
            file.write(f"{comment}\n")
            for atom, (x, y, z) in zip(atoms, coordinates):
                file.write(f"{atom} {x:.8f} {y:.8f} {z:.8f}\n")

def align_to_origin(coordinates):
    """Shift the molecule so that the geometric center is at the origin."""
    geometric_center = np.mean(coordinates, axis=0)
    shifted_coordinates = coordinates - geometric_center  # Shift all coordinates
    return shifted_coordinates

def process_xyz_file(input_file, output_file):
    """Read, align, and write the molecules in the xyz file."""
    molecules = read_multiple_xyz(input_file)
    aligned_molecules = [(atoms, align_to_origin(coordinates), comment) for atoms, coordinates, comment in molecules]
    write_multiple_xyz(output_file, aligned_molecules)
    print(f"All molecules have been aligned and written to {output_file}.")

# Set the input and output file paths
input_file = 'ts_conformers.xyz'  # Your input xyz file with multiple molecules
output_file = 'aligned_ts_conformers.xyz'  # Output xyz file

# Process the file
process_xyz_file(input_file, output_file)
