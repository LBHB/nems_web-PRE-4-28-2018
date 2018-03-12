"""View functions for handling Submit Plot button.

Query database with batch, cell and model selection.
Filter out cells that don't meet minimum SNR/Iso/SNRi criteria.
Pass the returned NarfResults dataframe - along with measure, onlyFair and
includeOutliers criterio - to a PlotGenerator subclass based on the selected
plot type.
Use that PlotGenerator's generate_plot() method to generate <script> and <div>
components to pass back to the JS ajax function, which will insert them into
the display area in the browser.

"""

import logging
from base64 import b64encode

import pandas.io.sql as psql

from flask import render_template, jsonify, request, Response

from nems_web.nems_analysis import app
from nems_db.db import Session, NarfResults, NarfBatches
import nems_web.plot_functions.PlotGenerator as pg

log = logging.getLogger(__name__)

@app.route('/generate_plot_html')
def generate_plot_html():

    session = Session()

    plotType = request.args.get('plotType')
    bSelected = request.args.get('bSelected')[:3]
    mSelected = request.args.getlist('mSelected[]')
    cSelected = request.args.getlist('cSelected[]')
    measure = request.args.get('measure')
    onlyFair = request.args.get('onlyFair')
    if int(onlyFair):
        onlyFair = True
    else:
        onlyFair = False
    includeOutliers = request.args.get('includeOutliers')
    if int(includeOutliers):
        includeOutliers = True
    else:
        includeOutliers = False

    # TODO: Re-do this to include any new criteria dynamically instead of
    #       hard-coding snr/iso/snri.
    filterCriteria = {
            'snr' : float(request.args.get('snr')),
            'iso' : float(request.args.get('iso')),
            'snri' : float(request.args.get('snri')),
            }

    # TODO: Looks like this is what NARF does, but not 100% sure.
    # Always exclude negative values
    for key in filterCriteria:
        if filterCriteria[key] < 0:
            filterCriteria[key] = 0

    removalCount = 0
    for cellid in cSelected:
        dbCriteria = (
                session.query(NarfBatches)
                .filter(NarfBatches.batch == bSelected)
                .filter(NarfBatches.cellid == cellid)
                .all()
                )
        if dbCriteria:
            if len(dbCriteria) > 1:
                log.info(
                    "Multiple results found for cellid: %s in batch: %s"
                    %(cellid, bSelected)
                    )#!/usr/bin/env python3

            min_snr = min(dbCriteria[0].est_snr, dbCriteria[0].val_snr)
            min_isolation = dbCriteria[0].min_isolation
            min_snr_index = dbCriteria[0].min_snr_index

            a = (filterCriteria['snr'] > min_snr)
            b = (filterCriteria['iso'] > min_isolation)
            c = (filterCriteria['snri'] > min_snr_index)

            if a or b or c:
                filterReason = ""
                if a:
                    filterReason += (
                            "min snr: %s -- was less than criteria: %s\n"
                            %(min_snr, filterCriteria['snr'])
                            )
                if b:
                    filterReason += (
                            "min iso: %s -- was less than criteria: %s\n"
                            %(min_isolation, filterCriteria['iso'])
                            )
                if c:
                    filterReason += (
                            "min snr index: %s -- was less than criteria: %s\n"
                            %(min_snr_index, filterCriteria['snri'])
                            )
                #log.info(
                #    "Removing cellid: %s,\n"
                #    "because: %s"
                #    %(cellid, filterReason)
                #    )
                cSelected.remove(cellid)
                removalCount += 1
        else:
            log.info(
                "No entry in NarfBatches for cellid: %s in batch: %s"
                %(cellid, bSelected)
                )
            cSelected.remove(cellid)
            removalCount += 1
    log.info("Number of cells filtered due to snr/iso criteria: %d"%removalCount)

    results = psql.read_sql_query(
            session.query(NarfResults)
            .filter(NarfResults.batch == bSelected)
            .filter(NarfResults.cellid.in_(cSelected))
            .filter(NarfResults.modelname.in_(mSelected))
            .statement,
            session.bind
            )
    log.debug("Results retrieved, with size: {}".format(results.size))
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
    log.debug("Modelnames re-ordered and filtered to: {}".format(ordered_models))
    Plot_Class = getattr(pg, plotType)
    plot = Plot_Class(
            data=results, measure=measure, models=ordered_models,
            fair=onlyFair, outliers=includeOutliers,
            )
    log.debug("Plot successfully initialized")
    if plot.emptycheck:
        log.info('Plot checked empty after forming data array')
        return jsonify(script='Empty',div='Plot')
    else:
        plot.generate_plot()

    session.close()

    if hasattr(plot, 'script') and hasattr(plot, 'div'):
        return jsonify(script=plot.script, div=plot.div)
    elif hasattr(plot, 'html'):
        return jsonify(html=plot.html)
    elif hasattr(plot, 'img_str'):
        image = str(b64encode(plot.img_str))[2:-1]
        return jsonify(image=image)
    else:
        return jsonify(script="Couldn't find anything ", div="to return")


@app.route('/plot_window')
def plot_window():
    return render_template('/plot/plot.html')



### DEPRECATED ###
def load_plot_args(request, session):
    """Combines user selections and database entries into a dict of arguments.

    Queries database based on user selections for batch, cell and modelname and
    packages the results into a Pandas DataFrame. The DataFrame, along with
    the performance measure, fair and outliers options from the nems_analysis
    web interface are then packaged into a dict structure to match the
    argument requirements of the Plot_Generator base class.
    Since all Plot_Generator objects use the same required arguments, this
    eliminates the need to repeat the selection and querying code for every
    view function.

    Arguments:
    ----------
    request : flask request context
        Current request context generated by flask. See flask documentation.
    session : sqlalchemy database session
        An open transaction with the database. See sqlalchemy documentation.

    Returns:
    --------
    {} : dict-like
        A dictionary specifying the arguments that should be passed to a
        Plot_Generator object.

    Note:
    -----
    This adds no additional functionality, it is only used to simplify
    the code for the above view functions. If desired, it can be copy-pasted
    back into the body of each view function instead, with few changes.

    """

    bSelected = request.form.get('batch')[:3]
    mSelected = request.form.getlist('modelnames[]')
    cSelected = request.form.getlist('celllist[]')
    measure = request.form['measure']
    onlyFair = request.form.get('onlyFair')
    if onlyFair == "fair":
        onlyFair = True
    else:
        onlyFair = False
    includeOutliers = request.form.get('includeOutliers')
    if includeOutliers == "outliers":
        includeOutliers = True
    else:
        includeOutliers = False

    #useSNRorIso = (request.form.get('plotOption[]'),request.form.get('plotOpVal'))

    # TODO: filter results based on useSNRorIso before passing data to plot generator
    # note: doing this here instead of in plot generator since it requires db access
    #       make a list of cellids that fail snr/iso criteria
    #       then remove all rows of results where cellid is in that list

    results = psql.read_sql_query(session.query(NarfResults).filter\
              (NarfResults.batch == bSelected).filter\
              (NarfResults.cellid.in_(cSelected)).filter\
              (NarfResults.modelname.in_(mSelected)).statement,session.bind)

    return {
        'data':results,'measure':measure,'fair':onlyFair,
        'outliers':includeOutliers,
        }



