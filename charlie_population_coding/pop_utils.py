'''
Functions to interact with .mat file for population data
'''
import scipy.io as spi
import numpy as np
import pandas as pd
import sys
import matplotlib.pyplot as plt

from importlib import reload
import nems.db as ndb
import nems.utilities as ut
import nems.stack as ns
sys.path.append('/auto/users/hellerc/nems/charlie_population_coding/')
from classify_cell_types import getCellTypes
from tqdm import tqdm

def get_data(m):
    '''
    Takes a .mat file as argument. Returns dictionary of data contained in the
    matlab file
    '''
    data = spi.loadmat(m)
    return data

def get_cellids(exp):
    '''
    Input
    ------------------------------------------------------
    exp: Dict created from loading .mat file

    Out
    ------------------------------------------------------
    cellids: (list) list of strings containing cellids
        if there are greater than one experiments, i.e. if the data returned in
        mat file it multidimensional, this will return a list of lists. The
        dimensions matching the shape of data

        For example, will get separate list of cellids for VOC_VOC and PPS_VOC
    '''
    nconds = exp['data'].shape[1]
    cellids = [[]]*nconds
    for i in range(0, nconds):
        cellids[i] = exp['data'][0][i][11][0]
    return cellids

def get_spont_data(r, p, prestim, fs):
    '''
    Input
    -----------------------------------------------------
    r: 4-D array of neural responses
    p: 3-D array of pupil
    prestim: time (in s) of prestim duration
    fs: sampling rate of response
    Out
    -----------------------------------------------------
    spont_data: contains 4-D array containg cell activity
    '''
    r_spont = r[0:int(prestim*fs), :,:,:]
    p_spont = p[0:int(prestim*fs),:,:]
    return r_spont, p_spont


def whiten(r):
    '''
    z-score neuronal responses
    '''
    bincount = r.shape[0]
    repcount = r.shape[1]
    stimcount = r.shape[2]
    if len(r.shape) == 4:
        cellcount = r.shape[3]
        r = r.reshape(r.shape[0]*r.shape[1]*r.shape[2], r.shape[3])
        for i in range(0, cellcount):
            r[:,i] = r[:,i] - np.mean(r[:,i])
            r[:,i] = r[:,i]/np.std(r[:,i])
        r = r.reshape(bincount, repcount, stimcount, cellcount)
    elif len(r.shape) == 3:
        r = r.reshape(r.shape[0]*r.shape[1]*r.shape[2],1)
        r = r - np.mean(r)
        r = r/np.std(r)
        r = r.reshape(bincount, repcount, stimcount)
    return r

def downsample(resp_raster, pup, fs, fs_new):
    '''
    Input:
    resp_raster: 4-D numpy array containing neural responses (bins X reps X stim X neurons)
    pup: 3-D numpy array of pupil area
    fs: int current sampling rate
    fs_new: desired sampling rate
    Output:
    resp_down 4-D numpy array downsampled

    If the requested fs is not possible i.e. can't evenly divide bins, throw error
    '''
    bincount = resp_raster.shape[0]
    stimcount = resp_raster.shape[2]
    repcount = resp_raster.shape[1]
    cellcount = resp_raster.shape[3]
    time = bincount/fs
    if bincount%fs_new != 0:
        sys.exit('requested fs not divisible by original bincount')
    else:
        n_new_bins = int(bincount/(fs/fs_new))
        r = resp_raster.reshape(bincount*stimcount*repcount, cellcount)
        p = pup.reshape(bincount*stimcount*repcount, 1)
        n_comb = int(fs/fs_new)
        rd_temp = np.empty((n_new_bins*stimcount*repcount, cellcount))
        p_temp = np.empty((n_new_bins*stimcount*repcount, 1))
        for i in range(0,cellcount):
            z = 0
            for j in range(0, n_new_bins*repcount*stimcount):
                rd_temp[j, i] = np.mean(np.squeeze(r[z:z+n_comb, i]))
                if j == n_new_bins*repcount*stimcount-1:
                    p_temp[j] = np.mean(np.squeeze(p[z:z+n_comb]))
                z+=n_comb
        return rd_temp.reshape((n_new_bins, repcount, stimcount, cellcount)), p_temp.reshape((n_new_bins, repcount, stimcount))

def load_population_stack(modelname, batch):
    
    meta=ndb.get_batch_cells(batch=301)
    cellids=meta['cellid']
    cell1=meta['cellid'][0]
    stack=ut.io.load_single_model(cell1, batch, modelname)
    
    nfiles = len(stack.data[-1])
    a_p=[]
    stacks=[]
    for j in tqdm(range(1,nfiles,2)):
    
        for i, cellid in (enumerate(cellids)):
            if j == 1:
                stack=ut.io.load_single_model(cellid, batch, modelname)
                stacks.append(stack)
            
            p = stacks[i].data[-1][j]['pred'].copy()
            r = stacks[i].data[-1][j]['resp_raw'].copy()
            if len(r.shape)==2:
                r = r[np.newaxis,:,:]
            if r.shape[0]>1:
                p = np.transpose(np.tile(p, (r.shape[1],1,1)).T, (0,2,1))
          
            pup = stacks[i].data[-1][j]['pupil'].copy()
            
            if i == 0:
                if stack.data[-1][j]['stimparam'][0].find('_a_') > 0:
                    for z in range(0, stack.data[-1][j]['resp_raw'].shape[1]):
                        a_p.append(1)
                else:
                    for z in range(0, stack.data[-1][j]['resp_raw'].shape[1]):
                        a_p.append(0)
        
            if j == 1:
                if i == 0:
                    pred = np.empty((p.shape+ (len(cellids),)))
                    resp = np.empty((r.shape+ (len(cellids),)))
                    pupil = np.empty((pup.shape))
                    ptemp = np.empty((r.shape+(len(cellids),)))
                    rtemp = np.empty((r.shape+(len(cellids),)))
                    pupTemp = np.empty((pup.shape))
                
                pred[:,:,:,i]=p
                resp[:,:,:,i]=r
                pupil[:,:,:]=pup
                
                ptemp[:,:,:,i]=p
                rtemp[:,:,:,i]=r
                pupTemp[:,:,:]=pup
            
            if j > 1:
                if i == 0:
                    ptemp = np.empty((r.shape+(len(cellids),)))
                    rtemp = np.empty((r.shape+(len(cellids),)))
                    pupTemp = np.empty((pup.shape))
                   
                ptemp[:,:,:,i]=p
                rtemp[:,:,:,i]=r
                pupTemp[:,:,:]=pup
    
        if j > 1:
            pred = np.concatenate((pred, ptemp),axis=1)
            resp = np.concatenate((resp, rtemp),axis=1)
            pupil = np.concatenate((pupil, pupTemp),axis=1)
            
                
    
    return resp, pred, pupil
    
    
    
    
    
    
    