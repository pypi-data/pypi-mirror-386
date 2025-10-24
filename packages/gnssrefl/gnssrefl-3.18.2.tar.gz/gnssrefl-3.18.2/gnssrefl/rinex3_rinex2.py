# -*- coding: utf-8 -*-
"""
Translates rinex3 to rinex2. relies on gfzrnx
"""
import argparse
import os
import subprocess
import sys

import gnssrefl.gps as g
import gnssrefl.rinex2snr as r

def main():
    """
    Converts a RINEX 3 file into a RINEX 2.11 file. Uses gfzrnx.

    It will delete your RINEX 3 file!

    This code has been updated so that your input filename can include a path

    Parameters
    ----------
    rinex3 : str
        filename for RINEX 3 file
    rinex2 : str, optional
        filename for RINEX 2.11 file
    dec : integer, optional
        decimation value (seconds)
    overwrite : bool, optional
        whether to overwrite existing RINEX 2 file. Default is False (F)
    gpsonly : bool, optional
        whether to remove everything except GPS. Default is False (F)
    quiet : bool, optional
        whether to print gfzrnx output to the screen. Set to F to see it 

    """

    parser = argparse.ArgumentParser()
    parser.add_argument("rinex3", help="rinex3 filename", type=str)
    parser.add_argument("-rinex2", help="rinex2 filename", type=str,default=None)
    parser.add_argument("-dec", help="decimation value (seconds)", type=int,default=None)
    parser.add_argument("-overwrite", help="boolean, T to overwrite existing rinex2 file", type=str,default=None)
    parser.add_argument("-gpsonly", help="remove everything except GPS (T input allowed)", type=str,default=None)
    parser.add_argument("-quiet", help="boolean, F to write gfzrnx output to the screen", type=str,default=None)

    args = parser.parse_args()
    rinex3 = args.rinex3
    rinex3_basename = os.path.basename(rinex3)  # Extract just the filename

    gexe = g.gfz_version()

    # should use utils but don't have the time
    gpsonly = False
    if (args.gpsonly == 'True') or (args.gpsonly == 'T'):
        gpsonly = True

    station = rinex3_basename[0:4].lower()
    cyyyy = rinex3_basename[12:16]
    cdoy = rinex3_basename[16:19]
    year = int(cyyyy)
    doy = int(cdoy)

    quiet = True
    if args.quiet is 'F':
        quiet = False
    print('is it quiet ' , quiet)

    if args.rinex2 is None:
        rinex2 = station + cdoy + '0.' + cyyyy[2:4] + 'o'
    else:
        rinex2 = args.rinex2

    print('RINEX 2 filename will be ', rinex2)
    if  os.path.exists(rinex2) and args.overwrite == 'T':
        subprocess.call(['rm', rinex2])

    if args.dec is None:
        dec = 1
    else:
        dec=args.dec

    if not os.path.exists(gexe):
        print('Required gfzrnx executable does not exist. Exiting.')
        sys.exit()


    #print(station,year,doy)
    log,nada,exedir,genlog = r.set_rinex2snr_logs(station,year,doy)
    print('Log (mostly) written to ', genlog)

    if os.path.isfile(rinex3):
        log.write('WARNING: your RINEX 3 file will be deleted.')
        log.write('Your RINEX 3 input file does exist: {0:s} \n'.format(rinex3))
        if (rinex3[-2::] == 'gz'):
            subprocess.call(['gunzip', rinex3])
            rinex3 = rinex3[0:-3]
        print(quiet)
        g.new_rinex3_rinex2(rinex3,rinex2,dec,gpsonly,log,quiet=quiet)
        log.close()
    else:
        log.write('ERROR: your input file does not exist: {0:s} \n'.format(rinex3))
        log.close()
        print('ERROR: your input file does not exist: {0:s} \n'.format(rinex3))
        sys.exit()



if __name__ == "__main__":
    main()
