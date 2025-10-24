# coding: utf-8
#
# Copyright 2020 Florian Holderied

"""
Modules to compute inner products with given functions in 2D.
"""

import scipy.sparse as spa

import struphy.eigenvalue_solvers.kernels_2d as ker
from struphy.utils.arrays import xp as np


# ================ inner product in V0 ===========================
def inner_prod_V0(tensor_space_FEM, domain, fun):
    """
    Assembles the 2D inner product [NN] * fun * |det(DF)|  of the given tensor product B-spline space of bi-degree (p1, p2) within a computational domain defined by the given object "domain" from struphy.geometry.domain.

    Parameters
    ----------
    tensor_space_FEM : Tensor_spline_space
        tensor product B-spline space for finite element spaces

    domain : domain
        domain object defining the geometry

    fun : callable or np.ndarray
        the 0-form with which the inner products shall be computed (either callable or 2D array with values at quadrature points)
    """

    p = tensor_space_FEM.p  # spline degrees
    Nel = tensor_space_FEM.Nel  # number of elements
    indN = (
        tensor_space_FEM.indN
    )  # global indices of local non-vanishing basis functions in format (element, global index)

    n_quad = tensor_space_FEM.n_quad  # number of quadrature points per element
    pts = tensor_space_FEM.pts  # global quadrature points in format (element, local quad_point)
    wts = tensor_space_FEM.wts  # global quadrature weights in format (element, local weight)

    basisN = tensor_space_FEM.basisN  # evaluated basis functions at quadrature points

    # evaluation of |det(DF)| at eta3 = 0 and quadrature points in format (Nel1, nq1, Nel2, nq2)
    det_df = abs(domain.jacobian_det(pts[0].flatten(), pts[1].flatten(), 0.0))
    det_df = det_df.reshape(Nel[0], n_quad[0], Nel[1], n_quad[1])

    # evaluation of given 0-form at quadrature points
    mat_f = np.empty((pts[0].size, pts[1].size), dtype=float)

    if callable(fun):
        quad_mesh = np.meshgrid(pts[0].flatten(), pts[1].flatten(), indexing="ij")
        mat_f[:, :] = fun(quad_mesh[0], quad_mesh[1], 0.0)
    else:
        mat_f[:, :] = fun

    # assembly
    Ni = tensor_space_FEM.Nbase_0form

    F = np.zeros((Ni[0], Ni[1]), dtype=float)

    mat_f = mat_f.reshape(Nel[0], n_quad[0], Nel[1], n_quad[1])

    ker.kernel_inner(
        Nel[0],
        Nel[1],
        p[0],
        p[1],
        n_quad[0],
        n_quad[1],
        0,
        0,
        wts[0],
        wts[1],
        basisN[0],
        basisN[1],
        indN[0],
        indN[1],
        F,
        mat_f * det_df,
    )

    return tensor_space_FEM.E0_0.dot(F.flatten())


# ================ inner product in V1 ===========================
def inner_prod_V1(tensor_space_FEM, domain, fun):
    """
    Assembles the 2D inner prodcut [DN, ND, NN] * |det(DF)| * G^(-1) * [fun_1, fun_2, fun_3] of the given tensor product B-spline space of bi-degree (p1, p2) within a computational domain defined by the given object "domain" from struphy.geometry.domain.

    tensor_space_FEM : Tensor_spline_space
        tensor product B-spline space for finite element spaces

    domain : domain
        domain object defining the geometry

    fun : list of callables or np.ndarrays
        the 1-form components with which the inner products shall be computed (either list of 3 callables or 2D arrays with values at quadrature points)
    """

    p = tensor_space_FEM.p  # spline degrees
    Nel = tensor_space_FEM.Nel  # number of elements
    indN = (
        tensor_space_FEM.indN
    )  # global indices of non-vanishing basis functions (N) in format (element, global index)
    indD = (
        tensor_space_FEM.indD
    )  # global indices of non-vanishing basis functions (D) in format (element, global index)

    n_quad = tensor_space_FEM.n_quad  # number of quadrature points per element
    pts = tensor_space_FEM.pts  # global quadrature points
    wts = tensor_space_FEM.wts  # global quadrature weights

    basisN = tensor_space_FEM.basisN  # evaluated basis functions at quadrature points (N)
    basisD = tensor_space_FEM.basisD  # evaluated basis functions at quadrature points (D)

    # indices and basis functions of components of a 1-form
    ind = [[indD[0], indN[1]], [indN[0], indD[1]], [indN[0], indN[1]]]
    basis = [[basisD[0], basisN[1]], [basisN[0], basisD[1]], [basisN[0], basisN[1]]]
    ns = [[1, 0], [0, 1], [0, 0]]

    # evaluation of |det(DF)| at eta3 = 0 and quadrature points in format (Nel1, nq1, Nel2, nq2)
    det_df = abs(domain.jacobian_det(pts[0].flatten(), pts[1].flatten(), 0.0))
    det_df = det_df.reshape(Nel[0], n_quad[0], Nel[1], n_quad[1])

    # evaluation of G^(-1) at eta3 = 0 and quadrature points in format (3, 3, Nel1*nq1, Nel2*nq2)
    g_inv = domain.metric_inv(pts[0].flatten(), pts[1].flatten(), 0.0)

    # 1-form components at quadrature points
    mat_f = np.empty((pts[0].size, pts[1].size), dtype=float)

    if callable(fun[0]):
        quad_mesh = np.meshgrid(pts[0].flatten(), pts[1].flatten(), indexing="ij")

    # components of global inner product
    F = [0, 0, 0]

    # assembly
    for a in range(3):
        Ni = tensor_space_FEM.Nbase_1form[a]
        F[a] = np.zeros((Ni[0], Ni[1]), dtype=float)

        mat_f[:, :] = 0.0

        for b in range(3):
            # evaluate g^ab * f_b at quadrature points
            if callable(fun[b]):
                mat_f += fun[b](quad_mesh[0], quad_mesh[1], 0.0) * g_inv[a, b]
            else:
                mat_f += fun[b] * g_inv[a, b]

        mat_f = mat_f.reshape(Nel[0], n_quad[0], Nel[1], n_quad[1])

        ker.kernel_inner(
            Nel[0],
            Nel[1],
            p[0],
            p[1],
            n_quad[0],
            n_quad[1],
            ns[a][0],
            ns[a][1],
            wts[0],
            wts[1],
            basis[a][0],
            basis[a][1],
            ind[a][0],
            ind[a][1],
            F[a],
            mat_f * det_df,
        )

    F1 = tensor_space_FEM.E1_pol_0.dot(np.concatenate((F[0].flatten(), F[1].flatten())))
    F2 = tensor_space_FEM.E0_pol_0.dot(F[2].flatten())

    return F1, F2


# ================ inner product in V2 ===========================
def inner_prod_V2(tensor_space_FEM, domain, fun):
    """
    Assembles the 2D inner product [ND, DN, DD] / |det(DF)| * G * [fun_1, fun_2, fun_3] of the given tensor product B-spline space of bi-degree (p1, p2) within a computational domain defined by the given object "domain" from struphy.geometry.domain.

    tensor_space_FEM : Tensor_spline_space
        tensor product B-spline space for finite element spaces

    domain : domain
        domain object defining the geometry

    fun : list of callables or np.ndarrays
        the 2-form components with which the inner products shall be computed (either list of 3 callables or 2D arrays with values at quadrature points)
    """

    p = tensor_space_FEM.p  # spline degrees
    Nel = tensor_space_FEM.Nel  # number of elements
    indN = (
        tensor_space_FEM.indN
    )  # global indices of non-vanishing basis functions (N) in format (element, global index)
    indD = (
        tensor_space_FEM.indD
    )  # global indices of non-vanishing basis functions (D) in format (element, global index)

    n_quad = tensor_space_FEM.n_quad  # number of quadrature points per element
    pts = tensor_space_FEM.pts  # global quadrature points
    wts = tensor_space_FEM.wts  # global quadrature weights

    basisN = tensor_space_FEM.basisN  # evaluated basis functions at quadrature points (N)
    basisD = tensor_space_FEM.basisD  # evaluated basis functions at quadrature points (D)

    # indices and basis functions of components of a 2-form
    ind = [[indN[0], indD[1]], [indD[0], indN[1]], [indD[0], indD[1]]]
    basis = [[basisN[0], basisD[1]], [basisD[0], basisN[1]], [basisD[0], basisD[1]]]
    ns = [[0, 1], [1, 0], [1, 1]]

    # evaluation of |det(DF)| at eta3 = 0 and quadrature points in format (Nel1, nq1, Nel2, nq2)
    det_df = abs(domain.jacobian_det(pts[0].flatten(), pts[1].flatten(), 0.0))
    det_df = det_df.reshape(Nel[0], n_quad[0], Nel[1], n_quad[1])

    # evaluation of G at eta3 = 0 and quadrature points in format (3, 3, Nel1*nq1, Nel2*nq2)
    g = domain.metric(pts[0].flatten(), pts[1].flatten(), 0.0)

    # 2-form components at quadrature points
    mat_f = np.empty((pts[0].size, pts[1].size), dtype=float)

    if callable(fun[0]):
        quad_mesh = np.meshgrid(pts[0].flatten(), pts[1].flatten(), indexing="ij")

    # components of global inner product
    F = [0, 0, 0]

    # assembly
    for a in range(3):
        Ni = tensor_space_FEM.Nbase_2form[a]
        F[a] = np.zeros((Ni[0], Ni[1]), dtype=float)

        mat_f[:, :] = 0.0

        for b in range(3):
            # evaluate g_ab * f_b at quadrature points
            if callable(fun[b]):
                mat_f += fun[b](quad_mesh[0], quad_mesh[1], 0.0) * g[a, b]
            else:
                mat_f += fun[b] * g[a, b]

        mat_f = mat_f.reshape(Nel[0], n_quad[0], Nel[1], n_quad[1])

        ker.kernel_inner(
            Nel[0],
            Nel[1],
            p[0],
            p[1],
            n_quad[0],
            n_quad[1],
            ns[a][0],
            ns[a][1],
            wts[0],
            wts[1],
            basis[a][0],
            basis[a][1],
            ind[a][0],
            ind[a][1],
            F[a],
            mat_f / det_df,
        )

    F1 = tensor_space_FEM.E2_pol_0.dot(np.concatenate((F[0].flatten(), F[1].flatten())))
    F2 = tensor_space_FEM.E3_pol_0.dot(F[2].flatten())

    return F1, F2


# ================ inner product in V3 ===========================
def inner_prod_V3(tensor_space_FEM, domain, fun):
    """
    Assembles the 2D inner product [DD] * fun / |det(DF)| of the given tensor product B-spline space of bi-degree (p1, p2) within a computational domain defined by the given object "domain" from struphy.geometry.domain.

    tensor_space_FEM : Tensor_spline_space
        tensor product B-spline space for finite element spaces

    domain : domain
        domain object defining the geometry

    fun : callable or np.ndarray
        the 3-form component with which the inner products shall be computed (either callable or 2D array with values at quadrature points)
    """

    p = tensor_space_FEM.p  # spline degrees
    Nel = tensor_space_FEM.Nel  # number of elements
    indD = (
        tensor_space_FEM.indD
    )  # global indices of local non-vanishing basis functions in format (element, global index)

    n_quad = tensor_space_FEM.n_quad  # number of quadrature points per element
    pts = tensor_space_FEM.pts  # global quadrature points in format (element, local quad_point)
    wts = tensor_space_FEM.wts  # global quadrature weights in format (element, local weight)

    basisD = tensor_space_FEM.basisD  # evaluated basis functions at quadrature points

    # evaluation of |det(DF)| at eta3 = 0 and quadrature points in format (Nel1, nq1, Nel2, nq2)
    det_df = abs(domain.jacobian_det(pts[0].flatten(), pts[1].flatten(), 0.0))
    det_df = det_df.reshape(Nel[0], n_quad[0], Nel[1], n_quad[1])

    # evaluation of given 3-form at quadrature points
    mat_f = np.empty((pts[0].size, pts[1].size), dtype=float)

    if callable(fun):
        quad_mesh = np.meshgrid(pts[0].flatten(), pts[1].flatten(), indexing="ij")
        mat_f[:, :] = fun(quad_mesh[0], quad_mesh[1], 0.0)
    else:
        mat_f[:, :] = fun

    # assembly
    Ni = tensor_space_FEM.Nbase_3form

    F = np.zeros((Ni[0], Ni[1]), dtype=float)

    mat_f = mat_f.reshape(Nel[0], n_quad[0], Nel[1], n_quad[1])

    ker.kernel_inner(
        Nel[0],
        Nel[1],
        p[0],
        p[1],
        n_quad[0],
        n_quad[1],
        1,
        1,
        wts[0],
        wts[1],
        basisD[0],
        basisD[1],
        indD[0],
        indD[1],
        F,
        mat_f / det_df,
    )

    return tensor_space_FEM.E3_0.dot(F.flatten())
