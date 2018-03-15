"""Placeholder views function file for modelpane.

Only used for testing the template right now.

"""

import copy
import inspect
import json
import pkgutil as pk

from flask import (
        request, render_template, Response, jsonify, redirect,
        url_for,
        )
import matplotlib.pyplot as plt, mpld3
import numpy as np

from nems_web.nems_analysis import app

FIGSIZE = (9, 3)  # width, height for matplotlib figures
mp_stack = None


@app.route('/modelpane_view', methods=['GET', 'POST'])
def modelpane_view():
    """Launches Modelpane window to inspect the model fit to the selected
    cell and model."""

    # reset stack if modelpane is restarted
    global mp_stack
    mp_stack = None

    bSelected = request.form.get('batch')[:3]
    cSelected = request.form.get('cellid')
    mSelected = request.form.get('modelname')

    try:
        mp_stack = ut.io.load_single_model(
                cellid=cSelected, batch=bSelected, modelname=mSelected,
                )
    except Exception as e:
        log.info("error when calling load_single_model")
        print(e)
        return Response(
                "Model has not been fitted yet, its fit file "
                "is not in local storage, "
                "or there was an error when loading the model."
                )
    # TODO: need to fix this for new split package structure
    #package = nm
    #all_mods = [
    #       modname for importer, modname, ispkg
    #        in pkgutil.iter_modules(package.__path__)
    #        ]
    # remove any modules that shouldn't show up as an option in modelpane
    #all_mods.remove('load_mat')

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
                [
                getattr(m, field)
                if hasattr(m, field) else "None"
                for field in fields[i]
                ]
            for i, m in enumerate(stackmods)
            ]
    types = [
                [
                str(type(getattr(m, field)))
                .replace("<class '","").replace("'>","")
                if hasattr(m, field) else "NoneType"
                for field in fields[i]
                ]
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

    # TODO: Fix this calculation for the range of possible stimulus choices.
    #       some times causes 'index out of range error'

    #dummy_mod = stackmods[-1]
    #data_max = (len(dummy_mod.d_in) - 1)
    #shape_len = dummy_mod.d_in[0]['stim'].ndim
    #if shape_len == 3:
    #    stim_max = (dummy_mod.d_in[mp_stack.plot_dataidx]['stim'].shape[1] - 1)
    #elif shape_len == 2:
    #    stim_max = (dummy_mod.d_in[mp_stack.plot_dataidx]['stim'].shape[0] - 1)
    #else:
        # TODO: Would shape length ever be anything other than 2 or 3?
    stim_max = "N/A"
    data_max = "N/A"

    return render_template(
            "/modelpane/modelpane.html",
            modules=[m.name for m in stackmods],
            plots=plots,
            title="Cellid: %s --- Model: %s"%(cSelected,mSelected),
            fields_values_types=fields_values_types,
            plottypes=plot_fns,
            #all_mods=all_mods,
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
                [
                getattr(m, field) if hasattr(m, field) else "None"
                for field in fields[i]
                ]
            for i, m in enumerate(stackmods)
            ]
    types = [
                [
                str(type(getattr(m, field)))
                .replace("<class '","").replace("'>","")
                if hasattr(m, field)
                else "NoneType"
                for field in fields[i]
                ]
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
            if callable(value):
                v = str(value)
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
        log.info("index was: " + str(i))
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
            log.info(
                    "Couldn't find attribute (%s)"
                    "for module at index (%d)."
                    %(f, modIdx)
                    )
            continue
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
                log.info("Error converting numpy.ndarray pickle-string back to array")
                print(e)
        else:
            log.info("Unexpected data type (" + t + ") for field: " + f)
            continue

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
            log.info("Issue with plot for: " + m.name)
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
    mod_found=False
    for importer, modname, ispkg in pk.iter_modules(nm.__path__):
        try:
            m=getattr(importer.find_module(modname).load_module(modname),module_name)
            log.info('Found %s'%module_name)
            mod_found=True
            break
        except:
            pass
    if mod_found is False:
        log.info('Module not found')
        m = None
    try:
        mp_stack.append(m)
    except Exception as e:
        log.info("Exception inside nems_modules > stack > append()")
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
    mod_found=False
    for importer, modname, ispkg in pk.iter_modules(nm.__path__):
        try:
            m=getattr(importer.find_module(modname).load_module(modname),module_name)
            print('Found %s'%module_name)
            mod_found=True
            break
        except:
            pass
    if mod_found is False:
        print('Module not found')
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
    mod_found=False
    for importer, modname, ispkg in pk.iter_modules(nm.__path__):
        try:
            m=getattr(importer.find_module(modname).load_module(modname),module_name)
            print('Found %s'%module_name)
            mod_found=True
            break
        except:
            pass
    if mod_found is False:
        print('Module not found')
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


@app.route('/get_kw_defaults')
def get_kw_defaults():
    """VERY DEPRECATED"""

    global mp_stack
    kw = request.args.get('kSelected')
    mod = request.args.get('modAffected')
    module = getattr(nm, mod)
    editable_fields = module.user_editable_fields

    # TODO: still getting ndarray type error when trying to jsonify.
    #       looks like it's b/c there are some times multi-dim nd arrays
    #       as editable fields, which can't be serialized.
    #if hasattr(nm, kw):
    #    # if above passed w/o exception, kw must have been the
    #    # base class default
    #    inst = module(mp_stack)
    #    defaults = {
    #            field: getattr(inst, field)
    #            for field in editable_fields
    #            }
    #    # convert any np types to scalar equivalents
    #    for key in defaults.keys():
    #        x = defaults[key]
    #        if isinstance(x, float) or isinstance(x, int) or isinstance(x, str):
    #            pass
    #        elif isinstance(x, list):
    #            #flatten list into string
    #            defaults[key] = ','.join(x)
    #        else:
    #            try:
    #                x = defaults[key][0]
    #            except:
    #                x = defaults[key]
    #            finally:
    #                try:
    #                    x = np.asscalar(x)
    #                except Exception as e:
    #                    print("couldn't convert to np.scalar")
    #                    print(type(x))
    #                   print(e)
    #else:
    if hasattr(nk, kw):
        fn = getattr(nk, kw)
        if isinstance(fn, list):
            defaults = {
                field: value for value, field
                in enumerate(editable_fields)
                }
        else:
            defaults = get_kw_args(fn, editable_fields)
    else:
        print("Default values could not be found for: " + kw)
        defaults = {
                field: value for value, field
                in enumerate(editable_fields)
                }

    return jsonify(**defaults)


def get_kw_args(function, editables):
    """DEPRECATED"""
    source = inspect.getsource(function)
    values = {}
    for field in source:
        # find index of first character of field arg
        i = source.find(field + "=")
        # find index of first character of assigned value
        # IMPORTANT: this assumes that field and value are separated by
        #            single '=' character.
        j = i + len(field) + 2
        # get the last index of the assigned value
        k = source[j:].find(',')
        if k == -1:
            k = source[j:].find(')')
        # get the value
        values[field] = source[j:k+1]

    return values

#@app.route('/refresh_modelpane')
def refresh_modelpane():
    """
    DEPRECATED VERSION -- keeping for now incase switch back

    Copy of modelpane_view code after loading model.
    Returns dict of arguments for re-rendering the modelpane template.

    """

    # TODO: Better way to do this instead of copy-pasting updates from main
    #        view function? Should convert to ajax eventually too instead of
    #        full refresh.
    global mp_stack

    cell = mp_stack.meta['cellid']
    model = mp_stack.meta['modelname']

    all_mods = [cls.name for cls in nm.base.nems_module.__subclasses__()]
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
    arrays = [[] for m in stackmods]
    for i, itr in enumerate(values):
        for value in itr:
            if isinstance(value, np.ndarray):
                array = pickle.dumps(value)
                arrays[i].append(array)
            else:
                arrays[i].append("")

    fields_values_types = []
    for i, itr in enumerate(fields):
        fields_values_types.append(zip(
                fields[i], values[i], types[i], arrays[i]
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
        stim_max = (dummy_mod.d_in[mp_stack.plot_dataidx]['stim'].shape[1]) - 1
    elif shape_len == 2:
        stim_max = (dummy_mod.d_in[mp_stack.plot_dataidx]['stim'].shape[0]) - 1
    else:
        # TODO: Would shape length ever be anything other than 2 or 3?
        stim_max = "N/A"


    return render_template(
            "/modelpane/modelpane.html",
            modules=[m.name for m in stackmods],
            plots=plots,
            title="Cellid: %s --- Model: %s"%(cell, model),
            fields_values_types=fields_values_types,
            plottypes=plot_fns,
            all_mods=all_mods,
            plot_stimidx=mp_stack.plot_stimidx,
            plot_dataidx=mp_stack.plot_dataidx,
            plot_stimidx_max=stim_max,
            plot_dataidx_max=data_max,
           )

