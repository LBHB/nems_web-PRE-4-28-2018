#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  8 13:59:22 2017

@author: hellerc
"""
'''

Classify all units exported by phy as fast spiking or regular spiking.

In order to run this file, will have to run cell_type.py snippet in .phy beforehand
to export the relevant files into the results folder for your recording
and will have had to save phy sorting to db

cell_type.py is located in LBHB/phy-contrib. Look there for instructions on running
it

===============================================================================

Function: getCellTypes

Based on work by Niell and Stryker, 2008

Classify all sorted units as fast-spiking inhibitory and regular-spiking excitatory
'''

import numpy as np
from sklearn.cluster import KMeans
import pandas as pd
import scipy.io as io

def getCellTypes(fn = None, animal=None, automerged=True):
    '''
    Input:
        fn (string) = filename of spike sorting job. ex: TAR010c_9_10_11_12_96clusts_V2
        animal (string) = animal's name
        automerged (boolean): if automerged results. Default = True
    Output:
        classifiers (pd data frame):
            
        
    '''
    anID = fn.split('_')[0][:-1]
    if automerged:
        resultPath = '/auto/data/daq/'+animal+'/'+anID+'/tmp/KiloSort/'+fn+'/results_after_automerge/'
    else:
        resultPath = '/auto/data/daq/'+animal+'/'+anID+'/tmp/KiloSort/'+fn+'/results/'
        
    
    # Get necessary data from result folder
    mwf = np.load(resultPath+'mwf.npy')
    sw = np.load(resultPath+'spike_width.npy')
    ptr = np.load(resultPath+'peak_trough_ratio.npy')
    bc = np.load(resultPath+'best_channels.npy')
    clusters = pd.DataFrame.from_csv(resultPath+'cluster_group.tsv', sep='\t',header=0)
    mask = []
    for index, i in enumerate(clusters['group']):
        if i == 'good' or i == 'mua':
            mask.append(index)
   
    mwf=mwf[:,mask]
    sw=sw[mask]
    ptr=ptr[mask]
    bc=bc[mask]+1
    
    sw_ptr = np.vstack((sw,ptr)).T
    kmeans = KMeans(n_clusters=2, random_state=0).fit(sw_ptr)
    color=list(kmeans.labels_)
    for i, cat in enumerate(color):
        if cat == 0:
            color[i]='blue'
        else:
            color[i]='red'

    mlist = list()
    for i in range(0, len(sw)):
        temp = {'mean_waveform' : mwf[:,i],
                'spike_width' : sw[i],
                'peak_trough_ratio' : ptr[i],
                'best_channel' : bc[i],
                'reg_spiking' : kmeans.labels_[i]
                }
        mlist.append(temp)
        
    classifiers = pd.DataFrame(mlist)
    classifiers = classifiers.sort_values(by = 'best_channel')
    isolation = io.loadmat(resultPath+'isolation.mat')['isolations']
    classifiers['isolation'] = isolation
    return classifiers

        
        
        
        