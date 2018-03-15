"""View functions for "Fit Single Now" and "Enqueue Models" buttons.

These functions communicate with modelfit.py and are called by flask
when the browser navigates to their app.route URL signatures.
fit_single_model_view calls modelfit.fit_single_model
for the cell, batch and model selection passed via AJAX.
enqueue_models_view calls enqueue_models for the list of
cell selections, batch selection, and list of model selections
passed via AJAX.
Both functions return json-serialized summary information for the user
to indicate the success/failure and results of the model fit/queue.

See Also:
---------
. : modelfit.py

"""

import logging

import ast
from flask import jsonify, request
from flask_login import login_required

from nems_web.nems_analysis import app
from nems_db.db import enqueue_models
from nems_web.account_management.views import get_current_user

log = logging.getLogger(__name__)


@app.route('/fit_single_model')
def fit_single_model_view():
    """Call lib.nems_main.fit_single_model with user selections as args."""

    return jsonify(r_est='This function no longer supported.',
                   r_val='Awaiting removal from interface.')

    # Deprecated
    '''
    user = get_current_user()

    cSelected = request.args.getlist('cSelected[]')
    bSelected = request.args.get('bSelected')[:3]
    mSelected = request.args.getlist('mSelected[]')

    # Disallow multiple cell/model selections for a single fit.
    if (len(cSelected) > 1) or (len(mSelected) > 1):
        return jsonify(r_est='error', r_val='more than 1 cell and/or model')


    log.info(
            "Beginning model fit -- this may take several minutes."
            "Please wait for a success/failure response."
            )
    try:
        stack = nems.fit_single_model(
                        cellid=cSelected[0],
                        batch=bSelected,
                        modelname=mSelected[0],
                        autoplot=False,
                        )
    except Exception as e:
        web_log.info("Error when calling nems_main.fit_single_model")
        log.info(e)
        web_log.info("Fit failed.")
        raise e

    preview = stack.quick_plot_save(mode="png")
    r_id = update_results_table(stack, preview, user.username, user.labgroup)
    web_log.info("Results saved with id: {0}".format(r_id))

    r_est = stack.meta['r_est'][0]
    r_val = stack.meta['r_val'][0]

    # Manually release stack for garbage collection -- having memory issues?
    stack = None

    return jsonify(r_est=r_est, r_val=r_val)
    '''


@app.route('/enqueue_models')
@login_required
def enqueue_models_view():
    """Call modelfit.enqueue_models with user selections as args."""

    user = get_current_user()

    # Only pull the numerals from the batch string, leave off the description.
    bSelected = request.args.get('bSelected')[:3]
    cSelected = request.args.getlist('cSelected[]')
    mSelected = request.args.getlist('mSelected[]')
    codeHash = request.args.get('codeHash')
    jerbQuery = request.args.get('jerbQuery')

    log.info('codeHash retrieved properly?: {0}'.format(codeHash))

    if not codeHash:
        codeHash = 'master'

    if not jerbQuery:
        jerbQuery = ''

    force_rerun = request.args.get('forceRerun', type=int)

    enqueue_models(
            cSelected, bSelected, mSelected,
            force_rerun=bool(force_rerun), user=user.username,
            codeHash=codeHash, jerbQuery=jerbQuery,
            )
    return jsonify(data=True)


@app.route('/add_jerb_kv')
def add_jerb_kv():
    """Take key, list of values, and existing JSON object (query) from input
    then combine them into a new JSON object with the key and values added."""

    key = request.args.get('key')
    values = request.args.get('val')
    query = request.args.get('query')

    if not query:
        query = {}
    else:
        # Evaluate JSON-formatted string as a dict
        query = ast.literal_eval(query)

    if not values:
        val_list = []
    else:
        values = values.replace(' ', '')
        val_list = values.split(',')

    query[key] = val_list
    return jsonify(newQuery=query)
