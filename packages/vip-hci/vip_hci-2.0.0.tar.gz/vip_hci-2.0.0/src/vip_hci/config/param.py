#! /usr/bin/env python
"""
Dictionaries with telescope/instrument parameters.

Usage
-----

.. code:: python

    from vip_hci.config import VLT_NACO
    lbda = VLT_NACO['lambdal']
    diameter = VLT_NACO['diam']
    pxscale = VLT_NACO['plsc']

    resel = lambda/diameter*206265/pxscale

"""

VLT_SPHERE_IFS = {
    "latitude": -24.627,
    "longitude": -70.404,
    "plsc": 0.00746,  # plate scale [arcsec]/px for IFS
    "diam": 8.2,  # telescope diameter [m]
}

VLT_SPHERE_IRDIS = {
    "latitude": -24.627,
    "longitude": -70.404,
    "plsc": 0.01225,  # plate scale [arcsec]/px for IRDIS
    "diam": 8.2,  # telescope diameter [m]
}

VLT_NACO = {
    "latitude": -24.627,
    "longitude": -70.404,
    "plsc": 0.027190,  # plate scale [arcsec]/px
    "diam": 8.2,  # telescope diameter [m]
    # filter central wavelength [m] L band
    "lambdal": 3.8e-6,
    # header keywords
    # header keyword for calibration frames: 'CALIB' / 'SCIENCE'
    "kw_categ": "HIERARCH ESO DPR CATG",
    # header keyword for frame type: 'FLAT,SKY' / 'DARK' / 'OBJECT' / 'SKY'
    "kw_type": "HIERARCH ESO DPR TYPE",
}

VLT_SINFONI = {
    "latitude": -24.627,
    "longitude": -70.404,
    # plsc: depending on the chosen mode, can also be: 0.125'' or 0.05''
    "plsc": 0.0125,  # plate scale [arcsec]/px
    "diam": 8.2,  # telescope diameter [m]
    "lambdahk": 1.95e-6,  # wavelength of the middle of H+K
    "lambdah": 1.65e-6,  # wavelength of the middle of H band
    # wavelength of the Brackett gamma line (~middle of the K band)
    "lambdak": 2.166e-6,
    # header keywords
    # header keyword for calibration frames: 'CALIB' / 'SCIENCE'
    "kw_categ": "HIERARCH ESO DPR CATG",
    # header keyword for frame type: 'FLAT,SKY' / 'DARK' / 'OBJECT' / 'SKY'
    "kw_type": "HIERARCH ESO DPR TYPE",
}

GPI_IFS = {
    "latitude": -30.2417,
    "longitude": -70.747,
    "plsc": 0.014166,  # plate scale [arcsec]/px for IFS
    "diam": 8.1,  # telescope diameter [m]
}

LBT = {
    "latitude": 32.70131,  # LBT's latitude in degrees
    "longitude": -109.889064,  # LBT's longitude in degrees
    # central wavelength L cont2' band [m]
    "lambdal": 3.47e-6,
    "plsc": 0.0106,  # plate scale [arcsec]/px
    "diam": 8.4,  # telescope diameter [m]
    # header keywords
    "lst": "LBT_LST",  # Local sidereal Time header keyword
    "ra": "LBT_RA",  # right ascension header keyword
    "dec": "LBT_DEC",  # declination header keyword
    "altitude": "LBT_ALT",  # altitude header keyword
    "azimuth": "LBT_AZ",  # azimuth header keyword
    # nominal total integration time per pixel header keyword
    "exptime": "EXPTIME",
    # total controller acquisition time header keyword
    "acqtime": "ACQTIME",
    "filter": "LMIR_FW2",  # filter
}

KECK_NIRC2 = {
    "latitude": 19.82636,  # Keck's latitude in degrees
    # plate scale [arcsec]/px, narrow camera
    "plsc_narrow": 0.009942,
    # plate scale [arcsec]/px, medium camera
    "plsc_medium": 0.019829,
    # plate scale [arcsec]/px, wide camera
    "plsc_wide": 0.039686,
    "diam": 10.0,  # telescope diameter [m]
    # header keywords
    "camera_name": "CAMNAME",  # camera name bwt narrow, medium and wide
}
