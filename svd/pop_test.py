#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 30 11:12:53 2017

@author: svd
"""

import nems.db as ndb
import nems.utilities as nu

import numpy as np
import matplotlib.pyplot as plt
import scipy.signal

batch=301
modelname="fb18ch100x_wcg02_fir15_dexp_fit01_nested5"

d=ndb.get_batch_cells(batch=batch)
cellcount=len(d['cellid'])

plt.figure()
cc=np.ceil(np.sqrt(cellcount))
rr=np.ceil(cellcount/cc)
for ii in range(0,cellcount):
    cellid=d['cellid'][ii]
    print("loading {0}".format(cellid))
    stack=nu.io.load_single_model(cellid, batch, modelname, evaluate=False)

    h=stack.modules[3].get_strf()
    
    if ii==0:
        h_all=h[:,:,np.newaxis]
    else:
        h_all=np.concatenate((h_all,h[:,:,np.newaxis]),axis=2)
        
    plt.subplot(rr,cc,ii+1)
    mmax=np.max(np.abs(h.reshape(-1)))
    plt.imshow(h, aspect='auto', origin='lower',cmap=plt.get_cmap('jet'), interpolation='none')
    plt.clim(-mmax,mmax)
    #cbar = plt.colorbar()
    #cbar.set_label('gain')



