#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 31 17:29:39 2017

@author: hellerc
"""

import sklearn as sk
from sklearn.decomposition import NMF
import numpy as np
from tqdm import tqdm

kmin = 1                #min rank
kmax = 10 #resp.shape[-1]   #max rank
B1 = 10                 #n bootstrap samples

resp_nnmf = resp.reshape(bincount*repcount*stimcount, cellcount).T
RHO = []
for i in tqdm(range(kmin, kmax)):
    model = NMF(n_components = i, init='nndsvd')
    H_k = []
    diss_k = []
    for j in range(1, B1):
        rand_inds = np.random.randint(0, resp_nnmf.shape[1], resp_nnmf.shape[1])
        resp_t = resp_nnmf[:, rand_inds]
        W = model.fit_transform(resp_t)
        H = model.components_
        H_k.append(H)
        if j == 1:
            Rand_inds = rand_inds
            H_ = H
        else:
            Rand_inds = np.vstack((Rand_inds, rand_inds))
            H_ = np.vstack((H_,H))
    
    
    for x in range(0, B1-1):
        for y in range(0, B1-1):
            
            diss_k.append((1/(2*i)) * (2*i - sum(np.max(np.matmul(H_k[x], H_k[y].T),0)) - sum(np.max(np.matmul(H_k[x],H_k[y].T),1))))
    
    RHO.append(sum(diss_k))
k = np.argwhere(abs(np.array(RHO)) == min(abs(np.array(RHO))))[0][0]+1

B1 = 50
for boot in tqdm(range(0, B1)):
    model = NMF(n_components = k, init='nndsvd')
    rand_inds = np.random.randint(0, resp_nnmf.shape[1], resp_nnmf.shape[1])
    resp_t = resp_nnmf[:, rand_inds]
    W = model.fit_transform(resp_t)
    H = model.components_
    if j == 1:
            Rand_inds = rand_inds
            H_stack = H
    else:
        Rand_inds = np.vstack((Rand_inds, rand_inds))
        H_stack = np.vstack((H_,H))