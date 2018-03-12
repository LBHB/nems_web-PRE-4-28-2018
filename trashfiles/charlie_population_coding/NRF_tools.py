'''

Tools for fitting neural receptive field (NRF) model

created CRH 09_20_2017

'''

import numpy as np
import numpy.linalg as la
import pandas as pd
import sys
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split

import sklearn as sk
from sklearn.decomposition import NMF
import numpy as np
from tqdm import tqdm
from scipy.ndimage.filters import gaussian_filter1d

sys.path.append('/auto/users/hellerc/nems/nems/utilities')
from utils import crossval_set
from pop_utils import whiten
def get_weight_mat(r, lag=1, fs=1):
    '''
    Args
    ---------------------------------
    r (numpy array, required): 4-D array of cell responses (bins x reps x stim x cells)
                               or 2-D array where dims: (bins*reps*stim x cells)
    lags (int, optional): Time (s) over which to perform reverse correlation.
                          Default is to only do correlation at current time bin
    fs (int): sampling frequency of the r matrix
    Output
    ---------------------------------
    h (numpy array): 3-D array containing the relative weight between all pairs of
                     neurons (cells X lags X weights) - 2-D if lags not specified
    '''
    if lag!=1 and fs==1:
        sys.exit('Must specify sampling frequency')
    lags = int(lag*fs)
    if len(r.shape) > 2:
        bincount = r.shape[0]
        repcount = r.shape[1]
        stimcount = r.shape[2]
        cellcount = r.shape[3]
        r = r.reshape(bincount*stimcount*repcount, cellcount)
    else:
        cellcount = r.shape[1]

    h = np.empty((cellcount, lags, cellcount-1))
    for i in range(0,cellcount):
        neuron = r[:,i]
        r_temp = np.delete(r, i, 1)
        Css = np.matmul(r_temp.T, r_temp)/len(r_temp)
        for j in range(0, lags):
            Csr = np.matmul(r_temp.T, np.roll(neuron, j))/len(r_temp)
            h_temp = np.matmul(la.inv(Css).T, Csr)
            h[i,j,:] = np.concatenate((h_temp[0:i], h_temp[i:len(h_temp)]))

    return np.squeeze(h)

def get_single_lag_wm(r,lag=0,fs=0):
    '''
    Args
    ---------------------------------
    r (numpy array, required): 4-D array of cell responses (bins x reps x stim x cells)
                               or 2-D array where dims: (bins*reps*stim x cells)
    lags (int, optional): Time (s) over which to perform reverse correlation.
                          Default is to only do correlation at current time bin
    fs (int): sampling frequency of the r matrix
    Output
    ---------------------------------
    h (numpy array): 2-D array containing the relative weight between all pairs of
                     neurons (cells X weights) at the specified time lag 
    '''
    if lag!=0 and fs==0:
        sys.exit('Must specify sampling frequency')
    lag = int(lag*fs)
    if len(r.shape) > 2:
        bincount = r.shape[0]
        repcount = r.shape[1]
        stimcount = r.shape[2]
        cellcount = r.shape[3]
        r = r.reshape(bincount*stimcount*repcount, cellcount)
    else:
        cellcount = r.shape[1]

    h = np.empty((cellcount, cellcount-1))
    for i in range(0,cellcount):
        neuron = r[:,i]
        r_temp = np.delete(r, i, 1)
        Css = np.matmul(r_temp.T, r_temp)/len(r_temp)
        Csr = np.matmul(r_temp.T, np.roll(neuron, lag))/len(r_temp)
        h_temp = np.matmul(la.inv(Css).T, Csr)
        h[i,:] = np.concatenate((h_temp[0:i], h_temp[i:len(h_temp)]))

    return np.squeeze(h)

def get_PSTH(r):
    '''
    Args
    -----------------------------------------
    r (numpy array): 4-D array of cell responses (bins x reps x stim x cells),

    Output
    -----------------------------------------
    psth (numpy array): bincount x stims x cells psth array
    '''
    bincount = r.shape[0]
    repcount = r.shape[1]
    stimcount = r.shape[2]
    cellcount = r.shape[3]

    psth = np.empty((bincount, stimcount, cellcount))
    for stim in range(0,stimcount):
        for cell in range(0, cellcount):
            psth[:,stim, cell] = np.squeeze(np.mean(r[:,:,stim, cell],1))
    return psth

def NRF_fit(r, r0_strf=None, cv_count=10, lag=1, fs=1, single_lag=False, model=None, spontonly=None, shuffle=True):
    '''
    Function fits full model (rN + r0), rN only, or r0 only and returns the
    array of predicted responses for the model of choice.

    Args
    -------------------------------------------
    r (numpy array, required): 4-D (or 3-D) array of cell responses (bins x reps x stim x cells)
    r0_strf (numpy array, required if model = NRF_STRF): 3-D array of strf precited responses to PPS stims
    trialset (float): Fraction of data to be used as the trial set. Default is 0.8
    lag (int, optional): Time (s) over which to perform reverse correlation.
                          Default is to only do correlation at current time bin
    fs (int): sampling freq uency of the r matrix
    model (string): String specifying which model you'd like to use for the fit
                            NRF_only
                            PSTH_only
                            NRF_PSTH
    Output
    --------------------------------------------
    r_fit: 4-D arrays of predicted neural responses during test set
    '''
    if spontonly==None:
        sys.exit('must specify if spontonly')
    if model == 'NRF_STRF' and r0_strf == None:
        sys.exit('must provide null model (strf)')
    bincount = r.shape[0]
    repcount = r.shape[1]
    if len(r.shape) == 4:
        stimcount = r.shape[2]
        cellcount = r.shape[3]
    elif len(r.shape) == 3:
        cellcount = r.shape[2]
        
    psth = get_PSTH(r)
    rdiff = r - np.tile(psth[:,np.newaxis,:,:], [1,repcount, 1, 1])
    train_idx, test_idx = crossval_set(repcount, cv_count=cv_count, interleave_valtrials=shuffle)
    prediction = np.empty(r.shape)
    for i in range(0, len(train_idx)):
# ======================== pulling train/test sets ============================
        r_train = r[:,train_idx[i],:,:]
        rdiff_train = rdiff[:,train_idx[i],:,:]
        r_test = r[:,test_idx[i],:,:]
        rdiff_test = rdiff[:,test_idx[i],:,:]

        pred = np.empty((r_test.shape[0]*r_test.shape[1]*r_test.shape[2], cellcount))
# ============================== fitting models ==============================
        if model == 'NRF_only':
            if single_lag:
                h = get_single_lag_wm(r_train,lag=lag,fs=fs)
            else:
                h = get_weight_mat(r_train,lag=lag,fs=fs)
            for neuron in range(0, cellcount):
                stim = r_test.reshape(bincount*len(test_idx[i])*stimcount, cellcount)
                stim = np.delete(stim,neuron,1)
                h_neuron = h[neuron,:]
                pred[:, neuron] = np.matmul(np.squeeze(h_neuron),stim.T)

        elif model == 'PSTH_only':
            pred = get_PSTH(r_train)
            pred = np.tile(pred[:,np.newaxis,:,:], [1,len(test_idx[i]),1,1])
            pred = pred.reshape(bincount*len(test_idx[i])*stimcount, cellcount)

        elif model == 'NRF_PSTH':
            if spontonly:
                if single_lag:
                    h = get_single_lag_wm(r_train,lag=lag,fs=fs)
                else:
                    h = get_weight_mat(r_train,lag=lag,fs=fs)
            else:
                if single_lag:
                    h = get_single_lag_wm(rdiff_train,lag=lag,fs=fs)
                else:
                    h = get_weight_mat(rdiff_train,lag=lag,fs=fs)
            psth_stim = get_PSTH(r_train)
            psth_stim = np.tile(psth_stim[:,np.newaxis,:,:], [1,len(test_idx[i]),1,1])
            psth_stim = psth_stim.reshape(bincount*len(test_idx[i])*stimcount, cellcount) # making psth prediciton
            for neuron in range(0, cellcount):
                if spontonly:
                    stim = r_test.reshape(bincount*len(test_idx[i])*stimcount, cellcount)
                else:
                    stim = rdiff_test.reshape(bincount*len(test_idx[i])*stimcount, cellcount)
                stim = np.delete(stim, neuron,1)
                h_neuron = h[neuron, :]
                pred[:, neuron] = np.matmul(np.squeeze(h_neuron),stim.T) + psth_stim[:,neuron]
        elif model == 'NRF_STRF':
            
            if len(r0_strf.shape)>3:
                r0 = r0_strf[:,0:len(test_idx[i]),:,:]
                r0 = r0.reshape(bincount*len(test_idx[i])*stimcount, cellcount)
                r_train = r[:,train_idx[i],:,:] - r0_strf[:,train_idx[i],:,:]
                r_test = r[:,test_idx[i],:,:] - r0_strf[:,test_idx[i],:,:]
                if single_lag:
                    h = get_single_lag_wm(r_train,lag=lag,fs=fs)
                else:
                    h = get_weight_mat(r_train,lag=lag,fs=fs)
                for neuron in range(0, cellcount):
                    stim = r_test.reshape(bincount*len(test_idx[i])*stimcount, cellcount)
                    stim = np.delete(stim, neuron,1)
                    h_neuron = h[neuron,:]
                    pred[:,neuron]=np.matmul(np.squeeze(h_neuron),stim.T)+r0[:,neuron]    
            else:               
                r0 = r0_strf.reshape(bincount*repcount, cellcount)
                r_train = r[:,train_idx[i],:] - r0_strf[:,train_idx[i],:]
                r_test = r[:,test_idx[i],:] - r0_strf[:,test_idx[i],:]
                h = get_weight_mat(r_train,lag=lag,fs=fs)
                for neuron in range(0, cellcount):
                    stim = r_test.reshape(bincount*len(test_idx[i]), cellcount)
                    stim = np.delete(stim, neuron,1)
                    h_neuron = h[neuron,:]
                    pred[:,neuron]=np.matmul(np.squeeze(h_neuron),stim.T)+r0[:,neuron]
        else:
            sys.exit('specify a model selection')
# =========================== Save predictions =================================
# ========================== Sort predictions ==================================
        prediction[:,test_idx[i],:,:] = pred.reshape(bincount, len(test_idx[i]), stimcount, cellcount)
    return prediction



def eval_fit(r, rpred):
    '''
    Given the true dataset and predicted data set, this functio will evalute the
    performance of the prediction using pearson correlation coefficient

    Args:
    -------------------------------------------------
    r (numpy array, required): 4-D array of cell responses (bins x reps x stim x cells)
    rpred (numpy array, required): 4-D array of predicted cell responses (bins x reps x stim x cells)
    Output
    --------------------------------------------------
    coeff (dictionary):
        mean (numpy array): correlation coeff across all trials and stims for each cell
        bytrial: (numpy array): reps x stim x cell array of corr coefs for each trial/stim/cell
    '''
    bincount = r.shape[0]
    repcount = r.shape[1]
    if len(r.shape) == 4:
        stimcount = r.shape[2]
        cellcount = r.shape[3]    
    elif len(r.shape)==3:
        stimcount = 1
        cellcount = r.shape[2]
        r = r[:,:,np.newaxis,:]
        rpred = rpred[:,:,np.newaxis,:]
    coeff = dict()
    coeff['mean'] = np.empty(cellcount)
    for i in range(0, cellcount):
        coeff['mean'][i] = (np.corrcoef(r.reshape(bincount*repcount*stimcount, cellcount)[:,i],
        rpred.reshape(bincount*repcount*stimcount, cellcount)[:,i])[0][1])

    coeff['bytrial'] = np.empty((repcount, stimcount, cellcount))
    for cell in range(0, cellcount):
        for rep in range(0, repcount):
            for stim in range(0, stimcount):
                coeff['bytrial'][rep, stim, cell] = np.corrcoef(r[:,rep,stim,cell], rpred[:,rep,stim,cell])[0][1]
    return coeff

def sort_bytrial_voc(r, p, data):
    '''
    takes r, and data object (with resp, pupil, stim info, etc.) sorts into trials defined
    by stim type,
    '''
    bincount =r.shape[0]
    trialcount = r.shape[2]
    cellcount = r.shape[-1]
    stimids = data['stimids']

    stim2 = int(max(stimids))
    repcount = int(trialcount/stim2)
    rbystim = np.empty((bincount, stim2, repcount, cellcount))
    pbystim = np.empty((bincount, stim2, repcount))
    for stim in range(0, stim2):
        inds = [t[0] for t in np.argwhere(stimids==(stim+1))]
        rbystim[:,stim, :, :]=np.squeeze(r[:,0,inds,:])
        pbystim[:,stim,:]=np.squeeze(p[:,0,inds])
    rbystim = np.transpose(rbystim, (0, 2, 1, 3))
    pbystim = np.transpose(pbystim, (0, 2, 1))
    return pbystim, rbystim
    
    
def plt_perf_by_trial(r, r1, r2, combine_stim=False, a_p=None, r1name='Network', r2name='Null', cellname=None, **kwargs):
    '''
    Function to visualize the performance of two models over trials. "Trials has
    a flexible meaning. This function assumes you input data in which the first 
    dimension is time and the last dimension is cells. It will simply collapse 
    over whatever is in between these two dims and call this trials. 
    
    THEREFORE, IF FOR EXAMPLE YOU'D LIKE TO SEE THE PLOT FOR A SINGLE CELL, 
    YOU MUST MAKE SURE THE LAST DIM OF RESPONSE MATRIX IS A SINGLETON
    
    Input:
        r: numpy array (4-D or 3-D), true response matrix (required) - will assume time is first dimension, cells are last dim
        r1: numpy array (4-D or 3-D), predicted response matrix (required) - will assume time is first dimension, cells are last dim
        r2: numpy array (4-D or 3-D), predicted response matrix (required) - will assume time is first dimension, cells are last dim
        combine_stim: bool (whether or not to average over all stims)
        a_p: boolean specifying trial type (size: Middle dimensions collapses of response matrix) (optional - must specify if behavior)
        r1name: string (optional, default "Network)
        r2name: string (optional, default "Null")
        cellname: string (optional, will be title of graph if included)
        kwargs:
            pupil: numpy array, pupil matrix (optional)
            pop_state: string ('PCA', 'NNMF') - dimensionality reduction. 
            If it exists, compare state variables with pupil (if exists) and model performance
            
    Output - none
        <matplotlib fig>
    
        Note - if you want the correlation coefficients for model prediciton, use
        function "NRF_tools.eval_fit"
    '''
    if combine_stim==True:
        r1_perf = np.nanmean(np.nanmean(eval_fit(r, r1)['bytrial'],1),-1)
        r2_perf = np.nanmean(np.nanmean(eval_fit(r, r2)['bytrial'],1),-1)
    
    else:
        if len(r.shape)==4:
            r1_perf = np.nanmean(eval_fit(r, r1)['bytrial'],-1).reshape(r.shape[1]*r.shape[2])
            r2_perf = np.nanmean(eval_fit(r, r2)['bytrial'],-1).reshape(r.shape[1]*r.shape[2])
        else:
            r1_perf = np.nanmean(eval_fit(r, r1)['bytrial'],-1)
            r2_perf = np.nanmean(eval_fit(r, r2)['bytrial'],-1)
        
    if len(r1_perf.shape)==3 and combine_stim==False:
        r1_perf = np.nanmean(r1_perf.reshape(r1_perf.shape[0]*r1_perf.shape[1], r1_perf.shape[2]),-1)
        r2_perf = np.nanmean(r2_perf.reshape(r2_perf.shape[0]*r2_perf.shape[1], r2_perf.shape[2]),-1)

    
    
    if 'pop_state' in kwargs:
        nplots1=3
        nplots2=2
        p1=1
        p2=3
        p3=5
    else:
        nplots1=2
        nplots2=1
        p1 = 1
        p2 = 2
        p3 = 3
        
    if 'pupil' in kwargs.keys():
        pupil = kwargs['pupil']
        if len(pupil.shape)==3 and combine_stim==True:
            pupil = np.mean(np.mean(pupil,-1),0)/2
        elif len(pupil.shape)==3 and combine_stim==False:
            pupil = np.mean(pupil,0).reshape(pupil.shape[1]*pupil.shape[2])/2
        else:
            pupil=np.mean(pupil,0)/2
     
    
    fig = plt.figure()   
    # If behavior
    if a_p is not None:
        if 'pupil' in kwargs:
            plt.subplot(nplots1,nplots2,p1)
            plt.plot(r1_perf, '.-', color='red', alpha=0.7)
            plt.plot(r2_perf, '.-', color='blue', alpha=0.7)
            plt.legend([r1name,r2name],loc='upper right')
            plt.xlabel('Trials')
            plt.ylabel('Model Performance - correlation coefficient')
            
            plt.subplot(nplots1,nplots2,p2)
            plt.plot(pupil-np.mean(pupil)+np.mean(r1_perf-r2_perf), '.-',color='k',alpha=0.7)
            plt.plot(r1_perf-r2_perf, '.-',color='green')
            plt.legend(['Model diff', 'Pupil'],loc='upper right')
            plt.title('Model vs. pupil: %s' %(round(np.corrcoef(pupil,r1_perf-r2_perf)[0][1],2)))
            plt.xlabel('Trials')
            plt.ylabel('Model Performance - correlation coefficient')
        else:
            plt.subplot(nplots1,nplots2,p1)
            plt.plot(r1_perf, '.-', color='red', alpha=0.7)
            plt.plot(r2_perf, '.-', color='blue', alpha=0.7)
            plt.legend([r1name,r2name],loc='upper right')
            plt.xlabel('Trials')
            plt.ylabel('Model Performance - correlation coefficient')
            
            plt.subplot(nplots1, nplots2, p2)
            plt.plot(r1_perf-r2_perf, '.-',color='green',alpha=0.7)
            plt.legend(['Model diff'],loc='upper right')
            plt.xlabel('Trials')
            plt.ylabel('Model Performance - correlation coefficient')
            
        starts = np.argwhere(np.diff(a_p)==1)
        ends = np.argwhere(np.diff(a_p)==-1)
        if len(starts)>len(ends):
            ends=np.append(ends,len(a_p)-1)
        elif len(ends)>len(starts):
            starts=np.insert(starts,0,0)
        for i in range(0, len(starts)):
            plt.subplot(nplots1,nplots2,p1)
            plt.axvspan(starts[i],ends[i],color='k',alpha=0.2)
            plt.subplot(nplots1,nplots2,p2)
            plt.axvspan(starts[i],ends[i],color='k',alpha=0.2)
            plt.xlabel('Trials')
            plt.ylabel('Model Performance - correlation coefficient')
    else:
         if 'pupil' in kwargs:
            plt.subplot(nplots1,nplots2,p1)
            plt.plot(r1_perf, '.-', color='red', alpha=0.7)
            plt.plot(r2_perf, '.-', color='blue', alpha=0.7)
            plt.legend([r1name,r2name],loc='upper right')
            plt.xlabel('Trials')
            plt.ylabel('Model Performance - correlation coefficient')
            
            plt.subplot(nplots1,nplots2,p2)
            plt.plot(pupil-np.mean(pupil)+np.mean(r1_perf-r2_perf), '.-',color='k',alpha=0.7)
            plt.plot(r1_perf-r2_perf, '.-',color='green')
            plt.legend(['Model diff', 'Pupil'],loc='upper right')
            plt.title('Model vs. pupil: %s' %(round(np.corrcoef(pupil,r1_perf-r2_perf)[0][1],2)))
            plt.xlabel('Trials')
            plt.ylabel('Model Performance - correlation coefficient')
         else:
            plt.subplot(nplots1,nplots2,p1)
            plt.plot(r1_perf, '.-', color='red', alpha=0.7)
            plt.plot(r2_perf, '.-', color='blue', alpha=0.7)
            plt.legend([r1name,r2name],loc='upper right')
            plt.xlabel('Trials')
            plt.ylabel('Model Performance - correlation coefficient')
            
            plt.subplot(nplots1,nplots2,p2)
            plt.plot(r1_perf-r2_perf, '.-',color='green',alpha=0.7)
            plt.legend(['Model diff'],loc='upper right')
            plt.xlabel('Trials')
            plt.ylabel('Model Performance - correlation coefficient')
    
    if cellname is not None:
        plt.suptitle(cellname)
        
        
    if 'pop_state' in kwargs:
        method = kwargs['pop_state']['method']
        dims = kwargs['pop_state']['dims']
        if method == 'SVD':
            if len(r.shape)==3:
                resp_pca = (whiten(r).reshape(r.shape[0]*r.shape[1], r.shape[2]))
                U,S,V = np.linalg.svd(resp_pca,full_matrices=False)
                pcs_reshaped=np.nanmean(U.reshape(r.shape[0],r.shape[1],r.shape[-1]),0)
    
                    
            elif len(r.shape)==4:
                resp_pca = (whiten(r).reshape(r.shape[0]*r.shape[1]*r.shape[2], r.shape[3]))
                U,S,V = np.linalg.svd(resp_pca,full_matrices=False)
                
                if combine_stim:
                    pcs_reshaped=np.nanmean(np.nanmean(U.reshape(r.shape[0],r.shape[1],r.shape[2],r.shape[-1]),0),2)
                else:
                    pcs_reshaped=np.nanmean(U.reshape(r.shape[0],r.shape[1]*r.shape[2],r.shape[-1]),0)
        
            plt.subplot(nplots1, nplots2, p3)
            for i in range(0, dims):
                plt.plot(pcs_reshaped[:,i]+np.mean(pcs_reshaped)*10*i)
            pup_corr = []
            mod_corr = []
            beh_corr=[]
            legend=[]
            for i in range(0,dims):
                pup_corr.append(np.corrcoef((pcs_reshaped[:,i],pupil))[0][1])
                mod_corr.append(np.corrcoef((pcs_reshaped[:,i],r1_perf-r2_perf))[0][1])
                beh_corr.append(np.corrcoef((pcs_reshaped[:,i],a_p))[0][1])
                legend.append('LV'+str(i+1)+',   pup: '+str(round(pup_corr[i],2))+',  model: ' + str(round(mod_corr[i],2))+',  behavior: ' 
                              +str(round(beh_corr[i],2)))
            #plt.legend(legend,loc='upper right')
            plt.suptitle('Principle components')
            
            plt.subplot(nplots1,nplots2,2)
            plt.title('Pupil')
            plt.ylabel('Corr coef')
            plt.bar(range(0,dims),abs(np.array(pup_corr)))
            plt.subplot(nplots1,nplots2,4)
            plt.title('Coupling')
            plt.ylabel('Corr coef')
            plt.bar(range(0,dims),abs(np.array(mod_corr)))            
            plt.subplot(nplots1,nplots2,6)
            plt.title('Behavior')
            plt.ylabel('Corr coef')
            plt.xlabel('LVs')
            plt.bar(range(0,dims),abs(np.array(beh_corr)))
        
        
        elif method=='NNMF':
            model=NMF(n_components=dims,init='nndsvd')
            
            if len(r.shape)==3:
                resp_nnmf = r.reshape(r.shape[0]*r.shape[1], r.shape[2]) 
                W = model.fit_transform(resp_nnmf)
                W=np.nanmean(W.reshape(r.shape[0],r.shape[1],dims),0)
    
                    
            elif len(r.shape)==4:
                resp_nnmf = r.reshape(r.shape[0]*r.shape[1]*r.shape[2], r.shape[3]) 
                W = model.fit_transform(resp_nnmf)
                
                if combine_stim:
                    W_reshaped=np.nanmean(np.nanmean(W.reshape(r.shape[0],r.shape[1],r.shape[2],dims),0),2)
                else:
                    W_reshaped=np.nanmean(W.reshape(r.shape[0],r.shape[1]*r.shape[2],dims),0)
                    
            plt.subplot(nplots1, nplots2, p3)
            for i in range(0, dims):            
                plt.plot(W_reshaped[:,i] + np.mean(W_reshaped)*i)
            pup_corr = []
            mod_corr = []
            beh_corr=[]
            legend=[]
            for i in range(0,dims):
                pup_corr.append(np.corrcoef((W_reshaped[:,i],pupil))[0][1])
                mod_corr.append(np.corrcoef((W_reshaped[:,i],r1_perf-r2_perf))[0][1])
                beh_corr.append(np.corrcoef((W_reshaped[:,i],a_p))[0][1])
                legend.append('LV'+str(i+1)+',   pup: '+str(round(pup_corr[i],2))+',  model: ' + str(round(mod_corr[i],2))+',  behavior: ' 
                              +str(round(beh_corr[i],2)))
            #plt.legend(legend,loc='upper right')
            plt.suptitle('Non-negative matrix factorization')
            
            plt.subplot(nplots1,nplots2,2)
            plt.title('Pupil')
            plt.ylabel('Corr coef')
            plt.bar(range(0,dims),abs(np.array(pup_corr)))
            plt.subplot(nplots1,nplots2,4)
            plt.title('Coupling')
            plt.ylabel('Corr coef')
            plt.bar(range(0,dims),abs(np.array(mod_corr)))            
            plt.subplot(nplots1,nplots2,6)
            plt.title('Behavior')
            plt.ylabel('Corr coef')
            plt.bar(range(0,dims),abs(np.array(beh_corr)))
    

    return fig
    







# ====== First pass at dealing with nans and cont. data, just re-writing=======
#=======                the above functions to handle nans              =======



def NRF_fit_continuous(r, r0_strf, cv_count=10, lag=1, fs=1, single_lag=False, spontonly=None, shuffle=True):
    '''
    Function fits full model (rN + r0), rN only, or r0 only and returns the
    array of predicted responses for the model of choice.

    Args
    -------------------------------------------
    r (numpy array, required): 4-D (or 3-D) array of cell responses (bins x reps x stim x cells)
    r0_strf (numpy array, required if model = NRF_STRF): 3-D array of strf precited responses to PPS stims
    trialset (float): Fraction of data to be used as the trial set. Default is 0.8
    lag (int, optional): Time (s) over which to perform reverse correlation.
                          Default is to only do correlation at current time bin
    fs (int): sampling freq uency of the r matrix
    model (string): String specifying which model you'd like to use for the fit
                            NRF_only
                            PSTH_only
                            NRF_PSTH
    Output
    --------------------------------------------
    r_fit: 4-D arrays of predicted neural responses during test set
    '''
    if spontonly==None:
        sys.exit('must specify if spontonly')

    if len(r.shape)==4 and r.shape[0]==1:
        r = r.squeeze()
        r0_strf = r0_strf.squeeze()
    elif len(r.shape)==4 and r.shape[0]!=1:
        sys.exit('Dont know how to handle this case')
        
    repcount = r.shape[-2]
    bincount=r.shape[0]
    cellcount = r.shape[-1]
        
    train_idx, test_idx = crossval_set(repcount, cv_count=cv_count, interleave_valtrials=shuffle)
    prediction = np.empty(r.shape)
    for i in range(0, len(train_idx)):

        
# ============================== fitting models ==============================
        
        r0 = r0_strf[:,(test_idx[i]),:]
        r0 = r0.reshape(bincount*len(test_idx[i]), cellcount)
        r_train = r[:,train_idx[i],:] - r0_strf[:,train_idx[i],:]
        r_test = r[:,test_idx[i],:] - r0_strf[:,test_idx[i],:]
        pred = np.empty((r_test.shape[0]*r_test.shape[1], cellcount))
        if single_lag:
            h = get_single_lag_wm(r_train,lag=lag,fs=fs)
        else:
            h = get_wm_nans(r_train.squeeze(),lag=lag,fs=fs)
        for neuron in range(0, cellcount):
            stim = r_test.reshape(bincount*len(test_idx[i]), cellcount)
            stim = np.delete(stim, neuron,1)
            h_neuron = h[neuron,:]
            pred[:,neuron]=np.matmul(np.squeeze(h_neuron),stim.T)+r0[:,neuron]    

# =========================== Save predictions =================================
# ========================== Sort predictions ==================================
        prediction[:,test_idx[i],:] = pred.reshape(bincount, len(test_idx[i]), cellcount)
    return prediction  
    
    
def get_wm_nans(r,lag=0,fs=0):
    '''
    Args
    ---------------------------------
    r (numpy array, required): 3-D array of cell responses (bins x reps x cells)
                               or 2-D array where dims: (bins*reps*stim x cells)
    lags (int, optional): Time (s) over which to perform reverse correlation.
                          Default is to only do correlation at current time bin
    fs (int): sampling frequency of the r matrix
    Output
    ---------------------------------
    h (numpy array): 2-D array containing the relative weight between all pairs of
                     neurons (cells X weights) at the specified time lag 
    '''
    if lag!=0 and fs==0:
        sys.exit('Must specify sampling frequency')
    lag = int(lag*fs)
    if len(r.shape) > 2:
        bincount = r.shape[0]
        repcount = r.shape[1]
        cellcount = r.shape[2]
        r = r.reshape(bincount*repcount, cellcount)
    else:
        cellcount = r.shape[1]

    h = np.empty((cellcount, cellcount-1))
    for i in range(0,cellcount):
        neuron = r[~np.isnan(r[:,0]),i]
        r_temp = np.delete(r, i, 1)[~np.isnan(r[:,0]),:]
        Css = np.matmul(r_temp.T, r_temp)/len(r_temp)
        Csr = np.matmul(r_temp.T, np.roll(neuron, lag))/len(r_temp)
        h_temp = np.matmul(la.inv(Css).T, Csr)
        h[i,:] = np.concatenate((h_temp[0:i], h_temp[i:len(h_temp)]))

    return np.squeeze(h)
    
def eval_fit_nans(r, rpred):
    '''
    Given the true dataset and predicted data set, this functio will evalute the
    performance of the prediction using pearson correlation coefficient

    Args:
    -------------------------------------------------
    r (numpy array, required): 4-D array of cell responses (bins x reps x stim x cells)
    rpred (numpy array, required): 4-D array of predicted cell responses (bins x reps x stim x cells)
    Output
    --------------------------------------------------
    coeff (dictionary):
        mean (numpy array): correlation coeff across all trials and stims for each cell
        bytrial: (numpy array): reps x stim x cell array of corr coefs for each trial/stim/cell
    '''
    bincount = r.shape[0]
    repcount = r.shape[1]
    if len(r.shape) == 4:
        stimcount = r.shape[2]
        cellcount = r.shape[3]    
    elif len(r.shape)==3:
        stimcount = 1
        cellcount = r.shape[2]
        r = r[:,:,np.newaxis,:]
        rpred = rpred[:,:,np.newaxis,:]
    coeff = dict()
    coeff['mean'] = np.empty(cellcount)
    for i in range(0, cellcount):
        coeff['mean'][i] = (np.corrcoef(r.reshape(bincount*repcount*stimcount, cellcount)[:,i],
        rpred.reshape(bincount*repcount*stimcount, cellcount)[:,i])[0][1])

    coeff['bytrial'] = np.empty((repcount, stimcount, cellcount))
    for cell in range(0, cellcount):
        for rep in range(0, repcount):
            for stim in range(0, stimcount):
                coeff['bytrial'][rep, stim, cell] = np.corrcoef(r[~np.isnan(r[:,rep,stim,cell]),rep,stim,cell], 
                     rpred[~np.isnan(r[:,rep,stim,cell]),rep,stim,cell])[0][1]
    return coeff
    
    