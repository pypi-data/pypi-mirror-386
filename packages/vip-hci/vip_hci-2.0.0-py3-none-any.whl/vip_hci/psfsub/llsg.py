#! /usr/bin/env python
"""
Module containing the Local Low-rank plus Sparse plus Gaussian-noise
decomposition algorithm for ADI data.

.. [GOM16]
   | Gomez-Gonzalez et al. 2016
   | **Low-rank plus sparse decomposition for exoplanet detection in
     direct-imaging ADI sequences. The LLSG algorithm**
   | *Astronomy & Astrophysics, Volume 589, Issue 1, p. 54*
   | `https://arxiv.org/abs/1602.08381
     <https://arxiv.org/abs/1602.08381>`_

"""

__author__ = "Carlos Alberto Gomez Gonzalez, Thomas Bédrine"
__all__ = ["llsg", "thresholding", "LLSG_Params"]


import numpy as np
from scipy.linalg import qr
from multiprocessing import cpu_count
from astropy.stats import median_absolute_deviation
from dataclasses import dataclass
from typing import List
from enum import Enum
from .svd import svd_wrapper, get_eigenvectors
from ..config import time_ini, timing
from ..config.paramenum import Collapse, LowRankMode, AutoRankMode, ThreshMode, ALGO_KEY
from ..config.utils_conf import pool_map, iterable
from ..config.utils_param import setup_parameters, separate_kwargs_dict
from ..preproc import cube_derotate, cube_collapse
from ..var import get_annulus_segments, cube_filter_highpass


@dataclass
class LLSG_Params:
    """
    Set of parameters for the LLSG algorithm.

    See function `llsg` below for the documentation.
    """

    cube: np.ndarray = None
    angle_list: np.ndarray = None
    fwhm: float = None
    rank: int = 10
    thresh: float = 1
    max_iter: int = 10
    low_rank_ref: bool = False
    low_rank_mode: Enum = LowRankMode.SVD
    auto_rank_mode: Enum = AutoRankMode.NOISE
    residuals_tol: float = 1e-1
    cevr: float = 0.9
    thresh_mode: Enum = ThreshMode.SOFT
    nproc: int = 1
    asize: int = None
    n_segments: int = 4
    azimuth_overlap: int = None
    radius_int: int = None
    random_seed: int = None
    high_pass: int = None
    collapse: Enum = Collapse.MEDIAN
    full_output: bool = False
    verbose: bool = True
    debug: bool = False


def llsg(*all_args: List, **all_kwargs: dict):
    """Local Low-rank plus Sparse plus Gaussian-noise decomposition (LLSG) as
    described in [GOM16]_. This first version of our algorithm aims at
    decomposing ADI cubes into three terms L+S+G (low-rank, sparse and Gaussian
    noise). Separating the noise from the S component (where the moving planet
    should stay) allow us to increase the SNR of potential planets.

    The three tunable parameters are the *rank* or expected rank of the L
    component, the ``thresh`` or threshold for encouraging sparsity in the S
    component and ``max_iter`` which sets the number of iterations. The rest of
    parameters can be tuned at the users own risk (do it if you know what you're
    doing).

    Parameters
    ----------
    all_args: list, optional
        Positionnal arguments for the LLSG algorithm. Full list of parameters
        below.
    all_kwargs: dictionary, optional
        Mix of keyword arguments that can initialize a LLSGParams and the optional
        'rot_options' dictionnary, with keyword values for "border_mode", "mask_val",
        "edge_blend", "interp_zeros", "ker" (see documentation of
        ``vip_hci.preproc.frame_rotate``). Can also contain a LLSGParams named as
        `algo_params`.

    LLSG parameters
    ----------
    cube : numpy ndarray, 3d
        Input ADI cube.
    angle_list : 1d numpy ndarray
        Vector of derotation angles to align North up in your cube images.
    fwhm : float
        Known size of the FWHM in pixels to be used.
    rank : int, optional
        Expected rank of the L component.
    thresh : float, optional
        Factor that scales the thresholding step in the algorithm.
    max_iter : int, optional
        Sets the number of iterations.
    low_rank_ref :
        If True the first estimation of the L component is obtained from the
        remaining segments in the same annulus.
    low_rank_mode : Enum, see `vip_hci.config.paramenum.LowRankMode`
        Sets the method of solving the L update.
    auto_rank_mode : Enum, see `vip_hci.config.paramenum.AutoRankMode`
        If ``rank`` is None, then ``auto_rank_mode`` sets the way that the
        ``rank`` is determined: the noise minimization or the cumulative
        explained variance ratio (when 'svd' is used).
    residuals_tol : float, optional
        The value of the noise decay to be used when ``rank`` is None and
        ``auto_rank_mode`` is set to ``noise``.
    cevr : float, optional
        Float value in the range [0,1] for selecting the cumulative explained
        variance ratio to choose the rank automatically (if ``rank`` is None).
    thresh_mode : Enum, see `vip_hci.config.paramenum.ThreshMode`
        Sets the type of thresholding.
    nproc : None or int, optional
        Number of processes for parallel computing. If None the number of
        processes will be set to cpu_count()/2. By default the algorithm works
        in single-process mode.
    asize : int or None, optional
        If ``asize`` is None then each annulus will have a width of ``2*asize``.
        If an integer then it is the width in pixels of each annulus.
    n_segments : int or list of ints, optional
        The number of segments for each annulus. When a single integer is given
        it is used for all annuli.
    azimuth_overlap : int or None, optional
        Sets the amount of azimuthal averaging.
    radius_int : int, optional
        The radius of the innermost annulus. By default is 0, if >0 then the
        central circular area is discarded.
    random_seed : int or None, optional
        Controls the seed for the Pseudo Random Number generator.
    high_pass : odd int or None, optional
        If set to an odd integer <=7, a high-pass filter is applied to the
        frames. The ``vip_hci.var.frame_filter_highpass`` is applied twice,
        first with the mode ``median-subt`` and a large window, and then with
        ``laplacian-conv`` and a kernel size equal to ``high_pass``. 5 is an
        optimal value when ``fwhm`` is ~4.
    collapse : Enum, see `vip_hci.config.paramenum.Collapse`
        Sets the way of collapsing the frames for producing a final image.
    full_output: bool, optional
        Whether to return the final median combined image only or with other
        intermediate arrays.
    verbose : bool, optional
        If True prints to stdout intermediate info.
    debug : bool, optional
        Whether to output some intermediate information.

    Returns
    -------
    frame_s : numpy ndarray, 2d
        Final frame (from the S component) after rotation and median-combination.

    If ``full_output`` is True, the following intermediate arrays are returned:
    list_l_array_der, list_s_array_der, list_g_array_der, frame_l, frame_s,
    frame_g

    """

    # Separating the parameters of the ParamsObject from the optionnal rot_options
    class_params, rot_options = separate_kwargs_dict(
        initial_kwargs=all_kwargs, parent_class=LLSG_Params
    )

    # Extracting the object of parameters (if any)
    algo_params = None
    if ALGO_KEY in rot_options.keys():
        algo_params = rot_options[ALGO_KEY]
        del rot_options[ALGO_KEY]

    if algo_params is None:
        algo_params = LLSG_Params(*all_args, **class_params)

    if algo_params.cube.ndim != 3:
        raise TypeError("Input array is not a cube (3d array)")
    if not algo_params.cube.shape[0] == algo_params.angle_list.shape[0]:
        msg = "Angle list vector has wrong length. It must equal the number"
        msg += " frames in the cube"
        raise TypeError(msg)

    if algo_params.low_rank_mode == LowRankMode.BRP:
        if algo_params.rank is None:
            msg = "Auto rank only works with SVD low_rank_mode."
            msg += " Set a value for the rank parameter"
            raise ValueError(msg)
        if algo_params.low_rank_ref:
            msg = "Low_rank_ref only works with SVD low_rank_mode"
            raise ValueError(msg)

    global cube_init
    if algo_params.high_pass is not None:
        cube_init = cube_filter_highpass(
            algo_params.cube, "median-subt", median_size=19, verbose=False
        )
        cube_init = cube_filter_highpass(
            cube_init,
            "laplacian-conv",
            kernel_size=algo_params.high_pass,
            verbose=False,
        )
    else:
        cube_init = algo_params.cube

    if algo_params.verbose:
        start_time = time_ini()
    n, y, x = algo_params.cube.shape

    if algo_params.azimuth_overlap == 0:
        algo_params.azimuth_overlap = None

    if algo_params.radius_int is None:
        algo_params.radius_int = 0

    if algo_params.nproc is None:
        algo_params.nproc = cpu_count() // 2  # Hyper-threading doubles the # of cores

    # Same number of pixels per annulus
    if algo_params.asize is None:
        annulus_width = int(np.ceil(2 * algo_params.fwhm))  # as in the paper
    elif isinstance(algo_params.asize, int):
        annulus_width = algo_params.asize
    n_annuli = int((y / 2 - algo_params.radius_int) / annulus_width)
    # TODO: asize in pxs to be consistent with other functions

    if algo_params.n_segments is None:
        algo_params.n_segments = [4 for _ in range(n_annuli)]  # as in the paper
    elif isinstance(algo_params.n_segments, int):
        algo_params.n_segments = [algo_params.n_segments] * n_annuli
    elif algo_params.n_segments == "auto":
        algo_params.n_segments = []
        algo_params.n_segments.append(2)  # for first annulus
        algo_params.n_segments.append(3)  # for second annulus
        ld = 2 * np.tan(360 / 4 / 2) * annulus_width
        for i in range(2, n_annuli):  # rest of annuli
            radius = i * annulus_width
            ang = np.rad2deg(2 * np.arctan(ld / (2 * radius)))
            algo_params.n_segments.append(int(np.ceil(360 / ang)))

    if algo_params.verbose:
        print("Annuli = {}".format(n_annuli))

    # Azimuthal averaging of residuals
    if algo_params.azimuth_overlap is None:
        algo_params.azimuth_overlap = 360  # no overlapping, single config of segments
    n_rots = int(360 / algo_params.azimuth_overlap)

    matrix_s = np.zeros((n_rots, n, y, x))
    if algo_params.full_output:
        matrix_l = np.zeros((n_rots, n, y, x))
        matrix_g = np.zeros((n_rots, n, y, x))

    # Looping the he annuli
    if algo_params.verbose:
        print("Processing annulus: ")
    for ann in range(n_annuli):
        inner_radius = algo_params.radius_int + ann * annulus_width
        n_segments_ann = algo_params.n_segments[ann]
        if algo_params.verbose:
            print(f"{ann+1} : in_rad={inner_radius}, n_segm={n_segments_ann}")

        # TODO: pool_map as in xloci function: build first a list
        for i in range(n_rots):
            theta_init = i * algo_params.azimuth_overlap
            indices = get_annulus_segments(
                algo_params.cube[0],
                inner_radius,
                annulus_width,
                n_segments_ann,
                theta_init,
            )

            add_params = {
                "indices": indices,
                "i_patch": iterable(range(n_segments_ann)),
                "n_segments_ann": n_segments_ann,
                "verbose": False,
            }

            func_params = setup_parameters(
                params_obj=algo_params, fkt=_decompose_patch, as_list=True, **add_params
            )

            patches = pool_map(
                algo_params.nproc,
                _decompose_patch,
                *func_params,
            )

            for j in range(n_segments_ann):
                yy = indices[j][0]
                xx = indices[j][1]

                if algo_params.full_output:
                    matrix_l[i, :, yy, xx] = patches[j][0]
                    matrix_s[i, :, yy, xx] = patches[j][1]
                    matrix_g[i, :, yy, xx] = patches[j][2]
                else:
                    matrix_s[i, :, yy, xx] = patches[j]

    if algo_params.full_output:
        list_s_array_der = [
            cube_derotate(
                matrix_s[k],
                algo_params.angle_list,
                nproc=algo_params.nproc,
                **rot_options,
            )
            for k in range(n_rots)
        ]
        list_frame_s = [
            cube_collapse(list_s_array_der[k], mode=algo_params.collapse)
            for k in range(n_rots)
        ]
        frame_s = cube_collapse(np.array(list_frame_s),
                                mode=algo_params.collapse)

        list_l_array_der = [
            cube_derotate(
                matrix_l[k],
                algo_params.angle_list,
                nproc=algo_params.nproc,
                **rot_options,
            )
            for k in range(n_rots)
        ]
        list_frame_l = [
            cube_collapse(list_l_array_der[k], mode=algo_params.collapse)
            for k in range(n_rots)
        ]
        frame_l = cube_collapse(np.array(list_frame_l),
                                mode=algo_params.collapse)

        list_g_array_der = [
            cube_derotate(
                matrix_g[k],
                algo_params.angle_list,
                nproc=algo_params.nproc,
                **rot_options,
            )
            for k in range(n_rots)
        ]
        list_frame_g = [
            cube_collapse(list_g_array_der[k], mode=algo_params.collapse)
            for k in range(n_rots)
        ]
        frame_g = cube_collapse(np.array(list_frame_g),
                                mode=algo_params.collapse)

    else:
        list_s_array_der = [
            cube_derotate(
                matrix_s[k],
                algo_params.angle_list,
                nproc=algo_params.nproc,
                **rot_options,
            )
            for k in range(n_rots)
        ]
        list_frame_s = [
            cube_collapse(list_s_array_der[k], mode=algo_params.collapse)
            for k in range(n_rots)
        ]

        frame_s = cube_collapse(np.array(list_frame_s),
                                mode=algo_params.collapse)

    if algo_params.verbose:
        print("")
        timing(start_time)

    if algo_params.full_output:
        return (
            list_l_array_der,
            list_s_array_der,
            list_g_array_der,
            frame_l,
            frame_s,
            frame_g,
        )
    else:
        return frame_s


def _decompose_patch(
    indices,
    i_patch,
    n_segments_ann,
    rank,
    low_rank_ref,
    low_rank_mode,
    thresh,
    thresh_mode,
    max_iter,
    auto_rank_mode,
    cevr,
    residuals_tol,
    random_seed,
    debug=False,
    full_output=False,
):
    """Patch decomposition."""
    j = i_patch
    yy = indices[j][0]
    xx = indices[j][1]
    data_segm = cube_init[:, yy, xx]

    if low_rank_ref:
        ref_segments = list(range(n_segments_ann))
        ref_segments.pop(j)
        for m, n in enumerate(ref_segments):
            if m == 0:
                yy_ref = indices[n][0]
                xx_ref = indices[n][1]
            else:
                yy_ref = np.hstack((yy_ref, indices[n][0]))
                xx_ref = np.hstack((xx_ref, indices[n][1]))
        data_ref = cube_init[:, yy_ref, xx_ref]
    else:
        data_ref = data_segm

    patch = _patch_rlrps(
        data_segm,
        data_ref,
        rank,
        low_rank_ref,
        low_rank_mode,
        thresh,
        thresh_mode,
        max_iter,
        auto_rank_mode,
        cevr,
        residuals_tol,
        random_seed,
        debug=debug,
        full_output=full_output,
    )
    return patch


def _patch_rlrps(
    array,
    array_ref,
    rank,
    low_rank_ref,
    low_rank_mode,
    thresh,
    thresh_mode,
    max_iter,
    auto_rank_mode="noise",
    cevr=0.9,
    residuals_tol=1e-2,
    random_seed=None,
    debug=False,
    full_output=False,
):
    """Patch decomposition based on GoDec/SSGoDec (Zhou & Tao 2011)"""
    ############################################################################
    # Initializing L and S
    ############################################################################
    L = array
    if low_rank_ref:
        L_ref = array_ref.T
    else:
        L_ref = None
    S = np.zeros_like(L)
    random_state = np.random.RandomState(random_seed)
    itr = 0
    power = 0
    svdlib = "lapack"

    while itr <= max_iter:
        ########################################################################
        # Updating L
        ########################################################################
        if low_rank_mode == "brp":
            Y2 = random_state.randn(L.shape[1], rank)
            for _ in range(power + 1):
                Y1 = np.dot(L, Y2)
                Y2 = np.dot(L.T, Y1)
            Q, _ = qr(Y2, mode="economic")
            Lnew = np.dot(np.dot(L, Q), Q.T)

        elif low_rank_mode == "svd":
            if itr == 0:
                PC = get_eigenvectors(
                    rank,
                    L,
                    svdlib,
                    mode=auto_rank_mode,
                    cevr=cevr,
                    noise_error=residuals_tol,
                    data_ref=L_ref,
                    debug=debug,
                    collapse=True,
                    scaling="temp-standard",
                )
                rank = PC.shape[0]  # so we can use the optimized rank
                if low_rank_ref:
                    Lnew = np.dot(np.dot(PC, L).T, PC).T
                else:
                    Lnew = np.dot(np.dot(L, PC.T), PC)
            else:
                rank_i = min(rank, min(L.shape[0], L.shape[1]))
                PC = svd_wrapper(L, svdlib, rank_i, False,
                                 random_state=random_state)
                Lnew = np.dot(np.dot(L, PC.T), PC)

        else:
            raise RuntimeError("Low Rank estimation mode not recognized.")

        ########################################################################
        # Updating S
        ########################################################################
        T = L - Lnew + S
        threshold = np.sqrt(median_absolute_deviation(T.ravel())) * thresh

        # threshold = np.sqrt(median_absolute_deviation(T, axis=0)) * thresh
        # threshmat = np.zeros_like(T)
        # for i in range(threshmat.shape[0]):
        #     threshmat[i] = threshold
        # threshold = threshmat

        if debug:
            print("threshold = {:.3f}".format(threshold))
        S = thresholding(T, threshold, thresh_mode)

        T -= S
        L = Lnew + T
        itr += 1

    G = array - L - S

    L = L.T
    S = S.T
    G = G.T

    if full_output:
        return L, S, G
    else:
        return S


def thresholding(array, threshold, mode):
    """Array thresholding strategies."""
    x = array.copy()
    if mode == "soft":
        j = np.abs(x) <= threshold
        x[j] = 0
        k = np.abs(x) > threshold
        if np.isscalar(threshold):
            x[k] = x[k] - np.sign(x[k]) * threshold
        else:
            x[k] = x[k] - np.sign(x[k]) * threshold[k]
    elif mode == "hard":
        j = np.abs(x) < threshold
        x[j] = 0
    elif mode == "nng":
        j = np.abs(x) <= threshold
        x[j] = 0
        j = np.abs(x) > threshold
        x[j] = x[j] - threshold**2 / x[j]
    elif mode == "greater":
        j = x < threshold
        x[j] = 0
    elif mode == "less":
        j = x > threshold
        x[j] = 0
    else:
        raise RuntimeError("Thresholding mode not recognized")
    return x
