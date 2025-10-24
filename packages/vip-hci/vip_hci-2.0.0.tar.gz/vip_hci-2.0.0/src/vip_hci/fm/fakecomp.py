#! /usr/bin/env python
"""Module with fake companion injection functions."""

__author__ = 'Carlos Alberto Gomez Gonzalez, Valentin Christiaens'
__all__ = ['collapse_psf_cube',
           'normalize_psf',
           'cube_inject_companions',
           'generate_cube_copies_with_injections',
           'frame_inject_companion',
           'cube_planet_free']

from multiprocessing import cpu_count
import numpy as np
from scipy import stats
from scipy.interpolate import interp1d

try:
    from photutils.aperture import aperture_photometry, CircularAperture
except:
    from photutils import aperture_photometry, CircularAperture
from photutils.centroids import centroid_com

from ..preproc import (cube_crop_frames, frame_shift, frame_crop, cube_shift,
                       frame_rotate)
from ..var import (frame_center, fit_2dgaussian, fit_2dairydisk, fit_2dmoffat,
                   get_circle, get_annulus_segments, dist_matrix)
from ..config.utils_conf import print_precision, check_array, pool_map, iterable


def cube_inject_companions(array, psf_template, angle_list, flevel, rad_dists,
                           plsc=None, n_branches=1, theta=0, imlib='vip-fft',
                           interpolation='lanczos4', transmission=None,
                           radial_gradient=False, full_output=False,
                           verbose=False, nproc=1):
    """Inject fake companions in branches and given radial distances in an ADI\
    cube.

    Parameters
    ----------
    array : 3d/4d numpy ndarray
        Input cube. This is copied before the injections take place, so
        ``array`` is never modified.
    psf_template : 2d/3d numpy ndarray
        [for a 3D input array] 2d array with the normalized PSF template, with
        an odd or even shape. The PSF image must be centered wrt to the array.
        Therefore, it is recommended to run the function ``normalize_psf`` to
        generate a centered and flux-normalized PSF template.
        It can also be a 3D array, but length should match that of ADI cube.
        [for a 4D input array] In the ADI+mSDI case, it must be a 3d array
        (matching spectral dimensions).
    angle_list : 1d numpy ndarray
        Vector of derotation angles to align North up in your cube images.
    flevel : float or 1d array or 2d array
        Factor for controlling the brightness of the fake companions. If a
        float, the same flux is used for all injections.
        [3D input cube]: if a list/1d array is provided, it should have same
        length as number of frames in the 3D cube (can be used to take into
        account varying observing conditions or airmass).
        [4D (ADI+mSDI) input cube]: if a list/1d array should have the same
        length as the number of spectral channels (i.e. provide a spectrum). If
        a 2d array, it should be n_wavelength x n_frames (can e.g. be used to
        inject a spectrum in varying conditions).
    rad_dists : float, list or array 1d
        Vector of radial distances of fake companions in pixels.
    plsc : float or None
        Value of the plsc in arcsec/px. Only used for printing debug output when
        ``verbose=True``.
    n_branches : int, optional
        Number of azimutal branches.
    theta : float, optional
        Angle in degrees for rotating the position of the first branch that by
        default is located at zero degrees. Theta counts counterclockwise from
        the positive x axis.
    imlib : str, optional
        See the documentation of the ``vip_hci.preproc.frame_shift`` function.
    interpolation : str, optional
        See the documentation of the ``vip_hci.preproc.frame_shift`` function.
    transmission: numpy array, optional
        Radial transmission of the coronagraph, if any. Array with either
        2 x n_rad, 1+n_ch x n_rad columns. The first column should contain the
        radial separation in pixels, while the other column(s) are the
        corresponding off-axis transmission (between 0 and 1), for either all,
        or each spectral channel (only relevant for a 4D input cube).
    radial_gradient: bool, optional
        Whether to apply a radial gradient to the psf image at the moment of
        injection. By default False, i.e. the flux of the psf image is scaled
        only considering the value of transmission at the exact radius the
        companion is injected (e.g. this is the case for the vortex
        coronagraph). Setting it to True may better represent the transmission
        at the very edge of a physical mask though (e.g. ALC).
    full_output : bool, optional
        Returns the ``x`` and ``y`` coordinates of the injections, additionally
        to the new array.
    verbose : bool, optional
        If True prints out additional information.
    nproc: int or None, optional
        Number of CPUs to use for multiprocessing. If None, will be
        automatically set to half the number of available CPUs.

    Returns
    -------
    array_out : numpy ndarray
        Output array with the injected fake companions.
    positions : list of tuple(y, x)
        [full_output] Coordinates of the injections in the first frame (and
        first wavelength for 4D cubes).
    psf_trans: numpy ndarray
        [full_output & transmission != None] Array with injected psf affected
        by transmission (serves to check radial transmission)

    """
    if nproc is None:
        nproc = cpu_count()//2

    def _cube_inject_adi(array, psf_template, angle_list, flevel, plsc,
                         rad_dists, n_branches=1, theta=0, imlib='vip-fft',
                         interpolation='lanczos4', transmission=None,
                         radial_gradient=False, verbose=False):
        if np.isscalar(flevel):
            flevel = np.ones_like(angle_list)*flevel

        if transmission is not None:
            # last radial separation should be beyond the edge of frame
            interp_trans = interp1d(transmission[0], transmission[1])

        ceny, cenx = frame_center(array[0])
        nframes = array.shape[-3]
        size_fc = psf_template.shape[-1]

        positions = []
        # fake companion cube
        fc_fr = np.zeros([nframes, size_fc, size_fc])
        if psf_template.ndim == 2:
            for fr in range(nframes):
                fc_fr[fr] = psf_template
        else:
            for fr in range(nframes):
                fc_fr[fr] = psf_template[fr]

        psf_trans = None
        array_out = array.copy()

        for branch in range(n_branches):
            ang = (branch * 2 * np.pi / n_branches) + np.deg2rad(theta)

            if verbose:
                print('Branch {}:'.format(branch+1))

            for rad in rad_dists:
                fc_fr_rad = fc_fr.copy()
                if transmission is not None:
                    if radial_gradient:
                        y_star = pceny
                        x_star = pcenx - rad
                        d = dist_matrix(size_fc, x_star, y_star)
                        for i in range(d.shape[0]):
                            fc_fr_rad[:, i] = interp_trans(d[i])*fc_fr[:, i]

                        # check the effect of transmission on a single PSF tmp
                        psf_trans = frame_rotate(fc_fr_rad[0],
                                                 -(ang*180/np.pi-angle_list[0]),
                                                 imlib=imlib_rot,
                                                 interpolation=interpolation)
                    else:
                        fc_fr_rad = interp_trans(rad)*fc_fr
                if nproc == 1:
                    for fr in range(nframes):
                        array_out[fr] += _frame_shift_fcp(fc_fr_rad[fr],
                                                          array[fr], rad, ang,
                                                          angle_list[fr],
                                                          flevel[fr], size_fc,
                                                          imlib_sh, imlib_rot,
                                                          interpolation,
                                                          transmission,
                                                          radial_gradient)
                else:
                    res = pool_map(nproc, _frame_shift_fcp, iterable(fc_fr_rad),
                                   iterable(array), rad, ang,
                                   iterable(angle_list), iterable(flevel),
                                   size_fc, imlib_sh, imlib_rot, interpolation,
                                   transmission, radial_gradient)
                    array_out += np.array(res)

                pos_y = rad * np.sin(ang) + ceny
                pos_x = rad * np.cos(ang) + cenx

                positions.append((pos_y, pos_x))

                if verbose:
                    rad_arcs = rad * plsc
                    print('\t(X,Y)=({:.2f}, {:.2f}) at {:.2f} arcsec '
                          '({:.2f} pxs from center)'.format(pos_x, pos_y,
                                                            rad_arcs, rad))

        return array_out, positions, psf_trans

    check_array(array, dim=(3, 4), msg="array")
    check_array(psf_template, dim=(2, 3), msg="psf_template")

    nframes = array.shape[-3]

    pceny, pcenx = frame_center(psf_template)

    if array.ndim == 4 and psf_template.ndim != 3:
        raise ValueError('`psf_template` must be a 3d array')

    if verbose and not np.isscalar(plsc):
        raise TypeError("`plsc` must be a scalar")
    if not np.isscalar(flevel):
        if len(flevel) != array.shape[0]:
            msg = "if not scalar `flevel` must have same length as array"
            raise TypeError(msg)

    # set imlib for rotation & shift (rotation used if transmission!=None)
    if imlib == 'opencv':
        imlib_sh = imlib
        imlib_rot = imlib
    elif imlib == 'skimage' or imlib == 'ndimage-interp':
        imlib_sh = 'ndimage-interp'
        imlib_rot = 'skimage'
    elif imlib == 'vip-fft' or imlib == 'ndimage-fourier':
        imlib_sh = imlib
        imlib_rot = 'vip-fft'
    else:
        raise TypeError("Interpolation not recognized.")

    rad_dists = np.asarray(rad_dists).reshape(-1)  # forces ndim=1

    if not rad_dists[-1] < array.shape[-1] / 2:
        raise ValueError('rad_dists last location is at the border (or '
                         'outside) of the field')

    if transmission is not None:
        t_nz = transmission.shape[0]
        if transmission.ndim != 2:
            raise ValueError("transmission should be a 2D ndarray")
        elif t_nz != 2 and t_nz != 1+array.shape[0]:
            msg = "transmission dimensions should be (2,N) or (n_wave+1, N)"
            raise ValueError(msg)
        # if transmission doesn't have right format for interpolation, adapt it
        diag = np.sqrt(2)*array.shape[-1]
        if transmission[0, 0] != 0 or transmission[0, -1] < diag:
            trans_rad_list = transmission[0].tolist()
            for j in range(t_nz-1):
                trans_list = transmission[j+1].tolist()
                # should have a zero point
                if transmission[0, 0] != 0:
                    if j == 0:
                        trans_rad_list = [0]+trans_rad_list
                    trans_list = [0]+trans_list
                # last point should be max possible distance between fc and star
                if transmission[0, -1] < np.sqrt(2)*array.shape[-1]/2:
                    if j == 0:
                        trans_rad_list = trans_rad_list+[diag]
                    trans_list = trans_list+[1]
                if j == 0:
                    ntransmission = np.zeros([t_nz, len(trans_rad_list)])
                    ntransmission[0] = trans_rad_list
                ntransmission[j+1] = trans_list
            transmission = ntransmission.copy()

    # ADI case
    if array.ndim == 3:
        res = _cube_inject_adi(array, psf_template, angle_list, flevel, plsc,
                               rad_dists, n_branches, theta, imlib,
                               interpolation, transmission, radial_gradient,
                               verbose)
        array_out, positions, psf_trans = res

    # ADI+mSDI (IFS) case
    else:
        nframes_wav = array.shape[0]
        array_out = array.copy()
        if np.isscalar(flevel):
            flevel_all = np.ones([nframes_wav, nframes])*flevel
        elif flevel.ndim == 1:
            flevel_all = np.zeros([nframes_wav, nframes])
            for i in range(nframes_wav):
                flevel_all[i, :] = flevel[i]
        else:
            flevel_all = flevel
        for i in range(nframes_wav):
            if verbose:
                msg = "*** Processing spectral channel {}/{} ***"
                print(msg.format(i+1, nframes_wav))
            if transmission is None:
                trans = None
            elif transmission.shape[0] == 2:
                trans = transmission
            elif transmission.shape[0] == nframes_wav+1:
                trans = np.array([transmission[0], transmission[i+1]])
            else:
                msg = "transmission shape ({}, {}) is not valid"
                raise TypeError(msg.format(transmission.shape[0],
                                           transmission.shape[1]))
            res = _cube_inject_adi(array[i], psf_template[i], angle_list,
                                   flevel_all[i], plsc, rad_dists, n_branches,
                                   theta, imlib, interpolation, trans,
                                   radial_gradient,
                                   verbose=(i == 0 & verbose is True))
            array_out[i], positions, psf_trans = res

    if full_output:
        if transmission is not None:
            return array_out, positions, psf_trans
        else:
            return array_out, positions
    else:
        return array_out


def _frame_shift_fcp(fc_fr_rad, array, rad, ang, derot_ang, flevel, size_fc,
                     imlib_sh, imlib_rot, interpolation, transmission,
                     radial_gradient):
    """Specific cube shift algorithm to inject fake companions."""
    ceny, cenx = frame_center(array)
    sizey = array.shape[-2]
    sizex = array.shape[-1]

    array_sh = np.zeros_like(array)

    w = int(np.ceil(size_fc/2))
    if size_fc % 2:  # new convention
        w -= 1
    sty = int(ceny) - w
    stx = int(cenx) - w

    shift_y = rad * np.sin(ang - np.deg2rad(derot_ang))
    shift_x = rad * np.cos(ang - np.deg2rad(derot_ang))
    if transmission is not None and radial_gradient:
        fc_fr_ang = frame_rotate(fc_fr_rad, -(ang*180/np.pi - derot_ang),
                                 imlib=imlib_rot, interpolation=interpolation)
    else:
        fc_fr_ang = fc_fr_rad.copy()

    # sub-px shift (within PSF template frame)
    dsy = shift_y-int(shift_y)
    dsx = shift_x-int(shift_x)
    fc_fr_ang = frame_shift(fc_fr_ang, dsy, dsx, imlib_sh, interpolation,
                            border_mode='constant')
    # integer shift (in final cube)
    y0 = sty+int(shift_y)
    x0 = stx+int(shift_x)
    yN = y0+size_fc
    xN = x0+size_fc
    p_y0 = 0
    p_x0 = 0
    p_yN = size_fc
    p_xN = size_fc
    if y0 < 0:
        p_y0 = -y0
        y0 = 0
    if x0 < 0:
        p_x0 = -x0
        x0 = 0
    if yN > sizey:
        p_yN -= yN-sizey
        yN = sizey
    if xN > sizex:
        p_xN -= xN-sizex
        xN = sizex

    array_sh[y0:yN, x0:xN] = flevel*fc_fr_ang[p_y0:p_yN, p_x0:p_xN]

    return array_sh


def generate_cube_copies_with_injections(array, psf_template, angle_list, plsc,
                                         n_copies=100, inrad=8, outrad=12,
                                         dist_flux=("uniform", 2, 500)):
    """
    Create multiple copies of ``array`` with different random injections.

    This is a wrapper around ``metrics.cube_inject_companions``, which deals
    with multiple copies of the original data cube and generates random
    parameters.

    Parameters
    ----------
    array : 3d/4d numpy ndarray
        Original input cube.
    psf_template : 2d/3d numpy ndarray
        Array with the normalized psf template. It should have an odd shape.
        It's recommended to run the function ``normalize_psf`` to get a proper
        PSF template. In the ADI+mSDI case it must be a 3d array.
    angle_list : 1d numpy ndarray
        Vector of derotation angles to align North up in your cube images.
    plsc : float
        Value of the plsc in arcsec/px. Only used for printing debug output when
        ``verbose=True``.
    n_copies : int
        This is the number of 'cube copies' returned.
    inrad,outrad : float
        Inner and outer radius of the injections. The actual injection position
        is chosen randomly.
    dist_flux : tuple('method', params)
        Tuple describing the flux selection. Method can be a function, the
        ``*params`` are passed to it. Method can also be a string, for a
        pre-defined random function:

            ``('skewnormal', skew, mean, var)``
                uses scipy.stats.skewnorm.rvs
            ``('uniform', low, high)``
                uses np.random.uniform
            ``('normal', loc, scale)``
                uses np.random.normal

    Returns
    -------
    fake_data : dict
        Represents a copy of the original ``array``, with fake injections. The
        dictionary keys are:

            ``cube``
                Array shaped like the input ``array``, with the fake injections.
            ``position`` : list of tuples(y,x)
                List containing the positions of the injected companions, as
                (y,x) tuples.
            ``dist`` : float
                The distance of the injected companions, which was passed to
                ``cube_inject_companions``.
            ``theta`` : float, degrees
                The initial angle, as passed to ``cube_inject_companions``.
            ``flux`` : float
                The flux passed to ``cube_inject_companions``.

    """
    # TODO: 'mask' parameter for known companions?

    width = outrad - inrad
    yy, xx = get_annulus_segments(array[0], inrad, width)[0]
    num_patches = yy.shape[0]

    # Defining Fluxes according to chosen distribution
    dist_fkt = dict(skewnormal=stats.skewnorm.rvs,
                    normal=np.random.normal,
                    uniform=np.random.uniform).get(dist_flux[0],
                                                   dist_flux[0])
    fluxes = sorted(dist_fkt(*dist_flux[1:], size=n_copies))

    inds_inj = np.random.randint(0, num_patches, size=n_copies)

    # Injections
    for n in range(n_copies):

        injx = xx[inds_inj[n]] - frame_center(array[0])[1]
        injy = yy[inds_inj[n]] - frame_center(array[0])[0]
        dist = np.sqrt(injx**2 + injy**2)
        theta = np.mod(np.arctan2(injy, injx) / np.pi * 180, 360)

        fake_cube, positions = cube_inject_companions(
            array, psf_template, angle_list, plsc=plsc,
            flevel=fluxes[n], theta=theta,
            rad_dists=dist, n_branches=1,  # TODO: multiple injections?
            full_output=True, verbose=False
        )

        yield dict(
            positions=positions,
            dist=dist, theta=theta, flux=fluxes[n],
            cube=fake_cube
        )


def frame_inject_companion(array, array_fc, pos_y, pos_x, flux,
                           imlib='vip-fft', interpolation='lanczos4'):
    """
    Inject a fake companion in a single frame (can be a single multi-wavelength\
    frame) at given coordinates, or in a cube (at the same coordinates, flux\
    and with same fake companion image throughout the cube).

    Parameters
    ----------
    array : numpy ndarray, 2d or 3d
        Input frame or cube.
    array_fc : numpy ndarray, 2d
        Fake companion image to be injected. If even-dimensions, the center
        should be placed at coordinates [dim//2, dim//2] (0-based indexing),
        as per VIP's convention.
    pos_y, pos_x: float
         Y and X coordinates where the companion should be injected
    flux : int
        Flux at which the fake companion should be injected (i.e. scaling
        factor for the injected image)
    imlib : str, optional
        See documentation of the ``vip_hci.preproc.frame_shift`` function.
    interpolation : str, optional
        See documentation of the ``vip_hci.preproc.frame_shift`` function.

    Returns
    -------
    array_out : numpy ndarray
        Frame or cube with the companion injected
    """
    if not (array.ndim == 2 or array.ndim == 3):
        raise TypeError('Array is not a 2d or 3d array.')
    if array.ndim == 2:
        size_fc = array_fc.shape[0]
        ceny, cenx = frame_center(array)
        ceny = int(ceny)
        cenx = int(cenx)
        fc_fr = np.zeros_like(array)
        w = int(np.floor(size_fc/2.))
        odd = size_fc % 2
        # fake companion in the center of a zeros frame
        fc_fr[ceny-w:ceny+w+odd, cenx-w:cenx+w+odd] = array_fc
        array_out = array + frame_shift(fc_fr, pos_y-ceny, pos_x-cenx, imlib,
                                        interpolation) * flux

    if array.ndim == 3:
        size_fc = array_fc.shape[1]
        ceny, cenx = frame_center(array[0])
        ceny = int(ceny)
        cenx = int(cenx)
        fc_fr = np.zeros_like(array)
        w = int(np.floor(size_fc/2.))
        odd = size_fc % 2
        # fake companion in the center of a zeros frame
        fc_fr[:, ceny-w:ceny+w+odd, cenx-w:cenx+w+odd] = array_fc
        array_out = array + cube_shift(fc_fr, pos_y - ceny, pos_x - cenx,
                                       imlib, interpolation) * flux

    return array_out


def collapse_psf_cube(array, size, fwhm=4, verbose=True, collapse='mean'):
    """Create a 2d PSF template from a cube of non-saturated off-axis frames\
    of the star by taking the mean and normalizing the PSF flux.

    Parameters
    ----------
    array : numpy ndarray, 3d
        Input cube.
    size : int
        Size of the squared subimage.
    fwhm: float, optional
        The size of the Full Width Half Maximum in pixel.
    verbose : {True,False}, bool optional
        Whether to print to stdout information about file opening, cropping and
        completion of the psf template.
    collapse : {'mean','median'}, string optional
        Defines the way the frames are collapsed.

    Returns
    -------
    psf_normd : numpy ndarray
        Normalized PSF.

    """
    if array.ndim != 3 and array.ndim != 4:
        raise TypeError('Array is not a cube, 3d or 4d array.')

    n = array.shape[0]
    psf = cube_crop_frames(array, size=size, verbose=verbose)
    if collapse == 'mean':
        psf = np.mean(psf, axis=0)
    elif collapse == 'median':
        psf = np.median(psf, axis=0)
    else:
        raise TypeError('Collapse mode not recognized.')

    psf_normd = normalize_psf(psf, size=size, fwhm=fwhm)

    if verbose:
        print("Done scaled PSF template from the average of", n, "frames.")
    return psf_normd


def normalize_psf(array, fwhm='fit', size=None, threshold=None, mask_core=None,
                  model='gauss', imlib='vip-fft', interpolation='lanczos4',
                  force_odd=True, correct_outliers=True, full_output=False,
                  verbose=True, debug=False):
    """Normalize a PSF (2d or 3d array), to have the flux in a 1xFWHM aperture\
    equal to one.

    It also allows cropping of the array. Automatic recentering of the PSF is
    done internally - as long as it is already roughly centered within ~2px.

    Parameters
    ----------
    array: numpy ndarray
        The PSF, 2d (ADI data) or 3d array (IFS data).
    fwhm: int, float, 1d array or str, optional
        The Full Width Half Maximum in pixels. It can handle a different
        FWHM value for different wavelengths (IFS data). If set to 'fit' then
        a ``model`` (assuming the PSF is centered in the array) is fitted to
        estimate the FWHM in 2D or 3D PSF arrays.
    size : int or None, optional
        If int it will correspond to the size of the centered sub-image to be
        cropped form the PSF array. The PSF is assumed to be roughly centered
        with respect to the array.
    threshold : None or float, optional
        Sets to zero values smaller than threshold (in the normalized image).
        This can be used to only leave the core of the PSF.
    mask_core : None or float, optional
        Sets the radius of a circular aperture for the core of the PSF,
        everything else will be set to zero.
    model : {'gauss', 'moff', 'airy'}, str optional
        The assumed model used to fit the PSF: either a Gaussian, a Moffat
        or an Airy 2d distribution.
    imlib : str, optional
        See the documentation of the ``vip_hci.preproc.frame_shift`` function.
    interpolation : str, optional
        See the documentation of the ``vip_hci.preproc.frame_shift`` function.
    force_odd : bool, optional
        If True the resulting array will have odd size (and the PSF will be
        placed at its center). If False, and the frame size is even, then the
        PSF will be put at the center of an even-sized frame.
    correct_outliers: bool, optional
        For an input 3D cube (IFS) of PSFs, if the 2D fit fails for one of the
        channels, whether to interpolate FWHM value from surrounding channels,
        and recalculate flux and normalization.
    full_output : bool, optional
        If True the flux in a FWHM aperture is returned along with the
        normalized PSF.
    verbose : bool, optional
        If True intermediate results are printed out.
    debug : bool, optional
        If True the fitting will output additional information and a diagnostic
        plot will be shown (this might cause a long output if ``array`` is 3d
        and has many slices).

    Returns
    -------
    psf_norm : numpy ndarray
        The normalized PSF (2d or 3d array).
    fwhm_flux : numpy ndarray
        [full_output=True] The flux in a FWHM aperture (it can be a single
        value or a vector).
    fwhm : numpy ndarray
        [full_output=True] The FWHM size. If ``fwhm`` is set to 'fit' then it
        is the fitted FWHM value according to the assumed ``model`` (the mean in
        X and Y is returned when ``model`` is set to 'gauss').

    """
    def psf_norm_2d(psf, fwhm, threshold, mask_core, full_output, verbose):
        """Normalize PSF in the 2d case."""
        # we check if the psf is centered and fix it if needed
        cy, cx = frame_center(psf, verbose=False)
        xcom, ycom = centroid_com(psf)
        if not (np.allclose(cy, ycom, atol=1e-2) or
                np.allclose(cx, xcom, atol=1e-2)):
            # first we find the centroid and put it in the center of the array
            centry, centrx = fit_2d(psf, full_output=False, debug=False)
            if not np.isnan(centry) and not np.isnan(centrx):
                shiftx, shifty = centrx - cx, centry - cy
                psf = frame_shift(psf, -shifty, -shiftx, imlib=imlib,
                                  interpolation=interpolation)

                for _ in range(2):
                    centry, centrx = fit_2d(psf, full_output=False, debug=False)
                    if np.isnan(centry) or np.isnan(centrx):
                        break
                    cy, cx = frame_center(psf, verbose=False)
                    shiftx, shifty = centrx - cx, centry - cy
                    psf = frame_shift(psf, -shifty, -shiftx, imlib=imlib,
                                      interpolation=interpolation)

        # we check whether the flux is normalized and fix it if needed
        fwhm_aper = CircularAperture((cx, cy), fwhm/2)
        fwhm_aper_phot = aperture_photometry(psf, fwhm_aper,
                                             method='exact')
        fwhm_flux = np.array(fwhm_aper_phot['aperture_sum'])

        if fwhm_flux > 1.1 or fwhm_flux < 0.9:
            psf_norm_array = psf / np.array(fwhm_aper_phot['aperture_sum'])
        else:
            psf_norm_array = psf

        if threshold is not None:
            psf_norm_array[np.where(psf_norm_array < threshold)] = 0

        if mask_core is not None:
            psf_norm_array = get_circle(psf_norm_array, radius=mask_core)

        if verbose:
            print("Flux in 1xFWHM aperture: {:.3f}".format(fwhm_flux[0]))

        if full_output:
            return psf_norm_array, fwhm_flux, fwhm
        else:
            return psf_norm_array
    ###########################################################################
    if model == 'gauss':
        fit_2d = fit_2dgaussian
    elif model == 'moff':
        fit_2d = fit_2dmoffat
    elif model == 'airy':
        fit_2d = fit_2dairydisk
    else:
        raise ValueError('`Model` not recognized')

    if array.ndim == 2:
        y, x = array.shape
        if size is not None:
            if force_odd and size % 2 == 0:
                size += 1
                msg = "`Force_odd` is True therefore `size` was set to {}"
                print(msg.format(size))
        else:
            if force_odd and y % 2 == 0:
                size = y - 1
                msg = "`Force_odd` is True and frame size is even, therefore "
                msg += "new frame size was set to {}"
                print(msg.format(size))

        if size is not None:
            if size < array.shape[0]:
                array = frame_crop(array, size, force=True, verbose=False)
            else:
                array = array.copy()
        else:
            array = array.copy()

        if not np.isscalar(fwhm):
            msg = "For a 2d input array, fwhm should be a scalar or string."
            raise ValueError(msg)
        elif fwhm == 'fit':
            fit = fit_2d(array, full_output=True, debug=debug)
            if model == 'gauss':
                fwhm = np.mean((fit['fwhm_x'], fit['fwhm_y']))
                if verbose:
                    print("\nMean FWHM: {:.3f}".format(fwhm))
            elif model == 'moff' or model == 'airy':
                fwhm = fit.fwhm.at[0]
                if verbose:
                    print("FWHM: {:.3f}".format(fwhm))

        res = psf_norm_2d(array, fwhm, threshold, mask_core, full_output,
                          verbose)
        return res

    elif array.ndim == 3:
        n, y, x = array.shape
        if size is not None:
            if force_odd and size % 2 == 0:
                size += 1
                msg = "`Force_odd` is True therefore `size` was set to {}"
                print(msg.format(size))
        else:
            if force_odd and y % 2 == 0:
                size = y - 1
                msg = "`Force_odd` is True and frame size is even, therefore "
                msg += "new frame size was set to {}"
                print(msg.format(size))

        if size is not None:
            if size < array.shape[1]:
                array = cube_crop_frames(array, size, force=True, verbose=False)
            else:
                array = array.copy()

        if np.isscalar(fwhm):
            if fwhm != 'fit':
                fwhm = [fwhm] * array.shape[0]
            else:
                fits_vect = [fit_2d(array[i],
                                    full_output=True,
                                    debug=debug) for i in range(n)]
                if model == 'gauss':
                    fwhmx = [fits_vect[i]['fwhm_x'] for i in range(n)]
                    fwhmy = [fits_vect[i]['fwhm_y'] for i in range(n)]
                    fwhm_vect = [np.mean((fwhmx[i], fwhmy[i]))
                                 for i in range(n)]
                    fwhm = np.array(fwhm_vect)
                    if verbose:
                        print("Mean FWHM per channel: ")
                        print_precision(fwhm)
                elif model == 'moff' or model == 'airy':
                    fwhm_vect = [fits_vect[i]['fwhm'] for i in range(n)]
                    fwhm = np.array(fwhm_vect)
                    fwhm = fwhm.flatten()
                    if verbose:
                        print("FWHM per channel:")
                        print_precision(fwhm)
                # Replace outliers if needed
                if correct_outliers:
                    if np.sum(np.isnan(fwhm)) > 0:
                        for f in range(n):
                            if np.isnan(fwhm[f]) and f != 0 and f != n-1:
                                fwhm[f] = np.nanmean(np.array([fwhm[f-1],
                                                               fwhm[f+1]]))
                            elif np.isnan(fwhm[f]):
                                msg = "2D fit failed for first or last channel."
                                msg += " Try other parameters?"
                                raise ValueError(msg)
        elif len(fwhm) != array.shape[0]:
            msg = "If fwhm is a list/1darray it should have a length of {}"
            raise ValueError(msg.format(array.shape[0]))

        array_out = []
        fwhm_flux = np.zeros(n)

        for fr in range(array.shape[0]):
            restemp = psf_norm_2d(array[fr], fwhm[fr], threshold, mask_core,
                                  True, False)
            array_out.append(restemp[0])
            fwhm_flux[fr] = restemp[1][0]

        array_out = np.array(array_out)
        if verbose:
            print("Flux in 1xFWHM aperture: ")
            print_precision(fwhm_flux)

        if full_output:
            return array_out, fwhm_flux, fwhm
        else:
            return array_out

    else:
        msg = "Input psf should be 2D or 3D. If of higher dimension, either use"
        msg += " ``vip_hci.preproc.cube_collapse`` first, or loop on the "
        msg += "temporal axis."
        raise ValueError(msg.format(array.shape[0]))


def cube_planet_free(planet_parameter, cube, angs, psfn, imlib='vip-fft',
                     interpolation='lanczos4', transmission=None,
                     radial_gradient=False):
    """Return a cube in which we have injected negative fake companion at the\
    position/flux given by planet_parameter.

    Parameters
    ----------
    planet_parameter: numpy.array or list or tuple
        The (r, theta, flux) for all known companions. For a 3D cube, this
        parameter must have a shape (n_pl,3) or (3,) -- the latter case assumes
        a single planet in the data. For a 4d cube r, theta and flux
        must all be 1d arrays with length equal to cube.shape[0]; i.e.
        planet_parameter should have shape: (n_pl,3,n_ch) or (3,n_ch) -- the
        latter case assumes a single planet in the data.
    cube: numpy ndarray
        The cube of fits images expressed as a numpy.array.
    angs: numpy ndarray
        The parallactic angle fits image expressed as a numpy.array.
    psfn: 2d or 3d numpy ndarray
        The normalized psf expressed as a numpy ndarray. Can be 3d for a 4d
        (spectral+ADI) input cube.
    imlib : str, optional
        See the documentation of the ``vip_hci.preproc.frame_rotate`` function.
    interpolation : str, optional
        See the documentation of the ``vip_hci.preproc.frame_rotate`` function.
    transmission: numpy array, optional
        Radial transmission of the coronagraph, if any. Array with either
        2 x n_rad, 1+n_ch x n_rad columns. The first column should contain the
        radial separation in pixels, while the other column(s) are the
        corresponding off-axis transmission (between 0 and 1), for either all,
        or each spectral channel (only relevant for a 4D input cube).
    radial_gradient: bool, optional
        Whether to apply a radial gradient to the psf image at the moment of
        injection. By default False, i.e. the flux of the psf image is scaled
        only considering the value of transmission at the exact radius the
        companion is injected (e.g. this is the case for the vortex
        coronagraph). Setting it to True may better represent the transmission
        at the very edge of a physical mask though (e.g. ALC).

    Returns
    -------
    cpf : numpy.array
        The cube with negative companions injected at the position given in
        planet_parameter.

    """
    cpf = np.zeros_like(cube)

    # unify planet_parameter format
    planet_parameter = np.array(planet_parameter)
    cond1 = cube.ndim == 3 and planet_parameter.ndim < 2
    cond2 = cube.ndim == 4 and planet_parameter.ndim < 3
    if cond1 or cond2:
        planet_parameter = planet_parameter[np.newaxis, :]

    if cube.ndim == 4:
        if planet_parameter.shape[2] != cube.shape[0]:
            raise TypeError("Input planet parameter with wrong dimensions.")

    for i in range(planet_parameter.shape[0]):
        if i == 0:
            cube_temp = cube
        else:
            cube_temp = cpf

        if cube.ndim == 4:
            for j in range(cube.shape[0]):
                flevel = -planet_parameter[i, 2, j]
                r = planet_parameter[i, 0, j]
                theta = planet_parameter[i, 1, j]
                cpf[j] = cube_inject_companions(cube_temp[j], psfn[j], angs,
                                                flevel=flevel,
                                                rad_dists=[r],
                                                n_branches=1,
                                                theta=theta,
                                                imlib=imlib,
                                                interpolation=interpolation,
                                                verbose=False,
                                                transmission=transmission,
                                                radial_gradient=radial_gradient)
        else:
            cpf = cube_inject_companions(cube_temp, psfn, angs, n_branches=1,
                                         flevel=-planet_parameter[i, 2],
                                         rad_dists=[planet_parameter[i, 0]],
                                         theta=planet_parameter[i, 1],
                                         imlib=imlib, verbose=False,
                                         interpolation=interpolation,
                                         transmission=transmission,
                                         radial_gradient=radial_gradient)
    return cpf
