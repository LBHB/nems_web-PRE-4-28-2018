#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  7 14:39:05 2017

@author: svd
"""

import scipy
import numpy as np
import pickle
import os
import copy
import io
import json
import pprint
import h5py

import nems.utilities as ut
from nems_config.defaults import DEMO_MODE

try:
    import boto3
    import nems_config.Storage_Config as sc
    AWS = sc.USE_AWS
except Exception as e:
    print(e)
    from nems_config.defaults import STORAGE_DEFAULTS
    sc = STORAGE_DEFAULTS
    AWS = False
    

"""
load_single_model - load and evaluate a model, specified by cellid, batch and modelname

example:
    import lib.nems_main as nems
    cellid='bbl061h-a1'
    batch=291
    modelname='fb18ch100_ev_fir10_dexp_fit00'
    stack=nems.load_single_model(cellid,batch,modelname)
    stack.quick_plot()
    
"""
def load_single_model(cellid, batch, modelname, evaluate=True):
    
    filename = get_file_name(cellid, batch, modelname)
    stack = load_model(filename)
    
    if evaluate:
        try:
            stack.valmode = True
            stack.evaluate()
            
        except Exception as e:
            print("Error evaluating stack")
            print(e)
            
            # TODO: What to do here? Is there a special case to handle, or
            #       did something just go wrong?
    
    return stack

def load_from_dict(batch,cellid,modelname):
    filepath = get_file_name(cellid, batch, modelname)
    sdict=load_model_dict(filepath)
    
    #Maybe move some of this to the load_model_dict function?
    stack=ns.nems_stack()
    
    stack.meta=sdict['meta']
    stack.nests=sdict['nests']
    parm_list=[]
    for i in sdict['parm_fits']:
        parm_list.append(np.array(i))
    stack.parm_fits=parm_list
    #stack.cv_counter=sdict['cv_counter']
    stack.fitted_modules=sdict['fitted_modules']
    
    for i in range(0,len(sdict['modlist'])):
        stack.append(op.attrgetter(sdict['modlist'][i])(nm),**sdict['mod_dicts'][i])
        #stack.evaluate()
        
    stack.valmode=True
    stack.evaluate()
    #stack.quick_plot()
    return stack



def save_model(stack, file_path):
    
    # truncate data to save disk space
    stack2=copy.deepcopy(stack)
    for i in range(1,len(stack2.data)):
        del stack2.data[i][:]
    del stack2.keyfuns
    
    if AWS:
        # TODO: Need to set up AWS credentials in order to test this
        # TODO: Can file key contain a directory structure, or do we need to
        #       set up nested 'buckets' on s3 itself?
        s3 = boto3.resource('s3')
        # this leaves 'nems_saved_models/' as a prefix, so that s3 will
        # mimick a saved models folder
        key = file_path[len(sc.DIRECTORY_ROOT):]
        fileobj = pickle.dumps(stack2, protocol=pickle.HIGHEST_PROTOCOL)
        s3.Object(sc.PRIMARY_BUCKET, key).put(Body=fileobj)
    else:
        directory = os.path.dirname(file_path)
    
        try:
            os.stat(directory)
        except:
            os.mkdir(directory)       
    
        if os.path.isfile(file_path):
            print("Removing existing model at: {0}".format(file_path))
            os.remove(file_path)

        try:
            # Store data (serialize)
            with open(file_path, 'wb') as handle:
                pickle.dump(stack2, handle, protocol=pickle.HIGHEST_PROTOCOL)
        except FileExistsError:
            # delete pkl file first and try again
            print("Removing existing model at: {0}".format(file_path))
            os.remove(file_path)
            with open(file_path, 'wb') as handle:
                pickle.dump(stack2, handle, protocol=pickle.HIGHEST_PROTOCOL)
        
        os.chmod(file_path, 0o666)
        print("Saved model to {0}".format(file_path))
        
def save_model_dict(stack, filepath=None):
    sdict=dict.fromkeys(['modlist','mod_dicts','parm_fits','meta','nests','fitted_modules'])
    sdict['modlist']=[]
    sdict['mod_dicts']=[]
    parm_list=[]
    for i in stack.parm_fits:
        parm_list.append(i.tolist())
    sdict['parm_fits']=parm_list
    sdict['nests']=stack.nests
    sdict['fitted_modules']=stack.fitted_modules
    
    # svd 2017-08-10 -- pull out all of meta
    sdict['meta']=stack.meta
    sdict['meta']['mse_est']=[]
    
    for m in stack.modules:
        sdict['modlist'].append(m.name)
        sdict['mod_dicts'].append(m.get_user_fields())
    
    # TODO: normalization parms have to be saved as part of the normalization module(s)
    try:
        d=stack.d
        g=stack.g
        sdict['d']=d
        sdict['g']=g
    except:
        pass
    
    # to do: this info should go to a table in celldb if compact enough
    if filepath:
        if AWS:
            s3 = boto3.resource('s3')
            key = filepath[len(sc.DIRECTORY_ROOT):]
            fileobj = json.dumps(sdict)
            s3.Object(sc.PRIMARY_BUCKET, key).put(Body=fileobj)
        else:
            with open(filepath,'w') as fp:
                json.dump(sdict,fp)
    
    return sdict
        

def load_model_dict(filepath):
    #TODO: need to add AWS stuff
    if AWS:
        s3_client = boto3.client('s3')
        key = filepath[len(sc.DIRECTORY_ROOT):]
        fileobj = s3_client.get_object(Bucket=sc.PRIMARY_BUCKET, Key=key)
        sdict = json.loads(fileobj['Body'].read())
    else:
        with open(filepath,'r') as fp:
            sdict=json.load(fp)
    
    return sdict
    

def load_model(file_path):
    if AWS:
        # TODO: need to set up AWS credentials to test this
        s3_client = boto3.client('s3')
        key = file_path[len(sc.DIRECTORY_ROOT):]
        fileobj = s3_client.get_object(Bucket=sc.PRIMARY_BUCKET, Key=key)
        stack = pickle.loads(fileobj['Body'].read())
        
        return stack
    else:
        try:
            # Load data (deserialize)
            with open(file_path, 'rb') as handle:
                stack = pickle.load(handle)
            print('stack successfully loaded')

            if not stack.data:
                raise Exception("Loaded stack from pickle, but data is empty")
                
            return stack
        except Exception as e:
            # TODO: need to do something else here maybe? removed return stack
            #       at the end b/c it was being returned w/o assignment when
            #       open file failed.
            print("error loading {0}".format(file_path))
            raise e


def get_file_name(cellid, batch, modelname):
    
    filename=(
        sc.DIRECTORY_ROOT + "nems_saved_models/batch{0}/{1}/{2}.pkl"
        .format(batch, cellid, modelname)
        )
    
    return filename


def get_mat_file(filename, chars_as_strings=True):
    """ 
    get_mat_file : load matfile using scipy loadmat, but redirect to s3 if toggled on.
        TODO: generic support of s3 URI, not NEMS-specific
           check for local version (where, cached? before loading from s3)
    """
    
    if DEMO_MODE:
        s3_client = boto3.client('s3')
        i = filename.find('batch')
        key = 'sample_data/{0}'.format(filename[i:])
        fileobj = s3_client.get_object(Bucket='nemspublic', Key=key)
        data = scipy.io.loadmat(
                io.BytesIO(fileobj['Body'].read()),
                chars_as_strings=chars_as_strings,
                )
        return data
    if AWS:
        s3_client = boto3.client('s3')
        key = filename[len(sc.DIRECTORY_ROOT):]
        try:
            fileobj = s3_client.get_object(Bucket=sc.PRIMARY_BUCKET, Key=key)
        except Exception as e:
            print("File not found on S3: {0}".format(key))
            raise e
            
        data = scipy.io.loadmat(
                io.BytesIO(fileobj['Body'].read()),
                chars_as_strings=chars_as_strings
                )
        return data
    else:
        data = scipy.io.loadmat(filename, chars_as_strings=chars_as_strings)
        return data


def load_ecog(stack,fs=25):
    """
    special hard-coded loader from ECOG data from Sam
    """
    
    cellinfo=stack.meta["cellid"].split("-")
    channel=int(cellinfo[1])
    
    stimfile='/auto/data/daq/ecog/coch.mat'
    respfile='/auto/data/daq/ecog/reliability0.1.mat'
    
    stimdata = h5py.File(stimfile,'r')
    respdata = h5py.File(respfile,'r')
    
    data={}
    for name,d in respdata.items():
        #print (name)
        data[name]=d.value
    for name,d in stimdata.items():
        #print (name)
        data[name]=d.value
    data['resp']=data['D'][channel,:,:]   # shape to stim X time (25Hz)
    
    # reshape stimulus to be channel X stim X time and downsample from 400 to 25 Hz
    stim_resamp_factor=int(400/25)
    noise_thresh=0
    # reduce spectral sampling to speed things up
    data['stim']=ut.utils.thresh_resamp(data['coch_all'],6,thresh=noise_thresh,ax=1)
    
    # match temporal sampling to response
    data['stim']=ut.utils.thresh_resamp(data['stim'],stim_resamp_factor,thresh=noise_thresh,ax=2)
    data['stim']=np.transpose(data['stim'],[1,0,2])

    data['repcount']=np.ones([data['resp'].shape[0],1])
    data['pred']=data['stim']
    data['respFs']=25
    data['stimFs']=400  # original
    data['fs']=25       # final, matched for both
    del data['D']
    del data['coch_all']
    
    return data

def load_nat_cort(fs=100,prestimsilence=0.5,duration=3,poststimsilence=0.5):
    """
    special hard-coded loader for cortical filtered version of NAT
    
    file saved with 200 Hz fs and 3-sec duration + 1-sec poststim silence to tail off filters
    use pre/dur/post parameters to adjust size appropriately
    """
      
    stimfile='/auto/data/tmp/filtcoch_PCs_100.mat'
    stimdata = h5py.File(stimfile,'r')
    
    data={}
    for name,d in stimdata.items():
        #print (name)
        #if name=='S_mod':
        #    S_mod=d.value
        if name=='U_mod':
            U_mod=d.value
        #if name=='V_mod':
        #    V_mod=d.value
    fs_in=200
    noise_thresh=0.0
    stim_resamp_factor=int(fs_in/fs)
    
    # reshape and normalize to max of approx 1
    
    data['stim']=np.reshape(U_mod,[100,93,800])/0.05
    if stim_resamp_factor != 1:
        data['stim']=ut.utils.thresh_resamp(data['stim'],stim_resamp_factor,thresh=noise_thresh,ax=2)
    s=data['stim'].shape
    prepad=np.zeros([s[0],s[1],int(prestimsilence*fs)])
    offbin=int((duration+poststimsilence)*fs)
    data['stim']=np.concatenate((prepad,data['stim'][:,:,0:offbin]),axis=2)
    data['stimFs']=fs_in
    data['fs']=fs
    
    return data


def load_nat_coch(fs=100,prestimsilence=0.5,duration=3,poststimsilence=0.5):
    """
    special hard-coded loader for cortical filtered version of NAT
    
    file saved with 200 Hz fs and 3-sec duration + 1-sec poststim silence to tail off filters
    use pre/dur/post parameters to adjust size appropriately
    """
      
    stimfile='/auto/data/tmp/coch.mat'
    stimdata = h5py.File(stimfile,'r')
    
    data={}
    for name,d in stimdata.items():
        if name=='coch_all':
            coch_all=d.value
            
    fs_in=200
    noise_thresh=0.0
    stim_resamp_factor=int(fs_in/fs)
    
    # reduce spectral sampling to speed things up
    #data['stim']=ut.utils.thresh_resamp(coch_all,2,thresh=noise_thresh,ax=1)
    
    data['stim']=coch_all
    data['stim']=np.transpose(data['stim'],[1,0,2])
    
    if stim_resamp_factor != 1:
        data['stim']=ut.utils.thresh_resamp(data['stim'],stim_resamp_factor,thresh=noise_thresh,ax=2)
    s=data['stim'].shape
    prepad=np.zeros([s[0],s[1],int(prestimsilence*fs)])
    offbin=int((duration+poststimsilence)*fs)
    data['stim']=np.concatenate((prepad,data['stim'][:,:,0:offbin]),axis=2)
    data['stimFs']=fs_in
    data['fs']=fs
    
    return data

