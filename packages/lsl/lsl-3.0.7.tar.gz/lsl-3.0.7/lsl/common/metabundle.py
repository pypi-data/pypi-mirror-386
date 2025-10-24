"""
Module for working with any MCS meta-data tarball and extracting the useful bits
out it and putting those bits into Python objects, e.g, 
:class:`lsl.common.stations.LWAStation` and :class:`lsl.common.sdmDP.SDM`.
"""

import os

from lsl.common import metabundleDP, metabundleADP, metabundleNDP

from lsl.misc import telemetry
telemetry.track_module()

__version__ = '1.2'
__all__ = ['get_style', 'get_sdm', 'get_beamformer_min_delay', 'get_station',
           'get_session_metadata', 'get_session_spec', 'get_observation_spec',
           'get_sdf', 'get_command_script', 'get_asp_configuration',
           'get_asp_configuration_summary', 'is_valid']


def get_style(tarname, return_module=False, verbose=False):
    """
    Given a filename, determine which metadata style (DP, ADP, or NDP) it
    corresponds to.  Returns a string of the module name that can read it, None
    if one cannot be found.
    
    .. versionadded:: 3.0.0
    """
    
    if not os.path.isfile(tarname) or not os.access(tarname, os.R_OK):
        raise OSError("%s does not exists or is not readable" % tarname)
        
    provider = None
    for backend in (metabundleDP, metabundleADP, metabundleNDP):
        if backend.is_valid(tarname, verbose=False):
            if return_module:
                provider = backend
            else:
                provider = backend.__name__
            break
    return provider


def get_sdm(tarname):
    """
    Given an MCS meta-data tarball, extract the information stored in the 
    dynamic/sdm.dat file and return a :class:`lsl.common.sdmDP.SDM` instance
    describing the dynamic condition of the station.
    
    If a sdm.dat file cannot be found in the tarball, None is returned.
    """
    
    if not os.path.isfile(tarname) or not os.access(tarname, os.R_OK):
        raise OSError("%s does not exists or is not readable" % tarname)
        
    backend = get_style(tarname, return_module=True)
    if backend is None:
        raise RuntimeError("Failed to determine metadata style")
    return backend.get_sdm(tarname)


def get_beamformer_min_delay(tarname):
    """
    Given an MCS meta-data tarball, extract the minimum beamformer delay in 
    samples and return it.  If no minimum delay can be found in the tarball, 
    None is returned.
    """
    
    if not os.path.isfile(tarname) or not os.access(tarname, os.R_OK):
        raise OSError("%s does not exists or is not readable" % tarname)
        
    backend = get_style(tarname, return_module=True)
    if backend is None:
        raise RuntimeError("Failed to determine metadata style")
    return backend.get_beamformer_min_delay(tarname)


def get_station(tarname, apply_sdm=True):
    """
    Given an MCS meta-data tarball, extract the information stored in the ssmif.dat 
    file and return a :class:`lsl.common.stations.LWAStation` object.  Optionally, 
    update the :class:`lsl.common.stations.Antenna` instances associated whith the
    LWAStation object using the included SDM file.
    
    If a ssmif.dat file cannot be found in the tarball, None is returned.  
    """
    
    if not os.path.isfile(tarname) or not os.access(tarname, os.R_OK):
        raise OSError("%s does not exists or is not readable" % tarname)
        
    backend = get_style(tarname, return_module=True)
    if backend is None:
        raise RuntimeError("Failed to determine metadata style")
    return backend.get_station(tarname, apply_sdm=apply_sdm)


def get_session_metadata(tarname):
    """
    Given an MCS meta-data tarball, extract the session meta-data file (MCS0030, 
    Section 7) and return a dictionary of observations that contain dictionaries 
    of the OP_TAG (tag), DRSU Barcode (drsu), OBS_OUTCOME (outcome), and the 
    MSG (msg).
    
    .. versionchanged:: 0.6.5
        Update to the new _metadata.txt format
    """
    
    if not os.path.isfile(tarname) or not os.access(tarname, os.R_OK):
        raise OSError("%s does not exists or is not readable" % tarname)
        
    backend = get_style(tarname, return_module=True)
    if backend is None:
        raise RuntimeError("Failed to determine metadata style")
    return backend.get_session_metadata(tarname)


def get_session_spec(tarname):
    """
    Given an MCS meta-data tarball, extract the session specification file (MCS0030, 
    Section 5) and return a dictionary of parameters.
    """
    
    if not os.path.isfile(tarname) or not os.access(tarname, os.R_OK):
        raise OSError("%s does not exists or is not readable" % tarname)
        
    backend = get_style(tarname, return_module=True)
    if backend is None:
        raise RuntimeError("Failed to determine metadata style")
    return backend.get_session_spec(tarname)


def get_observation_spec(tarname, obs_id=None):
    """
    Given an MCS meta-data tarball, extract one or more observation specification 
    file (MCS0030, Section 6) and return a list of dictionaries corresponding to
    each OBS file.  If the `obs_id` keyword is set to a list of observation
    numbers, only observations matching the numbers in `obs_id` are returned.
    """
    
    if not os.path.isfile(tarname) or not os.access(tarname, os.R_OK):
        raise OSError("%s does not exists or is not readable" % tarname)
        
    backend = get_style(tarname, return_module=True)
    if backend is None:
        raise RuntimeError("Failed to determine metadata style")
    return backend.get_observation_spec(tarname, obs_id=obs_id)


def get_sdf(tarname):
    """
    Given an MCS meta-data tarball, extract the session specification file, the 
    session meta-data file, and all observation specification files to build up
    a SDF-representation of the session.
    
    .. note::
        This function returns a full :class:`lsl.common.sdf.Project` instance 
        with the session in question stored under `project.sessions[0]` and the 
        observations under `project.sessions[0].observations`.
    """
    
    if not os.path.isfile(tarname) or not os.access(tarname, os.R_OK):
        raise OSError("%s does not exists or is not readable" % tarname)
        
    backend = get_style(tarname, return_module=True)
    if backend is None:
        raise RuntimeError("Failed to determine metadata style")
    return backend.get_sdf(tarname)


def get_command_script(tarname):
    """
    Given an MCS meta-data tarball, extract the command script and parse it.  The
    commands are returned as a list of dictionaries (one dictionary per command).
    """
    
    if not os.path.isfile(tarname) or not os.access(tarname, os.R_OK):
        raise OSError("%s does not exists or is not readable" % tarname)
        
    backend = get_style(tarname, return_module=True)
    if backend is None:
        raise RuntimeError("Failed to determine metadata style")
    return backend.get_command_script(tarname)


def get_asp_configuration(tarname, which='beginning'):
    """
    Given an MCS meta-data tarball, extract the ASP MIB contained in it and return 
    a dictionary of values for the filter, AT1, AT2, and ATSplit.  The 'which'
    keyword is used to specify whether or not the configuration returned is at the
    beginning (default) or end of the session.
    
    .. versionadded:: 0.6.5
    """
    
    if not os.path.isfile(tarname) or not os.access(tarname, os.R_OK):
        raise OSError("%s does not exists or is not readable" % tarname)
        
    which = which.lower()
    if which not in ('beginning', 'begin', 'end'):
        raise ValueError(f"Unknown configuration time '{which}'")
        
    backend = get_style(tarname, return_module=True)
    if backend is None:
        raise RuntimeError("Failed to determine metadata style")
    return backend.get_asp_configuration(tarname, which=which)


def get_asp_configuration_summary(tarname, which='beginning'):
    """
    Similar to get_asp_configuration, but returns only a single value for each
    of the four ASP paramters:  filter, AT, AT2, and ATSplit.  The values
    are based off the mode of the parameter.
    
    .. versionadded:: 0.6.5
    """
    
    if not os.path.isfile(tarname) or not os.access(tarname, os.R_OK):
        raise OSError("%s does not exists or is not readable" % tarname)
        
    backend = get_style(tarname, return_module=True)
    if backend is None:
        raise RuntimeError("Failed to determine metadata style")
    return backend.get_asp_configuration_summary(tarname, which=which)


def is_valid(tarname, verbose=False):
    """
    Given a filename, see if it is valid metadata tarball or not.
    
    .. versionadded:: 1.2.0
    """
    
    if not os.path.isfile(tarname) or not os.access(tarname, os.R_OK):
        raise OSError("%s does not exists or is not readable" % tarname)
        
    valid = False
    for backend in (metabundleDP, metabundleADP, metabundleNDP):
        valid |= backend.is_valid(tarname, verbose=False)
        if valid:
            break
    return valid
