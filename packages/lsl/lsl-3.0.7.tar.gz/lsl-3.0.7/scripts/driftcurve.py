#! /usr/bin/env python3

"""
Predict driftcurve for a given site using a given antenna model.
"""

import os
import sys
import math
import numpy as np
import pylab
import argparse

from scipy.interpolate import interp1d

from lsl import skymap, astro
from lsl.common import stations
from lsl.sim.beam import get_avaliable_models, beam_response
from lsl.misc import parser as aph

from lsl.misc import telemetry
telemetry.track_script()


__version__  = "0.1"
__author__    = "D.L.Wood"
__maintainer__ = "Jayce Dowell"


def main(args):
    # Validate
    if args.pol not in ('EW', 'NS'):
        raise ValueError("Invalid polarization: %s" % args.pol)
        
    # Get the site information
    if args.lwasv:
        nam = 'lwasv'
        sta = stations.lwasv
    elif args.lwana:
        nam = 'lwana'
        sta = stations.lwana
    elif args.ovrolwa:
        nam = 'ovro'
        sta = stations.lwa1
        sta.lat, sta.lon, sta.elev = ('37.23977727', '-118.2816667', 1183.48)
    else:
        nam = 'lwa1'
        sta = stations.lwa1
        
    # Read in the skymap (GSM or LF map @ 74 MHz)
    if not args.lfsm:
        smap = skymap.SkyMapGSM(freq_MHz=args.frequency/1e6)
        smap_name = 'GSM'
    else:
        smap = skymap.SkyMapLFSM(freq_MHz=args.frequency/1e6)
        smap_name = 'LFSM'
    if args.verbose:
        print(f"Read in {smap_name} map at {args.frequency/1e6:.2f} MHz of {len(smap.ra)} pixels; min={smap._power.min()}, max={smap._power.max()}")
        
    # Dipole beam pattern function
    model = 'llfss' if args.empirical else 'empirical'
    pol = 'XX' if args.pol == 'EW' else 'YY'
    bfunc = lambda x, y: beam_response(model, pol, x, y, frequency=args.frequency, degrees=True)
    
    if args.do_plot:
        az = np.zeros((90,360))
        alt = np.zeros((90,360))
        for i in range(360):
            az[:,i] = i
        for i in range(90):
            alt[i,:] = i
        pylab.figure(1)
        pylab.title(f"Antenna Response: {args.pol} pol. @ {args.frequency/1e6:.2f} MHz")
        pylab.imshow(bfunc(az, alt), extent=(0,359, 0,89), origin='lower')
        pylab.xlabel("Azimuth [deg]")
        pylab.ylabel("Altitude [deg]")
        pylab.grid(1)
        pylab.draw()
    
    # Calculate times in both site LST and UTC
    t0 = astro.get_julian_from_sys()
    lst = astro.get_local_sidereal_time(sta.long*180.0/math.pi, t0) / 24.0
    t0 -= lst*(23.933/24.0) # Compensate for shorter sidereal days
    times = np.arange(0.0, 1.0, args.time_step/1440.0) + t0
    
    lstList = []
    powListAnt = [] 
    
    for t in times:
        # Project skymap to site location and observation time
        pmap = skymap.ProjectedSkyMap(smap, sta.lat*180.0/math.pi, sta.long*180.0/math.pi, t)
        lst = astro.get_local_sidereal_time(sta.long*180.0/math.pi, t)
        lstList.append(lst)
        
        # Convolution of user antenna pattern with visible skymap
        gain = bfunc(pmap.visibleAz, pmap.visibleAlt)
        powerAnt = (pmap.visiblePower * gain).sum() / gain.sum()
        powListAnt.append(powerAnt)

        if args.verbose:
            lstH = int(lst)
            lstM = int((lst - lstH)*60.0)
            lstS = ((lst - lstH)*60.0 - lstM)*60.0
            sys.stdout.write(f"LST: {lstH:02d}:{lstM:02d}:{lstS:04.1f}, Power_ant: {powerAnt:.1f} K\r")
            sys.stdout.flush()
    sys.stdout.write("\n")
            
    # plot results
    if args.do_plot:
        pylab.figure(2)
        pylab.title(f"Driftcurve: {args.pol} pol. @ {args.frequency/1e6:.2f} MHz - {nam.upper()}")
        pylab.plot(lstList, powListAnt, "ro", label="Antenna Pattern")
        pylab.xlabel("LST [hours]")
        pylab.ylabel("Temp. [K]")
        pylab.grid(2)
        pylab.draw()
        pylab.show()
    
    outputFile = f"driftcurve_{nam}_{args.pol}_{args.frequency/1e6:.2f}.txt"
    print(f"Writing driftcurve to file '{outputFile}'")
    with open(outputFile, "w") as mf:
        for lst,pow in zip(lstList, powListAnt):
            mf.write(f"{lst}  {pow}\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='simulate a drift curve for a dipole at LWA1 observing at a given frequency in MHz', 
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
    parser.add_argument('-f', '--frequency', type=aph.frequency, default='74.0', 
                    help='frequency of the simulation in MHz')
    sgroup = parser.add_mutually_exclusive_group(required=False)
    sgroup.add_argument('-s', '--lwasv', action='store_true',
                        help='calculate for LWA-SV instead of LWA1')
    sgroup.add_argument('-n', '--lwana', action='store_true',
                        help='calculate for LWA-NA instead of LWA1')
    sgroup.add_argument('-o', '--ovrolwa', action='store_true',
                        help='calculate for OVRO-LWA instead of LWA1')
    parser.add_argument('-p', '--pol', type=str, default='EW', 
                        help='polarization of the simulations (NS or EW)')
    parser.add_argument('-e', '--empirical', action='store_true', 
                    help='enable empirical corrections to the dipole model (valid from 35 to 80 MHz)')
    parser.add_argument('-l', '--lfsm', action='store_true', 
                        help='use LFSM instead of GSM')
    parser.add_argument('-t', '--time-step', type=float, default=10.0, 
                        help='time step of the simulation in minutes')
    parser.add_argument('-x', '--do-plot', action='store_true', 
                        help='plot the driftcurve data')
    parser.add_argument('-v', '--verbose', action='store_true', 
                        help='run %(prog)s in verbose mode')
    args = parser.parse_args()
    main(args)
