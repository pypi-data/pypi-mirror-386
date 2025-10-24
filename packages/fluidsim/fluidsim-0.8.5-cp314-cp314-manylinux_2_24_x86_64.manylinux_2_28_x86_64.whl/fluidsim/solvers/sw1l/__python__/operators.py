import numpy as np


def _qapamfft_from_uxuyetafft(ux_fft, uy_fft, eta_fft, n0, n1, KX, KY, K2, Kappa_over_ic, f, c2, rank):
    """Calculate normal modes from primitive variables."""
    freq_Corio = f
    f_over_c2 = freq_Corio / c2
    q_fft = np.empty([n0, n1], dtype=np.complex128)
    ap_fft = np.empty([n0, n1], dtype=np.complex128)
    am_fft = np.empty([n0, n1], dtype=np.complex128)
    if freq_Corio != 0:
        for i0 in range(n0):
            for i1 in range(n1):
                if i0 == 0 and i1 == 0 and (rank == 0):
                    q_fft[i0, i1] = 0
                    ap_fft[i0, i1] = ux_fft[0, 0] + 1j * uy_fft[0, 0]
                    am_fft[i0, i1] = ux_fft[0, 0] - 1j * uy_fft[0, 0]
                else:
                    rot_fft = 1j * \
                        (KX[i0, i1] * uy_fft[i0, i1] -
                         KY[i0, i1] * ux_fft[i0, i1])
                    q_fft[i0, i1] = rot_fft - freq_Corio * eta_fft[i0, i1]
                    a_over2_fft = 0.5 * \
                        (K2[i0, i1] * eta_fft[i0, i1] + f_over_c2 * rot_fft)
                    Deltaa_over2_fft = 0.5j * \
                        Kappa_over_ic[i0, i1] * \
                        (KX[i0, i1] * ux_fft[i0, i1] +
                         KY[i0, i1] * uy_fft[i0, i1])
                    ap_fft[i0, i1] = a_over2_fft + Deltaa_over2_fft
                    am_fft[i0, i1] = a_over2_fft - Deltaa_over2_fft
    else:
        for i0 in range(n0):
            for i1 in range(n1):
                if i0 == 0 and i1 == 0 and (rank == 0):
                    q_fft[i0, i1] = 0
                    ap_fft[i0, i1] = ux_fft[0, 0] + 1j * uy_fft[0, 0]
                    am_fft[i0, i1] = ux_fft[0, 0] - 1j * uy_fft[0, 0]
                else:
                    q_fft[i0, i1] = 1j * \
                        (KX[i0, i1] * uy_fft[i0, i1] -
                         KY[i0, i1] * ux_fft[i0, i1])
                    a_over2_fft = 0.5 * K2[i0, i1] * eta_fft[i0, i1]
                    Deltaa_over2_fft = 0.5j * \
                        Kappa_over_ic[i0, i1] * \
                        (KX[i0, i1] * ux_fft[i0, i1] +
                         KY[i0, i1] * uy_fft[i0, i1])
                    ap_fft[i0, i1] = a_over2_fft + Deltaa_over2_fft
                    am_fft[i0, i1] = a_over2_fft - Deltaa_over2_fft
    return (q_fft, ap_fft, am_fft)


def __for_method__OperatorsPseudoSpectralSW1L__divfft_from_apamfft(self_Kappa_over_ic, self_nK0_loc, self_nK1_loc, self_rank, ap_fft, am_fft):
    """Return div from the eigen modes ap and am."""
    n0 = self_nK0_loc
    n1 = self_nK1_loc
    Kappa_over_ic = self_Kappa_over_ic
    rank = self_rank
    Delta_a_fft = ap_fft - am_fft
    d_fft = np .empty([n0, n1], dtype=np .complex128)
    for i0 in range(n0):
        for i1 in range(n1):
            if i0 == 0 and i1 == 0 and (rank == 0):
                d_fft[i0, i1] = 0.0
            else:
                d_fft[i0, i1] = Delta_a_fft[i0, i1]/Kappa_over_ic[i0, i1]
    return d_fft


def __code_new_method__OperatorsPseudoSpectralSW1L__divfft_from_apamfft(): return """

def new_method(self, ap_fft, am_fft):
    return backend_func(self.Kappa_over_ic, self.nK0_loc, self.nK1_loc, self.rank, ap_fft, am_fft)

"""


def __transonic__(): return "0.8.0"
