"""
Unit test for the lsl.writer.sdfits module.
"""

import os
import time
import unittest
import numpy as np
import tempfile
import shutil
from astropy.io import fits as astrofits

from lsl.astro import unix_to_taimjd
from lsl.common import stations as lwa_common
from lsl.writer import sdfits


__version__  = "0.2"
__author__    = "Jayce Dowell"


class sdfits_tests(unittest.TestCase):
    """A unittest.TestCase collection of unit tests for the lsl.writer.sdfits
    module."""
    
    def setUp(self):
        """Turn off all numpy warnings and create the temporary file directory."""

        np.seterr(all='ignore')
        self.testPath = tempfile.mkdtemp(prefix='test-sdfits-', suffix='.tmp')

    def _init_data(self):
        """Private function to generate a random set of data for writing a SDFITS 
        file.  The data is returned as a dictionary with keys:
        * freq - frequency array in Hz
        * site - lwa.common.stations object
        * stands - array of stand numbers
        * spec - array of spectrometer data stand x freq format
        """

        # Frequency range
        freq = np.arange(0,512)*20e6/512 + 40e6
        # Site and stands
        site = lwa_common.lwa1
        antennas = site.antennas[0:40:2]
        
        # Set data
        specData = np.random.rand(len(antennas), len(freq))
        specData = specData.astype(np.float32)

        return {'freq': freq, 'site': site, 'antennas': antennas, 'spec': specData}
    
    def test_write_tables(self):
        """Test if the SDFITS writer writes all of the tables."""

        testTime = time.time()
        testFile = os.path.join(self.testPath, 'sd-test-W.fits')
        
        # Get some data
        data = self._init_data()
        
        # Start the file
        fits = sdfits.Sd(testFile, ref_time=testTime)
        fits.set_stokes(['xx'])
        fits.set_frequency(data['freq'])
        fits.add_comment('This is a comment')
        fits.add_history('This is history')
        fits.add_data_set(unix_to_taimjd(testTime), 6.0, data['antennas'], data['spec'])
        fits.write()
        fits.close()

        # Open the file and examine
        hdulist = astrofits.open(testFile)
        # Check that all of the extensions are there
        extNames = [hdu.name for hdu in hdulist]
        for ext in ['SINGLE DISH',]:
            self.assertTrue(ext in extNames)
        # Check the comments and history
        self.assertTrue('This is a comment' in str(hdulist[0].header['COMMENT']).split('\n'))
        self.assertTrue('This is history' in str(hdulist[0].header['HISTORY']).split('\n'))
        
        hdulist.close()
    
    def test_data(self):
        """Test the data table in the SINGLE DISH extension"""

        testTime = time.time()
        testFile = os.path.join(self.testPath, 'sd-test-data.fits')
        
        # Get some data
        data = self._init_data()
        
        # Start the file
        fits = sdfits.Sd(testFile, ref_time=testTime)
        fits.set_stokes(['xx'])
        fits.set_frequency(data['freq'])
        fits.add_data_set(unix_to_taimjd(testTime), 6.0, data['antennas'], data['spec'])
        fits.write()
        fits.close()

        # Open the file and examine
        hdulist = astrofits.open(testFile)
        sd = hdulist['SINGLE DISH'].data

        # Correct number of elements
        self.assertEqual(len(sd.field('DATA')), len(data['antennas']))
        
        # Correct values
        for beam, spec in zip(sd.field('BEAM'), sd.field('DATA')):
            # Find out which visibility set in the random data corresponds to the 
            # current visibility
            i = 0
            for ant in data['antennas']:
                if ant.id == beam:
                    break
                else:
                    i = i + 1
            
            # Extract the data and run the comparison
            np.testing.assert_allclose(spec[0,0,0,:], data['spec'][i,:])
            i = i + 1
        
        hdulist.close()
    
    def tearDown(self):
        """Remove the test path directory and its contents"""

        shutil.rmtree(self.testPath, ignore_errors=True)


class  sdfits_test_suite(unittest.TestSuite):
    """A unittest.TestSuite class which contains all of the lsl.sim.vis units 
    tests."""
    
    def __init__(self):
        unittest.TestSuite.__init__(self)

        loader = unittest.TestLoader()
        self.addTests(loader.loadTestsFromTestCase(sdfits_tests)) 


if __name__ == '__main__':
    unittest.main()
