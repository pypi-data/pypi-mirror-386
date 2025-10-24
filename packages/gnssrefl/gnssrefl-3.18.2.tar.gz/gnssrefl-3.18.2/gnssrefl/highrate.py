import os 
import subprocess
import sys
import time
import wget

import gnssrefl.gps as g

def cddis_highrate(station, year, month, day,stream,dec_rate):
    """
    picks up highrate RINEX files from CDDIS
    and merges them

    Parameters
    ----------
    station : str
        4 char or 9 char station name
        Rinex 2.11 for the first and rinex 3 for the latter
    year : int
        full year
    month : int
        calendar month
    day : int 
        calendar day
    stream : str
        rinex3 ID, S or R
    dec_rate : int
        decimation rate, seconds

    Returns
    -------
    rinexname : str
        name of the merged/uncompressed outputfile
    fexist : bool
        whether the Rinex file was successfully retrieved

    requires hatanaka code and gfzrnx
    """
    fexist  = False
    if len(station) == 4:
        version = 2
    else:
        version = 3
    crnxpath = g.hatanaka_version()
    gfzpath = g.gfz_version()
    alpha='abcdefghijklmnopqrstuvwxyz'
    # if doy is input
    if day == 0:
        doy=month
        d = g.doy2ymd(year,doy);
        month = d.month; day = d.day
    doy,cdoy,cyyyy,cyy = g.ymd2doy(year,month,day); 

    if not os.path.isfile(gfzpath):
        print('You need to install gfzrnx to use high-rate RINEX data in my code.')
        return

    gns = 'https://cddis.nasa.gov/archive/gnss/data/highrate/' 
    gns = gns + cyyyy + '/'+ cdoy + '/' +cyy + 'd/'
    #YYYY/DDD/YYt/HH/mmmmDDDHMM.YYt.gz

    s1=time.time()
    print('WARNING: Get yourself a cup of coffeee. Downloading 96 files takes a long time.')
    fileF = 0
    streamID  = '_' + stream + '_'
    s1 = time.time()
    for h in range(0,24):
        # subdirectory
        ch = '{:02d}'.format(h)
        print('Hour: ', ch)
        for e in ['00', '15', '30', '45']:
            if version == 2:
                oname = station + cdoy + alpha[h] + e + '.' + cyy + 'o'; 
                file_name, crnx_name, file_name2, crnx_name2, exe1, exe2 = variableArchives(station,year,doy,cyyyy,cyy,cdoy,alpha[h],e) 
            else:
                file_name = station.upper() + streamID + cyyyy + cdoy + ch + e + '_15M_01S_MO.crx.gz'
                crnx_name = file_name[:-3] 
                oname = station.upper() + streamID + cyyyy + cdoy + ch + e + '_15M_01S_MO.rnx' # do we need this?

            new_way_dir = '/gnss/data/highrate/' + cyyyy + '/' + cdoy + '/' + cyy + 'd/' + ch + '/'
            #print(new_way_dir)
            if os.path.isfile(oname):
                print('Found it:', new_way_dir,file_name)
                fileF = fileF + 1
            elif os.path.isfile(file_name):
                print('Found gzip/hatanaka file:', new_way_dir,file_name)
                subprocess.call(['gunzip',file_name])
                subprocess.call([crnxpath, crnx_name])
                subprocess.call(['rm',crnx_name])
                fileF = fileF + 1
            else:
                print('Looking for:', new_way_dir,file_name)
                try:
                    g.cddis_download_2022B(file_name,new_way_dir)
                    if (version == 3):
                        if os.path.isfile(file_name): 
                            subprocess.call(['gunzip',file_name])
                            subprocess.call([crnxpath, crnx_name])
                            subprocess.call(['rm',crnx_name])
                    if (version == 2):
                        if os.path.isfile(file_name):
                            subprocess.call([exe1,file_name])
                            subprocess.call([crnxpath, crnx_name])
                            subprocess.call(['rm',crnx_name])
                        else:
                            g.cddis_download_2022B(file_name2,new_way_dir)
                            subprocess.call([exe2,file_name2])
                            subprocess.call([crnxpath, crnx_name2])
                            subprocess.call(['rm',crnx_name2])
                except:
                    #print('Failure using cddis_download_2022B')
                    subprocess.call(['rm','-f',file_name])

                if os.path.isfile(oname):
                    fileF = fileF + 1
                    print(' >>>  and found it')
    if version == 2:
        searchpath = station + cdoy + '*.' + cyy + 'o'
        rinexname = station + cdoy + '0.' + cyy + 'o'
        tmpname = station + cdoy + '0.' + cyy + 'o.tmp'
    else:
        searchpath = station.upper() + streamID + cyyyy + cdoy + '*.rnx'
        rinexname = station.upper() + streamID + cyyyy + cdoy + '0000_01D_01S_MO.rnx'
        tmpname = rinexname + 'tmp'

    s2=time.time()
    print('That download experience took ', int(s2-s1), ' seconds.')
    print('Attempt to merge the 15 minute files using gfzrnx and move to ', rinexname)
    if (fileF > 0): # files exist
        if (dec_rate == 1):
            subprocess.call([gfzpath,'-finp', searchpath, '-fout', tmpname, '-vo',str(version),'-f','-q'])
        else:
            s3=time.time()
            crate = str(dec_rate)
            subprocess.call([gfzpath,'-finp', searchpath, '-fout', tmpname, '-vo',str(version),'-sei','out','-smp',crate,'-f','-q'])
            s4=time.time()

        cm = 'rm ' + searchpath 
        if os.path.isfile(tmpname): # clean up
            ok = 1
            subprocess.call(cm,shell=True)
            subprocess.call(['mv',tmpname,rinexname])
            print('File created ', rinexname)
            fexist = True

    s2=time.time()
    print('The whole experience took ', int(s2-s1), ' seconds.')
    return rinexname,  fexist

def variableArchives(station,year,doy,cyyyy,cyy, cdoy,chh,cmm):
    """
    creates rinex3 compliant file names and finds executables needed
    to manipulate those files

    Parameters
    ----------
    station : str
        9 ch station name
    year : int
        full year
    doy : int
        day of year
    cyyyy : str
        4 ch year
    cyy : str
        two ch year
    cdoy : str
        3 ch day of year
    chh : str
        2 ch hour
    cmm : str
        2 ch minutes

    Returns
    -------
    file_name : str 
        first filename to look for 
    crnx_name : str
        first hatanaka name 
    file_name2 : str
        second filename to look for
    crnx_name2 : str
        second hatanaka compressed name 
    exe1 : str
        uncompression executable to use for file_name
    exe2 : str
        uncompression executable to use for file_name2

    """
# Before being merged into tar files, all Unix compressed RINEX V2 data with file 
#  extension ".Z" will be switched to gzip compression with the file extension ".gz". This 
#  change in compression is in accordance with the IGS transition to gzip conversion for 
#  RINEX V2 data after December 1, 2020.
#
# 335 is december 1 2020
    T0 = 2020 + 335/365.25
    if ((year+doy/365.25) <= T0):
        file_name = station + cdoy + chh + cmm + '.' + cyy + 'd.Z'
        crnx_name = file_name[:-2]
        file_name2 = station + cdoy + chh + cmm + '.' + cyy + 'd.gz'
        crnx_name2 = file_name2[:-3]
        exe1 = 'uncompress'
        exe2 = 'gunzip'
    else:
        file_name = station + cdoy +  chh + cmm + '.' + cyy + 'd.gz'
        crnx_name = file_name[:-3]
        file_name2 = station + cdoy + chh + cmm + '.' + cyy + 'd.Z'
        crnx_name2 = file_name2[:-2]
        exe2 = 'uncompress'
        exe1 = 'gunzip'

    return file_name, crnx_name, file_name2, crnx_name2, exe1, exe2

def bkg_highrate(station, year, month, day,stream,dec_rate,bkg,**kwargs):
    """
    picks up a highrate RINEX 3 file from BKG, merges and decimates it.
    requires gfzrnx

    Parameters
    ----------
    station : str
        9 ch station name 
    year : int
        full year
    month : integer
        month or day of year if day set to 0
    day : int
        day of the month
    stream : str
        R or S
    dec_rate : int
        decimation rate in seconds
    bkg : str
        file directory at BKG (igs or euref)

    Returns
    -------
    file_name24 : str
        name of merged rinex file
    fexist : boolean
        whether file exists

    """
    timeout = kwargs.get('timeout',0)
    if (timeout > 0) :
        print('timeout parameter has been set')

    fexist  = False
    version = 3
    crnxpath = g.hatanaka_version()
    gexe = g.gfz_version()
    alpha='abcdefghijklmnopqrstuvwxyz'
    # if doy is input
    if day == 0:
        doy=month
        d = g.doy2ymd(year,doy);
        month = d.month; day = d.day
    doy,cdoy,cyyyy,cyy = g.ymd2doy(year,month,day); 

    if not os.path.isfile(crnxpath):
        g.hatanaka_warning(); return

    if not os.path.isfile(gexe):
        print('You need to install gfzrnx to use high-rate RINEX data in my code.')
        return '', fexist

#    https://igs.bkg.bund.de/root_ftp/EUREF/highrate/2022/233/a/VLIS00NLD_R_20222330000_15M_01S_MO.crx.gz
    gns = 'https://igs.bkg.bund.de/root_ftp/' + bkg + '/highrate/'
    # base directory name
    gns = gns + cyyyy + '/'+ cdoy + '/' 
    print('looking for files in: ', gns)

    s1=time.time()
    print('WARNING: Get yourself a cup of coffeee. Downloading 96 files takes a long time.')
    fileF = 0
    streamID  = '_' + stream + '_'
    s1 = time.time()
    for h in range(0,24):
        # subdirectory
        ch = '{:02d}'.format(h)
        print('Hour: ', ch)
        for e in ['00', '15', '30', '45']:
            file_name = station.upper() + streamID + cyyyy + cdoy + ch + e + '_15M_01S_MO.crx.gz'
            dirname = gns + '/' + alpha[h] + '/'
            #print('looking for', dirname + file_name)
            crnx_name = file_name[:-3] 
            oname = file_name[:-6] + 'rnx'

            if os.path.isfile(oname):
                fileF = fileF + 1
                print('You already have ', oname, ' so no need to download')
            else:
                try:
                    if timeout > 0:
                        #print('using replace_wget')
                        s = g.replace_wget(dirname+file_name, file_name,timeout=timeout)
                    else:
                        # it is not getting all the files. maybe go back to wget
                        #s = g.replace_wget(dirname+file_name, file_name)
                        #print('using wget.download')
                        wget.download(dirname+file_name,file_name)
                    if os.path.isfile(file_name):
                        subprocess.call(['gunzip',file_name]) # unzip
                        subprocess.call([crnxpath, crnx_name]) # hatanaka
                        subprocess.call(['rm',crnx_name]) # remove old file
                except:
                    okok = 1
                    print('Could not find ', file_name, ' at BKG')
                if os.path.isfile(oname):
                    #print('successful download ', oname)
                    fileF = fileF + 1
                else:
                    print('Unsuccessful download ', oname)

    searchP = station.upper() + streamID + cyyyy + cdoy + '*15M*MO.rnx'
    print('Found ', fileF,' 15 minute files')

    outfile = station.upper() + cyyyy + cdoy + '.tmp'
    crate = '{:02d}'.format(dec_rate)

    file_name24 = ''

    if (fileF > 0):
        subprocess.call([gexe,'-finp', searchP, '-fout', outfile, '-vo','3', '-smp', crate, '-f','-q'])
        file_name24 = station.upper() + streamID + cyyyy + cdoy + '0000_01D_' + crate + 'S_MO.rnx'
        subprocess.call(['mv',outfile, file_name24]) # remove old file
        fexist = True

    s2=time.time()
    print('That download and merging experience took ', int(s2-s1), ' seconds.')

    # remove 15 minute files
    cm = 'rm ' + station.upper() + streamID + cyyyy + cdoy + '*15M_01S_MO.rnx'
    if fexist:
        subprocess.call(cm,shell=True)

    return file_name24,  fexist


def esp_highrate(station, year, month, day,stream,dec_rate):
    """
    picks up a highrate RINEX 3 file from Spanish Geodeic Center, merges and decimates it.
    requires gfzrnx

    Parameters
    ----------
    inputs: string
        9 ch station name 
    year : integer
        full year
    month : integer
        month or day of year if day set to 0
    day : integer
        day of the month
    stream : str
        R or S
    dec_rate : integer
        decimation rate in seconds

    Returns
    -------
    file_name24 : str
        name of merged rinex file
    fexist : boolean
        whether file exists

    """
    fexist  = False
    version = 3
    crnxpath = g.hatanaka_version()
    gexe = g.gfz_version()
    # if doy is input
    if day == 0:
        doy=month
        d = g.doy2ymd(year,doy);
        month = d.month; day = d.day
    doy,cdoy,cyyyy,cyy = g.ymd2doy(year,month,day); 

    if not os.path.isfile(crnxpath):
        g.hatanaka_warning(); return

    if not os.path.isfile(gexe):
        print('You need to install gfzrnx to use high-rate RINEX data in my code.')
        return '', fexist

    fileid = str(year) + '{:02d}'.format(month) + '{:02d}'.format(day)

#    https://igs.bkg.bund.de/root_ftp/EUREF/highrate/2022/233/a/VLIS00NLD_R_20222330000_15M_01S_MO.crx.gz
#   https://datos-geodesia.ign.es/ERGNSS/horario_1s/20231110/00/
    gns = 'https://datos-geodesia.ign.es/ERGNSS/horario_1s/' + fileid + '/' 
    # base directory name
    print('looking for files in: ', gns)

    s1=time.time()
    print('WARNING: Downloading and merging 24 one hour files.')
    fileF = 0
    streamID  = '_' + stream + '_'
    s1 = time.time()
    for h in range(0,23):
        # subdirectory
        ch = '{:02d}'.format(h)
        print('Hour: ', ch)
        file_name = station.upper() + streamID + cyyyy + cdoy + ch + '00_01H_01S_MO.crx.gz'
        dirname = gns + '/' + ch + '/'
        #print('looking for', dirname + file_name)
        crnx_name = file_name[:-3] 
        oname = file_name[:-6] + 'rnx'
        if os.path.isfile(oname):
            fileF = fileF + 1
            print('already have ', oname)
        else:
            try:
                wget.download(dirname+file_name,file_name)
                subprocess.call(['gunzip',file_name]) # gunzip
                subprocess.call([crnxpath, crnx_name]) # hatanaka
                subprocess.call(['rm',crnx_name]) # remove old file
            except:
                okok = 1
            if os.path.isfile(oname):
                print('Successful download ', oname)
                fileF = fileF + 1
            else:
                print('Unsuccessful download ', oname)

    searchP = station.upper() + streamID + cyyyy + cdoy + '*01H*MO.rnx'
    print(searchP)
    print('Found ', fileF,' one hour files')

    outfile = station.upper() + '.tmp'
    crate = '{:02d}'.format(dec_rate)

    file_name24 = ''

    file_name24 = station.upper() + streamID + cyyyy + cdoy + '0000_01D_' + crate + 'S_MO.rnx'
    print(file_name24,outfile)
    if (fileF > 0):
        subprocess.call([gexe,'-finp', searchP, '-fout', outfile, '-vo','3', '-smp', crate, '-f','-q'])
        subprocess.call(['mv',outfile, file_name24]) # remove old file
        fexist = True

    s2=time.time()
    print('That download and merging experience took ', int(s2-s1), ' seconds.')

    # remove one hour files
    cm = 'rm ' + station.upper() + streamID + cyyyy + cdoy + '*01H_01S_MO.rnx'
    if fexist:
        subprocess.call(cm,shell=True)

    return file_name24,  fexist


def cddis_highrate_tar(station, year, month, day,stream,dec_rate):
    """
    picks up a tar'ed highrate RINEX files from CDDIS, untars it, and merges.


    added a try so it doesn't die if the file does not exist

    Parameters
    ----------
    station : str
        4 char or 9 char station name
        Rinex 2.11 for the first and rinex 3 for the latter
    year : int
        full year
    month : int
        calendar month
    day : int 
        calendar day
    stream : str
        rinex3 ID, S or R
    dec_rate : int
        decimation rate, seconds

    Returns
    -------
    rinexname : str
        name of the merged/uncompressed outputfile
    fexist : bool
        whether the Rinex file was successfully retrieved

    requires hatanaka code and gfzrnx
    """
    s1=time.time()
    fexist  = False
    version = 3 # only version 3
    crnxpath = g.hatanaka_version()
    gfzpath = g.gfz_version()
    alpha='abcdefghijklmnopqrstuvwxyz'
    # if doy is input
    if day == 0:
        doy=month
        d = g.doy2ymd(year,doy);
        month = d.month; day = d.day
    doy,cdoy,cyyyy,cyy = g.ymd2doy(year,month,day); 

    if not os.path.isfile(gfzpath):
        print('You need to install gfzrnx to use high-rate RINEX data in gnssrefl.')
        return

    gns = 'https://cddis.nasa.gov/archive/gnss/data/highrate/' 
    gns = gns + cyyyy + '/'+ cdoy + '/' +cyy + 'd/'

    streamID  = '_' + stream + '_'

    new_way_dir = 'gnss/data/highrate/' + cyyyy + '/' + cdoy + '/'
    file_name = station.upper() +  streamID + cyyyy + cdoy + '0000_01D_01S_MO.crx.tar'
    #print(new_way_dir,file_name)
    if os.path.isfile(file_name):
        print('already have the tar file - so it has probably been un tarred')
    else:
        try:
            g.cddis_download_2022B(file_name,new_way_dir)
        except:
            print('Problem downloading', file_name)

        if os.path.isfile(file_name):
            siz = os.path.getsize(file_name)
            if (siz == 0):
                print('No tar file available at CDDIS')
                subprocess.call(['rm', file_name])
                fexist = False
                rinexname = station.upper() + streamID + cyyyy + cdoy + '0000_01D_01S_MO.rnx'
                return rinexname,  fexist
            else:
                subprocess.call(['tar','-xf', file_name])
                print('File exists ; remove the tar file')
                subprocess.call(['rm', file_name])
        else:
            print('File does not exist')
            fexist = False
            rinexname = station.upper() + streamID + cyyyy + cdoy + '0000_01D_01S_MO.rnx'
            return rinexname,  fexist

    fileF = 0
    for h in range(0,24):
        # subdirectory
        ch = '{:02d}'.format(h)
        print('Hour: ', ch)
        #gnss/data/highrate/2023/199/23d/22
        new_way_dir = 'gnss/data/highrate/' + cyyyy + '/' + cdoy + '/' + cyy + 'd/' + ch + '/'
        for e in ['00', '15', '30', '45']:
            file_name = station.upper() + streamID + cyyyy + cdoy + ch + e + '_15M_01S_MO.crx.gz'
            crnx_name = file_name[:-3] 
            oname = station.upper() + streamID + cyyyy + cdoy + ch + e + '_15M_01S_MO.rnx' # do we need this?
            if os.path.isfile(new_way_dir + oname):
                #print('Found rnx file', oname)
                subprocess.call(['mv',new_way_dir + oname, 'gnss/data'])
                fileF = fileF + 1
            elif os.path.isfile(new_way_dir + file_name):
                #print('Found file:', new_way_dir,file_name)
                subprocess.call(['gunzip',new_way_dir + file_name])
                subprocess.call([crnxpath, new_way_dir + crnx_name])
                subprocess.call(['rm',new_way_dir + crnx_name])
                subprocess.call(['mv',new_way_dir + oname, 'gnss/data'])
                if os.path.isfile('gnss/data/' + oname):
                    fileF = fileF + 1
            else:
                print('did not find  file:', new_way_dir,file_name)
    # moved the files to 'gnss/data/'
    searchpath = 'gnss/data/' + station.upper() + streamID + cyyyy + cdoy + '*.rnx'
    #print(searchpath)
    rinexname = station.upper() + streamID + cyyyy + cdoy + '0000_01D_01S_MO.rnx'
    tmpname = rinexname + 'tmp'

    print('Attempt to merge the 15 minute files using gfzrnx and move to ', rinexname)
    if (fileF > 0): # files exist
        if (dec_rate == 1):
            subprocess.call([gfzpath,'-finp', searchpath, '-fout', tmpname, '-vo',str(version),'-f','-q'])
        else:
            print('Am decimating with gfzrnx')
            crate = str(dec_rate)
            subprocess.call([gfzpath,'-finp', searchpath, '-fout', tmpname, '-vo',str(version),'-sei','out','-smp',crate,'-f','-q'])

        cm = 'rm ' + searchpath 
        if os.path.isfile(tmpname): # clean up
            ok = 1
            subprocess.call(cm,shell=True)
            subprocess.call(['mv',tmpname,rinexname])
            print('File created ', rinexname)
            fexist = True

        # remove unneeded 15 minute files
        #new_way_dir = 'gnss/data/highrate/' + cyyyy + '/' + cdoy + '/' + cyy + 'd/' + ch + '/'
        new_dir =      'gnss/data/highrate/' + cyyyy + '/' + cdoy + '/' + cyy + 'd/*'
        print('remove compressed 15 minute files')
        cm = 'rm -rf ' + new_dir
        subprocess.call(cm,shell=True)

        print('remove converted 15 minute files')
        searchpath = 'gnss/data/' + station.upper() + streamID + cyyyy + cdoy + '*.rnx'
        cm = 'rm -rf ' + searchpath
        subprocess.call(cm,shell=True)

        # remove junk from CDDIS
        searchpath = station.upper() + streamID + cyyyy + cdoy + '*.md5.txt'
        cm = 'rm -rf ' + searchpath
        subprocess.call(cm,shell=True)

        searchpath = station.upper() + streamID + cyyyy + cdoy + '*.sha512.txt'
        cm = 'rm -rf ' + searchpath
        subprocess.call(cm,shell=True)

    s2=time.time()
    print('That download/merge experience took ', int(s2-s1), ' seconds.')
    return rinexname,  fexist

def bkg_highrate_tar(station, year, month, day,stream,dec_rate,bkg):
    """
    picks up a highrate RINEX 3 file from BKG, merges and decimates it.
    requires gfzrnx

    Parameters
    ----------
    station : str
        9 ch station name 
    year : int
        full year
    month : integer
        month or day of year if day set to 0
    day : int
        day of the month
    stream : str
        R or S
    dec_rate : int
        decimation rate in seconds
    bkg : str
        file directory at BKG (igs or euref)

    Returns
    -------
    file_name24 : str
        name of merged rinex file
    fexist : boolean
        whether file exists

    """
    fexist  = False
    version = 3
    crnxpath = g.hatanaka_version()
    gexe = g.gfz_version()
    alpha='abcdefghijklmnopqrstuvwxyz'
    # if doy is input
    if day == 0:
        doy=month
        d = g.doy2ymd(year,doy);
        month = d.month; day = d.day
    doy,cdoy,cyyyy,cyy = g.ymd2doy(year,month,day); 

    if not os.path.isfile(crnxpath):
        g.hatanaka_warning(); return

    if not os.path.isfile(gexe):
        print('You need to install gfzrnx to use high-rate RINEX data in my code.')
        return '', fexist

#    https://igs.bkg.bund.de/root_ftp/EUREF/highrate/2022/233/a/VLIS00NLD_R_20222330000_15M_01S_MO.crx.gz
# 	VLIS00NLD_R_20231220000_01D_01S_MO.crx.tar.gz
    gns = 'https://igs.bkg.bund.de/root_ftp/' + bkg + '/highrate/'
    streamID  = '_' + stream + '_'
    # base directory name
    dirname = gns + cyyyy + '/'+ cdoy + '/' 
    xend = '0000_01D_01S_MO'
    #print('looking for files in: ', dirname)
    file_name = station.upper() + streamID + cyyyy + cdoy + xend + '.crx'
    file_name1 = file_name + '.tar.gz'
    print(dirname + file_name1)
    if not os.path.isfile(file_name + '.tar'):
        s1=time.time()
        s = g.replace_wget(dirname+file_name1, file_name1)
        s2=time.time()
        print('That file took ', int(s2-s1), ' seconds to download')
        if os.path.isfile(file_name1):
            subprocess.call(['gunzip',file_name1]) # unzip
            subprocess.call(['tar','-xf', file_name + '.tar'])
        else:
            print('Something is wrong with tar download')
            return '', False

    fileF = 0
    for h in range(0,24):
        # subdirectory
        ch = '{:02d}'.format(h)
        print('Hour: ', ch)
        for e in ['00', '15', '30', '45']:
            crnx_name = station.upper() + streamID + cyyyy + cdoy + ch + e + '_15M_01S_MO.crx'
            oname = crnx_name[:-3] + 'rnx'
            print(oname)

            if os.path.isfile(oname):
                fileF = fileF + 1
                print('You already have ', oname, ' so no need to make it ')
                if os.path.isfile(crnx_name):
                    subprocess.call(['rm',crnx_name])  
            else:
                if os.path.isfile(crnx_name):
                    subprocess.call([crnxpath,crnx_name])  
                    if os.path.isfile(oname):
                        fileF = fileF + 1
                        subprocess.call(['rm',crnx_name])  
                else:
                    print('File does not exist', oname)

    searchP = station.upper() + streamID + cyyyy + cdoy + '*15M*MO.rnx'
    print('Found ', fileF,' 15 minute files')


    outfile = station.upper() + streamID + cyyyy + cdoy + '.tmp'
    crate = '{:02d}'.format(dec_rate)

    file_name24 = station.upper() + streamID + cyyyy + cdoy + '0000_01D_01S_MO.rnx'
    print('Final name of RINEX 3 file ', file_name24)

    if os.path.isfile(outfile):
        print('you already merged')
        fexist = True
    else:
        if (fileF > 0):
            s1= time.time()
            subprocess.call([gexe,'-finp', searchP, '-fout', outfile, '-vo','3', '-smp', crate, '-f','-q'])
            fexist = True
            s2=time.time()
            print('That merging/decimating experience took ', int(s2-s1), ' seconds.')
            print('remove 15 minute files')
            cm = 'rm ' + station.upper() + streamID + cyyyy + cdoy + '*15M_01S_MO.rnx'
            subprocess.call(cm,shell=True)

    if fexist:
        print('Now change the output name: ', file_name24)
        subprocess.call(['mv', outfile, file_name24])
        subprocess.call(['rm', file_name+'.tar'])
    else:
        file_name24 = ''

    return file_name24,  fexist


def kadaster_highrate(station, year, doy,stream,dec_rate):
    """
    picks up a highrate RINEX 3 file from Dutch archive, merges and decimates it.
    requires gfzrnx. Someone should add regular 30 second downloads - but it is not 
    gonna be me.

    Parameters
    ----------
    station : str
        9 ch station name 
    year : int
        full year
    doy : int
        day of year
    stream : str
        R or S
    dec_rate : int
        decimation rate in seconds

    Returns
    -------
    file_name24 : str
        name of merged rinex file
    fexist : boolean
        whether the new merged file exists

    """
    timeout = 0

    fexist  = False
    version = 3
    crnxpath = g.hatanaka_version()
    gexe = g.gfz_version()
    # if doy is input
    d = g.doy2ymd(year,doy);
    month = d.month; day = d.day

    doy,cdoy,cyyyy,cyy = g.ymd2doy(year,month,day); 

    if not os.path.isfile(crnxpath):
        g.hatanaka_warning(); return

    if not os.path.isfile(gexe):
        print('You need to install gfzrnx to use high-rate RINEX data in my code.')
        return '', fexist

    gns = 'https://gnss-data.kadaster.nl/data/highrate/'
    # base directory name
    gns = gns + cyyyy + '/'+ cdoy + '/' 
    print('looking for files in: ', gns)

    print('WARNING: Get yourself a cup of coffeee. Downloading 96 files takes a long time.')
    fileF = 0
    streamID  = '_' + stream + '_'
    for h in range(0,24):
        # subdirectory
        ch = '{:02d}'.format(h)
        print('Hour: ', ch)
        for e in ['00', '15', '30', '45']:
            file_name = station.upper() + streamID + cyyyy + cdoy + ch + e + '_15M_01S_MO.crx.gz'
            dirname = gns 
            crnx_name = file_name[:-3] 
            oname = file_name[:-6] + 'rnx'

            if os.path.isfile(oname):
                fileF = fileF + 1
                print('You already have ', oname, ' so no need to download and uncompress')
            else:
                print('****', dirname+file_name)
                try:
                    if not os.path.isfile(file_name):
                        wget.download(dirname+file_name,file_name)

                    if os.path.isfile(file_name):
                        print('found crx')
                        subprocess.call(['gunzip',file_name]) # unzip
                        subprocess.call([crnxpath, crnx_name]) # hatanaka
                        subprocess.call(['rm',crnx_name]) # remove old file
                except:
                    okok = 1
                    #print('Could not find ', file_name, ' at Kadaster')

                if os.path.isfile(oname):
                    print('found rnx ', oname)
                    fileF = fileF + 1
                else:
                    print('did not find rnx ', oname)

    searchP = station.upper() + streamID + cyyyy + cdoy + '*15M*MO.rnx'
    print('Found ', fileF,' 15 minute files')

    outfile = station.upper() + cyyyy + cdoy + '.tmp'
    crate = '{:02d}'.format(dec_rate)

    file_name24 = ''

    if (fileF > 0):
        print('Merging and decimating')
        subprocess.call([gexe,'-finp', searchP, '-fout', outfile, '-vo','3', '-smp', crate, '-f','-q'])
        file_name24 = station.upper() + streamID + cyyyy + cdoy + '0000_01D_' + crate + 'S_MO.rnx'
        subprocess.call(['mv',outfile, file_name24]) # remove old file
        fexist = True

    # remove 15 minute files
    cm = 'rm ' + station.upper() + streamID + cyyyy + cdoy + '*15M_01S_MO.rnx'
    if fexist:
        subprocess.call(cm,shell=True)

    return file_name24,  fexist
