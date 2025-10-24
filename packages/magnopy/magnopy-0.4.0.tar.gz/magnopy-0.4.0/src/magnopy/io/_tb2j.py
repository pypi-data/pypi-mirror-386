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
from wulfric.crystal import get_distance

from magnopy._parameters._p22 import from_dmi, from_iso
from magnopy._spinham._convention import Convention
from magnopy._spinham._hamiltonian import SpinHamiltonian

# Save local scope at this moment
old_dir = set(dir())
old_dir.add("old_dir")


def load_tb2j(
    filename, spin_values=None, spglib_types=None, g_factors=None, quiet=True
) -> SpinHamiltonian:
    r"""
    Reads spin Hamiltonian from the "exchange.out" file produced by |TB2J|_.

    Parameters
    ----------

    filename : str
        Path to the "exchange.out" file produced by |TB2J|_.

    spin_values : (M, ) iterable of floats, optional
        Spin values for all magnetic atoms. Order is the same as in |TB2J|_ file. Magnetic
        atoms are defined as those that have at least one parameter associated with them.
        If none given, magnopy sets spin value as :math:`|\boldsymbol{m} / g_{factor}|`
        for each spin, where :math:`\boldsymbol{m}` is the magnetic moment, read from the
        |TB2J|_ file.

    spglib_types : (M_prime, ) iterable of ints, optional
        Spglib types for all atoms (not only for magnetic ones, but for all). Order is the
        same as in |TB2J|_ file. If none given, then there will be no "spglib_types" key
        in ``spinham.atoms``.

    g_factors : (M, ) iterable of floats, optional
        g-factors for all atoms. Order is the same as in |TB2J|_ file. If none given, then
        magnopy sets :math:`g = 2` for all atoms.

    quiet : bool, default True
        If ``False``, warnings are printed when distances between atoms computed by
        magnopy are different from the distances read from the |TB2J|_ file. This is a
        legacy feature, kept for the sake of backward compatibility. See Notes for
        details.

    Returns
    -------

    spinham : :py:class:`.SpinHamiltonian`
        Spin Hamiltonian, that is built from the |TB2J|_ file.

    Raises
    ------

    ValueError
        If ``spin_values`` is provided and its length does not match the number of
        magnetic atoms in the Hamiltonian.

    ValueError
        If ``spglib_types`` is provided and its length does not match the number of
        atoms in the Hamiltonian.


    Notes
    -----

    |TB2J|_ outputs distances between atoms for each exchange bond. Magnopy do not use
    those, but rather computes distances based on the unit cell and atom positions if
    necessary. At the moment of reading the file it can check if the distance read from
    the file is different from the computed one and print a warning if ``quiet=False``.
    Computed and read distances tend to differ in the last digits, since the unit cell is
    provided with the same precision as the distance in the |TB2J|_ file.
    """

    minor_sep = "-" * 88
    garbage = str.maketrans(
        {"(": None, ")": None, "[": None, "]": None, ",": None, "'": None}
    )
    # Do not correct spelling, it is taken from TB2J.
    cell_flag = "Cell (Angstrom):"
    atoms_flag = "Atoms:"
    atom_end_flag = "Total"
    exchange_flag = "Exchange:"
    iso_flag = "J_iso:"
    aniso_flag = "J_ani:"
    dmi_flag = "DMI:"

    file = open(filename, "r", encoding="utf-8")
    # model = SpinHamiltonian(convention="TB2J")
    line = True

    # Read everything before exchange
    while line:
        line = file.readline()

        # Read cell
        if line and cell_flag in line:
            a1 = file.readline().split()
            a2 = file.readline().split()
            a3 = file.readline().split()

            cell = np.array(
                [
                    list(map(float, a1)),
                    list(map(float, a2)),
                    list(map(float, a3)),
                ]
            )

        # Read atoms
        if line and atoms_flag in line:
            atoms = dict(names=[], positions=[], magnetic_moments=[], charges=[])
            line = file.readline()
            line = file.readline()
            line = file.readline().split()
            i = 0
            while line and atom_end_flag not in line:
                try:
                    # Slicing is not used intentionally.
                    magmom = tuple(map(float, [line[5], line[6], line[7]]))
                except IndexError:
                    magmom = float(line[5])
                try:
                    charge = float(line[4])
                except IndexError:
                    charge = None

                position = np.array(tuple(map(float, line[1:4]))) @ np.linalg.inv(cell)
                atoms["names"].append(line[0])
                atoms["positions"].append(position)
                atoms["magnetic_moments"].append(magmom)
                atoms["charges"].append(charge)

                line = file.readline().split()
                i += 1

        # Check if the exchange section is reached
        if line and exchange_flag in line:
            break

    # Populate g_factors of atoms
    if g_factors is None:
        g_factors = [2.0 for _ in range(len(atoms["names"]))]

    atoms["g_factors"] = g_factors

    # Create a spin Hamiltonian
    spinham = SpinHamiltonian(
        cell=cell, atoms=atoms, convention=Convention.get_predefined(name="tb2j")
    )

    # Prepare index mapping for atom names
    index_mapping = {}

    # Names of the atoms are unique in the TB2J files
    for index, name in enumerate(spinham.atoms.names):
        index_mapping[name] = index

    # Read exchange (22) parameters
    while line:
        while line and minor_sep not in line:
            line = file.readline()
        line = file.readline().translate(garbage).split()
        atom1 = index_mapping[line[0]]
        atom2 = index_mapping[line[1]]
        ijk = tuple(map(int, line[2:5]))
        distance = float(line[-1])
        iso = None
        aniso = None
        dmi = None
        while line and minor_sep not in line:
            line = file.readline()

            # Read isotropic exchange
            if line and iso_flag in line:
                iso = float(line.split()[-1])

            # Read anisotropic exchange
            if line and aniso_flag in line:
                aniso = np.array(
                    [
                        list(map(float, file.readline().translate(garbage).split())),
                        list(map(float, file.readline().translate(garbage).split())),
                        list(map(float, file.readline().translate(garbage).split())),
                    ]
                )

            # Read DMI
            if line and dmi_flag in line:
                dmi = tuple(map(float, line.translate(garbage).split()[-3:]))

        parameter = np.zeros((3, 3), dtype=float)
        if iso is not None:
            parameter = parameter + from_iso(iso=iso)
        if dmi is not None:
            parameter = parameter + from_dmi(dmi=dmi)
        if aniso is not None:
            parameter = parameter + aniso

        # Adding info from the exchange block to the SpinHamiltonian structure
        spinham.add_22(
            alpha=atom1,
            beta=atom2,
            nu=ijk,
            # Avoid passing aniso to the function as then the function make it traceless
            # and symmetric, potentially loosing part of the matrix.
            # Due to the TB2J problem: aniso not always traceless.
            parameter=parameter,
            when_present="replace",
        )

        computed_distance = get_distance(spinham.cell, spinham.atoms, atom1, atom2, ijk)
        if abs(computed_distance - distance) > 0.001 and not quiet:
            print(
                "\nComputed distance is a different from the read one:\n"
                + f"  Computed: {computed_distance:.4f}\n  "
                + f"Read: {distance:.4f}\n"
            )

    # Populate spin_values of atoms
    if spin_values is not None:
        if len(spin_values) != spinham.M:
            raise ValueError(
                f"Expected {spinham.M} spin values, got {len(spin_values)}"
            )
        true_spin_values = [0.0 for _ in spinham.atoms.names]

        for i in range(len(spin_values)):
            true_spin_values[spinham.map_to_all[i]] = spin_values[i]
    else:
        true_spin_values = [
            float(np.linalg.norm(atoms["magnetic_moments"][alpha]))
            / atoms["g_factors"][alpha]
            for alpha in range(len(atoms["names"]))
        ]

    spinham.atoms["spins"] = true_spin_values

    # Populate spglib_types of atoms
    if spglib_types is not None:
        if len(spglib_types) != len(spinham.atoms.names):
            raise ValueError(
                f"Expected {len(spinham.atoms.names)} spglib types, got {len(spglib_types)}"
            )
        spinham.atoms["spglib_types"] = [int(_) for _ in spglib_types]

    spinham._reset_internals()

    return spinham


# Populate __all__ with objects defined in this file
__all__ = list(set(dir()) - old_dir)
# Remove all semi-private objects
__all__ = [i for i in __all__ if not i.startswith("_")]
del old_dir
