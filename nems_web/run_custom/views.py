""" view function to handle running custom scripts. """

import importlib

from flask import request, jsonify
from nems_web.nems_analysis import app
from nems_web.run_custom.script_utils import scan_for_scripts

@app.route('/run_custom')
def run_custom():
    argsdict = {
            'batch' : request.args.get('bSelected')[:3],
            'models' : request.args.getlist('mSelected[]'),
            'cells' : request.args.getlist('cSelected[]'),
            'onlyFair' : bool(request.args.get('onlyFair')),
            'includeOutliers' : bool(request.args.get('includeOutliers')),
            'snr' : float(request.args.get('snr')),
            'iso' : float(request.args.get('iso')),
            'snri' : float(request.args.get('snri')),
            'measure' : request.args.get('measure'),
            }
    script_name = ('nems_scripts.' + request.args.get('scriptName'))
    script = importlib.import_module(script_name)
    script_output = script.run_script(argsdict)
    
    if isinstance(script_output, dict) and 'html' in script_output:
        return jsonify(html=script_output['html'])
    else:
        return jsonify(
                html="Script: {0} has no html output to display"
                .format(script_name)
                )
        
@app.route('/reload_scripts')
def reload_scripts():
    scriptlist = scan_for_scripts()
    return jsonify(scriptlist=scriptlist)
    