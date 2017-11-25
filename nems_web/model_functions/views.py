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

from flask import jsonify, request
from flask_login import login_required

from nems_web.nems_analysis import app
from nems.db import NarfResults, enqueue_models, update_results_table
import nems.main as nems
from nems_web.account_management.views import get_current_user
from nems.keyword_rules import keyword_test_routine
from nems.utilities.print import web_print

@app.route('/fit_single_model')
def fit_single_model_view():
    """Call lib.nems_main.fit_single_model with user selections as args."""
    
    user = get_current_user()
    
    cSelected = request.args.getlist('cSelected[]')
    bSelected = request.args.get('bSelected')[:3]
    mSelected = request.args.getlist('mSelected[]')
    
    # Disallow multiple cell/model selections for a single fit.
    if (len(cSelected) > 1) or (len(mSelected) > 1):
        return jsonify(r_est='error',r_val='more than 1 cell and/or model')
    
    # turn off keyword rules tests for now
    #try:
    #    keyword_test_routine(mSelected[0])
    #except Exception as e:
    #    web_print(e)
    #    web_print('Fit failed.')
    #    raise e
    
    web_print(
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
        web_print("Error when calling nems_main.fit_single_model")
        print(e)
        web_print("Fit failed.")
        raise e
        
    preview = stack.quick_plot_save(mode="png")
    r_id = update_results_table(stack, preview, user.username, user.labgroup)
    web_print("Results saved with id: {0}".format(r_id))
    
    r_est = stack.meta['r_est'][0]
    r_val = stack.meta['r_val'][0]
    
    # Manually release stack for garbage collection -- having memory issues?
    stack = None
    
    return jsonify(r_est=r_est, r_val=r_val)

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
    jerbKey = request.args.get('jerbKey')
    jerbVal = request.args.get('jerbVal')
    
    if not codeHash:
        codeHash = 'master'
    force_rerun = request.args.get('forceRerun', type=int)
    
    # TODO: need helper function to parse entries into formatted json
    #       --Comma-separted keys, comma-separated lists of values?
    #       i.e. jerbKey: a, b, c
    #            jerbVal: [a1, a2, a3], [b1, b2, b3], [c1, c2, c3]
    #       would translate to {a:[a1, a2, a3], b:[b1, b2, b3], c:[c1, c2, c3]}
    jerbQuery = {jerbKey:jerbVal}
    
    # TODO: add jerbQuery to tQueue table
    enqueue_models(
            cSelected, bSelected, mSelected,
            force_rerun=bool(force_rerun), user=user.username,
            codeHash=codeHash, 
            )
    return jsonify(data=True)
    