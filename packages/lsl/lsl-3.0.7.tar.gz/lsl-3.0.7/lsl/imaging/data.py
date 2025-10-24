"""
Classes to hold visibility data that are used internally with LSL.
"""

import aipy
import copy
import numpy as np

from lsl import astro

from lsl.misc import telemetry
telemetry.track_module()


__version__ = "0.1"
__all__ = ['PolarizationDataSet', 'VisibilityDataSet', 'VisibilityData']


class PolarizationDataSet(object):
    """
    Class to hold the visibility data/weight/mask for a single polarization.
    """
    
    def __init__(self, polarization, data=None, weight=None, mask=None):
        self.polarization = polarization.upper()
        if data is not None:
            self.data = data
        else:
            self.data = np.array([], dtype=np.complex64)
            
        if weight is None:
            weight = np.ones(self.data.shape, dtype=np.float32)
        self.weight = weight
        
        if mask is None:
            mask = np.zeros(self.data.shape, dtype=bool)
        self.mask = mask
            
    @property
    def nbaseline(self):
        """
        The number of baselines contained in the data.
        """
        
        return len(self.data)
        
    def copy(self):
        """
        Return a copy of the object.
        """
        
        pol_copy = PolarizationDataSet(self.polarization, 
                                       data=self.data.copy(), 
                                       weight=self.weight.copy(), 
                                       mask=self.mask.copy())
        return pol_copy
        
    def append(self, data, weight=None, mask=None):
        """
        Append a new visibility to the object.
        """
        
        if self.data.size == 0:
            ## Deal with the first batch of data being added
            self.data = data
            
            if weight is None:
                weight = np.ones(data.shape, dtype=np.float32)
            if self.weight.shape != data.shape:
                raise ValueError("weight shape does not match the data shape")
            self.weight = weight
            
            if mask is None:
                mask = np.zeros(data.shape, dtype=bool)
            if self.mask.shape != data.shape:
                raise ValueError("mask shape does not match the data shape")
            self.mask = mask
            
        else:
            self.data = np.vstack([self.data, data])
            
            if weight is None:
                weight = np.ones(data.shape, dtype=np.float32)
            if self.weight.shape != data.shape:
                raise ValueError("weight shape does not match the data shape")
            self.weight = np.vstack([self.weight, weight])
            
            if mask is None:
                mask = np.zeros(data.shape, dtype=bool)
            if self.mask.shape != data.shape:
                raise ValueError("mask shape does not match the data shape")
            self.mask = np.vstack([self.mask, mask])
            
    def extend(self, data, weight=None, mask=None):
        """
        Extend the object with a collection of visibilites.
        """
        
        if weight is None:
            weight = [None for i in data]
        if mask is None:
            mask = [None for i in data]
        for d,w,m in zip(data, weight, mask):
            self.append(d, weight=w, mask=m)
            
    def sort(self, order):
        """
        Apply the specified ordering on the object.
        """
        
        if len(order) != self.data.shape[0]:
            raise ValueError("order length does not match data length")
        self.data = np.take(self.data, order, axis=0)
        self.weight = np.take(self.weight, order, axis=0)
        self.mask = np.take(self.mask, order, axis=0)
        
    def subset(self, selection):
        """
        Return a subset of the data.
        """
        
        new_pol = PolarizationDataSet(self.polarization, 
                                      data=np.take(self.data, selection, axis=0),
                                      weight=np.take(self.weight, selection, axis=0), 
                                      mask=np.take(self.mask, selection, axis=0))
        return new_pol


class VisibilityDataSet(object):
    """
    Class to wrap a single integration of visibility data.
    """
    
    def __init__(self, jd, freq, baselines, uvw, antennaarray=None, phase_center=None, **kwds):
        self.jd = jd
        self.freq = freq
        self.baselines = baselines
        self.uvw = uvw
        if antennaarray is not None and not isinstance(antennaarray, aipy.amp.AntennaArray):
            raise TypeError("Expected antennaarray to be either None or AntennaArray")
        self.antennaarray = copy.copy(antennaarray)
        if self.antennaarray is not None:
            self.antennaarray.set_jultime(self.jd)
        self.phase_center = phase_center
        
        self.pols = []
        self._extra_attrs = []
        for key in kwds:
            if key.upper() in ('XX', 'XY', 'YX', 'YY', 'RR', 'RL', 'LR', 'LL', 'I', 'Q', 'U', 'V'):
                self.append( kwds[key] )
            else:
                self._extra_attrs.append( key )
                setattr(self, key, kwds[key])
                
    def __contains__(self, value):
        return True if value in self.pols else False
        
    def __iter__(self):
        i = 0
        while i < self.npol:
            pol = self.pols[i]
            yield getattr(self, pol)
            i += 1
            
    @property
    def nbaseline(self):
        """
        The number of baselines in the data.
        """
        
        return len(self.baselines)
        
    @property
    def nchan(self):
        """
        The number of frequency channels in the data.
        """
        
        return len(self.freq)
        
    @property
    def npol(self):
        """
        The number of polarizations stored.
        """
        
        return len(self.pols)
        
    @property
    def mjd(self):
        """
        The MJD that the data correspond to.
        """
        
        return self.jd - astro.MJD_OFFSET
        
    def copy(self, include_pols=True):
        """
        Return a copy of the object.  Be default this includes copies of all 
        of the associated PolarizationDataSet objects.  Setting 'include_pols'
        to False will not copy these objects.
        """
        
        set_copy = VisibilityDataSet(self.jd*1.0, 
                                     self.freq.copy(), 
                                     copy.copy(self.baselines), 
                                     self.uvw.copy(), 
                                     antennaarray=copy.copy(self.antennaarray), 
                                     phase_center=self.phase_center)
        for attr in self._extra_attrs:
            set_copy._extra_attrs.append( attr )
            setattr(set_copy, attr, copy.copy(getattr(self, attr)))
            
        if include_pols:
            for pol in self:
                pol_copy = pol.copy()  
                set_copy.append(pol_copy)
        return set_copy               
        
    def append(self, value):
        """
        Append a new PolarizationDataSet object.  If the polarization already
        exists it is replaced.
        """
        
        if not isinstance(value, PolarizationDataSet):
            raise TypeError("Must be a VisibilityDataSet instance")
        if self.nbaseline != value.nbaseline:
            raise RuntimeError("Baseline count mis-match")
            
        pol = value.polarization.upper()
        if pol not in self.pols:
            self.pols.append(pol)
        setattr(self, pol, value)
        
    @property
    def _baseline_order(self):
        def __cmp_baseline(bl):
            return 4096*bl[0] + bl[1]
            
        return [i for (v, i) in sorted((v, i) for (i, v) in enumerate([__cmp_baseline(bl) for bl in self.baselines]))]
        
    def sort(self, order=None):
        """
        Sort the stored data using the order provided in the 'order' keyword.
        If not ordering is provided, the data are sorted by baseline pair.
        """
        
        if order is None:
            order = self._baseline_order
            
        self.baselines = [self.baselines[i] for i in order]
        self.uvw = np.take(self.uvw, order, axis=0)
        for pds in self:
            pds.sort(order)
            
    def rephase(self, new_phase_center):
        """
        Shift the phase center of the data to a new phase center.
        """
        
        if self.phase_center is None:
            raise AttributeError("No phase center defined for this data set")
        if self.antennaarray is None:
            raise AttributeError("No anntennaarray defined for this data set")
            
        # Update the time for the AntennaArray
        self.antennaarray.set_jultime(self.jd)
        
        # Recompute
        if self.phase_center != 'z':
            self.phase_center.compute(self.antennaarray)
        if new_phase_center != 'z':
            new_phase_center.compute(self.antennaarray)
            
        # Go!
        for pds in self:
            pds.data = pds.data.astype(np.complex128)
            ## Loop over baselines
            for k in range(self.nbaseline):
                ### Load in the data
                i,j = self.baselines[k]
                vis = pds.data[k,:]
                
                ### Compute the uvw coordinates and the new phasing
                try:
                    crd = self.antennaarray.gen_uvw(j, i, src=new_phase_center)[:,0,:]
                    vis = self.antennaarray.unphs2src(vis, self.phase_center, j, i)
                    vis = self.antennaarray.phs2src(vis, new_phase_center, j, i)
                except aipy.phs.PointingError:
                    raise RuntimeError("Rephasing center is below the horizon")
                    
                ### Save
                self.uvw[k,:,:] = crd
                pds.data[k,:] = vis
                
        # Update the phase center
        self.phase_center = new_phase_center
        
    def get_uv_range(self, min_uv=0.0, max_uv=np.inf):
        """
        Return a copy of the data containing only baselines with the (u,v)
        distances allowed by the 'min_uv' and 'max_uv' cuts.
        """
        
        # Force min to be less than max
        if min_uv > max_uv:
            temp = min_uv
            min_uv = max_uv
            max_uv = temp
            
        # Find out the baseline lengths and create a list of good ones
        center_uvw = self.uvw[:,:2,self.nchan//2]
        center_uvw = np.sqrt( (center_uvw**2).sum(axis=1) ).ravel()
        selection = np.where( (center_uvw >= min_uv) & (center_uvw < max_uv) )[0]
        
        # Create the new data set
        new_baselines = [self.baselines[b] for b in selection]
        new_data = self.copy(include_pols=False)
        new_data.baselines = new_baselines
        new_data.uvw = self.uvw[selection,:,:]*1.0
        
        for pds in self:
            new_data.append( pds.subset(selection) )
            
        # Done
        return new_data
        
    def get_antenna_subset(self, include=None, exclude=None, indicies=True):
        """
        Return a copy of the data containing baselines that meet the specified
        antenna selection criteria.  The selection is governed by the 'include', 
        'exclude', and 'indicies' keywords.  If 'include' is not 'all' or None,
        only baselines containing antennas in the list are selected.  If
        'exclude' is not 'none' or None, only baselines not containing antennas
        in the list are selected.  If both 'include' and 'exclude' are provided,
        the 'include' list has priority.  'indicies' sets whether or not the
        selection criteria are provided as indicies of the antennas stored in
        the antennaarray attribute or are stand numbers.
        """
        
        # Validate
        if include == 'all':
            include = None
        if include is not None:
            if not isinstance(include, (list, tuple)):
                raise TypeError("Expected 'include' to by a list or tuple")
        if exclude == 'none':
            exclude = None
        if exclude is not None:
            if isinstance(exclude, int):
                exclude = [exclude,]
            if not isinstance(exclude, (list, tuple)):
                raise TypeError("Expected 'exclude' to by a list or tuple")
        else:
            exclude = []
        if not indicies:
            if self.antennaarray is None:
                raise AttributeError("No anntennaarray defined for this data set")
                
        # Convert to indicies, if needed
        stands = list(self.antennaarray.get_stands())
        if not indicies:
            if include is not None:
                include = [stands.index(i) for i in include if i in stands]
            if exclude is not None:
                exclude = [stands.index(e) for e in exclude if e in stands]
                
        # Merge include and exclude
        to_keep = list(range(len(stands)))
        if include is not None:
            to_keep = include
        for e in exclude:
            ## Don't exclude things in the include list
            if include is not None:
                if e in include:
                    continue
                    
            ## Remove excluded values
            try:
                del to_keep[to_keep.index(e)]
            except ValueError:
                pass
                
        # Find the baselines to keep based on what we were given
        selection = []
        for i,(a1,a2) in enumerate(self.baselines):
            if a1 in to_keep and a2 in to_keep:
                selection.append( i )
                
        # Create the new data set
        new_baselines = [self.baselines[b] for b in selection]
        new_data = self.copy(include_pols=False)
        new_data.baselines = new_baselines
        new_data.uvw = self.uvw[selection,:,:]*1.0
        
        for pds in self:
            new_data.append( pds.subset(selection) )
            
        # Done
        return new_data


class VisibilityData(object):
    """
    Class to hold multiple integrations of visibility data.
    """
    
    def __init__(self, data=None):
        if data is not None:
            if isinstance(data, (list, tuple)):
                ## Do we have a list or tuple to iterate over?
                for i,d in enumerate(data):
                    if not isinstance(d, VisibilityDataSet):
                        ### Is everybody in the list a VisibilityDataSet?
                        raise TypeError(f"Excepted element {i} to be a VisibilityDataSet object")
                self._data = data
            elif isinstance(data, VisibilityDataSet):
                ## Do we have a single VisibilityDataSet?
                self._data = [data,]
            else:
                raise TypeError("Expected a VisbilityDataSet object or a list/tuple of VisibilityDataSet objects")
        else:
            self._data = []
            
    def __iter__(self):
        return self._data.__iter__()
        
    def __len__(self):
        return len(self._data)
        
    def __getitem__(self, value):
        return self._data.__getitem__(value)
        
    def __setitem__(self, index, value):
        if not isinstance(value, VisibilityDataSet):
            raise TypeError("Expected type to be VisibilityDataSet")
        self._data[index] = value
        
    @property
    def jds(self):
        """
        Return a list of JDs for all VisibilityDataSets contained.
        """
        
        return [d.jd for d in self._data]
        
    @property
    def mjds(self):
        """
        Return a list of MJDs for all VisibilityDataSets contained.
        """
        
        return [d.mjd for d in self._data]
        
    @property
    def baselines(self):
        """
        Return a list baselines contained in the first VisbilityDataSet object.
        """
        
        try:
            baselines = self._data[0].baselines
        except IndexError:
            baselines = []
        return baselines
        
    @property
    def freq(self):
        """
        Return a list polarizations contained in the first VisbilityDataSet object.
        """
        
        try:
            freq = self._data[0].freq
        except IndexError:
            freq = []
        return freq
        
    @property
    def pols(self):
        """
        Return a list polarizations contained in the first VisbilityDataSet object.
        """
        
        try:
            pols = self._data[0].pols
        except IndexError:
            pols = []
        return pols
        
    @property
    def nbaseline(self):
        """
        The number of baselines contained in the first VisbilityDataSet object.
        """
        
        try:
            n = self._data[0].nbaseline
        except IndexError:
            n = 0
        return n
        
    @property
    def nchan(self):
        """
        The number of frequency channels contained in the first VisbilityDataSet object.
        """
        
        try:
            n = self._data[0].nchan
        except IndexError:
            n = 0
        return n
        
    @property
    def npol(self):
        """
        The number of polarizations contained in the first VisbilityDataSet object.
        """
        
        try:
            n = self._data[0].npol
        except IndexError:
            n = 0
        return n
        
    def copy(self, include_pols=True):
        """
        Return a copy of the object.  Be default this includes copies of all 
        of the associated PolarizationDataSet objects stored in the individual
        VisibilityDataSet sets.  Setting 'include_pols' to False will not copy 
        these objects.
        """
        
        data_copy = VisibilityData()
        for data_set in self:
            data_copy.append( data_set.copy(include_pols=include_pols) )
        return data_copy
        
    def append(self, value):
        """
        Append a new integration stored as a VisibilityDataSet to the object.
        """
        
        if not isinstance(value, VisibilityDataSet):
            raise TypeError("Expected type to be VisibilityDataSet")
        if value.jd in self.jds:
            raise ValueError(f"Data for JD {value.jd} have already been added")
        if self.nbaseline > 0 and value.nbaseline != self.nbaseline:
            raise ValueError("Data do not have the expected number of baselines")
        if self.nchan > 0 and value.nchan != self.nchan:
            raise ValueError("Data do not have the expected number of frequency channels")
        if self.npol > 0 and value.npol != self.npol:
            raise ValueError("Data do no have the expected number of polarizations")
            
        self._data.append(value)
        
    def extend(self, values):
        """
        Append a collection of new integration stored as VisibilityDataSet to 
        the objects.
        """
        
        for value in values:
            if not isinstance(value, VisibilityDataSet):
                raise TypeError("Expected type to be VisibilityDataSet")
            self._data.append(value)
            
    def pop(self, index=-1):
        """
        Pop and return the VisibilityDataSet specified by the provided index.
        """
        
        return self._data.pop(index)
        
    def sort(self):
        """
        Sort the VisibilityDataSet objects contained by the JD of the 
        integrations.
        """
        
        self._data.sort(key=lambda x: x.jd)
        for data_set in self._data:
            data_set.sort()
            
    def rephase(self, new_phase_center, ignore_errors=False):
        """
        Shift the phase center for all of the integrations stored.
        """
        for data_set in self._data:
            try:
                data_set.rephase(new_phase_center)
            except Exception as e:
                if not ignore_errors:
                    raise e
                    
    def get_uv_range(self, min_uv=0.0, max_uv=np.inf):
        """
        Return a copy of the data containing only baselines with the (u,v)
        distances allowed by the 'min_uv' and 'max_uv' cuts.
        """
        
        new_data = VisibilityData()
        for data_set in self:
            new_data.append( data_set.get_uv_range(min_uv=min_uv, max_uv=max_uv) )
        return new_data
        
    def get_antenna_subset(self, include=None, exclude=None, indicies=True):
        """
        Return a copy of the data containing baselines that meet the specified
        antenna selection criteria.  The selection is governed by the 'include', 
        'exclude', and 'indicies' keywords.  If 'include' is not None, only 
        baselines containing antennas in the list are selected.  If 'exclude' 
        is not None, only baselines not containing antennas in the list are 
        selected.  If both 'include' and 'exclude' are provided, the 'include' 
        list has priority.  'indicies' sets whether or not the selection 
        criteria are provided as indicies of the antennas stored in the 
        antennaarray attribute or are stand numbers.
        """
        
        new_data = VisibilityData()
        for data_set in self:
            new_data.append( data_set.get_antenna_subset(include=include, exclude=exclude, indicies=True) )
        return new_data
        
