# coding: utf-8
#
# Copyright 2021 Florian Holderied (florian.holderied@ipp.mpg.de)

"""
Classes for local projectors in 1D and 3D based on quasi-spline interpolation and histopolation.
"""

import scipy.sparse as spa

import struphy.feec.bsplines as bsp
import struphy.feec.projectors.pro_local.kernels_projectors_local as ker_loc
from struphy.utils.arrays import xp as np


# ======================= 1d ====================================
class projectors_local_1d:
    """
    Local commuting projectors pi_0 and pi_1 in 1d.

    Parameters
    ----------
    spline_space : Spline_space_1d
        a 1d space of B-splines

    n_quad : int
        number of quadrature points per integration interval for histopolations
    """

    def __init__(self, spline_space, n_quad):
        self.kind = "local"

        self.space = spline_space  # 1D spline space
        self.T = spline_space.T  # knot vector
        self.p = spline_space.p  # spline degree
        self.bc = spline_space.bc  # boundary conditions

        self.NbaseN = spline_space.NbaseN  # number of basis functions (N)
        self.NbaseD = spline_space.NbaseD  # number of basis functions (D)

        self.n_quad = n_quad  # number of quadrature point per integration interval

        # Gauss - Legendre quadrature points and weights in (-1, 1)
        self.pts_loc = np.polynomial.legendre.leggauss(self.n_quad)[0]
        self.wts_loc = np.polynomial.legendre.leggauss(self.n_quad)[1]

        # set interpolation and histopolation coefficients
        if self.bc == True:
            self.coeff_i = np.zeros((1, 2 * self.p - 1), dtype=float)
            self.coeff_h = np.zeros((1, 2 * self.p), dtype=float)

            if self.p == 1:
                self.coeff_i[0, :] = np.array([1.0])
                self.coeff_h[0, :] = np.array([1.0, 1.0])

            elif self.p == 2:
                self.coeff_i[0, :] = 1 / 2 * np.array([-1.0, 4.0, -1.0])
                self.coeff_h[0, :] = 1 / 2 * np.array([-1.0, 3.0, 3.0, -1.0])

            elif self.p == 3:
                self.coeff_i[0, :] = 1 / 6 * np.array([1.0, -8.0, 20.0, -8.0, 1.0])
                self.coeff_h[0, :] = 1 / 6 * np.array([1.0, -7.0, 12.0, 12.0, -7.0, 1.0])

            elif self.p == 4:
                self.coeff_i[0, :] = 2 / 45 * np.array([-1.0, 16.0, -295 / 4, 140.0, -295 / 4, 16.0, -1.0])
                self.coeff_h[0, :] = 2 / 45 * np.array([-1.0, 15.0, -231 / 4, 265 / 4, 265 / 4, -231 / 4, 15.0, -1.0])

            else:
                print("degree > 4 not implemented!")

        else:
            self.coeff_i = np.zeros((2 * self.p - 1, 2 * self.p - 1), dtype=float)
            self.coeff_h = np.zeros((2 * self.p - 1, 2 * self.p), dtype=float)

            if self.p == 1:
                self.coeff_i[0, :] = np.array([1.0])
                self.coeff_h[0, :] = np.array([1.0, 1.0])

            elif self.p == 2:
                self.coeff_i[0, :] = 1 / 2 * np.array([2.0, 0.0, 0.0])
                self.coeff_i[1, :] = 1 / 2 * np.array([-1.0, 4.0, -1.0])
                self.coeff_i[2, :] = 1 / 2 * np.array([0.0, 0.0, 2.0])

                self.coeff_h[0, :] = 1 / 2 * np.array([3.0, -1.0, 0.0, 0.0])
                self.coeff_h[1, :] = 1 / 2 * np.array([-1.0, 3.0, 3.0, -1.0])
                self.coeff_h[2, :] = 1 / 2 * np.array([0.0, 0.0, -1.0, 3.0])

            elif self.p == 3:
                self.coeff_i[0, :] = 1 / 18 * np.array([18.0, 0.0, 0.0, 0.0, 0.0])
                self.coeff_i[1, :] = 1 / 18 * np.array([-5.0, 40.0, -24.0, 8.0, -1.0])
                self.coeff_i[2, :] = 1 / 18 * np.array([3.0, -24.0, 60.0, -24.0, 3.0])
                self.coeff_i[3, :] = 1 / 18 * np.array([-1.0, 8.0, -24.0, 40.0, -5.0])
                self.coeff_i[4, :] = 1 / 18 * np.array([0.0, 0.0, 0.0, 0.0, 18.0])

                self.coeff_h[0, :] = 1 / 18 * np.array([23.0, -17.0, 7.0, -1.0, 0.0, 0.0])
                self.coeff_h[1, :] = 1 / 18 * np.array([-8.0, 56.0, -28.0, 4.0, 0.0, 0.0])
                self.coeff_h[2, :] = 1 / 18 * np.array([3.0, -21.0, 36.0, 36.0, -21.0, 3.0])
                self.coeff_h[3, :] = 1 / 18 * np.array([0.0, 0.0, 4.0, -28.0, 56.0, -8.0])
                self.coeff_h[4, :] = 1 / 18 * np.array([0.0, 0.0, -1.0, 7.0, -17.0, 23.0])

            elif self.p == 4:
                self.coeff_i[0, :] = 1 / 360 * np.array([360.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
                self.coeff_i[1, :] = 1 / 360 * np.array([-59.0, 944.0, -1000.0, 720.0, -305.0, 64.0, -4.0])
                self.coeff_i[2, :] = 1 / 360 * np.array([23.0, -368.0, 1580.0, -1360.0, 605.0, -128.0, 8.0])
                self.coeff_i[3, :] = 1 / 360 * np.array([-16.0, 256.0, -1180.0, 2240.0, -1180.0, 256.0, -16.0])
                self.coeff_i[4, :] = 1 / 360 * np.array([8.0, -128.0, 605.0, -1360.0, 1580.0, -368.0, 23.0])
                self.coeff_i[5, :] = 1 / 360 * np.array([-4.0, 64.0, -305.0, 720.0, -1000.0, 944.0, -59.0])
                self.coeff_i[6, :] = 1 / 360 * np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 360.0])

                self.coeff_h[0, :] = 1 / 360 * np.array([419.0, -525.0, 475.0, -245.0, 60.0, -4.0, 0.0, 0.0])
                self.coeff_h[1, :] = 1 / 360 * np.array([-82.0, 1230.0, -1350.0, 730.0, -180.0, 12.0, 0.0, 0.0])
                self.coeff_h[2, :] = 1 / 360 * np.array([39.0, -585.0, 2175.0, -1425.0, 360.0, -24.0, 0.0, 0.0])
                self.coeff_h[3, :] = 1 / 360 * np.array([-16.0, 240.0, -924.0, 1060.0, 1060.0, -924.0, 240.0, -16.0])
                self.coeff_h[4, :] = 1 / 360 * np.array([0.0, 0.0, -24.0, 360.0, -1425.0, 2175.0, -585.0, 39.0])
                self.coeff_h[5, :] = 1 / 360 * np.array([0.0, 0.0, 12.0, -180.0, 730.0, -1350.0, 1230.0, -82.0])
                self.coeff_h[6, :] = 1 / 360 * np.array([0.0, 0.0, -4.0, 60.0, -245.0, 475.0, -525.0, 419.0])

            else:
                print("degree > 4 not implemented!")

        # set interpolation points
        n_lambda_int = np.copy(self.NbaseN)  # number of coefficients in space V0
        self.n_int = 2 * self.p - 1  # number of local interpolation points (1, 3, 5, 7, ...)

        if self.p == 1:
            self.n_int_locbf_N = 2  # number of non-vanishing N bf in interpolation interval (2, 3, 5, 7, ...)
            self.n_int_locbf_D = 1  # number of non-vanishing D bf in interpolation interval (1, 2, 4, 6, ...)

        else:
            self.n_int_locbf_N = (
                2 * self.p - 1
            )  # number of non-vanishing N bf in interpolation interval (2, 3, 5, 7, ...)
            self.n_int_locbf_D = (
                2 * self.p - 2
            )  # number of non-vanishing D bf in interpolation interval (1, 2, 4, 6, ...)

        self.x_int = np.zeros((n_lambda_int, self.n_int), dtype=float)  # interpolation points for each coeff.

        self.int_global_N = np.zeros(
            (n_lambda_int, self.n_int_locbf_N), dtype=int
        )  # global indices of non-vanishing N bf
        self.int_global_D = np.zeros(
            (n_lambda_int, self.n_int_locbf_D), dtype=int
        )  # global indices of non-vanishing D bf

        self.int_loccof_N = np.zeros((n_lambda_int, self.n_int_locbf_N), dtype=int)  # index of non-vanishing coeff. (N)
        self.int_loccof_D = np.zeros((n_lambda_int, self.n_int_locbf_D), dtype=int)  # index of non-vanishing coeff. (D)

        self.x_int_indices = np.zeros((n_lambda_int, self.n_int), dtype=int)

        self.coeffi_indices = np.zeros(n_lambda_int, dtype=int)

        if self.bc == False:
            # maximum number of non-vanishing coefficients
            if self.p == 1:
                self.n_int_nvcof_D = 2
                self.n_int_nvcof_N = 2
            else:
                self.n_int_nvcof_D = 3 * self.p - 3
                self.n_int_nvcof_N = 3 * self.p - 2

            # shift in local coefficient indices at right boundary (only for non-periodic boundary conditions)
            self.int_add_D = np.arange(self.n_int - 2) + 1
            self.int_add_N = np.arange(self.n_int - 1) + 1

            counter_D = 0
            counter_N = 0

            # shift local coefficients --> global coefficients (D)
            if self.p == 1:
                self.int_shift_D = np.arange(self.NbaseD)
            else:
                self.int_shift_D = np.arange(self.NbaseD) - (self.p - 2)
                self.int_shift_D[: 2 * self.p - 2] = 0
                self.int_shift_D[-(2 * self.p - 2) :] = self.int_shift_D[-(2 * self.p - 2)]

            # shift local coefficients --> global coefficients (N)
            if self.p == 1:
                self.int_shift_N = np.arange(self.NbaseN)
                self.int_shift_N[-1] = self.int_shift_N[-2]

            else:
                self.int_shift_N = np.arange(self.NbaseN) - (self.p - 1)
                self.int_shift_N[: 2 * self.p - 1] = 0
                self.int_shift_N[-(2 * self.p - 1) :] = self.int_shift_N[-(2 * self.p - 1)]

            counter_coeffi = np.copy(self.p)

            for i in range(n_lambda_int):
                # left boundary region
                if i < self.p - 1:
                    self.int_global_N[i] = np.arange(self.n_int_locbf_N)
                    self.int_global_D[i] = np.arange(self.n_int_locbf_D)

                    self.x_int_indices[i] = np.arange(self.n_int)
                    self.coeffi_indices[i] = i
                    for j in range(2 * (self.p - 1) + 1):
                        xi = self.p - 1
                        self.x_int[i, j] = (self.T[xi + 1 + int(j / 2)] + self.T[xi + 1 + int((j + 1) / 2)]) / 2

                # right boundary region
                elif i > n_lambda_int - self.p:
                    self.int_global_N[i] = np.arange(self.n_int_locbf_N) + n_lambda_int - self.p - (self.p - 1)
                    self.int_global_D[i] = np.arange(self.n_int_locbf_D) + n_lambda_int - self.p - (self.p - 1)

                    self.x_int_indices[i] = np.arange(self.n_int) + 2 * (n_lambda_int - self.p - (self.p - 1))
                    self.coeffi_indices[i] = counter_coeffi
                    counter_coeffi += 1
                    for j in range(2 * (self.p - 1) + 1):
                        xi = n_lambda_int - self.p
                        self.x_int[i, j] = (self.T[xi + 1 + int(j / 2)] + self.T[xi + 1 + int((j + 1) / 2)]) / 2

                # interior
                else:
                    if self.p == 1:
                        self.int_global_N[i] = np.arange(self.n_int_locbf_N) + i
                        self.int_global_D[i] = np.arange(self.n_int_locbf_D) + i

                        self.int_global_N[-1] = self.int_global_N[-2]
                        self.int_global_D[-1] = self.int_global_D[-2]

                    else:
                        self.int_global_N[i] = np.arange(self.n_int_locbf_N) + i - (self.p - 1)
                        self.int_global_D[i] = np.arange(self.n_int_locbf_D) + i - (self.p - 1)

                    if self.p == 1:
                        self.x_int_indices[i] = i
                    else:
                        self.x_int_indices[i] = np.arange(self.n_int) + 2 * (i - (self.p - 1))

                    self.coeffi_indices[i] = self.p - 1
                    for j in range(2 * (self.p - 1) + 1):
                        self.x_int[i, j] = (self.T[i + 1 + int(j / 2)] + self.T[i + 1 + int((j + 1) / 2)]) / 2

                # local coefficient index
                if self.p == 1:
                    self.int_loccof_N[i] = np.array([0, 1])
                    self.int_loccof_D[-1] = np.array([1])

                else:
                    if i > 0:
                        for il in range(self.n_int_locbf_D):
                            k_glob_new = self.int_global_D[i, il]
                            bol = k_glob_new == self.int_global_D[i - 1]

                            if np.any(bol):
                                self.int_loccof_D[i, il] = self.int_loccof_D[i - 1, np.where(bol)[0][0]] + 1

                            if (k_glob_new >= n_lambda_int - self.p - (self.p - 2)) and (self.int_loccof_D[i, il] == 0):
                                self.int_loccof_D[i, il] = self.int_add_D[counter_D]
                                counter_D += 1

                        for il in range(self.n_int_locbf_N):
                            k_glob_new = self.int_global_N[i, il]
                            bol = k_glob_new == self.int_global_N[i - 1]

                            if np.any(bol):
                                self.int_loccof_N[i, il] = self.int_loccof_N[i - 1, np.where(bol)[0][0]] + 1

                            if (k_glob_new >= n_lambda_int - self.p - (self.p - 2)) and (self.int_loccof_N[i, il] == 0):
                                self.int_loccof_N[i, il] = self.int_add_N[counter_N]
                                counter_N += 1

        else:
            # maximum number of non-vanishing coefficients
            if self.p == 1:
                self.n_int_nvcof_D = 2 * self.p - 1
                self.n_int_nvcof_N = 2 * self.p

            else:
                self.n_int_nvcof_D = 2 * self.p - 2
                self.n_int_nvcof_N = 2 * self.p - 1

            # shift local coefficients --> global coefficients
            if self.p == 1:
                self.int_shift_D = np.arange(self.NbaseN) - (self.p - 1)
                self.int_shift_N = np.arange(self.NbaseN) - (self.p)
            else:
                self.int_shift_D = np.arange(self.NbaseN) - (self.p - 2)
                self.int_shift_N = np.arange(self.NbaseN) - (self.p - 1)

            for i in range(n_lambda_int):
                # global indices of non-vanishing basis functions and position of coefficients in final matrix
                self.int_global_D[i] = (np.arange(self.n_int_locbf_D) + i - (self.p - 1)) % self.NbaseD
                self.int_loccof_D[i] = np.arange(self.n_int_locbf_D - 1, -1, -1)

                self.int_global_N[i] = (np.arange(self.n_int_locbf_N) + i - (self.p - 1)) % self.NbaseN
                self.int_loccof_N[i] = np.arange(self.n_int_locbf_N - 1, -1, -1)

                if self.p == 1:
                    self.x_int_indices[i] = i
                else:
                    self.x_int_indices[i] = np.arange(self.n_int) + 2 * (i - (self.p - 1))

                self.coeffi_indices[i] = 0

                for j in range(2 * (self.p - 1) + 1):
                    self.x_int[i, j] = ((self.T[i + 1 + int(j / 2)] + self.T[i + 1 + int((j + 1) / 2)]) / 2) % 1.0

        # set histopolation points, quadrature points and weights
        n_lambda_his = np.copy(self.NbaseD)  # number of coefficients in space V1

        self.n_his = 2 * self.p  # number of histopolation intervals (2, 4, 6, 8, ...)
        self.n_his_locbf_N = 2 * self.p  # number of non-vanishing N bf in histopolation interval (2, 4, 6, 8, ...)
        self.n_his_locbf_D = 2 * self.p - 1  # number of non-vanishing D bf in histopolation interval (2, 4, 6, 8, ...)

        self.x_his = np.zeros((n_lambda_his, self.n_his + 1), dtype=float)  # histopolation boundaries

        self.his_global_N = np.zeros((n_lambda_his, self.n_his_locbf_N), dtype=int)
        self.his_global_D = np.zeros((n_lambda_his, self.n_his_locbf_D), dtype=int)

        self.his_loccof_N = np.zeros((n_lambda_his, self.n_his_locbf_N), dtype=int)
        self.his_loccof_D = np.zeros((n_lambda_his, self.n_his_locbf_D), dtype=int)

        self.x_his_indices = np.zeros((n_lambda_his, self.n_his), dtype=int)

        self.coeffh_indices = np.zeros(n_lambda_his, dtype=int)

        if self.bc == False:
            # maximum number of non-vanishing coefficients
            self.n_his_nvcof_D = 3 * self.p - 2
            self.n_his_nvcof_N = 3 * self.p - 1

            # shift in local coefficient indices at right boundary (only for non-periodic boundary conditions)
            self.his_add_D = np.arange(self.n_his - 2) + 1
            self.his_add_N = np.arange(self.n_his - 1) + 1

            counter_D = 0
            counter_N = 0

            # shift local coefficients --> global coefficients (D)
            self.his_shift_D = np.arange(self.NbaseD) - (self.p - 1)
            self.his_shift_D[: 2 * self.p - 1] = 0
            self.his_shift_D[-(2 * self.p - 1) :] = self.his_shift_D[-(2 * self.p - 1)]

            # shift local coefficients --> global coefficients (N)
            self.his_shift_N = np.arange(self.NbaseN) - self.p
            self.his_shift_N[: 2 * self.p] = 0
            self.his_shift_N[-2 * self.p :] = self.his_shift_N[-2 * self.p]

            counter_coeffh = np.copy(self.p)

            for i in range(n_lambda_his):
                # left boundary region
                if i < self.p - 1:
                    self.his_global_N[i] = np.arange(self.n_his_locbf_N)
                    self.his_global_D[i] = np.arange(self.n_his_locbf_D)

                    self.x_his_indices[i] = np.arange(self.n_his)
                    self.coeffh_indices[i] = i
                    for j in range(2 * self.p + 1):
                        xi = self.p - 1
                        self.x_his[i, j] = (self.T[xi + 1 + int(j / 2)] + self.T[xi + 1 + int((j + 1) / 2)]) / 2

                # right boundary region
                elif i > n_lambda_his - self.p:
                    self.his_global_N[i] = np.arange(self.n_his_locbf_N) + n_lambda_his - self.p - (self.p - 1)
                    self.his_global_D[i] = np.arange(self.n_his_locbf_D) + n_lambda_his - self.p - (self.p - 1)

                    self.x_his_indices[i] = np.arange(self.n_his) + 2 * (n_lambda_his - self.p - (self.p - 1))
                    self.coeffh_indices[i] = counter_coeffh
                    counter_coeffh += 1
                    for j in range(2 * self.p + 1):
                        xi = n_lambda_his - self.p
                        self.x_his[i, j] = (self.T[xi + 1 + int(j / 2)] + self.T[xi + 1 + int((j + 1) / 2)]) / 2

                # interior
                else:
                    self.his_global_N[i] = np.arange(self.n_his_locbf_N) + i - (self.p - 1)
                    self.his_global_D[i] = np.arange(self.n_his_locbf_D) + i - (self.p - 1)

                    self.x_his_indices[i] = np.arange(self.n_his) + 2 * (i - (self.p - 1))
                    self.coeffh_indices[i] = self.p - 1
                    for j in range(2 * self.p + 1):
                        self.x_his[i, j] = (self.T[i + 1 + int(j / 2)] + self.T[i + 1 + int((j + 1) / 2)]) / 2

                # local coefficient index
                if i > 0:
                    for il in range(self.n_his_locbf_D):
                        k_glob_new = self.his_global_D[i, il]
                        bol = k_glob_new == self.his_global_D[i - 1]

                        if np.any(bol):
                            self.his_loccof_D[i, il] = self.his_loccof_D[i - 1, np.where(bol)[0][0]] + 1

                        if (k_glob_new >= n_lambda_his - self.p - (self.p - 2)) and (self.his_loccof_D[i, il] == 0):
                            self.his_loccof_D[i, il] = self.his_add_D[counter_D]
                            counter_D += 1

                    for il in range(self.n_his_locbf_N):
                        k_glob_new = self.his_global_N[i, il]
                        bol = k_glob_new == self.his_global_N[i - 1]

                        if np.any(bol):
                            self.his_loccof_N[i, il] = self.his_loccof_N[i - 1, np.where(bol)[0][0]] + 1

                        if (k_glob_new >= n_lambda_his - self.p - (self.p - 2)) and (self.his_loccof_N[i, il] == 0):
                            self.his_loccof_N[i, il] = self.his_add_N[counter_N]
                            counter_N += 1

            # quadrature points and weights
            self.pts, self.wts = bsp.quadrature_grid(np.unique(self.x_his.flatten()), self.pts_loc, self.wts_loc)

        else:
            # maximum number of non-vanishing coefficients
            self.n_his_nvcof_D = 2 * self.p - 1
            self.n_his_nvcof_N = 2 * self.p

            # shift local coefficients --> global coefficients
            self.his_shift_D = np.arange(self.NbaseD) - (self.p - 1)
            self.his_shift_N = np.arange(self.NbaseD) - self.p

            for i in range(n_lambda_his):
                self.his_global_N[i] = (np.arange(self.n_his_locbf_N) + i - (self.p - 1)) % self.NbaseN
                self.his_global_D[i] = (np.arange(self.n_his_locbf_D) + i - (self.p - 1)) % self.NbaseD
                self.his_loccof_N[i] = np.arange(self.n_his_locbf_N - 1, -1, -1)
                self.his_loccof_D[i] = np.arange(self.n_his_locbf_D - 1, -1, -1)

                self.x_his_indices[i] = np.arange(self.n_his) + 2 * (i - (self.p - 1))
                self.coeffh_indices[i] = 0
                for j in range(2 * self.p + 1):
                    self.x_his[i, j] = (self.T[i + 1 + int(j / 2)] + self.T[i + 1 + int((j + 1) / 2)]) / 2

            # quadrature points and weights
            self.pts, self.wts = bsp.quadrature_grid(
                np.append(np.unique(self.x_his.flatten() % 1.0), 1.0), self.pts_loc, self.wts_loc
            )

    # quasi interpolation
    def pi_0(self, fun):
        lambdas = np.zeros(self.NbaseN, dtype=float)

        # evaluate function at interpolation points
        mat_f = fun(np.unique(self.x_int.flatten()))

        for i in range(self.NbaseN):
            for j in range(self.n_int):
                lambdas[i] += self.coeff_i[self.coeffi_indices[i], j] * mat_f[self.x_int_indices[i, j]]

        return lambdas

    # quasi histopolation
    def pi_1(self, fun):
        lambdas = np.zeros(self.NbaseD, dtype=float)

        # evaluate function at quadrature points
        mat_f = fun(self.pts)

        for i in range(self.NbaseD):
            for j in range(self.n_his):
                f_int = 0.0

                for q in range(self.n_quad):
                    f_int += self.wts[self.x_his_indices[i, j], q] * mat_f[self.x_his_indices[i, j], q]

                lambdas[i] += self.coeff_h[self.coeffh_indices[i], j] * f_int

        return lambdas

    # projection matrices of products of basis functions: pi0_i(A_j*B_k) and pi1_i(A_j*B_k)
    def projection_matrices_1d(self, bc_kind=["free", "free"]):
        PI0_NN = np.empty((self.NbaseN, self.NbaseN, self.NbaseN), dtype=float)
        PI0_DN = np.empty((self.NbaseN, self.NbaseD, self.NbaseN), dtype=float)
        PI0_DD = np.empty((self.NbaseN, self.NbaseD, self.NbaseD), dtype=float)

        PI1_NN = np.empty((self.NbaseD, self.NbaseN, self.NbaseN), dtype=float)
        PI1_DN = np.empty((self.NbaseD, self.NbaseD, self.NbaseN), dtype=float)
        PI1_DD = np.empty((self.NbaseD, self.NbaseD, self.NbaseD), dtype=float)

        # ========= PI0__NN and PI1_NN =============
        ci = np.zeros(self.NbaseN, dtype=float)
        cj = np.zeros(self.NbaseN, dtype=float)

        for i in range(self.NbaseN):
            for j in range(self.NbaseN):
                ci[:] = 0.0
                cj[:] = 0.0

                ci[i] = 1.0
                cj[j] = 1.0

                fun = lambda eta: self.space.evaluate_N(eta, ci) * self.space.evaluate_N(eta, cj)

                PI0_NN[:, i, j] = self.pi_0(fun)
                PI1_NN[:, i, j] = self.pi_1(fun)

        # ========= PI0__DN and PI1_DN =============
        ci = np.zeros(self.NbaseD, dtype=float)
        cj = np.zeros(self.NbaseN, dtype=float)

        for i in range(self.NbaseD):
            for j in range(self.NbaseN):
                ci[:] = 0.0
                cj[:] = 0.0

                ci[i] = 1.0
                cj[j] = 1.0

                fun = lambda eta: self.space.evaluate_D(eta, ci) * self.space.evaluate_N(eta, cj)

                PI0_DN[:, i, j] = self.pi_0(fun)
                PI1_DN[:, i, j] = self.pi_1(fun)

        # ========= PI0__DD and PI1_DD =============
        ci = np.zeros(self.NbaseD, dtype=float)
        cj = np.zeros(self.NbaseD, dtype=float)

        for i in range(self.NbaseD):
            for j in range(self.NbaseD):
                ci[:] = 0.0
                cj[:] = 0.0

                ci[i] = 1.0
                cj[j] = 1.0

                fun = lambda eta: self.space.evaluate_D(eta, ci) * self.space.evaluate_D(eta, cj)

                PI0_DD[:, i, j] = self.pi_0(fun)
                PI1_DD[:, i, j] = self.pi_1(fun)

        PI0_ND = np.transpose(PI0_DN, (0, 2, 1))
        PI1_ND = np.transpose(PI1_DN, (0, 2, 1))

        # remove contributions from first and last N-splines
        if bc_kind[0] == "dirichlet":
            PI0_NN[:, :, 0] = 0.0
            PI0_NN[:, 0, :] = 0.0
            PI0_DN[:, :, 0] = 0.0
            PI0_ND[:, 0, :] = 0.0

            PI1_NN[:, :, 0] = 0.0
            PI1_NN[:, 0, :] = 0.0
            PI1_DN[:, :, 0] = 0.0
            PI1_ND[:, 0, :] = 0.0

        if bc_kind[1] == "dirichlet":
            PI0_NN[:, :, -1] = 0.0
            PI0_NN[:, -1, :] = 0.0
            PI0_DN[:, :, -1] = 0.0
            PI0_ND[:, -1, :] = 0.0

            PI1_NN[:, :, -1] = 0.0
            PI1_NN[:, -1, :] = 0.0
            PI1_DN[:, :, -1] = 0.0
            PI1_ND[:, -1, :] = 0.0

        PI0_NN_indices = np.nonzero(PI0_NN)
        PI0_DN_indices = np.nonzero(PI0_DN)
        PI0_ND_indices = np.nonzero(PI0_ND)
        PI0_DD_indices = np.nonzero(PI0_DD)

        PI1_NN_indices = np.nonzero(PI1_NN)
        PI1_DN_indices = np.nonzero(PI1_DN)
        PI1_ND_indices = np.nonzero(PI1_ND)
        PI1_DD_indices = np.nonzero(PI1_DD)

        PI0_NN_indices = np.vstack((PI0_NN_indices[0], PI0_NN_indices[1], PI0_NN_indices[2]))
        PI0_DN_indices = np.vstack((PI0_DN_indices[0], PI0_DN_indices[1], PI0_DN_indices[2]))
        PI0_ND_indices = np.vstack((PI0_ND_indices[0], PI0_ND_indices[1], PI0_ND_indices[2]))
        PI0_DD_indices = np.vstack((PI0_DD_indices[0], PI0_DD_indices[1], PI0_DD_indices[2]))

        PI1_NN_indices = np.vstack((PI1_NN_indices[0], PI1_NN_indices[1], PI1_NN_indices[2]))
        PI1_DN_indices = np.vstack((PI1_DN_indices[0], PI1_DN_indices[1], PI1_DN_indices[2]))
        PI1_ND_indices = np.vstack((PI1_ND_indices[0], PI1_ND_indices[1], PI1_ND_indices[2]))
        PI1_DD_indices = np.vstack((PI1_DD_indices[0], PI1_DD_indices[1], PI1_DD_indices[2]))

        return (
            PI0_NN,
            PI0_DN,
            PI0_ND,
            PI0_DD,
            PI1_NN,
            PI1_DN,
            PI1_ND,
            PI1_DD,
            PI0_NN_indices,
            PI0_DN_indices,
            PI0_ND_indices,
            PI0_DD_indices,
            PI1_NN_indices,
            PI1_DN_indices,
            PI1_ND_indices,
            PI1_DD_indices,
        )


# ======================= 3d ====================================
class projectors_local_3d:
    """
    Local commuting projectors pi_0, pi_1, pi_2 and pi_3 in 3d.

    Parameters
    ----------
    tensor_space : Tensor_spline_space
        a 3d tensor product space of B-splines

    n_quad : list of ints
        number of quadrature points per integration interval for histopolations
    """

    def __init__(self, tensor_space, n_quad):
        self.kind = "local"  # kind of projector

        self.tensor_space = tensor_space  # 3D tensor-product B-splines space

        self.T = tensor_space.T  # knot vector
        self.p = tensor_space.p  # spline degree
        self.bc = tensor_space.spl_kind  # boundary conditions
        self.el_b = tensor_space.el_b  # element boundaries

        self.Nel = tensor_space.Nel  # number of elements
        self.NbaseN = tensor_space.NbaseN  # number of basis functions (N)
        self.NbaseD = tensor_space.NbaseD  # number of basis functions (D)

        self.n_quad = n_quad  # number of quadrature point per integration interval

        self.polar = False  # local projectors for polar splines are not implemented yet

        # Gauss - Legendre quadrature points and weights in (-1, 1)
        self.pts_loc = [np.polynomial.legendre.leggauss(n_quad)[0] for n_quad in self.n_quad]
        self.wts_loc = [np.polynomial.legendre.leggauss(n_quad)[1] for n_quad in self.n_quad]

        # set interpolation and histopolation coefficients
        self.coeff_i = [0, 0, 0]
        self.coeff_h = [0, 0, 0]

        for a in range(3):
            if self.bc[a] == True:
                self.coeff_i[a] = np.zeros((1, 2 * self.p[a] - 1), dtype=float)
                self.coeff_h[a] = np.zeros((1, 2 * self.p[a]), dtype=float)

                if self.p[a] == 1:
                    self.coeff_i[a][0, :] = np.array([1.0])
                    self.coeff_h[a][0, :] = np.array([1.0, 1.0])

                elif self.p[a] == 2:
                    self.coeff_i[a][0, :] = 1 / 2 * np.array([-1.0, 4.0, -1.0])
                    self.coeff_h[a][0, :] = 1 / 2 * np.array([-1.0, 3.0, 3.0, -1.0])

                elif self.p[a] == 3:
                    self.coeff_i[a][0, :] = 1 / 6 * np.array([1.0, -8.0, 20.0, -8.0, 1.0])
                    self.coeff_h[a][0, :] = 1 / 6 * np.array([1.0, -7.0, 12.0, 12.0, -7.0, 1.0])

                elif self.p[a] == 4:
                    self.coeff_i[a][0, :] = 2 / 45 * np.array([-1.0, 16.0, -295 / 4, 140.0, -295 / 4, 16.0, -1.0])
                    self.coeff_h[a][0, :] = (
                        2 / 45 * np.array([-1.0, 15.0, -231 / 4, 265 / 4, 265 / 4, -231 / 4, 15.0, -1.0])
                    )

                else:
                    print("degree > 4 not implemented!")

            else:
                self.coeff_i[a] = np.zeros((2 * self.p[a] - 1, 2 * self.p[a] - 1), dtype=float)
                self.coeff_h[a] = np.zeros((2 * self.p[a] - 1, 2 * self.p[a]), dtype=float)

                if self.p[a] == 1:
                    self.coeff_i[a][0, :] = np.array([1.0])
                    self.coeff_h[a][0, :] = np.array([1.0, 1.0])

                elif self.p[a] == 2:
                    self.coeff_i[a][0, :] = 1 / 2 * np.array([2.0, 0.0, 0.0])
                    self.coeff_i[a][1, :] = 1 / 2 * np.array([-1.0, 4.0, -1.0])
                    self.coeff_i[a][2, :] = 1 / 2 * np.array([0.0, 0.0, 2.0])

                    self.coeff_h[a][0, :] = 1 / 2 * np.array([3.0, -1.0, 0.0, 0.0])
                    self.coeff_h[a][1, :] = 1 / 2 * np.array([-1.0, 3.0, 3.0, -1.0])
                    self.coeff_h[a][2, :] = 1 / 2 * np.array([0.0, 0.0, -1.0, 3.0])

                elif self.p[a] == 3:
                    self.coeff_i[a][0, :] = 1 / 18 * np.array([18.0, 0.0, 0.0, 0.0, 0.0])
                    self.coeff_i[a][1, :] = 1 / 18 * np.array([-5.0, 40.0, -24.0, 8.0, -1.0])
                    self.coeff_i[a][2, :] = 1 / 18 * np.array([3.0, -24.0, 60.0, -24.0, 3.0])
                    self.coeff_i[a][3, :] = 1 / 18 * np.array([-1.0, 8.0, -24.0, 40.0, -5.0])
                    self.coeff_i[a][4, :] = 1 / 18 * np.array([0.0, 0.0, 0.0, 0.0, 18.0])

                    self.coeff_h[a][0, :] = 1 / 18 * np.array([23.0, -17.0, 7.0, -1.0, 0.0, 0.0])
                    self.coeff_h[a][1, :] = 1 / 18 * np.array([-8.0, 56.0, -28.0, 4.0, 0.0, 0.0])
                    self.coeff_h[a][2, :] = 1 / 18 * np.array([3.0, -21.0, 36.0, 36.0, -21.0, 3.0])
                    self.coeff_h[a][3, :] = 1 / 18 * np.array([0.0, 0.0, 4.0, -28.0, 56.0, -8.0])
                    self.coeff_h[a][4, :] = 1 / 18 * np.array([0.0, 0.0, -1.0, 7.0, -17.0, 23.0])

                elif self.p[a] == 4:
                    self.coeff_i[a][0, :] = 1 / 360 * np.array([360.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
                    self.coeff_i[a][1, :] = 1 / 360 * np.array([-59.0, 944.0, -1000.0, 720.0, -305.0, 64.0, -4.0])
                    self.coeff_i[a][2, :] = 1 / 360 * np.array([23.0, -368.0, 1580.0, -1360.0, 605.0, -128.0, 8.0])
                    self.coeff_i[a][3, :] = 1 / 360 * np.array([-16.0, 256.0, -1180.0, 2240.0, -1180.0, 256.0, -16.0])
                    self.coeff_i[a][4, :] = 1 / 360 * np.array([8.0, -128.0, 605.0, -1360.0, 1580.0, -368.0, 23.0])
                    self.coeff_i[a][5, :] = 1 / 360 * np.array([-4.0, 64.0, -305.0, 720.0, -1000.0, 944.0, -59.0])
                    self.coeff_i[a][6, :] = 1 / 360 * np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 360.0])

                    self.coeff_h[a][0, :] = 1 / 360 * np.array([419.0, -525.0, 475.0, -245.0, 60.0, -4.0, 0.0, 0.0])
                    self.coeff_h[a][1, :] = 1 / 360 * np.array([-82.0, 1230.0, -1350.0, 730.0, -180.0, 12.0, 0.0, 0.0])
                    self.coeff_h[a][2, :] = 1 / 360 * np.array([39.0, -585.0, 2175.0, -1425.0, 360.0, -24.0, 0.0, 0.0])
                    self.coeff_h[a][3, :] = (
                        1 / 360 * np.array([-16.0, 240.0, -924.0, 1060.0, 1060.0, -924.0, 240.0, -16.0])
                    )
                    self.coeff_h[a][4, :] = 1 / 360 * np.array([0.0, 0.0, -24.0, 360.0, -1425.0, 2175.0, -585.0, 39.0])
                    self.coeff_h[a][5, :] = 1 / 360 * np.array([0.0, 0.0, 12.0, -180.0, 730.0, -1350.0, 1230.0, -82.0])
                    self.coeff_h[a][6, :] = 1 / 360 * np.array([0.0, 0.0, -4.0, 60.0, -245.0, 475.0, -525.0, 419.0])

                else:
                    print("degree > 4 not implemented!")

        # set interpolation points
        n_lambda_int = [NbaseN for NbaseN in self.NbaseN]  # number of coefficients in space V0
        self.n_int = [2 * p - 1 for p in self.p]  # number of interpolation points (1, 3, 5, 7, ...)

        self.n_int_locbf_N = [0, 0, 0]
        self.n_int_locbf_D = [0, 0, 0]

        for a in range(3):
            if self.p[a] == 1:
                self.n_int_locbf_N[a] = 2  # number of non-vanishing N bf in interpolation interval (2, 3, 5, 7)
                self.n_int_locbf_D[a] = 1  # number of non-vanishing D bf in interpolation interval (1, 2, 4, 6)

            else:
                self.n_int_locbf_N[a] = (
                    2 * self.p[a] - 1
                )  # number of non-vanishing N bf in interpolation interval (2, 3, 5, 7)
                self.n_int_locbf_D[a] = (
                    2 * self.p[a] - 2
                )  # number of non-vanishing D bf in interpolation interval (1, 2, 4, 6)

        self.x_int = [
            np.zeros((n_lambda_int, n_int), dtype=float) for n_lambda_int, n_int in zip(n_lambda_int, self.n_int)
        ]

        self.int_global_N = [
            np.zeros((n_lambda_int, n_int_locbf_N), dtype=int)
            for n_lambda_int, n_int_locbf_N in zip(n_lambda_int, self.n_int_locbf_N)
        ]
        self.int_global_D = [
            np.zeros((n_lambda_int, n_int_locbf_D), dtype=int)
            for n_lambda_int, n_int_locbf_D in zip(n_lambda_int, self.n_int_locbf_D)
        ]

        self.int_loccof_N = [
            np.zeros((n_lambda_int, n_int_locbf_N), dtype=int)
            for n_lambda_int, n_int_locbf_N in zip(n_lambda_int, self.n_int_locbf_N)
        ]
        self.int_loccof_D = [
            np.zeros((n_lambda_int, n_int_locbf_D), dtype=int)
            for n_lambda_int, n_int_locbf_D in zip(n_lambda_int, self.n_int_locbf_D)
        ]

        self.x_int_indices = [
            np.zeros((n_lambda_int, n_int), dtype=int) for n_lambda_int, n_int in zip(n_lambda_int, self.n_int)
        ]
        self.coeffi_indices = [np.zeros(n_lambda_int, dtype=int) for n_lambda_int in n_lambda_int]

        self.n_int_nvcof_D = [None, None, None]
        self.n_int_nvcof_N = [None, None, None]

        self.int_add_D = [None, None, None]
        self.int_add_N = [None, None, None]

        self.int_shift_D = [0, 0, 0]
        self.int_shift_N = [0, 0, 0]

        for a in range(3):
            if self.bc[a] == False:
                # maximum number of non-vanishing coefficients
                if self.p[a] == 1:
                    self.n_int_nvcof_D[a] = 2
                    self.n_int_nvcof_N[a] = 2

                else:
                    self.n_int_nvcof_D[a] = 3 * self.p[a] - 3
                    self.n_int_nvcof_N[a] = 3 * self.p[a] - 2

                # shift in local coefficient indices at right boundary (only for non-periodic boundary conditions)
                self.int_add_D[a] = np.arange(self.n_int[a] - 2) + 1
                self.int_add_N[a] = np.arange(self.n_int[a] - 1) + 1

                counter_D = 0
                counter_N = 0

                # shift local coefficients --> global coefficients (D)
                if self.p[a] == 1:
                    self.int_shift_D[a] = np.arange(self.NbaseD[a])
                else:
                    self.int_shift_D[a] = np.arange(self.NbaseD[a]) - (self.p[a] - 2)
                    self.int_shift_D[a][: 2 * self.p[a] - 2] = 0
                    self.int_shift_D[a][-(2 * self.p[a] - 2) :] = self.int_shift_D[a][-(2 * self.p[a] - 2)]

                # shift local coefficients --> global coefficients (N)
                if self.p[a] == 1:
                    self.int_shift_N[a] = np.arange(self.NbaseN[a])
                    self.int_shift_N[a][-1] = self.int_shift_N[a][-2]

                else:
                    self.int_shift_N[a] = np.arange(self.NbaseN[a]) - (self.p[a] - 1)
                    self.int_shift_N[a][: 2 * self.p[a] - 1] = 0
                    self.int_shift_N[a][-(2 * self.p[a] - 1) :] = self.int_shift_N[a][-(2 * self.p[a] - 1)]

                counter_coeffi = np.copy(self.p[a])

                for i in range(n_lambda_int[a]):
                    # left boundary region
                    if i < self.p[a] - 1:
                        self.int_global_N[a][i] = np.arange(self.n_int_locbf_N[a])
                        self.int_global_D[a][i] = np.arange(self.n_int_locbf_D[a])

                        self.x_int_indices[a][i] = np.arange(self.n_int[a])
                        self.coeffi_indices[a][i] = i
                        for j in range(2 * (self.p[a] - 1) + 1):
                            xi = self.p[a] - 1
                            self.x_int[a][i, j] = (
                                self.T[a][xi + 1 + int(j / 2)] + self.T[a][xi + 1 + int((j + 1) / 2)]
                            ) / 2

                    # right boundary region
                    elif i > n_lambda_int[a] - self.p[a]:
                        self.int_global_N[a][i] = (
                            np.arange(self.n_int_locbf_N[a]) + n_lambda_int[a] - self.p[a] - (self.p[a] - 1)
                        )
                        self.int_global_D[a][i] = (
                            np.arange(self.n_int_locbf_D[a]) + n_lambda_int[a] - self.p[a] - (self.p[a] - 1)
                        )

                        self.x_int_indices[a][i] = np.arange(self.n_int[a]) + 2 * (
                            n_lambda_int[a] - self.p[a] - (self.p[a] - 1)
                        )
                        self.coeffi_indices[a][i] = counter_coeffi
                        counter_coeffi += 1
                        for j in range(2 * (self.p[a] - 1) + 1):
                            xi = n_lambda_int[a] - self.p[a]
                            self.x_int[a][i, j] = (
                                self.T[a][xi + 1 + int(j / 2)] + self.T[a][xi + 1 + int((j + 1) / 2)]
                            ) / 2

                    # interior
                    else:
                        if self.p[a] == 1:
                            self.int_global_N[a][i] = np.arange(self.n_int_locbf_N[a]) + i
                            self.int_global_D[a][i] = np.arange(self.n_int_locbf_D[a]) + i

                            self.int_global_N[a][-1] = self.int_global_N[a][-2]
                            self.int_global_D[a][-1] = self.int_global_D[a][-2]

                        else:
                            self.int_global_N[a][i] = np.arange(self.n_int_locbf_N[a]) + i - (self.p[a] - 1)
                            self.int_global_D[a][i] = np.arange(self.n_int_locbf_D[a]) + i - (self.p[a] - 1)

                        if self.p[a] == 1:
                            self.x_int_indices[a][i] = i
                        else:
                            self.x_int_indices[a][i] = np.arange(self.n_int[a]) + 2 * (i - (self.p[a] - 1))

                        self.coeffi_indices[a][i] = self.p[a] - 1

                        for j in range(2 * (self.p[a] - 1) + 1):
                            self.x_int[a][i, j] = (
                                self.T[a][i + 1 + int(j / 2)] + self.T[a][i + 1 + int((j + 1) / 2)]
                            ) / 2

                    # local coefficient index
                    if self.p[a] == 1:
                        self.int_loccof_N[a][i] = np.array([0, 1])
                        self.int_loccof_D[a][-1] = np.array([1])

                    else:
                        if i > 0:
                            for il in range(self.n_int_locbf_D[a]):
                                k_glob_new = self.int_global_D[a][i, il]
                                bol = k_glob_new == self.int_global_D[a][i - 1]

                                if np.any(bol):
                                    self.int_loccof_D[a][i, il] = self.int_loccof_D[a][i - 1, np.where(bol)[0][0]] + 1

                                if (k_glob_new >= n_lambda_int[a] - self.p[a] - (self.p[a] - 2)) and (
                                    self.int_loccof_D[a][i, il] == 0
                                ):
                                    self.int_loccof_D[a][i, il] = self.int_add_D[a][counter_D]
                                    counter_D += 1

                            for il in range(self.n_int_locbf_N[a]):
                                k_glob_new = self.int_global_N[a][i, il]
                                bol = k_glob_new == self.int_global_N[a][i - 1]

                                if np.any(bol):
                                    self.int_loccof_N[a][i, il] = self.int_loccof_N[a][i - 1, np.where(bol)[0][0]] + 1

                                if (k_glob_new >= n_lambda_int[a] - self.p[a] - (self.p[a] - 2)) and (
                                    self.int_loccof_N[a][i, il] == 0
                                ):
                                    self.int_loccof_N[a][i, il] = self.int_add_N[a][counter_N]
                                    counter_N += 1

            else:
                # maximum number of non-vanishing coefficients
                if self.p[a] == 1:
                    self.n_int_nvcof_D[a] = 2 * self.p[a] - 1
                    self.n_int_nvcof_N[a] = 2 * self.p[a]

                else:
                    self.n_int_nvcof_D[a] = 2 * self.p[a] - 2
                    self.n_int_nvcof_N[a] = 2 * self.p[a] - 1

                # shift local coefficients --> global coefficients
                if self.p[a] == 1:
                    self.int_shift_D[a] = np.arange(self.NbaseN[a]) - (self.p[a] - 1)
                    self.int_shift_N[a] = np.arange(self.NbaseN[a]) - (self.p[a])
                else:
                    self.int_shift_D[a] = np.arange(self.NbaseN[a]) - (self.p[a] - 2)
                    self.int_shift_N[a] = np.arange(self.NbaseN[a]) - (self.p[a] - 1)

                for i in range(n_lambda_int[a]):
                    # global indices of non-vanishing basis functions and position of coefficients in final matrix
                    self.int_global_N[a][i] = (np.arange(self.n_int_locbf_N[a]) + i - (self.p[a] - 1)) % self.NbaseN[a]
                    self.int_global_D[a][i] = (np.arange(self.n_int_locbf_D[a]) + i - (self.p[a] - 1)) % self.NbaseD[a]

                    self.int_loccof_N[a][i] = np.arange(self.n_int_locbf_N[a] - 1, -1, -1)
                    self.int_loccof_D[a][i] = np.arange(self.n_int_locbf_D[a] - 1, -1, -1)

                    if self.p[a] == 1:
                        self.x_int_indices[a][i] = i
                    else:
                        self.x_int_indices[a][i] = (np.arange(self.n_int[a]) + 2 * (i - (self.p[a] - 1))) % (
                            2 * self.Nel[a]
                        )

                    self.coeffi_indices[a][i] = 0

                    for j in range(2 * (self.p[a] - 1) + 1):
                        self.x_int[a][i, j] = (
                            (self.T[a][i + 1 + int(j / 2)] + self.T[a][i + 1 + int((j + 1) / 2)]) / 2
                        ) % 1.0

        # set histopolation points, quadrature points and weights
        n_lambda_his = [np.copy(NbaseD) for NbaseD in self.NbaseD]  # number of coefficients in space V1

        self.n_his = [2 * p for p in self.p]  # number of histopolation intervals
        self.n_his_locbf_N = [2 * p for p in self.p]  # number of non-vanishing N bf in histopolation interval
        self.n_his_locbf_D = [2 * p - 1 for p in self.p]  # number of non-vanishing D bf in histopolation interval

        self.x_his = [
            np.zeros((n_lambda_his, n_his + 1), dtype=float) for n_lambda_his, n_his in zip(n_lambda_his, self.n_his)
        ]

        self.his_global_N = [
            np.zeros((n_lambda_his, n_his_locbf_N), dtype=int)
            for n_lambda_his, n_his_locbf_N in zip(n_lambda_his, self.n_his_locbf_N)
        ]
        self.his_global_D = [
            np.zeros((n_lambda_his, n_his_locbf_D), dtype=int)
            for n_lambda_his, n_his_locbf_D in zip(n_lambda_his, self.n_his_locbf_D)
        ]

        self.his_loccof_N = [
            np.zeros((n_lambda_his, n_his_locbf_N), dtype=int)
            for n_lambda_his, n_his_locbf_N in zip(n_lambda_his, self.n_his_locbf_N)
        ]
        self.his_loccof_D = [
            np.zeros((n_lambda_his, n_his_locbf_D), dtype=int)
            for n_lambda_his, n_his_locbf_D in zip(n_lambda_his, self.n_his_locbf_D)
        ]

        self.x_his_indices = [
            np.zeros((n_lambda_his, n_his), dtype=int) for n_lambda_his, n_his in zip(n_lambda_his, self.n_his)
        ]
        self.coeffh_indices = [np.zeros(n_lambda_his, dtype=int) for n_lambda_his in n_lambda_his]

        self.pts = [0, 0, 0]
        self.wts = [0, 0, 0]

        self.n_his_nvcof_D = [None, None, None]
        self.n_his_nvcof_N = [None, None, None]

        self.his_add_D = [None, None, None]
        self.his_add_N = [None, None, None]

        self.his_shift_D = [0, 0, 0]
        self.his_shift_N = [0, 0, 0]

        for a in range(3):
            if self.bc[a] == False:
                # maximum number of non-vanishing coefficients
                self.n_his_nvcof_D[a] = 3 * self.p[a] - 2
                self.n_his_nvcof_N[a] = 3 * self.p[a] - 1

                # shift in local coefficient indices at right boundary (only for non-periodic boundary conditions)
                self.his_add_D[a] = np.arange(self.n_his[a] - 2) + 1
                self.his_add_N[a] = np.arange(self.n_his[a] - 1) + 1

                counter_D = 0
                counter_N = 0

                # shift local coefficients --> global coefficients (D)
                self.his_shift_D[a] = np.arange(self.NbaseD[a]) - (self.p[a] - 1)
                self.his_shift_D[a][: 2 * self.p[a] - 1] = 0
                self.his_shift_D[a][-(2 * self.p[a] - 1) :] = self.his_shift_D[a][-(2 * self.p[a] - 1)]

                # shift local coefficients --> global coefficients (N)
                self.his_shift_N[a] = np.arange(self.NbaseN[a]) - self.p[a]
                self.his_shift_N[a][: 2 * self.p[a]] = 0
                self.his_shift_N[a][-2 * self.p[a] :] = self.his_shift_N[a][-2 * self.p[a]]

                counter_coeffh = np.copy(self.p[a])

                for i in range(n_lambda_his[a]):
                    # left boundary region
                    if i < self.p[a] - 1:
                        self.his_global_N[a][i] = np.arange(self.n_his_locbf_N[a])
                        self.his_global_D[a][i] = np.arange(self.n_his_locbf_D[a])

                        self.x_his_indices[a][i] = np.arange(self.n_his[a])
                        self.coeffh_indices[a][i] = i
                        for j in range(2 * self.p[a] + 1):
                            xi = self.p[a] - 1
                            self.x_his[a][i, j] = (
                                self.T[a][xi + 1 + int(j / 2)] + self.T[a][xi + 1 + int((j + 1) / 2)]
                            ) / 2

                    # right boundary region
                    elif i > n_lambda_his[a] - self.p[a]:
                        self.his_global_N[a][i] = (
                            np.arange(self.n_his_locbf_N[a]) + n_lambda_his[a] - self.p[a] - (self.p[a] - 1)
                        )
                        self.his_global_D[a][i] = (
                            np.arange(self.n_his_locbf_D[a]) + n_lambda_his[a] - self.p[a] - (self.p[a] - 1)
                        )

                        self.x_his_indices[a][i] = np.arange(self.n_his[a]) + 2 * (
                            n_lambda_his[a] - self.p[a] - (self.p[a] - 1)
                        )
                        self.coeffh_indices[a][i] = counter_coeffh
                        counter_coeffh += 1
                        for j in range(2 * self.p[a] + 1):
                            xi = n_lambda_his[a] - self.p[a]
                            self.x_his[a][i, j] = (
                                self.T[a][xi + 1 + int(j / 2)] + self.T[a][xi + 1 + int((j + 1) / 2)]
                            ) / 2

                    # interior
                    else:
                        self.his_global_N[a][i] = np.arange(self.n_his_locbf_N[a]) + i - (self.p[a] - 1)
                        self.his_global_D[a][i] = np.arange(self.n_his_locbf_D[a]) + i - (self.p[a] - 1)

                        self.x_his_indices[a][i] = np.arange(self.n_his[a]) + 2 * (i - (self.p[a] - 1))
                        self.coeffh_indices[a][i] = self.p[a] - 1
                        for j in range(2 * self.p[a] + 1):
                            self.x_his[a][i, j] = (
                                self.T[a][i + 1 + int(j / 2)] + self.T[a][i + 1 + int((j + 1) / 2)]
                            ) / 2

                    # local coefficient index
                    if i > 0:
                        for il in range(self.n_his_locbf_D[a]):
                            k_glob_new = self.his_global_D[a][i, il]
                            bol = k_glob_new == self.his_global_D[a][i - 1]

                            if np.any(bol):
                                self.his_loccof_D[a][i, il] = self.his_loccof_D[a][i - 1, np.where(bol)[0][0]] + 1

                            if (k_glob_new >= n_lambda_his[a] - self.p[a] - (self.p[a] - 2)) and (
                                self.his_loccof_D[a][i, il] == 0
                            ):
                                self.his_loccof_D[a][i, il] = self.his_add_D[a][counter_D]
                                counter_D += 1

                        for il in range(self.n_his_locbf_N[a]):
                            k_glob_new = self.his_global_N[a][i, il]
                            bol = k_glob_new == self.his_global_N[a][i - 1]

                            if np.any(bol):
                                self.his_loccof_N[a][i, il] = self.his_loccof_N[a][i - 1, np.where(bol)[0][0]] + 1

                            if (k_glob_new >= n_lambda_his[a] - self.p[a] - (self.p[a] - 2)) and (
                                self.his_loccof_N[a][i, il] == 0
                            ):
                                self.his_loccof_N[a][i, il] = self.his_add_N[a][counter_N]
                                counter_N += 1

                # quadrature points and weights
                self.pts[a], self.wts[a] = bsp.quadrature_grid(
                    np.unique(self.x_his[a].flatten()), self.pts_loc[a], self.wts_loc[a]
                )

            else:
                # maximum number of non-vanishing coefficients
                self.n_his_nvcof_D[a] = 2 * self.p[a] - 1
                self.n_his_nvcof_N[a] = 2 * self.p[a]

                # shift local coefficients --> global coefficients (D)
                self.his_shift_D[a] = np.arange(self.NbaseD[a]) - (self.p[a] - 1)

                # shift local coefficients --> global coefficients (N)
                self.his_shift_N[a] = np.arange(self.NbaseD[a]) - self.p[a]

                for i in range(n_lambda_his[a]):
                    self.his_global_N[a][i] = (np.arange(self.n_his_locbf_N[a]) + i - (self.p[a] - 1)) % self.NbaseN[a]
                    self.his_global_D[a][i] = (np.arange(self.n_his_locbf_D[a]) + i - (self.p[a] - 1)) % self.NbaseD[a]
                    self.his_loccof_N[a][i] = np.arange(self.n_his_locbf_N[a] - 1, -1, -1)
                    self.his_loccof_D[a][i] = np.arange(self.n_his_locbf_D[a] - 1, -1, -1)

                    self.x_his_indices[a][i] = (np.arange(self.n_his[a]) + 2 * (i - (self.p[a] - 1))) % (
                        2 * self.Nel[a]
                    )
                    self.coeffh_indices[a][i] = 0

                    for j in range(2 * self.p[a] + 1):
                        self.x_his[a][i, j] = (self.T[a][i + 1 + int(j / 2)] + self.T[a][i + 1 + int((j + 1) / 2)]) / 2

                # quadrature points and weights
                self.pts[a], self.wts[a] = bsp.quadrature_grid(
                    np.append(np.unique(self.x_his[a].flatten() % 1.0), 1.0), self.pts_loc[a], self.wts_loc[a]
                )

    # projector on space V0 (interpolation)
    def pi_0(self, fun, include_bc=True, eval_kind="meshgrid"):
        """
        Local projector on the discrete space V0.

        Parameters
        ----------
        fun : callable
            the function (0-form) to be projected.

        include_bc : boolean
            whether the boundary coefficients in the first logical direction are included

        eval_kind : string
            kind of evaluation of function at interpolation/quadrature points ('meshgrid', 'tensor_product', 'point_wise')

        Returns
        -------
        lambdas : array_like
            the coefficients in V0 corresponding to the projected function
        """

        # interpolation points
        x_int1 = np.unique(self.x_int[0].flatten())
        x_int2 = np.unique(self.x_int[1].flatten())
        x_int3 = np.unique(self.x_int[2].flatten())

        # evaluation of function at interpolation points
        mat_f = np.empty((x_int1.size, x_int2.size, x_int3.size), dtype=float)

        # external function call if a callable is passed
        if callable(fun):
            # create a meshgrid and evaluate function on point set
            if eval_kind == "meshgrid":
                pts1, pts2, pts3 = np.meshgrid(x_int1, x_int2, x_int3, indexing="ij")
                mat_f[:, :, :] = fun(pts1, pts2, pts3)

            # tensor-product evaluation is done by input function
            elif eval_kind == "tensor_product":
                mat_f[:, :, :] = fun(x_int1, x_int2, x_int3)

            # point-wise evaluation
            else:
                for i1 in range(x_int1.size):
                    for i2 in range(x_int2.size):
                        for i3 in range(x_int3.size):
                            mat_f[i1, i2, i3] = fun(x_int1[i1], x_int2[i2], x_int3[i3])

        # internal function call
        else:
            print("no internal 3D function implemented!")

        # coefficients
        lambdas = np.zeros((self.NbaseN[0], self.NbaseN[1], self.NbaseN[2]), dtype=float)

        ker_loc.kernel_pi0_3d(
            self.NbaseN,
            self.p,
            self.coeff_i[0],
            self.coeff_i[1],
            self.coeff_i[2],
            self.coeffi_indices[0],
            self.coeffi_indices[1],
            self.coeffi_indices[2],
            self.x_int_indices[0],
            self.x_int_indices[1],
            self.x_int_indices[2],
            mat_f,
            lambdas,
        )

        return lambdas.flatten()

    # projector on space V1 ([histo, inter, inter], [inter, histo, inter], [inter, inter, histo])
    def pi_1(self, fun, include_bc=True, eval_kind="meshgrid"):
        """
        Local projector on the discrete space V1.

        Parameters
        ----------
        fun : list of callables
            the function (1-form) to be projected

        include_bc : boolean
            whether the boundary coefficients in the first logical direction are included

        eval_kind : string
            kind of evaluation of function at interpolation/quadrature points ('meshgrid', 'tensor_product', 'point_wise')

        Returns
        -------
        lambdas : list of array_like
            the coefficients in V1 corresponding to the projected function
        """

        # interpolation points
        x_int1 = np.unique(self.x_int[0].flatten())
        x_int2 = np.unique(self.x_int[1].flatten())
        x_int3 = np.unique(self.x_int[2].flatten())

        # ======== 1-component ========

        # evaluation of function at interpolation/quadrature points
        mat_f = np.empty((self.pts[0].flatten().size, x_int2.size, x_int3.size), dtype=float)

        # external function call if a callable is passed
        if callable(fun[0]):
            # create a meshgrid and evaluate function on point set
            if eval_kind == "meshgrid":
                pts1, pts2, pts3 = np.meshgrid(self.pts[0].flatten(), x_int2, x_int3, indexing="ij")
                mat_f[:, :, :] = fun[0](pts1, pts2, pts3)

            # tensor-product evaluation is done by input function
            elif eval_kind == "tensor_product":
                mat_f[:, :, :] = fun[0](self.pts[0].flatten(), x_int2, x_int3)

            # point-wise evaluation
            else:
                for i1 in range(self.pts[0].size):
                    for i2 in range(x_int2.size):
                        for i3 in range(x_int3.size):
                            mat_f[i1, i2, i3] = fun[0](self.pts[0].flatten()[i1], x_int2[i2], x_int3[i3])

        # internal function call
        else:
            print("no internal 3D function implemented!")

        # compute coefficients
        lambdas1 = np.zeros((self.NbaseD[0], self.NbaseN[1], self.NbaseN[2]), dtype=float)

        ker_loc.kernel_pi11_3d(
            [self.NbaseD[0], self.NbaseN[1], self.NbaseN[2]],
            self.p,
            self.n_quad,
            self.coeff_h[0],
            self.coeff_i[1],
            self.coeff_i[2],
            self.coeffh_indices[0],
            self.coeffi_indices[1],
            self.coeffi_indices[2],
            self.x_his_indices[0],
            self.x_int_indices[1],
            self.x_int_indices[2],
            self.wts[0],
            mat_f.reshape(self.pts[0].shape[0], self.pts[0].shape[1], x_int2.size, x_int3.size),
            lambdas1,
        )

        # ======== 2-component ========

        # evaluation of function at interpolation/quadrature points
        mat_f = np.empty((x_int1.size, self.pts[1].flatten().size, x_int3.size), dtype=float)

        # external function call if a callable is passed
        if callable(fun[1]):
            # create a meshgrid and evaluate function on point set
            if eval_kind == "meshgrid":
                pts1, pts2, pts3 = np.meshgrid(x_int1, self.pts[1].flatten(), x_int3, indexing="ij")
                mat_f[:, :, :] = fun[1](pts1, pts2, pts3)

            # tensor-product evaluation is done by input function
            elif eval_kind == "tensor_product":
                mat_f[:, :, :] = fun[1](x_int1, self.pts[1].flatten(), x_int3)

            # point-wise evaluation
            else:
                for i1 in range(x_int1.size):
                    for i2 in range(self.pts[1].size):
                        for i3 in range(x_int3.size):
                            mat_f[i1, i2, i3] = fun[1](x_int1[i1], self.pts[1].flatten()[i2], x_int3[i3])

        # internal function call
        else:
            print("no internal 3D function implemented!")

        # compute coefficients
        lambdas2 = np.zeros((self.NbaseN[0], self.NbaseD[1], self.NbaseN[2]), dtype=float)

        ker_loc.kernel_pi12_3d(
            [self.NbaseN[0], self.NbaseD[1], self.NbaseN[2]],
            self.p,
            self.n_quad,
            self.coeff_i[0],
            self.coeff_h[1],
            self.coeff_i[2],
            self.coeffi_indices[0],
            self.coeffh_indices[1],
            self.coeffi_indices[2],
            self.x_int_indices[0],
            self.x_his_indices[1],
            self.x_int_indices[2],
            self.wts[1],
            mat_f.reshape(x_int1.size, self.pts[1].shape[0], self.pts[1].shape[1], x_int3.size),
            lambdas2,
        )

        # ======== 3-component ========

        # evaluation of function at interpolation/quadrature points
        mat_f = np.empty((x_int1.size, x_int1.size, self.pts[2].flatten().size), dtype=float)

        # external function call if a callable is passed
        if callable(fun[2]):
            # create a meshgrid and evaluate function on point set
            if eval_kind == "meshgrid":
                pts1, pts2, pts3 = np.meshgrid(x_int1, x_int2, self.pts[2].flatten(), indexing="ij")
                mat_f[:, :, :] = fun[2](pts1, pts2, pts3)

            # tensor-product evaluation is done by input function
            elif eval_kind == "tensor_product":
                mat_f[:, :, :] = fun[2](x_int1, x_int2, self.pts[2].flatten())

            # point-wise evaluation
            else:
                for i1 in range(x_int1.size):
                    for i2 in range(xint2.size):
                        for i3 in range(self.pts[2].size):
                            mat_f[i1, i2, i3] = fun[2](x_int1[i1], x_int2[i2], self.pts[2].flatten()[i3])

        # internal function call
        else:
            print("no internal 3D function implemented!")

        # compute coefficients
        lambdas3 = np.zeros((self.NbaseN[0], self.NbaseN[1], self.NbaseD[2]), dtype=float)

        ker_loc.kernel_pi13_3d(
            [self.NbaseN[0], self.NbaseN[1], self.NbaseD[2]],
            self.p,
            self.n_quad,
            self.coeff_i[0],
            self.coeff_i[1],
            self.coeff_h[2],
            self.coeffi_indices[0],
            self.coeffi_indices[1],
            self.coeffh_indices[2],
            self.x_int_indices[0],
            self.x_int_indices[1],
            self.x_his_indices[2],
            self.wts[2],
            mat_f.reshape(x_int1.size, x_int2.size, self.pts[2][:, 0].shape[0], self.pts[2].shape[1]),
            lambdas3,
        )

        return np.concatenate((lambdas1.flatten(), lambdas2.flatten(), lambdas3.flatten()))

    # projector on space V1 ([inter, histo, histo], [histo, inter, histo], [histo, histo, inter])
    def pi_2(self, fun, include_bc=True, eval_kind="meshgrid"):
        """
        Local projector on the discrete space V2.

        Parameters
        ----------
        fun : list of callables
            the function (2-form) to be projected

        include_bc : boolean
            whether the boundary coefficients in the first logical direction are included

        eval_kind : string
            kind of evaluation of function at interpolation/quadrature points ('meshgrid', 'tensor_product', 'point_wise')

        Returns
        -------
        lambdas : list of array_like
            the coefficients in V2 corresponding to the projected function
        """

        # interpolation points
        x_int1 = np.unique(self.x_int[0].flatten())
        x_int2 = np.unique(self.x_int[1].flatten())
        x_int3 = np.unique(self.x_int[2].flatten())

        # ======== 1-component ========

        # evaluation of function at interpolation/quadrature points
        mat_f = np.empty((x_int1.size, self.pts[1].flatten().size, self.pts[2].flatten().size), dtype=float)

        # external function call if a callable is passed
        if callable(fun[0]):
            # create a meshgrid and evaluate function on point set
            if eval_kind == "meshgrid":
                pts1, pts2, pts3 = np.meshgrid(x_int1, self.pts[1].flatten(), self.pts[2].flatten(), indexing="ij")
                mat_f[:, :, :] = fun[0](pts1, pts2, pts3)

            # tensor-product evaluation is done by input function
            elif eval_kind == "tensor_product":
                mat_f[:, :, :] = fun[0](x_int1, self.pts[1].flatten(), self.pts[2].flatten())

            # point-wise evaluation
            else:
                for i1 in range(x_int1.size):
                    for i2 in range(self.pts[1].size):
                        for i3 in range(self.pts[2].size):
                            mat_f[i1, i2, i3] = fun[0](x_int1[i1], self.pts[1].flatten()[i2], self.pts[2].flatten()[i3])

        # internal function call
        else:
            print("no internal 3D function implemented!")

        # compute coefficients
        lambdas1 = np.zeros((self.NbaseN[0], self.NbaseD[1], self.NbaseD[2]), dtype=float)

        ker_loc.kernel_pi21_3d(
            [self.NbaseN[0], self.NbaseD[1], self.NbaseD[2]],
            self.p,
            self.n_quad,
            self.coeff_i[0],
            self.coeff_h[1],
            self.coeff_h[2],
            self.coeffi_indices[0],
            self.coeffh_indices[1],
            self.coeffh_indices[2],
            self.x_int_indices[0],
            self.x_his_indices[1],
            self.x_his_indices[2],
            self.wts[1],
            self.wts[2],
            mat_f.reshape(
                x_int1.size, self.pts[1].shape[0], self.pts[1].shape[1], self.pts[2].shape[0], self.pts[2].shape[1]
            ),
            lambdas1,
        )

        # ======== 2-component ========

        # evaluation of function at interpolation/quadrature points
        mat_f = np.empty((self.pts[0].flatten().size, x_int2.size, self.pts[2].flatten().size), dtype=float)

        # external function call if a callable is passed
        if callable(fun[1]):
            # create a meshgrid and evaluate function on point set
            if eval_kind == "meshgrid":
                pts1, pts2, pts3 = np.meshgrid(self.pts[0].flatten(), x_int2, self.pts[2].flatten(), indexing="ij")
                mat_f[:, :, :] = fun[1](pts1, pts2, pts3)

            # tensor-product evaluation is done by input function
            elif eval_kind == "tensor_product":
                mat_f[:, :, :] = fun[1](self.pts[0].flatten(), x_int2, self.pts[2].flatten())

            # point-wise evaluation
            else:
                for i1 in range(self.pts[0].size):
                    for i2 in range(x_int2.size):
                        for i3 in range(self.pts[2].size):
                            mat_f[i1, i2, i3] = fun[1](self.pts[0].flatten()[i1], x_int2[i2], self.pts[2].flatten()[i3])

        # internal function call
        else:
            print("no internal 3D function implemented!")

        # compute coefficients
        lambdas2 = np.zeros((self.NbaseD[0], self.NbaseN[1], self.NbaseD[2]), dtype=float)

        ker_loc.kernel_pi22_3d(
            [self.NbaseD[0], self.NbaseN[1], self.NbaseD[2]],
            self.p,
            self.n_quad,
            self.coeff_h[0],
            self.coeff_i[1],
            self.coeff_h[2],
            self.coeffh_indices[0],
            self.coeffi_indices[1],
            self.coeffh_indices[2],
            self.x_his_indices[0],
            self.x_int_indices[1],
            self.x_his_indices[2],
            self.wts[0],
            self.wts[2],
            mat_f.reshape(
                self.pts[0].shape[0], self.pts[0].shape[1], x_int2.size, self.pts[2].shape[0], self.pts[2].shape[1]
            ),
            lambdas2,
        )

        # ======== 3-component ========

        # evaluation of function at interpolation/quadrature points
        mat_f = np.empty((self.pts[0].flatten().size, self.pts[1].flatten().size, x_int3.size), dtype=float)

        # external function call if a callable is passed
        if callable(fun[2]):
            # create a meshgrid and evaluate function on point set
            if eval_kind == "meshgrid":
                pts1, pts2, pts3 = np.meshgrid(self.pts[0].flatten(), self.pts[1].flatten(), x_int3, indexing="ij")
                mat_f[:, :, :] = fun[2](pts1, pts2, pts3)

            # tensor-product evaluation is done by input function
            elif eval_kind == "tensor_product":
                mat_f[:, :, :] = fun[2](self.pts[0].flatten(), self.pts[1].flatten(), x_int3)

            # point-wise evaluation
            else:
                for i1 in range(self.pts[0].size):
                    for i2 in range(self.pts[1].size):
                        for i3 in range(x_int3.size):
                            mat_f[i1, i2, i3] = fun[2](self.pts[0].flatten()[i1], self.pts[1].flatten()[i2], x_int3[i3])

        # internal function call
        else:
            print("no internal 3D function implemented!")

        # compute coefficients
        lambdas3 = np.zeros((self.NbaseD[0], self.NbaseD[1], self.NbaseN[2]), dtype=float)

        ker_loc.kernel_pi23_3d(
            [self.NbaseD[0], self.NbaseD[1], self.NbaseN[2]],
            self.p,
            self.n_quad,
            self.coeff_h[0],
            self.coeff_h[1],
            self.coeff_i[2],
            self.coeffh_indices[0],
            self.coeffh_indices[1],
            self.coeffi_indices[2],
            self.x_his_indices[0],
            self.x_his_indices[1],
            self.x_int_indices[2],
            self.wts[0],
            self.wts[1],
            mat_f.reshape(
                self.pts[0].shape[0], self.pts[0].shape[1], self.pts[1].shape[0], self.pts[1].shape[1], x_int3.size
            ),
            lambdas3,
        )

        return np.concatenate((lambdas1.flatten(), lambdas2.flatten(), lambdas3.flatten()))

    # projector on space V3 (histopolation)
    def pi_3(self, fun, include_bc=True, eval_kind="meshgrid"):
        """
        Local projector on the discrete space V3.

        Parameters
        ----------
        fun : callable
            the function (3-form) to be projected

        include_bc : boolean
            whether the boundary coefficients in the first logical direction are included

        eval_kind : string
            kind of evaluation of function at interpolation/quadrature points ('meshgrid', 'tensor_product', 'point_wise')

        Returns
        -------
        lambdas : array_like
            the coefficients in V3 corresponding to the projected function
        """

        # evaluation of function at quadrature points
        mat_f = np.empty(
            (self.pts[0].flatten().size, self.pts[1].flatten().size, self.pts[2].flatten().size), dtype=float
        )

        # external function call if a callable is passed
        if callable(fun):
            # create a meshgrid and evaluate function on point set
            if eval_kind == "meshgrid":
                pts1, pts2, pts3 = np.meshgrid(
                    self.pts[0].flatten(), self.pts[1].flatten(), self.pts[2].flatten(), indexing="ij"
                )
                mat_f[:, :, :] = fun(pts1, pts2, pts3)

            # tensor-product evaluation is done by input function
            elif eval_kind == "tensor_product":
                mat_f[:, :, :] = fun(self.pts[0].flatten(), self.pts[1].flatten(), self.pts[2].flatten())

            # point-wise evaluation
            else:
                for i1 in range(self.pts[0].size):
                    for i2 in range(self.pts[1].size):
                        for i3 in range(self.pts[2].size):
                            mat_f[i1, i2, i3] = fun(
                                self.pts[0].flatten()[i1], self.pts[1].flatten()[i2], self.pts[2].flatten()[i3]
                            )

        # internal function call
        else:
            print("no internal 3D function implemented!")

        # compute coefficients
        lambdas = np.zeros((self.NbaseD[0], self.NbaseD[1], self.NbaseD[2]), dtype=float)

        ker_loc.kernel_pi3_3d(
            self.NbaseD,
            self.p,
            self.n_quad,
            self.coeff_h[0],
            self.coeff_h[1],
            self.coeff_h[2],
            self.coeffh_indices[0],
            self.coeffh_indices[1],
            self.coeffh_indices[2],
            self.x_his_indices[0],
            self.x_his_indices[1],
            self.x_his_indices[2],
            self.wts[0],
            self.wts[1],
            self.wts[2],
            mat_f.reshape(
                self.pts[0].shape[0],
                self.pts[0].shape[1],
                self.pts[1].shape[0],
                self.pts[1].shape[1],
                self.pts[2].shape[0],
                self.pts[2].shape[1],
            ),
            lambdas,
        )

        return lambdas.flatten()
