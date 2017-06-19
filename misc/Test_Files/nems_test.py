#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 17 23:16:23 2017

@author: svd
"""

import numpy as np
import matplotlib.pyplot as plt

import scipy.io
import scipy.signal
import lib.nems_modules as nm
import lib.nems_fitters as nf
import lib.nems_keywords as nk
import lib.nems_utils as nu

#datapath='/Users/svd/python/nems/ref/week5_TORCs/'
#est_files=[datapath + 'tor_data_por073b-b1.mat']

#datapath='/auto/data/code/nems_in_cache/batch271/'
#est_files=[datapath + 'chn020f-b1_b271_ozgf_c24_fs200.mat']
datapath='/Users/svd/python/nems/misc/ref/'
est_files=[datapath + 'bbl031f-a1_nat_export.mat']
#'/auto/users/shofer/data/batch291/bbl038f-a2_nat_export.mat'
# create an empty stack
stack=nm.nems_stack()

stack.meta['batch']=291
#stack.meta['cellid']='chn020f-b1'
#stack.meta['cellid']='bbl031f-a1'
stack.meta['cellid']='bbl061h-a1'
#stack.meta['cellid']='bbl038f-a2_nat_export'

stack.meta['batch']=267
stack.meta['cellid']='ama024a-17-1'

# add a loader module to stack
nk.fb18ch100(stack)
#nk.loadlocal(stack)

nk.ev(stack)

# add fir filter module to stack & fit a little
#nk.dlog(stack)
nk.fir10(stack)

# add nonlinearity and refit
nk.dexp(stack)

# following has been moved to nk.fit00
stack.append(nm.mean_square_error)

stack.fitter=nf.basic_min(stack)
stack.fitter.tol=0.005
stack.fitter.do_fit()

stack.valmode=True
stack.evaluate(1)
corridx=nu.find_modules(stack,'correlation')
if not corridx:
    # add MSE calculator module to stack if not there yet
    stack.append(nm.correlation)    

stack.plot_dataidx=1

# default results plot
stack.quick_plot()

# save
#filename="/auto/data/code/nems_saved_models/batch{0}/{1}.pkl".format(stack.meta['batch'],stack.meta['cellid'])
#nu.save_model(stack,filename)


## single figure display
#plt.figure(figsize=(8,9))
#for idx,m in enumerate(stack.modules):
#    plt.subplot(len(stack.modules),1,idx+1)
#    m.do_plot()
    
## display the output of each module in a separate figure
#for idx,m in enumerate(stack.modules):
#    plt.figure(num=idx,figsize=(8,3))
#    #ax=plt.plot(5,1,idx+1)
#    m.do_plot(idx=idx)
    

