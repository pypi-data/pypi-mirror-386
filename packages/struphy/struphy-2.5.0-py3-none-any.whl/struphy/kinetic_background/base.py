"Base classes for kinetic backgrounds."

import copy
from abc import ABCMeta, abstractmethod

from struphy.fields_background.base import FluidEquilibrium
from struphy.fields_background.equils import set_defaults
from struphy.initial import perturbations
from struphy.initial.utilities import Noise
from struphy.kinetic_background import moment_functions
from struphy.utils.arrays import xp as np


class KineticBackground(metaclass=ABCMeta):
    r"""Base class for kinetic background distributions
    defined on :math:`[0, 1]^3 \times \mathbb R^n, n \geq 1,`
    with logical position coordinates :math:`\boldsymbol{\eta} \in [0, 1]^3`.

    Explicit expressions for the following number density :math:`n`
    and mean velocity :math:`\mathbf u` must be implemented:

    .. math::

        n &= \int f \,\mathrm{d} \mathbf v

        \mathbf u &= \frac 1n \int \mathbf v f \,\mathrm{d} \mathbf v\,.
    """

    @property
    @abstractmethod
    def coords(self):
        """Coordinates of the distribution."""
        pass

    @property
    @abstractmethod
    def vdim(self):
        """Dimension of the velocity space (vdim = n)."""
        pass

    @property
    @abstractmethod
    def is_polar(self):
        """List of booleans of length vdim. True for a velocity coordinate that is a radial polar coordinate (v_perp)."""
        pass

    @property
    @abstractmethod
    def volume_form(self):
        """Boolean. True if the background is represented as a volume form (thus including the velocity Jacobian)."""
        pass

    @abstractmethod
    def velocity_jacobian_det(self, eta1, eta2, eta3, *v):
        """Jacobian determinant of the velocity coordinate transformation."""
        pass

    @abstractmethod
    def n(self, *etas):
        """Number density (0-form).

        Parameters
        ----------
        etas : numpy.arrays
            Evaluation points. All arrays must be of same shape (can be 1d for flat evaluation).

        Returns
        -------
        A numpy.array with the density evaluated at evaluation points (same shape as etas).
        """
        pass

    @abstractmethod
    def u(self, *etas):
        """Mean velocities (Cartesian components evaluated at x = F(eta)).

        Parameters
        ----------
        etas : numpy.arrays
            Evaluation points. All arrays must be of same shape (can be 1d for flat evaluation).

        Returns
        -------
        A list[float] (background values) or a list[numpy.array] of the evaluated velocities.
        """
        pass

    @abstractmethod
    def __call__(self, *args):
        """Evaluates the background distribution function f0(etas, v1, ..., vn).

        There are two use-cases for this function in the code:

        1. Evaluating for particles ("flat evaluation", inputs are all 1D of length N_p)
        2. Evaluating the function on a meshgrid (in phase space).

        Hence all arguments must always have

        1. the same shape
        2. either ndim = 1 or ndim = 3 + vdim.

        Parameters
        ----------
        *args : array_like
            Position-velocity arguments in the order eta1, eta2, eta3, v1, ..., vn.

        Returns
        -------
        f0 : np.ndarray
            The evaluated background.
        """
        pass

    def __add__(self, other_f0):
        return SumKineticBackground(self, other_f0)

    def __mul__(self, a):
        return ScalarMultiplyKineticBackground(self, a)

    def __rmul__(self, a):
        return ScalarMultiplyKineticBackground(self, a)

    def __div__(self, a):
        assert isinstance(a, float) or isinstance(a, int) or isinstance(a, np.int64)
        assert a != 0, "Cannot divide by zero!"
        return ScalarMultiplyKineticBackground(self, 1 / a)

    def __rdiv__(self, a):
        assert isinstance(a, float) or isinstance(a, int) or isinstance(a, np.int64)
        assert a != 0, "Cannot divide by zero!"
        return ScalarMultiplyKineticBackground(self, 1 / a)

    def __sub__(self, other_f0):
        return SumKineticBackground(self, ScalarMultiplyKineticBackground(other_f0, -1.0))


class SumKineticBackground(KineticBackground):
    def __init__(self, f1, f2):
        assert isinstance(f1, KineticBackground)
        assert isinstance(f2, KineticBackground)
        assert f1.vdim == f2.vdim
        assert f1.is_polar == f2.is_polar
        assert f1.volume_form == f2.volume_form

        self._f1 = f1
        self._f2 = f2

    @property
    def coords(self):
        """Coordinates of the distribution."""
        return self._f1.coords

    @property
    def vdim(self):
        """Dimension of the velocity space (vdim = n)."""
        return self._f1.vdim

    @property
    def is_polar(self):
        """List of booleans. True if the velocity coordinates are polar coordinates."""
        return self._f1.is_polar

    @property
    def volume_form(self):
        """Boolean. True if the background is represented as a volume form (thus including the velocity Jacobian)."""
        return self._f1.volume_form

    def velocity_jacobian_det(self, eta1, eta2, eta3, *v):
        """Jacobian determinant of the velocity coordinate transformation."""
        return self._f1.velocity_jacobian_det(eta1, eta2, eta3, *v)

    def n(self, *etas):
        """Number density (0-form).

        Parameters
        ----------
        etas : numpy.arrays
            Evaluation points. All arrays must be of same shape (can be 1d for flat evaluation).

        Returns
        -------
        A numpy.array with the density evaluated at evaluation points (same shape as etas).
        """
        return self._f1.n(*etas) + self._f2.n(*etas)

    def u(self, *etas):
        """Mean velocities (Cartesian components evaluated at x = F(eta)).

        Parameters
        ----------
        etas : numpy.arrays
            Evaluation points. All arrays must be of same shape (can be 1d for flat evaluation).

        Returns
        -------
        A list[float] (background values) or a list[numpy.array] of the evaluated velocities.
        """

        n1 = self._f1.n(*etas)
        n2 = self._f2.n(*etas)

        return [(n1 * u1 + n2 * u2) / (n1 + n2) for u1, u2 in zip(self._f1.u(*etas), self._f2.u(*etas))]

    def __call__(self, *args):
        """Evaluates the background distribution function f0(etas, v1, ..., vn).

        There are two use-cases for this function in the code:

        1. Evaluating for particles ("flat evaluation", inputs are all 1D of length N_p)
        2. Evaluating the function on a meshgrid (in phase space).

        Hence all arguments must always have

        1. the same shape
        2. either ndim = 1 or ndim = 3 + vdim.

        Parameters
        ----------
        *args : array_like
            Position-velocity arguments in the order eta1, eta2, eta3, v1, ..., vn.

        Returns
        -------
        f0 : np.ndarray
            The evaluated background.
        """
        return self._f1(*args) + self._f2(*args)


class ScalarMultiplyKineticBackground(KineticBackground):
    def __init__(self, f0, a):
        assert isinstance(f0, KineticBackground)
        assert isinstance(a, float) or isinstance(a, int) or isinstance(a, np.int64)

        self._f = f0
        self._a = a

    @property
    def coords(self):
        """Coordinates of the distribution."""
        return self._f.coords

    @property
    def vdim(self):
        """Dimension of the velocity space (vdim = n)."""
        return self._f.vdim

    @property
    def is_polar(self):
        """List of booleans. True if the velocity coordinates are polar coordinates."""
        return self._f.is_polar

    @property
    def volume_form(self):
        """Boolean. True if the background is represented as a volume form (thus including the velocity Jacobian)."""
        return self._f.volume_form

    def velocity_jacobian_det(self, eta1, eta2, eta3, *v):
        """Jacobian determinant of the velocity coordinate transformation."""
        return self._f.velocity_jacobian_det(eta1, eta2, eta3, *v)

    def n(self, *etas):
        """Number density (0-form).

        Parameters
        ----------
        etas : numpy.arrays
            Evaluation points. All arrays must be of same shape (can be 1d for flat evaluation).

        Returns
        -------
        A numpy.array with the density evaluated at evaluation points (same shape as etas).
        """
        return self._a * self._f.n(*etas)

    def u(self, *etas):
        """Mean velocities (Cartesian components evaluated at x = F(eta)).

        Parameters
        ----------
        etas : numpy.arrays
            Evaluation points. All arrays must be of same shape (can be 1d for flat evaluation).

        Returns
        -------
        A list[float] (background values) or a list[numpy.array] of the evaluated velocities.
        """
        return self._f.u(*etas)

    def __call__(self, *args):
        """Evaluates the background distribution function f0(etas, v1, ..., vn).

        There are two use-cases for this function in the code:

        1. Evaluating for particles ("flat evaluation", inputs are all 1D of length N_p)
        2. Evaluating the function on a meshgrid (in phase space).

        Hence all arguments must always have

        1. the same shape
        2. either ndim = 1 or ndim = 3 + vdim.

        Parameters
        ----------
        *args : array_like
            Position-velocity arguments in the order eta1, eta2, eta3, v1, ..., vn.

        Returns
        -------
        f0 : np.ndarray
            The evaluated background.
        """
        return self._a * self._f(*args)


class Maxwellian(KineticBackground):
    r"""Base class for a Maxwellian distribution function.
    It is defined on :math:`[0, 1]^3 \times \mathbb R^n, n \geq 1,`
    with logical position coordinates :math:`\boldsymbol{\eta} \in [0, 1]^3`:

    .. math::

        f(\boldsymbol{\eta}, v_1,\ldots,v_n) = n(\boldsymbol{\eta}) \prod_{i=1}^n \frac{1}{\sqrt{2\pi}\,v_{\mathrm{th},i}(\boldsymbol{\eta})}
        \exp\left[-\frac{(v_i-u_i(\boldsymbol{\eta}))^2}{2\,v_{\mathrm{th},i}(\boldsymbol{\eta})^2}\right],

    defined by its velocity moments: the density :math:`n(\boldsymbol{\eta})`,
    the mean-velocities :math:`u_i(\boldsymbol{\eta})`,
    and the thermal velocities :math:`v_{\mathrm{th},i}(\boldsymbol{\eta})`.
    """

    def __init__(
        self,
        maxw_params: dict = None,
        pert_params: dict = None,
        equil: FluidEquilibrium = None,
    ):
        # Set background parameters
        if maxw_params is None:
            maxw_params = {}
        assert isinstance(maxw_params, dict)
        self._maxw_params = set_defaults(
            maxw_params,
            self.default_maxw_params(),
        )

        # check if fluid background is needed
        for key, val in self.maxw_params.items():
            if val == "fluid_background":
                assert equil is not None

        # parameters for perturbation
        if pert_params is None:
            pert_params = {}
        assert isinstance(pert_params, dict)
        self._pert_params = pert_params

        # Fluid equilibrium
        self._equil = equil

    @classmethod
    def default_maxw_params(cls):
        """Default parameters dictionary defining constant moments of the Maxwellian."""
        pass

    @abstractmethod
    def vth(self, *etas):
        """Thermal velocities (0-forms).

        Parameters
        ----------
        etas : numpy.arrays
            Evaluation points. All arrays must be of same shape (can be 1d for flat evaluation).

        Returns
        -------
        A list[float] (background values) or a list[numpy.array] of the evaluated thermal velocities.
        """
        pass

    @property
    def maxw_params(self):
        """Parameters dictionary defining constant moments of the Maxwellian."""
        return self._maxw_params

    @property
    def pert_params(self):
        """Parameters dictionary defining the perturbations."""
        return self._pert_params

    @property
    def equil(self):
        """One of :mod:`~struphy.fields_background.equils`
        in case that moments are to be set in that way, None otherwise.
        """
        return self._equil

    @classmethod
    def gaussian(self, v, u=0.0, vth=1.0, polar=False, volume_form=False):
        """1-dim. normal distribution, to which array-valued mean- and thermal velocities can be passed.

        Parameters
        ----------
        v : float | array-like
            Velocity coordinate(s).

        u : float | array-like
            Mean velocity evaluated at position array.

        vth : float | array-like
            Thermal velocity evaluated at position array, same shape as u.

        polar : bool
            True if the velocity coordinate is the radial one of polar coordinates (v >= 0).

        volume_form : bool
            If True, the polar Gaussian is multiplied by the polar velocity Jacobian |v|.

        Returns
        -------
        An array of size(v).
        """

        if isinstance(v, np.ndarray) and isinstance(u, np.ndarray):
            assert v.shape == u.shape, f"{v.shape = } but {u.shape = }"

        if not polar:
            out = 1.0 / vth * 1.0 / np.sqrt(2.0 * np.pi) * np.exp(-((v - u) ** 2) / (2.0 * vth**2))
        else:
            assert np.all(v >= 0.0)
            out = 1.0 / vth**2 * np.exp(-((v - u) ** 2) / (2.0 * vth**2))
            if volume_form:
                out *= v

        return out

    def __call__(self, *args):
        """Evaluates the Maxwellian distribution function M(etas, v1, ..., vn).

        There are two use-cases for this function in the code:

        1. Evaluating for particles ("flat evaluation", inputs are all 1D of length N_p)
        2. Evaluating the function on a meshgrid (in phase space).

        Hence all arguments must always have

        1. the same shape
        2. either ndim = 1 or ndim = 3 + vdim.

        Parameters
        ----------
        *args : array_like
            Position-velocity arguments in the order eta1, eta2, eta3, v1, ..., vn.

        Returns
        -------
        f : np.ndarray
            The evaluated Maxwellian.
        """

        # Check that all args have the same shape
        shape0 = np.shape(args[0])
        for i, arg in enumerate(args):
            assert np.shape(arg) == shape0, f"Argument {i} has {np.shape(arg) = }, but must be {shape0 = }."
            assert np.ndim(arg) == 1 or np.ndim(arg) == 3 + self.vdim, (
                f"{np.ndim(arg) = } not allowed for Maxwellian evaluation."
            )  # flat or meshgrid evaluation

        # Get result evaluated at eta's
        res = self.n(*args[: -self.vdim])
        us = self.u(*args[: -self.vdim])
        vths = self.vth(*args[: -self.vdim])

        # take care of correct broadcasting, assuming args come from phase space meshgrid
        if np.ndim(args[0]) > 3:
            # move eta axes to the back
            arg_t = np.moveaxis(args[0], 0, -1)
            arg_t = np.moveaxis(arg_t, 0, -1)
            arg_t = np.moveaxis(arg_t, 0, -1)

            # broadcast
            res_broad = res + 0.0 * arg_t

            # move eta axes to the front
            res = np.moveaxis(res_broad, -1, 0)
            res = np.moveaxis(res, -1, 0)
            res = np.moveaxis(res, -1, 0)

        # Multiply result with gaussian in v's
        for i, v in enumerate(args[-self.vdim :]):
            # correct broadcasting
            if np.ndim(args[0]) > 3:
                u_broad = us[i] + 0.0 * arg_t
                u = np.moveaxis(u_broad, -1, 0)
                u = np.moveaxis(u, -1, 0)
                u = np.moveaxis(u, -1, 0)

                vth_broad = vths[i] + 0.0 * arg_t
                vth = np.moveaxis(vth_broad, -1, 0)
                vth = np.moveaxis(vth, -1, 0)
                vth = np.moveaxis(vth, -1, 0)
            else:
                u = us[i]
                vth = vths[i]

            res *= self.gaussian(v, u=u, vth=vth, polar=self.is_polar[i], volume_form=self.volume_form)

        return res

    def _evaluate_moment(self, eta1, eta2, eta3, *, name="n"):
        """Scalar moment evaluation as background + perturbation.

        Parameters
        ----------
        eta1, eta2, eta3 : numpy.arrays
            Evaluation points. All arrays must be of same shape (can be 1d for flat evaluation).

        name : str
            Which moment to evaluate (see varaible "dct" below).

        Returns
        -------
        A float (background value) or a numpy.array of the evaluated scalar moment.
        """

        # collect arguments
        assert isinstance(eta1, np.ndarray)
        assert isinstance(eta2, np.ndarray)
        assert isinstance(eta3, np.ndarray)
        assert eta1.shape == eta2.shape == eta3.shape

        # flat evaluation for markers
        if eta1.ndim == 1:
            etas = [
                np.concatenate(
                    (eta1[:, None], eta2[:, None], eta3[:, None]),
                    axis=1,
                ),
            ]
        # assuming that input comes from meshgrid.
        elif eta1.ndim == 4:
            etas = (
                eta1[:, :, :, 0],
                eta2[:, :, :, 0],
                eta3[:, :, :, 0],
            )
        elif eta1.ndim == 5:
            etas = (
                eta1[:, :, :, 0, 0],
                eta2[:, :, :, 0, 0],
                eta3[:, :, :, 0, 0],
            )
        elif eta1.ndim == 6:
            etas = (
                eta1[:, :, :, 0, 0, 0],
                eta2[:, :, :, 0, 0, 0],
                eta3[:, :, :, 0, 0, 0],
            )
        else:
            etas = (eta1, eta2, eta3)

        # initialize output
        if eta1.ndim == 1:
            out = 0.0 * eta1
        else:
            out = 0.0 * etas[0]

        # correspondence name -> equilibrium attribute
        dct = {
            "n": "n0",
            "u1": "u_cart_1",
            "u2": "u_cart_2",
            "u3": "u_cart_3",
            "vth1": "vth0",
            "vth2": "vth0",
            "vth3": "vth0",
            "u_para": "u_para0",
            "u_perp": None,
            "vth_para": "vth0",
            "vth_perp": "vth0",
        }

        # fluid background
        if self.maxw_params[name] == "fluid_background":
            if dct[name] is not None:
                out += getattr(self.equil, dct[name])(*etas)
                if name in ("n") or "vth" in name:
                    assert np.all(out > 0.0), f"{name} must be positive!"
            else:
                print(f'Moment evaluation with "fluid_background" not implemented for {name}.')

        # when using moment functions, see test https://gitlab.mpcdf.mpg.de/struphy/struphy/-/blob/devel/src/struphy/kinetic_background/tests/test_maxwellians.py?ref_type=heads#L1760
        elif isinstance(self.maxw_params[name], dict):
            mom_funcs = copy.deepcopy(self.maxw_params[name])
            for typ, params in mom_funcs.items():
                assert params["given_in_basis"] == "0", "Moment functions must be passed as 0-forms to Maxwellians."
                params.pop("given_in_basis")
                nfun = getattr(moment_functions, typ)(**params)
                if eta1.ndim == 1:
                    out += nfun(eta1, eta2, eta3)
                else:
                    out += nfun(*etas)

        # constant background
        else:
            if eta1.ndim == 1:
                out += self.maxw_params[name]
            else:
                out += self.maxw_params[name]

        # add possible perturbations
        if name in self.pert_params:
            pp_copy = copy.deepcopy(self.pert_params)
            for pert, params in pp_copy[name].items():
                if pert == "Noise":
                    noise = Noise(**params)
                    if eta1.ndim == 1:
                        out += noise(eta1, eta2, eta3)
                    else:
                        out += noise(*etas)
                else:
                    assert params["given_in_basis"] == "0", (
                        "Moment perturbations must be passed as 0-forms to Maxwellians."
                    )
                    params.pop("given_in_basis")

                    perturbation = getattr(perturbations, pert)(
                        **params,
                    )

                    if eta1.ndim == 1:
                        out += perturbation(eta1, eta2, eta3)
                    else:
                        out += perturbation(*etas)

        return out


class CanonicalMaxwellian(metaclass=ABCMeta):
    r"""Base class for a canonical Maxwellian distribution function.
    It is defined by three constants of motion in the axissymmetric toroidal system:

    - Shifted canonical toroidal momentum

    .. math::

        \psi_c = \psi + \frac{m_s F}{q_s B}v_\parallel - \text{sign}(v_\parallel)\sqrt{2(\epsilon - \mu B)}\frac{m_sF}{q_sB} \mathcal{H}(\epsilon - \mu B),

    - Energy

    .. math::

        \epsilon = \frac{1}{2}m_sv_\parallel² + \mu B,

    - Magnetic moment

    .. math::

        \mu = \frac{m_s v_\perp²}{2B},

    where :math:`\psi` is the poloidal magnetic flux function, :math:`F=F(\psi)` is the poloidal current function and :math:`\mathcal{H}` is the Heaviside function.

    With the three constants of motion, a canonical Maxwellian distribution function is defined as

    .. math::

        F(\psi_c, \epsilon, \mu) = \frac{n(\psi_c)}{(2\pi)^{3/2}v_\text{th}³(\psi_c)} \text{exp}\left[ - \frac{\epsilon}{v_\text{th}²(\psi_c)}\right].

    """

    @property
    @abstractmethod
    def coords(self):
        """Coordinates of the distribution."""
        pass

    @abstractmethod
    def velocity_jacobian_det(self, eta1, eta2, eta3, *v):
        """Jacobian determinant of the velocity coordinate transformation."""
        pass

    @abstractmethod
    def n(self, psic):
        """Number density (0-form).

        Parameters
        ----------
        psic : numpy.arrays
            Shifted canonical toroidal momentum.

        Returns
        -------
        A numpy.array with the density evaluated at evaluation points (same shape as etas).
        """
        pass

    @abstractmethod
    def vth(self, psic):
        """Thermal velocities (0-forms).

        Parameters
        ----------
        psic : numpy.arrays
            Shifted canonical toroidal momentum.

        Returns
        -------
        A numpy.array with the thermal velocity evaluated at evaluation points (one dimension more than etas).
        The additional dimension is in the first index.
        """
        pass

    def gaussian(self, e, vth=1.0):
        """3-dim. normal distribution, to which array-valued thermal velocities can be passed.

        Parameters
        ----------
        e : float | array-like
            Energy.

        vth : float | array-like
            Thermal velocity evaluated at psic.

        Returns
        -------
        An array of size(e).
        """

        if isinstance(vth, np.ndarray):
            assert e.shape == vth.shape, f"{e.shape = } but {vth.shape = }"

        return 2.0 * np.sqrt(e / np.pi) / vth**3 * np.exp(-e / vth**2)

    def __call__(self, *args):
        """Evaluates the canonical Maxwellian distribution function.

        There are two use-cases for this function in the code:

        1. Evaluating for particles ("flat evaluation", inputs are all 1D of length N_p)
        2. Evaluating the function on a meshgrid (in phase space).

        Hence all arguments must always have

        1. the same shape
        2. either ndim = 1 or ndim = 3.

        Parameters
        ----------
        *args : array_like
            Position-velocity arguments in the order energy, magnetic moment, canonical toroidal momentum.

        Returns
        -------
        f : np.ndarray
            The evaluated Maxwellian.
        """

        # Check that all args have the same shape
        shape0 = np.shape(args[0])
        for i, arg in enumerate(args):
            assert np.shape(arg) == shape0, f"Argument {i} has {np.shape(arg) = }, but must be {shape0 = }."
            assert np.ndim(arg) == 1 or np.ndim(arg) == 3, (
                f"{np.ndim(arg) = } not allowed for canonical Maxwellian evaluation."
            )  # flat or meshgrid evaluation

        # Get result evaluated with each particles' psic
        res = self.n(args[2])
        vths = self.vth(args[2])

        # take care of correct broadcasting, assuming args come from phase space meshgrid
        if np.ndim(args[0]) == 3:
            # move eta axes to the back
            arg_t = np.moveaxis(args[0], 0, -1)
            arg_t = np.moveaxis(arg_t, 0, -1)
            arg_t = np.moveaxis(arg_t, 0, -1)

            # broadcast
            res_broad = res + 0.0 * arg_t

            # move eta axes to the front
            res = np.moveaxis(res_broad, -1, 0)
            res = np.moveaxis(res, -1, 0)
            res = np.moveaxis(res, -1, 0)

        # Multiply result with gaussian in energy
        if np.ndim(args[0]) == 3:
            vth_broad = vths + 0.0 * arg_t
            vth = np.moveaxis(vth_broad, -1, 0)
            vth = np.moveaxis(vth, -1, 0)
            vth = np.moveaxis(vth, -1, 0)
        else:
            vth = vths

        res *= self.gaussian(args[0], vth=vth)

        return res
