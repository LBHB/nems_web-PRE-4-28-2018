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
def load_single_model(cellid, batch, modelname):
    
    filename = get_file_name(cellid, batch, modelname)
    stack = load_model(filename)
    
    try:
        stack.valmode = True
        stack.evaluate()
    except Exception as e:
        print("Error evaluating stack")
        print(e)
        # TODO: What to do here? Is there a special case to handle, or
        #       did something just go wrong?
    #stack.quick_plot()
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
    if AWS:
        s3_client = boto3.client('s3')
        key = filename[len(sc.DIRECTORY_ROOT):]
        fileobj = s3_client.get_object(Bucket=sc.PRIMARY_BUCKET, Key=key)
        file = scipy.io.loadmat(io.BytesIO(fileobj['Body'].read()), chars_as_strings=chars_as_strings)
        return file
    else:
        file = scipy.io.loadmat(filename, chars_as_strings=chars_as_strings)
        return file
