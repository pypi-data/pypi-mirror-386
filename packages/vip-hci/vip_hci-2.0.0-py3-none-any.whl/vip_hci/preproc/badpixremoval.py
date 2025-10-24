#! /usr/bin/env python
"""
Module with functions for correcting bad pixels in cubes.

.. [AAC01]
   | Aach & Metzler 2001
   | **Defect interpolation in digital radiography how object-oriented
     transform coding helps**
   | *SPIE, Proceedings Volume 4322, Medical Imaging 2001: Image Processing*
   | `https://doi.org/10.1117/12.431161
     <https://doi.org/10.1117/12.431161>`_

"""
import warnings
__author__ = ('V. Christiaens, Carlos Alberto Gomez Gonzalez, '
              'Srikanth Kompella')
__all__ = ['frame_fix_badpix_isolated',
           'cube_fix_badpix_isolated',
           'cube_fix_badpix_annuli',
           'cube_fix_badpix_clump',
           'cube_fix_badpix_ifs',
           'cube_fix_badpix_interp',
           'frame_fix_badpix_fft']

import numpy as np
from skimage.draw import disk, ellipse
from scipy.ndimage import median_filter
from astropy.stats import sigma_clipped_stats
from multiprocessing import cpu_count
from ..stats import clip_array, sigma_filter
from ..var import frame_center, get_annulus_segments, frame_filter_lowpass
from ..config import timing, time_ini, Progressbar
from ..config.utils_conf import pool_map, iterable
from .rescaling import find_scal_vector, frame_rescaling
from .cosmetics import frame_pad
from multiprocessing import Process
import multiprocessing
from multiprocessing import set_start_method
shared_mem = True
try:
    from multiprocessing import shared_memory
except ImportError:
    print('Failed to import shared_memory from multiprocessing')
    try:
        print('Trying to import shared_memory directly(for python 3.7)')
        import shared_memory
    except ModuleNotFoundError:
        shared_mem = False
        print("WARNING: multiprocessing unavailable for bad pixel correction.")
        print('Either pip install shared-memory38, or upgrade to python>=3.8')

try:
    from numba import njit
    no_numba = False
except ImportError:
    msg = "Numba python bindings are missing."
    warnings.warn(msg, ImportWarning)
    no_numba = True


def frame_fix_badpix_isolated(array, bpm_mask=None, correct_only=False,
                              sigma_clip=3, num_neig=5, size=5, protect_mask=0,
                              excl_mask=None, cxy=None, mad=False,
                              ignore_nan=True, verbose=True, full_output=False):
    """ Corrects the bad pixels, marked in the bad pixel mask. The bad pixel is
    replaced by the median of the adjacent pixels. This function is very fast
    but works only with isolated (sparse) pixels.

    Parameters
    ----------
    array : numpy ndarray
        Input 2d array.
    bpm_mask : numpy ndarray, optional
        Input bad pixel map. Should have same size as array. Binary map where
        the bad pixels have a value of 1. If None is provided a bad pixel map
        will be created using sigma clip statistics.
    correct_only : bool, opt
        If True and bpix_map is provided, will only correct for provided bad
        pixels. Else, the algorithm will determine (more) bad pixels.
    sigma_clip : int, optional
        In case no bad pixel mask is provided all the pixels above and below
        sigma_clip*STDDEV will be marked as bad.
    num_neig : int, optional
        The side of the square window around each pixel where the sigma clipped
        statistics are calculated (STDDEV and MEDIAN). If the value is equal to
        0 then the statistics are computed in the whole frame.
    size : odd int, optional
        The size the box (size x size) of adjacent pixels for the median
        filter.
    protect_mask : int or float, optional
        If larger than 0, radius of a circular aperture (at the center of the
        frames) in which no bad pixels will be identified. This can be useful
        to protect the star and vicinity.
    excl_mask : numpy ndarray, optional
        Binary mask with 1 in areas that should not be considered as good
        neighbouring pixels during the identification of bad pixels. These
        should not be considered as bad pixels to be corrected neither (i.e.
        different to bpm_mask).
    cxy: None or tuple
        If protect_mask is True, this is the location of the star centroid in
        the images. If None, assumes the star is already centered. If a tuple,
        the location of the star is assumed to be the same in all frames of the
        cube.
    mad : {False, True}, bool optional
        If True, the median absolute deviation will be used instead of the
        standard deviation.
    ignore_nan: bool, optional
        Whether to not consider NaN values as bad pixels. If False, will also
        correct them.
    verbose : bool, optional
        If True additional information will be printed.
    full_output: bool, {False,True}, optional
        Whether to return as well the cube of bad pixel maps and the cube of
        defined annuli.

    Return
    ------
    frame : numpy ndarray
        Frame with bad pixels corrected.
    bpm_mask: 2d array
        The bad pixel map
    """
    if array.ndim != 2:
        raise TypeError('Array is not a 2d array or single frame')
    if size % 2 == 0:
        raise TypeError('Size of the median blur kernel must be an odd integer')
    if correct_only and bpm_mask is None:
        msg = "Bad pixel map should be provided if correct_only is True."
        raise ValueError(msg)

    if bpm_mask is not None:
        msg = "Input bad pixel mask should have same shape as array\n"
        assert bpm_mask.shape == array.shape, msg
        bpm_mask = bpm_mask.astype('bool')
    if excl_mask is None:
        excl_mask = np.zeros(array.shape, dtype=bool)
    else:
        msg = "Input exclusion mask should have same shape as array\n"
        assert excl_mask.shape == array.shape, msg
    ind_excl = np.where(excl_mask)

    if verbose:
        start = time_ini()

    if num_neig > 0:
        neigh = True
    else:
        neigh = False

    frame = array.copy()
    if cxy is None:
        cy, cx = frame_center(frame)
    else:
        cx, cy = cxy

    if bpm_mask is None or not correct_only:
        if bpm_mask is None:
            bpm_mask = np.zeros(array.shape, dtype=bool)
        bpm_mask = bpm_mask+excl_mask
        bpm_mask[np.where(bpm_mask > 1)] = 1
        ori_nan_mask = np.where(np.isnan(frame))
        ind = clip_array(frame, sigma_clip, sigma_clip, bpm_mask,
                         neighbor=neigh, num_neighbor=num_neig, mad=mad)
        bpm_mask = np.zeros(frame.shape, dtype=bool)
        bpm_mask[ind] = True
        if ignore_nan:
            bpm_mask[ori_nan_mask] = False
        if protect_mask:
            cir = disk((cy, cx), protect_mask, shape=bpm_mask.shape)
            bpm_mask[cir] = False
        bpm_mask[ind_excl] = False
        bpm_mask = bpm_mask.astype('bool')

    smoothed = median_filter(frame, size, mode='mirror')
    frame[np.where(bpm_mask)] = smoothed[np.where(bpm_mask)]
    array_out = frame
    count_bp = np.sum(bpm_mask)

    if verbose:
        msg = "Done replacing {} bad pixels using the median of neighbors"
        print(msg.format(count_bp))
        timing(start)

    if full_output:
        return array_out, bpm_mask
    else:
        return array_out


def cube_fix_badpix_isolated(array, bpm_mask=None, correct_only=False,
                             sigma_clip=3, num_neig=5, size=5,
                             frame_by_frame=False, protect_mask=0,
                             excl_mask=None, cxy=None, mad=False,
                             ignore_nan=True, verbose=True, full_output=False,
                             nproc=1):
    """Correct bad pixels, either marked in input bad pixel mask or identified\
    through sigma clipping.

    The bad pixels are replaced by the median of the adjacent pixels. This
    function is very fast but works only with sparse bad pixels. Consider the
    iterative ``vip_hci.preproc.cube_fix_badpix_clump`` function to identify and
    correct clumps of bad pixels.

    Parameters
    ----------
    array : numpy ndarray
        Input 3d array.
    bpm_mask : numpy ndarray, optional
        Input bad pixel map. Zeros frame where the bad pixels have a value of 1.
        If None is provided a bad pixel map will be created per frame using
        sigma clip statistics.
    correct_only : bool, opt
        If True and bpix_map is provided, will only correct for provided bad
        pixels. Else, the algorithm will determine (more) bad pixels.
    sigma_clip : int, optional
        In case no bad pixel mask is provided all the pixels above and below
        sigma_clip*STDDEV will be marked as bad.
    num_neig : int, optional
        The side of the square window around each pixel where the sigma clipped
        statistics are calculated (STDDEV and MEDIAN). If the value is equal to
        0 then the statistics are computed in the whole frame.
    size : odd int, optional
        The size the box (size x size) of adjacent pixels for the median filter.
    frame_by_frame: bool, optional
        Whether to correct bad pixels frame by frame in the cube. By default it
        is set to False; the bad pixels are computed on the mean frame of the
        stack (faster but not necessarily optimal).
    protect_mask : int or float, optional
        If larger than 0, radius of a circular aperture (at the center of the
        frames) in which no bad pixels will be identified. This can be useful
        to protect the star and vicinity.
    excl_mask : numpy ndarray, optional
        Binary mask with 1 in areas that should not be considered as good
        neighbouring pixels during the identification of bad pixels. These
        should not be considered as bad pixels to be corrected neither (i.e.
        different to bpm_mask).
    cxy: None, tuple or 2d numpy ndarray
        If protect_mask is True, this is the location of the star centroid in
        the images. If None, assumes the star is already centered. If a tuple,
        the location of the star is assumed to be the same in all frames of the
        cube. If a (n_frames x 2) ndarray, it should contain the xy location of
        the star in each frame.
    mad : {False, True}, bool optional
        If True, the median absolute deviation will be used instead of the
        standard deviation.
    ignore_nan: bool, optional
        Whether to not consider NaN values as bad pixels. If False, will also
        correct them.
    verbose : bool, optional
        If True additional information will be printed.
    full_output: bool, {False,True}, optional
        Whether to return as well the cube of bad pixel maps and the cube of
        defined annuli.
    nproc: int, optional
        This feature is added following ADACS update. Refers to the number of
        processors available for calculations. Choosing a number >1 enables
        multiprocessing for the correction of frames. This happens only when
        ``frame_by_frame=True''.

    Return
    ------
    array_out : numpy ndarray
        Cube with bad pixels corrected.
    bpm_mask: 2d or 3d array [if full_output is True]
        The bad pixel map or the cube of bad pixel maps

    """
    if array.ndim != 3:
        raise TypeError('Array is not a 3d array or cube')
    if size % 2 == 0:
        raise TypeError('Size of the median blur kernel must be an odd integer')
    if correct_only and bpm_mask is None:
        msg = "Bad pixel map should be provided if correct_only is True."
        raise ValueError(msg)

    if bpm_mask is not None:
        msg = "Input bad pixel mask should have same last 2 dims as array\n"
        assert bpm_mask.shape[-2:] == array.shape[-2:], msg
        bpm_mask = bpm_mask.astype('bool')

    if verbose:
        start = time_ini()

    if num_neig > 0:
        neigh = True
    else:
        neigh = False

    nz = array.shape[0]

    if cxy is None:
        cy, cx = frame_center(array[0])
    elif isinstance(cxy, tuple):
        cx, cy = cxy
    elif isinstance(cxy, np.ndarray):
        if cxy.shape[0] != nz or cxy.shape[1] != 2 or cxy.ndim != 2:
            raise ValueError("cxy does not have right shape")
        elif not frame_by_frame:
            msg = "cxy must be a tuple or None if not in frame_by_frame mode"
            raise ValueError(msg)
        else:
            cx = cxy[:, 0]
            cy = cxy[:, 1]

    array_out = array.copy()
    final_bpm = np.zeros_like(array_out, dtype=bool)
    n_frames = array.shape[0]
    count_bp = 0
    if frame_by_frame:
        if np.isscalar(cx):
            cx = [cx]*nz
            cy = [cy]*nz
        if bpm_mask is not None:
            if bpm_mask.ndim == 2:
                bpm_mask = [bpm_mask]*n_frames
                bpm_mask = np.array(bpm_mask)
        if nproc == 1 or not shared_mem:
            for i in Progressbar(range(n_frames), desc="processing frames"):
                if bpm_mask is not None:
                    bpm_mask_tmp = bpm_mask[i]
                else:
                    bpm_mask_tmp = None
                if excl_mask is not None:
                    excl_mask_tmp = excl_mask[i]
                else:
                    excl_mask_tmp = None
                res = frame_fix_badpix_isolated(array[i], bpm_mask=bpm_mask_tmp,
                                                correct_only=correct_only,
                                                sigma_clip=sigma_clip,
                                                num_neig=num_neig, size=size,
                                                protect_mask=protect_mask,
                                                excl_mask=excl_mask_tmp,
                                                verbose=False,
                                                cxy=(cx[i], cy[i]),
                                                ignore_nan=ignore_nan,
                                                full_output=True)
                array_out[i] = res[0]
                final_bpm[i] = res[1]
        else:
            if verbose:
                print("Cleaning frames using ADACS' multiprocessing approach")
            # dummy calling the function to create cached version of the code
            # prior to forking
            if bpm_mask is not None:
                bpm_mask_dum = bpm_mask[0]
            else:
                bpm_mask_dum = None
            if excl_mask is not None:
                excl_mask_dum = excl_mask[0]
            else:
                excl_mask_dum = None
            # point of dummy call
            frame_fix_badpix_isolated(array[0], bpm_mask=bpm_mask_dum,
                                      correct_only=correct_only,
                                      sigma_clip=sigma_clip, num_neig=num_neig,
                                      size=size, protect_mask=protect_mask,
                                      excl_mask=excl_mask_dum, verbose=False,
                                      cxy=(cx[0], cy[0]), ignore_nan=ignore_nan,
                                      full_output=False)
            # multiprocessing included only in the frame-by-frame branch of the
            # if statement above.
            # creating shared memory buffer for the cube (array)
            shm_arr = shared_memory.SharedMemory(create=True, size=array.nbytes)
            # creating a shared array_out version that is the shm_array_out
            # buffer above.
            sh_arr = np.ndarray(array.shape, dtype=array.dtype,
                                buffer=shm_arr.buf)
            # creating shared memory buffer for the final bad pixel mask cube.
            shm_fbpm = shared_memory.SharedMemory(create=True,
                                                  size=final_bpm.nbytes)
            # creating a shared final_bpm version that is in the shm_final_bpm
            # buffer above.
            sh_fbpm = np.ndarray(final_bpm.shape, dtype=final_bpm.dtype,
                                 buffer=shm_fbpm.buf)

            # function that calls frame_fix_badpix_isolated using the similar
            # arguments as in if nproc==1 branch above.
            def mp_clean_isolated(j, frame, bpm_mask=None, sigma_clip=3,
                                  num_neig=5, size=5, protect_mask=0,
                                  excl_mask=None, verbose=False, cxy=None,
                                  ignore_nan=True, full_output=True):
                sh_res = frame_fix_badpix_isolated(frame, bpm_mask,
                                                   correct_only=correct_only,
                                                   sigma_clip=sigma_clip,
                                                   num_neig=num_neig, size=size,
                                                   protect_mask=protect_mask,
                                                   excl_mask=excl_mask,
                                                   verbose=verbose, cxy=cxy,
                                                   ignore_nan=ignore_nan,
                                                   full_output=full_output)
                sh_arr[j], sh_fbpm[j] = sh_res
            # function that unwraps the arguments and passes them to
            # mp_clean_isolated.
            global _mp_clean_isolated

            def _mp_clean_isolated(args):
                pargs = args[0:2]
                kwargs = args[2]
                mp_clean_isolated(*pargs, **kwargs)

            context = multiprocessing.get_context('fork')
            pool = context.Pool(processes=nproc, maxtasksperchild=1)

            args = []
            for j in range(n_frames):
                if bpm_mask is not None:
                    bpm_mask_tmp = bpm_mask[j]
                else:
                    bpm_mask_tmp = None
                if excl_mask is not None:
                    excl_mask_tmp = excl_mask[j]
                else:
                    excl_mask_tmp = None
                dict_kwargs = {'bpm_mask': bpm_mask_tmp,
                               'sigma_clip': sigma_clip, 'num_neig': num_neig,
                               'size': size, 'protect_mask': protect_mask,
                               'excl_mask': excl_mask_tmp,
                               'cxy': (cx[j], cy[j]),
                               'ignore_nan': ignore_nan}
                args.append([j, array[j], dict_kwargs])

            try:
                pool.map_async(_mp_clean_isolated, args,
                               chunksize=1).get(timeout=10_000_000)
            finally:
                pool.close()
                pool.join()
                array_out[:] = sh_arr[:]
                final_bpm[:] = sh_fbpm[:]
                shm_arr.close()
                shm_arr.unlink()
                shm_fbpm.close()
                shm_fbpm.unlink()
        count_bp = np.sum(final_bpm)
    else:
        if excl_mask is None:
            excl_mask = np.zeros(array.shape[-2:], dtype=bool)
        elif excl_mask.ndim == 3:
            excl_mask = np.median(excl_mask, axis=0)
        else:
            msg = "Input exclusion mask should have same last 2 dims as array\n"
            assert excl_mask.shape == array.shape[-2:], msg
        ind_excl = np.where(excl_mask)
        if bpm_mask is None or not correct_only:
            if bpm_mask is None:
                bpm_mask = np.zeros(array.shape[-2:], dtype=bool)
            elif bpm_mask.ndim == 3:
                bpm_mask = np.median(bpm_mask, axis=0)
            all_excl_mask = bpm_mask+excl_mask
            ori_nan_mask = np.where(np.isnan(np.nanmean(array, axis=0)))
            ind = clip_array(np.nanmean(array, axis=0), sigma_clip, sigma_clip,
                             all_excl_mask, neighbor=neigh,
                             num_neighbor=num_neig, mad=mad)
            final_bpm = bpm_mask.copy()
            final_bpm[ind] = True
            if ignore_nan:
                final_bpm[ori_nan_mask] = False
            if protect_mask:
                cir = disk((cy, cx), protect_mask, shape=final_bpm.shape)
                final_bpm[cir] = False
            final_bpm[ind_excl] = False
            final_bpm = final_bpm.astype('bool')
        else:
            if bpm_mask.ndim == 3:
                final_bpm = np.median(bpm_mask, axis=0)
            else:
                final_bpm = bpm_mask.copy()

        for i in Progressbar(range(n_frames), desc="processing frames"):
            frame = array_out[i]
            smoothed = median_filter(frame, size, mode='mirror')
            frame[np.where(final_bpm)] = smoothed[np.where(final_bpm)]
            array_out[i] = frame
            if verbose:
                count_bp += np.sum(final_bpm)

    if verbose:
        msg = "Done replacing {:.0f} bad pixels using the median of neighbors"
        print(msg.format(count_bp))
        if not frame_by_frame:
            msg = "(i.e. {:.0f} static bad pixels per channel))"
            print(msg.format(count_bp/n_frames))
        timing(start)

    if full_output:
        return array_out, final_bpm
    else:
        return array_out


def cube_fix_badpix_annuli(array, fwhm, cy=None, cx=None, sig=5., bpm_mask=None,
                           protect_mask=0, excl_mask=None, r_in_std=50,
                           r_out_std=None, verbose=True, half_res_y=False,
                           min_thr=None, max_thr=None, min_thr_np=None,
                           bad_values=None, full_output=False):
    """
    Correct bad pixels in concentric annuli centered on the provided location\
    of the star, in an input frame or cube.

    This function is faster than ``cube_fix_badpix_clump``; hence to be
    preferred in all cases where there is only one bright source with circularly
    symmetric PSF. The bad pixel values are replaced by:
    ann_median + random_poisson;
    where ann_median is the median of the annulus, and random_poisson is
    random noise picked from a Poisson distribution centered on ann_median.

    Parameters
    ----------
    array : 3D or 2D array
        Input 3d cube or 2d image.
    fwhm: float or 1D array
        Vector containing the full width half maximum of the PSF in pixels, for
        each channel (cube_like); or single value (frame_like)
    cy, cx : None, float or 1D array, optional
        If None: will use the barycentre of the image found by
        photutils.centroid_com()
        If floats: coordinates of the center, assumed to be the same in all
        frames if the input is a cube.
        If 1D arrays: they must be the same length as the 0th dimension of the
        input cube.
    sig: Float scalar, optional
        Number of stddev above or below the median of the pixels in the same
        annulus, to consider a pixel as bad.
    bpm_mask: 3D or 2D array, opt
        Input bad pixel array. If 2D and array is 3D: should have same last 2
        dimensions as array. If 3D, should have exact same dimensions as input
        array. If not provided, the algorithm will attempt to identify bad pixel
        clumps automatically.
    protect_mask : int or float, optional
        If larger than 0, radius of a circular aperture (at the center of the
        frames) in which no bad pixels will be identified. This can be useful
        to protect the star and vicinity.
    excl_mask : numpy ndarray, optional
        Binary mask with 1 in areas that should not be considered as good
        neighbouring pixels during the identification of bad pixels. These
        should not be considered as bad pixels to be corrected neither (i.e.
        different to bpm_mask).
    r_in_std: float or None, optional
        Inner radius (in pixels) of the annulus used for the calculation of the
        standard deviation of the background noise - used as a min threshold
        when identifying bad pixels. Default: 50.
    r_out_std: float or None, optional
        Outer radius in pixels of the annulus used for the calculation of the
        standard deviation of the background noise - used as a min threshold
        when identifying bad pixels. If set to None, the default will be to
        consider the largest annulus starting at r_in_std which fits within the
        frame.
    verbose: bool, {False, True}, optional
        Whether to print out the number of bad pixels in each frame.
    half_res_y: bool, {True,False}, optional
        Whether the input data have only half the angular resolution vertically
        compared to horizontally (e.g. SINFONI data).
        The algorithm will then correct the bad pixels every other row.
    min_thr, max_thr: {None,float}, optional
        Any pixel whose value is lower (resp. larger) than this threshold will
        be automatically considered bad and hence sigma_filtered. If None, it
        is not used.
    min_thr_np: {None, float}, optional
        Any pixel whose value is lower than this threshold will be automatically
        considered bad and hence sigma_filtered, EVEN if located within the
        radius of protect_mask.
    bad_values: list or None, optional
        If not None, should correspond to a list of known bad values (e.g. 0).
        These pixels will be added to the input bad pixel map.
    full_output: bool, {False,True}, optional
        Whether to return as well the cube of bad pixel maps and the cube of
        defined annuli.

    Returns
    -------
    array_corr: 2d or 3d array
        The bad pixel corrected frame/cube.
    bpix_map: 2d or 3d array
        [full_output=True] The bad pixel map or the cube of bpix maps
    ann_frame_cumul: 2 or 3d array
        [full_output=True] The cube of defined annuli

    """
    ndims = array.ndim
    assert ndims == 2 or ndims == 3, "Object is not two or three dimensional.\n"

    # thresholds
    if min_thr is None:
        min_thr = np.amin(array)-1
    if max_thr is None:
        max_thr = np.amax(array)-1

    if bpm_mask is not None:
        msg = "Input bad pixel mask should have same last 2 dims as array\n"
        assert bpm_mask.shape[-2:] == array.shape[-2:], msg
        bpm_mask = bpm_mask.astype('bool')

    if bad_values is not None:
        if bpm_mask is None:
            bpm_mask = np.zeros(array.shape, dtype=bool)
        for bad in bad_values:
            bpm_mask[np.where(array == bad)] = 1

    def bp_removal_2d(array, cy, cx, fwhm, sig, protect_mask, bpm_mask_ori,
                      excl_mask, r_in_std, r_out_std, verbose):

        msg = "Input exclusion mask should have same shape as array\n"
        assert excl_mask.shape == array.shape, msg
        ind_excl = np.where(excl_mask)

        frame = array.copy()
        n_x = array.shape[1]
        n_y = array.shape[0]

        # Squash the frame if twice less resolved vertically than horizontally
        if half_res_y:
            if n_y % 2 != 0:
                msg = 'The input frames do not have of an even number of rows. '
                msg2 = 'Hence, you should not use option half_res_y = True'
                raise ValueError(msg+msg2)
            n_y = int(n_y/2)
            cy = int(cy/2)
            array = np.zeros([n_y, n_x])
            excl_mask_corr = np.zeros([n_y, n_x])
            for yy in range(n_y):
                array[yy] = frame[2*yy]
                excl_mask_corr[yy] = excl_mask[2*yy]
            excl_mask = excl_mask_corr
            if bpm_mask_ori is not None:
                bpm_mask_tmp = np.zeros([n_y, n_x])
                for yy in range(n_y):
                    bpm_mask_tmp[yy] = bpm_mask_ori[2*yy]
                bpm_mask_ori = bpm_mask_tmp

        # 1/ Stddev of background
        if r_in_std or r_out_std:
            r_in_std = min(r_in_std*fwhm, cx-2, cy-2, n_x-cx-2, n_y-cy-2)
            if r_out_std:
                r_out_std *= fwhm
            else:
                r_out_std = min(n_y-(cy+r_in_std), cy-r_in_std,
                                n_x-(cx+r_in_std), cx-r_in_std)
            width = max(2, r_out_std-r_in_std)
            array_crop = get_annulus_segments(array, r_in_std, width,
                                              mode="val")
        else:
            array_crop = array
        _, _, stddev = sigma_clipped_stats(array_crop, sigma=2.5)

        # 2/ Define each annulus, its median and stddev

        ymax = max(cy, n_y-cy)
        xmax = max(cx, n_x-cx)
        if half_res_y:
            ymax *= 2
        rmax = np.sqrt(ymax**2+xmax**2)
        # the annuli definition is optimized for Airy rings
        ann_width = max(1.5, 0.5*fwhm)  # 0.61*fwhm
        nrad = int(rmax/ann_width)+1
        d_bord_max = max(n_y-cy, cy, n_x-cx, cx)
        if half_res_y:
            d_bord_max = max(2*(n_y-cy), 2*cy, n_x-cx, cx)

        big_ell_frame = np.zeros_like(array)
        sma_ell_frame = np.zeros_like(array)
        ann_frame_cumul = np.zeros_like(array)
        n_neig = np.zeros(nrad, dtype=np.int16)
        med_neig = np.zeros(nrad)
        std_neig = np.zeros(nrad)
        neighbours = np.zeros([nrad, n_y*n_x])

        bpm_mask = excl_mask.copy()
        if bpm_mask_ori is not None:
            bpm_mask += bpm_mask_ori.astype(bool)

        if min_thr_np is not None:
            bpm_mask[np.where(array < min_thr_np)] = 1

        ind_bad = np.where(bpm_mask)

        for rr in range(nrad):
            if rr > int(d_bord_max/ann_width):
                # just to merge farthest annuli with very few elements
                rr_big = nrad
                rr_sma = int(d_bord_max/ann_width)
            else:
                rr_big = rr
                rr_sma = rr
            if half_res_y:
                big_ell_idx = ellipse(r=cy, c=cx,
                                      r_radius=((rr_big+1)*ann_width)/2,
                                      c_radius=(rr_big+1)*ann_width,
                                      shape=(n_y, n_x))
                if rr != 0:
                    small_ell_idx = ellipse(r=cy, c=cx,
                                            r_radius=(rr_sma*ann_width)/2,
                                            c_radius=rr_sma*ann_width,
                                            shape=(n_y, n_x))
            else:
                big_ell_idx = disk((cy, cx), radius=(rr_big+1)*ann_width,
                                   shape=(n_y, n_x))
                if rr != 0:
                    small_ell_idx = disk((cy, cx), radius=rr_sma*ann_width,
                                         shape=(n_y, n_x))
            big_ell_frame[big_ell_idx] = 1
            if rr != 0:
                sma_ell_frame[small_ell_idx] = 1
            sma_ell_frame[ind_bad] = 1
            ann_frame = big_ell_frame - sma_ell_frame
            n_neig[rr] = ann_frame[np.where(ann_frame)].shape[0]
            neighbours[rr, :n_neig[rr]] = array[np.where(ann_frame)]
            ann_frame_cumul[np.where(ann_frame)] = rr

            # We delete iteratively max and min outliers in each annulus,
            # so that the annuli median and stddev are not corrupted by bpixs
            neigh = neighbours[rr, :n_neig[rr]]
            n_rm = 0
            n_pix_init = neigh.shape[0]
            while neigh.shape[0] >= np.amin(n_neig[rr]) and n_rm < n_pix_init/5:
                min_neigh = np.amin(neigh)
                if reject_outliers(neigh, min_neigh, m=5, stddev=stddev):
                    min_idx = np.argmin(neigh)
                    neigh = np.delete(neigh, min_idx)
                    n_rm += 1
                else:
                    max_neigh = np.amax(neigh)
                    if reject_outliers(neigh, max_neigh, m=5, stddev=stddev):
                        max_idx = np.argmax(neigh)
                        neigh = np.delete(neigh, max_idx)
                        n_rm += 1
                    else:
                        break
            n_neig[rr] = neigh.shape[0]
            neighbours[rr, :n_neig[rr]] = neigh
            neighbours[rr, n_neig[rr]:] = 0
            med_neig[rr] = np.median(neigh)
            std_neig[rr] = np.std(neigh)

        # 3/ Create a tuple-array with coordinates of a circle of radius 1.8fwhm
        # centered on the provided coordinates of the star
        if protect_mask:
            if half_res_y:
                circl_new = ellipse(cy, cx, r_radius=protect_mask/2.,
                                    c_radius=protect_mask, shape=(n_y, n_x))
            else:
                circl_new = disk((cy, cx), radius=protect_mask,
                                 shape=(n_y, n_x))
        else:
            circl_new = []

        # 4/ Loop on all pixels to check bpix
        array_corr, bpix_map = correct_ann_outliers(array, bpm_mask, ann_width,
                                                    sig, med_neig, std_neig, cy,
                                                    cx, min_thr, max_thr,
                                                    stddev, half_res_y)

        # 5/ Count bpix and uncorrect if within the circle
        nbpix_tot = int(np.sum(bpix_map))
        nbpix_tbc = int(nbpix_tot - np.sum(bpix_map[circl_new]))

        if min_thr_np is not None:
            bp_tmp = np.zeros_like(bpix_map)
            bp_tmp[circl_new] = 1
            cond1 = array >= min_thr_np
            cond2 = bp_tmp == 1
            fin_mask = np.where(cond1 & cond2)
            bpix_map[fin_mask] = 0
            array_corr[fin_mask] = array[fin_mask]
        else:
            bpix_map[circl_new] = 0
            array_corr[circl_new] = array[circl_new]
        if verbose:
            print(nbpix_tot, ' bpix in total, and ', nbpix_tbc, ' corrected.')

        # Unsquash all the frames
        if half_res_y:
            frame = array_corr.copy()
            frame_bpix = bpix_map.copy()
            n_y = 2*n_y
            array_corr = np.zeros([n_y, n_x])
            bpix_map = np.zeros([n_y, n_x])
            ann_frame = ann_frame_cumul.copy()
            ann_frame_cumul = np.zeros([n_y, n_x])
            for yy in range(n_y):
                array_corr[yy] = frame[int(yy/2)]
                bpix_map[yy] = frame_bpix[int(yy/2)]
                ann_frame_cumul[yy] = ann_frame[int(yy/2)]

        # Include + exclude relevant pixels
        array_corr[ind_excl] = frame[ind_excl]
        bpix_map[ind_excl] = 0

        return array_corr, bpix_map, ann_frame_cumul

    if cy is None or cx is None:
        cy, cx = frame_center(array)
    if ndims == 2:
        if excl_mask is None:
            excl_mask = np.zeros(array.shape, dtype=bool)
        array_corr, bpix_map, ann_frame_cumul = bp_removal_2d(array, cy, cx,
                                                              fwhm, sig,
                                                              protect_mask,
                                                              bpm_mask,
                                                              excl_mask,
                                                              r_in_std,
                                                              r_out_std,
                                                              verbose)
    if ndims == 3:
        array_corr = array.copy()
        n_z = array.shape[0]
        bpix_map = np.zeros_like(array)
        ann_frame_cumul = np.zeros_like(array)
        if np.isscalar(fwhm):
            fwhm = [fwhm]*n_z
        if np.isscalar(cx) and np.isscalar(cy):
            cy = [cy]*n_z
            cx = [cx]*n_z
        if bpm_mask is None:
            bpm_mask = np.zeros(array_corr.shape, dtype=bool)
        elif bpm_mask.ndim == 2:
            bpm_mask = np.array([bpm_mask]*n_z, dtype=bool)
        if excl_mask is None:
            excl_mask = np.zeros(array_corr.shape, dtype=bool)
        elif excl_mask.ndim == 2:
            excl_mask = np.array([excl_mask]*n_z, dtype=bool)
        for i in range(n_z):
            if verbose:
                print('************Frame # ', i, ' *************')
                print('centroid assumed at coords:', cx[i], cy[i])
            res_i = bp_removal_2d(array[i], cy[i], cx[i], fwhm[i], sig,
                                  protect_mask, bpm_mask[i], excl_mask[i],
                                  r_in_std, r_out_std, verbose)
            array_corr[i], bpix_map[i], ann_frame_cumul[i] = res_i

    if full_output:
        return array_corr, bpix_map, ann_frame_cumul
    else:
        return array_corr


def cube_fix_badpix_clump(array, bpm_mask=None, correct_only=False, cy=None,
                          cx=None, fwhm=4., sig=4., protect_mask=0,
                          excl_mask=None, half_res_y=False, min_thr=None,
                          max_nit=15, mad=True, bad_values=None, verbose=True,
                          full_output=False, debug=True, nproc=1):
    """
    Identify and correct clumps of bad pixels.

    Very fast when a bad pixel map is provided. If a bad pixel map is not
    provided, the bad pixel clumps will be searched iteratively and replaced by
    the median of good neighbouring pixel values, when enough of them are
    available. The size of the box is set by the closest odd integer larger than
    fwhm (to avoid accidentally replacing point sources).

    Parameters
    ----------
    array : 3D or 2D array
        Input 3d cube or 2d image.
    bpm_mask: 3D or 2D array, opt
        Input bad pixel array. If 2D and array is 3D: should have same last 2
        dimensions as array. If 3D, should have exact same dimensions as input
        array. If not provided, the algorithm will attempt to identify bad pixel
        clumps automatically.
    correct_only : bool, opt
        If True and bpix_map is provided, will only correct for provided bad
        pixels. Else, the algorithm will determine (more) bad pixels.
    cy,cx : float or 1D array. opt
        Vector with approximate y and x coordinates of the star for each channel
        (cube_like), or single 2-elements vector (frame_like). These will be
        used if bpix_map is None and protect_mask set to True. If left to None,
        default values will correspond to the central pixel coordinates.
    fwhm: float or 1D array, opt
        Vector containing the full width half maximum of the PSF in pixels, for
        each channel (cube_like); or single value (frame_like). Should be
        provided if bpix map is None.
    sig: float, optional
        Value representing the number of "sigmas" above or below the "median" of
        the neighbouring pixel, to consider a pixel as bad. See details on
        parameter "m" of function reject_outlier.
    protect_mask : int or float, optional
        If larger than 0, radius of a circular aperture (at the center of the
        frames) in which no bad pixels will be identified. This can be useful
        to protect the star and vicinity.
    excl_mask : numpy ndarray, optional
        Binary mask with same dimensions as array, with 1 in areas that should
        not be considered as good neighbouring pixels during the identification
        of bad pixels. These should not be considered as bad pixels to be
        corrected neither (i.e. different to bpm_mask).
    half_res_y: bool, {True,False}, optional
        Whether the input data has only half the angular resolution vertically
        compared to horizontally (e.g. the case of SINFONI data); in other words
        there are always 2 rows of pixels with exactly the same values.
        The algorithm will just consider every other row (hence making it
        twice faster), then apply the bad pixel correction on all rows.
    min_thr: float, tuple or None, opt
        If a float is provided, corresponds to a minimum absolute threshold
        below which pixels are not considered bad (can be used to avoid the
        identification of bad pixels within noise).
        If a tuple of 2 values, corresponds to the range of values within which
        not to consider a pixel as bad. (e.g. (-0.1, 10.)).
    max_nit: float, optional
        Maximum number of iterations on a frame to correct bpix. Typically, it
        should be set to less than ny/2 or nx/2. This is a mean of precaution in
        case the algorithm gets stuck with 2 neighbouring pixels considered bpix
        alternately on two consecutively iterations hence leading to an infinite
        loop (very very rare case).
    mad : {False, True}, bool optional
        If True, the median absolute deviation will be used instead of the
        standard deviation.
    bad_values: list or None, optional
        If not None, should correspond to a list of known bad values (e.g. 0).
        These pixels will be added to the input bad pixel map.
    verbose: bool, {False,True}, optional
        Whether to print the number of bad pixels and number of iterations
        required for each frame.
    full_output: bool, {False,True}, optional
        Whether to return as well the cube of bad pixel maps and the cube of
        defined annuli.
    debug: bool, {False,True}, optional
        In case the algorithm encounters a problem for a given frame of the
        cube, whether to stop the function and write a fits file of it.
    nproc: int, optional
        This feature is added following ADACS update. Refers to the number of
        processors available for calculations. Choosing a number >1 enables
        multiprocessing for the correction of frames.

    Returns
    -------
    array_corr: 2d or 3d array
        The bad pixel corrected frame/cube.
    bpix_map: 2d or 3d array
        [full_output=True] The bad pixel map or the cube of bpix maps

    """
    array_corr = array.copy()
    ndims = array_corr.ndim
    assert ndims == 2 or ndims == 3, "Object is not two or three dimensional.\n"

    if bpm_mask is not None:
        msg = "Input bad pixel mask should have same last 2 dims as array\n"
        assert bpm_mask.shape[-2:] == array.shape[-2:], msg
        bpm_mask = bpm_mask.astype('bool')

    if bad_values is not None:
        if bpm_mask is None:
            bpm_mask = np.zeros(array_corr.shape, dtype=bool)
        for bad in bad_values:
            bpm_mask[np.where(array_corr == bad)] = 1

    if correct_only and bpm_mask is None:
        msg = "Bad pixel map should be provided if correct_only is True."
        raise ValueError(msg)

    def bp_removal_2d(array_corr, cy, cx, fwhm, sig, protect_mask, bpm_mask_ori,
                      excl_mask, min_thr, half_res_y, mad, verbose):

        msg = "Input exclusion mask should have same shape as array\n"
        assert excl_mask.shape == array_corr.shape, msg
        ind_excl = np.where(excl_mask)

        n_x = array_corr.shape[1]
        n_y = array_corr.shape[0]

        if half_res_y:
            if n_y % 2 != 0:
                msg = 'The input frames do not have of an even number of rows. '
                msg2 = 'Hence, you should not use option half_res_y = True'
                raise ValueError(msg+msg2)
            n_y = int(n_y/2)
            frame = array_corr.copy()
            array_corr = np.zeros([n_y, n_x])
            excl_mask_corr = np.zeros([n_y, n_x])
            for yy in range(n_y):
                array_corr[yy] = frame[2*yy]
                excl_mask_corr[yy] = excl_mask[2*yy]
            excl_mask = excl_mask_corr
            if bpm_mask_ori is not None:
                bpm_mask_tmp = np.zeros([n_y, n_x])
                for yy in range(n_y):
                    bpm_mask_tmp[yy] = bpm_mask_ori[2*yy]
                bpm_mask_ori = bpm_mask_tmp

        fwhm_round = int(round(fwhm))
        # This should reduce the chance to accidentally correct a bright planet:
        if fwhm_round % 2 == 0:
            neighbor_box = max(3, fwhm_round+1)
        else:
            neighbor_box = max(3, fwhm_round)
        nneig = sum(np.arange(3, neighbor_box+2, 2))

        # 1/ Create a tuple-array with coordinates of a circle of radius 1.8fwhm
        # centered on the approximate coordinates of the star
        if protect_mask:
            if half_res_y:
                circl_new = ellipse(int(cy/2), cx, r_radius=0.5*protect_mask,
                                    c_radius=protect_mask, shape=(n_y, n_x))
            else:
                circl_new = disk((cy, cx), radius=protect_mask,
                                 shape=(n_y, n_x))
        else:
            circl_new = []

        # 3/ Create a bad pixel map, by detecting them with clip_array
        bpm_mask = excl_mask.copy()
        if bpm_mask_ori is not None:
            bpm_mask += bpm_mask_ori.astype(bool)
        try:
            bp = clip_array(array_corr, sig, sig, bpm_mask, out_good=False,
                            neighbor=True, num_neighbor=neighbor_box, mad=mad,
                            half_res_y=half_res_y)
        except AssertionError:
            msg = "Prob with clip array using lower and upper sigma set to {},"
            msg += "{} bad pixels in in input bad pixel mask,"
            msg += "{} neighbours in neighbour box"
            print(msg.format(sig, np.sum(bpm_mask), neighbor_box))
            from vip_hci.fits import write_fits
            write_fits("TMP.fits", array_corr)
        bpix_map = np.zeros_like(array_corr)
        bpix_map[bp] = 1
        if min_thr is not None:
            if np.isscalar(min_thr):
                min_thr = (-min_thr, min_thr)
            elif not isinstance(min_thr, tuple):
                msg = "if provided, min_thr should be float or tuple"
                raise ValueError(msg)
            else:
                if len(min_thr) != 2:
                    msg = "if min_thr is a tuple, it should have 2 elements"
                    raise ValueError(msg)
            cond1 = array_corr > min_thr[0]
            cond2 = array_corr < min_thr[1]
            bpix_map[np.where(cond1 & cond2)] = 0
        nbpix_tot = int(np.sum(bpix_map))
        bpix_map[circl_new] = 0
        bpix_map[ind_excl] = 0
        nbpix_tbc = int(np.sum(bpix_map))
        bpix_map_cumul = np.zeros(bpix_map.shape, dtype=bool)
        bpix_map_cumul[:] = bpix_map[:]
        nit = 0

        # 4/ Loop over the bpix correction with sigma_filter, until 0 bpix left
        while nbpix_tbc > 0 and nit < max_nit:
            nit = nit+1
            if verbose:
                msg = "Iteration {}: {} bad pixels identified".format(nit,
                                                                      nbpix_tot)
                # if bpm_mask_ori is not None:
                #     nbpix_ori = np.sum(bpm_mask_ori)
                #     msg += " ({} new ones)".format(nbpix_tot-nbpix_ori)
                if protect_mask:
                    msg += ", {} to be corrected".format(nbpix_tbc)
                print(msg)
            array_corr = sigma_filter(array_corr, bpix_map,
                                      neighbor_box=neighbor_box,
                                      min_neighbors=nneig, half_res_y=half_res_y,
                                      verbose=verbose)
            bpm_mask = None  # known bad ones are corrected above +=bpix_map_cumul
            bp = clip_array(array_corr, sig, sig, bpm_mask, out_good=False,
                            neighbor=True, num_neighbor=neighbor_box, mad=mad,
                            half_res_y=half_res_y)
            bpix_map = np.zeros(array_corr.shape, dtype=bool)
            bpix_map[bp] = 1
            if min_thr is not None:
                cond1 = array_corr > min_thr[0]
                cond2 = array_corr < min_thr[1]
                bpix_map[np.where(cond1 & cond2)] = 0
            nbpix_tot = int(np.sum(bpix_map))
            bpix_map[circl_new] = 0
            bpix_map[ind_excl] = 0
            nbpix_tbc = int(np.sum(bpix_map))
            bpix_map_cumul = bpix_map_cumul+bpix_map

        if verbose:
            print('All bad pixels are corrected.')

        if half_res_y:
            frame = array_corr.copy()
            frame_bpix = bpix_map_cumul.copy()
            n_y = 2*n_y
            array_corr = np.zeros([n_y, n_x])
            bpix_map_cumul = np.zeros([n_y, n_x])
            for yy in range(n_y):
                array_corr[yy] = frame[int(yy/2)]
                bpix_map_cumul[yy] = frame_bpix[int(yy/2)]

        return array_corr, bpix_map_cumul

    if ndims == 2:
        if bpm_mask is None or not correct_only:
            if (cy is None or cx is None) and protect_mask:
                cy, cx = frame_center(array)
            if excl_mask is None:
                excl_mask = np.zeros(array_corr.shape, dtype=bool)
            array_corr, bpix_map_cumul = bp_removal_2d(array_corr, cy, cx, fwhm,
                                                       sig, protect_mask,
                                                       bpm_mask, excl_mask,
                                                       min_thr, half_res_y, mad,
                                                       verbose)
        else:
            fwhm_round = int(round(fwhm))
            fwhm_round = fwhm_round+1-(fwhm_round % 2)  # make it odd
            neighbor_box = max(3, fwhm_round)  # to not replace a companion
            nneig = sum(np.arange(3, neighbor_box+2, 2))
            array_corr = sigma_filter(array_corr, bpm_mask, neighbor_box, nneig,
                                      half_res_y, verbose)
            bpix_map_cumul = bpm_mask

    if ndims == 3:
        n_z = array_corr.shape[0]
        if bpm_mask is None or not correct_only:
            if bpm_mask is None:
                bpm_mask = np.zeros(array_corr.shape, dtype=bool)
            elif bpm_mask.ndim == 2:
                bpm_mask = np.array([bpm_mask]*n_z, dtype=bool)
            if excl_mask is None:
                excl_mask = np.zeros(array_corr.shape, dtype=bool)
            elif excl_mask.ndim == 2:
                excl_mask = np.array([excl_mask]*n_z, dtype=bool)
            if cy is None or cx is None:
                cy, cx = frame_center(array)
                cy = [cy]*n_z
                cx = [cx]*n_z
            elif np.isscalar(cy) and np.isscalar(cx):
                cy = [cy]*n_z
                cx = [cx]*n_z
            if np.isscalar(fwhm):
                fwhm = [fwhm]*n_z
            if nproc == 1 or not shared_mem:
                bpix_map_cumul = np.zeros_like(array_corr)
                for i in range(n_z):
                    if verbose:
                        print('************Frame # ', i, ' *************')
                    res = bp_removal_2d(array_corr[i], cy[i], cx[i], fwhm[i],
                                        sig, protect_mask, bpm_mask[i],
                                        excl_mask[i], min_thr, half_res_y, mad,
                                        verbose)
                    array_corr[i], bpix_map_cumul[i] = res
            else:
                if verbose:
                    print("Cleaning frames using ADACS' multiprocessing approach")
                # creating shared memory buffer space for the image cube.
                shm_clump = shared_memory.SharedMemory(create=True,
                                                       size=array_corr.nbytes)
                obj_tmp_shared_clump = np.ndarray(array_corr.shape,
                                                  dtype=array_corr.dtype,
                                                  buffer=shm_clump.buf)
                # creating shared memory buffer space for the bad pixel cube.
                shm_clump_bpix = shared_memory.SharedMemory(create=True,
                                                            size=array_corr.nbytes)
                # works with dtype=obj_tmp.dtype but not dtype=int
                bpix_map_cumul_shared = np.ndarray(array_corr.shape,
                                                   dtype=array_corr.dtype,
                                                   buffer=shm_clump_bpix.buf)

                def mp_clump_slow(j, array_corr, cy, cx, fwhm, sig, protect_mask,
                                  bpm_mask, excl_mask, min_thr, half_res_y, mad,
                                  verbose):
                    res = bp_removal_2d(array_corr, cy, cx, fwhm, sig,
                                        protect_mask, bpm_mask, excl_mask,
                                        min_thr, half_res_y, mad, verbose)
                    obj_tmp_shared_clump[j], bpix_map_cumul_shared[j] = res
                global _mp_clump_slow

                def _mp_clump_slow(args):
                    mp_clump_slow(*args)

                context = multiprocessing.get_context('fork')
                pool = context.Pool(processes=nproc, maxtasksperchild=1)
                args = []
                for i in range(n_z):
                    args.append([i, array_corr[i], cy[i], cx[i], fwhm[i], sig,
                                protect_mask, bpm_mask[i], excl_mask[i], min_thr,
                                half_res_y, mad, verbose])
                try:
                    pool.map_async(_mp_clump_slow, args, chunksize=1).get(
                        timeout=10_000_000)
                finally:
                    pool.close()
                    pool.join()
                    bpix_map_cumul = np.zeros_like(array_corr,
                                                   dtype=array_corr.dtype)
                    bpix_map_cumul[:] = bpix_map_cumul_shared[:]
                    array_corr[:] = obj_tmp_shared_clump[:]
                    shm_clump.close()
                    shm_clump.unlink()
                    shm_clump_bpix.close()
                    shm_clump_bpix.unlink()

        else:
            if np.isscalar(fwhm):
                fwhm_round = int(round(fwhm))
            else:
                fwhm_round = int(np.median(fwhm))
            fwhm_round = fwhm_round+1-(fwhm_round % 2)  # make it odd
            neighbor_box = max(3, fwhm_round)  # to not replace a companion
            nneig = sum(np.arange(3, neighbor_box+2, 2))

            if nproc == 1 or not shared_mem:
                for i in range(n_z):
                    if verbose:
                        print('Using serial approach')
                        print('************Frame # ', i, ' *************')
                    if bpm_mask.ndim == 3:
                        bpm = bpm_mask[i]
                    else:
                        bpm = bpm_mask
                    array_corr[i] = sigma_filter(array_corr[i], bpm,
                                                 neighbor_box, nneig, half_res_y,
                                                 verbose)
            else:
                if verbose:
                    print("Cleaning frames using ADACS' multiprocessing approach")
                # dummy calling sigma_filter function to create a cached version of the numba function
                if bpm_mask.ndim == 3:
                    dummy_bpm = bpm_mask[0]
                else:
                    dummy_bpm = bpm_mask
                # Actual dummy call is here.
                sigma_filter(array_corr[0], dummy_bpm,
                             neighbor_box, nneig, half_res_y, verbose)
                # creating shared memory that each process writes into.
                shm_clump = shared_memory.SharedMemory(
                    create=True, size=array_corr.nbytes)
                # creating an array that uses shared memory buffer and has the properties of array_corr.
                obj_tmp_shared_clump = np.ndarray(
                    array_corr.shape, dtype=array_corr.dtype, buffer=shm_clump.buf)
                # function that is called repeatedly by each process.

                def mp_clean_clump(j, array_corr, bpm, neighbor_box, nneig,
                                   half_res_y, verbose):
                    obj_tmp_shared_clump[j] = sigma_filter(array_corr, bpm,
                                                           neighbor_box, nneig,
                                                           half_res_y, verbose)

                global _mp_clean_clump
                # function that converts the args into bite-sized pieces for mp_clean_clump.

                def _mp_clean_clump(args):
                    mp_clean_clump(*args)
                context = multiprocessing.get_context('fork')
                pool = context.Pool(processes=nproc, maxtasksperchild=1)
                args = []
                for j in range(n_z):
                    if bpm_mask.ndim == 3:
                        bpm = bpm_mask[j]
                    else:
                        bpm = bpm_mask
                    args.append([j, array_corr[j], bpm, neighbor_box,
                                nneig, half_res_y, verbose])
                try:
                    pool.map_async(_mp_clean_clump, args, chunksize=1).get(
                        timeout=10_000_000)
                finally:
                    pool.close()
                    pool.join()
                    array_corr[:] = obj_tmp_shared_clump[:]
                    shm_clump.close()
                    shm_clump.unlink()
            bpix_map_cumul = bpm_mask

    # make it a binary map
    bpix_map_cumul[np.where(bpix_map_cumul > 1)] = 1

    if full_output:
        return array_corr, bpix_map_cumul
    else:
        return array_corr


def cube_fix_badpix_ifs(array, lbdas, fluxes=None, mask=None, cy=None, cx=None,
                        clumps=True, sigma_clip=3, num_neig=5, size=5,
                        protect_mask=0, mad=False, fwhm=4, min_thr=None,
                        max_nit=15, imlib='vip-fft', interpolation='lanczos4',
                        ignore_nan=True, verbose=True, full_output=False):
    """
    Function to identify and correct bad pixels in an IFS cube, leveraging on
    the radial expansion of the PSF with wavelength.
    Bad pixel identification is done with either the `cube_fix_badpix_isolated`
    or the `cube_fix_badpix_clump` function in PSF subtracted frames (through
    SDI).

    Parameters
    ----------
    array : 3D or 4D array
        Input 3D (spectral) or 4D (spectral+temporal) cube. In the latter case,
        dimensions should be spectral x temporal x vertical x horizontal.
    lbdas: 1d array or list
        Vector with the wavelengths, used for first guess on scaling factor.
    fluxes: 1d array or list, optional
        Vector with the (unsaturated) fluxes at the different wavelengths,
        used for first guess on flux factor.
    mask: 2D-array, opt
        Binary mask, with ones where the residual intensities should be
        evaluated. If None is provided, the whole field is used.
    cy, cx : None, float or 1D array, optional
        If None: will use the barycentre of the image found by
        photutils.centroid_com()
        If floats: coordinates of the center, assumed to be the same in all
        frames if the input is a cube.
        If 1D arrays: they must be the same length as the 0th dimension of the
        input cube.
    clumps: bool, optional
        Whether to use `cube_fix_badpix_clump` (True) or
        `cube_fix_badpix_isolated` (False) in the SDI residual cube.
    sigma_clip : int, optional
        In case no bad pixel mask is provided all the pixels above and below
        sigma_clip*STDDEV will be marked as bad.
    num_neig : int, optional
        The side of the square window around each pixel where the sigma clipped
        statistics are calculated (STDDEV and MEDIAN). If the value is equal to
        0 then the statistics are computed in the whole frame.
    size : odd int, optional
        The size the box (size x size) of adjacent pixels for the median filter.
    protect_mask : int or float, optional
        If larger than 0, radius of a circular aperture (at the center of the
        frames) in which no bad pixels will be identified. This can be useful
        to protect the star and vicinity.
    mad : {False, True}, bool optional
        If True, the median absolute deviation will be used instead of the
        standard deviation.
    fwhm: float or 1D array, opt
        Vector containing the full width half maximum of the PSF in pixels, for
        each channel (cube_like); or single value (frame_like). Shouod be
        provided if bpix map is None.
    min_thr: float, tuple or None, opt
        If a float is provided, corresponds to a minimum absolute threshold
        below which pixels are not considered bad in the residua images (can be
        used to avoid the identification of bad pixels within noise).
        If a tuple of 2 values, corresponds to the range of values within which
        not to consider a pixel as bad, in the residual images (e.g. (-1, 5)).
    max_nit: float, optional
        Maximum number of iterations on a frame to correct bpix. Typically, it
        should be set to less than ny/2 or nx/2. This is a mean of precaution in
        case the algorithm gets stuck with 2 neighbouring pixels considered bpix
        alternately on two consecutively iterations hence leading to an infinite
        loop (very very rare case).

    ignore_nan: bool, optional
        Whether to not consider NaN values as bad pixels. If False, will also
        correct them.
    verbose : bool, optional
        If True additional information will be printed.
    full_output: bool, {False,True}, optional
        Whether to return as well the cube of bad pixel maps and the cube of
        defined annuli.

    Return
    ------
    array_out : numpy ndarray
        Cube with bad pixels corrected.
    bpm_mask: 2d or 3d array [if full_output is True]
        The bad pixel map or the cube of bpix maps
    array_res: 2d or 3d array [if full_output is True]
        SDI-residual cube in which bad pixels are identified
    """

    def _res_scaled_images(array, lbdas, fluxes, mask, cy, cx):
        if fluxes is None:
            fluxes = [1]*len(lbdas)
        if cx is None or cy is None:
            ref_xy = None
        else:
            ref_xy = (cx, cy)
        scal_vec, flux_vec = find_scal_vector(array, lbdas, fluxes, mask=mask,
                                              nfp=2, fm="sum", imlib=imlib,
                                              interpolation=interpolation)
        res_array = np.zeros_like(array)
        for z in range(array.shape[0]):
            other_ch = [i for i in range(array.shape[0]) if i != z]
            res_arr_tmp = []
            for zp in other_ch:
                flux_scal = flux_vec[zp]/flux_vec[z]
                resc_fr = frame_rescaling(flux_scal*array[zp], ref_xy=ref_xy,
                                          scale=scal_vec[zp]/scal_vec[z],
                                          imlib=imlib,
                                          interpolation=interpolation)
                res_arr_tmp.append(array[z]-resc_fr)
            res_arr_tmp = np.array(res_arr_tmp)
            res_array[z] = np.median(res_arr_tmp, axis=0)

        return res_array

    cube = array.copy()
    ndims = cube.ndim

    if cy is None or cx is None:
        cxy = None
    else:
        cy, cx = frame_center(cube)
        cxy = (cx, cy)

    if ndims == 3:
        array_res = _res_scaled_images(cube, lbdas, fluxes, mask, cy, cx)
        # bad pixel identification in residual cube
        if clumps:
            _, final_bpm = cube_fix_badpix_clump(array_res, bpm_mask=None,
                                                 cy=cy, cx=cx, fwhm=fwhm,
                                                 sig=sigma_clip,
                                                 protect_mask=protect_mask,
                                                 verbose=verbose,
                                                 min_thr=min_thr,
                                                 max_nit=max_nit, mad=mad,
                                                 full_output=True)
        else:
            _, final_bpm = cube_fix_badpix_isolated(array_res, bpm_mask=None,
                                                    sigma_clip=sigma_clip,
                                                    num_neig=num_neig,
                                                    size=size,
                                                    frame_by_frame=True,
                                                    protect_mask=protect_mask,
                                                    cxy=cxy, mad=mad,
                                                    ignore_nan=ignore_nan,
                                                    verbose=verbose,
                                                    full_output=True)
        final_bpm[np.where(final_bpm > 1)] = 1
        # bad pixel correction in original cube
        array_out = cube_fix_badpix_isolated(cube, bpm_mask=final_bpm,
                                             sigma_clip=sigma_clip,
                                             num_neig=num_neig, size=size,
                                             frame_by_frame=True,
                                             protect_mask=protect_mask,
                                             cxy=cxy, mad=mad,
                                             ignore_nan=ignore_nan,
                                             verbose=verbose, full_output=False)

    elif ndims == 4:
        n_z = cube.shape[1]
        array_out = np.zeros_like(cube)
        array_res = np.zeros_like(cube)
        final_bpm = np.zeros_like(cube)
        if np.isscalar(cy) and np.isscalar(cx):
            cy = [cy]*n_z
            cx = [cx]*n_z
        for i in range(n_z):
            if verbose:
                print('************ Cube #{}/{} *************'.format(i+1, n_z))
            array_res[:, i] = _res_scaled_images(cube[:, i], lbdas, fluxes,
                                                 mask, cy, cx)

            # bad pixel identification in residual cube
            if clumps:
                res = cube_fix_badpix_clump(array_res[:, i], bpm_mask=None,
                                            cy=cy, cx=cx, fwhm=fwhm,
                                            sig=sigma_clip,
                                            protect_mask=protect_mask,
                                            verbose=verbose, min_thr=min_thr,
                                            max_nit=max_nit, mad=mad,
                                            full_output=True)
            else:
                res = cube_fix_badpix_isolated(array_res[:, i], bpm_mask=None,
                                               sigma_clip=sigma_clip,
                                               num_neig=num_neig, size=size,
                                               frame_by_frame=True,
                                               protect_mask=protect_mask,
                                               cxy=cxy, mad=mad,
                                               ignore_nan=ignore_nan,
                                               verbose=verbose,
                                               full_output=True)
            _, final_bpm[:, i] = res
            final_bpm[np.where(final_bpm > 1)] = 1
            # bad pixel correction in original cube
            array_out[:, i] = cube_fix_badpix_isolated(cube[:, i],
                                                       final_bpm[:, i],
                                                       correct_only=False,
                                                       sigma_clip=sigma_clip,
                                                       num_neig=num_neig,
                                                       size=size,
                                                       frame_by_frame=True,
                                                       protect_mask=protect_mask,
                                                       cxy=cxy, mad=mad,
                                                       ignore_nan=ignore_nan,
                                                       verbose=verbose,
                                                       full_output=False)

    else:
        raise TypeError("Input cube should be 3d or 4d")

    if full_output:
        return array_out, final_bpm, array_res
    else:
        return array_out


def cube_fix_badpix_interp(array, bpm_mask, mode='fft', excl_mask=None, fwhm=4.,
                           kernel_sz=None, psf=None, half_res_y=False, nit=500,
                           tol=1, nproc=1, full_output=False, **kwargs):
    """
    Function to correct clumps of bad pixels by interpolation with either a
    user-defined kernel (through astropy.convolution) or through the FFT-based
    algorithm described in [AAC01]_. A bad pixel map must be
    provided (e.g. found with function `cube_fix_badpix_clump`).

    Parameters
    ----------
    array : 3D or 2D array
        Input 3d cube or 2d image.
    bpm_mask: 3D or 2D array
        Input bad pixel array. Should have same x,y dimensions as array.
        If 2D, but input array is 3D, the same bpix_map will be assumed for all
        frames.
    mode: str, optional {'fft', 'gauss', 'psf'}
        Can be either a 2D Gaussian ('gauss') or an input normalized PSF
        ('psf').
    excl_mask: 3D or 2D array, optional
        [Only used if mode != 'fft'] Input exclusion mask array. Pixels in the
        exclusion mask will neither be used for interpolation, nor replaced as
        bad pixels. excl_mask should have same x,y dimensions as array. If 2D,
        but input array is 3D, the same exclusion mask will be assumed for all
        frames.
    fwhm: float, 1D array or tuple of 2 floats, opt
        If mode is 'gauss', the fwhm of the Gaussian.
    kernel_sz: int or None, optional
        Size of the kernel in pixels for 2D Gaussian and Moffat convolutions.
        If None, astropy.convolution will automatically consider 8*fwhm
        kernel sizes.
    psf: 2D or 3D array, optional
        If mode is 'psf', a normalized PSF array. If a 3D cube is provided
        (e.g. for spectral cubes), the first dimension should match that of the
        input array (which should also be 3D). Else, the same 2D PSF kernel
        will be for all input frames, whether the input is 2D or 3D.
        If half_res_y is True, psf should be provided vertically squashed.
    half_res_y: bool, {True,False}, optional
        Whether the input data has only half the angular resolution vertically
        compared to horizontally (e.g. the case for some IFUs); in other words
        there are always 2 rows of pixels with exactly the same values.
        If so, the Gaussian kernel will also be squashed vertically by a
        factor 2.
    nit: int or list of int, optional
        For FFT-based iterative interpolation, the number of iterations to use.
        If a list is provided, a list of bad pixel corrected frames/cubes is
        returned.
    tol: float
        Tolerance in terms of E_g (see [AAC01]_). The iterative process is
        stopped if the error E_g gets lower than this tolerance.
    nproc : None or int, optional
        Number of processes for parallel computing. If None the number of
        processes will be set to (cpu_count()/2). Note: only used for input
        3D cube and 'fft' mode.
    full_output: bool, {False,True}, optional
        In the case of FT-based interpolation, whether to return as well the
        reconstructed images.
    **kwargs : dict
        Passed through to the astropy.convolution.convolve or convolve_fft
        function.

    Returns
    -------
    array_corr: 2d or 3d array;
        The bad pixel corrected frame/cube.
    recon_cube: 2d or 3d array;
        [full_output=True & mode='fft'] The reconstructed frame/cube. If nit is
        a list, a list of reconstructed frames/cubes is returned.
    """

    ndims = array.ndim
    assert ndims == 2 or ndims == 3, "Object is not two or three dimensional.\n"

    if bpm_mask.shape[-2:] != array.shape[-2:]:
        raise TypeError("Bad pixel map has wrong y/x dimensions.")

    if excl_mask is None:
        excl_mask = np.zeros(array.shape, dtype=bool)
    elif excl_mask.ndim == 2 and array.ndim == 3:
        nz = array.shape[0]
        excl_mask = np.array([excl_mask]*nz, dtype=bool)
    msg = "Input exclusion mask should have same shape as array\n"
    assert excl_mask.shape[-2:] == array.shape[-2:], msg

    if np.sum(bpm_mask) == 0:
        msg = "Warning: no bad pixel found in bad pixel map. "
        msg += "Returning input array as is."
        print(msg)
        return array

    ny, nx = array.shape[-2:]
    if ndims == 3:
        nz = array.shape[0]

    if bpm_mask.ndim == 2 and ndims == 3:
        master_bpm = np.zeros([nz, ny, nx])
        for z in range(nz):
            master_bpm[z] = bpm_mask[np.newaxis, :, :]
        bpm_mask = master_bpm.copy()

    if half_res_y:
        # squash vertically
        def squash_v(array):
            ny, nx = array.shape
            if ny % 2:
                raise ValueError("Input array y dimension should be even")
            nny = ny//2
            new_array = np.zeros([nny, nx])
            for y in range(nny):
                new_array[y] = array[int(y*2)]
            return new_array

        if ndims == 2:
            array_squash = squash_v(array)
            bpm_mask = squash_v(bpm_mask)
            bpm_mask = squash_v(excl_mask)
        else:
            new_array_corr = []
            new_bpm_mask = []
            new_excl_mask = []
            for z in range(nz):
                new_array_corr.append(squash_v(array[z]))
                new_bpm_mask.append(squash_v(bpm_mask[z]))
                new_excl_mask.append(squash_v(excl_mask[z]))
            array_squash = np.array(new_array_corr)
            bpm_mask = np.array(new_bpm_mask)
            excl_mask = np.array(new_excl_mask)
        array_corr = array_squash.copy()
    else:
        array_corr = array.copy()
        array_squash = array.copy()

    if mode != 'fft':
        # first replace all bad pixels with NaNs - they will be interpolated
        array_corr[np.where(bpm_mask+excl_mask)] = np.nan
        if ndims == 2:
            array_corr_filt = frame_filter_lowpass(array_corr, mode=mode,
                                                   fwhm_size=fwhm,
                                                   conv_mode='conv',
                                                   kernel_sz=kernel_sz, psf=psf,
                                                   iterate=True,
                                                   half_res_y=half_res_y,
                                                   **kwargs)
        else:
            array_corr_filt = array_corr.copy()
            if np.isscalar(fwhm):
                fwhm = [fwhm]*nz
            elif len(fwhm) == 2 and len(fwhm) != nz:
                fwhm = [fwhm]*nz
            if psf is None:
                psf = [psf]*nz
            elif psf.ndim == 2:
                psf = [psf]*nz
            elif psf.shape[0] != nz:
                raise ValueError(
                    "input psf must have same z dimension as array")
            for z in range(nz):
                array_corr_filt[z] = frame_filter_lowpass(array_corr[z],
                                                          mode=mode,
                                                          fwhm_size=fwhm[z],
                                                          conv_mode='conv',
                                                          kernel_sz=kernel_sz,
                                                          psf=psf[z],
                                                          iterate=True,
                                                          half_res_y=half_res_y,
                                                          **kwargs)

        # replace only the bad pixels (array_corr is low-pass filtered)
        array_corr = array_squash.copy()  # redefined because NaNs otherwise
        array_corr[np.where(bpm_mask)] = array_corr_filt[np.where(bpm_mask)]

    else:
        full_bp_mask = np.zeros(array_corr.shape, dtype=bool)
        if ndims == 2:
            full_bp_mask[np.where(bpm_mask+excl_mask)] = 1
            res = frame_fix_badpix_fft(array_corr, full_bp_mask, nit=nit,
                                       tol=tol, full_output=full_output)
            if isinstance(nit, int):
                array_corr_filt = res
            else:
                array_corr_filt, recon_cube = res
        else:
            if bpm_mask.ndim == 2:
                bpm_mask = [bpm_mask]*nz
            full_bp_mask[np.where(bpm_mask+excl_mask)] = 1
            if nproc is None:
                nproc = cpu_count()//2
            res = pool_map(nproc, frame_fix_badpix_fft, iterable(array_corr),
                           iterable(full_bp_mask), nit, tol, 2, False,
                           full_output, msg="Correcting bad pixels")
            if full_output and isinstance(nit, int):
                array_corr_filt = np.array(res[:, 0], dtype=np.float64)
                recon_cube = np.array(res[:, 1], dtype=np.float64)
            elif full_output:
                nz = array_corr.shape[0]
                nnit = len(nit)
                tmp = res[:, 0]
                tmp2 = res[:, 1]
                array_corr_filt = []
                recon_cube = []
                for j in range(nnit):
                    tmp_list = [tmp[i][j] for i in range(nz)]
                    array_corr_filt.append(np.array(tmp_list))
                    tmp_list = [tmp2[i][j] for i in range(nz)]
                    recon_cube.append(np.array(tmp_list))
            else:
                array_corr_filt = np.array(res, dtype=np.float64)

        array_corr = array_squash.copy()  # redefined because NaNs otherwise
        array_corr[np.where(bpm_mask)] = array_corr_filt[np.where(bpm_mask)]

    if half_res_y:
        # unsquash vertically
        def unsquash_v(array):
            ny, nx = array.shape
            nny = int(ny*2)
            new_array_corr = np.zeros([nny, nx])
            for y in range(nny):
                new_array_corr[y] = array[y//2]
            return new_array_corr
        if ndims == 2:
            array_corr = unsquash_v(array_corr)
        else:
            new_array_corr = []
            for z in range(nz):
                new_array_corr.append(unsquash_v(array_corr[z]))
            array_corr = np.array(new_array_corr)

    if mode == 'fft' and full_output:
        return array_corr, recon_cube
    else:
        return array_corr


def find_outliers(frame, sig_dist, in_bpix=None, stddev=None, neighbor_box=3,
                  min_thr=None, mid_thr=None):
    """Estimate a bad pixel (or outlier) map for a given frame.

    Parameters
    ----------
    frame: 2d array
        Input 2d image.
    sig_dist: float
        Threshold used to discriminate good from bad neighbours, in terms of
        normalized distance to the median value of the set (see reject_outliers)
    in_bpix: 2d array, optional
        Input bpix map (typically known from the previous iteration), to only
        look for bpix around those locations.
    neighbor_box: int, optional
        The side of the square window around each pixel where the sigma and
        median are calculated for the bad pixel DETECTION and CORRECTION.
    min_thr: {None,float}, optional
        Any pixel whose value is lower than this threshold (expressed in adu)
        will be automatically considered bad and hence sigma_filtered. If None,
        it is not used.
    mid_thr: {None, float}, optional
        Pixels whose value is lower than this threshold (expressed in adu) will
        have its neighbours checked; if there is at max. 1 neighbour pixel whose
        value is lower than mid_thr+(5*stddev), then the pixel is considered bad
        (because it means it is a cold pixel in the middle of significant
        signal). If None, it is not used.

    Returns
    -------
    bpix_map : numpy ndarray
        Output cube with frames indicating the location of bad pixels

    """
    ndims = len(frame.shape)
    assert ndims == 2, "Object is not two dimensional.\n"

    nx = frame.shape[1]
    ny = frame.shape[0]
    bpix_map = np.zeros_like(frame)
    if stddev is None:
        stddev = np.std(frame)
    half_box = int(neighbor_box/2)

    if in_bpix is None:
        for xx in range(nx):
            for yy in range(ny):
                # 0/ Determine the box of neighbouring pixels
                # half size of the box at the bottom of the pixel
                hbox_b = min(half_box, yy)
                # half size of the box at the top of the pixel
                hbox_t = min(half_box, ny-1-yy)
                # half size of the box to the left of the pixel
                hbox_l = min(half_box, xx)
                # half size of the box to the right of the pixel
                hbox_r = min(half_box, nx-1-xx)
                # but in case we are at an edge, we want to extend the box by
                # one row/column of px in the direction opposite to the edge:
                if yy > ny-1-half_box:
                    hbox_b = hbox_b + (yy-(ny-1-half_box))
                elif yy < half_box:
                    hbox_t = hbox_t+(half_box-yy)
                if xx > nx-1-half_box:
                    hbox_l = hbox_l + (xx-(nx-1-half_box))
                elif xx < half_box:
                    hbox_r = hbox_r+(half_box-xx)

                # 1/ list neighbouring pixels, >8 (NOT including pixel itself)
                neighbours = frame[yy-hbox_b:yy+hbox_t+1,
                                   xx-hbox_l:xx+hbox_r+1]
                idx_px = ([[hbox_b], [hbox_l]])
                flat_idx = np.ravel_multi_index(idx_px, (hbox_t+hbox_b+1,
                                                         hbox_r+hbox_l+1))
                neighbours = np.delete(neighbours, flat_idx)

                # 2/ Det if central pixel is outlier
                test_result = reject_outliers(neighbours, frame[yy, xx],
                                              m=sig_dist, stddev=stddev,
                                              min_thr=min_thr, mid_thr=mid_thr)

                # 3/ Assign the value of the test to bpix_map
                bpix_map[yy, xx] = test_result

    else:
        nb = int(np.sum(in_bpix))  # number of bad pixels at previous iteration
        wb = np.where(in_bpix)     # pixels to check
        bool_bpix = np.zeros_like(in_bpix)
        for n in range(nb):
            for yy in [max(0, wb[0][n]-half_box), wb[0][n],
                       min(ny-1, wb[0][n]+half_box)]:
                for xx in [max(0, wb[1][n]-half_box), wb[1][n],
                           min(ny-1, wb[1][n]+half_box)]:
                    bool_bpix[yy, xx] = 1
        nb = int(np.sum(bool_bpix))  # true number of px to check  (including
        # neighbours of bpix from previous iteration)
        wb = np.where(bool_bpix)   # true px to check
        for n in range(nb):
            # 0/ Determine the box of neighbouring pixels
            # half size of the box at the bottom of the pixel
            hbox_b = min(half_box, wb[0][n])
            # half size of the box at the top of the pixel
            hbox_t = min(half_box, ny-1-wb[0][n])
            # half size of the box to the left of the pixel
            hbox_l = min(half_box, wb[1][n])
            # half size of the box to the right of the pixel
            hbox_r = min(half_box, nx-1-wb[1][n])
            # but in case we are at an edge, we want to extend the box by one
            # row/column of pixels in the direction opposite to the edge:
            if wb[0][n] > ny-1-half_box:
                hbox_b = hbox_b + (wb[0][n]-(ny-1-half_box))
            elif wb[0][n] < half_box:
                hbox_t = hbox_t+(half_box-wb[0][n])
            if wb[1][n] > nx-1-half_box:
                hbox_l = hbox_l + (wb[1][n]-(nx-1-half_box))
            elif wb[1][n] < half_box:
                hbox_r = hbox_r+(half_box-wb[1][n])

            # 1/ list neighbouring pixels, > 8, not including the pixel itself
            neighbours = frame[wb[0][n]-hbox_b:wb[0][n]+hbox_t+1,
                               wb[1][n]-hbox_l:wb[1][n]+hbox_r+1]
            c_idx_px = ([[hbox_b], [hbox_l]])
            flat_c_idx = np.ravel_multi_index(c_idx_px, (hbox_t+hbox_b+1,
                                                         hbox_r+hbox_l+1))
            neighbours = np.delete(neighbours, flat_c_idx)

            # 2/ test if bpix
            test_result = reject_outliers(neighbours, frame[wb[0][n], wb[1][n]],
                                          m=sig_dist, stddev=stddev,
                                          min_thr=min_thr, mid_thr=mid_thr)

            # 3/ Assign the value of the test to bpix_map
            bpix_map[wb[0][n], wb[1][n]] = test_result

    return bpix_map


def reject_outliers(data, test_value, m=5., stddev=None, debug=False):
    """ Function to reject outliers from a set.
    Instead of the classic standard deviation criterion (e.g. 5-sigma), the
    discriminant is determined as follow:
    - for each value in data, an absolute distance to the median of data is
    computed and put in a new array "d" (of same size as data)
    - scaling each element of "d" by the median value of "d" gives the absolute
    distances "s" of each element
    - each "s" is then compared to "m" (parameter): if s < m, we have a good
    neighbour, otherwise we have an outlier. A specific value test_value is
    tested as outlier.

    Parameters:
    -----------
    data: numpy ndarray
        Input array with respect to which either a test_value or the central a
        value of data is determined to be an outlier or not
    test_value: float
        Value to be tested as an outlier in the context of the input array data
    m: float, optional
        Criterion used to test if test_value is or pixels of data are outlier(s)
        (similar to the number of "sigma" in std_dev statistics)
    stddev: float, optional (but strongly recommended)
        Global std dev of the non-PSF part of the considered frame. It is needed
        as a reference to know the typical variation of the noise, and hence
        avoid detecting outliers out of very close pixel values. If the 9 pixels
        of data happen to be very uniform in values at some location, the
        departure in value of only one pixel could make it appear as a bad
        pixel. If stddev is not provided, the stddev of data is used (not
        recommended).

    Returns
    -------
    test_result: 0 or 1
        0 if test_value is not an outlier. 1 otherwise.
    """

    if no_numba:
        def _reject_outliers(data, test_value, m=5., stddev=None, debug=False):
            if stddev is None:
                stddev = np.std(data)

            med = np.median(data)
            d = np.abs(data - med)
            mdev = np.median(d)
            if debug:
                print("data = ", data)
                print("median(data)= ", np.median(data))
                print("d = ", d)
                print("mdev = ", mdev)
                print("stddev(box) = ", np.std(data))
                print("stddev(frame) = ", stddev)
                print("max(d) = ", np.max(d))

            if max(np.max(d), np.abs(test_value-med)) > stddev:
                mdev = mdev if mdev > stddev else stddev
                s = d/mdev
                if debug:
                    print("s =", s)
                test = np.abs((test_value-np.median(data))/mdev)
                if debug:
                    print("test =", test)
                else:
                    if test < m:
                        test_result = 0
                    else:
                        test_result = 1
            else:
                test_result = 0

            return test_result
        return _reject_outliers(data, test_value, m=m, stddev=stddev,
                                debug=debug)
    else:
        @njit
        def _reject_outliers(data, test_value, m=5., stddev=None):
            if stddev is None:
                stddev = np.std(data)

            med = np.median(data)
            d = data.copy()
            d_flat = d.flatten()
            for i in range(d_flat.shape[0]):
                d_flat[i] = np.abs(data.flatten()[i] - med)
            mdev = np.median(d_flat)
            if max(np.max(d), np.abs(test_value-med)) > stddev:
                test = np.abs((test_value-med)/mdev)
                if test < m:
                    test_result = 0
                else:
                    test_result = 1
            else:
                test_result = 0

            return test_result

        return _reject_outliers(data, test_value, m=m, stddev=stddev)


def correct_ann_outliers(array, bpix_map, ann_width, sig, med_neig, std_neig,
                         cy, cx, min_thr, max_thr, stddev, half_res_y=False):
    """Correct outliers in concentric annuli.

    Parameters
    ----------
    array: numpy ndarray
        Input array with respect to which either a test_value or the central
        value of data is determined to be an outlier or not
    bpix_map: numpy ndarray or None
        Input array of known bad pixels.
    ann_width: float
        Width of concenrtric annuli in pixels.
    sig: float
        Number of sigma to consider a pixel intensity as an outlier.
    med_neig, std_neig: 1d arrays
        Median and standard deviation of good pixel intensities in each annulus
    cy, cx: floats
        Coordinates of the center of the concentric annuli.
    min_thr, max_thr: {None,float}
        Any pixel whose value is lower (resp. larger) than this threshold will
        be automatically considered bad and hence sigma_filtered. If None, it
        is not used.
    stddev: float
        Global std dev of the non-PSF part of the considered frame. It is needed
        as a reference to know the typical variation of the noise, and hence
        avoid detecting outliers out of very close pixel values. If the 9 pixels
        of data happen to be very uniform in values at some location, the
        departure in value of only one pixel could make it appear as a bad
        pixel. If stddev is not provided, the stddev of data is used (not
        recommended).
    half_res_y: bool, {True,False}, optional
        Whether the input data have only half the angular resolution vertically
        compared to horizontally (e.g. SINFONI data).
        The algorithm will then correct the bad pixels every other row.

    Returns
    -------
    array_corr: np.array
        Array with corrected outliers.
    bpix_map: np.array
        Boolean array with location of outliers.

    """
    if no_numba:
        def _correct_ann_outliers(array, bpix_map, ann_width, sig, med_neig,
                                  std_neig, cy, cx, min_thr, max_thr, stddev,
                                  half_res_y=False):
            n_y, n_x = array.shape
            rand_arr = 2*(np.random.rand(n_y, n_x)-0.5)
            array_corr = array.copy()
            for yy in range(n_y):
                for xx in range(n_x):
                    if half_res_y:
                        rad = np.sqrt((2*(cy-yy))**2+(cx-xx)**2)
                    else:
                        rad = np.sqrt((cy-yy)**2+(cx-xx)**2)
                    rr = int(rad/ann_width)
                    dev = max(stddev, min(std_neig[rr], med_neig[rr]))

                    # check min_thr
                    if array[yy, xx] < min_thr:
                        bpix_map[yy, xx] = 1
                        array_corr[yy, xx] = med_neig[rr] + \
                            np.sqrt(np.abs(med_neig[rr]))*rand_arr[yy, xx]

                    # check max_thr
                    elif array[yy, xx] > max_thr:
                        bpix_map[yy, xx] = 1
                        array_corr[yy, xx] = med_neig[rr] + \
                            np.sqrt(np.abs(med_neig[rr]))*rand_arr[yy, xx]

                    elif (array[yy, xx] < med_neig[rr]-sig*dev or
                          array[yy, xx] > med_neig[rr]+sig*dev):
                        bpix_map[yy, xx] = 1

                    if bpix_map[yy, xx]:
                        array_corr[yy, xx] = med_neig[rr] + \
                            np.sqrt(np.abs(med_neig[rr]))*rand_arr[yy, xx]

            return array_corr, bpix_map
    else:
        @njit
        def _correct_ann_outliers(array, bpix_map, ann_width, sig, med_neig,
                                  std_neig, cy, cx, min_thr, max_thr, stddev,
                                  half_res_y=False):
            n_y, n_x = array.shape
            rand_arr = 2*(np.random.rand(n_y, n_x)-0.5)
            array_corr = array.copy()
            for yy in range(n_y):
                for xx in range(n_x):
                    if half_res_y:
                        rad = np.sqrt((2*(cy-yy))**2+(cx-xx)**2)
                    else:
                        rad = np.sqrt((cy-yy)**2+(cx-xx)**2)
                    rr = int(rad/ann_width)
                    dev = max(stddev, min(std_neig[rr], med_neig[rr]))

                    # check min_thr
                    if array[yy, xx] < min_thr:
                        bpix_map[yy, xx] = 1

                    # check max_thr
                    elif array[yy, xx] > max_thr:
                        bpix_map[yy, xx] = 1

                    elif (array[yy, xx] < med_neig[rr]-sig*dev or
                          array[yy, xx] > med_neig[rr]+sig*dev):
                        bpix_map[yy, xx] = 1

                    if bpix_map[yy, xx]:
                        array_corr[yy, xx] = med_neig[rr] + \
                            np.sqrt(np.abs(med_neig[rr]))*rand_arr[yy, xx]

            return array_corr, bpix_map

    return _correct_ann_outliers(array, bpix_map, ann_width, sig, med_neig,
                                 std_neig, cy, cx, min_thr, max_thr, stddev,
                                 half_res_y=half_res_y)


def frame_fix_badpix_fft(array, bpm_mask, nit=500, tol=1, pad_fac=2,
                         verbose=True, full_output=False):
    """
    Function to interpolate bad pixels with the FFT-based algorithm in [AAC01]_.

    Parameters
    ----------
    array : 2D ndarray
        Input image.
    bpm_mask : 2D ndarray
        Bad pixel map.
    nit: int or list of int, optional
        The number of iterations to use. If a list is provided, a list of bad
        pixel corrected frames/cubes is returned.
    tol: float, opt
        Tolerance in terms of E_g (see [AAC01]_). The iterative process is
        stopped if the error E_g gets lower than this tolerance.
    pad_fac: int or float, opt
        Padding factor before calculating 2D-FFT.
    verbose: bool
        Whether to print additional information during processing, incl.
        progress bar.
    full_output: bool
        Whether to also return the reconstructed estimate f_hat of the input
        array.

    Returns
    -------
    array_corr: 2D ndarray or list of 2D ndarray
        Image in which the bad pixels have been interpolated.
    f_est: 2D ndarray or list of 2D ndarray
        [full_output=True] Reconstructed estimate (f_hat in [AAC01]_) of the
        input array
    """

    if array.ndim != 2:
        raise TypeError("Input array should be 2D")
    if array.shape != bpm_mask.shape:
        raise TypeError("Input bad pixel map should have same shape as array")

    if isinstance(nit, list):
        nit_max = max(nit)
        return_list = True
    else:
        nit_max = nit
        return_list = False

    final_array_corr = []
    final_f_est = []

    # Pad zeros for better results
    ini_y, ini_x = array.shape
    pad_fac = (int(pad_fac*ini_x/ini_y), pad_fac)
    g = frame_pad(array, pad_fac, keep_parity=False, fillwith=0)
    w = frame_pad(1-bpm_mask, pad_fac, keep_parity=False, fillwith=0)

    # Following AAC01 notations:
    g *= w
    if verbose:
        start = time_ini()
    G_i = np.fft.fft2(g)
    W = np.fft.fft2(w)

    # Initialisation
    dims = g.shape
    ny, nx = dims
    npix = float(ny * nx)
    F_est = np.zeros(dims, dtype=complex)
    it = 0
    Eg = tol + 1

    for it in Progressbar(range(nit_max), desc="iterative bad pixel correction"):
        # 1. select line as max(G_i) and infer conjugate coordinates
        ind = np.unravel_index(np.argmax(np.abs(G_i.real[:, 0: nx // 2])),
                               (ny, nx // 2))

        ind_conj = (np.mod(ny - ind[0], ny),
                    np.mod(nx - ind[1], nx))

        # 2. compute the new F_i

        # handle cases with no conjugate:
        cond1 = (ind[0] == 0) and (ind[1] == 0)
        cond2 = (ind[0] == ny / 2) and (ind[1] == 0)
        cond3 = (ind[0] == 0) and (ind[1] == nx / 2)
        cond4 = (ind[0] == ny / 2) and (ind[1] == nx / 2)
        if cond1 or cond2 or cond3 or cond4:
            F_i = npix * G_i[ind] / W[(0, 0)]

            # 3a. update F_est
            F_est[ind] += F_i

        # handle cases where conjugate indices exist
        else:
            a = np.power(np.abs(W[(0, 0)]), 2)
            b = np.power(np.abs(W[(2 * ind[0]) % ny,
                                  (2 * ind[1]) % nx]), 2)

            Wmin = np.amin(np.abs(W))
            if a == b:
                # avoid later division by 0
                W[(2 * ind[0]) % ny, (2 * ind[1]) % nx] += Wmin*1e-11

            a = np.power(np.abs(W[(0, 0)]), 2)
            b = np.power(np.abs(W[(2 * ind[0]) % ny,
                                  (2 * ind[1]) % nx]), 2)
            c = a - b

            F_i = (npix/c) * (G_i[ind] * W[(0, 0)] - np.conj(G_i[ind]) *
                              W[(2 * ind[0]) % ny, (2 * ind[1]) % nx])

            # 3b. update F_est
            F_est[ind] += F_i
            F_est[ind_conj] += np.conj(F_i)

        # 4. get the new error spectrum
        G_i = get_err_spec(F_i, W, ind, npix, G_i, dims)

        # 5. Calculate new error - to check if still larger than tolerance
        Eg = np.sum(np.power(np.abs(G_i.flatten()), 2))/npix

        if (return_list and it in nit) or (it == nit_max-1) or (Eg < tol):
            array_corr = g + np.fft.ifft2(F_est).real * (1 - w)

            # crop zeros to return to initial size
            cy, cx = frame_center(array_corr)
            wy = (ini_y - 1) / 2
            wx = (ini_x - 1) / 2
            y0 = int(cy - wy)
            y1 = int(
                cy + wy + 1)  # +1 cause endpoint is excluded when slicing
            x0 = int(cx - wx)
            x1 = int(cx + wx + 1)
            final_array_corr.append(array_corr[y0:y1, x0:x1])

            # Calculate reconstructed image
            f_est = np.fft.ifft2(F_est).real
            final_f_est.append(f_est[y0:y1, x0:x1])

        if Eg < tol:
            break

    if verbose:
        msg = "FFT-interpolation terminated after {} iterations (Eg={})"
        print(msg.format(it+1, Eg))

    if verbose:
        timing(start)

    if not return_list:
        final_array_corr = final_array_corr[-1]
        final_f_est = final_f_est[-1]

    if full_output:
        return final_array_corr, final_f_est
    else:
        return final_array_corr


def get_err_spec(F_i, W, ind, npix, G_i, dims):

    def _err_spec(F_i, W, ind, npix, G_i, dims):
        ny, nx = dims
        conv = np.zeros(dims, dtype=np.complex64)

        cond1 = (ind[0] == 0) and (ind[1] == 0)
        cond2 = (ind[0] == ny / 2) and (ind[1] == 0)
        cond3 = (ind[0] == 0) and (ind[1] == nx / 2)
        cond4 = (ind[0] == ny / 2) and (ind[1] == nx / 2)
        # cases with no conjugate:
        if cond1 or cond2 or cond3 or cond4:
            for y in range(ny):
                for x in range(nx):
                    conv[y, x] = F_i * W[y - ind[0], x - ind[1]]
        else:
            for y in range(ny):
                for x in range(nx):
                    conv[y, x] = (F_i * W[y - ind[0], x - ind[1]] +
                                  np.conj(F_i) * W[(y + ind[0]) % ny,
                                                   (x + ind[1]) % nx])

        return G_i - conv/float(npix)

    if not no_numba:
        _err_spec_numba = njit(_err_spec)
        return _err_spec_numba(F_i, W, ind, npix, G_i, dims)
    else:
        return _err_spec(F_i, W, ind, npix, G_i, dims)
