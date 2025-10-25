#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import sys
import copy
import itertools

import numpy as np
import scipy.linalg
import scipy.spatial
import scipy.spatial.distance

H = 1e-3  # Magnitude of the finite displacements, in nm.
SYMPREC = 1e-5  # Tolerance for symmetry search


def gen_SPOSCAR(poscar, na, nb, nc):
    """
    Create a dictionary similar to the first argument but describing a
    supercell.
    """
    nruter = dict()
    nruter["na"] = na
    nruter["nb"] = nb
    nruter["nc"] = nc
    nruter["lattvec"] = np.array(poscar["lattvec"])
    nruter["lattvec"][:, 0] *= na
    nruter["lattvec"][:, 1] *= nb
    nruter["lattvec"][:, 2] *= nc
    nruter["elements"] = copy.copy(poscar["elements"])
    nruter["numbers"] = na * nb * nc * poscar["numbers"]
    nruter["positions"] = np.empty((3, poscar["positions"].shape[1] * na * nb * nc))
    pos = 0
    for pos, (k, j, i, iat) in enumerate(
        itertools.product(
            range(nc), range(nb), range(na), range(poscar["positions"].shape[1])
        )
    ):
        nruter["positions"][:, pos] = (poscar["positions"][:, iat] + [i, j, k]) / [
            na,
            nb,
            nc,
        ]
    nruter["types"] = []
    for i in range(na * nb * nc):
        nruter["types"].extend(poscar["types"])
    return nruter


def calc_dists(sposcar):
    """
    Return the distances between atoms in the supercells, their
    degeneracies and the associated supercell vectors.
    """
    ntot = sposcar["positions"].shape[1]
    posi = np.dot(sposcar["lattvec"], sposcar["positions"])
    d2s = np.empty((27, ntot, ntot))
    for j, (ja, jb, jc) in enumerate(
        itertools.product(range(-1, 2), range(-1, 2), range(-1, 2))
    ):
        posj = np.dot(sposcar["lattvec"], (sposcar["positions"].T + [ja, jb, jc]).T)
        d2s[j, :, :] = scipy.spatial.distance.cdist(posi.T, posj.T, "sqeuclidean")
    d2min = d2s.min(axis=0)
    dmin = np.sqrt(d2min)
    degenerate = np.abs(d2s - d2min) < 1e-4
    nequi = degenerate.sum(axis=0, dtype=np.intc)
    maxequi = nequi.max()
    shifts = np.empty((ntot, ntot, maxequi))
    sorting = np.argsort(np.logical_not(degenerate), axis=0)
    shifts = np.transpose(sorting[:maxequi, :, :], (1, 2, 0)).astype(np.intc)
    return (dmin, nequi, shifts)


def calc_frange(poscar, sposcar, n, dmin):
    """
    Return the maximum distance between n-th neighbors in the structure.
    """
    natoms = len(poscar["types"])
    tonth = []
    warned = False
    for i in range(natoms):
        ds = dmin[i, :].tolist()
        ds.sort()
        u = []
        for j in ds:
            for k in u:
                if np.allclose(k, j):
                    break
            else:
                u.append(j)
        try:
            tonth.append(0.5 * (u[n] + u[n + 1]))
        except IndexError:
            if not warned:
                sys.stderr.write(
                    "Warning: supercell too small to find n-th neighbours\n"
                )
                warned = True
            tonth.append(1.1 * max(u))
    return max(tonth)


def move_three_atoms(poscar, iat, icoord, ih, jat, jcoord, jh, kat, kcoord, kh):
    """
    Return a copy of poscar with atom iat displaced by ih nm along
    its icoord-th Cartesian coordinate and atom jat displaced by
    jh nm along its jcoord-th Cartesian coordinate and atom kat
    displaced by kh nm along its kcoord-th Cartesian coordinate.
    """
    nruter = copy.deepcopy(poscar)
    disp = np.zeros(3)
    disp[icoord] = ih
    nruter["positions"][:, iat] += scipy.linalg.solve(nruter["lattvec"], disp)
    disp[:] = 0.0
    disp[jcoord] = jh
    nruter["positions"][:, jat] += scipy.linalg.solve(nruter["lattvec"], disp)
    disp[:] = 0.0
    disp[kcoord] = kh
    nruter["positions"][:, kat] += scipy.linalg.solve(nruter["lattvec"], disp)
    return nruter


def write_pos(sposcar, ngrid, nspecies, filename):
    """
    Write out the position information
    """
    pos = np.dot(sposcar["lattvec"], sposcar["positions"])
    ntot = ngrid[0] * ngrid[1] * ngrid[2] * nspecies
    np_icell = np.empty((3, ntot), dtype=np.intc)
    car = pos
    np_ispecies = np.empty(ntot, dtype=np.intc)
    icell = np_icell
    ispecies = np_ispecies

    f = io.StringIO()

    for ii in range(ntot):
        tmp, ispecies[ii] = divmod(ii, nspecies)
        tmp, icell[0, ii] = divmod(tmp, ngrid[0])
        icell[2, ii], icell[1, ii] = divmod(tmp, ngrid[1])
        car[0, ii], car[1, ii], car[2, ii] = (
            np.dot(sposcar["lattvec"], sposcar["positions"][:, ii]) * 10
        )
        f.write(
            "{:>6d} {:>6d} {:>15.10f} {:>15.10f} {:>15.10f}\n".format(
                ii + 1, ispecies[ii] + 1, car[0, ii], car[1, ii], car[2, ii]
            )
        )
    ffinal = open(filename, "w")
    ffinal.write(f.getvalue())
    f.close()
    ffinal.close()


def id2ind(ngrid, nspecies, filename):
    """
    Create a map from supercell indices to cell+atom indices.
    """
    ntot = ngrid[0] * ngrid[1] * ngrid[2] * nspecies
    np_icell = np.empty((3, ntot), dtype=np.intc)
    np_ispecies = np.empty(ntot, dtype=np.intc)
    icell = np_icell
    ispecies = np_ispecies

    f = io.StringIO()

    for ii in range(ntot):
        tmp, ispecies[ii] = divmod(ii, nspecies)
        tmp, icell[0, ii] = divmod(tmp, ngrid[0])
        icell[2, ii], icell[1, ii] = divmod(tmp, ngrid[1])
        # jj = (icell[0, ii] + 1) * (icell[1, ii] + 1) * (icell[2, ii] + 1)
        f.write(
            "{:>6d} {:>6d} {:>6d}\n".format(
                ii + 1, (ii + nspecies) // nspecies, ispecies[ii]
            )
        )
    ffinal = open(filename, "w")
    ffinal.write(f.getvalue())
    f.close()
    ffinal.close()


def write_indexcell(ngrid, poscar, sposcar, dmin, nequi, shifts, frange, filename):
    """
    Write out the indexcell for each quartet,
    taking the force cutoff into account.
    """
    natoms = len(poscar["types"])
    ntot = len(sposcar["types"])
    nspecies = len(poscar["types"])
    ntot = ngrid[0] * ngrid[1] * ngrid[2] * nspecies
    np_icell = np.empty((3, ntot), dtype=np.intc)
    np_ispecies = np.empty(ntot, dtype=np.intc)
    cellmap = np.empty((3, ntot), dtype=np.intc)
    icell = np_icell
    ispecies = np_ispecies

    for ii in range(ntot):
        tmp, ispecies[ii] = divmod(ii, nspecies)
        tmp, icell[0, ii] = divmod(tmp, ngrid[0])
        icell[2, ii], icell[1, ii] = divmod(tmp, ngrid[1])
        cellmap[0, ii], cellmap[1, ii], cellmap[2, ii] = (
            ii,
            (ii + natoms) // natoms - 1,
            ispecies[ii],
        )

    shifts27 = list(itertools.product(range(-1, 2), range(-1, 2), range(-1, 2)))
    frange2 = frange * frange

    nblocks = 0
    f = io.StringIO()
    for ii, jj in itertools.product(range(natoms), range(ntot)):
        if dmin[ii, jj] >= frange:
            continue
        jatom = jj % natoms
        shiftsij = [shifts27[i] for i in shifts[ii, jj, : nequi[ii, jj]]]
        for kk in range(ntot):
            if dmin[ii, kk] >= frange:
                continue
            katom = kk % natoms
            shiftsik = [shifts27[i] for i in shifts[ii, kk, : nequi[ii, kk]]]
            for ll in range(ntot):
                if dmin[ii, ll] >= frange:
                    continue
                latom = ll % natoms
                shiftsil = [shifts27[i] for i in shifts[ii, ll, : nequi[ii, ll]]]
                # d2min_1 = np.inf
                # d2min_2 = np.inf
                # d2min_3 = np.inf
                d2min = np.inf
                for shift2 in shiftsij:
                    carj = np.dot(
                        sposcar["lattvec"], shift2 + sposcar["positions"][:, jj]
                    )
                    for shift3 in shiftsik:
                        cark = np.dot(
                            sposcar["lattvec"], shift3 + sposcar["positions"][:, kk]
                        )
                        for shift4 in shiftsil:
                            carl = np.dot(
                                sposcar["lattvec"], shift4 + sposcar["positions"][:, ll]
                            )
                            d2_1 = ((carj - cark) ** 2).sum()
                            d2_2 = ((carj - carl) ** 2).sum()
                            d2_3 = ((cark - carl) ** 2).sum()
                            d2 = max(d2_1, d2_2, d2_3)
                            if d2 < d2min:
                                # best2 = shift2
                                # best3 = shift3
                                # best4 = shift4
                                d2min = d2
                if d2min >= frange2:
                    continue
                nblocks += 1
                f.write(
                    "{:>6d} {:>6d} {:>6d} {:>6d} {:>6d} {:>6d} {:>6d} {:>6d}\n".format(
                        cellmap[1, ii],
                        ii,
                        cellmap[1, jj],
                        jatom,
                        cellmap[1, kk],
                        katom,
                        cellmap[1, ll],
                        latom,
                    )
                )
    ffinal = open(filename, "w")
    ffinal.write("{:>5}\n".format(nblocks))
    ffinal.write(f.getvalue())
    f.close()
    ffinal.close()


def write_ifcs(phifull, poscar, sposcar, dmin, nequi, shifts, frange, filename):
    """
    Write out the full fourth-order interatomic force constant matrix,
    taking the force cutoff into account.
    """
    natoms = len(poscar["types"])
    ntot = len(sposcar["types"])

    shifts27 = list(itertools.product(range(-1, 2), range(-1, 2), range(-1, 2)))
    frange2 = frange * frange

    nblocks = 0
    f = io.StringIO()
    for ii, jj in itertools.product(range(natoms), range(ntot)):
        if dmin[ii, jj] >= frange:
            continue
        jatom = jj % natoms
        shiftsij = [shifts27[i] for i in shifts[ii, jj, : nequi[ii, jj]]]
        for kk in range(ntot):
            if dmin[ii, kk] >= frange:
                continue
            katom = kk % natoms
            shiftsik = [shifts27[i] for i in shifts[ii, kk, : nequi[ii, kk]]]
            for ll in range(ntot):
                if dmin[ii, ll] >= frange:
                    continue
                latom = ll % natoms
                shiftsil = [shifts27[i] for i in shifts[ii, ll, : nequi[ii, ll]]]
                # d2min_1 = np.inf
                # d2min_2 = np.inf
                # d2min_3 = np.inf
                d2min = np.inf
                for shift2 in shiftsij:
                    carj = np.dot(
                        sposcar["lattvec"], shift2 + sposcar["positions"][:, jj]
                    )
                    for shift3 in shiftsik:
                        cark = np.dot(
                            sposcar["lattvec"], shift3 + sposcar["positions"][:, kk]
                        )
                        for shift4 in shiftsil:
                            carl = np.dot(
                                sposcar["lattvec"], shift4 + sposcar["positions"][:, ll]
                            )
                            d2_1 = ((carj - cark) ** 2).sum()
                            d2_2 = ((carj - carl) ** 2).sum()
                            d2_3 = ((cark - carl) ** 2).sum()
                            d2 = max(d2_1, d2_2, d2_3)
                            if d2 < d2min:
                                best2 = shift2
                                best3 = shift3
                                best4 = shift4
                                d2min = d2
                if d2min >= frange2:
                    continue
                nblocks += 1
                Rj = np.dot(
                    sposcar["lattvec"],
                    best2
                    + sposcar["positions"][:, jj]
                    - sposcar["positions"][:, jatom],
                )
                Rk = np.dot(
                    sposcar["lattvec"],
                    best3
                    + sposcar["positions"][:, kk]
                    - sposcar["positions"][:, katom],
                )
                Rl = np.dot(
                    sposcar["lattvec"],
                    best4
                    + sposcar["positions"][:, ll]
                    - sposcar["positions"][:, latom],
                )
                f.write("\n")
                f.write("{:>5}\n".format(nblocks))
                f.write(
                    "{0[0]:>15.10e} {0[1]:>15.10e} {0[2]:>15.10e}\n".format(
                        list(10.0 * Rj)
                    )
                )
                f.write(
                    "{0[0]:>15.10e} {0[1]:>15.10e} {0[2]:>15.10e}\n".format(
                        list(10.0 * Rk)
                    )
                )
                f.write(
                    "{0[0]:>15.10e} {0[1]:>15.10e} {0[2]:>15.10e}\n".format(
                        list(10.0 * Rl)
                    )
                )
                f.write(
                    "{:>6d} {:>6d} {:>6d} {:>6d}\n".format(
                        ii + 1, jatom + 1, katom + 1, latom + 1
                    )
                )
                for mm, nn, oo, pp in itertools.product(
                    range(3), range(3), range(3), range(3)
                ):
                    f.write(
                        "{:>2d} {:>2d} {:>2d} {:>2d} {:>20.10f}\n".format(
                            mm + 1,
                            nn + 1,
                            oo + 1,
                            pp + 1,
                            phifull[mm, nn, oo, pp, ii, jj, kk, ll],
                        )
                    )
    ffinal = open(filename, "w")
    ffinal.write("{:>5}\n".format(nblocks))
    ffinal.write(f.getvalue())
    f.close()
    ffinal.close()


def check_ASRs(phifull, poscar, sposcar, filename):
    """
    Check Acoustic sum rule for each component.
    """
    # natoms = len(poscar["types"])
    ntot = len(sposcar["types"])

    f = io.StringIO()
    tot = 0
    # nblocks = 0
    for ll in range(ntot):
        tot += phifull[0, 0, 0, 0, 1, 2, 3, ll]
    f.write("{:>20.10f}\n".format(tot))
    ffinal = open(filename, "w")
    ffinal.write(f.getvalue())
    f.close()
    ffinal.close()
