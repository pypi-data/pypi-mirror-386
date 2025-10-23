# ProbingMC (Python package: `Structure`)

*A lightweight, ASE‑style toolkit for crystal structures, molecules, and I/O to/from CIF/XYZ and Quantum ESPRESSO (`pw.x`) files.*

ProbingMC exposes a single importable package named **`Structure`**. You install the PyPI project `ProbingMC`, then import like:

```python
from Structure import Structure
````

---

## Key features

* **Core `Structure` class** for loading structures from **CIF**, **Quantum ESPRESSO** outputs (`vc-relax`, `relax`, `scf`), **QE inputs** (`.in`), and **XYZ/MOPAC**; includes coordinate transforms, supercells, rotations/reflections, atom insertion, and multiple writers (CIF/XYZ/MOP/QE input). 
* **CIF I/O**: parses `_cell_*` parameters and atomic positions; if CIF symmetry operations (`_symmetry_equiv_pos_as_xyz`) are present, atoms are duplicated accordingly (basic symmetry expansion). Writing uses a CIF template. 
* **Quantum ESPRESSO I/O**: reads `vc-relax` and `relax` outputs (including final cell, positions, and total energy when available), reads `.in` files, and writes QE inputs from templates. 
* **Atom utilities**: van der Waals/covalent radii, masses, simple overlap checks (vdW/covalent), neighbor handling, and pseudopotential name maps used when writing QE inputs. 
* **ASE interoperability**: convert to/from `ase.Atoms` (`get_ase`, `add_ase_structure`) for quick visualization or downstream workflows. 

> **Note on scope**: this project focuses on pragmatic structure manipulation. CIF symmetry handling is limited to duplicating positions from provided operations; it does not perform full symmetry analysis/reduction. 

---

## Install

From PyPI:

```bash
pip install ProbingMC
```

From source (editable dev install):

```bash
git clone https://github.com/Andrey-Tokarev/probingmc.git
cd probingmc
pip install -e .
```

> The package on import is **`Structure`** even though the distribution name is **`ProbingMC`**.

---

## Quickstart

```python
from Structure import Structure

# Load a CIF
s = Structure("examples/data/graphene.cif")   # reads cell + atoms and expands symmetry if present
print(s.number_of_atoms())

# Make a 2×2 supercell and export
s.super_cell(2, 2, 1)                          # builds supercell
s.write_structure_to_xyz(modifier="2x2")       # writes <name>_2x2.xyz next to the input
```

The `Structure` class supports `.cif`, QE `.out`/`.in`, and `.xyz`/MOPAC sources; writers include CIF/XYZ/MOP/QE‐input. See `write_structure_to_cif`, `write_structure_to_xyz`, `write_structure_to_qe_in`, rotations/reflections, and more in the source. 

**With ASE (optional):**

```python
ase_atoms = s.get_ase()                        # to ASE
# ... visualize or process with ASE ...
```



---

## Quantum ESPRESSO notes

* Readers: `load_structure_from_qe_relax` (also captures total energy), `load_structure_from_qe_vc_relax`, and `load_structure_from_qe_in`. 
* Writer: `write_structure_to_qe_in(...)` populates a QE input file using templates and pseudopotential maps declared in `Atom`. Ensure your pseudopotential filenames match the entries in `Atom.PPs_ONCV_PBE` or adjust them.
* **Template path**: the current writer uses a hard‑coded templates folder path in `QEIO.dump_structure_to_qe` (marked as a “quick fix”). Update that constant or refactor to load templates from a project‑relative `templates/` directory before publishing. 

---

## CIF notes

* CIF reader (`load_structure_from_cif`) parses cell parameters and atomic sites; when `_symmetry_equiv_pos_as_xyz` is present, it expands atoms by applying the listed operations. The CIF writer fills a `sample.cif` template—adjust the template location as needed. 

---

## API overview

* **`Structure.Structure`**: load/write, coordinate transforms, supercells, rotations (`rotate_structure_from_a_to_b`, bond‑to‑bond), atom add/copy/remove, double‑layer builder, surface/volume/composition utilities. 
* **`Structure.Atom`**: radii, masses, overlap checks, relaxed DOF flags, distance with/without periodic images. 
* **`Structure.CIFIO`** / **`Structure.QEIO`**: file readers/writers for CIF and QE formats.
* **`Structure.controls`**: simple error helper used across modules. 

---


## Requirements

* Python **3.10+** (pattern‑matching syntax is used in the QE input reader). 
* Runtime deps: `numpy` and `ase`.

---

## Contributing

PRs and issues are welcome. Please:

* Add a minimal example and/or unit test for new features.
* Keep I/O templates project‑relative and configurable.
* Avoid committing large generated files (`dist/`, `build/`, `*.out`, `*.xyz`)—see `.gitignore`.

---

## License

MIT — see [LICENSE](./LICENSE) for details.

