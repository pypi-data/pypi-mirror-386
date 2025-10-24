# ========================================================
def kernel_pi0(
    n: "int[:]",
    n_int: "int[:]",
    n_nvbf: "int[:]",
    i_glo1: "int[:,:]",
    i_glo2: "int[:,:]",
    i_glo3: "int[:,:]",
    c_loc1: "int[:,:]",
    c_loc2: "int[:,:]",
    c_loc3: "int[:,:]",
    coeff1: "float[:,:]",
    coeff2: "float[:,:]",
    coeff3: "float[:,:]",
    coeff_ind1: "int[:]",
    coeff_ind2: "int[:]",
    coeff_ind3: "int[:]",
    bs1: "float[:,:]",
    bs2: "float[:,:]",
    bs3: "float[:,:]",
    x_int_ind1: "int[:,:]",
    x_int_ind2: "int[:,:]",
    x_int_ind3: "int[:,:]",
    tau: "float[:,:,:,:,:,:]",
    mat_eq: "float[:,:,:]",
):
    tau[:, :, :, :, :, :] = 0.0

    # -- removed omp: #$ omp parallel
    # -- removed omp: #$ omp do reduction ( + : tau) private (i1, i2, i3, j1, j2, j3, coeff, kl1, k1, c1, kl2, k2, c2, kl3, k3, c3, basis)
    for i1 in range(n[0]):
        for i2 in range(n[1]):
            for i3 in range(n[2]):
                for j1 in range(n_int[0]):
                    for j2 in range(n_int[1]):
                        for j3 in range(n_int[2]):
                            coeff = coeff1[coeff_ind1[i1], j1] * coeff2[coeff_ind2[i2], j2] * coeff3[coeff_ind3[i3], j3]

                            for kl1 in range(n_nvbf[0]):
                                k1 = i_glo1[i1, kl1]
                                c1 = c_loc1[i1, kl1]

                                for kl2 in range(n_nvbf[1]):
                                    k2 = i_glo2[i2, kl2]
                                    c2 = c_loc2[i2, kl2]

                                    for kl3 in range(n_nvbf[2]):
                                        k3 = i_glo3[i3, kl3]
                                        c3 = c_loc3[i3, kl3]

                                        basis = (
                                            bs1[x_int_ind1[i1, j1], k1]
                                            * bs2[x_int_ind2[i2, j2], k2]
                                            * bs3[x_int_ind3[i3, j3], k3]
                                        )

                                        tau[k1, k2, k3, c1, c2, c3] += (
                                            coeff
                                            * basis
                                            * mat_eq[x_int_ind1[i1, j1], x_int_ind2[i2, j2], x_int_ind3[i3, j3]]
                                        )
    # -- removed omp: #$ omp end do
    # -- removed omp: #$ omp end parallel

    ierr = 0


# ========================================================
def kernel_pi1_1(
    n: "int[:]",
    n_quad1: "int",
    n_inthis: "int[:]",
    n_nvbf: "int[:]",
    i_glo1: "int[:,:]",
    i_glo2: "int[:,:]",
    i_glo3: "int[:,:]",
    c_loc1: "int[:,:]",
    c_loc2: "int[:,:]",
    c_loc3: "int[:,:]",
    coeff1: "float[:,:]",
    coeff2: "float[:,:]",
    coeff3: "float[:,:]",
    coeff_ind1: "int[:]",
    coeff_ind2: "int[:]",
    coeff_ind3: "int[:]",
    bs1: "float[:,:,:]",
    bs2: "float[:,:]",
    bs3: "float[:,:]",
    x_his_ind1: "int[:,:]",
    x_int_ind2: "int[:,:]",
    x_int_ind3: "int[:,:]",
    wts1: "float[:,:]",
    tau: "float[:,:,:,:,:,:]",
    mat_eq: "float[:,:,:,:]",
):
    tau[:, :, :, :, :, :] = 0.0

    # -- removed omp: #$ omp parallel
    # -- removed omp: #$ omp do reduction ( + : tau) private (i1, i2, i3, j1, j2, j3, coeff, kl1, k1, c1, kl2, k2, c2, kl3, k3, c3, f_int, q1)
    for i1 in range(n[0]):
        for i2 in range(n[1]):
            for i3 in range(n[2]):
                for j1 in range(n_inthis[0]):
                    for j2 in range(n_inthis[1]):
                        for j3 in range(n_inthis[2]):
                            coeff = coeff1[coeff_ind1[i1], j1] * coeff2[coeff_ind2[i2], j2] * coeff3[coeff_ind3[i3], j3]

                            for kl1 in range(n_nvbf[0]):
                                k1 = i_glo1[i1, kl1]
                                c1 = c_loc1[i1, kl1]

                                for kl2 in range(n_nvbf[1]):
                                    k2 = i_glo2[i2, kl2]
                                    c2 = c_loc2[i2, kl2]

                                    for kl3 in range(n_nvbf[2]):
                                        k3 = i_glo3[i3, kl3]
                                        c3 = c_loc3[i3, kl3]

                                        f_int = 0.0

                                        for q1 in range(n_quad1):
                                            f_int += (
                                                wts1[x_his_ind1[i1, j1], q1]
                                                * bs1[x_his_ind1[i1, j1], q1, k1]
                                                * bs2[x_int_ind2[i2, j2], k2]
                                                * bs3[x_int_ind3[i3, j3], k3]
                                                * mat_eq[x_his_ind1[i1, j1], q1, x_int_ind2[i2, j2], x_int_ind3[i3, j3]]
                                            )

                                        tau[k1, k2, k3, c1, c2, c3] += coeff * f_int
    # -- removed omp: #$ omp end do
    # -- removed omp: #$ omp end parallel

    ierr = 0


# ========================================================
def kernel_pi1_2(
    n: "int[:]",
    n_quad2: "int",
    n_inthis: "int[:]",
    n_nvbf: "int[:]",
    i_glo1: "int[:,:]",
    i_glo2: "int[:,:]",
    i_glo3: "int[:,:]",
    c_loc1: "int[:,:]",
    c_loc2: "int[:,:]",
    c_loc3: "int[:,:]",
    coeff1: "float[:,:]",
    coeff2: "float[:,:]",
    coeff3: "float[:,:]",
    coeff_ind1: "int[:]",
    coeff_ind2: "int[:]",
    coeff_ind3: "int[:]",
    bs1: "float[:,:]",
    bs2: "float[:,:,:]",
    bs3: "float[:,:]",
    x_int_ind1: "int[:,:]",
    x_his_ind2: "int[:,:]",
    x_int_ind3: "int[:,:]",
    wts2: "float[:,:]",
    tau: "float[:,:,:,:,:,:]",
    mat_eq: "float[:,:,:,:]",
):
    tau[:, :, :, :, :, :] = 0.0

    # -- removed omp: #$ omp parallel
    # -- removed omp: #$ omp do reduction ( + : tau) private (i1, i2, i3, j1, j2, j3, coeff, kl1, k1, c1, kl2, k2, c2, kl3, k3, c3, f_int, q2)
    for i1 in range(n[0]):
        for i2 in range(n[1]):
            for i3 in range(n[2]):
                for j1 in range(n_inthis[0]):
                    for j2 in range(n_inthis[1]):
                        for j3 in range(n_inthis[2]):
                            coeff = coeff1[coeff_ind1[i1], j1] * coeff2[coeff_ind2[i2], j2] * coeff3[coeff_ind3[i3], j3]

                            for kl1 in range(n_nvbf[0]):
                                k1 = i_glo1[i1, kl1]
                                c1 = c_loc1[i1, kl1]

                                for kl2 in range(n_nvbf[1]):
                                    k2 = i_glo2[i2, kl2]
                                    c2 = c_loc2[i2, kl2]

                                    for kl3 in range(n_nvbf[2]):
                                        k3 = i_glo3[i3, kl3]
                                        c3 = c_loc3[i3, kl3]

                                        f_int = 0.0

                                        for q2 in range(n_quad2):
                                            f_int += (
                                                wts2[x_his_ind2[i2, j2], q2]
                                                * bs1[x_int_ind1[i1, j1], k1]
                                                * bs2[x_his_ind2[i2, j2], q2, k2]
                                                * bs3[x_int_ind3[i3, j3], k3]
                                                * mat_eq[x_int_ind1[i1, j1], x_his_ind2[i2, j2], q2, x_int_ind3[i3, j3]]
                                            )

                                        tau[k1, k2, k3, c1, c2, c3] += coeff * f_int
    # -- removed omp: #$ omp end do
    # -- removed omp: #$ omp end parallel

    ierr = 0


# ========================================================
def kernel_pi1_3(
    n: "int[:]",
    n_quad3: "int",
    n_inthis: "int[:]",
    n_nvbf: "int[:]",
    i_glo1: "int[:,:]",
    i_glo2: "int[:,:]",
    i_glo3: "int[:,:]",
    c_loc1: "int[:,:]",
    c_loc2: "int[:,:]",
    c_loc3: "int[:,:]",
    coeff1: "float[:,:]",
    coeff2: "float[:,:]",
    coeff3: "float[:,:]",
    coeff_ind1: "int[:]",
    coeff_ind2: "int[:]",
    coeff_ind3: "int[:]",
    bs1: "float[:,:]",
    bs2: "float[:,:]",
    bs3: "float[:,:,:]",
    x_int_ind1: "int[:,:]",
    x_int_ind2: "int[:,:]",
    x_his_ind3: "int[:,:]",
    wts3: "float[:,:]",
    tau: "float[:,:,:,:,:,:]",
    mat_eq: "float[:,:,:,:]",
):
    tau[:, :, :, :, :, :] = 0.0

    # -- removed omp: #$ omp parallel
    # -- removed omp: #$ omp do reduction ( + : tau) private (i1, i2, i3, j1, j2, j3, coeff, kl1, k1, c1, kl2, k2, c2, kl3, k3, c3, f_int, q3)
    for i1 in range(n[0]):
        for i2 in range(n[1]):
            for i3 in range(n[2]):
                for j1 in range(n_inthis[0]):
                    for j2 in range(n_inthis[1]):
                        for j3 in range(n_inthis[2]):
                            coeff = coeff1[coeff_ind1[i1], j1] * coeff2[coeff_ind2[i2], j2] * coeff3[coeff_ind3[i3], j3]

                            for kl1 in range(n_nvbf[0]):
                                k1 = i_glo1[i1, kl1]
                                c1 = c_loc1[i1, kl1]

                                for kl2 in range(n_nvbf[1]):
                                    k2 = i_glo2[i2, kl2]
                                    c2 = c_loc2[i2, kl2]

                                    for kl3 in range(n_nvbf[2]):
                                        k3 = i_glo3[i3, kl3]
                                        c3 = c_loc3[i3, kl3]

                                        f_int = 0.0

                                        for q3 in range(n_quad3):
                                            f_int += (
                                                wts3[x_his_ind3[i3, j3], q3]
                                                * bs1[x_int_ind1[i1, j1], k1]
                                                * bs2[x_int_ind2[i2, j2], k2]
                                                * bs3[x_his_ind3[i3, j3], q3, k3]
                                                * mat_eq[x_int_ind1[i1, j1], x_int_ind2[i2, j2], x_his_ind3[i3, j3], q3]
                                            )

                                        tau[k1, k2, k3, c1, c2, c3] += coeff * f_int
    # -- removed omp: #$ omp end do
    # -- removed omp: #$ omp end parallel

    ierr = 0


# ========================================================
def kernel_pi2_1(
    n: "int[:]",
    n_quad: "int[:]",
    n_inthis: "int[:]",
    n_nvbf: "int[:]",
    i_glo1: "int[:,:]",
    i_glo2: "int[:,:]",
    i_glo3: "int[:,:]",
    c_loc1: "int[:,:]",
    c_loc2: "int[:,:]",
    c_loc3: "int[:,:]",
    coeff1: "float[:,:]",
    coeff2: "float[:,:]",
    coeff3: "float[:,:]",
    coeff_ind1: "int[:]",
    coeff_ind2: "int[:]",
    coeff_ind3: "int[:]",
    bs1: "float[:,:]",
    bs2: "float[:,:,:]",
    bs3: "float[:,:,:]",
    x_int_ind1: "int[:,:]",
    x_his_ind2: "int[:,:]",
    x_his_ind3: "int[:,:]",
    wts2: "float[:,:]",
    wts3: "float[:,:]",
    tau: "float[:,:,:,:,:,:]",
    mat_eq: "float[:,:,:,:,:]",
):
    tau[:, :, :, :, :, :] = 0.0

    # -- removed omp: #$ omp parallel
    # -- removed omp: #$ omp do reduction ( + : tau) private (i1, i2, i3, j1, j2, j3, coeff, kl1, k1, c1, kl2, k2, c2, kl3, k3, c3, f_int, q2, q3, wvol)
    for i1 in range(n[0]):
        for i2 in range(n[1]):
            for i3 in range(n[2]):
                for j1 in range(n_inthis[0]):
                    for j2 in range(n_inthis[1]):
                        for j3 in range(n_inthis[2]):
                            coeff = coeff1[coeff_ind1[i1], j1] * coeff2[coeff_ind2[i2], j2] * coeff3[coeff_ind3[i3], j3]

                            for kl1 in range(n_nvbf[0]):
                                k1 = i_glo1[i1, kl1]
                                c1 = c_loc1[i1, kl1]

                                for kl2 in range(n_nvbf[1]):
                                    k2 = i_glo2[i2, kl2]
                                    c2 = c_loc2[i2, kl2]

                                    for kl3 in range(n_nvbf[2]):
                                        k3 = i_glo3[i3, kl3]
                                        c3 = c_loc3[i3, kl3]

                                        f_int = 0.0

                                        for q2 in range(n_quad[0]):
                                            for q3 in range(n_quad[1]):
                                                wvol = wts2[x_his_ind2[i2, j2], q2] * wts3[x_his_ind3[i3, j3], q3]
                                                f_int += (
                                                    wvol
                                                    * bs1[x_int_ind1[i1, j1], k1]
                                                    * bs2[x_his_ind2[i2, j2], q2, k2]
                                                    * bs3[x_his_ind3[i3, j3], q3, k3]
                                                    * mat_eq[
                                                        x_int_ind1[i1, j1],
                                                        x_his_ind2[i2, j2],
                                                        q2,
                                                        x_his_ind3[i3, j3],
                                                        q3,
                                                    ]
                                                )

                                        tau[k1, k2, k3, c1, c2, c3] += coeff * f_int
    # -- removed omp: #$ omp end do
    # -- removed omp: #$ omp end parallel

    ierr = 0


# ========================================================
def kernel_pi2_2(
    n: "int[:]",
    n_quad: "int[:]",
    n_inthis: "int[:]",
    n_nvbf: "int[:]",
    i_glo1: "int[:,:]",
    i_glo2: "int[:,:]",
    i_glo3: "int[:,:]",
    c_loc1: "int[:,:]",
    c_loc2: "int[:,:]",
    c_loc3: "int[:,:]",
    coeff1: "float[:,:]",
    coeff2: "float[:,:]",
    coeff3: "float[:,:]",
    coeff_ind1: "int[:]",
    coeff_ind2: "int[:]",
    coeff_ind3: "int[:]",
    bs1: "float[:,:,:]",
    bs2: "float[:,:]",
    bs3: "float[:,:,:]",
    x_his_ind1: "int[:,:]",
    x_int_ind2: "int[:,:]",
    x_his_ind3: "int[:,:]",
    wts1: "float[:,:]",
    wts3: "float[:,:]",
    tau: "float[:,:,:,:,:,:]",
    mat_eq: "float[:,:,:,:,:]",
):
    tau[:, :, :, :, :, :] = 0.0

    # -- removed omp: #$ omp parallel
    # -- removed omp: #$ omp do reduction ( + : tau) private (i1, i2, i3, j1, j2, j3, coeff, kl1, k1, c1, kl2, k2, c2, kl3, k3, c3, f_int, q1, q3, wvol)
    for i1 in range(n[0]):
        for i2 in range(n[1]):
            for i3 in range(n[2]):
                for j1 in range(n_inthis[0]):
                    for j2 in range(n_inthis[1]):
                        for j3 in range(n_inthis[2]):
                            coeff = coeff1[coeff_ind1[i1], j1] * coeff2[coeff_ind2[i2], j2] * coeff3[coeff_ind3[i3], j3]

                            for kl1 in range(n_nvbf[0]):
                                k1 = i_glo1[i1, kl1]
                                c1 = c_loc1[i1, kl1]

                                for kl2 in range(n_nvbf[1]):
                                    k2 = i_glo2[i2, kl2]
                                    c2 = c_loc2[i2, kl2]

                                    for kl3 in range(n_nvbf[2]):
                                        k3 = i_glo3[i3, kl3]
                                        c3 = c_loc3[i3, kl3]

                                        f_int = 0.0

                                        for q1 in range(n_quad[0]):
                                            for q3 in range(n_quad[1]):
                                                wvol = wts1[x_his_ind1[i1, j1], q1] * wts3[x_his_ind3[i3, j3], q3]
                                                f_int += (
                                                    wvol
                                                    * bs1[x_his_ind1[i1, j1], q1, k1]
                                                    * bs2[x_int_ind2[i2, j2], k2]
                                                    * bs3[x_his_ind3[i3, j3], q3, k3]
                                                    * mat_eq[
                                                        x_his_ind1[i1, j1],
                                                        q1,
                                                        x_int_ind2[i2, j2],
                                                        x_his_ind3[i3, j3],
                                                        q3,
                                                    ]
                                                )

                                        tau[k1, k2, k3, c1, c2, c3] += coeff * f_int
    # -- removed omp: #$ omp end do
    # -- removed omp: #$ omp end parallel

    ierr = 0


# ========================================================
def kernel_pi2_3(
    n: "int[:]",
    n_quad: "int[:]",
    n_inthis: "int[:]",
    n_nvbf: "int[:]",
    i_glo1: "int[:,:]",
    i_glo2: "int[:,:]",
    i_glo3: "int[:,:]",
    c_loc1: "int[:,:]",
    c_loc2: "int[:,:]",
    c_loc3: "int[:,:]",
    coeff1: "float[:,:]",
    coeff2: "float[:,:]",
    coeff3: "float[:,:]",
    coeff_ind1: "int[:]",
    coeff_ind2: "int[:]",
    coeff_ind3: "int[:]",
    bs1: "float[:,:,:]",
    bs2: "float[:,:,:]",
    bs3: "float[:,:]",
    x_his_ind1: "int[:,:]",
    x_his_ind2: "int[:,:]",
    x_int_ind3: "int[:,:]",
    wts1: "float[:,:]",
    wts2: "float[:,:]",
    tau: "float[:,:,:,:,:,:]",
    mat_eq: "float[:,:,:,:,:]",
):
    tau[:, :, :, :, :, :] = 0.0

    # -- removed omp: #$ omp parallel
    # -- removed omp: #$ omp do reduction ( + : tau) private (i1, i2, i3, j1, j2, j3, coeff, kl1, k1, c1, kl2, k2, c2, kl3, k3, c3, f_int, q1, q2, wvol)
    for i1 in range(n[0]):
        for i2 in range(n[1]):
            for i3 in range(n[2]):
                for j1 in range(n_inthis[0]):
                    for j2 in range(n_inthis[1]):
                        for j3 in range(n_inthis[2]):
                            coeff = coeff1[coeff_ind1[i1], j1] * coeff2[coeff_ind2[i2], j2] * coeff3[coeff_ind3[i3], j3]

                            for kl1 in range(n_nvbf[0]):
                                k1 = i_glo1[i1, kl1]
                                c1 = c_loc1[i1, kl1]

                                for kl2 in range(n_nvbf[1]):
                                    k2 = i_glo2[i2, kl2]
                                    c2 = c_loc2[i2, kl2]

                                    for kl3 in range(n_nvbf[2]):
                                        k3 = i_glo3[i3, kl3]
                                        c3 = c_loc3[i3, kl3]

                                        f_int = 0.0

                                        for q1 in range(n_quad[0]):
                                            for q2 in range(n_quad[1]):
                                                wvol = wts1[x_his_ind1[i1, j1], q1] * wts2[x_his_ind2[i2, j2], q2]
                                                f_int += (
                                                    wvol
                                                    * bs1[x_his_ind1[i1, j1], q1, k1]
                                                    * bs2[x_his_ind2[i2, j2], q2, k2]
                                                    * bs3[x_int_ind3[i3, j3], k3]
                                                    * mat_eq[
                                                        x_his_ind1[i1, j1],
                                                        q1,
                                                        x_his_ind2[i2, j2],
                                                        q2,
                                                        x_int_ind3[i3, j3],
                                                    ]
                                                )

                                        tau[k1, k2, k3, c1, c2, c3] += coeff * f_int
    # -- removed omp: #$ omp end do
    # -- removed omp: #$ omp end parallel

    ierr = 0


# ========================================================
def kernel_pi3(
    n: "int[:]",
    n_quad: "int[:]",
    n_his: "int[:]",
    n_nvbf: "int[:]",
    i_glo1: "int[:,:]",
    i_glo2: "int[:,:]",
    i_glo3: "int[:,:]",
    c_loc1: "int[:,:]",
    c_loc2: "int[:,:]",
    c_loc3: "int[:,:]",
    coeff1: "float[:,:]",
    coeff2: "float[:,:]",
    coeff3: "float[:,:]",
    coeff_ind1: "int[:]",
    coeff_ind2: "int[:]",
    coeff_ind3: "int[:]",
    bs1: "float[:,:,:]",
    bs2: "float[:,:,:]",
    bs3: "float[:,:,:]",
    x_his_ind1: "int[:,:]",
    x_his_ind2: "int[:,:]",
    x_his_ind3: "int[:,:]",
    wts1: "float[:,:]",
    wts2: "float[:,:]",
    wts3: "float[:,:]",
    tau: "float[:,:,:,:,:,:]",
    mat_eq: "float[:,:,:,:,:,:]",
):
    tau[:, :, :, :, :, :] = 0.0

    # -- removed omp: #$ omp parallel
    # -- removed omp: #$ omp do reduction ( + : tau) private (i1, i2, i3, j1, j2, j3, coeff, kl1, k1, c1, kl2, k2, c2, kl3, k3, c3, f_int, q1, q2, q3, wvol)
    for i1 in range(n[0]):
        for i2 in range(n[1]):
            for i3 in range(n[2]):
                for j1 in range(n_his[0]):
                    for j2 in range(n_his[1]):
                        for j3 in range(n_his[2]):
                            coeff = coeff1[coeff_ind1[i1], j1] * coeff2[coeff_ind2[i2], j2] * coeff3[coeff_ind3[i3], j3]

                            for kl1 in range(n_nvbf[0]):
                                k1 = i_glo1[i1, kl1]
                                c1 = c_loc1[i1, kl1]

                                for kl2 in range(n_nvbf[1]):
                                    k2 = i_glo2[i2, kl2]
                                    c2 = c_loc2[i2, kl2]

                                    for kl3 in range(n_nvbf[2]):
                                        k3 = i_glo3[i3, kl3]
                                        c3 = c_loc3[i3, kl3]

                                        f_int = 0.0

                                        for q1 in range(n_quad[0]):
                                            for q2 in range(n_quad[1]):
                                                for q3 in range(n_quad[2]):
                                                    wvol = (
                                                        wts1[x_his_ind1[i1, j1], q1]
                                                        * wts2[x_his_ind2[i2, j2], q2]
                                                        * wts3[x_his_ind3[i3, j3], q3]
                                                    )
                                                    f_int += (
                                                        wvol
                                                        * bs1[x_his_ind1[i1, j1], q1, k1]
                                                        * bs2[x_his_ind2[i2, j2], q2, k2]
                                                        * bs3[x_his_ind3[i3, j3], q3, k3]
                                                        * mat_eq[
                                                            x_his_ind1[i1, j1],
                                                            q1,
                                                            x_his_ind2[i2, j2],
                                                            q2,
                                                            x_his_ind3[i3, j3],
                                                            q3,
                                                        ]
                                                    )

                                        tau[k1, k2, k3, c1, c2, c3] += coeff * f_int
    # -- removed omp: #$ omp end do
    # -- removed omp: #$ omp end parallel

    ierr = 0
