#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 14 15:48:21 2017

@author: hellerc
"""

import numpy as np
import matplotlib.pyplot as plt

from pop_utils import load_population_stack
from NRF_tools import NRF_fit_continuous
from NRF_tools import eval_fit_nans
from NRF_tools import plt_perf_by_trial


modelname = 'parm100pt_wcg02_fir15_fit01_nested5'
batch=301

resp, pred, pupil = load_population_stack(modelname,batch)

resp = np.transpose(resp.squeeze(),(1,0,2))
pred = np.transpose(pred.squeeze(),(1,0,2))
pupil = np.transpose(pupil.squeeze(),(1,0))
rN = NRF_fit_continuous(r=resp,r0_strf=pred,spontonly=False)

cc_rN = np.nanmean(eval_fit_nans(resp,rN)['bytrial'].squeeze(),-1)
cc_r0 = np.nanmean(eval_fit_nans(resp,pred)['bytrial'].squeeze(),-1)
pupil = np.nanmean(pupil,0)

plt.figure()
plt.subplot(211)
plt.plot(cc_rN,'.-',color='r')
plt.plot(cc_r0,'.-',color='b')
plt.legend(['Network', 'STRF'])
plt.title('rN vs. pupil: %s, r0 vs. pupil: %s' %(round(np.corrcoef((cc_rN, pupil))[0][1],2), 
                                                 round(np.corrcoef((cc_r0[~np.isnan(cc_r0)], pupil[~np.isnan(cc_r0)]))[0][1],2)))
plt.subplot(212)
model = cc_rN-cc_r0
plt.plot(model,'.-',color='g')
plt.plot(pupil,'.-',color='k')
plt.legend(['Model', 'pupil'])
plt.title('Model vs. pupil: %s' %round(np.corrcoef((model[~np.isnan(model)],pupil[~np.isnan(model)]))[0][1],2))
