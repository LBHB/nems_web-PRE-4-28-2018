#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 16 05:20:07 2017

@author: svd
"""

import lib.nems_modules as nm
import lib.nems_fitters as nf
import lib.nems_utils as nu
import lib.baphy_utils as baphy_utils

# NOTE: Added list of keywords associated with each module, so that the kw
#       options can be easily retrieved by the modelpane. If you add additional
#       keywords please add them to the associated list as well, or make a new
#       list if no keywords exist for a new module.
#       --Jacob 6/28/17

# loader keywords

load_mat = ['fb24ch200', 'fb18ch100', 'loadlocal']

def fb24ch200(stack):
    file=baphy_utils.get_celldb_file(stack.meta['batch'],stack.meta['cellid'],fs=200,stimfmt='ozgf',chancount=24)
    print("Initializing load_mat with file {0}".format(file))
    stack.append(nm.load_mat,est_files=[file],fs=200)
    
def fb18ch100(stack):
    file=baphy_utils.get_celldb_file(stack.meta['batch'],stack.meta['cellid'],fs=100,stimfmt='ozgf',chancount=18)
    print("Initializing load_mat with file {0}".format(file))
    stack.append(nm.load_mat,est_files=[file],fs=100)

def loadlocal(stack):
    """
    This keyword is just to load up a local file that is not yet on the BAPHY database.
    Right now just loads files from my computer --njs, June 27 2017
    """
    file='/auto/users/shofer/data/batch'+str(stack.meta['batch'])+'/'+str(stack.meta['cellid'])+'.mat'
    #file=baphy_utils.get_celldb_file(stack.meta['batch'],stack.meta['cellid'],fs=100,stimfmt='ozgf',chancount=18)
    print("Initializing load_mat with file {0}".format(file))
    stack.append(nm.load_mat,est_files=[file],fs=100)
    

standard_est_val = ['ev', ]

def ev(stack):
    stack.append(nm.standard_est_val, valfrac=0.05)


# weight channels keywords
###############################################################################

weight_channels = ['wc01', 'wc02', 'wc03', 'wc04']

def wc01(stack):
    stack.append(nm.weight_channels,num_chans=1)

def wc02(stack):
    stack.append(nm.weight_channels,num_chans=2)

def wc03(stack):
    stack.append(nm.weight_channels,num_chans=3)

def wc04(stack):
    stack.append(nm.weight_channels,num_chans=4)


# fir filter keywords
###############################################################################

fir_filter = ['fir10', 'fir15']

def fir10(stack):
    stack.append(nm.fir_filter,num_coefs=10)
    #stack.modules[-1].baseline=stack.data[-1][0]['resp'].mean()
    
    # mini fit
    stack.append(nm.mean_square_error)
    stack.error=stack.modules[-1].error
    stack.fitter=nf.basic_min(stack)
    stack.fitter.tol=0.05
    #stack.fitter=nf.coordinate_descent(stack)
    #stack.fitter.tol=0.001
    
    stack.fitter.do_fit()
    stack.popmodule()
    
    
def fir15(stack):
    stack.append(nm.fir_filter,num_coefs=15)

    # mini fit
    stack.append(nm.mean_square_error)
    stack.error=stack.modules[-1].error
    stack.fitter=nf.basic_min(stack)
    stack.fitter.tol=0.01
    
    stack.fitter.do_fit()
    stack.popmodule()

# static NL keywords
###############################################################################

nonlinearity = ['dlog', 'exp', 'dexp']

def dlog(stack):
    stack.append(nm.nonlinearity,nltype='dlog',fit_fields=['dlog'],phi0=[1])
    
def exp(stack):
    stack.append(nm.nonlinearity,nltype='exp',fit_fields=['exp'],phi0=[1,1])

def dexp(stack):
    stack.append(nm.nonlinearity,nltype='dexp',fit_fields=['dexp'],phi0=[1,1,1,1])


# state variable keyowrds
###############################################################################

state_gain = ['pupgain', ]

def pupgain(stack):
    stack.append(nm.state_gain,gain_type='linpupgain',fit_fields=['linpupgain'],phi0=[0,1,0,0])


# fitter keywords
###############################################################################

fitter = ['fit00', ]

def fit00(stack):
    mseidx=nu.find_modules(stack,'mean_square_error')
    if not mseidx:
        # add MSE calculator module to stack if not there yet
        stack.append(nm.mean_square_error)
        
        # set error (for minimization) for this stack to be output of last module
        stack.error=stack.modules[-1].error
        
    stack.evaluate(1)

    stack.fitter=nf.basic_min(stack)
    stack.fitter.tol=0.001
    stack.fitter.do_fit()
    
def fitannl00(stack):
    mseidx=nu.find_modules(stack,'mean_square_error')
    if not mseidx:
        # add MSE calculator module to stack if not there yet
        stack.append(nm.mean_square_error)
        
        # set error (for minimization) for this stack to be output of last module
        stack.error=stack.modules[-1].error
    
    stack.evaluate(1)
    
    stack.fitter=nf.anneal_min(stack,anneal_iter=50,stop=5,up_int=10,bounds=None)
    stack.fitter.tol=0.001
    stack.fitter.do_fit()
    

# etc etc for other keywords
###############################################################################

def perfectpupil(stack):
    """keyword to fit pupil gain using "perfect" model generated by pupil_model module.
    The idea here is not to fit a model to the data, but merely to see the effect of a 
    a linear pupil gain function on the "perfect" model generated by averaging the
    rasters of each trial for a given stimulus. This keyword loads up the data
    and generates the model. It should be used with pupgain and a fitter keyword.
    """
    file=baphy_utils.get_celldb_file(stack.meta['batch'],stack.meta['cellid'],fs=200,stimfmt='ozgf',chancount=24)
    print("Initializing load_mat with file {0}".format(file))
    stack.append(nm.load_mat,est_files=[file],fs=100,formpup=False)
    stack.append(nm.pupil_est_val,valfrac=0)
    stack.append(nm.pupil_model,tile_data=True)
    
    
    
