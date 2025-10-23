import numpy as np
from multiprocessing import Pool, cpu_count
from gwpy.timeseries import TimeSeries
from gwpy.time import from_gps, to_gps

# For the base classes and their extentions
import h5py

# imports related to gwdama
from .gwLogger import GWLogger

# Utilities
from gwdama.utilities import _add_method, _add_property

# For the hist and plot methods
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

# To have units
import astropy.units as apu

# To raise warnings
from warnings import warn

# ----- Modified Dataset class -----

@_add_method(h5py.Dataset)
def crop(self, start=None, end=None, return_type='dataset', dts_key=None):
    """
    Crop this :class:`~gwdama.io.Dataset` along the first axis  to the specified time interval. 

    Parameters
    ----------
    start : LIGOTimeGPS, float, str, optional
        lower time to crop to. Default the beginning of the :class:`~gwdama.io.Dataset` first axis
    end : LIGOTimeGPS, float, str, optional, optional
        upper time to crop to. Default the ending of the :class:`~gwdama.io.Dataset` first axis
    return_type : str, optional
            This parameter determines the output of this method, and can take the values ``'dataset'`` or ``'array'``; a ``ValueError`` is rised if it doesn't match any of them. If this is set to ``'dataset'`` (default), a new :class:`~gwdama.io.Dataset` object is created next to the current one, with the ``'_crop'`` string attached to its name, containing the cropped data corresponding to the original dataset. If ``return_type`` is set to ``'array'``, 
    dts_key : str, optional
        If ``return_type=='dataset'`` , this is the *key* associated to this dataset. If not set, custom name is chosen, which is the name of the current dataset followed by ``_psd``. Notice that attempting to call this method twice without specifying the name will rase: ``RuntimeError: Unable to create link (name already exists)``     
        
    Returns
    -------
    dataset
        If ``return_type`` is ``'dataset'``, this method will ruturn a :class:`~gwdama.io.Dataset` object that can be associated to a variable
    cropped : `numpy.ndarray <https://numpy.org/doc/stable/reference/generated/numpy.ndarray.html>`_ 
        Cropped time series associated to this dataset
        
    Raises
    ------
    RuntimeError
        When this method is called twice with ``return_type=='dataset'`` and different ``dts_key`` parameters are not specified  
    ValueError
        If something different than the options ``'dataset'`` or ``'array'`` is chosen
    TypeError
        If this :class:`~gwdama.io.Dataset` is not a time series with valid ``'t0'`` and ``'sample_rate'`` attributes
    
    Notes
    -----
    If ``return_type=='array'`` no indication of the actual starting time will be returned

    """
    if return_type not in ('dataset','array'):
        raise ValueError("Unrecognised 'return_type' parameter. Values must be either 'dataset' or 'array'.")
    
    # If the object doesn't have t0 and sample_rate, a TypeError is raised 
    xt = self.times.value
    
    if start:
        start = to_gps(start).gpsSeconds
        i_min = np.argwhere(xt>=start)[0][0]
    else:
        i_min = 0
    
    if end:
        end = to_gps(end).gpsSeconds
        i_max = np.argwhere(xt<=end)[-1][0]
    else:
        i_max = -1

    cropped = self[i_min:i_max,]
        
    if return_type == 'array':
        # The output array
        return cropped
    
    elif return_type == 'dataset':  
        # Define a structured data type
        
        # Get the name of the parent group to save the PSD along with it
        if dts_key is None:
            string_to_append = '_crop'
            dts_key = self.name+string_to_append
            grp = self.parent
        else:
            grp = self.file
        crop_dset = grp.create_dataset(dts_key, data=cropped)
        
        # Add the attributes
        for k in self.attrs.keys():
            crop_dset.attrs[k] = self.attrs[k] 
        crop_dset.attrs['t0'] = xt[i_min]
                
        return crop_dset
    
    

@_add_property(h5py.Dataset)
def data(self):
    """
    Returns the content of an h5py :class:`~gwdama.io.Dataset` in an easy looking way. If ``self`` has attribute ``'unit'`` and
    it is a string or a `astropy.units.Quantity <https://docs.astropy.org/en/stable/api/astropy.units.Quantity.html#astropy.units.Quantity>`_, then this is put next to the numeric value of this :class:`~gwdama.io.Dataset`. Otherwise, this method is equivalent to ``self[...]``.
    
    Returns
    ------- 
     : :py:func:`numpy.ndarray` of `astropy.units.Quantity <https://docs.astropy.org/en/stable/api/astropy.units.Quantity.html#astropy.units.Quantity>`_ 
         If a ``'unit'`` attribute is defined, the outp[ut is a `astropy.units.Quantity <https://docs.astropy.org/en/stable/api/astropy.units.Quantity.html#astropy.units.Quantity>`_, otherwise it is a :py:func:`numpy.ndarray` otherwise
    """

    raw = self[...]
    # If this is a structured/record array (e.g. dtype with named fields),
    # do NOT attempt to multiply by a single unit – it will fail and is ill-defined.
    if getattr(raw.dtype, "names", None):
        return raw

    unit_attr = self.attrs.get('unit', None)
    if unit_attr is None:
        return raw

    # Accept both Quantity and Unit/string inputs for 'unit' attribute
    if isinstance(unit_attr, apu.Quantity):
        return raw * unit_attr
    else:
        # Handles str (e.g. "m") or Unit object
        return raw * apu.Unit(unit_attr)
            
@_add_property(h5py.Dataset)
def times(self):
    """
    Returns a Numpy array with the time vector corresponding to the curtrrent Dataset if it has 
    ``t0`` and ``sample_rate`` attributes. Raises ValueError if these attributes are not present
    
    Returns
    -------
     : :py:func:`numpy.ndarray` of `astropy.units.Quantity <https://docs.astropy.org/en/stable/api/astropy.units.Quantity.html#astropy.units.Quantity>`_
        Array of times corresponding to this Dataset
        
    Raises
    ------
    KeyError
        if the Dataset is not a time series and has no ``'t0'`` and ``'sample_rate'`` attributes
        
    """
    return (np.arange(len(self))/self.attrs['sample_rate'] + self.attrs.get('t0',0)) *apu.s

@_add_method(h5py.Dataset)
def duration(self, fs=None):
    """
    This method returns the duration in seconds of the current dataset. If the parameter ``fs`` is specified, this is the chosen *sampling frequency* of the data. Otherwise, the method attempts to access the ``sample_rate`` attribute of *self* (if it exists). If a valid ``sample_rate`` is not found, this is automatically set to 1, printing a warning message. 

    Parameters
    ----------
    fs : int, optional
        Sampling frequency of this dataset. Automatically set to 1 if not specified and a ``sample_rate`` attribute doesn't exist in the dataset
    
    Returns
    -------
    : `Astrpy.units <https://docs.astropy.org/en/stable/units/>`_
        Duration in seconds of this time series
    
    Raises
    ------
    ValueError
        if the attribute ``sample_rate`` or alternatively ``fs`` can't be converted to integer
    
    """
    # fs not given
    if fs is None:
        rate_name="sample_rate"
        # attribute exists
        if rate_name in self.attrs:
            try:
                rate = int(self.attrs[rate_name])
                return len(self.data)/rate * apu.s
            except ValueError as ve:
                print(ve, "Unrecognised format for the 'sample_rate' attribute. It can't be converted to float.")
        
        else:
            warn("WARNING!! Unrecognised attribute with the meaning of a sampling frequency. The default value will be chosen to be\
            1. Modify it passing the correct one to the 'fs' parameter of this method, or add a 'sample_rate' attribute to the dataset.")
            fs = 1
            return len(self.data)/fs * apu.s

    elif isinstance(fs, (int,float)):
        return len(self.data)/fs * apu.s
    else:
        raise ValueError("Unrecognised value of the sampling frequency parameter 'fs'. Please, provide either int or float.")
                
@_add_method(h5py.Dataset)
def hist(self, closefig=True, figsize=(7,5), ax=None, **histkwgs):
    """
    Method for making a histogram of the data contained in this dataset, provided they are of numeric
    type and 1D. The output is a `Figure object of matplotlib <https://matplotlib.org/3.3.2/api/_as_gen/matplotlib.pyplot.figure.html>`_. The title is automatically set to be the name of the channel. You can
    access and modify it later. If ``dset.data.ndim`` is higher then one, a ``ValueError`` is raised.
    
    Parameters
    ----------
    closefig : bool, optional
        choose if the returned figure object is automatically closed (``plt.close(fig)``) or not. If ``True`` (default) the figure object is closed after being created. This allows to manipulate and re-open it with the ``.reshow()`` method 
    figsize : (float, float), optional,
        Size in inches of the returned figure object. Default ``(7,5)``
    ax : Matplotlib axes object, default None
        The axes to plot the histogram on.
    **histkwgs : dict, optional
        Dictionary of all the optional parameters for the `pyplot.hist class <https://matplotlib.org/3.3.1/api/_as_gen/matplotlib.pyplot.hist.html>`_.
        
    Returns
    -------
    : `matplotlib.pyplot.figure <https://matplotlib.org/3.3.2/api/_as_gen/matplotlib.pyplot.figure.html>`_
        Figure object of the histogram
    
    Raises
    ------
    ValueError
        If the dataset is not 1D, that is ``self.data.ndim`` > 1
    """
    if self.data.ndim != 1:
        raise ValueError("This dataset appears to be not 1D. Are you sure you whant to make an histogram out of it? If so, do it manually.")
    else:
        from gwdama.plot import make_hist
        if 'channel' in self.attrs:
            title = self.attrs['channel']
        else:
            title =''
        f = make_hist(self.data, title=title, figsize=figsize, ax=ax, **histkwgs)
        
        if ax:
            return ax
        elif closefig:
            plt.close(f)
        return f

@_add_method(h5py.Dataset)
def plot(self, figsize=(10,3), ax=None, epoch=None, scale=None, closefig=True, **axkwgs):
    """
    Plot the content of this Dataset if it is a one dimensional array. This method is meant for time series, so it seeks for attributes like the ``'sample_rate'`` (necessary) and an ``epoch`` (corresponding to the attribute ``'t0'``), which can be passed as an argument of this function.
    
    Parameters
    ----------
    figsize : (float,float), optional
        Size in inches of the returned figure object. Default ``(7,5)``  
    closefig : bool, optional
        choose if the returned figure object is automatically closed (``plt.close(fig)``) or not. If ``True`` (default) the figure object is closed after being created. This allows to manipulate and re-open it with the ``.reshow()`` method 
    ax : Matplotlib axes object, default None
        The axes to plot the histogram on.
    epoch : float, optional
        Time in seconds where to center the plot
    scale : `astropy.units <https://docs.astropy.org/en/stable/units/index.html#module-astropy.units>`_, optional
        This should be a valid `time unit <https://docs.astropy.org/en/stable/units/index.html#module-astropy.units.si>`_, for example ``'s'`` (or ``'second'``), ``'min'`` (or ``'minute'``), ``'hour'`` or ``'day'``
    **axkwgs : dict, optional
        Dictionary of all the optional parameters for the set method of matplotlib axis object.

    Returns
    -------
    : `matplotlib.pyplot.figure <https://matplotlib.org/3.3.2/api/_as_gen/matplotlib.pyplot.figure.html>`_
        Figure object of the plot
    
    Raises
    ------
    ValueError
        If the dataset is not 1D, that is ``self.data.ndim`` > 1
    """
    if self.data.ndim != 1:
        raise ValueError("This dataset appears to be not 1D. Are you sure you whant to make an histogram out of it? If so, do it manually.")
    
    # If an axis object already exists, use it
    if ax:
        axh = ax
    else:
        fig, axh = plt.subplots(figsize=figsize)
    
    # Define x axis
    if ('t0' in self.attrs) and ('sample_rate' in self.attrs):
        xt = self.times - (epoch or self.attrs.get('t0', 0))*apu.s
    
        if not scale:            
            try:
                if "xlim" in axkwgs:
                    xl, xr = axkwgs["xlim"]
                    dur = xr - xl
                else:
                    dur = self.duration().value
                if dur//90 < 1:
                    scale = 's'
                elif dur//(90*60) <1:
                    scale = 'min'
                elif dur//(48*60*60) <1:
                    scale = 'hour'
                else:
                    scale = 'day'
                xt = xt.to(scale)
            except ValueError:
                scale = 's'            

        axh.plot(xt, self[...]);

        axh.set(xlabel=f"Time [{scale}] form {from_gps(epoch or self.attrs.get('t0', 0)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} ({epoch or self.attrs.get('t0', 0)})",ylabel=self.attrs.get('unit',''), xlim=(xt[0].value,xt[-1].value), title=self.attrs.get('channel',''))
    
    else:
        axh.plot(self[...]);
        axh.set(ylabel=self.attrs.get('unit',''), title=self.attrs.get('channel',''))
        
    axh.set(**axkwgs)
    axh.grid(True)
    
    if ax:
        return axh
    elif closefig:
        plt.close(fig)
    return fig
    
@_add_method(h5py.Dataset)
def psd(self, fftlength=None, overlap=None, fs=None, return_type='dataset', dts_key=None, **psdkwgs):
    """
    If the dataset resambles a time series (1D and with an associateded sampling frequency), this metod estimates its Power Specvtral Density (PSD) function by means of the Welch's method, or some modifications of it (median averaging instead of mean). Refer to `scipy.signal.welch <https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html>`_ for further details.
    
    Parameters
    ----------
    fftlength : float, optional 
        Length in seconds of each FFT to use to estimate the PSD. If ``None``, defoult is to use all the data lenght, *i.e.* no averaging is applied
    overlap : float, optional
        Number of seconds of overlap between each consecutive FFTs. If ``None``, no overlap is used and the parameter is set to ``0``.
    fs : int, optional
        Sampling frequency in Hz of the data (if this attribute makes sense). By default, when this is set ot ``None``, this rate is recovered from the ``sample_rate`` attribute of the :ref:`Dataset` object, if available. If the latter is not available a ``ValueError`` is raised, and the ``fs`` parameter must be specified
    return_type : str, optional
        This parameter determines the output of this method, and can take the values ``'dataset'`` or ``'array'``; a ``ValueError`` is rised if it doesn't match any of the latter. If this is set to ``'dataset'`` (default), a new :ref:`Dataset` object is created next to the current one, with the ``'_psd'`` string attached to its name, containing the data corresponding to frequencies and PSD of computed with this method. If ``return_type`` is set to ``'array'``, the usual output of `scipy.signal.welch <https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html>`_ is returned instead
    dts_key : str, optional
        If ``return_type=='dataset'`` , this is the *key* associated to this dataset. If not set, custom name is chosen, which is the name of the current dataset followed by ``_psd``. Notice that attempting to call this method twice without specifying the name will rase: ``RuntimeError: Unable to create link (name already exists)``
    **psdkwargs : dict, optional
        Any other optional keyword argument accepted by `scipy.signal.welch <https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html>`_, with the exception of ``nperseg`` (replaced by ``fftlength``), ``noverlap`` (replaced by ``overlap``), ``nfft`` (automatically set to the next power or two of ``nperseg``), and ``axis`` (``-1``, only 1D arrays). Available arguments are: ``window`` (default ``blackman``), ``detrend`` (``'constant'``), ``return_onesided`` (``True``), ``scaling`` (``'density'``), and ``average`` (``'median'``)
            
    Returns
    -------
        dataset
            If ``return_type`` is ``'dataset'``, this method will ruturn a :ref:`Dataset` object that can be associated to a variable
        f : `numpy.ndarray <https://numpy.org/doc/stable/reference/generated/numpy.ndarray.html>`_ 
            Array of sample frequencies, with `Astrpy.units <https://docs.astropy.org/en/stable/units/>`_, if ``return_type`` is ``'array'``
        Pxx : `numpy.ndarray <https://numpy.org/doc/stable/reference/generated/numpy.ndarray.html>`_ 
            Power spectral density or power spectrum of the time series in the dataset, with `Astrpy.units <https://docs.astropy.org/en/stable/units/>`_, if ``return_type`` is ``'array'``
    
    Raises
    ------
    ValueError
        When the data is not numeric or 1D, the sampling frequency is not recovered from the data, or when the ``return_type`` attribute is set to something different than ``'array'`` or ``'dataset'``
    RuntimeError
        When this method is called twice with ``return_type=='dataset'`` and different ``dts_key`` parameters are not specified
    
    Notes
    -----
    Refer to `scipy documentation <https://docs.scipy.org/doc/scipy/reference/generated /scipy.signal.get_window.html#scipy.signal.get_window>`_ for a list of the available window functions to pass to the PSD estimation.
    
    If you select ``'dataset'`` as the output type, the resulting data will be in the form of a `structured array <https://numpy.org/doc/stable/user/basics.rec.html#module-numpy.doc.structured_arrays>`_ with ``freq`` and ``PSD`` as the *names* of its two *fields*.
        
    """
    if return_type not in ('dataset','array'):
        raise ValueError("Unrecognised 'return_type' parameter. Values must be either 'dataset' or 'array'.")
    
    if (self[...].ndim != 1):
        raise ValueError("This dataset appears to be not 1D. Unclear meaning to be attributre to the PSD of a multidimensional sequence.")
    else:
        pass
    
    if fs is None:
        try:
            fs = int(self.attrs['sample_rate'])
        except:
            raise ValueError("Unrecognised sampling frequency of the dataset. Please provide one to the 'fs' parameter.")
            
    from scipy.signal import welch
    
    # fftlength
    if fftlength is None:
        nperseg = len(self.data) 
    else:
        nperseg = int(fftlength*fs)
    
    # noverlap
    if overlap is None:
        noverlap = 0
    else:
        noverlap = int(overlap*fs)
    
    nfft=psdkwgs.get('nfft', 2**(nperseg - 1).bit_length())
    
    freq, Pxx = welch(self[...], fs=fs, window=psdkwgs.get('window','blackman'), nperseg=nperseg, noverlap=noverlap, nfft=nfft,
                      detrend=psdkwgs.get('detrend','constant'), return_onesided=psdkwgs.get('return_onesided',True),
                      scaling=psdkwgs.get('scaling','density'), axis =- 1, average=psdkwgs.get('average','median'))
    
    import astropy.units as u
    unit_attr = self.attrs.get('unit', None)
    if unit_attr is None:
        in_unit = u.dimensionless_unscaled
    elif isinstance(unit_attr, u.Quantity):
        in_unit = unit_attr.unit
    else:
        in_unit = u.Unit(unit_attr)  # parse strings like "m", "1/Hz", etc.

    scaling = psdkwgs.get('scaling', 'density')
    if scaling == 'density':
        out_unit = (in_unit ** 2) / u.Hz
    else:
        # 'spectrum' => unit**2 (Welch docs)
        out_unit = in_unit ** 2

    if return_type == 'array':
        return freq * u.Hz, Pxx * out_unit
    
    elif return_type == 'dataset':  
        # Define a structured data type
        # struct_data = np.array(list(zip(freq,Pxx)), dtype=([('freq',np.float),('PSD',np.float)])) 
        struct_data = np.array(list(zip(freq, Pxx)), dtype=[('freq', 'f8'), ('PSD', 'f8')]) # To enable to work with NumPy ≥ 2.0
        
        # Get the name of the parent group to save the PSD along with it
        if dts_key is None:
            string_to_append = '_psd'
            dts_key = self.name+string_to_append
            grp = self.parent
        else:
            grp = self.file
        psd_dset = grp.create_dataset(dts_key, data=struct_data)
        
        # Add the attributes
        psd_dset.attrs['f_nyquist'] = fs/2
        
        if 'channel' in self.attrs:
            psd_dset.attrs['channel'] = self.attrs['channel']

        # record the units in a clear way
        psd_dset.attrs['unit'] = str(out_unit)   # unit for the PSD field
        psd_dset.attrs['freq_unit'] = 'Hz'       # make freq unit explicit

        
        return psd_dset

@_add_method(h5py.Dataset)
def resample(self, outfs, fs=None, method='poly', return_type='dataset', dts_key=None, fraclimit=None, **reskwgs):
    """
    Resample ``self`` along the given axis using various possible methods, specified by the ``method`` argument. Each of them has some advantages and disadvantages, so a careful choise is advisable.
    
    ``poly`` (default) is based on `scipy.signal.resample_poly <https://docs.scipy.org/doc/scipy-0.19.0/reference/generated/scipy.signal.resample_poly.html#scipy.signal.resample_poly>`_ does upsampling/downsampling and the associated filtering, using a `polyphase filter <https://en.wikipedia.org/wiki/Polyphase_quadrature_filter>`_. This has a very good balance in speed and performance, with only a moderate distortion of the data close to the Nyquist frequency. If ``outfs`` and ``fs`` are prime, this can be quite slow too.
    
    ``fft`` is based on `scipy.signal.resample method <https://docs.scipy.org/doc/scipy-0.19.0/reference/generated/scipy.signal.resample.html>`_. It does upsampling/downsampling and the associated filtering, entirely in the frequency domain, using the `Fast Fourier Transform technique <https://en.wikipedia.org/wiki/Trigonometric_interpolation#Relation_with_the_discrete_Fourier_transform>`_ (bonus for data length that are multiple of two). Because it is using the Fourier Transform, a key assumption is that the signal that is fed in its input is *periodic*. This gives usually the best performances and mantaines the spectrum unaltered. However it can be slow if the input data lenght is not multiple of two and prime, and also if it is not multiple of the output samples. In the latter case, a slight distorsion of the time axis is also possible, with a linearly increasing phase difference. Avoid this method if this is the case.
    
    ``decimate`` is arguably the simplest and fastest method (``ftype='iir'``), although it is not always advisable to use it and the overal performances are not as good as the previous two methods. It is based on the `scipy.signal.decimate method <https://docs.scipy.org/doc/scipy-0.19.0/reference/generated/scipy.signal.decimate.html>`_, which consists in an antilaiasing low-pass filter (either an ``'iir'`` or a ``'fir'`` filter) followed by a decimation, such as ``data[::q_factor]``. If a ``'iir'`` filter is chosen and the relative *q_factor* between input and output frequency is larger than 10, the decimate method is called recursively. For ``iir``, the distorsion can be significant in proximity of the Nyquist frequency. Selecting ``'fir'`` as ``ftype`` we will have a linear phase, the output will be the same of ``poly``, but the method will result generally slower. If we select ``'iir'``, it is going to be much faster, but the phase is only approximately linear. Also, differently from the other two methods, this is not suitable for *upsampling* or when the original sampling frequency is not a multiple of ``outfs``. In this case ``poly`` is used instead.
   
    Parameters
    ----------
    outfs : float
        Desired output frequency of the resampled data. It is advisable to pick a frequency that is submultiple of the original sampling frequency of the data
    fs : float, optional
        Sampling frequency of ``self``. If not provided, this is automatically recovered from ``self.attrs['sample_rate']``. If this attribute is not present an ``AttributeError`` is raised.
    return_trype : str, optional
        array, dataset, inplace
    method : str, optional
        Method with which to perform the resampling. Default is ``'poly'``, for a *poly-phase filtering*. Don't modify it if you don't have read the description above first
    return_type : str, optional
        This parameter determines the output of this method, and can take the values ``'dataset'`` or ``'array'``; a ``ValueError`` is rised if it doesn't match any of the latter. If this is set to ``'dataset'`` (default), a new :ref:`Dataset` object is created next to the current one, with the ``'_r{outfs}'`` string attached to its name, containing the data corresponding to resampled time series. If ``return_type`` is set to ``'array'``, the output is an array  
    dts_key : str, optional
        If ``return_type=='dataset'`` , this is the *key* associated to this dataset. If not set, custom name is chosen, which is the name of the current dataset followed by ``f'_r{outfs}''``. Notice that attempting to call this method twice without specifying the name will rase: ``RuntimeError: Unable to create link (name already exists)``
    fraclimit : int, optional
        What if one attempts to reample to ``outfs = np.pi``? To prevent this questionable choice, still allowing float values for the input and output frequencies, we have introduced this parameter as the maximum denominator of the fraction equivalent to ``fs``/``outfs``. This also prevent rounding issues when working with floats. Default value is ``1000``. Try to make use of integer frequencies, instead of changing this value  

    **reskwgs : dict, optional
        These are all the other keyword arguments to pass to the previous resampling method. Refer to the corresponding documentation for further details
    Returns
    -------
    dataset
        If ``return_type`` is ``'dataset'``
    array
        If ``return_type`` is ``'array'``
    
    Raises
    ------
    AttributeError
        If ``fs`` is not specified and a valid ``'sample_rate'`` attribute is not present
    ValueError
        If ``method`` aor ``return_type`` take values that are not permitted
    RuntimeError
        When this method is called twice with ``return_type=='dataset'`` and different ``dts_key`` parameters are not specified
    
    See Also
    --------
    gwdama.preprocessing.decimate_recursive
        
    """
    from fractions import Fraction

    if not fs:
        fs = int(self.attrs['sample_rate'])
        
    if method=='poly':
        from scipy.signal import resample_poly
        
        # Allow float frequencies
        if not isinstance(fs,int):
            fs=Fraction(fs)
            
        if not isinstance(outfs,int):
            outfs=Fraction(outfs)

        Frac = Fraction(fs, outfs).limit_denominator(fraclimit or 1000)
        up, down = Frac.denominator, Frac.numerator
        res = resample_poly(self[...], up=up, down=down, **reskwgs)
    elif method=='fft':
        from scipy.signal import resample

        ax = reskwgs.get('axis',0)
        num = int(self.shape[ax] * outfs/fs)
        res = resample(self[...], num=num, **reskwgs)
    elif method=="decimate":
        from gwdama.preprocessing import decimate_recursive
        from scipy.signal import decimate

        # Allow float frequencies
        if not isinstance(fs,int):
            fs=Fraction(fs)
            
        if not isinstance(outfs,int):
            outfs=Fraction(outfs)

        Frac = Fraction(fs, outfs).limit_denominator(fraclimit or 1000)
        up, down = Frac.denominator, Frac.numerator
        if up==1:
            ftype = reskwgs.get('ftype','fir')
            if ftype=='fir':
                reskwgs.update({"ftype": "fir"})
                res = decimate(self[...], q=down, **reskwgs)
            else:
                res = decimate_recursive(self[...], q_factor=down, **reskwgs)[0]
        else:
            print("Warning!! The output frequency is not a submultiple of the original sampling. Decimation mathod not compatible, 'poly_phase' filter applied instead")
            from scipy.signal import resample_poly
            res = resample_poly(self[...], up=up, down=down)
    else:
        raise ValueError("Unrecognised 'method' parameter. Values must be either 'poly' (poly-phase filter), 'fft', or 'decimate' (lowpass+decimation).")
        
    if return_type=='array':
        return res
    
    elif return_type=='dataset':
        if dts_key is None:
            string_to_append = f'_r{outfs}'
            dts_key = self.name+string_to_append
            grp = self.parent
        else:
            grp = self.file            
        res_dset = grp.create_dataset(dts_key, data=res)
        for k in self.attrs.keys():
            res_dset.attrs[k] = self.attrs[k]
        if isinstance(outfs,Fraction):
            res_dset.attrs['sample_rate'] = float(outfs)
        else:
            res_dset.attrs['sample_rate'] = outfs
        return res_dset        
        
    else:
        raise ValueError("Unrecognised 'return_type' parameter. Values must be either 'dataset' or 'array'.")
        
    
@_add_method(h5py.Dataset)   
def taper(self, fs=None, side='leftright', duration=None, nsamples=None, return_type='dataset', dts_key=None, window=('tukey',0.25)):
    """
    Taper the edges of this datset smoothly to zero. The method automatically tapers from the second stationary point (local maximum or minimum) on the specified side of the input. However, the method will never taper more than half the full width of the data, and will fail if there are no stationary points.
    
    Parameters
    ----------
    fs : float, optional
        Sampling frequency of this dataset. By defoult (``fs=None``) this value is read from the ``sample_rate`` attribute of the dataset, if it exists. If not, this is automatically assumed to be 1
    side : str, optional
        Sides to smooth to zero. Possible options are: ``leftright`` (defautl), ``left``, or ``right``
    duration : float, optional
        The duration of time to taper, will override ``nsamples`` if both are provided as arguments
    nsamples : int, optional
        The number of samples to taper, will be overridden by ``duration`` if both are provided as arguments
    return_type: str, optional
        This parameter determines the output of this method, and can take the values ``'dataset'`` or ``'array'``; a ``ValueError`` is rised if it doesn't match any of the latter. If this is set to ``'dataset'`` (default), a new :ref:`Dataset` object is created next to the current one, with the ``'_taper'`` string attached to its name, containing the data corresponding to the whitened timeseries
    dts_key : str, optional
        If ``return_type=='dataset'`` , this is the *key* associated to this dataset. If not set, custom name is chosen, which is the name of the current dataset followed by ``_taper``. Notice that attempting to call this method twice without specifying the name will rase: ``RuntimeError: Unable to create link (name already exists)``
    
    Returns
    -------
    dataset
        If ``return_type`` is ``'dataset'``, this method will ruturn a :ref:`Dataset` object that can be associated to a variable
    whitened : `numpy.ndarray <https://numpy.org/doc/stable/reference/generated/numpy.ndarray.html>`_ 
        Whitened timeseries
        
    Raises
    ------
    RuntimeError
        When this method is called twice with ``return_type=='dataset'`` and different ``dts_key`` parameters are not specified   
    
    """
    from gwdama.preprocessing import taper
    
    if return_type not in ('dataset','array'):
        raise ValueError("Unrecognised 'return_type' parameter. Values must be either 'dataset' or 'array'.")
    
    if (self.data.ndim != 1):
        raise ValueError("This dataset appears to be not 1D. Plase, provide 1D sequence.")
    else:
        pass
    
    if not fs:
        try:
            fs = int(self.attrs['sample_rate'])
        except:
            fs = 1
            pass
    
    tp_data = taper(self[...], fs=fs, side=side, duration=duration, nsamples=nsamples, window=window)

    if return_type == 'array':
        return tp_data
    
    elif return_type == 'dataset':
        if dts_key is None:
            string_to_append = '_taper'
            dts_key = self.name+string_to_append
            grp = self.parent
        else:
            grp = self.file
        tp_dset = grp.create_dataset(dts_key, data=tp_data)
        
        tp_dset.attrs['taper'] = window
        for k in self.attrs.keys():
            tp_dset.attrs[k] = self.attrs[k] 
        
        return tp_dset
    

@_add_method(h5py.Dataset)
def to_TimeSeries(self, fs=None, unit=None, t0=None, **TSkwgs):
    """
    This method attemp to convert the current :class:`~gwdama.io.Dataset` into a `TimeSeries instance of GWpy <https://gwpy.github.io/docs/stable/api/gwpy.timeseries.TimeSeries.html#gwpy.timeseries.TimeSeries>`_. The array-like ``value`` is taken from ``self.data``. The other parameters are either read from the :class:`~gwdama.io.Dataset` attributes or set manually passing them as arguments to the method.
    
    Parameters
    ----------
    fs : float, optional
        The sampling rate of the current dataset. If not specified, this method attempts by default to read the value of the ``sample_rate`` attribute, if available. If not, ``fs`` is set to 1. Notice that this corresponds to the ``sample_rate`` parameter of the `TimeSeries class <https://gwpy.github.io/docs/stable/api/gwpy.timeseries.TimeSeries.html#gwpy.timeseries.TimeSeries>`_
    t0 :  LIGOTimeGPS, float, str, optional
        GPS epoch associated with these data, any input parsable by to_gps is fine
    unit : `Unit <https://docs.astropy.org/en/stable/api/astropy.units.Unit.html#astropy.units.Unit>`_, optional
        physical unit of these data
    **TSkwgs : dict, optional
        These are all the other keyword arguments to pass to the `TimeSeries class <https://gwpy.github.io/docs/stable/api/gwpy.timeseries.TimeSeries.html#gwpy.timeseries.TimeSeries>`_. Refer to the corresponding documentation for further details
        
    Returns
    -------
    : `TimeSeries <https://gwpy.github.io/docs/stable/api/gwpy.timeseries.TimeSeries.html#gwpy.timeseries.TimeSeries>`_
        The current dataset converted into an `instance of GWpy TimeSeries <https://gwpy.github.io/docs/stable/api/gwpy.timeseries.TimeSeries.html#gwpy.timeseries.TimeSeries>`_
    
    """
    if not fs:
        fs = self.attrs.get('sample_rate', 1)
    if not t0:
        t0 = self.attrs.get('t0', 0)
    if not unit:
        unit = self.attrs.get('unit', None)
        
    TS = TimeSeries(self[...], t0=t0, sample_rate=fs, unit=unit, **TSkwgs)
    return TS
    
    
@_add_method(h5py.Dataset)
def whiten(self, fftlength=None, overlap=None, fs=None, phase_shift=0, time_shift=0, return_type='dataset', dts_key=None, taper_edges=None, **psdkwgs):
    """
    Method to compute the *whiten time-series* from the current dataset: the input is detrended and the output normalised such that, if the input is stationary and Gaussian, then the output will have zero mean and unit variance. The most of the parameters of this mehtod are those needed to compute a PSD. A tapering of the edges is also applied to get rid of the effect of filter settle-in.
    
    Parameters
    ----------
    fftlength : float, optional
        Length in seconds of the segment to use for computuing the psd
    taper_edges : float, optional
        The edges of the whitened time-series can be round off to reduce filtering effects. You can specify the duration of the taper with this parameter or set it to 0 if you don't want any. Dafault duration is half of ``fftlength``
    dts_key : str, optional
        If ``return_type=='dataset'`` , this is the *key* associated to this dataset. If not set, custom name is chosen, which is the name of the current dataset followed by ``_whiten``. Notice that attempting to call this method twice without specifying the name will rase: ``RuntimeError: Unable to create link (name already exists)``
    
    Raises
    ------
    RuntimeError
        When this method is called twice with ``return_type=='dataset'`` and different ``dts_key`` parameters are not specified
   
    See Also
    --------
    gwdama.io.dataset.psd : Reference for the parameters to be chosen in this method
    gwdama.io.dataset.taper : Tapering edges technique
            
    """
    from scipy.interpolate import interp1d
    from gwdama.preprocessing import whiten, taper
    
    if not fs:
        try:
            fs = int(self.attrs['sample_rate'])
        except:
            raise ValueError("Unrecognised sampling frequency of the dataset. Please provide one to the 'fs' parameter.")
    
    if not fftlength:
        fftlength = min(4, self.duration().value)
    if not overlap:
        overlap = fftlength/2
    
    pkwgs = {'detrend':'linear', 'return_onesided':True, 'scaling':'density'}
    pkwgs.update(psdkwgs)
    # Get the PSD as an array
    freq, PSD = self.psd(fftlength=fftlength, overlap=overlap, fs=fs, return_type='array', **pkwgs)
    
    interp_psd = interp1d(freq, PSD, fill_value="extrapolate")
    
    # Detrend the data before applying the whitening function
    from scipy.signal import detrend
    ddata = detrend(self[...])
    white = whiten(ddata, interp_psd, 1/fs, phase_shift=phase_shift, time_shift=phase_shift)
    
    # Due to filter settle-in, a segment of length 0.5*fduration will be corrupted at the beginning and end
    # of the output. 
    if psdkwgs:
        win = psdkwgs.get('window', 'tukey')
    else:
        win = ('tukey',0.5)
    
    if taper_edges is None:
        white = taper(white, fs=fs, duration=fftlength/2, window=win)
    elif taper_edges>0:
        white = taper(white, fs=fs, duration=taper_edges, window=win)
    else:
        pass
    
    if return_type == 'array':
        return white
    
    elif return_type == 'dataset':
        if dts_key is None:
            string_to_append = '_whiten'
            dts_key = self.name+string_to_append
            grp = self.parent
        else:
            grp = self.file
        white_dset = grp.create_dataset(dts_key, data = white)
        
        for k in self.attrs.keys():
            white_dset.attrs[k] = self.attrs[k] 
        
        return white_dset
    
@_add_property(h5py.Dataset)
def show_attrs(self):
    """
    Method that make a Dataset to 'show the attributes'
    """
    to_print = ''
    for k, val in self.attrs.items():
        to_print += "{:>10} : {}\n".format(k, val)
    #return to_print
    print(to_print)

# ----- Experimental -----
@_add_method(Figure)
def reshow(self):
    """
    Method to re-show a closed Figure object
    """
    from gwdama.plot import reshow
    reshow(self)
    