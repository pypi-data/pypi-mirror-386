from Structure.controls import error_throw
import re
import os.path
import numpy as np
import math
from Structure.Atom import Atom


def load_structure_from_qe_in(filename):
    if not os.path.isfile(filename):
        error_throw("There is no such file: " + filename)
    f = open(filename)
    cell_matrix = []
    atoms = []
    what_was_found = 0  # 0 - nothing, 1 - A(alat), 2 - cell, 3 - atoms
    alat = None
    A = B = C = cosAB = cosAC = cosBC = None
    # bohr_to_angstrom = 0.52917721
    for line in f:
        # looking for the A(alat)
        if what_was_found == 0:
            ro = re.search('A\s*=\s*(\d*\.?\d*)', line)
            if ro is not None:
                alat = float(ro.group(1))
                what_was_found = 1
        # looking for the final cell vectors
        elif what_was_found == 1:
            blocks = re.split('\s+|,+', line)
            match blocks:
                case [_, 'B', '=', B, *_]:
                    B = float(B)
                case [_, 'C', '=', C, *_]:
                    C = float(C)
                case [_, 'cosAB', '=', cosAB, *_]:
                    cosAB = float(cosAB)
                case [_, 'cosAC', '=', cosAC, *_]:
                    cosAC = float(cosAC)
                case [_, 'cosBC', '=', cosBC, *_]:
                    cosBC = float(cosBC)
            if None not in (B, C, cosAB, cosAC, cosBC):
                # calculate cell matrix: https://www.quantum-espresso.org/Doc/INPUT_PW.html#idm218
                A = alat
                sinAB = math.sqrt(1 - cosAB**2)
                v3y = C * (cosBC - cosAC * cosAB) / sinAB
                v3z = C * math.sqrt( 1 + 2 * cosBC * cosAC * cosAB - cosBC**2 - cosAC**2 - cosAB**2 ) / sinAB
                cell_matrix = np.array([[A, 0, 0],
                                        [B * cosAB, B * sinAB, 0],
                                        [C * cosAC, v3y, v3z]])
                what_was_found = 2
                continue
            ro = re.search('^\s*(-?\d*\.?\d+)\s+(-?\d*\.?\d+)\s+(-?\d*\.?\d+)', line)
            if ro is not None:
                vx = float(ro.group(1))
                vy = float(ro.group(2))
                vz = float(ro.group(3))
                v = np.array([vx, vy, vz])
                cell_matrix.append(v)
            if len(cell_matrix) == 3:
                cell_matrix = np.array(cell_matrix) * alat
                what_was_found = 2
        # looking for the atomic coordinates
        elif what_was_found == 2:
            # insert atoms
            ro = re.search('^\s*(\w+)\s+(-?\d*\.\d+)\s+(-?\d*\.\d+)\s+(-?\d*\.\d+)\s*$', line)
            if ro is not None:
                label = ro.group(1)
                x = float(ro.group(2))
                y = float(ro.group(3))
                z = float(ro.group(4))
                ro = re.search('(\D)+', label)
                if not ro:
                    error_throw("No element name was found in the element label: " + label)
                element = ro.group(1)
                atoms.append(Atom(element, [x, y, z], "cryst"))
    f.close()
    return cell_matrix, atoms


def load_structure_from_qe_vc_relax(filename):
    if not os.path.isfile(filename):
        error_throw("There is no such file: " + filename)
    f = open(filename)
    cell_matrix = []
    atoms = []
    what_was_found = 0  # 0 - nothing, 1 - final, 2 - alat, 3 - cell, 4 - atoms
    alat = None
    bohr_to_angstrom = 0.52917721
    for line in f:
        # looking for the label of the final data
        if what_was_found == 0:
            ro = re.search('Begin final coordinates', line)
            if ro is not None:
                what_was_found = 1
        # looking for the alat
        elif what_was_found == 1:
            ro = re.search('alat\s*=\s*(\d*\.?\d*)', line)
            if ro is not None:
                alat = float(ro.group(1))
                what_was_found = 2
        # looking for the final cell vectors
        elif what_was_found == 2:
            ro = re.search('^\s*(-?\d*\.?\d*)\s+(-?\d*\.?\d*)\s+(-?\d*\.?\d*)', line)
            if ro is not None:
                vx = float(ro.group(1))
                vy = float(ro.group(2))
                vz = float(ro.group(3))
                v = np.array([vx, vy, vz])
                cell_matrix.append(v)
            if len(cell_matrix) == 3:
                cell_matrix = np.array(cell_matrix) * alat * bohr_to_angstrom
                what_was_found = 3
        # looking for the atomic coordinates
        elif what_was_found == 3:
            # insert atoms
            ro = re.search('^\s*(\w+)\s+(-?\d*\.\d*)\s+(-?\d*\.\d*)\s+(-?\d*\.\d*)\s*$', line)
            if ro is not None:
                label = ro.group(1)
                x = float(ro.group(2))
                y = float(ro.group(3))
                z = float(ro.group(4))
                ro = re.search('(\D)+', label)
                if not ro:
                    error_throw("No element name was found in the element label: " + label)
                element = ro.group(1)
                atoms.append(Atom(element, [x, y, z], "cryst"))
    f.close()
    return cell_matrix, atoms


def load_structure_from_qe_relax(filename, scf=False):  # in case of scf=True, don't require atoms to be present
    if not os.path.isfile(filename):
        error_throw("There is no such file: " + filename)
    f = open(filename)
    cell_matrix = []
    atoms = []
    what_was_found = 0  # 0 - nothing, 1 - alat, 2 - label 'crystal axes', 3 - cell vectors,
    # 4 - label 'Begin final coordinates', 5 - atoms
    alat = None
    bohr_to_angstrom = 0.52917721
    energy = None
    crystal_coors = None  # True if output in crystal coordinates and False if in cartesian
    for line in f:
        # looking for energy (new addition): either the last '!' (for unfinished calculations) or Final energy
        ro = re.search('!\s+total energy\s+=\s+(-?\d*\.?\d*)', line)
        if ro is not None:
            energy = float(ro.group(1))
        ro = re.search('Final\s+energy\s+=\s+(-?\d*\.?\d*)', line)
        if ro is not None:
            energy = float(ro.group(1))
        # looking for the alat
        if what_was_found == 0:
            ro = re.search('\(alat\)\s*=\s*(\d+\.\d+)', line)
            if ro is not None:
                alat = float(ro.group(1))
                what_was_found = 1
        # looking for the label 'crystal axes'
        if what_was_found == 1:
            ro = re.search('crystal axes', line)
            if ro is not None:
                what_was_found = 2
        # looking for the final cell vectors
        elif what_was_found == 2:
            ro = re.search('\(\s*(-?\d*\.?\d*)\s+(-?\d*\.?\d*)\s+(-?\d*\.?\d*)', line)
            if ro is not None:
                vx = float(ro.group(1))
                vy = float(ro.group(2))
                vz = float(ro.group(3))
                v = np.array([vx, vy, vz])
                cell_matrix.append(v)
            if len(cell_matrix) == 3:
                cell_matrix = np.array(cell_matrix) * alat * bohr_to_angstrom
                what_was_found = 3
        # looking for the label 'Begin final coordinates'
        elif what_was_found == 3:
            ro = re.search('Begin final coordinates', line)
            ro2 = re.search('End of BFGS Geometry Optimization', line)  # for the case of unfinished calculations
            if ro is not None or ro2 is not None:
                what_was_found = 4
        # # looking for the atomic coordinates
        elif what_was_found == 4:
            # insert atoms
            if crystal_coors is None:
                roc = re.search('ATOMIC_POSITIONS\s+\((\w+)\)', line)
                if roc is not None:
                    type_coor = roc.group(1)
                    if type_coor == 'crystal':
                        crystal_coors = True
                    elif type_coor == 'angstrom':
                        crystal_coors = False
                    else:
                        print(f'Error: Unknown type of coordinates: {type_coor} !!! Program stopped.')
                        exit(1)
            else:
                ro = re.search('^\s*(\w+)\s+(-?\d*\.\d*)\s+(-?\d*\.\d*)\s+(-?\d*\.\d*)\s*', line)
                if ro is not None:
                    label = ro.group(1)
                    x = float(ro.group(2))
                    y = float(ro.group(3))
                    z = float(ro.group(4))
                    ro = re.search('(\D+)', label)
                    if not ro:
                        error_throw("No element name was found in the element label: " + label)
                    element = ro.group(1)
                    if crystal_coors:
                        atom = Atom(element, [x, y, z], "cryst")
                    else:
                        atom = Atom(element, [x, y, z], "cart")
                        atom.cart_to_cryst(np.linalg.inv(cell_matrix))
                    atoms.append(atom)
    if len(atoms) == 0 and not scf:
        print('Error: No atoms were found !!! Program stopped.')
        exit(1)
    f.close()
    return cell_matrix, atoms, energy


def dump_structure_to_qe(cell_components, atoms, filename, name, type, path='..'):
    a_cell, b_cell, c_cell, alpha_cell, beta_cell, gamma_cell = cell_components
    in_qe_file = None
    atom_ind = None  # index of modified atom for XPS calculation
    path = r'C:\Users\andre\My Tresors\Cloud\modeling\ACMS\Ribbon'  # quick fix for the template location
    if type == 'scf':
        in_qe_file = f"{path}/qe_scf_sample.in"
    elif type == 'relax':
        in_qe_file = f"{path}/qe_relax_sample.in"
    elif type == 'vc-relax':
        in_qe_file = f"{path}/qe_vc_relax_sample.in"
    elif type == 'scf_xps':
        in_qe_file = f"{path}/qe_scf_xps_sample.in"
        ro = re.search('_(\d+)$', name)
        if ro is not None:
            atom_ind = int(ro.group(1))
            print(atom_ind)
        else:
            error_throw('There was no index for the excited atom for the XPS calculation!')
    else:
        error_throw("QE calculation type is not specified or unknown!")
    f = open(in_qe_file)
    text_file = f.read()
    f.close()
    text_file = re.sub('name_xxx', name, text_file)
    text_file = re.sub('a_cell', str(a_cell), text_file)
    text_file = re.sub('b_cell', str(b_cell), text_file)
    text_file = re.sub('c_cell', str(c_cell), text_file)
    text_file = re.sub('cosAB_xxx', str(math.cos(gamma_cell * math.pi / 180)), text_file)
    text_file = re.sub('cosAC_xxx', str(math.cos(beta_cell * math.pi / 180)), text_file)
    text_file = re.sub('cosBC_xxx', str(math.cos(alpha_cell * math.pi / 180)), text_file)
    text_file = re.sub('number_of_atoms', str(len(atoms)), text_file)
    elements = elements_of_structure(atoms)
    if type == 'scf_xps':
        if atom_ind is None:
            error_throw("XPS calculation could not find hole atom")
        elements.add(atoms[atom_ind].element + "h")
        # num_elements += 1  # to account for the potential with the hole
    num_elements = len(elements)
    text_file = re.sub('number_of_types', str(num_elements), text_file)
    text_file = re.sub('PPs_xxx', pps_text(elements, type), text_file)
    text_file = re.sub('atoms_xxx', atoms_text(atoms, atom_ind), text_file)
    f = open(filename, 'w')
    f.write(text_file)
    f.close()


def elements_of_structure(atoms):
    elements = set([])
    for atom in atoms:
        elements.add(atom.element)
    return elements


def atoms_text(atoms, ind=None):
    text = ""
    for i in range(len(atoms)):
        atom = atoms[i]
        el_name = atom.element
        if ind is not None:
            if ind == i:
                el_name += 'h'
        relax_flags = "" if atom.is_relax_everything() else (" " + atom.relaxation_flags())
        text += el_name + "\t" + str(atom.cryst_coors[0]) + "\t" + str(atom.cryst_coors[1])\
                      + "\t" + str(atom.cryst_coors[2]) + relax_flags + "\n"
    return text[:-1]  # remove the last "\n"


def pps_text(elements, type):
    #  :return: return text of pseudo potentials for elements
    text = ""
    for el in elements:
        # if type == 'scf_xps' or type == 'vc-relax':
        #     text += Atom.PPs_pbe_rrkjus[el] + "\n"
        # else:
        #     text += Atom.PPs[el] + "\n"
        # text += Atom.PPs_pbe_rrkjus[el] + "\n"
        text += Atom.PPs_ONCV_PBE[el] + "\n"
    return text[:-1]  # remove the last "\n"

# f = open("C:/Users/user/Dropbox/H2M/Projects/GO/Ready_GO/qe_scf_sample.in")
# f.close()
# cell, ats = load_structure_from_qe_relax('C:/Users/user/Dropbox/H2M/Projects/GO/Ready_GO/mt_fhi/relax/H2/relaxed/go_art_mt_fhi_K_72_relaxed_12.out')
# print(cell)
# print(len(ats))
# for at in ats:
#     print(at)
