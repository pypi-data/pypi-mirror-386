__all__ = ['read_cube']

import os
import sys
import pathlib
from datetime import datetime, timedelta
import numpy as np
import h5py
import astropy.wcs
import astropy.units as u
from astropy.nddata import StdDevUncertainty
import sunpy.coordinates as coords
from eispac.core.eiscube import EISCube, _make_wcs_from_cube_index
from eispac.core.read_wininfo import read_wininfo
from eispac.instr.calc_read_noise import calc_read_noise

def read_cube(filename=None, window=0, exp_set='sum', apply_radcal=True, radcal=None,
              abs_errs=True, count_offset=None, debug=False):
    """Load a single window of EIS data from an HDF5 file into an EISCube object

    Parameters
    ----------
    filename : str or `pathlib.Path` object
        Name of either the data or head HDF5 file for a single EIS observation
    window : int, float, or str, optional
        Requested spectral window number or the value of any wavelength within
        the requested window. Default is '0'
    exp_set : int or str, optional
        Index number of the exposure set to load from the file. Only used in the 
        rare case of scanning observations with multiple exposures per raster 
        position. Can also set to a value of "sum" to add together all exposures 
        and simulate a longer exposure image. Default is "sum".
    apply_radcal : bool, optional
        If set to True, will apply the pre-flight radiometric calibration curve
        found in the HDF5 header file and set units to erg/(cm^2 s sr). If set
        to False, will simply return the data in units of photon counts. Default
        is True.
    radcal : array_like, optional
        User-inputted radiometric calibration curve to be applied to the data.
    abs_errs : bool, optional
        If set to True, will calulate errors based on the absolute value of the
        counts. This allows for reasonable errors to be estimated for valid
        negative count values that are the result of the dark count subtraction
        method (not bad or filled data). Default it True.
    count_offset : int or float, optional
        Constant value to add to the count array before error estimate or
        calibration. Could be useful for testing data processing methods.
        Default is None (no count offset).
    debug : bool, optional
        If set to True, will return a dictionary with the raw counts and metadata
        instead of an EISCube class instance. Useful for examining data files that
        fail to load properly.

    Returns
    -------
    output_cube : `~eispac.core.EISCube` class instance
        An EISCube class instance containing the requested spectral data window
    """
    ############################################################################
    ### Read data and header information from hdf5 files
    ############################################################################
    # Input type validation (value checks are implemented later)
    if not isinstance(filename, (str, pathlib.Path)):
        print('Error: Please input a valid filepath as '
             +'either a string or pathlib.Path object', file=sys.stderr)
        return None
    if not isinstance(window, (int, float, str)):
        print('Error: Please input a valid window or wavelength number '
             +'as either an integer, float, or string', file=sys.stderr)
        return None

    # Initialize "meta" dictionary to contain ALL of the extra EIS information.
    # We may want to add some of the values as attributes of the EISCube instead.
    meta = dict()

    # Parse filename and determine the directory and filename
    abs_filepath = pathlib.Path(filename).resolve()
    input_name = str(abs_filepath.name)
    input_dir = abs_filepath.parent
    if str(input_dir) == '.':
        input_dir = pathlib.Path().cwd()

    # Determine data and header filenames, regardless of which one was inputted
    data_filepath = input_dir.joinpath(input_name.replace('.head.h5', '.data.h5'))
    head_filepath = input_dir.joinpath(input_name.replace('.data.h5', '.head.h5'))

    # Check for data and head files. Exit if either file does not exist.
    if not data_filepath.is_file():
        print('Error: Data file does not exist, ' + str(data_filepath),
              file=sys.stderr)
        return None
    else:
        meta['filename_data'] = str(data_filepath)
        print('Data file,\n   ' + str(data_filepath))
    if not head_filepath.is_file():
        print('Error: Header file does not exist, ' + str(head_filepath),
              file=sys.stderr)
        return None
    else:
        meta['filename_head'] = str(head_filepath)
        print('Header file,\n   ' + str(head_filepath))

    # Read in min and max wavelength for each window in the file so we can
    # search for the requested window. Note: wininfo is a recarray with the
    # following fields: 'iwin', 'line_id', 'wvl_min', 'wvl_max', 'nl', & 'xs'
    wininfo = read_wininfo(head_filepath)
    num_win = wininfo.size
    meta['wininfo'] = wininfo

    # Locate the requested data window. Exit if it does not exist.
    if int(window) < 25:
        # Interpret values < 25 as window number
        if window >=0 and window < num_win:
            meta['iwin'] = int(window)
            meta['iwin_str'] = f'win{window:02d}'
            print(f'Found window {window}')
        else:
            print(f'Error: Window {window} does not exist! The input data'
                 +f' file contains window numbers between 0 and {num_win}',
                  file=sys.stderr)
            return None
    else:
        # Interpret values > 25 as wavelength
        wvl = float(window)
        p = (wininfo['wvl_max'] - wvl)*(wvl - wininfo['wvl_min'])
        iwin = np.where(p >= 0)[0]
        if len(iwin) == 1:
            meta['iwin'] = int(iwin[0])
            meta['iwin_str'] = f'win{iwin[0]:02d}'
            print(f'Found a wavelength {wvl:.2f} [Angstroms] in window {iwin[0]}')
        else:
            print(f'Error: Wavelength not found! The input data file does'
                 +f' not contain a window that observes {window} Angstroms',
                  file=sys.stderr)
            return None

    # Read in the photon counts from data file
    with h5py.File(data_filepath, 'r') as f_data:
        lv_1_counts = np.array(f_data['level1/'+meta['iwin_str']])
        lv_1_count_units = f_data['level1/intensity_units'][0]
        lv_1_count_units = lv_1_count_units.decode('utf-8')

    # Read in metadata and instrumental correction factors from head file
    with h5py.File(head_filepath, 'r') as f_head:
        # Read index information (example data says it is from the level0 FITS file)
        index = {}
        for key in f_head['index']:
            val = np.array(f_head['index/'+key])
            if type(val[0]) == np.bytes_:
                val = val.astype(np.str_) # convert bytes to unicode
            if val.size == 1:
                # val = val[0]
                val = val.item() # Extract single-value to a Python scaler
            index[key] = val

        meta['index'] = index

        # Read general EIS pointing information (includes average corrections)
        pointing = {}
        for key in f_head['pointing']:
            val = np.array(f_head['pointing/'+key])
            if type(val[0]) == np.bytes_:
                val = val.astype(np.str_) # convert bytes to unicode
            if val.size == 1:
                # val = val[0]
                val = val.item() # Extract single-value to a Python scaler
            pointing[key] = val

        meta['pointing'] = pointing

        # Read calibration data
        meta['wave'] = np.array(f_head['wavelength/'+meta['iwin_str']])
        meta['radcal'] = np.array(f_head['radcal/'+meta['iwin_str']+'_pre'])
        meta['slit_width'] = np.array(f_head['instrumental_broadening/slit_width'])
        slit_width_units = f_head['instrumental_broadening/slit_width_units'][0]
        meta['slit_width_units'] = slit_width_units.decode('utf-8')
        meta['ccd_offset'] = np.array(f_head['ccd_offsets/'+meta['iwin_str']])

        # Read wavelength-dependent correction factor
        meta['wave_corr'] = np.array(f_head['wavelength/wave_corr'])
        meta['wave_corr_t'] = np.array(f_head['wavelength/wave_corr_t'])
        meta['wave_corr_tilt'] = np.array(f_head['wavelength/wave_corr_tilt'])

        # Read time and duration information
        try:
            meta['date_obs'] = np.array(f_head['times/date_obs']).astype(np.str_)
            meta['date_obs_format'] = str(np.array(f_head['times/time_format']).astype(np.str_)[0])
        except KeyError:
            # Estimate missing or broken timestamps (ideally, never used)
            print('WARNING: the header file has missing or incomplete date_obs' 
                 +' for each raster step! Filling with estimated timestamps.')
            total_time = np.datetime64(index['date_end']) - np.datetime64(index['date_obs'])
            total_time = total_time / np.timedelta64(1, 's') # ensure [s] units
            n_xsteps = index['nexp'] / index['nexp_prp']
            est_cad = total_time / n_xsteps
            est_date_obs = np.datetime64(index['date_obs']) \
                         + np.arange(n_xsteps) \
                         * np.timedelta64(int(est_cad*1000), 'ms')
            if index['nraster'] == 1:
                # Sit-and-stare timestamps inc left to right
                meta['date_obs'] = est_date_obs.astype('str').astype('<U24')
            else:
                # raster timestamps inc from right to left (scan dir)
                meta['date_obs'] = np.flip(est_date_obs.astype('str').astype('<U24'))
            meta['date_obs_format'] = 'iso_8601'
        meta['duration'] = np.array(f_head['exposure_times/duration'])
        step_duration_units = f_head['exposure_times/duration_units'][0]
        meta['duration_units'] = step_duration_units.decode('utf-8')

    if debug == True:
        print('DEBUG MODE ON: returning dictionary with raw counts and metadata')
        return {'data':lv_1_counts, 'data_units':lv_1_count_units, 'meta':meta}

    # Check for user-inputted radcal curve
    if apply_radcal or radcal is not None:
        apply_radcal = True
        if radcal is not None:
            # Confirm dimensions are compatiable
            radcal_array = np.array(radcal)
            num_wave = len(meta['wave'])
            if len(radcal_array) != num_wave:
                print(f'Error: Input radcal array has the incorrect number of'
                     +f' elements. For the selected window, please input an'
                     +f' array with {num_wave} elements.',
                     file=sys.stderr)
                return None
        else:
            # Just use the pre-flight radcal curve
            radcal_array = meta['radcal']
    else:
        radcal_array = None

    ############################################################################
    ### Check for multiple exposure sets and select one (very rarely used)
    ############################################################################
    if len(lv_1_counts.shape) == 4:
        nexp_per_pos = lv_1_counts.shape[0] # Num exposures per slit position

        if not isinstance(exp_set, (str, int)):
            print(f"ERROR: invalid 'raster' keyword data type. Please input a"
                 +f" string of 'sum' or an integer.", file=sys.stderr)
            return None
        elif isinstance(exp_set, str):
            if exp_set.isdigit():
                # convert string containing an integer
                exp_set = int(exp_set)
            elif exp_set.lower() != 'sum':
                print(f"ERROR: invalid raster string of '{exp_set}'. Please"
                     +f" input either 'sum' or an integer between 0 and"
                     +f" {nexp_per_pos-1}.", file=sys.stderr)
                return None

        if isinstance(exp_set, int):
            if (exp_set >= nexp_per_pos) or (exp_set < -1*nexp_per_pos):
                # Check for out-of-bound indices
                oob_exp_set = exp_set
                if exp_set < 0:
                    exp_set = 0
                else:
                    exp_set = nexp_per_pos-1
                print(f"WARNING: exp_set {oob_exp_set} is out of bounds."
                     +f" Loading the nearest valid exp_set ({exp_set}) instead.", 
                     file=sys.stderr)
            elif exp_set < 0:
                # convert negative indices to positive
                exp_set = nexp_per_pos - exp_set
    
        # Extract the correct subarrays
        if str(exp_set).lower() == 'sum':
            print(f'Summing all {nexp_per_pos} sets exposures per slit position')
            lv_1_counts = np.nansum(lv_1_counts, axis=0)
            meta['date_obs'] = meta['date_obs'][0, :]
            meta['duration'] = np.nansum(meta['duration'], axis=0)
            meta['wave_corr'] = np.nanmean(meta['wave_corr'], axis=0)
            meta['wave_corr_t'] = np.nanmean(meta['wave_corr_t'], axis=0)
            meta['pointing']['solar_x'] = meta['pointing']['solar_x'][0, :]
        else:
            print(f'Loading exposure set {exp_set} ({exp_set+1} of {nexp_per_pos})')
            lv_1_counts = lv_1_counts[exp_set,:,:,:]
            meta['date_obs'] = meta['date_obs'][exp_set, :]
            meta['duration'] = meta['duration'][exp_set, :]
            meta['wave_corr'] = meta['wave_corr'][exp_set, :, :]
            meta['wave_corr_t'] = meta['wave_corr_t'][exp_set, :]
            meta['pointing']['solar_x'] = meta['pointing']['solar_x'][exp_set, :]
    elif len(lv_1_counts.shape) > 4:
        print(f"ERROR: cannot read input file with data array shape of"
             +f" {lv_1_counts.shape}.", file=sys.stderr)
        return None

    ############################################################################
    ### Determine observation type
    ############################################################################
    if index['nraster'] == 1:
        obs_type = 'sit-and-stare'
    elif index['nexp_prp'] >= 2:
        obs_type = 'multi_scan'
    else:
        obs_type = 'scan'

    ############################################################################
    ### Apply pointing corrections and create output EISCube
    ############################################################################

    ### (1) Apply the AIA offset corrections
    x_center = pointing['xcen'] + pointing['offset_x']
    y_center = pointing['ycen'] + pointing['offset_y']

    ### (2) Compute mean ccd offset for the current window and apply to y_center
    # Note_1: 'ccd_offsets' are in units of [pixels] while 'y_center' is in [arcsec].
    #         However, this should not normally be problem since the EIS y-scale
    #         is 1 [arcsec]/[pixel]
    # Note_2: technically, the ccd_offset varies with wavelength. However, within
    #         a single window, the difference is on the order of 0.05 arcsec
    mean_ccd_offset = np.mean(meta['ccd_offset'])
    y_center = y_center - mean_ccd_offset

    ### (3) Apply wave correction and get median base wavelength value and delta
    counts_shape = lv_1_counts.shape
    ny_pxls = counts_shape[0] # num pixels along the slit (y-axis)
    nx_steps = counts_shape[1] # num raster steps (x-axis)
    n_wave = counts_shape[2] # num wavelength values (i.e. EIS window width)
    corrected_wave = np.zeros(counts_shape)
    for i in range(ny_pxls):
        for j in range(nx_steps):
            corrected_wave[i,j,:] = meta['wave'] - meta['wave_corr'][i,j]

    base_wave = np.median(corrected_wave[:,:,0])
    wave_delt = np.median(np.diff(corrected_wave, axis=2))

    ### (4) Calculate reference pixel coords and fov
    x1 = x_center - pointing['x_scale']*nx_steps/2.0
    x2 = x_center + pointing['x_scale']*nx_steps/2.0
    y1 = y_center - pointing['y_scale']*ny_pxls/2.0
    y2 = y_center + pointing['y_scale']*ny_pxls/2.0

    ### (5) Extract timestamps and calculate the mid point of the observation
    date_obs = index['date_obs']
    date_end = index['date_end']
    date_diff = datetime.fromisoformat(date_end) - datetime.fromisoformat(date_obs)
    date_avg = datetime.fromisoformat(date_obs) + date_diff/2.0
    date_avg = date_avg.isoformat(timespec='milliseconds') # convert to string

    ### (6) Fetch the observer location in heliographic coords
    hg_coords = coords.get_body_heliographic_stonyhurst('earth', time=date_obs)

    ### (7) Calculate average exposure time and cadence
    avg_exptime = np.mean(meta['duration'])
    if index['nexp'] > 1:
        diff_date_obs = np.diff(meta['date_obs'].astype('datetime64'))
        diff_date_obs = diff_date_obs / np.timedelta64(1, 's')
        avg_cad = np.mean(np.abs(diff_date_obs))
    else:
        avg_cad = avg_exptime # default for single exposure obs

    ### (8) Create a new header dict updated values
    # Note: the order of axes here is the same as the original fits index
    output_hdr = dict()

    # Time information
    output_hdr['naxis'] = 3
    output_hdr['date_obs'] = date_obs
    output_hdr['date_beg'] = date_obs
    output_hdr['date_avg'] = date_avg
    output_hdr['date_end'] = date_end
    output_hdr['timesys'] = 'UTC'

    # Observation details
    output_hdr['telescop'] = 'Hinode'
    output_hdr['instrume'] = 'EIS'
    output_hdr['line_id'] = wininfo['line_id'][meta['iwin']]
    output_hdr['measrmnt'] = 'intensity'
    output_hdr['bunit'] = 'unknown' # units of primary observable
    output_hdr['slit_id'] = index['slit_id']
    output_hdr['slit_ind'] = index['slit_ind']
    output_hdr['obs_type'] = obs_type
    output_hdr['nraster'] = index['nraster'] # 1 for sit-and-stare
    output_hdr['nexp'] = index['nexp'] # total num exposures
    output_hdr['nexp_prp'] = index['nexp_prp'] # num exposures per slit position
    output_hdr['tr_mode'] = index['tr_mode'] # tracking mode. "FIX" for no tracking
    output_hdr['saa'] = index['saa'] # IN / OUT South Atlantic Anomaly (SAA)
    output_hdr['hlz'] = index['hlz'] # IN / OUT High-Latitude Zone (HLZ)
    output_hdr['exptime'] = avg_exptime
    output_hdr['cadence'] = avg_cad
    output_hdr['timeunit'] = 's'

    # IDs and Study information
    output_hdr['tl_id'] = index['tl_id']
    output_hdr['jop_id'] = index['jop_id']
    output_hdr['study_id'] = index['study_id']
    output_hdr['stud_acr'] = index['stud_acr']
    output_hdr['rast_id'] = index['rast_id']
    output_hdr['rast_acr'] = index['rast_acr']
    output_hdr['obstitle'] = index['obstitle'][:-1].strip()
    output_hdr['obs_dec'] = index['obs_dec'][:-1].strip()
    output_hdr['target'] = index['target']
    output_hdr['sci_obj'] = index['sci_obj'][:-1].strip()
    output_hdr['noaa_num'] = index['noaa_num']

    # Coordinate information
    output_hdr['naxis1'] = nx_steps
    output_hdr['cname1'] = 'Solar-X'
    output_hdr['crval1'] = x1
    output_hdr['crpix1'] = 1
    output_hdr['cdelt1'] = pointing['x_scale']
    output_hdr['ctype1'] = 'HPLN-TAN'
    output_hdr['cunit1'] = 'arcsec'

    output_hdr['naxis2'] = ny_pxls
    output_hdr['cname2'] = 'Solar-Y'
    output_hdr['crval2'] = y1
    output_hdr['crpix2'] = 1
    output_hdr['cdelt2'] = pointing['y_scale']
    output_hdr['ctype2'] = 'HPLT-TAN'
    output_hdr['cunit2'] = 'arcsec'

    output_hdr['naxis3'] = n_wave
    output_hdr['cname3'] = 'Wavelength'
    output_hdr['crval3'] = base_wave
    output_hdr['crpix3'] = 1
    output_hdr['cdelt3'] = wave_delt
    output_hdr['ctype3'] = 'WAVE'
    output_hdr['cunit3'] = 'Angstrom'

    output_hdr['fovx'] = x2 - x1
    output_hdr['fovy'] = y2 - y1
    output_hdr['xcen'] = x1 + 0.5*(x2-x1)
    output_hdr['ycen'] = y1 + 0.5*(y2-y1)

    output_hdr['hgln_obs'] = hg_coords.lon.deg
    output_hdr['hglt_obs'] = hg_coords.lat.deg
    output_hdr['dsun_obs'] = hg_coords.radius.m

    # Calculate and append extra keys to meta dict for user convenience
    meta['mod_index'] = output_hdr
    meta['aspect'] = pointing['y_scale']/pointing['x_scale']
    meta['aspect_ratio'] = pointing['y_scale']/pointing['x_scale'] # DEPRICATED
    meta['extent_arcsec'] = [x1, x2, y1, y2] # [left, right, bottom, top]
    meta['notes'] = []

    try:
        # Create the WCS object
        # NB: For some reason, the order of axes in the WCS is reversed relative
        #     to the data array inside an NDCube. We should take care to fully
        #     document this for our users.
        clean_wcs = _make_wcs_from_cube_index(output_hdr)

        # Add a user-supplied constant value to the count array
        if count_offset is not None:
            lv_1_counts = lv_1_counts + count_offset

        # Calculate errors due to Poisson noise and read noise
        # Also create data mask to flag invalid values
        read_noise = calc_read_noise(corrected_wave)
        if abs_errs == True:
            data_mask = lv_1_counts <= -100 # mask missing data
            lv_1_count_errs = np.sqrt(np.abs(lv_1_counts) + read_noise**2)
        else:
            data_mask = lv_1_counts <= 0 # mask ALL negative or zero values
            clean_lv_1_counts = lv_1_counts.copy()
            clean_lv_1_counts[data_mask] = 0.0
            lv_1_count_errs = np.sqrt(clean_lv_1_counts + read_noise**2)

        lv_1_count_errs[data_mask] = -100 # EIS missing data err value (in IDL)
        if apply_radcal:
            cube_data = lv_1_counts*radcal_array
            cube_errs = lv_1_count_errs*radcal_array
            data_units = 'erg / (cm2 s sr)'
        else:
            cube_data = lv_1_counts
            cube_errs = lv_1_count_errs
            data_units = 'photon'

        cube_errs = StdDevUncertainty(cube_errs)
        meta['mod_index']['bunit'] = data_units
        output_cube = EISCube(cube_data, wcs=clean_wcs, uncertainty=cube_errs,
                              wavelength=corrected_wave, radcal=radcal_array,
                              meta=meta, unit=data_units, mask=data_mask)
    except:
        print('Error: Failed to initialize WCS or EISCube instance due to bad'
             +' header data. Please report this issue to the eispac development'
             + 'team', file=sys.stderr)
        return None

    return output_cube
