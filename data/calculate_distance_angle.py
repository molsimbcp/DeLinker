#!/usr/bin/env/python
"""
Usage:
    calculate_distance_angle.py [options]

Options:
    -h --help                Show this screen
    --data_path FILE         Path to data file containing fragments and reference molecules
    --sdf_path FILE          Path to SD file containing conformers of reference molecules
    --output_path FILE       Path to output file
    --verbose                Print progress and updates to terminal
"""

from rdkit import Chem
from rdkit.Chem import AllChem

import frag_utils

from docopt import docopt
import re

if __name__ == "__main__":
    # Parse args
    args = docopt(__doc__)
    data_path = args.get('--data_path')
    sdf_path = args.get('--sdf_path')
    output_path = args.get('--output_path')
    verbose = args.get('--verbose')

    # Load data
    data = frag_utils.read_paired_file(data_path)
    if verbose:
        print("Num entries: %d" % len(data))

    # Filter SMILES for permitted atom types
    data_filt = []
    errors = 0
    for i, d in enumerate(data):
        if frag_utils.check_smi_atom_types(d[0]) and frag_utils.check_smi_atom_types(d[1]):
            data_filt.append(d)
        else:
            errors +=1
    
        if i % 1000 == 0 and verbose:
            print("\rProcessed smiles: %d" % i, end='')
        
    if verbose:
        print("Original num entries: \t\t\t%d" % len(data))
        print("Number with permitted atom types: \t%d" % len(data_filt))
        print("Number of errors: \t\t\t%d" % errors)

    # Get linkers
    du = Chem.MolFromSmiles('*')
    for i, d in enumerate(data_filt):
        # Standardise SMILES to RDKit
        d[0]=Chem.MolToSmiles(Chem.MolFromSmiles(d[0]))
        d[1]=Chem.MolToSmiles(Chem.MolFromSmiles(d[1]))
        # Get linker
        clean_frag = Chem.RemoveHs(AllChem.ReplaceSubstructs(Chem.MolFromSmiles(d[0]),du,Chem.MolFromSmiles('[H]'),True)[0]) 
        linker = frag_utils.get_linker(Chem.MolFromSmiles(d[1]), clean_frag, d[0])
        linker = re.sub('[0-9]+\*', '*', linker)
        data_filt[i].append(linker)

    # Calculate structural information
    data_final, distances, angles, fails = frag_utils.compute_distance_and_angle_dataset_alt(data_filt, sdf_path, verbose=verbose)

    if verbose:
        print("Number of successful examples: \t\t%d" % len(distances))
        print("Number failed examples: \t\t\t%d" % fails[0]) 
        print("Number of SDF errors: \t\t\t%d" % fails[1])
        print("Number of examples without conformers: \t%d" % (len(data_filt)-len(data_final)))

    # Write data to file
    # Format: full_mol (SMILES), linker (SMILES), fragments (SMILES), distance (Angstrom), angle (Radians)
    with open(output_path, 'w') as f:
        for d, dist, ang in zip(data_final, distances, angles):
            f.write("%s %s %s %s %s\n" % (d[0], d[1], d[2], dist, ang))

    if verbose:
        print("Done")
