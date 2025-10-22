# -*- coding: utf-8 -*-
"""
Created on Tue Oct  5 15:51:24 2021

@author: Nathan Cross
"""


from os import listdir, mkdir, path
from . cfc_func import circ_wwtest, mean_amp
from seapipe.utils.misc import bandpass_mne, laplacian_mne, notch_mne, notch_mne2
from copy import deepcopy
import shutil
from math import degrees
from numpy import (argmax, array, asarray, ceil, concatenate, histogram, interp, 
                   isnan, linspace, mean, median, nan, nanmean, ones, pi, random, 
                   reshape, save, sin, squeeze, sum, zeros) 
from pandas import DataFrame, read_csv
from safepickle import load
from pingouin import (circ_mean, circ_r, circ_rayleigh, circ_corrcc)
from scipy.stats import zscore
import sys
from tensorpac import Pac
from wonambi import Dataset
from wonambi.trans import fetch
from wonambi.attr import Annotations 
from seapipe.utils.logs import create_logger
from ..utils.load import (load_channels, load_adap_bands, rename_channels, 
                          load_sessions, read_inversion, read_manual_peaks)
from ..utils.misc import infer_polarity


def pac_method(method, surrogate, correction, list_methods=False):
    
    ''' Formats the method and corrections to be applied through Tensorpac:
        https://etiennecmb.github.io/tensorpac/auto_examples/index.html#tutorials
    '''
    # Calculate Coupling Strength (idpac)
    methods = {1: 'Mean Vector Length (MVL) [Canolty et al. 2006 (Science)]',
               2 : 'Modulation Index (MI) [Tort 2010 (J Neurophys.)]',
               3 : 'Heights Ratio (HR) [Lakatos 2005 (J Neurophys.)]',
               4 : 'ndPAC [Ozkurt 2012 (IEEE)]',
               5 : 'Phase-Locking Value (PLV) [Penny 2008 (J. Neuro. Meth.), Lachaux 1999 (HBM)]',
               6 : 'Gaussian Copula PAC (GCPAC) `Ince 2017 (HBM)`'}
    surrogates = {0 :'No surrogates', 
                  1 : 'Swap phase / amplitude across trials [Tort 2010 (J Neurophys.)]',
                  2 : 'Swap amplitude time blocks [Bahramisharif 2013 (J. Neurosci.) ]',
                  3 : 'Time lag [Canolty et al. 2006 (Science)]'}
    corrections = {0 : 'No normalization',
                   1 : 'Subtract the mean of surrogates',
                   2 : 'Divide by the mean of surrogates',
                   3 : 'Subtract then divide by the mean of surrogates',
                   4 : 'Z-score'}
    
    if list_methods:
        idpac = [methods] + [surrogates] + [corrections]
    else:
        meth = [x for x in methods if method in methods[x]][0]
        surr = [x for x in surrogates if surrogate in surrogates[x]][0]
        corr = [x for x in corrections if correction in corrections[x]][0]
        idpac = tuple((meth,surr,corr))
    
    return idpac


class octopus:

    def __init__(self, rootpath, rec_dir, xml_dir, out_dir, chan, ref_chan, 
                 grp_name, stage, rater = None, subs = 'all', 
                 sessions = 'all', reject_artf = ['Artefact', 'Arou', 'Arousal'], 
                 tracking = None):
        
        self.rootpath = rootpath
        self.rec_dir = rec_dir
        self.xml_dir = xml_dir
        self.out_dir = out_dir
        self.chan = chan
        self.ref_chan = ref_chan
        self.grp_name = grp_name
        self.stage = stage
        self.rater = rater
        self.reject = reject_artf
        
        self.subs = subs
        self.sessions = sessions
        
        if tracking == None:
            tracking = {'event_pac':{}}
        self.tracking = tracking


    def pac_it(self, cycle_idx, cat, nbins, filter_opts, 
                 epoch_opts, frequency_opts, event_opts, filetype = '.edf',
                 idpac = (2,3,4), evt_type = None, min_dur = 1, 
                 adap_bands_phase = 'Fixed', frequency_phase = (0.5,1.25), 
                 adap_bands_amplitude = 'Fixed', frequency_amplitude = (11,16), 
                 adap_bw = 4, invert = False, progress=True,
                 logger = create_logger('Phase-amplitude coupling')):

        '''
        O.C.T.O.P.U.S
        
        Oscillatory Coupling: Timed Oscillations by Phase modUlation in Sleep 
        
        This script runs Phase Amplitude Coupling analyses on sleep EEG data. 
        The method for calculating PAC is set by the parameter <idpac>. 
        For more information on the available methods, refer to the documentation of 
        tensorpac (https://etiennecmb.github.io/tensorpac/index.html) or the article
        (Combrisson et al. 2020, PLoS Comp Bio: https://doi.org/10.1371/journal.pcbi.1008302)
        
        The script does the following:
            1. Extracts the EEG signal at each event specified by <evt_type> ± a buffer
               on either side of length (in sec) specified by <buffer>.
            2. For these EEG segments, filters the signal within a given frequency range
               specified by <fpha> to obtain the phase, and again within a given frequency 
               range specified by <famp>.  
            3. FOR EACH EACH EVENT: the instantaneous amplitude of the signal filtered 
               within a given frequency range specified by <famp> will be calculated 
               via the Hilbert transform, and the amplitude will be averaged across a 
               set number of phase bins specified by <nbins>. The phase bin with the 
               maxmimum mean amplitude will be stored.
            4. ACROSS ALL EVENTS: the average phase bin with the maximum amplitude will 
               be calculated (circular mean direction).
            5. The filtered events will also be concatenated and stored in blocks of 50,
               so that the PAC strength (method pecficied by the 1st entry in <idpac>)
               can be calculated AND surrogates can be accurately generated to test for
               the significance of PAC in each participant. The generation of surrogates
               is specified by the 2nd entry in <idpac>, and the correction of PAC 
               strength is also calculated, specified by the 3rd entry in <idpac>.
            6. Other metrics are also calculated for each participant and visit, notably:
                - mean vector length (given from mean circular calculation)
                - correlation between amplitudes (averaged over all events) and the phase 
                   giving sine wave
                - Rayleigh test for non-uniformity of circular data (sig. test for 
                                                                     preferred phase)
                
               
        If laplacian = True then a Laplacian spatial filter will be applied to remove high frequency EMG 
        noise. In this scenario you will need to provide a list of channel names to include in the laplacian
        spatial filtering. 
                        ## WARNING: TEST WHAT THE LAPLACIAN FILTER DOES TO THE POWER SPECTRUM BEFORE USING
                                    THIS OPTION
        
        If adap_bands_phase = True then the phase signal will be filtered within an adapted 
        frequency range for each individual subject or recording.
        
        If adap_bands_amplitude = True then the amplitude signal will be filtered within an adapted 
        frequency range for each individual subject or recording.
        
        The output provided by this script will be an array of size:
            [#cycles x #bins] (if cycle_idx is not None)
            [1 x #nbins]      (if cycle_idx is None)
                                            - corresponding to the mean amplitude of the signal 
                                             (across all cycles or events) per phase bin.
    
        '''
        # Get method descriptions
        pac_list = pac_method(0, 0, 0, list_methods=True)
        methods = pac_list[0]
        surrogates = pac_list[1]
        corrections = pac_list[2]
    
        ### 0.a Set up logging
        tracking = self.tracking
        flag = 0
        
        
        logger.info('')
        logger.debug(rf"""Commencing phase-amplitude coupling pipeline... 
                                
                                        ___
                                     .-'   `'.
                                    /         \
                                    |         ;
                                    |         |           ___.--,
                           _.._     |0) ~ (0) |    _.---'`__.-( (_.
                     __.--'`_..'.__.\    '--. \_.-' ,.--'`     `""`
                    ( ,.--'`   ',__ /./;   ;, '.__.'`    __
                  _`) )    .---.__.' / |   |\   \__..--""  ""--.,_
                 `---'   .'.''-._.-'`_./  /\ '.  \ _.-~~~````~~~-._`-.__.'
                         | |  .' _.-' |  |  \  \  '.               `~---`
                         \ \/ .'     \  \   '. '-._)
                          \/ /        \  \    `=.__`~-.
                          / /\         `) )    / / `"".`\
                    , _.-'.'\ \        / /    ( (     / /
                    `--~`   ) )    .-'.'      '.'.  | (
                            (/`    ( (`          ) )  '-;
                            `      '-;         (-'
    
                
                Oscillatory Coupling: Timed Oscillations by Phase modUlation in Sleep
                (O.C.T.O.P.U.S)
                
                Method: {methods[idpac[0]]}
                Correction: {surrogates[idpac[1]]}
                Normalisation: {corrections[idpac[2]]}
                                  
                                                    """,)
        ### 0.b. Set up organisation of export
        if cat[0] + cat[1] == 2:
            model = 'whole_night'
            logger.debug('Analysing PAC for the whole night.')
        elif cat[0] + cat[1] == 0:
            model = 'stage*cycle'
            logger.debug('Analysing PAC per stage and cycle separately.')
        elif cat[0] == 0:
            model = 'per_cycle'
            logger.debug('Analysing PAC per cycle separately.')
        elif cat[1] == 0:
            model = 'per_stage'  
            logger.debug('Analysing PAC per stage separately.')
        if 'cycle' in model and cycle_idx == None:
            logger.info('')
            logger.critical("To run cycles separately (i.e. cat[0] = 0), cycle_idx cannot be 'None'")
            return
        
        # Log filtering options
        logger.debug(f'Using {adap_bands_phase} bands for phase frequency.')
        logger.debug(f'Using {adap_bands_amplitude} bands for amplitude frequncy.')
        if filter_opts['notch']:
            logger.debug(f"Applying notch filtering: {filter_opts['notch_freq']} Hz")
        if filter_opts['notch_harmonics']: 
            logger.debug('Applying notch harmonics filtering.')
        if filter_opts['bandpass']:
            logger.debug(f"Applying bandpass filtering: {filter_opts['highpass']} - {filter_opts['lowpass']} Hz")
        if filter_opts['laplacian']:
            logger.debug('Applying Laplacian filtering.')
        
        # Check format of evt_type
        if not evt_type == None and not isinstance(evt_type, list):
            evt_type = [evt_type]
        
        ### 1. First we check the directories
        # a. Check for output folder, if doesn't exist, create
        if path.exists(self.out_dir):
                logger.debug("Output directory: " + self.out_dir + " exists")
        else:
            mkdir(self.out_dir)
        
        # b. Check input list
        subs = self.subs
        if isinstance(subs, list):
            None
        elif subs == 'all':
                subs = listdir(self.rec_dir)
                subs = [p for p in subs if not '.' in p]
        else:
            logger.error("'subs' must either be an array of subject ids or = 'all' ")   
        
        ### 2. Begin loop through dataset
        # a. Begin loop through participants
        subs.sort()
        for i, sub in enumerate(subs):
            if not sub in self.tracking['event_pac'].keys():
                self.tracking['event_pac'][sub] = {}
            # b. Begin loop through sessions
            flag, sessions = load_sessions(sub, self.sessions, self.rec_dir, flag, 
                                     logger, verbose=2) 
            
            for v, ses in enumerate(sessions):
                logger.info('')
                logger.debug(f'Commencing {sub}, {ses}')
                if not ses in self.tracking['event_pac'][sub].keys():
                    self.tracking['event_pac'][sub][ses] = {} 

                ## c. Load recording
                rdir = self.rec_dir + '/' + sub + '/' + ses + '/eeg/'
                try:
                    edf_file = [x for x in listdir(rdir) if x.endswith(filetype)]
                    dset = Dataset(rdir + edf_file[0])
                except:
                    logger.warning(f' No input {filetype} file in {rdir}')
                    flag +=1
                    break
                
                ## d. Load annotations
                xdir = self.xml_dir + '/' + sub + '/' + ses + '/'
                try:
                    xml_file = [x for x in listdir(xdir) if x.endswith('.xml')]
                    # Copy annotations file before beginning
                    if not path.exists(self.out_dir):
                        mkdir(self.out_dir)
                    if not path.exists(self.out_dir + '/' + sub):
                        mkdir(self.out_dir + '/' + sub)
                    if not path.exists(self.out_dir + '/' + sub + '/' + ses):
                        mkdir(self.out_dir + '/' + sub + '/' + ses)
                    outpath = self.out_dir + '/' + sub + '/' + ses
                    backup_file = (f'{outpath}/{sub}_{ses}_spindle.xml')
                    if not path.exists(backup_file):
                        shutil.copy(xdir + xml_file[0], backup_file)
                    else:
                        logger.debug(f'Using annotations file from: {xdir}')
                except:
                    logger.warning(f' No input annotations file in {xdir}')
                    flag +=1
                    break
                
                # 3.a. Read annotations file
                annot = Annotations(backup_file, rater_name=self.rater)
                
                ## b. Get sleep cycles (if any)
                if cycle_idx is not None:
                    all_cycles = annot.get_cycles()
                    cycle = [all_cycles[y - 1] for y in cycle_idx if y <= len(all_cycles)]
                else:
                    cycle = None
                
                ## c. Channel setup 
                pflag = deepcopy(flag)
                flag, chanset = load_channels(sub, ses, self.chan, self.ref_chan,
                                              flag, logger)
                if flag - pflag > 0:
                    logger.warning(f'Skipping {sub}, {ses}...')
                    flag +=1
                    break
                newchans = rename_channels(sub, ses, self.chan, logger)
                
                # 4.a. Loop through channels
                for c, ch in enumerate(chanset):
                    
                    chan_full = f'{ch} ({self.grp_name})'
                    
                    # b. Rename channel for output file (if required)
                    if newchans:
                        fnamechan = newchans[ch]
                        filter_opts['renames'] = {newchans[ch]:ch}
                        filter_opts['laplacian_rename'] = True
                    else:
                        fnamechan = ch
                        filter_opts['laplacian_rename'] = False

                    if ch == '_REF':
                        filter_opts['laplacian_rename'] = False
                        if not filter_opts['oREF']:
                            try:
                                filter_opts['oREF'] = newchans[ch]
                            except:
                                logger.warning("Channel selected is '_REF' but "
                                               "no information has been given "
                                               "about what standard name applies, "
                                               "either via filter_opts['oREF'] "
                                               "or 'chanset_rename' in the tracking "
                                               "sheet (see user guide). Skipping "
                                               "channel...")
                                flag += 1
                                continue
                    else:
                        filter_opts['oREF'] = None
                        
                    # c. Set frequency bands for:
                    # Phase
                    if adap_bands_phase == 'Fixed':
                        f_pha = frequency_phase   
                    elif adap_bands_phase == 'Manual':
                        f_pha = read_manual_peaks(self.rootpath, sub, ses, ch, 
                                                 adap_bw, logger)
                    elif adap_bands_phase == 'Auto':
                        stagename = '-'.join(self.stage)
                        band_limits = f'{frequency_phase[0]}-{frequency_phase[1]}Hz'
                        f_pha = load_adap_bands(self.tracking['fooof'], sub, ses,
                                               fnamechan, stagename, band_limits, 
                                               adap_bw, logger)
                    if not f_pha:
                        logger.warning('Will use fixed frequency bands for PHASE instead.')
                        f_pha = frequency_phase
                    if not chanset[ch]:
                        logchan = ['(no re-refrencing)']
                    else:
                        logchan = chanset[ch]
                    logger.debug("Using PHASE frequency band: "
                                 f"{round(f_pha[0],2)}-{round(f_pha[1],2)} Hz "
                                 f"for {sub}, {ses}, {str(ch)}:{'-'.join(logchan)}")    
                    
                    # Amplitude
                    if adap_bands_amplitude == 'Fixed':
                        f_amp = frequency_amplitude   
                    elif adap_bands_amplitude == 'Manual':
                        f_amp = read_manual_peaks(self.rootpath, sub, ses, ch, 
                                                 adap_bw, logger)
                    elif adap_bands_amplitude == 'Auto':
                        stagename = '-'.join(self.stage)
                        band_limits = f'{frequency_amplitude[0]}-{frequency_amplitude[1]}Hz'
                        f_amp = load_adap_bands(self.tracking['fooof'], sub, ses,
                                               fnamechan, stagename, band_limits, 
                                               adap_bw, logger)
                    if not f_amp:
                        logger.warning('Will use fixed frequency bands for PHASE instead.')
                        f_amp = frequency_amplitude
                    if not chanset[ch]:
                        logchan = ['(no re-refrencing)']
                    else:
                        logchan = chanset[ch]
                    logger.debug("Using AMPLITUDE frequency band: "
                                 f"{round(f_amp[0],2)}-{round(f_amp[1],2)} Hz "
                                 f"for {sub}, {ses}, {str(ch)}:{'-'.join(logchan)}")    
                    
                    # d. Check if channel needs to be inverted for detection
                    if type(invert) == type(DataFrame()):
                        inversion = read_inversion(sub, ses, invert, ch, logger)
                        if not inversion:
                            inversion = infer_polarity(dset, annot, ch, 
                                                       chanset[ch], (1,1,1,1), 
                                                       evt_type, self.stage, 
                                                       cycle, logger)
                    elif type(invert) == bool:
                        inversion = invert
                    else:
                        logger.critical("The argument 'invert' must be set to either: "
                                        f"'True', 'False' or 'None'; but it was set as {invert}.")
                        logger.info('Check documentation for how to set up staging data:')
                        logger.info('https://seapipe.readthedocs.io/en/latest/index.html')
                        logger.info('-' * 10)
                        return
                    logger.debug(f"{'Inverting' if inversion else 'Not inverting'}"
                                 f" channel {ch} prior to detection for {sub}, {ses}")
                    
                    
                    # 5.a. Fetch data
                    logger.debug(f"Reading EEG data for {sub}, {ses}, {str(ch)}:{'-'.join(logchan)}")
                    try:
                        segments = fetch(dset, annot, cat = cat, evt_type = evt_type, 
                                     stage = self.stage, cycle = cycle, 
                                     buffer = event_opts['buffer'])
                    except Exception as error:
                        logger.error(error.args[0])
                        logger.warning(f"Skipping {sub}, {ses}, channel {str(ch)} ... ")
                        flag+=1
                        continue

                    if len(segments)==0:
                        logger.warning(f"No valid data found for {sub}, {ses}, "
                                       f"{self.stage}, Cycles:{cycle}.")
                        flag +=1
                        break
                    
                    # 5.b. Read data
                    if filter_opts['laplacian']:
                        try:
                            segments.read_data(filter_opts['lapchan'], chanset[ch]) 
                            laplace_flag = True
                        except:
                            logger.error("Channels listed in filter_opts['lapchan']: "
                                         f"{filter_opts['lapchan']} are not found "
                                         f"in recording for {sub}, {ses}.")
                            logger.warning("Laplacian filtering will NOT be run "
                                           f"for {sub}, {ses}, {ch}. Check parameters "
                                           "under: filter_opts['lapchan']")
                            segments.read_data(ch, chanset[ch])
                            laplace_flag = False
                            flag += 1
                    else:
                        segments.read_data(ch, chanset[ch])
                    
                    
                    # 6. Define PAC object
                    pac = Pac(idpac = idpac, f_pha = f_pha, f_amp = f_amp, 
                              dcomplex = filter_opts['dcomplex'], 
                              cycle = filter_opts['filtcycle'], 
                              width = filter_opts['width'], 
                              n_bins = nbins,
                              verbose='ERROR')
                    
                    # 7.a. Divide segments based on concatenation
                    nsegs=[]
                    if model == 'whole_night':
                        nsegs = [[s for s in segments]]
                        seg_label = ['whole_night']
                    elif model == 'stage*cycle':
                        seg_label = []
                        for st in self.stage:
                            for cy in cycle_idx:
                                segs = [s for s in segments if st in s['stage'] 
                                        if cy in s['cycle']]
                                nsegs.append(segs)
                                seg_label.append(f'{st}_cycle{cy}')
                    elif model == 'per_cycle':
                        seg_label = []
                        for cy in cycle_idx:
                            segs = [s for s in segments if cy in s['cycle']]
                            nsegs.append(segs)
                            seg_label.append(f'cycle{cy}')
                    elif model == 'per_stage':
                        seg_label = []
                        for st in self.stage:
                            segs = [s for s in segments if st in s['stage']]
                            nsegs.append(segs)
                            seg_label.append(f'{st}')
                    
                    # 7.b. Loop over segments and apply filtering (if required)
                    logger.info('')
                    for nsg in range(len(nsegs)):
                        seg = nsegs[nsg]
                        logger.debug(f'Analysing {seg_label[nsg]}')
                        
                        # 7.c. Create blocks
                        ampbin = zeros((len(seg), nbins))
                        ms = int(ceil(len(seg)/50))
                        longamp = zeros((ms,50),dtype=object) # initialise (blocked) amplitude series
                        longpha = zeros((ms,50),dtype=object) # initialise (blocked) phase series 
                        
                        
                        for s, sg in enumerate(seg):
                            
                            # Print out progress
                            if progress:
                                j = s/len(seg)
                                sys.stdout.write('\r')
                                sys.stdout.write("                      Progress: "
                                                 f"[{'»' * int(50 * j):{50}s}] {int(100 * j)}%")
                                sys.stdout.flush()
                            
                            out = dict(sg)
                            data = sg['data']
                            timeline = data.axis['time'][0]
                            out['start'] = timeline[0]
                            out['end'] = timeline[-1]
                            out['duration'] = len(timeline) / data.s_freq
                            if filter_opts['laplacian']:
                                selectchans = filter_opts['lapchan']
                            else:
                                selectchans = ch
                            
                            # 7.d. Notch filters
                            filtflag = 0
                            if filter_opts['notch']:
                                data.data[0], filtflag = notch_mne(data,  
                                                        channel=selectchans, 
                                                        freq=filter_opts['notch_freq'],
                                                        oREF=filter_opts['oREF'],
                                                        rename=filter_opts['laplacian_rename'],
                                                        renames=filter_opts['renames'],
                                                        montage=filter_opts['montage']
                                                        )
                                
                            if filter_opts['notch_harmonics']: 
                                data.data[0], filtflag = notch_mne2(data, 
                                                          channel=selectchans,
                                                          oREF=filter_opts['oREF'], 
                                                          rename=filter_opts['laplacian_rename'],
                                                          renames=filter_opts['renames'],
                                                          montage=filter_opts['montage']
                                                          )    
                            
                            # 7.e. Bandpass filters
                            if filter_opts['bandpass']:
                                data.data[0], filtflag = bandpass_mne(data, 
                                                            channel=selectchans, 
                                                            highpass=filter_opts['highpass'], 
                                                            lowpass=filter_opts['lowpass'], 
                                                            oREF=filter_opts['oREF'],
                                                            rename=filter_opts['laplacian_rename'],
                                                            renames=filter_opts['renames'],
                                                            montage=filter_opts['montage']
                                                            )
                            
                            # 7.f. Laplacian transform
                            if filter_opts['laplacian'] and laplace_flag:
                                data.data[0], filtflag = laplacian_mne(data, 
                                                                       channel=selectchans, 
                                                                       ref_chan=chanset[ch], 
                                                                       oREF=filter_opts['oREF'], 
                                                                       laplacian_rename=filter_opts['laplacian_rename'], 
                                                                       renames=filter_opts['renames'],
                                                                       montage=filter_opts['montage']
                                                                       )
                                data.axis['chan'][0] = asarray([x for x in chanset])
                                selectchans = ch
                                dat = data[0]
                            else:
                                dat = data()[0][0]
                            
                            # If any errors occured during filtering, break
                            if filtflag > 0:
                                break
                            
                            # 7.g. Fix polarity of recording
                            if inversion:
                                dat = dat*-1 
           
                            # 7.h. Obtain phase signal
                            pha = squeeze(pac.filter(data.s_freq, dat, ftype='phase'))
                            
                            if len(pha.shape)>2:
                                pha = squeeze(pha)
                            
                            # 7.i. obtain amplitude signal
                            amp = squeeze(pac.filter(data.s_freq, dat, ftype='amplitude'))
                            if len(amp.shape)>2:
                                amp = squeeze(amp)
                            
                            # 7.j. extract signal (minus buffer)
                            nbuff = int(event_opts['buffer'] * data.s_freq)
                            minlen = data.s_freq * min_dur
                            if len(pha) >= 2 * nbuff + minlen:
                                pha = pha[nbuff:-nbuff]
                                amp = amp[nbuff:-nbuff]                               
                                
                            # Apply phase correction for hilbert transform
                            #pha = roll(pha, int(pi/2*s_freq), axis=-1)
        
                            # 7.k. put data in blocks (for surrogate testing)
                            longpha[s//50, s%50] = pha
                            longamp[s//50, s%50] = amp
                            
                            # 7.l. put data in long format (for preferred phase)
                            ampbin[s, :] = mean_amp(pha, amp, nbins=nbins)
        
                        # 8.a. if number of events not divisible by block length,
                        #    pad incomplete final block with randomly resampled events
                        sys.stdout.write('\r')
                        sys.stdout.flush()
                        
                        rem = len(seg) % 50
                        if rem > 0:
                            pads = 50 - rem
                            for pad in range(pads):
                                ran = random.randint(0,rem)
                                longpha[-1,rem+pad] = longpha[-1,ran]
                                longamp[-1,rem+pad] = longamp[-1,ran]
                        
                        # b. Calculate Coupling Strength
                        mi = zeros((longamp.shape[0],1))
                        mi_pv = zeros((longamp.shape[0],1))
                        for row in range(longamp.shape[0]): 
                            amp = zeros((1))   
                            pha = zeros((1)) 
                            for col in range(longamp.shape[1]):
                                if row == 62 and col == 25:
                                    print(f'Col: {col}')
                                pha = concatenate((pha,longpha[row,col]))
                                amp = concatenate((amp,longamp[row,col]))
                            pha = reshape(pha,(1,1,len(pha)))
                            amp = reshape(amp,(1,1,len(amp)))
                            mi[row] = pac.fit(pha, amp, n_perm=400,random_state=5,
                                          verbose=False)[0][0]
                            mi_pv[row] = pac.infer_pvalues(p=0.95, mcp='fdr')[0][0]
    
                        ## c. Calculate preferred phase
                        ampbin = ampbin / ampbin.sum(-1, keepdims=True) # normalise amplitude
                        ampbin = ampbin.squeeze()
                        ampbin = ampbin[~isnan(ampbin[:,0]),:] # remove nan trials
                        ab = ampbin
                        
                        # d. Create bins for preferred phase
                        vecbin = zeros(nbins)
                        width = 2 * pi / nbins
                        for n in range(nbins):
                            vecbin[n] = n * width + width / 2  
                        
                        # e. Calculate mean direction (theta) & mean vector length (rad)
                        ab_pk = argmax(ab,axis=1)
                        theta = circ_mean(vecbin,histogram(ab_pk,bins=nbins, 
                                                            range=(0,nbins))[0])
                        theta_deg = degrees(theta)
                        if theta_deg < 0:
                            theta_deg += 360
                        rad = circ_r(vecbin, histogram(ab_pk,bins=nbins)[0], d=width)
                        
                        # f. Take mean across all segments/events
                        ma = nanmean(ab, axis=0)
                        
                        # g. Correlation between mean amplitudes and phase-giving sine wave
                        sine = sin(linspace(-pi, pi, nbins))
                        sine = interp(sine, (sine.min(), sine.max()), (ma.min(), ma.max()))
                        rho, pv1 = circ_corrcc(ma, sine)
    
                        # h. Rayleigh test for non-uniformity of circular data
                        ppha = vecbin[ab.argmax(axis=-1)]
                        z, pv2 = circ_rayleigh(ppha)
                        pv2 = round(pv2,5)
                        
                        # 9.a Export and save data
                        if adap_bands_phase == 'Fixed':
                            phadap = '-fixed'
                        else:
                            phadap = '-adap'
                        if adap_bands_amplitude == 'Fixed':
                            ampadap = '-fixed'
                        else:
                            ampadap = '-adap'  
                        phaname1 = round(f_pha[0],2)
                        phaname2 = round(f_pha[1],2)
                        ampname1 = round(f_amp[0],2)
                        ampname2 = round(f_amp[1],2)
                        freqs = f'pha-{phaname1}-{phaname2}Hz{phadap}_amp-{ampname1}-{ampname2}Hz{ampadap}'
                        if model == 'whole_night':
                            stagename = '-'.join(self.stage)
                            outputfile = '{}/{}_{}_{}_{}_{}_{}_pac_parameters.csv'.format(
                                            outpath,sub,ses,fnamechan,stagename,'-'.join(evt_type),freqs)
                        elif model == 'stage*cycle':    
                            outputfile = '{}/{}_{}_{}_{}_cycle{}_{}_{}_pac_parameters.csv'.format(
                                          outpath,sub,ses,fnamechan,self.stage[nsg],cycle_idx[nsg],'-'.join(evt_type),freqs)
                        elif model == 'per_stage':
                            outputfile = '{}/{}_{}_{}_{}_{}_{}_pac_parameters.csv'.format(
                                          outpath,sub,ses,fnamechan,self.stage[nsg],'-'.join(evt_type),freqs)
                        elif model == 'per_cycle':
                            stagename = '-'.join(self.stage)
                            outputfile = '{}/{}_{}_{}_{}_cycle{}_{}_{}_pac_parameters.csv'.format(
                                          outpath,sub,ses,fnamechan,stagename,cycle_idx[nsg],'-'.join(evt_type),freqs)
    
                        # b. Save cfc metrics to dataframe
                        d = DataFrame([mean(pac.pac), mean(mi), median(mi_pv), theta, 
                                        theta_deg, rad, rho, pv1, z, pv2])
                        d = d.transpose()
                        d.columns = ['mi_raw','mi_norm','pval1','pp_radians','ppdegrees','mvl',
                                      'rho','pval2','rayl','pval3']
                        d.to_csv(path_or_buf=outputfile, sep=',')
                        
                        # c. Save binned amplitudes to pickle file
                        outputfile = outputfile.split('_pac_parameters.csv')[0] + '_mean_amps'
                        save(outputfile, ab)
       
        ### 10. Check completion status and print
        if flag == 0:
            logger.debug('Phase-amplitude coupling finished without ERROR.')  
        else:
            logger.warning('Phase-amplitude coupling finished with WARNINGS. See log for details.')
        
        #self.tracking = tracking   ## TO UPDATE - FIX TRACKING
        
        return                             



                        

def generate_adap_bands(peaks,width,chan):
    
    '''
    Generates adapted bands of 2 x width from a file containing spectral peaks,
    for the specified channels
    '''
    peaks1 = read_csv(peaks, delimiter=',',index_col=0)
    peaks2 = DataFrame(nan, index=peaks1.index, columns=peaks1.columns)

    
    for c,ch in enumerate(chan):
        peaks2[ch] =  [(x - 2.0, x + 2.0) for x in peaks1[ch]] 
         

    return peaks2    



def watson_williams(in_dir, out_dir, band_pairs, chan, cycle_idx, stage, nbins,
                    test = 'within', comps = [('all','V1'), ('all','V2')]):
    
    '''
    This script conducts a Watson-Williams test between two time-points (within)
    or between 2 groups (between)
            
    '''  
    
    if len(comps)>2:
        print('')
        print('Please only provide 2 comparisons at a time in comps.')
        
    else:
        
        # Setup output directory
        if path.exists(out_dir):
                print(out_dir + " already exists")
        else:
            mkdir(out_dir)
            
        
        # Check if band_pairs is a list
        if isinstance(band_pairs,str):
            band_pairs = [band_pairs]
            
        # Create output file
        dset = zeros((len(chan),len(band_pairs)*2))

        # Set vecbin
        width = 2 * pi / nbins
        vecbin = zeros(nbins)
        for i in range(nbins):
            vecbin[i] = i * width + width / 2
        
        # Loop through channels
        for k, ch in enumerate(chan):
            for b,bp in enumerate(band_pairs):
                
                print('')
                print(f'CHANNEL: {ch}')
                print(f'BAND PAIR: {bp}')
                print('')
                
                # Create output filename    
                stagename = ''.join(stage)
                partstr = ['_'.join(x) for x in comps]
                comparisons = [partstr[0], partstr[1]]
                bands = '_'.join(band_pairs)
                outname = '_vs_'.join([x for x in comparisons])
                filename = f'{stagename}_{bands}_{outname}'
                
                data_m = []
                # Loop through comparisons
                for c,(part,visit) in enumerate(comps):
                
                    # Set list of input participants & visits
                    if isinstance(part, list):
                        None
                    elif part == 'all':
                            part = listdir(in_dir)
                            part = [ p for p in part if not '.' in p]
                    else:
                        print('')
                        print("ERROR: comps must either contain a list of subject ids or = 'all' ")
                        print('')
                    part.sort()
                    for i, p in enumerate(part):
                        if visit == 'all':
                            visit = listdir(in_dir + '/' + p)
                            visit = [x for x in visit if not'.' in x]  
                    if isinstance(visit,str):
                        visit = [visit]
                    visit.sort()    
                    # Define output object   
                    datab = zeros((len(part),len(visit),nbins))
                    
                    # Loop through participants & visits
                    for i, p in enumerate(part):
                        for j, vis in enumerate(visit): 
                            if not path.exists(in_dir + '/' + p + '/' + vis + '/'):
                                print(f'WARNING: input folder missing for Subject {p}, visit {vis}, skipping..')
                                continue
                            else:
                                p_files = [s for s in listdir(in_dir + '/' + p + '/' + vis) if 
                                           bp in s if '.p' in s]
                                p_files = [s for s in p_files if stagename in s] 
                                p_files = [s for s in p_files if ch in s]
                                
                                # Open files containing mean amplitudes (if existing)
                                if len(p_files) == 0:
                                    print(f'WARNING: mean amplitudes file does not exist for Subject {p}, visit {vis}, stage {stagename}, channel {ch} - check this. Skipping..')
                                elif len(p_files) >1:
                                    print(f'WARNING: multiple mean amplitudes files exist for Subject {p}, visit {vis}, stage {stagename}, channel {ch} - check this. Skipping..')
                                else:
                                    print(f'Extracting... Subject {p}, visit {vis}')
                                    ab_file = in_dir + '/' + p + '/' + vis + '/' + p_files[0]
                                    with open(ab_file, 'rb') as f:
                                        ab = load(f)
                                    
                                    # Calculate mean amplitudes across night per subject
                                    ab = nanmean(ab, axis=0)
    
                                    # Caculate z-score for binned data
                                    datab[i,j,:] = zscore(ab)
                                 
                                    
                    # Remove nans from output and take average           
                    databz = array([[[x if not isnan(x) else 0 for x in dim1] 
                                     for dim1 in dim2] for dim2 in datab])
                    data = mean(databz,axis=1)
                    data_m.append(array([circ_mean(vecbin, data[x, :] * 1000) for x in 
                                  range(data.shape[0])]))
                    
                # Create array of data
    
                if test == 'within':
                    if len(data_m[0]) == len(data_m[1]):
                        # Run permutation testing
                        print('')
                        print("Running 10,000 permutations... ")
                        F = zeros((10000))
                        P = zeros((10000))
                        warnings = True
                        for pm in range(0,10000):
                            perm = random.choice(a=[False, True], size=(len(data_m[0])))
                            da = deepcopy(data_m[0])
                            db = deepcopy(data_m[1])
                            if pm>0:
                                da[perm] = data_m[1][perm]
                                db[perm] = data_m[0][perm]
                                warnings = False
                                
                            F[pm], P[pm] = circ_wwtest(da, db, ones(da.shape), 
                                                       ones(db.shape), warnings)
                        dset[k,b*2] = F[0]
                        dset[k,(b*2)+1] = sum(F>F[0])/len(F)
                    else:
                        print("For within-subjects comparisons, the number of subjects in each condition need to match... ")
                elif test == 'between':
                    da = deepcopy(data_m[0])
                    db = deepcopy(data_m[1])
                    F, P = circ_wwtest(da, db, ones(da.shape), ones(db.shape))
                    dset[k,b*2] = F
                    dset[k,(b*2)+1] = P
                else:
                    print("WARNING: test must either be 'between' or 'within' ... ")
            
            
        # Save output to file
        columns = [x+'_'+y for x in band_pairs for y in ['F','p']]
        df = DataFrame(dset, index=chan, columns=columns)
        df.to_csv(r"{out_dir}/watson_williams_{filename}.csv".format(out_dir=out_dir,
                                                           filename=filename))
            
            
            
        print('')
        print("Completed... ")

            

            

