import numpy as np
import re
import math
import os.path
from Structure.controls import error_throw
from Structure.CIFIO import load_structure_from_cif, dump_structure_to_cif
from Structure.QEIO import load_structure_from_qe_vc_relax, dump_structure_to_qe, load_structure_from_qe_relax, load_structure_from_qe_in
from Structure.Atom import Atom
import ase


'''
Currently can create class from cif (primitive version), QE out and xyz files 
'''
class Structure:
    # expansion_coefficient expands entire cell, - realized only for cif files
    def __init__(self, filename, type_relax='vc-relax', shift_vect=None, expansion_coefficient=1.0, final=True):
        ro = re.search('^.+\.(.+)', filename)
        if ro is None:
            error_throw("Filename error")
        self.filename = filename
        self.type_relax = type_relax
        self.expansion_coefficient = expansion_coefficient
        self.cell_matrix = None
        self.a_cell = self.b_cell = self.c_cell = self.alpha_cell = self.beta_cell = self.gamma_cell = None
        self.energy = None  # will be found only in case of QE 'relax' calculation
        extension = ro.group(1)
        if extension == "cif":
            cell_components, self.atoms = load_structure_from_cif(filename)
            self.a_cell, self.b_cell, self.c_cell, self.alpha_cell, self.beta_cell, self.gamma_cell = cell_components
            self.a_cell *= self.expansion_coefficient
            self.b_cell *= self.expansion_coefficient
            self.c_cell *= self.expansion_coefficient
            self.calculate_cell_matrix()
            self.file_type = 'cif'
        elif extension == "out":
            if type_relax == 'vc-relax':
                self.cell_matrix, self.atoms = load_structure_from_qe_vc_relax(filename)
            elif type_relax == 'mopac':  # mopac output
                self.atoms = load_structure_from_mop_out(filename, final)
                self.a_cell, self.b_cell, self.c_cell = self.cell_vectors_from_xyz()
                self.alpha_cell = self.beta_cell = self.gamma_cell = 90
                self.calculate_cell_matrix()
            elif type_relax == 'scf':
                self.cell_matrix, self.atoms, self.energy = load_structure_from_qe_relax(filename, True)
            else:  # 'relax' calculations
                self.cell_matrix, self.atoms, self.energy = load_structure_from_qe_relax(filename)
            self.calculate_cell_components()
            self.file_type = 'out'
        elif extension == "in":
            self.cell_matrix, self.atoms = load_structure_from_qe_in(filename)
            self.calculate_cell_components()
            self.file_type = 'in'
        elif extension == "xyz":
            self.file_type = 'xyz'
            self.atoms = load_structure_from_xyz(filename)
            self.a_cell, self.b_cell, self.c_cell = self.cell_vectors_from_xyz()
            self.alpha_cell = self.beta_cell = self.gamma_cell = 90
            self.calculate_cell_matrix()
        else:
            error_throw("Only cif or QE output files are considered")
        self.cell_matrix_inv = np.linalg.inv(self.cell_matrix)
        for atom in self.atoms:
            if extension == "xyz" or self.type_relax == "mopac":
                atom.cart_to_cryst(self.cell_matrix_inv, shift_vect)
                if shift_vect is not None:
                    atom.cryst_to_cart(self.cell_matrix)  # to make cartesian in line with crystal
            else:
                atom.cryst_to_cart(self.cell_matrix)

    def add_atom(self, el, coors, type):
        at = Atom(el, coors, type)
        if type == 'cart':
            at.cart_to_cryst(self.cell_matrix_inv)
        elif type == 'cryst':
            at.cryst_to_cart(self.cell_matrix)
        else:
            error_throw('Unknown type of coordinates!')
        self.atoms.append(at)

    def add_ase_structure(self, ase_str):
        for ase_atom in ase_str:
            self.add_atom(el=ase_atom.symbol, coors=ase_atom.position, type='cart')

    def add_structure(self, struc):
        for a in struc.atoms:
            self.add_atom(el=a.element, coors=a.cart_coors, type='cart')

    '''
    Attach a new atom to the existing one through the bond
    atom - atom to which new atom is attached
    bond - vector of the new bond
    element - element name of the new atom
    '''
    def attach_atom(self, atom, bond, element):
        position = atom.cart_coors + bond
        self.add_atom(element, position, 'cart')

    def set_cell_height(self, new_height):
        self.c_cell = new_height
        self.calculate_cell_matrix()
        self.cell_matrix_inv = np.linalg.inv(self.cell_matrix)
        for atom in self.atoms:
            atom.cart_to_cryst(self.cell_matrix_inv)

    '''
    sets atom to the new position (pos)
    '''
    def atom_new_pos(self, atom, pos, type, wrap):
        pos_np = np.array(pos)
        if type == 'cart':
            if wrap:
                atom.cart_coors[0] = pos_np[0] % self.a_cell
                atom.cart_coors[1] = pos_np[1] % self.b_cell
                atom.cart_coors[2] = pos_np[2] % self.c_cell
            else:
                atom.cart_coors = pos_np
            atom.cart_to_cryst(self.cell_matrix_inv)
        elif type == 'cryst':
            if wrap:
                for i in range(3):
                    atom.cryst_coors[i] = pos_np[i] % 1.0
            else:
                atom.cryst_coors = pos_np
            atom.cryst_to_cart(self.cell_matrix)
        else:
            error_throw('Unknown type of coordinates!')

    def move_atom(self, atom, vector, type, wrap):
        vec_np = np.array(vector)
        new_pos = vec_np + (atom.cart_coors if type == 'cart' else atom.cryst_coors)
        self.atom_new_pos(atom, new_pos, type, wrap)

    def move_structure(self, vector, type, wrap, indices=None):
        if indices is None:
            indices = range(len(self.atoms))
        for ind in indices:
            atom = self.atoms[ind]
            self.move_atom(atom, vector, type, wrap)

    # return list of indicies of new atoms
    def copy_atoms(self, indices):
        first_new_index = len(self.atoms)
        for ind in indices:
            at = self.atoms[ind]
            copy_at = Atom(at.element, at.cart_coors, 'cart', cn=at.cn, layer=at.layer, branch=at.branch)
            copy_at.cart_to_cryst(self.cell_matrix_inv)
            self.atoms.append(copy_at)
        return list(range(first_new_index, len(self.atoms)))

    # r - point to reflect
    # h - plane vector
    # d - plane scalar
    @staticmethod
    def reflect_through_plane(r, h, d):
        r = np.array(r)
        h = np.array(h)
        return r - 2 * h * (np.dot(h,r) + d) / np.dot(h, h)

    # h - plane vector
    # d - plane scalar
    def reflect_structure_through_plane(self, atom_indices, h, d):
        for index in atom_indices:
            atom = self.atoms[index]
            # now reflect this atom through the plane
            self.atom_new_pos(atom, Structure.reflect_through_plane(atom.cart_coors, h, d), 'cart')

    def decoration(self, atom_indices, height, el):
        position = np.array([0.0, 0.0, 0.0])
        for index in atom_indices:
            position += self.atoms[index].cart_coors
        position /= len(atom_indices)
        position += np.array([0.0, 0.0, height])
        self.add_atom(el, position, "cart")
    
    def write_structure_to_cif(self, modifier=None, inserted_atoms=None, selected_atoms=None):
        cell_components = (self.a_cell, self.b_cell, self.c_cell, self.alpha_cell, self.beta_cell, self.gamma_cell)
        if modifier is not None:
            path, modified_name = Structure.modified_name(self.filename, str(modifier))
        else:
            path, modified_name = Structure.modified_name(self.filename)
        new_filename = path + modified_name + '.cif'
        print(new_filename)
        old_atoms = None
        if selected_atoms is None:
            old_atoms = self.atoms
        else:
            old_atoms = []
            for ind in selected_atoms:
                old_atoms.append(self.atoms[ind])
        if inserted_atoms is not None:
            dump_structure_to_cif(cell_components, old_atoms + inserted_atoms, new_filename)
        else:
            dump_structure_to_cif(cell_components, old_atoms, new_filename)

    def write_structure_to_xyz(self, modifier=None, inserted_atoms=None, new_path_filename=None):
        if new_path_filename is None:
            if modifier is not None:
                path, modified_name = Structure.modified_name(self.filename, str(modifier))
            else:
                path, modified_name = Structure.modified_name(self.filename)
            new_filename = path + modified_name + '.xyz'
        else:
            ro = re.search("(\w+)\.xyz$", new_path_filename)
            if not ro:
                error_throw("Could not resolve filename!")
            name = ro.group(1)
            modified_name = name
            new_filename = new_path_filename
        print(new_filename)
        if inserted_atoms is not None:
            dump_structure_to_xyz(self.atoms + inserted_atoms, new_filename, modified_name)
        else:
            dump_structure_to_xyz(self.atoms, new_filename, modified_name)
        return new_filename

    def write_structure_to_mop(self, modifier=None, inserted_atoms=None, new_path_filename=None):
        if new_path_filename is None:
            if modifier is not None:
                path, modified_name = Structure.modified_name(self.filename, str(modifier))
            else:
                path, modified_name = Structure.modified_name(self.filename)
            new_filename = path + modified_name + '.mop'
        else:
            ro = re.search("(\w+)\.mop$", new_path_filename)
            if not ro:
                error_throw("Could not resolve filename!")
            name = ro.group(1)
            modified_name = name
            new_filename = new_path_filename
        print(new_filename)
        if inserted_atoms is not None:
            dump_structure_to_mop(self.atoms + inserted_atoms, new_filename, modified_name)
        else:
            dump_structure_to_mop(self.atoms, new_filename, modified_name)
        return new_filename

    def write_structure_to_qe_in(self, modifier=None, inserted_atoms=None, type='scf'):
        cell_components = (self.a_cell, self.b_cell, self.c_cell, self.alpha_cell, self.beta_cell, self.gamma_cell)
        if modifier is not None:
            path, modified_name = Structure.modified_name(self.filename, str(modifier))
        else:
            path, modified_name = Structure.modified_name(self.filename)
        new_filename = path + modified_name + '.in'
        print(new_filename)
        if inserted_atoms is not None:
            dump_structure_to_qe(cell_components, self.atoms + inserted_atoms, new_filename, modified_name, type, path=path)
        else:
            dump_structure_to_qe(cell_components, self.atoms, new_filename, modified_name, type, path=path)

    @staticmethod
    def modified_name(filename, modifier=None):
        path, full_name = os.path.split(filename)
        path += "/"
        ro = re.search("^(\w+)\.\w+", full_name)
        if not ro:
            error_throw("Could not resolve filename!")
        name = ro.group(1)
        modified_name = name
        if modifier is not None:
            modified_name += "_" + modifier
        return path, modified_name

    def calculate_cell_matrix(self):
        gamma_rad = self.gamma_cell * math.pi / 180
        beta_rad = self.beta_cell * math.pi / 180
        alpha_rad = self.alpha_cell * math.pi / 180
        ax = self.a_cell
        bx = self.b_cell * math.cos(gamma_rad)
        by = self.b_cell * math.sin(gamma_rad)
        cx = self.c_cell * math.cos(beta_rad)
        cy = (self.b_cell * self.c_cell * math.cos(alpha_rad) - bx * cx) / by
        cz = math.sqrt(self.c_cell * self.c_cell - cx * cx - cy * cy)
        self.cell_matrix = np.array([[ax, 0, 0],
                                     [bx, by, 0],
                                     [cx, cy, cz]])

    def cell_volume(self):
        return np.linalg.det(self.cell_matrix)

    def ab_surface(self):
        """
        :return: surface of ab face
        """
        return self.a_cell * self.b_cell * math.sin(self.gamma_cell * math.pi / 180)

    def elemental_composition(self):
        composition = {}
        for atom in self.atoms:
            el = atom.element
            if el in composition:
                composition[el] += 1
            else:
                composition[el] = 1
        n_atoms = len(self.atoms)
        for key in composition.keys():
            composition[key] *= 100 / n_atoms
        return composition

    @staticmethod
    def vector_module(v):
        return math.sqrt(np.dot(v, v))

    @staticmethod
    def angle_between_vectors(v1, v2):
        v1_mod = Structure.vector_module(v1)
        v2_mod = Structure.vector_module(v2)
        cos_angle = np.dot(v1, v2) / (v1_mod * v2_mod)
        return math.acos(cos_angle) * 180 / math.pi

    def calculate_cell_components(self):
        a_vector = self.cell_matrix[0]
        b_vector = self.cell_matrix[1]
        c_vector = self.cell_matrix[2]
        self.a_cell = Structure.vector_module(a_vector)
        self.b_cell = Structure.vector_module(b_vector)
        self.c_cell = Structure.vector_module(c_vector)
        self.alpha_cell = Structure.angle_between_vectors(b_vector, c_vector)
        self.beta_cell = Structure.angle_between_vectors(a_vector, c_vector)
        self.gamma_cell = Structure.angle_between_vectors(a_vector, b_vector)

    def dist_between_atoms(self, i, j):
        if len(self.atoms) == 0:
            error_throw("No atoms in the structure!")
        if i < 0 or i >= len(self.atoms):
            error_throw("First index is out of boundaries!")
        if j < 0 or j >= len(self.atoms):
            error_throw("Second index is out of boundaries!")
        return (self.atoms[i]).dist_to_atom(self.atoms[j])

    # returns index of the reference atom
    # refernce atom - atom through which horizontal refelction plain comes
    def find_reference_atom(self):
        self.add_atom('C', [0.0, 0.0, 0.0], 'cryst')  # put atom to the origin to calculate distances to it
        ind_last_atom = self.number_of_atoms() - 1  # index of the last atom (dummy "origin" atom)
        ref_atom_ind = None
        min_dist = 1000000000  # arbitrary large number
        for at_ind in range(ind_last_atom):
            dist = self.dist_between_atoms(at_ind, ind_last_atom)
            if dist < min_dist:
                min_dist = dist
                ref_atom_ind = at_ind
        # block with choosing atom closest to the origin (0, 0, 0)
        self.remove_atom(ind_last_atom)
        return ref_atom_ind

    # chess_flip - alternating original cell with reflected in z plane one
    # z plan comes through the atom closest to the origin (0.0, 0.0, 0.0)
    def super_cell(self, nx, ny, nz, chess_flip=False):
        assert (not chess_flip) or (nx % 2 == 0 and ny % 2 == 0 and nz % 2 == 0), "With chess flip nx, ny, nz must be even!"
        reference_atom_index = None
        if chess_flip:
            reference_atom_index = self.find_reference_atom()
        # print("Reference atom's index is", reference_atom_index)
        if nx > 1:
            self.sc_build(0, nx, reference_atom_index)
        if ny > 1:
            self.sc_build(1, ny, reference_atom_index)
        if nz > 1:
            self.sc_build(2, nz, reference_atom_index)

    def sc_build(self, dim, n, reference_atom_index=None):
        trans_vect = np.array([0.0, 0.0, 0.0])  # translational vector
        trans_vect[dim] = 1 / float(n)
        self.cell_matrix[dim] *= n
        if dim == 0:
            self.a_cell *= n
        elif dim == 1:
            self.b_cell *= n
        elif dim == 2:
            self.c_cell *= n
        self.cell_matrix_inv = np.linalg.inv(self.cell_matrix)
        z_plane_refl = None  # z-plane relative to which reflection is happening
        if reference_atom_index is not None:
            z_plane_refl = self.atoms[reference_atom_index].cryst_coors[2]
            if dim == 2:
                z_plane_refl /= n
        new_atoms = []
        for atom in self.atoms:
            atom.cryst_coors[dim] /= n
            for i in range(n - 1):
                copy_cryst_coors = np.copy(atom.cryst_coors)  # crystal coordinates of the copy-atom
                if reference_atom_index is not None:
                    if i % 2 == 0:  # reflect every other copy
                        copy_cryst_coors[2] = 2 * z_plane_refl - copy_cryst_coors[2]
                new_atom = Atom(atom.element, copy_cryst_coors + (i + 1) * trans_vect, "cryst")
                new_atom.cryst_to_cart(self.cell_matrix)
                new_atoms.append(new_atom)
        self.atoms.extend(new_atoms)

    def print(self):
        '''
        print strucdture with arrays with commas
        :return:
        '''
        s = "Crystal cell:\n"
        s += " a = " + str(self.a_cell) + "\n"
        s += " b = " + str(self.b_cell) + "\n"
        s += " c = " + str(self.c_cell) + "\n"
        s += " alpha = " + str(self.alpha_cell) + "\n"
        s += " beta = " + str(self.beta_cell) + "\n"
        s += " gamma = " + str(self.gamma_cell) + "\n"
        s += str(self.cell_matrix) + "\n\n"
        s += "Atoms:\n"
        i = 0
        for atom in self.atoms:
            s += str(i) + "  " + atom.print() + "\n"
            i += 1
        print(s)

    def __str__(self):
        s = "Crystal cell:\n"
        s += " a = " + str(self.a_cell) + "\n"
        s += " b = " + str(self.b_cell) + "\n"
        s += " c = " + str(self.c_cell) + "\n"
        s += " alpha = " + str(self.alpha_cell) + "\n"
        s += " beta = " + str(self.beta_cell) + "\n"
        s += " gamma = " + str(self.gamma_cell) + "\n"
        s += str(self.cell_matrix) + "\n\n"
        s += "Atoms:\n"
        i = 0
        for atom in self.atoms:
            s += str(i) + "  " + str(atom) + "\n"
            i += 1
        return s

    def point_xy_images(self, p):
        images = []
        for i in range(-1, 2):
            for j in range(-1, 2):
                images.append(self.point_xy_image(p, i, j))
        return images

    def point_xy_image(self, p, nx, ny):
        cryst_coors = np.dot(p, self.cell_matrix_inv)
        cryst_coors[0] += nx
        cryst_coors[1] += ny
        return np.dot(cryst_coors, self.cell_matrix)

    '''
    Return center of atoms of the given element
    '''
    def element_center(self, el):
        sum_vect = np.array([0.0, 0.0, 0.0])
        n_elements = 0
        for atom in self.atoms:
            if atom.element == el:
                sum_vect += atom.cart_coors
                n_elements += 1
        return sum_vect / n_elements

    '''
    Weight of the system
    '''
    def weight(self):
        w = 0
        for atom in self.atoms:
            w += atom.weight()
        return w

    def remove_atoms(self):
        self.atoms = []

    # should be used as the last operation
    # because it affect all indices after specified "index"
    def remove_atom(self, index):
        del self.atoms[index]

    '''
    For one layer material (like graphene):
    make second shifted layer at distance d
    the whole structure hase 2d axis c
    so it becomes bulk layered material
    d - interlayer spacing distance
    shift_vector is in crystal coordinates
    '''
    def make_double_layer_structure(self, d=6.0, shift_vector=[0.5, 0.5, 0.0], reflection=None):
        old_len = len(self.atoms)
        self.copy_atoms(range(old_len))
        if reflection is not None:
            h, d0 = reflection
            self.reflect_structure_through_plane(range(old_len, len(self.atoms)), h, d0)
        self.move_structure([0, 0, d], 'cart', indices=range(old_len, len(self.atoms)))
        self.move_structure(shift_vector, 'cryst', indices=range(old_len, len(self.atoms)))
        self.set_cell_height(2 * d)


    "Returns mix and max of cartesian coordinates of the structure"
    def min_max_coors(self):
        coors = []
        for atom in self.atoms:
            coors.append(atom.cart_coors)
        return np.amin(coors, 0), np.amax(coors, 0)

    def cell_vectors_from_xyz(self):
        min_xyz, max_xyz = self.min_max_coors()
        return (max_xyz - min_xyz) + np.array([15, 15, 15])  # 5 padding from each edge

    def substitute_atom(self, index, new_el):
        self.atoms[index].change_element(new_el)

    def rotate_structure(self, rot_matr, indices=None):
        rot_matr_np = np.array(rot_matr)
        if indices is None:
            indices = range(len(self.atoms))
        for ind in indices:
            atom = self.atoms[ind]
            atom.cart_coors = np.matmul(rot_matr_np, atom.cart_coors)
            atom.cart_to_cryst(self.cell_matrix_inv)

    def rotate_structure_from_a_to_b(self, a, b, indices=None):
        if indices is None:
            indices = range(len(self.atoms))
        rotation_matrix = rotation_matrix_from_a_to_b(a, b)
        self.rotate_structure(rotation_matrix, indices)

    # a1, a2, b1, b2 - atom indicies of bond a and b
    def rotate_structure_from_bond_to_bond(self, a1, a2, b1, b2, indices=None):
        if indices is None:
            indices = range(len(self.atoms))
        bond1 = self.atoms[a2].cart_coors - self.atoms[a1].cart_coors
        bond2 = self.atoms[b2].cart_coors - self.atoms[b1].cart_coors
        self.rotate_structure_from_a_to_b(bond1, bond2, indices)

    def get_ase(self, inserted_atoms=None):
        ase_str = ase.Atoms()
        atoms = self.atoms
        if inserted_atoms is not None:
            atoms = self.atoms + inserted_atoms
        for atom in atoms:
            at = ase.Atom(atom.element, atom.cart_coors)
            ase_str.append(at)
        return ase_str

    def number_of_atoms(self):
        return len(self.atoms)

    def number_of_elements(self):
        list_of_elements = []
        for atom in self.atoms:
            list_of_elements.append(atom.element)
        return len(set(list_of_elements))


def load_structure_from_xyz(filename):
    if not os.path.isfile(filename):
        error_throw("There is no such file: " + filename)
    f = open(filename)
    atoms = []
    for line in f:
        ro = re.search('^\s*(\w+)\s+(-?\d*\.\d*)\s+(-?\d*\.\d*)\s+(-?\d*\.\d*)\s*', line)
        if ro is not None:
            label = ro.group(1)
            x = float(ro.group(2))
            y = float(ro.group(3))
            z = float(ro.group(4))
            ro = re.search('(\D)+', label)
            if not ro:
                error_throw("No element name was found in the element label: " + label)
            element = ro.group(1)
            atoms.append(Atom(element, [x, y, z], "cart"))
    return atoms


def load_structure_from_mop_out(filename, final=True):
    if not os.path.isfile(filename):
        error_throw("There is no such file: " + filename)
    f = open(filename)
    cart_coor_flag = 0  # index of 'CARTESIAN COORDINATES' phrase appearance
    reading_flag = 0  # 0 - before reading, 1 - reading, 2 - reading finished
    atoms = []
    image_index = 2 if final else 1
    for line in f:
        ro = re.search('CARTESIAN COORDINATES', line)
        if ro is not None:
            cart_coor_flag += 1
            continue
        if cart_coor_flag == image_index and reading_flag < 2:  # final coordinates appear after the second appearance of the 'CARTESIAN COORDINATES'
            ro = re.search('^\s*\d+\s*(\w+)\s+(-?\d*\.\d*)\s+(-?\d*\.\d*)\s+(-?\d*\.\d*)\s*', line)
            if ro is not None:
                reading_flag = 1
                label = ro.group(1)
                x = float(ro.group(2))
                y = float(ro.group(3))
                z = float(ro.group(4))
                ro = re.search('(\D)+', label)
                if not ro:
                    error_throw("No element name was found in the element label: " + label)
                element = ro.group(1)
                atoms.append(Atom(element, [x, y, z], "cart"))
            elif reading_flag == 1:
                reading_flag = 2  # finished reading coordinates
    return atoms


def dump_structure_to_mop(atoms, filename, name):
    f = open(filename, 'w')
    f.write("PM7\n")
    f.write(name + "\n\n")
    for atom in atoms:
        el = atom.element
        x, y, z = atom.cart_coors
        line = el + "\t" + str(x) + "\t" + "1" + "\t" + str(y) + "\t" + "1" + "\t" + str(z) + "\t" + "1" + "\n"
        f.write(line)
    f.close()


def dump_structure_to_xyz(atoms, filename, name):
    f = open(filename, 'w')
    f.write(str(len(atoms)) + "\n")
    f.write(name + "\n")
    for atom in atoms:
        el = atom.element
        x, y, z = atom.cart_coors
        line = el + "\t" + str(x) + "\t" + str(y) + "\t" + str(z) + "\n"
        f.write(line)
    f.close()


# return rotation matrix, that transforms vector a to vector b
def rotation_matrix_from_a_to_b(a, b):
    au = a / np.linalg.norm(a)  # make unit vectors
    bu = b / np.linalg.norm(b)
    c = np.dot(au, bu)
    v = np.cross(au, bu)
    s = np.linalg.norm(v)

    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    I = np.identity(3)

    R = I + vx + np.matmul(vx, vx) * (1 - c) / (s * s)

    return R

