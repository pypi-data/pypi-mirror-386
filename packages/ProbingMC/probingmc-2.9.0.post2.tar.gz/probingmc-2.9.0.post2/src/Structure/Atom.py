import numpy as np
import math
from Structure.controls import error_throw


class Atom:
    # from here: http://periodictable.com/Properties/A/VanDerWaalsRadius.v.html
    vdw_radii = {"H": 1.2, "C": 1.7, "O": 1.52, "K": 2.75, "B": 1.92, "F": 1.47, "N": 1.55, "Si": 2.1, "Li": 1.82, "Na": 2.27}
    # from here: https://en.wikipedia.org/wiki/Covalent_radius
    covalent_radii = {"H": 0.31, "C": 0.75, "O": 0.66, "K": 2.03, "B": 0.82, "N": 0.71, "F": 0.64, "Si": 1.11, "Li": 1.28, "Na": 1.66}
    weights = {"H": 1.008, "C": 12.011, "O": 15.999, "K": 39.098, "B": 10.81, "N": 14.007, "F": 18.998}
    PPs = {"H": "H 1.008 H.pbe-mt_fhi.UPF", "C": "C 12.0107 C.pbe-mt_fhi.UPF",  # pseudo-potentials
           "O": "O 15.999 O.pbe-mt_fhi.UPF", "K": "K 39.098 K.pbe-mt_fhi.UPF"}
    PPs_pbe_rrkjus = {"H": "H 1.008 H.pbe-rrkjus.UPF", "C": "C 12.0107 C.pbe-rrkjus.UPF",  # pseudo-potentials
           "O": "O 15.999 O.pbe-rrkjus.UPF", "K": "K 39.098 K.pbe-n-mt.UPF", "B": "B 10.81 B.pbe-n-rrkjus_psl.1.0.0.UPF",
            "N": "N 14.007 N.pbe-n-rrkjus_psl.0.1.UPF", "F": "F 18.998 F.pbe-n-rrkjus_psl.0.1.UPF",
            "Ch": "Ch 12.0107 C.star1s-pbe-rrkjus.UPF", "Bh": "Bh 10.81 B.star1s-pbe-n-rrkjus_psl.1.0.0.UPF"}
    PPs_ONCV_PBE = {"H": "H 1.008 H_ONCV_PBE-1.0.upf", "C": "C 12.0107 C_ONCV_PBE-1.0.upf",  # pseudo-potentials
           "O": "O 15.999 O_ONCV_PBE-1.0.upf", "K": "K 39.098 K_ONCV_PBE-1.0.upf", "B": "B 10.81 B_ONCV_PBE-1.0.upf",
            "N": "N 14.007 N_ONCV_PBE-1.0.upf", "Li": "Li 6.94 Li_ONCV_PBE-1.0.upf", "Na": "Na 22.99 Na_ONCV_PBE-1.0.upf"}

    def __init__(self, element, coors, coors_type, cn=0, layer=None, branch=None):
        self.element = element
        self.cart_coors = self.cryst_coors = None
        if coors_type == 'cart':
            self.cart_coors = np.array(coors)
        elif coors_type == 'cryst':
            self.cryst_coors = np.array(coors)
        else:
            error_throw('Unknown type of coordinates!')
        if self.element not in Atom.vdw_radii:
            error_throw("No VdW radius for the element: " + self.element)
        self.vdw_radius = Atom.vdw_radii[self.element]
        if self.element not in Atom.covalent_radii:
            error_throw("No covalent radius for the element: " + self.element)
        self.covalent_radius = Atom.covalent_radii[self.element]
        self.relax_x = True  # for relaxation calculations
        self.relax_y = True
        self.relax_z = True
        # the rest is for YjG structure calculation
        self.nbs = []  # neighboring atoms
        self.cn = cn  # coordination number (number of neighbours)
        self.layer = layer  # layer (core is 0, adjucent atoms are 1, next 2 and so on, except H which have the same layer as the atom they bound to)
        self.branch = branch  # branch of the structure (in case of YjG there are three branches)

    def add_neighbour(self, at, bond_degeneracy=1):
        self.nbs.append(at)
        self.cn += bond_degeneracy

    def fix_x(self):
        self.relax_x = False

    def fix_y(self):
        self.relax_y = False

    def fix_z(self):
        self.relax_z = False

    def is_relax_everything(self):
        return self.relax_x and self.relax_y and self.relax_z

    def relaxation_flags(self):
        flags = ""
        flags += "1" if self.relax_x else "0"
        flags += " 1" if self.relax_y else " 0"
        flags += " 1" if self.relax_z else " 0"
        return flags

    def cryst_to_cart(self, cell):
        if self.cryst_coors is None:
            error_throw("No crystal coodinates!")
        cell_matrix = cell
        if type(cell) is not np.ndarray:
            cell_matrix = np.array(cell)
        self.cart_coors = np.dot(self.cryst_coors, cell_matrix)

    def cart_to_cryst(self, cell_matrix_inv, shift_vect=None):
        if self.cart_coors is None:
            error_throw("No cartesian coodinates!")
        self.cryst_coors = np.dot(self.cart_coors, cell_matrix_inv) % 1.0
        if shift_vect is not None:
            self.cryst_coors += shift_vect
            self.cryst_coors %= 1.0

    '''
    In case of cell != None it calculates minimum distance
    to all neighboring images
    '''
    def dist_to_atom(self, atom, cell=None):
        if self.cart_coors is None or atom.cart_coors is None:
            error_throw("No cartesian coordinates!")
        return np.linalg.norm(self.cart_coors - atom.cart_coors) if cell is None else Atom.min_periodic_dist(self, atom, cell)

    @staticmethod
    def min_periodic_dist(a1, a2, cell):
        sq_distances = []  # squared distances
        for i in range(-1, 2):
            for j in range(-1, 2):
                for k in range(-1, 2):
                    if a1 == a2 and i == 0 and j == 0 and k == 0:  # for a1 == a2 skip self-distance
                        continue
                    sq_distances.append(Atom.sq_periodic_dist(a1, a2, i, j, k, cell))
        return math.sqrt(min(sq_distances))

    @staticmethod
    def min_periodic_dist_deg(a1, a2, cell):  # bond degeneracy counted and returned as well
        sq_distances = []  # squared distances
        for i in range(-1, 2):
            for j in range(-1, 2):
                for k in range(-1, 2):
                    if a1 == a2 and i == 0 and j == 0 and k == 0:  # for a1 == a2 skip self-distance
                        continue
                    sq_distances.append(Atom.sq_periodic_dist(a1, a2, i, j, k, cell))
        min_sqd = None  # minimal square distance
        bond_deg = 1  # bond degeneracy (appears because of PBC)
        for sqd in sorted(sq_distances):
            if min_sqd is None:
                min_sqd = sqd
            elif abs(sqd - min_sqd) < 0.00001:  # the same bond length
                bond_deg += 1
            else:
                break
        return math.sqrt(min_sqd), bond_deg

    @staticmethod
    def sq_periodic_dist(a1, a2, nx, ny, nz, cell):
        cryst_coors = np.copy(a2.cryst_coors)
        a2_new = Atom("C", cryst_coors, "cryst")
        a2_new.cryst_coors[0] += nx
        a2_new.cryst_coors[1] += ny
        a2_new.cryst_coors[2] += nz
        a2_new.cryst_to_cart(cell)
        return a1.sq_dist_to_atom(a2_new)

    # square distance between atoms
    def sq_dist_to_atom(self, atom):
        if self.cart_coors is None or atom.cart_coors is None:
            error_throw("No cartesian coordinates!")
        dr = self.cart_coors - atom.cart_coors
        return np.dot(dr, dr)

    '''
    k - reduction coefficient
    '''
    def overlap_with_atom_vdw(self, atom, cell=None, k=1.0):
        if self.dist_to_atom(atom, cell) > k * (self.vdw_radius + atom.vdw_radius):
            return False
        return True

    def overlap_with_atom_covalent(self, atom, cell=None):
        if self.dist_to_atom(atom, cell) > self.covalent_radius + atom.covalent_radius:
            return False
        return True

    def print_array(self, ar):
        if len(ar) == 0:
            return "[]"
        res = "["
        for i in range(len(ar) - 1):
            res += str(ar[i]) + ", "
        res += str(ar[-1])
        res += "]"
        return res

    def print(self):
        return self.element + ": " + self.print_array(self.cryst_coors) + "; " + self.print_array(self.cart_coors)

    def __str__(self, for_array=False):
        return self.element + ": " + str(self.cryst_coors) + "; " + str(self.cart_coors)

    def weight(self):
        return Atom.weights[self.element]

    def change_element(self, new_el):
        self.element = new_el
        if self.element not in Atom.vdw_radii:
            error_throw("No VdW radius for the element: " + self.element)
        self.vdw_radius = Atom.vdw_radii[self.element]
        if self.element not in Atom.covalent_radii:
            error_throw("No covalent radius for the element: " + self.element)
        self.covalent_radius = Atom.covalent_radii[self.element]

# cell0 = [[10, 0, 0],
#          [0, 10, 0],
#          [0, 0, 10]]
#
# a1 = Atom("H", [0, 0, 0], "cart")
# a2 = Atom("C", [1, 1, 8], "cart")
# a3 = Atom("O", [0.1, 0.1, 0.1], "cryst")
# a3.cryst_to_cart(cell0)
# print(a3)
# print(a2.dist_to_atom(a3))
# print(a2.overlap_with_atom(a3))
