#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 19 16:32:10 2024

@author: ncro8394
"""

import re
from itertools import product
from numpy import (asarray, full, nan, ndarray, sum)
from os import listdir, mkdir, path, walk
from pandas import concat, DataFrame, read_csv
from pathlib import Path
from wonambi import Dataset
from wonambi.attr import Annotations
from wonambi.trans import (fetch, get_times)
from wonambi.trans.analyze import event_params, export_event_params
from ..utils.logs import create_logger, create_logger_empty
from ..utils.load import (load_channels, load_adap_bands, rename_channels, 
                          read_manual_peaks, read_tracking_sheet,
                          reverse_chan_lookup)

class FISH:
    
    '''
        Functions for Information Saving and Hypothesis testing (FISH)
    
        
    '''
    
    
    def __init__(self, rootpath, rec_dir, xml_dir, out_dir, chan, ref_chan, 
                 grp_name, stage, rater = None,
                 subs = 'all', sessions = 'all', tracking = None):
        
        self.rootpath = rootpath
        self.rec_dir = rec_dir
        self.xml_dir = xml_dir
        self.out_dir = out_dir
        self.chan = chan
        self.ref_chan = ref_chan
        self.grp_name = grp_name
        self.stage = stage
        self.rater = rater
        
        self.subs = subs
        self.sessions = sessions
        if tracking == None:
            tracking = {}
        self.tracking = tracking

    def line(self, keyword = None, evt_name = None, cat = (0,0,0,0), 
             segs = None,  cycle_idx = None, frequency = None, 
             adap_bands = 'Fixed', peaks = None,  adap_bw = 4, 
             param_keys = 'all', epoch_dur = 30, Ngo = False, 
             filetype = '.edf',
             logger = create_logger('Export params')):
                           
            '''
                Listing Individual aNnotated Events (LINE)
            
                Extracts event parameters per participant and session.
                
                segs: to extract parameters between certain markers, 
                      these need to be defined in the Annotations file first. 
                      Format should be a list of tuples, with both tags named
                        e.g. [('N2_ON','N2_OFF'), ('N3_ON','N3_OFF')]
                        
                concat = (cycles, stages, discontinuous, evttypes) 
            '''
            ### 1.b. Format event names
            if evt_name == None:
                evt_name = ['spindle']
            if type(evt_name) is not list:
                evt_name = [evt_name]
            
            ### 0.a Set up logging
            flag = 0
            
            logger.info('')
            logger.debug(r""" Exporting event parameters...
                         
                       
                                        /^. 
                                       /   .
                                    o /     .
                                   (√        .
                                   |          .
                        _________/\____"      .
                       |  |     |    |         .
                       |  |     |    |          .  
                       |  |     |    |           .
                       !^~!~^~^~!~^~^!~^~^~^~^~^~^.~^~^~^~^~^~^~^~^~^~^~^~^~ 
                                                  .
                                                  .          œ«   
                                                  ¿   
                               ∞«                    <>≤   
                                                             »<> 
           
                             /\____^__                  ~~~•
                             | __   v  \_____
                             \/  \_____/
                             
                                                 ___:____     |"\/"|
                                               ,'        `.    \  /
                                              |  O   v    \___/  |
                                              \_________________/   
               
                Listing Individual aNnotated Events 
                (L.I.N.E) 
                                                        """,)
            
            ### 1.a. Set up organisation of export
            if cat[0] + cat[1] == 2:
                model = 'whole_night'
                logger.debug('Exporting parameters for the whole night.')
            elif cat[0] + cat[1] == 0:
                model = 'stage*cycle'
                logger.debug('Exporting parameters per stage and cycle separately.')
            elif cat[0] == 0:
                model = 'per_cycle'
                logger.debug('Exporting parameters per cycle separately.')
            elif cat[1] == 0:
                model = 'per_stage'  
                logger.debug('Exporting parameters per stage separately.')
            if 'cycle' in model and cycle_idx == None:
                logger.info('')
                logger.critical("To export cycles separately (i.e. cat[0] = 0), cycle_idx cannot be 'None'")
                return
            cat = tuple((cat[0],cat[1],0,0)) # force non-concatenation of discontinuous & events
            
    
            ### 1.c. Set default paramaters to export (if not pre-set)
            if param_keys is None:
                params = {k: 0 for k in ['dur', 'minamp', 'maxamp', 'ptp', 'rms',
                                          'power', 'peakpf', 'energy', 'peakef']}
            elif param_keys == 'all':
                params = {k: 1 for k in ['dur', 'minamp', 'maxamp', 'ptp', 'rms',
                                          'power', 'peakpf', 'energy', 'peakef']}
            if Ngo == False:
                Ngo = {'run' : False}
            
            # 2.a Get subjects
            subs = self.subs
            if isinstance(subs, list):
                None
            elif subs == 'all':
                    subs = next(walk(self.xml_dir))[1]
            else:
                logger.info('')
                logger.critical("'subs' must either be an array of Participant IDs or = 'all' ")
                return
            subs.sort()

            # 3.a. Loop over event types
            logger.info('') 
            for e, event in enumerate(evt_name):  
                # 3.b. Loop over subjects
                for i, sub in enumerate(subs):
                    
                    # 2.b. Get sessions
                    sessions = self.sessions
                    if sessions == 'all':
                        try:
                            sessions = next(walk(f'{self.xml_dir}/{sub}'))[1]  # Get list of session directories
                        except StopIteration:
                            logger.warning(f'No visits found in {self.xml_dir}{sub}. Skipping..')
                            continue
                    elif not isinstance(sessions, list):
                        logger.info('')
                        logger.critical("'sessions' must either be a list of Session IDs or = 'all'")
                        return
                    
                    if not sessions:
                        logger.warning(f'No visits found in {self.xml_dir}{sub}. Skipping..')
                        continue
                    
                    # 3.c. Loop over sessions
                    for v, ses in enumerate(sessions):  
                        logger.debug(f'Extracting {event} parameters for {sub}, {ses}..') 
                        
                        # 3.d. Get recording
                        rdir = f'{self.rec_dir}/{sub}/{ses}/eeg/'
                        edf_file = [x for x in listdir(rdir) if x.endswith(filetype)
                                    if not x.startswith('.')]
                        
                        # 3.d. Get proper annotations file
                        if keyword is not None:
                            xml_file = [x for x in listdir(self.xml_dir + '/' + sub + '/' + ses) 
                                    if x.endswith('.xml') if not x.startswith('.') if keyword in x] 
                        else:
                            xml_file = [x for x in listdir(self.xml_dir +  '/' + sub + '/' + ses ) 
                                    if x.endswith('.xml') if not x.startswith('.')]    
                        if len(xml_file) == 0:                
                            logger.warning(f'{event} has not been detected for {sub}, {ses} - skipping..')
                            flag+=1
                            continue
                        elif len(xml_file) > 1:
                            logger.warning(f"More than 1 annotations file found for {sub}, visit {ses} - to select the correct file you must define the variable 'keyword' - skipping..")
                            flag+=1
                            continue
                        else:
                            xml_file_path = f'{self.xml_dir}/{sub}/{ses}/{xml_file[0]}'
                            
                            # 4.a. Open dataset
                            dataset = Dataset(rdir + edf_file[0])
                    
                            # 4.b. Import Annotations file
                            annot = Annotations(xml_file_path, rater_name=self.rater)
                        
                            # 4.c. Get sleep cycles (if any)
                            if cycle_idx is not None:
                                all_cycles = annot.get_cycles()
                                if all_cycles:
                                    cycle = [all_cycles[y - 1] for y in cycle_idx if y <= len(all_cycles)]
                                else:
                                    logger.warning(f'Cycles have not been marked for {sub}, {ses} - exporting all cycles..')
                                    flag+=1
                                    cycle = None
                            else:
                                cycle = None
                            
                            # 4.d. Channel setup
                            flag, chanset = load_channels(sub, ses, self.chan, 
                                                          self.ref_chan, flag, logger)
                            if not chanset:
                                continue
                            
                            newchans = rename_channels(sub, ses, self.chan, logger)
                            
                            # 5. Run through channels
                            for ch, channel in enumerate(chanset):
                                
                                # 5.a. Define full channel name (in annotations file)
                                if Ngo['run'] == False:
                                    if self.grp_name is not None:
                                        chan_ful = [f'{channel} ({self.grp_name})']
                                    else:
                                        chan_ful = [channel]
                                        logger.debug(f'channel is {chan_ful}')
                                else:
                                    chan_ful = Ngo['chan']
                                if type(chan_ful)!=str and len(chan_ful)>1:
                                    chan_ful = chan_ful[0]
                                    
                                # 5.b Rename channel for output file (if required)
                                if newchans:
                                    fnamechan = newchans[channel]
                                else:
                                    fnamechan = channel
                                
                                # 5.c. Define frequency bands
                                if adap_bands == 'Fixed':
                                    logger.debug("Adapted bands has been set as 'Fixed'.")
                                    freq = frequency
                                    if frequency == None:
                                        logger.critical("If setting adap_bands = 'Fixed' a frequency range must also be set.")
                                        logger.info('                      Check documentation for how to extract event parameters:')
                                        logger.info('                      https://seapipe.readthedocs.io/en/latest/index.html')
                                        return
                                elif adap_bands == 'Manual':
                                    logger.debug("Adapted bands has been set as 'Manual'. Will search for peaks within the tracking sheet")
                                    freq = read_manual_peaks(self.rootpath, sub, ses, channel, 
                                                             adap_bw, logger)
                                    if not freq:
                                        flag += 1
                                elif adap_bands == 'Auto':
                                    stagename = '-'.join(self.stage)
                                    if frequency == None:
                                        logger.critical("If setting adap_bands = 'Auto' a frequency range must also be set.")
                                        logger.info('                      Check documentation for how to extract event parameters:')
                                        logger.info('                      https://seapipe.readthedocs.io/en/latest/index.html')
                                        return
                                    else:
                                        band_limits = f'{frequency[0]}-{frequency[1]}Hz'
                                        logger.debug(f"Adapted bands has been set as 'Auto'. Will search for peaks within the limits: {band_limits}")
                                        freq = load_adap_bands(self.tracking['fooof'], sub, ses,
                                                               fnamechan, stagename, band_limits, 
                                                               adap_bw, logger)
                                
                                # Final freq check (and set defaults if none)
                                if freq == None and self.out_dir.split('/')[-1] == 'spindle':
                                    freq = (11,16)
                                elif freq == None and self.out_dir.split('/')[-1] == 'slowwave':
                                    freq = (0.5, 1.25)
                                elif freq == None:
                                    freq = (0, 35)
                                
                                band_limits = f'{round(freq[0],2)}-{round(freq[1],2)}Hz'
                                logger.debug(f"Using band limits: {band_limits}")
                                
                                # 5.d. Select and read data
                                logger.info('')
                                logger.debug(f"Reading data for {sub}, {ses}, channel {str(channel)}:{'-'.join(chanset[channel])}")
                                
                                # 5.e. Events from annotations file
                                evts = annot.get_events(name=event, time=None,
                                                        chan=f'{channel} ({self.grp_name})', 
                                                        stage=self.stage)
                                
                                if len(evts) == 0:
                                    logger.info('')
                                    logger.warning(f"Events: '{event}' haven't been detected for {sub}, {ses} on channel {channel}, skipping...")
                                
                                ### WHOLE NIGHT ###
                                elif model == 'whole_night':
                                    try:
                                        segments = fetch(dataset, annot, cat=cat, 
                                                         evt_type=[event], 
                                                         cycle=cycle, chan_full=chan_ful, 
                                                         reject_epoch=True, 
                                                         reject_artf = ['Artefact', 'Arou', 'Arousal'],)
                                        segments.read_data([channel], chanset[channel], 
                                                           grp_name=self.grp_name)
                                    except Exception as e:
                                        logger.error(e)
                                        logger.warning(f'Error reading data for {sub}, {ses}, CHANNEL {channel}.')
                                        flag +=1
                                        continue
                                    if len(segments) < 1:
                                        logger.warning(f'No valid data found for {sub}, {ses}, CHANNEL {channel}.')
                                        flag +=1
                                        continue
                                    else:
                                        # Get times
                                        poi = get_times(annot, stage=self.stage, 
                                                        cycle=cycle, 
                                                        chan=[channel], 
                                                        exclude=True)
                                        total_dur = sum([x[1] - x[0] for y in poi for x in y['times']])
                                        count = len(evts)
                                        density = count / (total_dur / epoch_dur)
                                        logger.debug('----- WHOLE NIGHT -----')
                                        logger.debug(f'No. Events = {count}, Total duration (s) = {total_dur}')
                                        logger.debug(f'Density = {round(density, ndigits=2)} per epoch')
                                        logger.info('')
                                        # Export event parameters
                                        try:
                                            data = event_params(segments, params=param_keys, 
                                                                band=freq, n_fft=None)
                                            if not path.exists(self.out_dir + '/' + sub):
                                                mkdir(self.out_dir + '/' + sub)
                                            if not path.exists(self.out_dir + '/' + sub + '/' + ses):
                                                mkdir(self.out_dir + '/' + sub + '/' + ses)
                                            out_dir = self.out_dir + '/' + sub + '/' + ses
                                            data = sorted(data, key=lambda x: x['start'])
                                            stagename = '-'.join(self.stage)
                                            outputfile = f'{out_dir}/{sub}_{ses}_{fnamechan}_{stagename}_{event}.csv'
                                            export_event_params(outputfile, data, count=len(evts), 
                                                                density=density)
                                            logger.debug('Writing to ' + outputfile)
                                        except:
                                            logger.warning(f'Issue exporting data for {sub}, {ses}, {fnamechan}, {stagename}, {event}.')
                                            flag +=1
                                            continue
                                
                                ### PER STAGE AND CYCLE ###
                                elif model == 'stage*cycle':
                                    for s, st in enumerate(self.stage):
                                        for cy, cycc in enumerate(cycle_idx):
                                            try:
                                                cyc = cycle[cy]
                                                if not isinstance(chan_ful, list):
                                                    chan_ful = [chan_ful]
                                                    if len(chan_ful) > 1:
                                                        chan_ful = chan_ful[0] 
                                                segments = fetch(dataset, annot, 
                                                                 cat=cat, evt_type=[event], 
                                                                 stage = [st], 
                                                                 cycle=[cyc], 
                                                                 chan_full=chan_ful, 
                                                                 reject_epoch=True, 
                                                                 reject_artf=['Artefact', 'Arou', 'Arousal'], 
                                                                 min_dur=0.5)
                                                segments.read_data([channel], chanset[channel], 
                                                                   grp_name=self.grp_name)
                                            except Exception as e:
                                                logger.error(e)
                                                logger.warning(f'Error reading data for {sub}, {ses}, CHANNEL {channel}, STAGE {st} in CYCLE {cy+1}.')
                                                flag +=1
                                                continue
                                            if len(segments) < 1:
                                                logger.warning(f'No valid data found for {sub}, {ses}, CHANNEL {channel}, STAGE {st} in CYCLE {cy+1}.')
                                                flag +=1
                                                continue
                                            else:
                                                # Get times
                                                if isinstance(chan_ful, ndarray):
                                                    if len(chan_ful) > 1:
                                                        chan_ful = chan_ful[0]
            
                                                if len(chan_ful) > 1:
                                                    chan_ful = chan_ful[0]
            
                                                # Calculate event density (per cycle)
                                                poi = get_times(annot, stage=[st], 
                                                                cycle=[cyc], chan=[channel], 
                                                                exclude=True)
                                                total_dur = sum([x[1] - x[0] for y in poi for x in y['times']])
                                                evts = annot.get_events(name=event, 
                                                                        time=cycle[cy][0:2], 
                                                                        chan = f'{channel} ({self.grp_name})', 
                                                                        stage = st)
                                                count = len(evts)
                                                density = len(evts) / (total_dur / epoch_dur)
                                                logger.info('')
                                                logger.debug(f'---- STAGE {st}, CYCLE {cy+1} ----')
                                                logger.debug(f'No. Events = {count}, Total duration (s) = {total_dur}')
                                                logger.debug(f'Density = {round(density, ndigits=2)} per epoch')
                                                logger.info('')
    
                                                # Export event parameters
                                                data = event_params(segments, params=params, 
                                                                    band=freq, n_fft=None)
                                                if not path.exists(self.out_dir + '/' + sub):
                                                    mkdir(self.out_dir + '/' + sub)
                                                if not path.exists(self.out_dir + '/' + sub + '/' + ses):
                                                    mkdir(self.out_dir + '/' + sub + '/' + ses)
                                                out_dir = self.out_dir + '/' + sub + '/' + ses
                                                data = sorted(data, key=lambda x: x['start'])
                                                outputfile = f'{out_dir}/{sub}_{ses}_{fnamechan}_{st}_cycle{cy+1}_{event}.csv' 
                                                export_event_params(outputfile, data, 
                                                                    count=len(evts), 
                                                                    density=density)
                                                logger.debug('Writing to ' + outputfile)                
                                ### PER STAGE ###
                                elif model == 'per_stage':
                                    for s, st in enumerate(self.stage):
                                        try:
                                            segments = fetch(dataset, annot, cat=cat, 
                                                         evt_type=[event], 
                                                         stage = [st], cycle=cycle, 
                                                         chan_full=chan_ful, 
                                                         reject_epoch=True, 
                                                         reject_artf = ['Artefact', 'Arou', 'Arousal'], 
                                                         min_dur=0.5)
                                            segments.read_data([channel], chanset[channel], 
                                                               grp_name=self.grp_name)
                                        except Exception as e:
                                            logger.error(e)
                                            logger.warning(f'Error reading data for {sub}, {ses}, CHANNEL {channel}, STAGE {st}.')
                                            flag +=1
                                            continue
                                        if len(segments) < 1:
                                            logger.warning(f'No valid data found for {sub}, {ses}, CHANNEL {channel}, STAGE {st}.')
                                            flag +=1
                                            continue
                                        else:
                                            # Get times
                                            poi = get_times(annot, stage=[st], cycle=cycle, 
                                                            chan=[channel], exclude=True)
                                            total_dur = sum([x[1] - x[0] for y in poi for x in y['times']])
                                            evts = annot.get_events(name=event, time=None, 
                                                                    chan = f'{channel} ({self.grp_name})', 
                                                                    stage = st)
                                            count = len(evts)
                                            density = len(evts) / (total_dur / epoch_dur)
                                            logger.info('')
                                            logger.debug(f'---- STAGE {st} ----')
                                            logger.debug(f'No. Events = {count}, Total duration (s) = {total_dur}')
                                            logger.debug(f'Density = {round(density, ndigits=2)} per epoch')
                                            logger.info('')
                                            # Export event parameters 
                                            data = event_params(segments, params=params, 
                                                                band=freq, n_fft=None)
                                            if not data:
                                                data = [x for x in segments]
                                            else:
                                                data = sorted(data, key=lambda x: x['start'])
                                            
                                            if not path.exists(self.out_dir + '/' + sub):
                                                mkdir(self.out_dir + '/' + sub)
                                            if not path.exists(self.out_dir + '/' + sub + '/' + ses):
                                                mkdir(self.out_dir + '/' + sub + '/' + ses)
                                            out_dir = self.out_dir + '/' + sub + '/' + ses
                                            
                                            outputfile = f'{out_dir}/{sub}_{ses}_{fnamechan}_{st}_{event}.csv' 
                                            export_event_params(outputfile, data, 
                                                                count=len(evts), 
                                                                density=density)
                                            logger.debug('Writing to ' + outputfile) 
                                
                                ### PER CYCLE ###
                                elif model == 'per_cycle': 
                                    for cy, cycc in enumerate(cycle_idx):
                                        try:
                                            cyc = cycle[cy]
                                            if not isinstance(chan_ful, list):
                                                chan_ful = [chan_ful]
                                                if len(chan_ful) > 1:
                                                    chan_ful = chan_ful[0] 
                                            segments = fetch(dataset, annot, cat=cat, 
                                                             evt_type=[event],
                                                             stage = self.stage, 
                                                             cycle=[cyc], chan_full=chan_ful, 
                                                             reject_epoch=True, 
                                                             reject_artf = ['Artefact', 'Arou', 'Arousal'],
                                                             min_dur=0.5)
                                            segments.read_data([channel], chanset[channel], 
                                                               grp_name=self.grp_name)
                                        except Exception:
                                            logger.error(e)
                                            logger.warning(f'Error reading data for {sub}, {ses}, CHANNEL {channel}, CYCLE {cy}.')
                                            flag +=1
                                            continue
                                        if len(segments) < 1:
                                            logger.warning(f'No valid data found for {sub}, {ses}, CHANNEL {channel}, CYCLE {cy}.')
                                            flag +=1
                                            continue
                                        else:
                                            # Get times
                                            if isinstance(chan_ful, ndarray):
                                                if len(chan_ful) > 1:
                                                    chan_ful = chan_ful[0]
        
                                            if len(chan_ful) > 1:
                                                chan_ful = chan_ful[0]
        
                                            # Calculate event density (per cycle)
                                            poi = get_times(annot, stage=self.stage, 
                                                            cycle=[cyc], chan=[channel], 
                                                            exclude=True)
                                            total_dur = sum([x[1] - x[0] for y in poi for x in y['times']])
                                            evts = annot.get_events(name=event, 
                                                                    time=cycle[cy][0:2], 
                                                                    chan = f'{channel} ({self.grp_name})', 
                                                                    stage = self.stage)
                                            count = len(evts)
                                            density = len(evts) / (total_dur / epoch_dur)
                                            logger.info('')
                                            logger.debug(f'---- CYCLE {cy+1} ----')
                                            logger.debug(f'No. Events = {count}, Total duration (s) = {total_dur}')
                                            logger.debug(f'Density = {round(density, ndigits=2)} per epoch')
                                            logger.info('')
                                            # Export event parameters 
                                            data = event_params(segments, params=params, 
                                                                band=freq, n_fft=None)
                                            if not path.exists(self.out_dir + '/' + sub):
                                                mkdir(self.out_dir + '/' + sub)
                                            if not path.exists(self.out_dir + '/' + sub + '/' + ses):
                                                mkdir(self.out_dir + '/' + sub + '/' + ses)
                                            out_dir = self.out_dir + '/' + sub + '/' + ses
                                            data = sorted(data, key=lambda x: x['start'])
                                            stagename = '-'.join(self.stage)
                                            outputfile = f'{out_dir}/{sub}_{ses}_{fnamechan}_{stagename}_cycle{cy+1}_{event}.csv'  
                                            export_event_params(outputfile, data, 
                                                                count=len(evts), 
                                                                density=density)
                                            logger.debug('Writing to ' + outputfile)
                                    
                                ### PER SEGMENT ###
                                if segs:
                                    segnames = ['-'.join((x[0],x[1])) for x in segs]
                                    for s,seg in enumerate(segs): 
                                        
                                        # Calculate event density (per segment type)
                                        poi = get_times(annot, evt_type=[seg[0],seg[1]], 
                                                        stage=None, chan=[channel], 
                                                        exclude=True)
                                        duos=[]
                                        [duos.extend([(poi[0]['times'][x][0],poi[1]['times'][x][1])]) 
                                                             for x,item in enumerate(poi[0]['times'])]
                                        total_dur = sum([x[1] - x[0] for x in duos])
                                        evts =[]
                                        for d in duos:
                                            evts.extend(annot.get_events(name=event, 
                                                                         time=d, 
                                                                         chan = chan_ful, 
                                                                         stage = None))
                                        count = len(evts)
                                        density = len(evts) / (total_dur / epoch_dur)
                                        logger.info('')
                                        logger.debug(f'----- Segment {seg} -----')
                                        logger.debug(f'No. Events = {count}, Total duration (s) = {total_dur}')
                                        logger.debug(f'Density = {round(density, ndigits=2)} per epoch')
                                        logger.info('')
                                        
                                        # Export event parameters
                                        data = event_params(segments, params=params, 
                                                            band=freq, n_fft=None)
                                        if data:
                                                data = sorted(data, key=lambda x: x['start'])
                                                outputfile = f'{self.out_dir}/{sub}/{ses}/{sub}_{ses}_{fnamechan}_{segnames[s]}_{event}.csv'
                                                export_event_params(outputfile, data, 
                                                                    count=len(evts), 
                                                                    density=density)
                                        else:
                                            logger.warning(f'No valid data found for {sub}, {ses}, {seg}.')
                                            flag+=1
                                            continue

                ### 3. Check completion status and print
                if flag == 0:
                    logger.info('')
                    logger.debug('Listing Individual aNnotated Events (L.I.N.E) '
                                 'finished without ERROR.')  
                else:
                    logger.info('')
                    logger.warning('Listing Individual aNnotated Events (L.I.N.E) ' 
                                   f'finished with {flag} WARNINGS. See log for details.')
                return 
    
                    
    def net(self, chan, evt_name, adap_bands, params = 'all', cat = (1,1,1,1), 
                  cycle_idx = None, logger = create_logger('Event dataset')):
        
        '''
            aNnotated Event Tabulation (NET)
            
            This function extracts average (or stdev) parameters of 
            specific (named) events from the whole cohort and creates a 
            master-level dataframe tabulating this information.
            This function can only be used one-event-at-a-time.
        '''
        
        ### 0.a Set up logging
        flag = 0
        logger.info('')
        logger.debug(r""" Commencing Event Dataset Creation

                     
                              ∆       ∆       ∆    ∆     ∆       ∆    ∆         ∆
                      ~^~^~~^~O~^~^~^~O~^~^~^~O~^~~O~^~^~O~^~^~^~O~^~~O~^~^~^~^~O~^~^~~
                              .       .       .    .     .       .    .         .
                               •. . .• •..• .• •..• •. .• •..• .• •..• •...•.•.•.
                               •. •.•   ;   ;   ; »<>;  ;   ;   ;   ;   ;   ;  .                                                                                                  
                                 •.•....;...;...;...;...;...;...;...;...;...;.•
                      »<>          .•   ;   ;   ;   ;   ;   ;   ;  ;   ;    ;  »<>
                                   •....;...;...;...;...;...;...;...;...;...;.
                                   .•   ;   ;   ;   ;  ; »<> ;   ;  ;   ;    ;..
                                  .•....;...;...;...;...;...;...;...;...;...;..•.
                                   •.   ;  ;    ;   ;   ;   ;   ;  ;   ;    ;   ;
                                   .•..•..;.•...•...•...•..•..;•..•...•....•.;.•
                                
                                
                                
                                aNnotated Events Tabulation 
                                (N.E.T) 
                                
                                                    """,)
        
        ### 1. First check the directories
        # a. Check for output folder, if doesn't exist, create
        if not path.exists(self.out_dir):
                mkdir(self.out_dir)
        
        # b. Get subject IDs
        subs = self.subs
        if isinstance(subs, list):
            None
        elif subs == 'all':
                subs = next(walk(self.xml_dir))[1]
        else:
            logger.error("'subs' must either be an array of participant ids or = 'all' ")
            
        # c. Take a look through directories to get sessions
        subs.sort()
        sessions = {}
        for s, sub in enumerate(subs):
            if self.sessions == 'all':
                sessions[sub] = next(walk(f'{self.xml_dir}/{sub}'))[1]
        sessions = list(set([y for x in sessions.values() for y in x]))           
        sessions.sort() 
        
        ### 2. Set up organisation of export
        if cat[0] + cat[1] == 2:
            model = 'whole_night'
            logger.debug('Exporting parameters for the whole night.')
        elif cat[0] + cat[1] == 0:
            model = 'stage*cycle'
            logger.debug('Exporting parameters per stage and cycle separately.')
        elif cat[0] == 0:
            model = 'per_cycle'
            logger.debug('Exporting parameters per cycle separately.')
        elif cat[1] == 0:
            model = 'per_stage'  
            logger.debug('Exporting parameters per stage separately.')
        if 'cycle' in model and cycle_idx == None:
            logger.info('')
            logger.critical("To export cycles separately (i.e. cat[0] = 0), cycle_idx cannot be 'None'")
            return
        
        # 3. Set variable names and combine with visits 
        if params == 'all':
            variables = ['Count','Density','Duration_mean','Duration_stdv',
                         'Min_amplitude_mean','Min_amplitude_stdv', 'Max_amplitude_mean',
                         'Max_amplitude_stdv','Ptp_amplitude_mean', 'Ptp_amplitude_stdev',
                         'Power_mean','Power_stdev', 'Peak_power_frequency_mean',
                         'Peak_power_frequency_std']
        else:
            variables = params
        
        
        # 4. Begin data extraction
        for c, ch in enumerate(chan):
            logger.debug(f'Creating a {evt_name} dataset for {ch}..')
            
            # a. Create column names (append chan and ses names)
            for v, ses in enumerate(sessions):
                sesvar = []
                for pair in product(variables, [ses]):
                    sesvar.append('_'.join(pair))
                columns = []
                for pair in product([evt_name], sesvar, [ch]):
                    columns.append('_'.join(pair))
                
                # b. Extract data based on cycle and stage setup
                if model == 'whole_night':
                    stagename = '-'.join(self.stage)
                    logger.debug(f'Collating {evt_name} parameters from {ch}, {stagename}..')
                    st_columns = [x + f'_{stagename}' for x in columns]
                    df = DataFrame(index=subs, columns=st_columns,dtype=float) 
                    for s, sub in enumerate(subs): 
                        logger.debug(f'Extracting from {sub}, {ses}')
                        data_file = f'{self.xml_dir}/{sub}/{ses}/{sub}_{ses}_{ch}_{stagename}_{evt_name}.csv' 
                        if path.isfile(data_file):
                            try:
                                df.loc[sub] = extract_event_data(data_file, variables)
                            except:
                                extract_data_error(logger)
                                flag +=1
                                return
                        else:
                            flag +=1
                            logger.warning(f'Data not found for {sub}, {ses}, '
                                           f'{ch}, {stagename}, Event: {evt_name} '
                                           '- has export_eventparams been run for '
                                           f'{model}, using adap_bands = {adap_bands}?')
                    if not path.exists(f'{self.out_dir}/{evt_name}_{model}'):
                        mkdir(f'{self.out_dir}/{evt_name}_{model}')
                    df.to_csv(f"{self.out_dir}/{evt_name}_{model}/{evt_name}_{ses}_{ch}_{stagename}.csv")
                    
                elif model == 'stage*cycle':
                    for cyc in cycle_idx:
                        cycle = f'cycle{cyc}'
                        for st in self.stage:
                            st_columns = [x + f'_{st}_{cycle}' for x in columns]
                            df = DataFrame(index=subs, columns=st_columns,dtype=float) 
                            logger.debug(f'Collating {evt_name} parameters from {ch}, {st}..')
                            for s, sub in enumerate(subs): 
                                logger.debug(f'Extracting from {sub}, {ses}')
                                data_file = f'{self.xml_dir}/{sub}/{ses}/{sub}_{ses}_{ch}_{st}_{cycle}_{evt_name}.csv'
                                if path.isfile(data_file):
                                    try:
                                        df.loc[sub] = extract_event_data(data_file, variables)
                                    except:
                                        extract_data_error(logger)
                                        flag +=1
                                        return
                                else:
                                    flag +=1
                                    logger.warning(f'Data not found for {sub}, '
                                                   f'{ses}, {ch}, {st}, Event: '
                                                   f'{evt_name} - has export_eventparams '
                                                   f'been run for {model}, '
                                                   f'using adap_bands = {adap_bands}?')
                            if not path.exists(f'{self.out_dir}/{evt_name}_{model}'):
                                mkdir(f'{self.out_dir}/{evt_name}_{model}')
                            df.to_csv(f"{self.out_dir}/{evt_name}_{model}/{evt_name}_{ses}_{ch}_{st}_{cycle}.csv")
                
                elif model == 'per_cycle':
                    for cyc in cycle_idx:
                        cycle = f'cycle{cyc}'
                        stagename = '-'.join(self.stage)
                        st_columns = [x + f'_{stagename}_{cycle}' for x in columns]
                        df = DataFrame(index=subs, columns=st_columns,dtype=float) 
                        logger.debug(f'Collating {evt_name} parameters from {ch}, '
                                     f'{stagename}, {cycle}..')
                        for s, sub in enumerate(subs): 
                            logger.debug(f'Extracting from {sub}, {ses}')
                            data_file = f'{self.xml_dir}/{sub}/{ses}/{sub}_{ses}_{ch}_{stagename}_{cycle}_{evt_name}.csv'
                            if path.isfile(data_file):
                                try:
                                    df.loc[sub] = extract_event_data(data_file, variables)
                                except:
                                    extract_data_error(logger)
                                    flag +=1
                                    return
                            else:
                                flag +=1
                                logger.warning(f'Data not found for {sub}, {ses}, '
                                               f'{ch}, {stagename}, {cycle}, Event: '
                                               f'{evt_name} - has export_eventparams '
                                               f'been run for {model}, using adap_bands '
                                               f'= {adap_bands}?')
                        if not path.exists(f'{self.out_dir}/{evt_name}_{model}'):
                            mkdir(f'{self.out_dir}/{evt_name}_{model}')
                        df.to_csv(f"{self.out_dir}/{evt_name}_{model}/{evt_name}_{ses}_{ch}_{stagename}_{cycle}.csv")
                    
                elif model == 'per_stage':
                    for st in self.stage:
                        st_columns = [x + f'_{st}' for x in columns]
                        df = DataFrame(index=subs, columns=st_columns,dtype=float) 
                        logger.debug(f'Collating {evt_name} parameters from {ch}, {st}..')
                        for s, sub in enumerate(subs): 
                            logger.debug(f'Extracting from {sub}, {ses}')
                            data_file = f'{self.xml_dir}/{sub}/{ses}/{sub}_{ses}_{ch}_{st}_{evt_name}.csv'
                            if path.isfile(data_file):
                                try:
                                    df.loc[sub] = extract_event_data(data_file, variables)
                                except:
                                    extract_data_error(logger)
                                    flag +=1
                                    return
                            else:
                                flag +=1
                                logger.warning(f'Data not found for {sub}, {ses}, {ch}, {st}, '
                                               f'Event: {evt_name} - has export_eventparams been '
                                               f'run for {model}, using adap_bands = {adap_bands}?')
                        if not path.exists(f'{self.out_dir}/{evt_name}_{model}'):
                            mkdir(f'{self.out_dir}/{evt_name}_{model}')  
                        df.to_csv(f"{self.out_dir}/{evt_name}_{model}/{evt_name}_{ses}_{ch}_{st}.csv")
        
                
        ### 3. Check completion status and print
        if flag == 0:
            logger.info('')
            logger.debug('aNnotated Events Tabulation (N.E.T) finished without ERROR.')  
        else:
            logger.info('')
            logger.warning('aNnotated Events Tabulation (N.E.T) finished with '
                           f'{flag} WARNINGS. See log for details.')
        return 

    
    def scalops(self, chan, evt_name, bands, params = 'all', 
                 logger = create_logger('Cluster dataset')):
        
        '''
            Summary of Clustering And Low-frequency Oscillatory Power Signatures
            S.C.A.L.O.P.S
            
            This function extracts individual parameters of 
            clustering and LFF stats from the whole cohort and creates a 
            master-level dataframe tabulating this information.
            This function can only be used one-event-at-a-time.
        '''
        
        ### 0.a Set up logging
        flag = 0
        logger.info('')
        logger.debug(r""" Commencing Event Dataset Creation

                     
                               _.---._              _.---._
                           .'"".'/|\`.""'.      .'""/     \""'. 
                          :  .' / | \ `.  :    :  .'\-___-/`.  :
                          '.'  /  |  \  `.'    '.'  /  |  \  `.'
                           `. /   |   \ .'      `. /   |   \ .'
                             `-.__|__.-'          `-.__|__.-'
                                                    
                    Summary of Clustering And Low-frequency Oscillatory Power Signatures
                    S.C.A.L.O.P.S
                                
                                                    """,)
        
        ### 1. First check the directories
        # a. Check for output folder, if doesn't exist, create
        if not path.exists(self.out_dir):
                mkdir(self.out_dir)
        
        # b. Get subject IDs
        subs = self.subs
        if isinstance(subs, list):
            None
        elif subs == 'all':
                subs = next(walk(self.xml_dir))[1]
        else:
            logger.error("'subs' must either be an array of participant ids or = 'all' ")
            
        # c. Take a look through directories to get sessions
        subs.sort()
        if isinstance(self.sessions, str) and self.sessions == "all":
            sessions = set()
            for subdir in Path(self.xml_dir).iterdir():
                if subdir.is_dir() and subdir.name.startswith("sub-"):
                    for sesdir in subdir.iterdir():
                        if sesdir.is_dir() and sesdir.name.startswith("ses-"):
                            sessions.add(sesdir.name)
            sessions = sorted(sessions)
        elif isinstance(self.sessions, list):
            sessions = self.sessions
        else:
            raise ValueError("sessions must be a list or 'all'")
 
        # 3. Set variable names and combine with visits 
        if params == 'all':
            variables = ['cv','cv_p_value','VMR','VMR_p_value',
                         'num_clusters_n','average_cluster_size_n',
                         'max_cluster_size_n','min_cluster_size_n',
                         'clusters_per_60s','ave_within_cluster_freq',
                         'mean_iei_s','median_iei_s','min_interval_s',
                         'mean_interval_s','max_interval_s',
                         'min_cluster_duration_s','avg_cluster_duration_s',
                         'max_cluster_duration_s']
            for band in bands:
                variables.extend([f'{band}_peak_freq', f'{band}_avg_peak_power'])
        else:
            variables = params
        
        # band names
        fbandnames = '-'.join(bands)
        
        # 4. Begin data extraction
        for c, ch in enumerate(chan):
            logger.debug(f'Collating cluster parameters for {fbandnames}, {evt_name} in {ch}..')
            # a. Create column names (append chan and ses names)
            for v, ses in enumerate(sessions):
                sesvar = []
                for pair in product(variables, [ses]):
                    sesvar.append('_'.join(pair))
                columns = []
                for pair in product([evt_name], sesvar, [ch]):
                    columns.append('_'.join(pair))
                
                stagename = '-'.join(self.stage)
                st_columns = [x + f'_{stagename}' for x in columns]
                df_stats = DataFrame(index=subs, columns=st_columns, dtype=float)
                df_hist = []
                for s, sub in enumerate(subs): 
                    logger.debug(f'Extracting from {sub}, {ses}')
                    
                    # Cluster metrics
                    ar = []
                    data_file = f'{self.xml_dir}/{sub}/{ses}/{sub}_{ses}_{ch}_{stagename}_{evt_name}_clustering.csv'     
                    if path.isfile(data_file):
                        try:
                            ar.extend(extract_cluster_data(data_file, variables))
                        except:
                            extract_data_error(logger)
                            flag +=1
                            continue
                    else:
                        flag +=1
                        logger.warning(f'*clustering.csv not found for {sub}, '
                                       f'{ses}, {ch}, {stagename}, {fbandnames}'
                                       f'in {self.xml_dir}/{sub}/{ses}/')
                        continue
                    
                    # Peak data
                    data_file = f'{self.xml_dir}/{sub}/{ses}/{sub}_{ses}_{ch}_{stagename}_{fbandnames}_fluctuation_stats.csv'     
                    if path.isfile(data_file):
                        try:
                            ar.extend(extract_cluster_data(data_file, variables))
                        except:
                            extract_data_error(logger)
                            flag +=1
                            continue
                    else:
                        flag +=1
                        logger.warning(f'*fluctuation_stats.csv not found for {sub}, '
                                       f'{ses}, {ch}, {stagename}, {fbandnames} '
                                       f'in {self.xml_dir}/{sub}/{ses}/')
                        continue
                        
                    # Save to df
                    df_stats.loc[sub] = ar
                 
                df_stats.to_csv(f"{self.out_dir}/{evt_name}_{ses}_{ch}_{stagename}_cluster_stats.csv")
                
        for c, ch in enumerate(chan):
            for band in bands:
                logger.debug(f'Collating phase-histograms for {band}, {evt_name} in {ch}..')
                
                # a. Create column names (append chan and ses names)
                for v, ses in enumerate(sessions):
                    # Histogram
                    df_hist = []
                    for s, sub in enumerate(subs): 
                        logger.debug(f'Extracting from {sub}, {ses}')   
                        data_file = f'{self.xml_dir}/{sub}/{ses}/{sub}_{ses}_{ch}_{stagename}_{evt_name}_{band}_coupling.csv'
                        if path.isfile(data_file):
                            try:
                                hist = read_csv(data_file, index_col = 0)
                                hist.index = [sub]
                                df_hist.append(hist)
                            except:
                                extract_data_error(logger)
                                flag +=1
                                continue
                        else:
                            flag +=1
                            logger.warning(f'*coupling.csv not found for {sub}, '
                                           f'{ses}, {ch}, {stagename}, {evt_name}, {band} '
                                           f'in {self.xml_dir}/{sub}/{ses}/')
                            
                            
                   
                    # Concatenate all dataframes vertically (row-wise)
                    master_df = concat(df_hist)
                    master_df.to_csv(f"{self.out_dir}/{evt_name}-{band}_{ses}_{ch}_{stagename}_histogram.csv")
            
        for c, ch in enumerate(chan):
            for band in bands:
                logger.debug(f'Collating PSD for {band}, {evt_name} in {ch}..')
                
                # a. Create column names (append chan and ses names)
                for v, ses in enumerate(sessions):
                    # Histogram
                    df_psd = []
                    for s, sub in enumerate(subs): 
                        logger.debug(f'Extracting from {sub}, {ses}')   
                        data_file = f'{self.xml_dir}/{sub}/{ses}/{sub}_{ses}_{ch}_{stagename}_{band}_fluctuations_psd.csv'
                        if path.isfile(data_file):
                            try:
                                psd = read_csv(data_file, index_col = 0)
                                psd.index = [sub]
                                df_psd.append(psd)
                            except:
                                extract_data_error(logger)
                                flag +=1
                                continue
                        else:
                            flag +=1
                            logger.warning(f'*fluctuations_psd.csv not found for {sub}, '
                                           f'{ses}, {ch}, {stagename}, {evt_name}, {band} '
                                           f'in {self.xml_dir}/{sub}/{ses}/')
                            
                            
                   
                    # Concatenate all dataframes vertically (row-wise)
                    master_df = concat(df_psd)
                    master_df.to_csv(f"{self.out_dir}/{band}_{ses}_{ch}_{stagename}_fluctuations_psd.csv")
                        
                  
        ### 3. Check completion status and print
        if flag == 0:
            logger.info('')
            logger.debug('Summary of Clustering And Low-frequency Oscillatory Power Signatures '
                         '(S.C.A.L.O.P.S) finished without ERROR.')  
        else:
            logger.info('')
            logger.warning('Summary of Clustering And Low-frequency Oscillatory Power Signatures '
                           f'(S.C.A.L.O.P.S) finished with {flag} WARNINGS. See log for details.')
        return            
                    
    
    def pac_summary(self, chan, evt_name = None, 
                          adap_bands_phase = 'Fixed', 
                          frequency_phase = (0.5, 1.25), 
                          adap_bands_amplitude = 'Fixed', 
                          frequency_amplitude = (11, 16),
                          adap_bw = 4,
                          params = 'all', 
                          cat = (1,1,1,1), 
                          cycle_idx = None, 
                          logger = create_logger('PAC dataset')):
        
        
        '''
            PAC summary
            
            This function extracts the summary parameters of PAC for each sub 
            and ses, and creates a master-level dataframe tabulating this 
            information. This function can only be used for one set of analyses
            at a time.
        '''
        
        ### ---- 0.a Set up logging ----
        missing_data_flag = 0
        
        logger.info('')
        logger.debug(r""" Commencing PAC Dataset Creation

                     
                      (Graphic Under Construction...)
                      
                      ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀  ⢀⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                        ⠀⠀⠀⠀⠀⠀⠀⢀⣠⣴⠾⢻⣿⡟⠻⠶⢦⣤⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                        ⠀⠀⠀⠀⣀⣤⠾⠛⠉⠀⠀⣸⠛⣷⠀⠀⠀⠀⠉⠙⠻⠶⣦⣤⣀⠀⠀⠀⠀⠀
                        ⠀⠀⠐⠛⠋⠀⠀⠀⠀⠀⠀⠛⠀⠛⠂⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⠛⠒⠂⠀⠀
                        ⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀
                        ⠀⠀⠀⢠⣤⣤⣤⠀⠀⠀⠀⢠⣤⡄⢠⣤⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⡄⠀⠀⠀
                        ⠀⠀⠀⠈⠉⠉⠉⠀⠀⠀⠀⠸⠿⠇⠸⠿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀
                        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣶⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀
                        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀
                        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠃⠀⠀⠀
                        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠃⡀⠀⠀
                        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠋⠈⠛⠀⠀
                        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⢸⣿⡇⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⡇⠀
                        ⠀⠀⠀⠀⠀⠀⠀⢀⣴⠾⠋⢸⣿⡇⠈⠳⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                        ⠀⠀⠀⠀⠀⠀⠀⠈⠁⠀⠀⠈⠛⠃⠀⠀⠀⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                                
                                                    """,)
        
        ### ---- 1. First check the directories ----

        # a. Ensure output directory exists
        if not path.exists(self.out_dir):
            mkdir(self.out_dir)
        
        # b. Get subject IDs
        subs = self.subs
        sub_pattern = re.compile(r"^sub-\w+")
        
        if isinstance(subs, list):
            if not all(sub_pattern.match(s) for s in subs):
                logger.error("Invalid participant ID format in list. IDs should "
                             "be BIDS-compatible (e.g., 'sub-01').")
                return
        elif subs == 'all':
            try:
                subs = sorted(next(walk(self.xml_dir))[1])
                subs = [s for s in subs if sub_pattern.match(s)]
            except StopIteration:
                logger.critical(f"No participant directories found in {self.xml_dir}")
                return
        else:
            logger.error("'subs' must either be a list of participant IDs or 'all'")
            return
        
        # c. Get all sessions (may differ across subjects)
        if isinstance(self.sessions, str) and self.sessions == "all":
            sessions = set()
            for subdir in Path(self.xml_dir).iterdir():
                if subdir.is_dir() and subdir.name.startswith("sub-"):
                    for sesdir in subdir.iterdir():
                        if sesdir.is_dir() and sesdir.name.startswith("ses-"):
                            sessions.add(sesdir.name)
            sessions = sorted(sessions)
        elif isinstance(self.sessions, list):
            sessions = self.sessions
        else:
            raise ValueError("sessions must be a list or 'all'")
        
        # ---- 2. Determine export model based on 'cat' ----    
        if not isinstance(cat, tuple) or len(cat) != 4:
            logger.critical("'cat' must be a tuple of four binary flags: (cycle, "
                            "stage, continuous, event).")
            return
        
        cycle_flag, stage_flag, _, _ = cat  # continuous and event flags are unused here
        
        if cycle_flag and stage_flag:
            model = 'whole_night'
            logger.debug('Exporting parameters for the whole night (concatenated '
                         'across cycles and stages).')
        elif not cycle_flag and not stage_flag:
            model = 'stage*cycle'
            logger.debug('Exporting parameters per stage and per cycle separately.')
        elif not cycle_flag:
            model = 'per_cycle'
            logger.debug('Exporting parameters per cycle separately (but across '
                         'stages).')
        elif not stage_flag:
            model = 'per_stage'
            logger.debug('Exporting parameters per stage separately (but across '
                         'cycles).')
        else:
            logger.critical("Unrecognized combination of 'cat' flags for cycle "
                            "and stage.")
            return
        
        # Validation: If we're splitting by cycle, we need to know which ones
        if 'cycle' in model and cycle_idx is None:
            logger.critical("To export data by cycle, 'cycle_idx' must be specified.")
            return
        
        
        # ---- 3. Set PAC variable names and column generation ----
        if params == 'all':
            variables = ['mi_raw', 'mi_norm', 'pval1', 'pp_radians', 
                         'ppdegrees', 'mvl']
            logger.debug(f"Using default PAC variables: {variables}")
        elif isinstance(params, list) and all(isinstance(p, str) for p in params):
            variables = params
            logger.debug(f"Using custom PAC variables: {variables}")
        else:
            logger.critical("'params' must be 'all' or a list of variable names (strings).")
            return


        # ---- 4. Set PAC band names for phase and amplitude ----
        # Phase Band Naming
        if adap_bands_phase == 'Fixed':
            adap_phase_name = 'fixed'
        else:
            adap_phase_name = 'adap'

        # Amplitude Band Naming
        if adap_bands_amplitude == 'Fixed':
            adap_amp_name = 'fixed'
        else:
            adap_amp_name = 'adap'
        
        # Generate pac_name with event if specified, otherwise without
        if evt_name:
            pac_name = f'{evt_name}_**-{adap_phase_name}_##-{adap_amp_name}_pac'
        else:
            pac_name = f'**-{adap_phase_name}_##-{adap_amp_name}_pac'
        
        # Setup for output filename
        out_phasebw = f'{frequency_phase[0]}-{frequency_phase[1]}Hz'  
        out_ampbw = f'{frequency_amplitude[0]}-{frequency_amplitude[1]}Hz' 
        pac_outname = f'pac_pha-{out_phasebw}-{adap_phase_name}_amp-{out_ampbw}-{adap_amp_name}'

        # ---- 5. Begin data extraction ----
        for c, ch in enumerate(chan):
            logger.debug(f'Creating a PAC dataset for {ch}..')
                
            for v, ses in enumerate(sessions):
                sesvar = []
                for pair in product(variables, [ses]):
                    sesvar.append('_'.join(pair))
                columns = []
                for pair in product(sesvar, [ch]):
                    columns.append('_'.join(pair))
                    
                missing_data_flag = extract_pac_summary(subs, 
                                                        ses, 
                                                        model,
                                                        evt_name,
                                                        pac_name,
                                                        pac_outname,
                                                        ch, 
                                                        self.stage, 
                                                        cycle_idx,
                                                        columns, 
                                                        variables, 
                                                        self.rootpath, 
                                                        self.xml_dir, 
                                                        self.out_dir,
                                                        adap_bands_phase,  
                                                        frequency_phase,
                                                        adap_bands_amplitude, 
                                                        frequency_amplitude, 
                                                        adap_bw, 
                                                        self.tracking, 
                                                        logger, 
                                                        missing_data_flag
                                                        )    
                    
        # ---- 6. Check completion status and print ----
        if missing_data_flag == 0:
            logger.info('')
            logger.debug('Create PAC dataset finished without ERROR.')  
        else:
            logger.info('')
            logger.warning(f'Create PAC dataset finished with {missing_data_flag} WARNINGS. '
                           'See log for details.')
        
        return 
       
    
def extract_pac_summary(subs, ses, model, evt_name, pac_name, pac_outname, 
                        chan, stage, cycle_idx, 
                        columns, variables, rootpath, xml_dir, out_dir, 
                        adap_bands_phase, frequency_phase,
                        adap_bands_amplitude, frequency_amplitude, 
                        adap_bw, 
                        tracking, logger, flag):
    
    
    if not path.exists(f'{out_dir}/{pac_outname}_{model}'):
        mkdir(f'{out_dir}/{pac_outname}_{model}')

    evt = f'_{evt_name}' if evt_name else ""
    
    # ---- Extract data based on cycle and stage setup ----
    if model == 'whole_night':
        stagename = '-'.join(stage)
        logger.debug(f'Collating PAC parameters from {chan}, {stagename}..')
        st_columns = [x + f'_{stagename}' for x in columns]
        df = DataFrame(index=subs, columns=st_columns, dtype=float) 
        out_filename = f'{ses}_{chan}_{stagename}{evt}_{pac_outname}.csv'
        for s, sub in enumerate(subs): 
            logger.debug(f'Extracting from {sub}, {ses}')
            
            phase_bw, amp_bw = extract_phase_amp_bw(rootpath, sub, ses, 
                                                           chan, stage, adap_bw,
                                                           adap_bands_phase, 
                                                           frequency_phase,
                                                           adap_bands_amplitude, 
                                                           frequency_amplitude,
                                                           tracking, logger)
            
            pac_name = pac_name.replace("**", phase_bw).replace("##", amp_bw)
            data_file = f'{xml_dir}/{sub}/{ses}/{sub}_{ses}_{chan}_{stagename}_{pac_name}_parameters.csv' 
            df.loc[sub] = extract_pac_data(data_file, model, variables, logger)
            flag += df.loc[sub].isna().any()
        df.to_csv(f"{out_dir}/{pac_outname}_{model}/{out_filename}")

    elif model == 'stage*cycle':
        for cyc in cycle_idx:
            cycle = f'cycle{cyc}'
            for st in stage:
                logger.debug(f'Collating PAC parameters from {chan}, {st}..')
                st_columns = [x + f'_{st}_{cycle}' for x in columns]
                df = DataFrame(index=subs, columns=st_columns,dtype=float) 
                out_filename = f'{ses}_{chan}_{st}_{cycle}{evt}_{pac_outname}.csv'
                for s, sub in enumerate(subs): 
                    logger.debug(f'Extracting from {sub}, {ses}')
                    
                    phase_bw, amp_bw = extract_phase_amp_bw(rootpath, sub, ses, 
                                                                   chan, stage, adap_bw,
                                                                   adap_bands_phase, 
                                                                   frequency_phase,
                                                                   adap_bands_amplitude, 
                                                                   frequency_amplitude,
                                                                   tracking, logger)
                    
                    pac_name = pac_name.replace("**", phase_bw).replace("##", amp_bw)
                    data_file = f'{xml_dir}/{sub}/{ses}/{sub}_{ses}_{chan}_{st}_{cycle}_{pac_name}_parameters.csv'
                    df.loc[sub] = extract_pac_data(data_file, model, variables, logger)
                    flag += df.loc[sub].isna().any()
                df.to_csv(f"{out_dir}/{pac_outname}_{model}/{out_filename}")
                    
    elif model == 'per_cycle':
        for cyc in cycle_idx:
            cycle = f'cycle{cyc}'
            stagename = '-'.join(stage)
            logger.debug(f'Collating PAC parameters from {chan}, {stagename}, {cycle}..')
            st_columns = [x + f'_{stagename}_{cycle}' for x in columns]
            df = DataFrame(index=subs, columns=st_columns, dtype=float) 
            out_filename = f'{ses}_{chan}_{stagename}_{cycle}{evt}_{pac_outname}.csv'
            for s, sub in enumerate(subs): 
                logger.debug(f'Extracting from {sub}, {ses}')
                
                phase_bw, amp_bw = extract_phase_amp_bw(rootpath, sub, ses, 
                                                               chan, stage, adap_bw,
                                                               adap_bands_phase, 
                                                               frequency_phase,
                                                               adap_bands_amplitude, 
                                                               frequency_amplitude,
                                                               tracking, logger)
                
                pac_name = pac_name.replace("**", phase_bw).replace("##", amp_bw)
                data_file = f'{xml_dir}/{sub}/{ses}/{sub}_{ses}_{chan}_{stagename}_{cycle}_{pac_name}_parameters.csv'
                df.loc[sub] = extract_pac_data(data_file, model, variables, logger)
                flag += df.loc[sub].isna().any()
            df.to_csv(f"{out_dir}/{pac_outname}_{model}/{out_filename}")

    elif model == 'per_stage':
        for st in stage:
            st_columns = [x + f'_{st}' for x in columns]
            logger.debug(f'Collating PAC parameters from {chan}, {st}..')
            df = DataFrame(index=subs, columns=st_columns, dtype=float) 
            out_filename = f'{ses}_{chan}_{st}_{pac_outname}.csv'
            for s, sub in enumerate(subs): 
                logger.debug(f'Extracting from {sub}, {ses}')
                
                phase_bw, amp_bw = extract_phase_amp_bw(rootpath, sub, ses, 
                                                               chan, stage, adap_bw,
                                                               adap_bands_phase, 
                                                               frequency_phase,
                                                               adap_bands_amplitude, 
                                                               frequency_amplitude,
                                                               tracking, logger)
                
                pac_name = pac_name.replace("**", phase_bw).replace("##", amp_bw)
                data_file = f'{xml_dir}/{sub}/{ses}/{sub}_{ses}_{chan}_{st}_{pac_name}_parameters.csv'
                df.loc[sub] = extract_pac_data(data_file, model, variables, logger)
                flag += df.loc[sub].isna().any()
            df.to_csv(f"{out_dir}/{pac_outname}_{model}/{out_filename}")

    return flag
 
    
def extract_phase_amp_bw(rootpath, sub, ses, ch, stage, adap_bw,
                            adap_bands_phase, frequency_phase, 
                            adap_bands_amplitude, frequency_amplitude,
                            tracking, logger = create_logger("Extract Phase Amplitude Bandwidths")):
    
    def get_band(band_type, method, freq_range, label):
        if method == 'Fixed':
            band = freq_range
        elif method == 'Manual':
            chansheet = read_tracking_sheet(rootpath, logger)
            oldchans = reverse_chan_lookup(sub, ses, chansheet, logger)
            fnamechan = oldchans[ch]
            band = read_manual_peaks(rootpath, sub, ses, fnamechan, adap_bw, logger)
        elif method == 'Auto':
            stagename = '-'.join(stage)
            band_limits = f'{freq_range[0]}-{freq_range[1]}Hz'
            band = load_adap_bands(tracking['fooof'], sub, ses, ch,
                                   stagename, band_limits, adap_bw, logger)
        else:
            raise ValueError(f"Unknown {label} method: {method}")
        return band

    # Get phase and amplitude frequency bands
    f_pha = get_band('phase', adap_bands_phase, frequency_phase, 'phase')
    if not f_pha:
        f_pha = frequency_phase
    f_amp = get_band('amplitude', adap_bands_amplitude, frequency_amplitude, 'amplitude')
    if not f_amp:
        f_amp = frequency_amplitude
    
    # Format names
    phase_bw = f'pha-{round(f_pha[0], 2)}-{round(f_pha[1], 2)}Hz'
    amp_bw = f'amp-{round(f_amp[0], 2)}-{round(f_amp[1], 2)}Hz'

    return phase_bw, amp_bw



def extract_data_error(logger = create_logger(" ")):
    logger.critical("Data extraction error: Check that all 'params' are written correctly.")
    logger.info('                      Check documentation for how event parameters need to be written:')
    logger.info('                      https://seapipe.readthedocs.io/en/latest/index.html')
    


def extract_pac_data(data_file, model, variables, logger = create_logger("Extract PAC data")):
    
    data = []
    if not path.exists(data_file):
        logger.warning(f"{data_file} not found. Has pac been run for {model}, "
                       "with these frequency bands?")
        data = full(len(variables), nan)
    else:
        try:
            # Read csv
            df = read_csv(data_file, header=0)
            
            # PAC variables
            if 'mi_raw' in variables:
                data.append(df['mi_raw'][0])
            if 'mi_norm' in variables:
                data.append(df['mi_norm'][0])
            if 'pval1' in variables:
                data.append(df['pval1'][0])              
            if 'pp_radians' in variables:
                data.append(df['pp_radians'][0])               
            if 'ppdegrees' in variables:
                data.append(df['ppdegrees'][0])
            if 'mvl' in variables:
                data.append(df['mvl'][0])					
            data = asarray(data)
        except:
            extract_data_error(logger)  
            data = full(len(variables), nan)

    return data
    
    
def extract_event_data(data_file, variables):
    
    # Delimiter
    data_file_delimiter = ','
    
    # The max column count a line in the file could have
    largest_column_count = 0
    
    # Loop the data lines
    with open(data_file, 'r') as temp_f:
        # Read the lines
        lines = temp_f.readlines()
    
        for l in lines:
            # Count the column count for the current line
            column_count = len(l.split(data_file_delimiter)) + 1
            
            # Set the new most column count
            largest_column_count = column_count if largest_column_count < column_count else largest_column_count
    
    # Generate column names (will be 0, 1, 2, ..., largest_column_count - 1)
    column_names = [i for i in range(0, largest_column_count)]
    
    # Read csv
    df = read_csv(data_file, header=None, delimiter=data_file_delimiter, 
                  names=column_names, index_col=0)
    
    data = []
    if 'Count' in variables:
        data.append(float(df.loc['Count'][1]))
    if 'Density' in variables:
       data.append(round(float(df.loc['Density'][1]),3))
       
       
    df = read_csv(data_file, skiprows=3, header=0, delimiter=data_file_delimiter, 
                   index_col=0)
    
    if 'Duration_mean' in variables:
        data.append(df['Duration (s)'].loc['Mean'])
    if 'Duration_stdv' in variables:
        data.append(df['Duration (s)'].loc['SD'])
    
    if 'Min_amplitude_mean' in variables:
        data.append(df['Min. amplitude (uV)'].loc['Mean'])
    if 'Min_amplitude_stdv' in variables:
        data.append(df['Min. amplitude (uV)'].loc['SD'])
    
    if 'Max_amplitude_mean' in variables:
        data.append(df['Max. amplitude (uV)'].loc['Mean'])
    if 'Max_amplitude_stdv' in variables:
        data.append(df['Max. amplitude (uV)'].loc['SD'])
        
    if 'Ptp_amplitude_mean' in variables:
        data.append(df['Peak-to-peak amplitude (uV)'].loc['Mean'])
    if 'Ptp_amplitude_stdev' in variables:
        data.append(df['Peak-to-peak amplitude (uV)'].loc['SD'])
        
    if 'Power_mean' in variables:
        data.append(df['Power (uV^2)'].loc['Mean'])
    if 'Power_stdev' in variables:
        data.append(df['Power (uV^2)'].loc['SD'])
        
    if 'Peak_power_frequency_mean' in variables:
        data.append( df['Peak power frequency (Hz)'].loc['Mean'])
    if 'Peak_power_frequency_std' in variables:
        data.append(df['Peak power frequency (Hz)'].loc['SD'])
    
    
    data = asarray(data)

    return data
    

def extract_cluster_data(data_file, variables):
    
    # Delimiter
    data_file_delimiter = ','
    
    # Read csv
    df = read_csv(data_file, index_col=0, delimiter=data_file_delimiter)
    
    data = []
    for col in df.columns:
        if col in variables:
            data.append(df.loc[0,col])
            
    return data

        
    
def trawls():
    
    '''
        Tabulating and Reordering Aggregated WhoLe Statistics (TRAWLS)
        
        Function to combine multiple datasets together into 1.
    '''
    
    return    
    