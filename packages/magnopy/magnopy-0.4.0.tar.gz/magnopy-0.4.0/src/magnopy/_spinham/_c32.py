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

from magnopy._data_validation import (
    _spins_ordered,
    _validate_atom_index,
    _validate_unit_cell_index,
    _validated_units,
)
from magnopy._constants._units import _PARAMETER_UNITS


def _get_primary_p32(alpha, beta, nu, parameter=None, S_alpha=None, S_beta=None):
    r"""
    Return the primary version of the parameter.

    For the definition of the primary version see
    :ref:`user-guide_theory-behind_multiple-counting`.

    Parameters
    ----------
    alpha : int
        Index of the first atom.

    beta : int
        Index of the second atom.

    nu : tuple of 3 int
        Unit cell for the second atom.

    parameter : (3, 3, 3) :numpy:`ndarray`, optional
        Full matrix of the parameter.

    S_alpha : float, optional
        Spin value of atom ``alpha``

    S_beta : float, optional
        Spin value of atom ``beta``

    Returns
    -------

    alpha : int
        Index of the first atom.

    beta : int
        Index of the second atom.

    nu : tuple of 3 int
        Unit cell for the second atom.

    parameter : (3, 3, 3) :numpy:`ndarray`
        Full matrix of the parameter. It is returned only if ``parameter is not None``.
    """

    if _spins_ordered(mu1=(0, 0, 0), alpha1=alpha, mu2=nu, alpha2=beta):
        pass
    else:
        i, j, k = nu
        alpha, beta, nu = beta, alpha, (-i, -j, -k)
        if parameter is not None:
            parameter = np.transpose(parameter, (2, 1, 0)) * S_alpha / S_beta

    if parameter is None:
        return alpha, beta, nu
    return alpha, beta, nu, parameter


class _P32_iterator:
    R"""
    Iterator over the (three spins & two sites) parameters of the spin Hamiltonian.
    """

    def __init__(self, spinham) -> None:
        self.container = spinham._32
        self.mc = spinham.convention.multiple_counting
        self.length = len(self.container)
        self.index = 0
        self.spins = spinham.atoms.spins

    def __next__(self):
        if self.index < self.length:
            self.index += 1
            return self.container[self.index - 1]

        elif self.mc and self.index < 2 * self.length:
            self.index += 1
            alpha, beta, (i, j, k), parameter = self.container[
                self.index - 1 - self.length
            ]
            return [
                beta,
                alpha,
                (-i, -j, -k),
                np.transpose(parameter, (2, 1, 0))
                * self.spins[alpha]
                / self.spins[beta],
            ]

        raise StopIteration

    def __len__(self):
        return self.length * (1 + int(self.mc))

    def __iter__(self):
        return self


@property
def _p32(spinham):
    r"""
    Parameters of (three spins & two sites) term of the Hamiltonian.

    .. math::

        \boldsymbol{J}_{3,2}(\boldsymbol{r}_{\nu,\alpha\beta})

    of the term

    .. math::

        C_{3,2}
        \sum_{\substack{\mu, \nu, \alpha, \beta,\\ i, j, u}}
        J^{iju}_{3,2}(\boldsymbol{r}_{\nu,\alpha\beta})
        S_{\mu,\alpha}^i
        S_{\mu,\alpha}^j
        S_{\mu+\nu,\beta}^u

    Returns
    -------

    parameters : iterator
        List of parameters. The list has a form of

        .. code-block:: python

            [[alpha, beta, nu, J], ...]

        where

        ``alpha`` is an index of the atom located in the (0,0,0) unit cell.

        ``beta`` is an index of the atom located in the  nu unit cell.

        ``nu`` defines the unit cell of the second atom (beta). It is a tuple of 3
        integers.

        ``J`` is a (3, 3, 3) :numpy:`ndarray`.

    See Also
    --------

    add_32
    remove_32
    """

    return _P32_iterator(spinham)


# ARGUMENT "replace" DEPRECATED since 0.4.0
# Remove in May of 2026
def _add_32(
    spinham,
    alpha: int,
    beta: int,
    nu: tuple,
    parameter,
    units=None,
    when_present="raise error",
    replace=None,
) -> None:
    r"""
    Adds a (three spins & two sites) parameter to the Hamiltonian.

    Doubles of the bonds are managed automatically (independently of the convention of the
    Hamiltonian).


    Parameters
    ----------
    alpha : int
        Index of an atom from the (0, 0, 0) unit cell.

        ``0 <= alpha < len(spinham.atoms.names)``.

    beta : int
        Index of an atom from the nu unit cell.

        ``0 <= beta < len(spinham.atoms.names)``.

    nu : tuple of 3 int
        Three relative coordinates with respect to the three lattice vectors, that
        specify the unit cell for the second atom.

        .. math::

            \nu
            =
            (x_{\boldsymbol{a}_1}, x_{\boldsymbol{a}_2}, x_{\boldsymbol{a}_3})

    parameter : (3, 3, 3) |array-like|_
        Value of the parameter (:math:`3\times3\times3` matrix). Given in the units of ``units``.

    units : str, optional
        .. versionadded:: 0.3.0

        Units in which the ``parameter`` is given. Parameters have the the units of energy.
        By default assumes :py:attr:`.SpinHamiltonian.units`. For the list of the supported
        units see :ref:`user-guide_usage_units_parameter-units`. If given ``units`` are different from
        :py:attr:`.SpinHamiltonian.units`, then the parameter's value will be converted
        automatically from ``units`` to :py:attr:`.SpinHamiltonian.units`.

    when_present : str, default "raise error"
        .. versionadded:: 0.4.0

        Action to take if a pair of atoms already has a parameter associated with it.
        Case-insensitive. Supported values are:

        - ``"raise error"`` (default): raises an error if a pair of atoms already has a
          parameter associated with it.
        - ``"replace"``: replace existing value of the parameter with the new one.
        - ``"add"``: add the value of the parameter to the existing one.
        - ``"mean"``: replace the value of the parameter with the arithmetic mean of
          existing and new parameters.
        - ``"skip"``: Leave existing parameter unchanged and continue without raising an
          error.

    replace : bool, default False
        Whether to replace the value of the parameter if a pair of atoms already has a
        parameter associated with it.

        .. deprecated:: 0.4.0
            The ``replace`` argument will be removed in May of 2026. Use
            ``modify="replace"`` instead.


    Raises
    ------

    ValueError
        If a pair of atoms already has a parameter associated with it and ``when_present="raise error"``.

    ValueError
        If ``when_present`` has an unsupported value.

    See Also
    --------

    p32
    remove_32

    Notes
    -----

    If ``spinham.convention.multiple_counting`` is ``True``, then this function adds both
    the bond and its double to the Hamiltonian. It will cause an ``ValueError`` to
    add the double of the bond after the bond is added.

    If ``spinham.convention.multiple_counting`` is ``False``, then only the primary
    version of the bond is added to the Hamiltonian.

    For the definition of the primary version see
    :ref:`user-guide_theory-behind_multiple-counting`.
    """

    if replace is not None:
        import warnings

        warnings.warn(
            'The "replace" argument is deprecated since version 0.4.0 and will be removed in May of 2026. Use when_present="replace" instead.',
            DeprecationWarning,
            stacklevel=2,
        )
        if replace:
            when_present = "replace"
        else:
            when_present = "raise error"

    _validate_atom_index(index=alpha, atoms=spinham.atoms)
    _validate_atom_index(index=beta, atoms=spinham.atoms)
    _validate_unit_cell_index(ijk=nu)
    spinham._reset_internals()

    parameter = np.array(parameter)

    if units is not None:
        units = _validated_units(units=units, supported_units=_PARAMETER_UNITS)
        parameter = (
            parameter * _PARAMETER_UNITS[units] / _PARAMETER_UNITS[spinham._units]
        )

    alpha, beta, nu, parameter = _get_primary_p32(
        alpha=alpha,
        beta=beta,
        nu=nu,
        parameter=parameter,
        S_alpha=spinham.atoms.spins[alpha],
        S_beta=spinham.atoms.spins[beta],
    )

    # TODO BINARY SEARCH
    # Try to find the place for the new one inside the list
    index = 0
    while index < len(spinham._32):
        # If already present in the model
        if spinham._32[index][:3] == [alpha, beta, nu]:
            # Either replace
            if when_present.lower() == "replace":
                spinham._32[index][3] = parameter
            # Or add
            elif when_present.lower() == "add":
                spinham._32[index][3] = spinham._32[index][3] + parameter
            # Or replace with mean value
            elif when_present.lower() == "mean":
                spinham._32[index][3] = (spinham._32[index][3] + parameter) / 2.0
            # Or do nothing
            elif when_present.lower() == "skip":
                pass
            # Or raise an error
            elif when_present.lower() == "raise error":
                raise ValueError(
                    f"(Three spins & two sites) parameter is already set for the pair of atoms {alpha} and {beta} ({nu}). Or for their double bond."
                )
            else:
                raise ValueError(
                    f'Unsupported value of when_present: "{when_present}". Supported values are: "raise error", "replace", "add", "mean", "skip".'
                )

            return

        # If it should be inserted before current element
        if spinham._32[index][:3] > [alpha, beta, nu]:
            spinham._32.insert(index, [alpha, beta, nu, parameter])
            return

        index += 1

    # If it should be inserted at the end or at the beginning of the list
    spinham._32.append([alpha, beta, nu, parameter])


def _remove_32(spinham, alpha: int, beta: int, nu: tuple) -> None:
    r"""
    Removes a (three spins & two sites) parameter from the Hamiltonian.

    Doubles of the bonds are managed automatically (independently of the convention of the
    Hamiltonian).

    Parameters
    ----------

    alpha : int
        Index of an atom from the (0, 0, 0) unit cell.

        ``0 <= alpha < len(spinham.atoms.names)``.

    beta : int
        Index of an atom from the nu unit cell.

        ``0 <= beta < len(spinham.atoms.names)``.

    nu : tuple of 3 int
        Three relative coordinates with respect to the three lattice vectors, that
        specify the unit cell for the second atom.

        .. math::

            \nu
            =
            (x_{\boldsymbol{a}_1}, x_{\boldsymbol{a}_2}, x_{\boldsymbol{a}_3})

    See Also
    --------

    p32
    add_32

    Notes
    -----

    If ``spinham.convention.multiple_counting`` is ``True``, then this function removes
    all versions of the bond from the Hamiltonian.

    If ``spinham.convention.multiple_counting`` is ``False``, then this function removes
    the primary version of the given bond.

    For the definition of the primary version see
    :ref:`user-guide_theory-behind_multiple-counting`.

    For instance, if ``(1, 0, (0, 0, 0))`` is given, then this function attempts to
    remove either both ``(1, 0, (0, 0, 0))`` and ``(0, 1, (0, 0, 0))`` if
    ``spinham.convention.multiple_counting == True`` or the primary version
    ``(0, 1, (0, 0, 0))`` if ``spinham.convention.multiple_counting == False``.
    """

    _validate_atom_index(index=alpha, atoms=spinham.atoms)
    _validate_atom_index(index=beta, atoms=spinham.atoms)
    _validate_unit_cell_index(ijk=nu)

    alpha, beta, nu = _get_primary_p32(alpha=alpha, beta=beta, nu=nu)

    # TD-BINARY_SEARCH

    for index in range(len(spinham._32)):
        # As the list is sorted, there is no point in resuming the search
        # when a larger element is found
        if spinham._32[index][:3] > [alpha, beta, nu]:
            return

        if spinham._32[index][:3] == [alpha, beta, nu]:
            del spinham._32[index]
            spinham._reset_internals()
            return
