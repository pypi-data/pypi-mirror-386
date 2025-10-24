# -*- coding: utf-8 -*-
"""Forcing schemes (:mod:`fluidsim.base.forcing.specific`)
================================================================

Provides:

.. autoclass:: SpecificForcing
   :members:
   :private-members:

.. autoclass:: SpecificForcingPseudoSpectralSimple
   :members:
   :private-members:

.. autoclass:: InScriptForcingPseudoSpectral
   :members:
   :private-members:

.. autoclass:: SpecificForcingPseudoSpectralCoarse
   :members:
   :private-members:

.. autoclass:: InScriptForcingPseudoSpectralCoarse
   :members:
   :private-members:

.. autoclass:: NormalizedForcing
   :members:
   :private-members:

.. autoclass:: Proportional
   :members:
   :private-members:

.. autoclass:: RandomSimplePseudoSpectral
   :members:
   :private-members:

.. autoclass:: TimeCorrelatedRandomPseudoSpectral
   :members:
   :private-members:

"""

from copy import deepcopy
import types
from warnings import warn
from pathlib import Path

import numpy as np

from fluiddyn.util import mpi
from fluiddyn.calcul.easypyfft import fftw_grid_size

from fluidsim.base.setofvariables import SetOfVariables


def _fftw_grid_size(size: np.number) -> int:
    try:
        # The "+ 1" aims to give some gap between the kxmax and
        # the boundary of the oper_coarse.
        result = 2 * fftw_grid_size(int(size) + 1)
    except ImportError:
        warn("To use smaller forcing arrays: pip install pulp")
        i = 0
        while 2 * size > 2**i:
            i += 1
        result = 2**i
    return result


class SpecificForcing:
    """Base class for specific forcing"""

    tag = "specific"

    @classmethod
    def _complete_params_with_default(cls, params):
        params.forcing.available_types.append(cls.tag)

    def __init__(self, sim):
        self.sim = sim
        self.oper = sim.oper
        self.params = sim.params


class SpecificForcingPseudoSpectralSimple(SpecificForcing):
    """Specific forcing for pseudo-spectra solvers"""

    tag = "pseudo_spectral"

    def __init__(self, sim):
        super().__init__(sim)
        self.fstate = sim.state.__class__(sim, oper=self.sim.oper)
        self.forcing_fft = self.fstate.state_spect

    def compute(self):
        """compute the forcing."""
        obj = self.compute_forcing_fft_each_time()
        if isinstance(obj, dict):
            kwargs = obj
        else:
            if self.sim.params.forcing.key_forced is None:
                raise ValueError("params.forcing.key_forced must be initialized.")
            kwargs = {self.sim.params.forcing.key_forced: obj}
        self.fstate.init_statespect_from(**kwargs)

    def compute_forcing_fft_each_time(self):
        raise NotImplementedError


class InScriptForcingPseudoSpectral(SpecificForcingPseudoSpectralSimple):
    """Forcing maker for forcing defined by the user in the launching script

    .. inheritance-diagram:: InScriptForcingPseudoSpectral

    """

    tag = "in_script"

    def __init__(self, sim):
        super().__init__(sim)
        self.is_initialized = False

    def compute_forcing_fft_each_time(self):
        """Compute the coarse forcing in Fourier space"""
        obj = self.compute_forcing_each_time()
        if isinstance(obj, dict):
            kwargs = {key: self.sim.oper.fft(value) for key, value in obj.items()}
        else:
            if self.sim.params.forcing.key_forced is None:
                raise ValueError("params.forcing.key_forced must be initialized.")
            kwargs = {self.sim.params.forcing.key_forced: self.sim.oper.fft(obj)}
        return kwargs

    def compute_forcing_each_time(self):
        """Compute the coarse forcing in real space"""
        return self.sim.oper.create_arrayX(value=0)

    def monkeypatch_compute_forcing_fft_each_time(self, func):
        """Replace the method by a user-defined method"""
        self.compute_forcing_fft_each_time = types.MethodType(func, self)
        self.is_initialized = True

    def monkeypatch_compute_forcing_each_time(self, func):
        """Replace the method by a user-defined method"""
        self.compute_forcing_each_time = types.MethodType(func, self)
        self.is_initialized = True


class SpecificForcingPseudoSpectralCoarse(SpecificForcing):
    """Specific forcing for pseudo-spectra solvers"""

    tag = "pseudo_spectral"
    _key_forced_default = "rot_fft"

    def __init__(self, sim):
        super().__init__(sim)

        params = sim.params

        self.forcing_fft = SetOfVariables(
            like=sim.state.state_spect, info="forcing_fft", value=0.0
        )

        if params.forcing.nkmax_forcing < params.forcing.nkmin_forcing:
            raise ValueError(
                f"params.forcing.nkmax_forcing = {params.forcing.nkmax_forcing} < "
                f"params.forcing.nkmin_forcing = {params.forcing.nkmin_forcing}"
            )

        # oper.deltak is max deltak_i in the different directions
        # i.e. based on the smallest edge of the numerical domain.
        self.kmax_forcing = self.oper.deltak * params.forcing.nkmax_forcing
        self.kmin_forcing = self.oper.deltak * params.forcing.nkmin_forcing

        self.forcing_rate = params.forcing.forcing_rate

        if params.forcing.key_forced is not None:
            self.key_forced = params.forcing.key_forced
        else:
            self.key_forced = self._key_forced_default

        if mpi.rank == 0:
            params_coarse = self._create_params_coarse()

            self.oper_coarse = sim.oper.__class__(params=params_coarse)

            if np.any(
                np.greater(self.oper_coarse.shapeX_seq, sim.oper.shapeX_seq)
            ):
                raise NotImplementedError(
                    "The resolution is too small for the required forcing: "
                    f"any(np.greater({self.oper_coarse.shapeX_seq}, {sim.oper.shapeX_seq}))"
                )

            self.shapeK_loc_coarse = self.oper_coarse.shapeK_loc
            self.COND_NO_F = self._compute_cond_no_forcing()

            self.nb_forced_modes = (
                self.COND_NO_F.size
                - np.array(self.COND_NO_F, dtype=np.int32).sum()
            )
            if not self.nb_forced_modes:
                raise ValueError("0 modes forced.")

            try:
                hasattr(self, "plot_forcing_region")
            except NotImplementedError:
                pass
            else:
                mpi.printby0(
                    "To plot the forcing modes, you can use:\n"
                    "sim.forcing.forcing_maker.plot_forcing_region()"
                )

            self.ind_forcing = (
                np.logical_not(self.COND_NO_F).flatten().nonzero()[0]
            )

            self.fstate_coarse = sim.state.__class__(sim, oper=self.oper_coarse)
        else:
            self.shapeK_loc_coarse = None

        if mpi.nb_proc > 1:
            self.shapeK_loc_coarse = mpi.comm.bcast(
                self.shapeK_loc_coarse, root=0
            )

    def _create_params_coarse(self):
        params_coarse = deepcopy(self.sim.params)
        params_coarse.oper.type_fft = "sequential"
        params_coarse.oper.coef_dealiasing = 1.0
        self._set_params_coarse(params_coarse)
        return params_coarse

    def _set_params_coarse(self, params_coarse):
        params_coarse.oper.nx = _fftw_grid_size(
            self.kmax_forcing / self.sim.oper.deltakx
        )

        try:
            params_coarse.oper.ny
        except AttributeError:
            pass
        else:
            params_coarse.oper.ny = _fftw_grid_size(
                self.kmax_forcing / self.sim.oper.deltaky
            )

        try:
            params_coarse.oper.nz
        except AttributeError:
            pass
        else:
            params_coarse.oper.nz = _fftw_grid_size(
                self.kmax_forcing / self.sim.oper.deltakz
            )

        return params_coarse

    def _compute_cond_no_forcing(self):
        if hasattr(self.oper_coarse, "K"):
            K = self.oper_coarse.K
        else:
            K = np.sqrt(self.oper_coarse.K2)
        COND_NO_F = np.logical_or(K > self.kmax_forcing, K < self.kmin_forcing)

        if len(self.oper.axes) == 2:
            nkyc, nkxc = self.oper_coarse.shapeK_loc
            COND_NO_F[nkyc // 2, :] = True
            COND_NO_F[:, nkxc - 1] = True
        elif len(self.oper.axes) == 3:
            nkzc, nkyc, nkxc = self.oper_coarse.shapeK_loc
            COND_NO_F[nkzc // 2, :, :] = True
            COND_NO_F[:, nkyc // 2, :] = True
            COND_NO_F[:, :, nkxc - 1] = True

        return COND_NO_F

    def put_forcingc_in_forcing(self):
        """Copy data from self.fstate_coarse.state_spect into forcing_fft."""
        if mpi.rank == 0:
            state_spect = self.fstate_coarse.state_spect
            oper_coarse = self.oper_coarse
        else:
            state_spect = None
            oper_coarse = None

        self.oper.put_coarse_array_in_array_fft(
            state_spect, self.forcing_fft, oper_coarse, self.shapeK_loc_coarse
        )

    def verify_injection_rate(self):
        """Verify injection rate."""
        f_fft = self.forcing_fft.get_var(self.key_forced)
        var_fft = self.sim.state.state_spect.get_var(self.key_forced)
        deltat = self.sim.time_stepping.deltat

        P_forcing1 = np.real(f_fft.conj() * var_fft)
        P_forcing2 = abs(f_fft) ** 2
        P_forcing2 = deltat / 2 * self.oper.sum_wavenumbers(P_forcing2)
        P_forcing1 = self.oper.sum_wavenumbers(P_forcing1)
        if mpi.rank == 0:
            print(
                "P_f = {:9.4e} ; P_1 = {:9.4e}; P_2 = {:9.4e}".format(
                    P_forcing1 + P_forcing2, P_forcing1, P_forcing2
                )
            )

    def verify_injection_rate_coarse(self, var_fft=None):
        """Verify injection rate."""
        if var_fft is None:
            var_fft = self.sim.state.state_spect.get_var(self.key_forced)
            var_fft = self.oper.coarse_seq_from_fft_loc(
                var_fft, self.shapeK_loc_coarse
            )

        if mpi.rank == 0:
            f_fft = self.fstate_coarse.get_var(self.key_forced)
            deltat = self.sim.time_stepping.deltat

            P_forcing1 = np.real(f_fft.conj() * var_fft)
            P_forcing2 = abs(f_fft) ** 2
            P_forcing2 = deltat / 2 * self.oper_coarse.sum_wavenumbers(P_forcing2)
            P_forcing1 = self.oper_coarse.sum_wavenumbers(P_forcing1)
            print(
                "P_f = {:9.4e} ; P_1 = {:9.4e}; P_2 = {:9.4e} (coarse)".format(
                    P_forcing1 + P_forcing2, P_forcing1, P_forcing2
                )
            )

    def compute(self):
        """compute a forcing normalize with a 2nd degree eq."""

        obj = self.compute_forcingc_fft_each_time()
        if mpi.rank == 0:
            if isinstance(obj, dict):
                kwargs = obj
            else:
                kwargs = {self.key_forced: obj}
            self.fstate_coarse.init_statespect_from(**kwargs)
            self.oper_coarse.dealiasing_setofvar(self.fstate_coarse.state_spect)

        self.put_forcingc_in_forcing()

    def compute_forcingc_fft_each_time(self):
        raise NotImplementedError


class InScriptForcingPseudoSpectralCoarse(SpecificForcingPseudoSpectralCoarse):
    """Forcing maker for forcing defined by the user in the launching script

    .. inheritance-diagram:: InScriptForcingPseudoSpectralCoarse

    """

    tag = "in_script_coarse"

    def __init__(self, sim):
        super().__init__(sim)
        self.is_initialized = False

    def compute_forcingc_fft_each_time(self):
        """Compute the coarse forcing in Fourier space"""
        forcingc = self.compute_forcingc_each_time()
        if mpi.rank == 0:
            return self.oper_coarse.fft(forcingc)

    def compute_forcingc_each_time(self):
        """Compute the coarse forcing in real space"""
        return self.oper_coarse.create_arrayX(value=0)

    def monkeypatch_compute_forcingc_fft_each_time(self, func):
        """Replace the method by a user-defined method"""
        self.compute_forcingc_fft_each_time = types.MethodType(func, self)
        self.is_initialized = True

    def monkeypatch_compute_forcingc_each_time(self, func):
        """Replace the method by a user-defined method"""
        self.compute_forcingc_each_time = types.MethodType(func, self)
        self.is_initialized = True


class Proportional(SpecificForcingPseudoSpectralCoarse):
    """Specific forcing proportional to the forced variable

    .. inheritance-diagram:: Proportional

    """

    tag = "proportional"

    def compute(self):
        """compute a forcing normalize with a 2nd degree eq."""

        try:
            a_fft = self.sim.state.state_spect.get_var(self.key_forced)
        except ValueError:
            a_fft = self.sim.state.get_var(self.key_forced)

        a_fft = self.oper.coarse_seq_from_fft_loc(a_fft, self.shapeK_loc_coarse)

        if mpi.rank == 0:
            fa_fft = self.forcingc_raw_each_time(a_fft)
            kwargs = {self.key_forced: fa_fft}
            self.fstate_coarse.init_statespect_from(**kwargs)

        self.put_forcingc_in_forcing()

    def forcingc_raw_each_time(self, vc_fft):
        """Modify the array fvc_fft to fixe the injection rate.

        varc : ndarray
            a variable at the coarse resolution.

        To be called only with proc 0.
        """
        fvc_fft = vc_fft.copy()
        fvc_fft[self.COND_NO_F] = 0.0

        Z_fft = abs(fvc_fft) ** 2 / 2.0

        Z = self.oper_coarse.sum_wavenumbers(Z_fft)
        deltat = self.sim.time_stepping.deltat
        alpha = (np.sqrt(1 + deltat * self.forcing_rate / Z) - 1.0) / deltat
        fvc_fft = alpha * fvc_fft

        return fvc_fft


class NormalizedForcing(SpecificForcingPseudoSpectralCoarse):
    """Specific forcing normalized to keep constant injection

    .. inheritance-diagram:: NormalizedForcing

    """

    tag = "normalized"

    @classmethod
    def _complete_params_with_default(cls, params):
        """This static method is used to complete the *params* container."""
        super()._complete_params_with_default(params)
        try:
            params.forcing.normalized
        except AttributeError:
            params.forcing._set_child(
                "normalized",
                {
                    "type": "2nd_degree_eq",
                    "which_root": "minabs",
                    "constant_rate_of": None,
                },
            )

            params.forcing._set_doc("How the forcing is normalized")

    def __init__(self, sim):
        super().__init__(sim)

        params_norm = self.params.forcing.normalized

        if not hasattr(params_norm, "constant_rate_of"):
            params_norm._set_attr("constant_rate_of", None)

        if (
            params_norm.constant_rate_of is not None
            and params_norm.type != "2nd_degree_eq"
        ):
            raise NotImplementedError(
                "params.forcing.normalized.constant_rate_of is implemented "
                'only for params.forcing.normalized.type == "2nd_degree_eq"'
            )

    def compute(self):
        """compute a forcing normalize with a 2nd degree eq."""

        if isinstance(self.key_forced, (list, tuple)):
            keys_forced = self.key_forced
        else:
            keys_forced = [self.key_forced]

        if mpi.rank == 0:
            state_spect = np.zeros_like(self.fstate_coarse.state_spect)
        for key_forced in keys_forced:
            try:
                a_fft = self.sim.state.state_spect.get_var(key_forced)
            except ValueError:
                a_fft = self.sim.state.get_var(key_forced)

            try:
                a_fft = self.oper.coarse_seq_from_fft_loc(
                    a_fft, self.shapeK_loc_coarse
                )
            except IndexError as error:
                raise ValueError(
                    f"rank={self.oper.rank}; {self.shapeK_loc_coarse = }; "
                    f"{self.oper.shapeK_loc = }"
                ) from error

            if mpi.rank == 0:
                fa_fft = self.forcingc_raw_each_time(a_fft)
                self.normalize_forcingc(fa_fft, a_fft, key_forced)

                kwargs = {key_forced: fa_fft}
                self.fstate_coarse.init_statespect_from(**kwargs)

                state_spect += self.fstate_coarse.state_spect

                self.fstate_coarse.state_spect[:] = state_spect

        self.put_forcingc_in_forcing()

    def normalize_forcingc(self, fa_fft, a_fft, key_forced=None):
        """Normalize the coarse forcing"""
        type_normalize = self.params.forcing.normalized.type
        if type_normalize == "2nd_degree_eq":
            self.normalize_forcingc_2nd_degree_eq(fa_fft, a_fft, key_forced)
        elif type_normalize == "particular_k":
            self.normalize_forcingc_part_k(fa_fft, a_fft, key_forced)
        else:
            ValueError(
                "Bad value for parameter forcing.type_normalize:", type_normalize
            )

    def normalize_forcingc_part_k(self, fvc_fft, vc_fft, key_forced=None):
        """Modify the array fvc_fft to fixe the injection rate.

        To be called only with proc 0.

        Parameters
        ----------

        fvc_fft : ndarray
            The non-normalized forcing at the coarse resolution.

        vc_fft : ndarray
            The forced variable at the coarse resolution.

        """
        oper_c = self.oper_coarse

        oper_c.project_fft_on_realX(fvc_fft)

        P_forcing2 = np.real(fvc_fft.conj() * vc_fft)
        P_forcing2 = oper_c.sum_wavenumbers(P_forcing2)

        # we choice randomly a "particular" wavenumber
        # in the forced space
        KX_f = oper_c.KX[~self.COND_NO_F].flatten()
        KY_f = oper_c.KY[~self.COND_NO_F].flatten()
        nb_wn_f = len(KX_f)

        # warning : this is 2d specific!

        ipart = np.random.randint(0, nb_wn_f - 1)
        kx_part = KX_f[ipart]
        ky_part = KY_f[ipart]
        ikx_part = abs(oper_c.kx_loc - kx_part).argmin()
        iky_part = abs(oper_c.ky_loc - ky_part).argmin()

        ik0_part = iky_part
        ik1_part = ikx_part

        P_forcing2_part = np.real(
            fvc_fft[ik0_part, ik1_part].conj() * vc_fft[ik0_part, ik1_part]
            + fvc_fft[ik0_part, ik1_part] * vc_fft[ik0_part, ik1_part].conj()
        )

        if ikx_part == 0:
            P_forcing2_part = P_forcing2_part / 2.0
        P_forcing2_other = P_forcing2 - P_forcing2_part
        fvc_fft[ik0_part, ik1_part] = (
            -P_forcing2_other / vc_fft[ik0_part, ik1_part].real
        )

        if ikx_part != 0:
            fvc_fft[ik0_part, ik1_part] = fvc_fft[ik0_part, ik1_part] / 2.0

        oper_c.project_fft_on_realX(fvc_fft)

        # normalisation to obtain the wanted total forcing rate
        PZ_nonorm = (
            oper_c.sum_wavenumbers(abs(fvc_fft) ** 2)
            * self.sim.time_stepping.deltat
            / 2
        )
        fvc_fft *= np.sqrt(float(self.forcing_rate) / PZ_nonorm)

    def normalize_forcingc_2nd_degree_eq(self, fvc_fft, vc_fft, key_forced=None):
        r"""Modify the array fvc_fft to fixe the injection rate.

        To be called only with proc 0.

        .. |p| mathmacro:: \partial

        .. |var| mathmacro:: \hat\alpha

        .. |fvar| mathmacro:: \hat f

        .. |Sum| mathmacro:: \sum_{\mathbf k}

        We consider that we force a variable |var| with a forcing |fvar|.

        .. math::

            \p_t \var = \fvar

        We want to normalize the forcing |fvar| such that the average over the
        time step of the injection of a quadratic quantity be equal to
        ``self.forcing_rate`` (:math:`P`). Let's consider that the time step
        starts at :math:`t=0` and that the time increment is :math:`\delta t`.

        For simplicity, we first consider that the quadratic quantity is the
        quadratic quantity of the forced variable |var|. Note that this
        function supports other quadratic quantities (for details, read the
        code). The average of the injection rate over the time step is:

        .. math::

            P = \int_0^{\delta t} \frac{dt}{\delta t} \Sum \p_t \frac{|\var^2|}{2}
            = \int_0^{\delta t} \frac{dt}{\delta t} \Sum \var^* \fvar

        We compute an approximation at first order in :math:`\delta t` so that
        we can normalize the forcing such that the value given by this
        approximation is constant for all time steps. For each time step, the
        forcing |fvar| is constant in time. At first order in :math:`\delta t`,
        we have during the time step:

        .. math::

            \var(t) \simeq \var(0) + \fvar t

        and we get

        .. math::

            P \simeq \fvar \int_0^{\delta t} \frac{dt}{\delta t} \Sum (\var(0)^* + \fvar^* t)
            = \Sum \var(0)^* \fvar + \Sum \frac{|\fvar|^2}{2} \delta t

        The final forcing |fvar| is proportional to the "random" forcing :math:`\fvar_r`:

        .. math:: \fvar = R \fvar_r

        We solve a second-order equation to get the value of the coefficient
        :math:`R`:

        .. math::

            \left(\Sum \frac{|\fvar_r|^2}{2} \delta t\right) R^2 + \left(\Sum \var(0)^* \fvar_r\right) R - P = 0

        Parameters
        ----------

        fvc_fft : ndarray
            The non-normalized forcing at the coarse resolution.

        vc_fft : ndarray
            The forced variable at the coarse resolution.
        """
        oper_c = self.oper_coarse
        deltat = self.sim.time_stepping.deltat

        if self.params.forcing.normalized.constant_rate_of is not None:
            if not hasattr(self.sim.forcing, "compute_coef_ab_normalize"):
                raise NotImplementedError
            a, b = self.sim.forcing.compute_coef_ab_normalize(
                self.params.forcing.normalized.constant_rate_of,
                key_forced,
                fvc_fft,
                vc_fft,
                deltat,
            )
        else:
            a = deltat / 2 * oper_c.sum_wavenumbers(abs(fvc_fft) ** 2)
            b = oper_c.sum_wavenumbers((vc_fft.conj() * fvc_fft).real)

        c = -self.forcing_rate

        fvc_fft *= self.coef_normalization_from_abc(a, b, c)

    def coef_normalization_from_abc(self, a, b, c):
        """Compute the roots of a quadratic equation

        Compute the roots given the coefficients ``a``, ``b`` and ``c``.
        Then, select one of the roots based on a criteria and return it.

        Notes
        -----
        Set params.forcing.normalized.which_root to choose the root with:

        - ``minabs`` : minimum absolute value
        - ``first`` : root with positive sign before discriminant
        - ``second`` : root with negative sign before discriminant
        - ``positive`` : positive root

        """
        try:
            alpha1, alpha2 = np.roots([a, b, c])
        except ValueError:
            return 0.0

        which_root = self.params.forcing.normalized.which_root

        if which_root == "minabs":
            if abs(alpha2) < abs(alpha1):
                return alpha2

            else:
                return alpha1

        elif which_root == "first":
            return alpha1

        elif which_root == "second":
            return alpha2

        elif which_root == "positive":
            if alpha2 > 0.0:
                return alpha2

            else:
                return alpha1

        else:
            raise ValueError(
                "Not sure how to choose which root to normalize forcing with."
            )


class RandomSimplePseudoSpectral(NormalizedForcing):
    """Random normalized forcing

    .. inheritance-diagram:: RandomSimplePseudoSpectral
    """

    tag = "random"

    @classmethod
    def _complete_params_with_default(cls, params):
        """This static method is used to complete the *params* container."""
        super()._complete_params_with_default(params)

        try:
            params.forcing.random
        except AttributeError:
            params.forcing._set_child("random", {"only_positive": False})

    def __init__(self, sim):
        super().__init__(sim)

        if self.params.forcing.random.only_positive:
            self._min_val = None
        else:
            self._min_val = -1

    def compute_forcingc_raw(self):
        """Random coarse forcing.

        To be called only with proc 0.
        """
        f_fft = self.oper_coarse.create_arrayK_random(min_val=self._min_val)
        f_fft[self.COND_NO_F] = 0.0
        f_fft = self.oper_coarse.project_fft_on_realX(f_fft)
        return f_fft

    def forcingc_raw_each_time(self, _):
        return self.compute_forcingc_raw()


class TimeCorrelatedRandomPseudoSpectral(RandomSimplePseudoSpectral):
    """Time correlated random normalized forcing

    .. inheritance-diagram:: TimeCorrelatedRandomPseudoSpectral
    """

    tag = "tcrandom"

    @classmethod
    def _complete_params_with_default(cls, params):
        """This static method is used to complete the *params* container."""
        super()._complete_params_with_default(params)

        try:
            params.forcing.tcrandom
        except AttributeError:
            params.forcing._set_child(
                "tcrandom", {"time_correlation": "based_on_forcing_rate"}
            )

    def __init__(self, sim):
        super().__init__(sim)

        if mpi.rank == 0:
            self._forcing_state_file_path = (
                Path(sim.output.path_run) / "_forcing_state.txt"
            )

            if self._forcing_state_file_path.exists():
                with open(self._forcing_state_file_path) as file:
                    lines = file.readlines()

                t_last_change, seed0, seed1 = lines[-1].split()
                self.t_last_change = float(t_last_change)
                self._seed0 = int(seed0)
                self._seed1 = int(seed1)
            else:
                self.t_last_change = self.sim.time_stepping.t
                self._seed0 = np.random.randint(0, 2**31)
                self._seed1 = np.random.randint(0, 2**31)
                self._save_state()

            np.random.seed(self._seed0)
            self.forcing0 = self.compute_forcingc_raw()
            np.random.seed(self._seed1)
            self.forcing1 = self.compute_forcingc_raw()

            pforcing = self.params.forcing
            try:
                time_correlation = pforcing[self.tag].time_correlation
            except AttributeError:
                time_correlation = pforcing.tcrandom.time_correlation

            if time_correlation == "based_on_forcing_rate":
                self.period_change_f0f1 = self.forcing_rate ** (-1.0 / 3)
            else:
                self.period_change_f0f1 = time_correlation

    def forcingc_raw_each_time(self, a_fft):
        """Return a coarse forcing as a linear combination of 2 random arrays

        Compute the new random coarse forcing arrays when necessary.

        """
        tsim = self.sim.time_stepping.t
        if tsim - self.t_last_change >= self.period_change_f0f1:
            self.t_last_change = tsim
            self._seed0 = self._seed1
            self.forcing0 = self.forcing1
            self._seed1 = np.random.randint(0, 2**31)
            np.random.seed(self._seed1)
            self.forcing1 = self.compute_forcingc_raw()
            self._save_state()

        f_fft = self.forcingc_from_f0f1()
        return f_fft

    def _save_state(self):
        if not self.params.output.HAS_TO_SAVE:
            return

        with open(self._forcing_state_file_path, "w") as file:
            file.write(
                "# do not modify by hand\n# t_last_change seed0 seed1\n"
                f"{self.t_last_change} {self._seed0} {self._seed1}\n"
            )

    def forcingc_from_f0f1(self):
        """Return a coarse forcing as a linear combination of 2 random arrays"""
        tsim = self.sim.time_stepping.t
        deltat = self.period_change_f0f1
        omega = np.pi / deltat

        deltaf = self.forcing1 - self.forcing0

        f_fft = (
            self.forcing1
            - 0.5 * (np.cos((tsim - self.t_last_change) * omega) + 1) * deltaf
        )

        return f_fft
