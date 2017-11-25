#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 17 23:16:23 2017

@author: svd
"""
import sys
sys.path.append('/auto/users/hellerc/nems')
sys.path.append('/auto/users/hellerc/nems/nems/utilities')
from baphy import load_baphy_file
import imp
import scipy.io
import pkgutil as pk
import os


import nems.modules as nm
import nems.main as main
import nems.fitters as nf
import nems.keyword as nk

import nems.utilities as ut
import nems.stack as ns

import numpy as np
import matplotlib.pyplot as plt
import scipy.signal

imp.reload(nm)
imp.reload(main)
imp.reload(nf)
imp.reload(nk)
imp.reload(ut)
imp.reload(ns)


user = 'david'
passwd = 'nine1997'
host = 'neuralprediction.org'
database = 'cell'
from sqlalchemy import create_engine
db_uri = 'mysql+pymysql://{0}:{1}@{2}/{3}'.format(user, passwd, host, database)
engine = create_engine(db_uri)
f = '/auto/data/code/nems_in_cache/batch299/BOL005c-04-1_b299_none_fs100.mat'
#f = '/auto/data/code/nems_in_cache/batch299/BOL006b-02-1_b299_none_fs100.mat'
data = load_baphy_file(f)
cid = data['cellids'][0]
respfile = os.path.basename(data['resp_fn'][0])
rid = engine.execute('SELECT rawid FROM sCellFile WHERE respfile = "'+respfile+'" and cellid = %s', (cid,))
for obj in rid:
    rawid = str(obj[0])
isolation = 84
chan_unit_cellid = engine.execute('SELECT channum, unit, cellid FROM gSingleRaw WHERE isolation  > %s AND rawid = %s', (isolation,rawid)).fetchall()
chan_unit_cellid = sorted(chan_unit_cellid, key=lambda x: x[0])

keep_ind = []
for i in range(0, len(chan_unit_cellid)):
    keep_ind.append(np.argwhere(data['cellids'] == np.array(chan_unit_cellid)[:,2][i]))

keep_ind = [int(s) for s in keep_ind]

r = data['resp'][:,:,:,keep_ind]
cellids = data['cellids'][keep_ind]

# above code is only used to get list of cell ids. Just using mat files for 
# familiarity and convencience


rvals = []
for i, cellid in enumerate(cellids):
    #cellid='BOL005c-18-1'
    cellid = cellid[0]
    sys.exit()
    batch=293
    modelname= "parm50_wcg02_fir10_dexp_fit01_nested5" #"parm50_wcg02_fir10_pupgainctl_fit01_nested5"
    
    stack=ut.io.load_single_model(cellid, batch, modelname)
    
    #sys.exit('laoded stack for first cell')
    
    '''
    weight_module_idx=ut.utils.find_modules(stack,'filters.weight_channels')
    fir_module_idx=ut.utils.find_modules(stack,'filters.fir')
    val_file_idx=1   #entry in data stack that contains validation set
    
    m_input=stack.modules[1]  # stack that generates the crossval sets
    stim_in=m_input.d_out[val_file_idx]['stim'].copy()
    
    wgt_coefs=stack.modules[weight_module_idx[0]].coefs
    
    m=stack.modules[fir_module_idx[0]]
    '''
    
    #p=m.d_out[val_file_idx]['pred'].copy()
    #r=m.d_out[val_file_idx]['resp'].copy()
    
    p = stack.data[-1][0]['pred'].copy()
    r = stack.data[-1][0]['resp'].copy()
    pup = stack.data[-1][0]['pupil'].copy()
    pup = pup.T
    
    if i == 0:
        pred = np.empty((r.shape[1], r.shape[0], len(cellids)))
        resp = np.empty((r.shape[1], r.shape[0], len(cellids)))
        
    #pup=m.d_out[val_file_idx]['pupil'].copy().T
    #fir_coefs=m.coefs
    #strf_baseline=m.baseline  # h0 in Taylor series expansion
    
    #strf_coefs=np.matmul(wgt_coefs.T,fir_coefs)  # h1 in Taylor series
    
    pred[:,:,i] = p.T
    resp[:,:,i] = r.T
    
    r_val=stack.meta['r_val']  # test set prediction accuracy
    rvals.append(r_val)
    
sys.path.append('/auto/users/hellerc/nems/charlie_population_coding')    
from NRF_tools import NRF_fit, eval_fit   
rN = NRF_fit(resp[:,:,np.newaxis,:], r0_strf = pred, model='NRF_only', spontonly=0,shuffle=True)
fullModel = np.squeeze(rN) 

cc_rN = np.empty((resp.shape[1], resp.shape[-1]))
cc_r0 = np.empty((resp.shape[1], resp.shape[-1]))
for i in range(0, resp.shape[1]):
    for cell in range(0, resp.shape[-1]):
        cc_rN[i, cell]=np.corrcoef(fullModel[:,i,cell], resp[:,i,cell])[0][1]
        cc_r0[i,cell]=np.corrcoef(pred[:,i,cell], resp[:,i,cell])[0][1]

plt.subplot(211)
plt.plot(np.nanmean(cc_rN,1), '-o', color='r')
plt.plot(np.nanmean(cc_r0,1), '-o', color='b')
plt.ylabel('pearsons corr coef')
plt.xlabel('pip trial')
plt.legend(['rN', 'r0 (strf)'])
pup_m = np.mean(pup,0)/2
plt.title('rN vs. pupil: %s, r0 vs. pupil: %s' 
          %(np.corrcoef(np.nanmean(cc_rN,1), pup_m)[0][1], np.corrcoef(np.nanmean(cc_r0,1), pup_m)[0][1]))

diff = np.nanmean(cc_rN,1)-np.nanmean(cc_r0,1)
plt.subplot(212)
plt.plot(pup_m,'-o', color='k', alpha=0.5, lw=2)
plt.plot(diff, '-o', color='g')
plt.legend(['pup', 'rN-r0'])
plt.xlabel('pip trials')
plt.title('corr coef btwn rN-r0 and pupil: %s' 
          %(np.corrcoef(diff, pup_m)[0][1]))



print('Comparing different models...')
def onpick3(event):
    ind = event.ind
    print('onpick3 scatter:', cellids[ind][0])
    
rN_perf = eval_fit(resp, fullModel)
r0_perf = eval_fit(resp, pred)

x = np.linspace(-1,1,3)
ncols = 8
nrows = 10
cellcount = resp.shape[-1]
repcount = resp.shape[1]
bincount = resp.shape[0]
spontonly=0
fs=100
stim=0
color = np.arange(cellcount)
fig = plt.figure()
for rep in range(0, repcount):
    ax = fig.add_subplot(nrows,ncols,rep+1)
    ax.scatter(r0_perf['bytrial'][rep,stim,:], rN_perf['bytrial'][rep,stim,:], c=color,s=10,picker=True)
    ax.plot(x, x, '-k',lw=2)
    ax.axis([-.1,1,-.1,1])
    ax.set_title(rep+1, fontsize=7)
    fig.canvas.mpl_connect('pick_event',onpick3)
    if rep != (ncols*nrows - ncols):
            ax.set_xticks([])
            ax.set_yticks([])
    else:
        ax.set_ylabel('rN')
        ax.set_xlabel('r0')
fig.suptitle('r0 vs. rN for each cell \n stim: %s, rawid: %s, spontonly: %s, fs: %s' %(stim+1, rawid, spontonly, fs))


