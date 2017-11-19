"""Miscellaneous view functions.

Contents so far:
    status_report
    
"""

import time
import itertools
from base64 import b64encode

import pandas.io.sql as psql
import pandas as pd
import numpy as np
from flask import request, render_template, jsonify

from nems_web.nems_analysis import app
from nems.db import Session, NarfResults, cluster_tQueue, cluster_Session
from nems_web.plot_functions.reports import Performance_Report, Fit_Report
from nems.speed_test import Timer

@app.route('/batch_performance', methods=['GET', 'POST'])
def batch_performance():
    session = Session()
    
    cSelected = request.form['cSelected']
    bSelected = request.form['bSelected'][:3]
    mSelected = request.form['mSelected']
    findAll = request.form['findAll']
    
    cSelected = cSelected.split(',')
    mSelected = mSelected.split(',')
    
    if int(findAll):
        results = psql.read_sql_query(
                session.query(
                        NarfResults.cellid, NarfResults.modelname,
                        NarfResults.r_test
                        )
                .filter(NarfResults.batch == bSelected)
                .statement,
                session.bind
                )
    else:
        results = psql.read_sql_query(
                session.query(
                        NarfResults.cellid, NarfResults.modelname,
                        NarfResults.r_test
                        )
                .filter(NarfResults.batch == bSelected)
                .filter(NarfResults.cellid.in_(cSelected))
                .filter(NarfResults.modelname.in_(mSelected))
                .statement,
                session.bind
                )
    # get back list of models that matched other query criteria
    results_models = [
            m for m in
            list(set(results['modelname'].values.tolist()))
            ]
    # filter mSelected to match results models so that list is in the
    # same order as on web UI
    ordered_models = [
            m for m in mSelected
            if m in results_models
            ]
    
    report = Performance_Report(results, bSelected, ordered_models)
    report.generate_plot()
        
    session.close()
    return render_template(
            'batch_performance.html', script=report.script, div=report.div
            )
    
@app.route('/fit_report')
def fit_report():
    session = Session()
    cluster_session = cluster_Session()
    
    cSelected = request.args.getlist('cSelected[]')
    bSelected = request.args.get('bSelected')[:3]
    mSelected = request.args.getlist('mSelected[]')
    
    multi_index = pd.MultiIndex.from_product(
            [mSelected, cSelected], names=['modelname', 'cellid']
            )
    status = pd.DataFrame(index=multi_index, columns=['yn'])
    
    # TODO: the nested queries are causing the majority of the sluggishness,
    #       especially the cluster_session queries since they have to route
    #       through bhangra. need to figure out a way to do this with 1 query.
    tuples = list(itertools.product(cSelected, [bSelected], mSelected))
    notes = ['{0}/{1}/{2}'.format(t[0],t[1],t[2]) for t in tuples]
    
    qdata = psql.read_sql_query(
            cluster_session.query(cluster_tQueue)
            .filter(cluster_tQueue.note.in_(notes))
            .statement,
            cluster_session.bind,
            )

    results = psql.read_sql_query(
            session.query(
                    NarfResults.cellid, NarfResults.batch,
                    NarfResults.modelname,
                    )
            .filter(NarfResults.batch == bSelected)
            .filter(NarfResults.cellid.in_(cSelected))
            .filter(NarfResults.modelname.in_(mSelected))
            .statement,
            session.bind
            )

    for i, t in enumerate(tuples):
        yn = 0.3 # missing
        try:
            complete = qdata.loc[qdata['note'] == notes[i], 'complete'].iloc[0]
            if complete < 0:
                yn = 0.4 # in progress
            elif complete == 0:
                yn = 0.5 # not started
            elif complete == 1:
                yn = 0.6# finished
            elif complete == 2:
                yn = 0 # dead entry
            else:
                pass # unknown value, so leave as missing?
        except:
            try:
                result = results.loc[
                        (results['cellid'] == t[0])
                        & (results['batch'] == int(t[1]))
                        & (results['modelname'] == t[2]),
                        'cellid'
                        ].iloc[0]
                yn = 0.6
            except:
                pass
        status['yn'].loc[t[2],t[0]] = yn
    
    status.reset_index(inplace=True)
    status = status.pivot(index='cellid', columns='modelname', values='yn')
    status = status[status.columns].astype(float)
    report = Fit_Report(status)
    report.generate_plot()
    
    session.close()
    cluster_session.close()
    
    image = str(b64encode(report.img_str))[2:-1]
    return jsonify(image=image)
    
                    
    
    
    