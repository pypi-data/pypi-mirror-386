# ================================== LICENSE ===================================
# Magnopy - Python package for magnons.
# Copyright (C) 2023-2025 Magnopy Team
#
# e-mail: anry@uv.es, web: magnopy.org
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# ================================ END LICENSE =================================


import numpy as np

from magnopy._spinham._convention import Convention
from magnopy._spinham._hamiltonian import SpinHamiltonian

# Save local scope at this moment
old_dir = set(dir())
old_dir.add("old_dir")


def load_grogu(filename, spin_values=None, spglib_types=None) -> SpinHamiltonian:
    r"""
    Reads spin Hamiltonian from the .txt file produced by |GROGU|_.

    For more information on GROGU's file format see |GROGU-FF|_.

    Parameters
    ----------

    filename : str
        Path to the .txt file produced by |GROGU|_.

    spin_values : (M, ) iterable of floats, optional
        Spin values for all magnetic atom. Order is the same as in |GROGU|_ file. Magnetic
        atoms are defined as those that have at least one parameter associated with them.
        If none given, magnopy uses spin values computed from DFT (as provided in the
        |GROGU|_ file).

    spglib_types : (M_prime, ) iterable of ints, optional
        Spglib types for all atoms (not only for magnetic ones, but for all). Order is the
        same as in |GROGU|_ file. If none given, then there will be no "spglib_types" key
        in ``spinham.atoms``.

    Returns
    -------

    spinham : :py:class:`.SpinHamiltonian`
        Spin Hamiltonian, that is built from the |GROGU|_ file.

    Raises
    ------

    ValueError
        If ``spin_values`` is provided and its length does not match the number of
        magnetic atoms in the Hamiltonian.

    ValueError
        If ``spglib_types`` is provided and its length does not match the number of
        atoms in the Hamiltonian.

    """

    convention = Convention.get_predefined("grogu")

    # Read the content of the file
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Read the cell
    i = 0
    while "cell" not in lines[i].lower() or "(ang)" not in lines[i].lower():
        i += 1

    i += 1

    cell = [
        list(map(float, lines[i].split())),
        list(map(float, lines[i + 1].split())),
        list(map(float, lines[i + 2].split())),
    ]

    # Read the atoms
    while "magnetic" not in lines[i].lower() or "sites" not in lines[i].lower():
        i += 1

    i += 1
    M = int(lines[i].split()[3])
    i += 1

    # Check if spin_values were provided and of correct length
    if spin_values is not None and len(spin_values) != M:
        raise ValueError(f"Expected {M} spin values, got {len(spin_values)}")
    # Check if spglib_types were provided and of correct length
    if spglib_types is not None and len(spglib_types) != M:
        raise ValueError(f"Expected {M} spglib types, got {len(spglib_types)}")

    name_to_index = {}
    atoms = dict(names=[], positions=[], spins=[], g_factors=[2 for _ in range(M)])

    for atom_index in range(M):
        i += 1
        words = lines[i].split()

        name = words[0]
        name_to_index[name] = atom_index

        positions = list(map(float, words[1:4]))
        positions = positions @ np.linalg.inv(cell)

        if spin_values is not None:
            spin = spin_values[atom_index]
        else:
            spin = float(words[4])

        atoms["names"].append(name)
        atoms["positions"].append(positions)
        atoms["spins"].append(spin)

    # Add spglib types if provided
    if spglib_types is not None:
        atoms["spglib_types"] = [int(_) for _ in spglib_types]

    # Construct spin Hamiltonian
    spinham = SpinHamiltonian(convention=convention, cell=cell, atoms=atoms)

    while (
        "intra-atomic" not in lines[i].lower()
        or "anisotropy" not in lines[i].lower()
        or "tensor" not in lines[i].lower()
        or "(mev)" not in lines[i].lower()
    ):
        i += 1

    for _ in range(M):
        i += 2
        name = lines[i].split()[0]
        alpha = name_to_index[name]
        i += 2
        parameter = [
            list(map(float, lines[i].split())),
            list(map(float, lines[i + 1].split())),
            list(map(float, lines[i + 2].split())),
        ]
        i += 2
        spinham.add_21(alpha=alpha, parameter=parameter)

    while (
        "exchange" not in lines[i].lower()
        or "tensor" not in lines[i].lower()
        or "(mev)" not in lines[i].lower()
    ):
        i += 1

    i += 1
    N = int(lines[i].split()[3])
    i += 2

    for _ in range(N):
        i += 2

        words = lines[i].split()
        alpha = name_to_index[words[0]]
        beta = name_to_index[words[1]]
        nu = tuple(list(map(int, words[2:5])))

        i += 2

        parameter = [
            list(map(float, lines[i].split())),
            list(map(float, lines[i + 1].split())),
            list(map(float, lines[i + 2].split())),
        ]

        i += 2

        spinham.add_22(
            alpha=alpha, beta=beta, nu=nu, parameter=parameter, when_present="replace"
        )

    return spinham


# Populate __all__ with objects defined in this file
__all__ = list(set(dir()) - old_dir)
# Remove all semi-private objects
__all__ = [i for i in __all__ if not i.startswith("_")]
del old_dir
