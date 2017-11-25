#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  7 12:14:38 2017

@author: svd
"""


import pandas.io.sql as psql
from nems.db import NarfResults, Session
import matplotlib.pyplot as plt
import numpy as np

batch=303
modelnames=['parm100pt_wcg02_fir15_pupgainctl_fit01_nested5',
           'parm100pt_wcg02_fir15_behgain_fit01_nested5',
           'parm100pt_wcg02_fir15_pupgain_fit01_nested5',
           'parm100pt_wcg02_fir15_stategain_fit01_nested5'
           ]

session = Session()

results = psql.read_sql_query(
     session.query(NarfResults)
     .filter(NarfResults.batch == batch)
     .filter(NarfResults.modelname.in_(modelnames))
     .statement,
     session.bind
     )
session.close()

results.head()

mapping = {modelname: i for i, modelname in enumerate(modelnames)}
results['modelindex'] = results.modelname.map(mapping)


# quick plot:
#results.set_index(['modelindex', 'cellid'])['r_test'].unstack('modelindex').T.plot().legend(bbox_to_anchor=(1, 1))


r_test = results.set_index(['modelindex', 'cellid'])['r_test'].unstack('modelindex')

#plt.plot(r_test)

f, ax = plt.subplots(1, 1)
ph=ax.plot(r_test.T, linewidth=1.0, zorder=0)
for p in ph:
    c=p.get_color()
    p.set_color(c+'80')
ax.plot(r_test.T, 'o', zorder=1)

x=np.arange(0,len(modelnames))
m=r_test.mean()
e=r_test.sem()

ax.errorbar(x,m,yerr=e, color='k', linewidth=2.0, zorder=2)

ax.xaxis.set_ticklabels(modelnames)
ax.xaxis.set_ticks([0, 1, 2])


