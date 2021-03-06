#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  7 12:55:17 2017

@author: shofer
"""
import scipy.io
import scipy.signal
import lib.nems_modules as nm
import lib.nems_fitters as nf
import lib.nems_keywords as nk
import lib.nems_utils as nu
import lib.nems_stack as ns
import lib.baphy_utils as bu
import copy
import numpy as np

stack=ns.nems_stack()
    
stack.meta['batch']=294
stack.meta['cellid']='eno052d-a1'
stack.meta['modelname']='perfectpupil50_nopupgain_fit01'
#stack.cross_val=True #This is now incorporated into the data loading keyword
#stack.nests=1

# extract keywords from modelname    
keywords=stack.meta['modelname'].split("_")
stack.cv_counter=0
stack.cond=False
stack.fitted_modules=[]
while stack.cond is False:
    print('iter loop='+str(stack.cv_counter))
    stack.clear()
    stack.valmode=False
    for k in keywords:
        f = getattr(nk, k)
        f(stack)
    
    #TODO: this stuff below could be wrapped into do_fit somehow
    phi=[] 
    for idx,m in enumerate(stack.modules):
        this_phi=m.parms2phi()
        if this_phi.size:
            if stack.cv_counter==0:
                stack.fitted_modules.append(idx)
            phi.append(this_phi)
    phi=np.concatenate(phi)
    stack.parm_fits.append(phi)
    print(stack.nests)
    if stack.nests==1:
        stack.cond=True
    else:
        stack.cv_counter+=1
#print(stack.parm_fits)
# measure performance on both estimation and validation data
stack.valmode=True

#stack.nests=1
print(stack.modules[1])
stack.evaluate(1)

stack.append(nm.mean_square_error)


corridx=nu.find_modules(stack,'correlation')
if not corridx:
   # add MSE calculator module to stack if not there yet
    stack.append(nm.correlation)
                
#print("mse_est={0}, mse_val={1}, r_est={2}, r_val={3}".format(stack.meta['mse_est'],
             #stack.meta['mse_val'],stack.meta['r_est'],stack.meta['r_val']))
print("mse_est={0}, r_est={1}, r_val={2}".format(stack.meta['mse_est'],
             stack.meta['r_est'],stack.meta['r_val']))
valdata=[i for i, d in enumerate(stack.data[-1]) if not d['est']]
print(valdata)
if valdata:
    stack.plot_dataidx=valdata[0]
else:
    stack.plot_dataidx=0

# edit: added autoplot kwarg for option to disable auto plotting
#       -jacob, 6/20/17
stack.plot_dataidx=1
stack.plot_stimidx=5
#alldats=stack.data[2]
stack.quick_plot()
