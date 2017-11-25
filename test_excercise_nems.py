#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  7 09:47:58 2017

@author: hellerc
"""

import nems.modules as nm
import nems.utilities as ut
import nems.stack as ns

# Walk through nems model fitting procedure to learn how stack is made/saved

# Use model/batch I've been using for TORC data: 
batch=301
modelname= "fb18ch100x_wcg02_fir15_dexp_fit01_nested5"
cellid = 'TAR010c-30-1'

# Get celldb file for this experiment (specified by batch and cellid)
file=ut.baphy.get_celldb_file(batch, cellid,fs=100, stimfmt='ozgf', chancount=18)

# Create a stack (usually, this would be passed to "fit_single" which then would parse keys and fit)
stack=ns.nems_stack()
    
stack.meta['batch']=batch
stack.meta['cellid']=cellid
stack.meta['modelname']=modelname
stack.valmode=False
stack.keywords=modelname.split("_")

# module append, appends an instance of a module and evaluates the module at the same time

# Here we append the module load_mat (which is a class), and provide arguments for initializing this instance
###          stack.append(nm.loaders.load_mat,est_files=[file],fs=100,avg_resp=True)  #####