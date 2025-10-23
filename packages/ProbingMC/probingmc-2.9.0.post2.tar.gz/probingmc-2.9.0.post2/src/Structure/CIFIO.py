import numpy as np
from Structure.controls import error_throw
import re
import os.path
from Structure.Atom import Atom

# hashing
def position_2_integer(pos):
    hash_code = 0
    for coord in pos:
        coord %= 1.0
        hash_code = 100 * hash_code + 100 * round(coord, ndigits=2)
    return hash_code

def duplicate_atoms(atoms, reflection_planes, reflection_coeffs_list):
    atoms_pos = set()  # position of atoms
    # firstly add all current atoms
    for atom in atoms:
        atoms_pos.add(position_2_integer(atom.cryst_coors))
    # now duplicate it according to symmetry operations
    n_atoms = len(atoms)
    for i in range(n_atoms):
        atom = atoms[i]
        # cycle on every symmetry operation:
        for j in range(len(reflection_coeffs_list)):
            reflection_coeffs = reflection_coeffs_list[j]
            reflection_plane = reflection_planes[j]
            new_coors = reflection_plane + np.multiply(atom.cryst_coors, reflection_coeffs)
            new_coors %= 1.0
            new_coors_hash_code = position_2_integer(new_coors)
            if new_coors_hash_code not in atoms_pos:
                new_atom = Atom(atom.element, new_coors, "cryst")
                atoms.append(new_atom)
                atoms_pos.add(new_coors_hash_code)


def load_structure_from_cif(filename):
    if not os.path.isfile(filename):
        error_throw("There is no such file: " + filename)
    f = open(filename)
    a_cell = None
    b_cell = None
    c_cell = None
    alpha_cell = None
    beta_cell = None
    gamma_cell = None
    atoms = []
    n_cell = 0  # number of cell components found
    symmetry_operation = False
    has_symmetry = False
    reflection_planes = []
    reflection_coeffs_list = []
    for line in f:
        # cell parameters
        ro = re.search('_cell_length_a\s+(\d*\.?\d*)', line)
        if ro is not None:
            a_cell = float(ro.group(1))
            n_cell += 1
        ro = re.search('_cell_length_b\s+(\d*\.?\d*)', line)
        if ro is not None:
            b_cell = float(ro.group(1))
            n_cell += 1
        ro = re.search('_cell_length_c\s+(\d*\.?\d*)', line)
        if ro is not None:
            c_cell = float(ro.group(1))
            n_cell += 1
        ro = re.search('_cell_angle_alpha\s+(-?\d*\.?\d*)', line)
        if ro is not None:
            alpha_cell = float(ro.group(1))
            n_cell += 1
        ro = re.search('_cell_angle_beta\s+(-?\d*\.?\d*)', line)
        if ro is not None:
            beta_cell = float(ro.group(1))
            n_cell += 1
        ro = re.search('_cell_angle_gamma\s+(-?\d*\.?\d*)', line)
        if ro is not None:
            gamma_cell = float(ro.group(1))
            n_cell += 1

        # look for symmetry operations
        if re.search('_symmetry_equiv_pos_as_xyz', line):
            symmetry_operation = True
            continue
        if symmetry_operation:
            if not re.search('\'.*x.*,.*y.*,.*z.*\'', line):
                symmetry_operation = False
        if symmetry_operation:
            has_symmetry = True
            ro = re.search('\'(.+)\'', line)
            operation = ro.group(1)
            components = operation.split(',')
            reflection_plane = np.array([0.0, 0.0, 0.0])
            reflection_coeffs = np.array([1.0, 1.0, 1.0])
            for i in range(3):
                ro = re.search('(\d+)/(\d+)', components[i])
                if ro:
                    fraction = int(ro.group(1)) / int(ro.group(2))
                    reflection_plane[i] = fraction
                if re.search('-', components[i]):
                    reflection_coeffs[i] = -1.0
            reflection_planes.append(reflection_plane)
            reflection_coeffs_list.append(reflection_coeffs)
            continue

        # insert atoms
        # number_pattern = '-?\d*\.\d*'
        # the following pattern matches float numbers in ordinary and scientific formats
        # taken from http://stackoverflow.com/questions/638565/parsing-scientific-notation-sensibly
        number_pattern = '[+\-]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?'
        atoms_pattern = '(?!\')(\w+){1,2}\s+(' + number_pattern + ')\s+(' + number_pattern + ')\s+(' + number_pattern + ')'
        ro = re.search(atoms_pattern, line)
        if ro is not None:
            # print(line)
            label = ro.group(1)
            x = float(ro.group(2))
            y = float(ro.group(3))
            z = float(ro.group(4))
            ro = re.search('(\D+)', label)
            if not ro:
                error_throw("CIFIO.py: No element name was found in the element label: " + label)
            element = ro.group(1)
            atoms.append(Atom(element, [x, y, z], "cryst"))
    f.close()

    # now duplicate atoms according to symmetry operations
    if has_symmetry:
        # print symmetries to compare with original file
        for a, b in zip(reflection_planes, reflection_coeffs_list):
            print(a, b)
        duplicate_atoms(atoms, reflection_planes, reflection_coeffs_list)

    if n_cell != 6:  # check for number of cell components
        error_throw("Not all cell components were found!")
    return (a_cell, b_cell, c_cell, alpha_cell, beta_cell, gamma_cell), atoms


def dump_structure_to_cif(cell_components, atoms, filename):
    a_cell, b_cell, c_cell, alpha_cell, beta_cell, gamma_cell = cell_components
    f = open("../sample.cif")
    text_file = f.read()
    f.close()
    text_file = re.sub('\sa_cell', ' ' + str(a_cell), text_file)
    text_file = re.sub('\sb_cell', ' ' + str(b_cell), text_file)
    text_file = re.sub('\sc_cell', ' ' + str(c_cell), text_file)
    text_file = re.sub('alpha_cell', str(alpha_cell), text_file)
    text_file = re.sub('beta_cell', str(beta_cell), text_file)
    text_file = re.sub('gamma_cell', str(gamma_cell), text_file)
    atoms_text = ""
    for atom in atoms:
        atoms_text += atom.element + "\t" + str(atom.cryst_coors[0]) + "\t" + str(atom.cryst_coors[1])\
                      + "\t" + str(atom.cryst_coors[2]) + "\n"
    text_file = re.sub('atoms_xxx', atoms_text, text_file)
    f = open(filename, 'w')
    f.write(text_file)
    f.close()
