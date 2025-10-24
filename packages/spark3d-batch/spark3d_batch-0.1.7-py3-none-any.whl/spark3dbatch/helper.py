"""Provide helper functions."""

import math
from typing import Literal

from numpy.typing import NDArray

COLORS = Literal["red", "blue", "green", "magenta", "cyan", "normal"]


def e_acc_to_power(
    e_acc: NDArray,
    freq: float,
    r_q: float,
    l_acc: float,
    e_stored: float = 2.0,
) -> NDArray:
    r"""Convert array of accelerating fields to RMS powers.

    .. important::
       SPARK3D uses peak power, but their definition is non-conventional.
       With single carriers, it corresponds to the classic RMS power, or half
       the classic peak power.

    .. important::
       SPARK3D rescales field when imported from the eigenmode solver. By
       default, the rescaling factor ``stored_energy`` is :math:`2\,\mathrm
       {J/W}`. Under these conditions, the following scaling factor applies:
       +---------------------+----------------------+------------------+
       | RMS power :unit:`W` | Peak power :unit:`W` | Scaling factor   |
       +=====================+======================+==================+
       | :math:`1`           | :math:`2`            | :math:`1`        |
       +---------------------+----------------------+------------------+
       | :math:`2`           | :math:`4`            | :math:`2`        |
       +---------------------+----------------------+------------------+
       | :math:`4`           | :math:`8`            | :math:`\sqrt{8}` |
       +---------------------+----------------------+------------------+

    The power-accelerating voltage conversion comes from the definition of the
    :math:`R / Q`:

    .. math::

       R / Q = \frac{V_\mathrm{acc}^2}{\omega_0 U}

    :math:`V_\mathrm{acc}=E_\mathrm{acc}/L_\mathrm{acc}` is the accelerating
    voltage in :unit:`V`. :math:`U` is the stored energy in :unit:`J`. We use
    the following:

    .. math::

       U = E_\mathrm{stored}P_\mathrm{SPARK3D}

    with :math:`E_\mathrm{stored}` is the stored energy set by user in SPARK3D
    in :math:`J/W`. Remember that powers are RMS, this is why the default is
    :math:`2\,\mathrm{J/W}`.

    :math:`R/Q` can be calculated in CST eigenmode in :unit:`\\Omega`.

    Parameters
    ----------
    e_acc :
        Array of accelerating fields in :unit:`V/m`.
    freq :
        Frequency in :unit:`Hz`.
    r_q :
        Shunt impedance over quality factor ratio in :unit:`\\Omega`.
    l_acc :
        Accelerating length in :unit:`m`.
    e_stored :
        Rescaling factor in SPARK3D, in :unit:`J/W`.

    Returns
    -------
        Array of RMS powers in :unit:`W`.

    """
    omega_0 = 2.0 * math.pi * freq
    u_stored = (l_acc * e_acc) ** 2 / (omega_0 * r_q)
    return e_stored * u_stored


def fmt_array(p_s: NDArray) -> str:
    """Convert numpy array to a string that SPARK3D can understand.

    Parameters
    ----------
    p_s :
        Array of powers.

    Returns
    -------
    str
        List of floats as understood by SPARK3D.

    """
    return ";".join(f"{x:.12g}" for x in p_s)
