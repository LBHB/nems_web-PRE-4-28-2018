"""Placeholder views function file for modelpane.

Only used for testing the template right now.

"""

import copy
import json

from flask import (
        Flask, request, render_template, Session, Response, jsonify, redirect, 
        url_for,
        )
import matplotlib.pyplot as plt, mpld3
import numpy as np

import nems.modules as nm
import nems.fitters as nf
import nems.keywords as nk
import nems.utils as nu
import nems.main as nems

# When copy-pasting updates from other modelpane:
#  --replace 'from nems_analysis import app' with 'app = Flask(__name__)
#  --add    
#           if __name__ == '__main__':
#               app.run(host="0.0.0.0", port=8000, debug=True)
#
#    to the bottom of the file
# --change bSelected, cSelected and mSelected to be assigned manually
#      instead of pulling from request.args
# --make sure to copy changes to .js, .css and .html files as well
# --Everything else should stay the same, as of 7/5/2017
#
# -Jacob


app = Flask(__name__)

FIGSIZE = (12,4) # width, height for matplotlib figures
mp_stack = None

@app.route('/')
def modelpane_view():
    """Launches Modelpane window to inspect the model fit to the selected
    cell and model."""

    """
    copy-paste from nems_main for testing
    
    if model has not been fitted, will need to run the script below in
    i-python to fit the model, then refresh browser.
    
    import lib.nems_main as nems
    cellid='bbl061h-a1'
    batch=291
    modelname='fb18ch100_ev_wc01_fir10_dexp_fit00'
    nems.fit_single_model(cellid,batch,modelname)
    """
    
    # reset stack if modelpane is restarted
    global mp_stack
    mp_stack = None

    #batch (as string, not int)
    bSelected = "291"
    #cellid
    cSelected = "bbl061h-a1"
    #modelname
    mSelected = "fb18ch100_ev_wc01_fir10_dexp_fit00"

    try:
        mp_stack = nems.load_single_model(
                cellid=cSelected, batch=bSelected, modelname=mSelected,
                )
    except:
        return Response(
                "Model has not been fitted yet, or its fit file "
                "is not in local storage."
                )
        
    all_mods = [cls.name for cls in nm.nems_module.__subclasses__()]
    # remove any modules that shouldn't show up as an option in modelpane
    all_mods.remove('load_mat')
    
    stackmods = mp_stack.modules[1:]
    plots = re_render_plots()
    # make double sure that all figures close after loop
    # to avoid excess memory usage.
    plt.close("all")
    
    # Need to use copy to avoid overriding modules' attributes
    plot_fns = copy.deepcopy([m.plot_fns for m in stackmods])
    for i, pf in enumerate(plot_fns):
        for j, f in enumerate(pf):
            newf = printable_plot_name(f)
            plot_fns[i][j] = newf
    
    fields = [m.user_editable_fields for m in stackmods]
    values = [
            [getattr(m, field) for field in fields[i]]
            for i, m in enumerate(stackmods)
            ]
    types = [
            [str(type(getattr(m, field)))
            .replace("<class '","").replace("'>","")
            for field in fields[i]]
            for i, m in enumerate(stackmods)
            ]
    for i, itr in enumerate(values):
        for j, value in enumerate(itr):
            if isinstance(value, np.ndarray):
                a = str(value.tolist())
                values[i][j] = a
    fields_values_types = []
    for i, itr in enumerate(fields):
        fields_values_types.append(zip(
                fields[i], values[i], types[i],
                ))

    # TODO: dummy_mod selection is assuming that there's something in the stack
    #       other than load_mat and standard_est_eval.
    #       Is this a good assumption?
    try:
        dummy_mod = stackmods[1]
    except IndexError:
        dummy_mod = stackmods[0]
        print("Stack only has data loader and standard eval?")
    data_max = (len(dummy_mod.d_in) - 1)
    shape_len = len(dummy_mod.d_in[0]['stim'].shape)
    if shape_len == 3:
        stim_max = (dummy_mod.d_in[mp_stack.plot_dataidx]['stim'].shape[1])
    elif shape_len == 2:
        stim_max = (dummy_mod.d_in[mp_stack.plot_dataidx]['stim'].shape[0])
    else:
        # TODO: Would shape length ever be anything other than 2 or 3?
        stim_max = "N/A"
    
    return render_template(
            "/modelpane/modelpane.html", 
            modules=[m.name for m in stackmods],
            plots=plots,
            title="Cellid: %s --- Model: %s"%(cSelected,mSelected),
            fields_values_types=fields_values_types,
            plottypes=plot_fns,
            all_mods=all_mods,
            plot_stimidx=mp_stack.plot_stimidx,
            plot_dataidx=mp_stack.plot_dataidx,
            plot_stimidx_max=stim_max,
            plot_dataidx_max=data_max,
           )
   

@app.route('/refresh_modelpane')
def refresh_modelpane_json(modIdx):
    
    global mp_stack

    stackmods = mp_stack.modules[modIdx:]
    plots = re_render_plots(modIdx)
    # make double sure that all figures close after loop
    # to avoid excess memory usage.
    plt.close("all")

    fields = [m.user_editable_fields for m in stackmods]
    values = [
            [getattr(m, field) for field in fields[i]]
            for i, m in enumerate(stackmods)
            ]
    types = [
            [str(type(getattr(m, field)))
            .replace("<class '","").replace("'>","")
            for field in fields[i]]
            for i, m in enumerate(stackmods)
            ]
    for i, itr in enumerate(values):
        for j, value in enumerate(itr):
            if isinstance(value, np.ndarray):
                v = str(value.tolist())
                values[i][j] = v
            if isinstance(value, type(None)):
                v = "None"
                values[i][j] = v
    
    return jsonify(
            plots=plots,
            fields=fields,
            values=values,
            types=types,
            modIdx=(modIdx-1),
           )
    

@app.route('/update_modelpane_plot')
def update_modelpane_plot():
    """Re-render the plot for the affected module after changing
    the selected plot type.
    
    """
    
    global mp_stack
    
    modAffected = request.args.get('modAffected')
    plotType = request.args.get('plotType')
    if not modAffected:
        return jsonify(html="<p>Affected module is None<p>")
    
    try:
        i = [mod.name for mod in mp_stack.modules].index(modAffected)
    except Exception as e:
        print(e)
        return Response('')
    
    try:
        m = mp_stack.modules[i]
    except Exception as e:
        print(e)
        print("index was: " + str(i))
        return Response('')
    
    p = plt.figure(figsize=FIGSIZE)
    plot_fn = getattr(nu, plotType)
    plot_fn(m)
    html = mpld3.fig_to_html(p)
    
    return jsonify(html=html)
                 

@app.route('/update_data_idx')
def update_data_idx():
    
    global mp_stack
    plot_dataidx = request.args.get('plot_dataidx')

    mp_stack.plot_dataidx = int(plot_dataidx)
    # reset stim idx to 0 when data idx changes, since max will likely change
    mp_stack.plot_stimidx = 0
    plots = re_render_plots()
    
    stackmods = mp_stack.modules[1:]
    dummy_mod = stackmods[1]
    shape_len = len(dummy_mod.d_in[0]['stim'].shape)
    if shape_len == 3:
        stim_max = (dummy_mod.d_in[mp_stack.plot_dataidx]['stim'].shape[1]) - 1
    elif shape_len == 2:
        stim_max = (dummy_mod.d_in[mp_stack.plot_dataidx]['stim'].shape[0]) - 1
    else:
        # TODO: Would shape length ever be anything other than 2 or 3?
        stim_max = "N/A"
    
    return jsonify(plots=plots, stim_max=stim_max)
    
@app.route('/update_stim_idx')
def update_stim_idx():
    
    global mp_stack
    plot_stimidx = request.args.get('plot_stimidx')
    
    # data idx stays the same
    mp_stack.plot_stimidx = int(plot_stimidx)
    
    print("stim idx:")
    print(str(int(plot_stimidx)))
    
    plots = re_render_plots()
    
    return jsonify(plots=plots)

@app.route('/update_module')
def update_module():
    
    global mp_stack
    fields = request.args.getlist('fields[]')
    values = request.args.getlist('values[]')
    types = request.args.getlist('types[]')
    if (not fields) or (not values) or (not types):
        raise ValueError("No fields and/or values and/or types came through")
    fields_values_types = zip(fields, values, types)

    modAffected = request.args.get('modAffected')
    modIdx = nu.find_modules(mp_stack, modAffected)
    if modIdx:
        modIdx = modIdx[0]
    else:
        raise ValueError("No module index found for: %s"%modAffected)
    
    for f, v, t in fields_values_types:
        #TODO: figure out a good way to set type dynamically instead of trying
        #      to think of every possible data type."
        if not hasattr(mp_stack.modules[modIdx], f):
            raise AttributeError(
                    "Couldn't find attribute (%s)"
                    "for module at index (%d)."
                    %(f, modIdx)
                    )
        if t == "NoneType":
            v = None
        elif t == "str":
            pass
        elif t == "int":
            v = int(v)
        elif t == "float":
            v = float(v)
        elif t == "list":
            v = v.strip('[').strip(']').replace(' ','')
            v = v.split(',')
        elif t == "bool":
            v = v.lower()
            if v == "true":
                v = True
            else:
                v = False
        elif t == "numpy.ndarray":
            try:
                a = json.loads(v)
                v = np.array(a)
            except Exception as e:
                print("Error converting numpy.ndarray pickle-string back to array")
                print(e)
        else:
            raise TypeError("Unexpected data type (" + t + ") for field: " + f)
                
        setattr(mp_stack.modules[modIdx], f, v)
        
    mp_stack.evaluate(start=modIdx)
    
    #return jsonify(success=True)
    return refresh_modelpane_json(modIdx)
    

def re_render_plots(modIdx=1):
    
    global mp_stack
    
    stackmods = mp_stack.modules[modIdx:]
    plot_list = []
    for m in stackmods:
        try:
            p = plt.figure(figsize=FIGSIZE)
            m.do_plot(m)
            html = mpld3.fig_to_html(p)
            plot_list.append(html)
            plt.close(p)
        except Exception as e:
            print("Issue with plot for: " + m.name)
            print(e)
            plot_list.append(
                    "Couldn't generate plot for this module."
                    "Make sure data and stim idx are within the listed range."
                    )
            continue

    return plot_list

def convert(string, type_):
    """Adapted from stackoverflow. Not quite working as desired.
    Stopped using for now but wanted to retain for later use.
    
    """
    import importlib
    import builtins
    try:
        cls = getattr(builtins, type_)
    except AttributeError:
        module, type_ = type_.rsplit(".", 1)
        module = importlib.import_module(module)
        cls = getattr(module, type_)
    return cls(string)
    

@app.route('/append_module', methods=['GET','POST'])
def append_module():

    global mp_stack
    
    module_name = request.form.get('a_module')
    
    try:
        m = getattr(nm, module_name)
    except Exception as e:
        print(e)
        m = None
    try:    
        mp_stack.append(m)
    except Exception as e:
        print("Exception inside nems_modules > stack > append()")
        print(e)
    
    return redirect(url_for('refresh_modelpane'))

@app.route('/insert_module', methods=['GET','POST'])
def insert_module():
    
    #TODO: Not currently working, html components disabled for now
    global mp_stack
    
    module_name = request.form.get('a_module')
    idx = request.form.get('idx')
    if not idx:
        print("No insertion index selected")
        return redirect(url_for('refresh_modelpane'))
    idx = int(idx)
    
    try:
        m = getattr(nm, module_name)
    except Exception as e:
        print(e)
        m = None
    try:
        mp_stack.insert(mod=m, idx=idx)
    except Exception as e:
        print("Exception inside nem_modules > stack > insert()")
        print(e)

    return redirect(url_for('refresh_modelpane'))

@app.route('/remove_module', methods=['GET','POST'])
def remove_module():
    
    global mp_stack
    
    module_name = request.form.get('r_module')
    # TODO: all_idx not getting picked up by form submission? disabled for now
    all_idx = request.form.get('all_idx')
    if not all_idx:
        all_idx = False
    else:
        all_idx = True
    
    try:
        m = getattr(nm, module_name)
    except Exception as e:
        print(e)
        m = None
    try:
        mp_stack.remove(mod=m, all_idx=all_idx)
    except Exception as e:
        print("Exception inside nems_modules > stack > remove()")
        print(e)

    # refresh modelpane view
    return redirect(url_for('refresh_modelpane'))


def printable_plot_name(plot_fn):
    p = str(plot_fn).replace('<function ', '')
    i = p.find(' at')
    if i > 0:
        p = p[:i]
    return p



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
