#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  3 12:15:26 2017

@author: shofer
"""
import numpy as np
import nems.keywords as nk
import nems.utils as nu
import nems.baphy_utils as bu
import nems.modules as nm
import nems.stack as ns
import nems.fitters as nf
import nems.main as mn
import os
import os.path
import copy

#keyword='parm50_wc03_fir10_dexp_fit01_nested20'
#batch=293
#cellid='BOL006b-60-1'
#"""
stack=ns.nems_stack()
stack.meta['batch']=296
stack.meta['cellid']='gus019d-a1'
stack.meta['modelname']='jitterload_fir15_fit00'  
#stack.meta['batch']=293
#stack.meta['cellid']='BOL006b-60-1'
#stack.meta['modelname']='parm50a_wc03_fir10_fit00_nested10'
#stack.meta['batch']=294
#stack.meta['cellid']='zee018c-d2'
#eno052d-a1
#zee018c-d2
#zee017c-a1
#stack.meta['modelname']='perfectpupil50_pupgain_fit00_nested20'
stack.keywords=stack.meta['modelname'].split("_")
# extract keywords from modelname    
if 'nested' in stack.keywords[-1]:
    print('Using nested cross-validation, fitting will take longer!')
    f=getattr(nk,stack.keywords[-1])
    f(stack)
else:
    print('Using standard est/val conditions')
    stack.valmode=False
    for k in stack.keywords:
        f = getattr(nk, k)
        f(stack)    
      

 # measure performance on both estimation and validation data
stack.valmode=True
alldata=stack.data  
stack.evaluate(1)

alldata=stack.data

stack.append(nm.correlation)
                    
#print("mse_est={0}, mse_val={1}, r_est={2}, r_val={3}".format(stack.meta['mse_est'],
                 #stack.meta['mse_val'],stack.meta['r_est'],stack.meta['r_val']))
print("mse_est={0}, mse_val={1}, r_est={2}, r_val={3}".format(stack.meta['mse_est'],
                 stack.meta['mse_val'],stack.meta['r_est'],stack.meta['r_val']))
valdata=[i for i, d in enumerate(stack.data[-1]) if not d['est']]
if valdata:
    stack.plot_dataidx=valdata[0]
else:
    stack.plot_dataidx=0
        
        
    # edit: added autoplot kwarg for option to disable auto plotting
    #       -jacob, 6/20/17
stack.quick_plot()
#"""

#unres=stack.unresampled
"""
stack=ns.nems_stack()

stack.meta['batch']=293
#stack.meta['cellid']='eno053f-a1'
stack.meta['cellid']='eno048f-b1'

#file='/auto/users/shofer/data/batch'+str(stack.meta['batch'])+'/'+str(stack.meta['cellid'])+'.mat'
file=bu.get_celldb_file(stack.meta['batch'],stack.meta['cellid'],fs=100,stimfmt='parm',chancount=16)
print("Initializing load_mat with file {0}".format(file))
stack.cv_counter=0
stack.append(nm.load_mat,est_files=[file],fs=50,avg_resp=False)
stack.append(nm.crossval,valfrac=0.05)
stack.append(nm.weight_channels,num_chans=3)
stack.append(nm.fir_filter,num_coefs=10)

stack.append(nm.mean_square_error)
stack.error=stack.modules[-1].error
stack.fitter=nf.basic_min(stack)
stack.fitter.tol=0.0001
#stack.fitter=nf.coordinate_descent(stack)
#stack.fitter.tol=0.001
fitidx=nu.find_modules(stack,'weight_channels') + nu.find_modules(stack,'fir_filter')
stack.fitter.fit_modules=fitidx
stack.fitter.do_fit()

stack.popmodule()
stack.append(nm.state_gain,gain_type='polypupgain',fit_fields=['theta'],theta=[0,0,0,0,1])

stack.append(nm.mean_square_error)
stack.error=stack.modules[-1].error
stack.fitter=nf.basic_min(stack,routine='SLSQP')
stack.fitter.tol=0.0001
stack.fitter.do_fit()


stack.valmode=True
    
    #stack.nests=1
stack.evaluate(1)
    
stack.append(nm.mean_square_error)
    
corridx=nu.find_modules(stack,'correlation')
if not corridx:
   # add MSE calculator module to stack if not there yet
   stack.append(nm.correlation)
#stack.append(nm.normalize)

#stack.append(nm.pupil_model,tile_data=True)
#unpacked=stack.modules[-1].unpack_data()
#unpackresp=stack.modules[-1].unpack_data(name='resp')
alldata=stack.data
"""



