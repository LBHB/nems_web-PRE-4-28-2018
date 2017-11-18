"""View functions for the main page of the nems_analysis web interface.

UI Upate functions handle the initial state of the landing page as well as
refreshing analysis, batch, cell and model selectors when a user makes a
selection. The general procedure for each function is:
    -Get the user's selections from an AJAX call.
    -Query the database for a list of new entries for the dependent selector,
        based on the user's selections.
    -Return a JSON-serialized version of the list of new entries.

Analysis Editor functions populate the fields of the Analysis Editor modal,
add the data in the fields to the database, and/or delete an analysis from
the database.

Table Selection functions implement callbacks for the Preview button (so far),
as well as any other buttons whose behavior depends on selections within the
results table (as opposed to the selectors).

Miscellaneous functions handle other simple UI features that don't fit in
any other category (so far, just one function to serve error_log.txt).

"""

import copy
import datetime
from base64 import b64encode
import json

from flask import (
        render_template, jsonify, request, 
        )
from flask_login import login_required
import pandas.io.sql as psql
from sqlalchemy.orm import Query
from sqlalchemy import desc, asc, or_

from nems.web.nems_analysis import app
from nems.db import (
        Session, NarfAnalysis, NarfBatches, NarfResults, sBatch, NarfUsers,
        )
from nems.web.nems_analysis.ModelFinder import ModelFinder
from nems.web.plot_functions.PlotGenerator import PLOT_TYPES
from nems.web.account_management.views import get_current_user
#from nems.keyword_rules import keyword_test_routine
from nems.web.run_custom.script_utils import scan_for_scripts
from nems.utilities.print import web_print
from nems_config.defaults import UI_OPTIONS, DEMO_MODE
n_ui = UI_OPTIONS

try:
    import boto3
    import nems_config.Storage_Config as sc
    AWS = sc.USE_AWS
except:
    from nems_config.defaults import STORAGE_DEFAULTS
    sc = STORAGE_DEFAULTS
    AWS = False

# TODO: Currently, analysis edit/delete/etc are handled by name, 
#       which requires enforcing a unique name for each analysis. 
#       Should re-work selector to includ id with each name so that 
#       id can be used instead, since it's the primary key.
#       But each analysis should probably have a unique name anyway, 
#       so low priority change.



##################################################################
####################   UI UPDATE FUNCTIONS  ######################
##################################################################



@app.route('/')
def main_view():
    """Initialize the nems_analysis landing page.
    
    Queries the database to get lists of available analyses, batches,
    status filters, tag filters, and results columns.
    Specifies defaults for results columns, row limit and sort column.
    
    Returns:
    --------
    main.html : template
        The landing page template rendered with variables for analysislist,
        batchlist, collist, defaultcols, measurelist, defaultrowlimit,
        sortlist, defaultsort, statuslist, and taglist.
    
    """
    
    
    # TODO: figure out how to integrate sec_lvl/superuser mode
    #       maybe need to add sec_lvl column to analysis/batches/results?
    #       then can compare in query ex: if user.sec_lvl > analysis.sec_lvl
    user = get_current_user()
    
    session = Session()
    
    # .all() returns a list of tuples, so it's necessary to pull the
    # name elements out into a list by themselves.
    analyses = (
            session.query(NarfAnalysis)
            .filter(or_(
                    int(user.sec_lvl) == 9,
                    NarfAnalysis.public == '1',
                    NarfAnalysis.labgroup.ilike('%{0}%'.format(user.labgroup)),
                    NarfAnalysis.username == user.username,
                    ))
            .order_by(asc(NarfAnalysis.id))
            .all()
            )
    analysislist = [
            a.name for a in analyses
            ]
    analysis_ids = [
            a.id for a in analyses
            ]
    
    batchids = [
            i[0] for i in
            session.query(NarfBatches.batch)
            .distinct()
            #.filter(or_(
            #        int(user.sec_lvl) == 9,
            #        NarfBatches.public == '1',
            #        NarfBatches.labgroup.ilike('%{0}%'.format(user.labgroup)),
            #        NarfBatches.username == user.username,
            #        ))
            .all()
            ]
    batchnames = []
    for i in batchids:
        name = (
                session.query(sBatch.name)
                .filter(sBatch.id == i)
                .first()
                )
        if not name:
            batchnames.append('')
        else:
            batchnames.append(name.name)
    batchlist = [
            (batch + ': ' + batchnames[i])
            for i, batch in enumerate(batchids)
            ]
    batchlist.sort()
    
    # Default settings for results display.
    # TODO: let user choose their defaults and save for later sessions
    # cols are in addition to cellid, modelname and batch,
    # which are set up to be required
    defaultcols = n_ui.cols
    defaultrowlimit = n_ui.rowlimit
    defaultsort = n_ui.sort
    measurelist = n_ui.measurelist
    statuslist = [
            i[0] for i in
            session.query(NarfAnalysis.status)
            .filter(NarfAnalysis.name.in_(analysislist))
            .distinct().all()
            ]
    
    # Separate tags into list of lists of strings.
    tags = [
            i[0].split(",") for i in
            session.query(NarfAnalysis.tags)
            .filter(NarfAnalysis.name.in_(analysislist))
            .distinct().all()
            ]
    # Flatten list of lists into a single list of all tag strings
    # and remove leading and trailing whitespace.
    taglistbldupspc = [i for sublist in tags for i in sublist]
    taglistbldup = [t.strip() for t in taglistbldupspc]
    # Reform the list with only unique tags
    taglistbl = list(set(taglistbldup))
    # Finally, remove any blank tags and sort the list.
    taglist = [t for t in taglistbl if t != '']
    taglist.sort()
    
    # Returns all columns in the format 'NarfResults.columnName,'
    # then removes the leading 'NarfResults.' from each string
    collist = ['%s'%(s) for s in NarfResults.__table__.columns]
    collist = [s.replace('NarfResults.', '') for s in collist]
    sortlist = copy.deepcopy(collist)
    # Remove cellid and modelname from options toggles- make them required.
    required_cols = n_ui.required_cols
    for col in required_cols:
        collist.remove(col)

    # imported at top from PlotGenerator
    plotTypeList = PLOT_TYPES
    # imported at top from nems.web.run_scrits.script_utils
    scriptList = scan_for_scripts()
    
    session.close()
    
    return render_template(
            'main.html', analysislist=analysislist, analysis_ids=analysis_ids,
            batchlist=batchlist, collist=collist, defaultcols=defaultcols,
            measurelist=measurelist, defaultrowlimit=defaultrowlimit, 
            sortlist=sortlist, defaultsort=defaultsort,statuslist=statuslist,
            taglist=taglist, plotTypeList=plotTypeList, username=user.username,
            seclvl = int(user.sec_lvl), iso=n_ui.iso, snr=n_ui.snr,
            snri=n_ui.snri, scripts=scriptList,
            )


@app.route('/update_batch')
def update_batch():
    """Update current batch selection after an analysis is selected."""
    
    session = Session()
    blank = 0
    
    aSelected = request.args.get('aSelected', type=str)
    batch = (
            session.query(NarfAnalysis.batch)
            .filter(NarfAnalysis.name == aSelected)
            .first()
            )
    try:
        batch = batch.batch
    except Exception as e:
        print(e)
        batch = ''
        blank = 1
    
    session.close()
    
    return jsonify(batch=batch, blank=blank)
    

@app.route('/update_models')
def update_models():
    """Update the list of modelnames in the model selector after an
    analysis is selected.
    
    """
    
    session = Session()
    
    aSelected = request.args.get('aSelected', type=str)
    
    modeltree = (
            session.query(NarfAnalysis.modeltree)
            .filter(NarfAnalysis.name == aSelected)
            .first()
            )
    # Pass modeltree string from NarfAnalysis to a ModelFinder constructor,
    # which will use a series of internal methods to convert the tree string 
    # to a list of model names.
    if modeltree:
        mf = ModelFinder(modeltree[0])
    else:
        return jsonify(modellist="Model tree not found.")
        
    session.close()
    
    return jsonify(modellist=mf.modellist)


@app.route('/update_cells')
def update_cells():
    """Update the list of cells in the cell selector after a batch
    is selected (this will cascade from an analysis selection).
    
    Also updates current batch in NarfAnalysis for current analysis.
    
    """
    
    session = Session()
    # Only get the numerals for the selected batch, not the description.
    bSelected = request.args.get('bSelected')
    aSelected = request.args.get('aSelected')

    celllist = [
            i[0] for i in 
            session.query(NarfBatches.cellid)
            .filter(NarfBatches.batch == bSelected[:3])
            .all()
            ]
    
    batchname = (
            session.query(sBatch)
            .filter(sBatch.id == bSelected[:3])
            .first()
            )
    if batchname:
        batch = str(bSelected[:3] + ': ' + batchname.name)
    else:
        batch = bSelected
    analysis = (
            session.query(NarfAnalysis)
            .filter(NarfAnalysis.name == aSelected)
            .first()
            )
    # don't change batch association if batch is blank
    if analysis and bSelected:
        analysis.batch = batch

    session.commit()
    session.close()
    
    return jsonify(celllist=celllist)


@app.route('/update_results')
def update_results():
    """Update the results table after a batch, cell or model selection
    is changed.
    
    """
    
    user = get_current_user()
    session = Session()
    nullselection = """
            MUST SELECT A BATCH AND ONE OR MORE CELLS AND
            ONE OR MORE MODELS BEFORE RESULTS WILL UPDATE
            """
    
    bSelected = request.args.get('bSelected')
    cSelected = request.args.getlist('cSelected[]')
    mSelected = request.args.getlist('mSelected[]')
    colSelected = request.args.getlist('colSelected[]')
    # If no batch, cell or model is selected, display an error message.
    if (len(bSelected) == 0) or (not cSelected) or (not mSelected):
        return jsonify(resultstable=nullselection)
    # Only get numerals for selected batch.
    bSelected = bSelected[:3]
    # Use default value of 500 if no row limit is specified.
    rowlimit = request.args.get('rowLimit', 500)
    ordSelected = request.args.get('ordSelected')
    # Parse string into appropriate sqlalchemy method
    if ordSelected == 'asc':
        ordSelected = asc
    elif ordSelected == 'desc':
        ordSelected = desc
    sortSelected = request.args.get('sortSelected', 'cellid')

    # Always add cellid and modelname to column lists,
    # since they are required for selection behavior.
    cols = [
            getattr(NarfResults, 'cellid'),
            getattr(NarfResults, 'modelname'),
            ]
    cols += [
            getattr(NarfResults, c) for c in colSelected
            if hasattr(NarfResults, c)
            ]
    
    # Package query results into a DataFrame
    results = psql.read_sql_query(
            Query(cols,session)
            .filter(NarfResults.batch == bSelected)
            .filter(NarfResults.cellid.in_(cSelected))
            .filter(NarfResults.modelname.in_(mSelected))
            .filter(or_(
                    int(user.sec_lvl) == 9,
                    NarfResults.public == '1',
                    NarfResults.labgroup.ilike('%{0}%'.format(user.labgroup)),
                    NarfResults.username == user.username,
                    ))
            .order_by(ordSelected(getattr(NarfResults, sortSelected)))
            .limit(rowlimit).statement,
            session.bind
            )
    resultstable = results.to_html(
            index=False, classes="table-hover table-condensed",
            )
    
    session.close()
    
    return jsonify(resultstable=resultstable)


@app.route('/update_analysis')
def update_analysis():
    """Update list of analyses after a tag and/or filter selection changes."""
    
    user = get_current_user()
    session = Session()
    
    tagSelected = request.args.getlist('tagSelected[]')
    statSelected = request.args.getlist('statSelected[]')
    # If special '__any' value is passed, set tag and status to match any
    # string in ilike query.
    if '__any' in tagSelected:
        tagStrings = [NarfAnalysis.tags.ilike('%%')]
    else:
        tagStrings = [
                NarfAnalysis.tags.ilike('%{0}%'.format(tag))
                for tag in tagSelected
                ]
    if '__any' in statSelected:
        statStrings = [NarfAnalysis.status.ilike('%%')]
    else:
        statStrings = [
                NarfAnalysis.status.ilike('%{0}%'.format(stat))
                for stat in statSelected
                ]
    analyses = (
            session.query(NarfAnalysis)
            .filter(or_(*tagStrings))
            .filter(or_(*statStrings))
            .filter(or_(
                    int(user.sec_lvl) == 9,
                    NarfAnalysis.public == '1',
                    NarfAnalysis.labgroup.ilike('%{0}%'.format(user.labgroup)),
                    NarfAnalysis.username == user.username,
                    ))
            .order_by(asc(NarfAnalysis.id))
            .all()
            )
    analysislist = [
            a.name for a in analyses
            ]
    analysis_ids = [
            a.id for a in analyses
            ]
    
    session.close()
    
    return jsonify(analysislist=analysislist, analysis_ids=analysis_ids)


@app.route('/update_analysis_details')
def update_analysis_details():
    """Update contents of the analysis details popover when the analysis
    selection is changed.
    
    """
    
    session = Session()
    # TODO: Find a better/centralized place to store these options.
    # Columns to display in detail popup - add/subtract here if desired.
    detailcols = n_ui.detailcols
    
    aSelected = request.args.get('aSelected')
    
    cols = [
            getattr(NarfAnalysis,c) for c in detailcols 
            if hasattr(NarfAnalysis,c)
            ]
    
    # Package query results into a DataFrame
    results = psql.read_sql_query(
            Query(cols,session)
            .filter(NarfAnalysis.name == aSelected)
            .statement,
            session.bind
            )
    
    detailsHTML = """"""
    
    if results.size > 0:
        for col in detailcols:
            # Use a single line for id and status columns
            if (col == 'id') or (col == 'status'):
                detailsHTML += """
                    <p><strong>%s</strong>: %s</p>
                    """%(col,results.get_value(0, col))
                    # Use a header + paragraph for everything else
            else:
                detailsHTML += """
                    <h5><strong>%s</strong>:</h5>
                    <p>%s</p>
                    """%(col,results.get_value(0, col))
                    
    session.close()
    
    return jsonify(details=detailsHTML)


@app.route('/update_status_options')
def update_status_options():
    
    user = get_current_user()
    session = Session()
    
    statuslist = [
        i[0] for i in
        session.query(NarfAnalysis.status)
        .filter(or_(
                NarfAnalysis.public == '1',
                NarfAnalysis.labgroup.ilike('%{0}%'.format(user.labgroup)),
                NarfAnalysis.username == user.username,
                ))
        .distinct().all()
        ]

    session.close()
    
    return jsonify(statuslist=statuslist)


@app.route('/update_tag_options')
def update_tag_options():
    
    user = get_current_user()
    session = Session()
    
    tags = [
        i[0].split(",") for i in
        session.query(NarfAnalysis.tags)
        .filter(or_(
                NarfAnalysis.public == '1',
                NarfAnalysis.labgroup.ilike('%{0}%'.format(user.labgroup)),
                NarfAnalysis.username == user.username,
                ))
        .distinct().all()
        ]
    # Flatten list of lists into a single list of all tag strings
    # and remove leading and trailing whitespace.
    taglistbldupspc = [i for sublist in tags for i in sublist]
    taglistbldup = [t.strip() for t in taglistbldupspc]
    # Reform the list with only unique tags
    taglistbl = list(set(taglistbldup))
    # Finally, remove any blank tags and sort the list.
    taglist = [t for t in taglistbl if t != '']
    taglist.sort()
    
    session.close()
    
    return jsonify(taglist=taglist)
    

##############################################################################
################      edit/delete/new  functions for Analysis Editor #########
##############################################################################



#TODO: Handle Analysis Editor functions with an AJAX call instead of a form
#      submission so that the entire page doesn't have to be refreshed each
#      time - really only need to update the analysis selector's options.


@app.route('/edit_analysis', methods=['GET','POST'])
@login_required
def edit_analysis():
    """Take input from Analysis Editor modal and save it to the database.
    
    Button : Edit Analysis
    
    """
    
    user = get_current_user()
    session = Session()
    modTime = datetime.datetime.now().replace(microsecond=0)
    
    eName = request.args.get('name')
    eId = request.args.get('id')
    eStatus = request.args.get('status')
    eTags = request.args.get('tags')
    eQuestion = request.args.get('question')
    eAnswer = request.args.get('answer')
    eTree = request.args.get('tree')
    #TODO: add checks to require input inside form fields
    #      or allow blank so that people can erase stuff?

    # Turned this off for now -- can re-enable when rule needs are more stable
    # Make sure the keyword combination is valid using nems.keyword_rules
    #try:
    #    mf = ModelFinder(eTree)
    #    for modelname in mf.modellist:
    #        keyword_test_routine(modelname)
    #except Exception as e:
    #    return jsonify(success='Analysis not saved: \n' + str(e))
    
    if eId == '__none':
        checkExists = False
    else:
        checkExists = (
                session.query(NarfAnalysis)
                .filter(NarfAnalysis.id == eId)
                .first()
                )
    
    if checkExists:
        a = checkExists
        if (
                a.public
                or (user.labgroup in a.labgroup)
                or (a.username == user.username)
                ):
            a.name = eName
            a.status = eStatus
            a.question = eQuestion
            a.answer = eAnswer
            a.tags = eTags
            try:
                a.lastmod = modTime
            except:
                a.lastmod = str(modTime)
            a.modeltree = eTree
        else:
            web_print("You do not have permission to modify this analysis.")
            return jsonify(
                    success=("failed")
                    )
    # If it doesn't exist, add new sql alchemy object with the
    # appropriate attributes, which should get assigned to a new id
    else:
        # TODO: Currently copies user's labgroup by default.
        #       Is that the behavior we want?
        try:
            a = NarfAnalysis(
                    name=eName, status=eStatus, question=eQuestion,
                    answer=eAnswer, tags=eTags, batch='',
                    lastmod=modTime, modeltree=eTree, username=user.username,
                    labgroup=user.labgroup, public='0'
                    )
        except:
            a = NarfAnalysis(
                    name=eName, status=eStatus, question=eQuestion,
                    answer=eAnswer, tags=eTags, batch='',
                    lastmod=str(modTime), modeltree=eTree, username=user.username,
                    labgroup=user.labgroup, public='0'
                    )
            
        session.add(a)
    
    # For verifying correct logging - comment these out 
    # when not needed for testing.
    #print("Added the following analysis to database:")
    #print("------------------")
    #print("name:"); print(a.name)
    #print("question:"); print(a.question)
    #print("answer:"); print(a.answer)
    #print("status:"); print(a.status)
    #print("tags:"); print(a.tags)
    #print("model tree:"); print(a.modeltree)
    #print("-----------------\n\n")
    addedName = a.name
    session.commit()
    session.close()
    
    # After handling submissions, return user to main page so that it
    # refreshes with new analysis included in list    
    return jsonify(success="Analysis %s saved successfully."%addedName)


@app.route('/get_current_analysis')
def get_current_analysis():
    """Populate the Analysis Editor form with the database contents for the
    currently selected analysis.
    
    """
    
    session = Session()
    
    aSelected = request.args.get('aSelected')
    # If no analysis was selected, fill fields with blank text to
    # mimic 'New Analysis' behavior.
    if len(aSelected) == 0:
        return jsonify(
                name='', status='', tags='', question='',
                answer='', tree='',
                )
        
    a = (
        session.query(NarfAnalysis)
        .filter(NarfAnalysis.id == aSelected)
        .first()
        )
    
    session.close()
    
    return jsonify(
            id=a.id, name=a.name, status=a.status, tags=a.tags,
            question=a.question, answer=a.answer, tree=a.modeltree,
            )
        
    
@app.route('/check_analysis_exists')
def check_analysis_exists():
    """Check for a duplicate analysis name when an Analysis Editor form is
    submitted. If a duplicate exists, warn the user before overwriting.
    
    """
    
    session = Session()
    
    nameEntered = request.args.get('nameEntered')
    analysisId = request.args.get('analysisId')
    
    exists = False
    result = (
            session.query(NarfAnalysis)
            .filter(NarfAnalysis.name == nameEntered)
            .first()
            )
             
    # only set to True if id is different, so that
    # overwriting own analysis doesn't cause flag
    if result and (
            analysisId == '__none' or
            (int(result.id) != int(analysisId))
            ):
        exists = True
        
    session.close()
    
    return jsonify(exists=exists)


@app.route('/delete_analysis')
@login_required
def delete_analysis():
    """Delete the selected analysis from the database."""
    
    user = get_current_user()
    session = Session()
    
    success = False
    aSelected = request.args.get('aSelected')
    if len(aSelected) == 0:
        return jsonify(success=success)
    
    result = (
            session.query(NarfAnalysis)
            .filter(NarfAnalysis.id == aSelected)
            .first()
            )
    if result is None:
        return jsonify(success=success)

    # Leave these tests here incase accidental deletion
    # or some other issue occurs.
    # That way, the prints can be copy pasted back into a new analysis
    # form to restore the database entry.
    #print("checking for correct deletion. Deleting:")
    #print("name:"); print(result.name)
    #print("question:"); print(result.question)
    #print("answer:"); print(result.answer)
    #print("status:"); print(result.status)
    #print("tags:"); print(result.tags)
    #print("batch:"); print(result.batch)
    #print("model tree:"); print(result.modeltree)

    if (
            result.public
            or (result.username == user.username)
            or (user.labgroup in result.labgroup)
            ):
        success = True
        session.delete(result)
        session.commit()
    else:
        web_print("You do not have permission to delete this analysis.")
        return jsonify(success=success)
    
    session.close()

    return jsonify(success=success)



####################################################################
###############     TABLE SELECTION FUNCTIONS     ##################
####################################################################



@app.route('/get_preview')
def get_preview():
    """Queries the database for the filepath to the preview image
    for the selected cell, batch and model combination(s)
    
    """
    
    session = Session()
    
    # Only get the numerals for the selected batch, not the description.
    bSelected = request.args.get('bSelected', type=str)[:3]
    cSelected = request.args.getlist('cSelected[]')
    mSelected = request.args.getlist('mSelected[]')

    # if using demo database, get preview image from aws public bucket
    if DEMO_MODE:
        s3_client = boto3.client('s3')
        key = (
                'nems_saved_images/batch291/{0}/{1}.png'
                .format(cSelected[0], mSelected[0])
                )
        print("Inside get_preview, passed DEMO_MODE check. Key is: {0}".format(key))
        fileobj = s3_client.get_object(Bucket='nemspublic', Key=key)
        image=str(b64encode(fileobj['Body'].read()))[2:-1]
        return jsonify(image=image)
    
    figurefile = None
    # only need this to be backwards compatible with NARF preview images?
    path = (
            session.query(NarfResults)
            .filter(NarfResults.batch == bSelected)
            .filter(NarfResults.cellid.in_(cSelected))
            .filter(NarfResults.modelname.in_(mSelected))
            .first()
            )
    
    if not path:
        session.close()
        return jsonify(image='missing preview')
    else:
        figurefile = str(path.figurefile)
        session.close()
    
    # TODO: Make this not ugly, and incorporate check for sample images
    
    if AWS:
        s3_client = boto3.client('s3')
        try:
            key = figurefile[len(sc.DIRECTORY_ROOT):]
            fileobj = s3_client.get_object(Bucket=sc.PRIMARY_BUCKET, Key=key)
            image = str(b64encode(fileobj['Body'].read()))[2:-1]
            
            return jsonify(image=image)
        except Exception as e:
            print(e)
            print("key was: {0}".format(path.figurefile[len(sc.DIRECTORY_ROOT)]))
            try:
                key = figurefile[len(sc.DIRECTORY_ROOT)-1:]
                fileobj = s3_client.get_object(
                        Bucket=sc.PRIMARY_BUCKET, 
                        Key=key
                        )
                image = str(b64encode(fileobj['Body'].read()))[2:-1]
                return jsonify(image=image)
            except Exception as e:
                print(e)
                with open(app.static_folder + '/lbhb_logo.png', 'r+b') as img:
                    image = str(b64encode(img.read()))[2:-1]
                return jsonify(image=image)
    else:
        try:
            #local = sc.DIRECTORY_ROOT + path.figurefile.strip('/auto/data/code')
            with open('/' + figurefile, 'r+b') as img:
                image = str(b64encode(img.read()))[2:-1]
            return jsonify(image=image)
        except:
            try:
                with open(figurefile, 'r+b') as img:
                    image = str(b64encode(img.read()))[2:-1]
                return jsonify(image=image)
            except Exception as e:
                print(e)
                with open(app.static_folder + '/lbhb_logo.png', 'r+b') as img:
                    image = str(b64encode(img.read()))[2:-1]
                return jsonify(image=image)

    
    
###############################################################################
#################   SAVED SELECTIONS    #######################################
###############################################################################



@app.route('/get_saved_selections')
def get_saved_selections():
    session = Session()
    user = get_current_user()
    user_entry = (
            session.query(NarfUsers)
            .filter(NarfUsers.username == user.username)
            .first()
            )
    if not user_entry:
        return jsonify(response="user not logged in, can't load selections")
    selections = user_entry.selections
    null = False
    if not selections:
        null = True
    session.close()
    return jsonify(selections=selections, null=null)

@app.route('/set_saved_selections', methods=['GET', 'POST'])
def set_saved_selections():
    user = get_current_user()
    if not user.username:
        return jsonify(
                response="user not logged in, can't save selections",
                null=True,
                )
    session = Session()
    saved_selections = request.args.get('stringed_selections')
    user_entry = (
            session.query(NarfUsers)
            .filter(NarfUsers.username == user.username)
            .first()
            )
    user_entry.selections = saved_selections
    session.commit()
    session.close()
    
    return jsonify(response='selections saved', null=False)


############ jerb test #################
    
@app.route('/jerb_viewer')
def jerb_viewer():
    jerb_json = make_jerb_json()
    return render_template('jerb_test.html', json=jerb_json)


def make_jerb_json():
    
    user = get_current_user()
    
    session = Session()
    
    # .all() returns a list of tuples, so it's necessary to pull the
    # name elements out into a list by themselves.
    analyses = (
            session.query(NarfAnalysis)
            .filter(or_(
                    int(user.sec_lvl) == 9,
                    NarfAnalysis.public == '1',
                    NarfAnalysis.labgroup.ilike('%{0}%'.format(user.labgroup)),
                    NarfAnalysis.username == user.username,
                    ))
            .order_by(asc(NarfAnalysis.id))
            .all()
            )
    analysislist = [
            a.name for a in analyses
            ]

    batchids = [
            i[0] for i in
            session.query(NarfBatches.batch)
            .distinct()
            #.filter(or_(
            #        int(user.sec_lvl) == 9,
            #        NarfBatches.public == '1',
            #        NarfBatches.labgroup.ilike('%{0}%'.format(user.labgroup)),
            #        NarfBatches.username == user.username,
            #        ))
            .all()
            ]
    batchnames = []
    for i in batchids:
        name = (
                session.query(sBatch.name)
                .filter(sBatch.id == i)
                .first()
                )
        if not name:
            batchnames.append('')
        else:
            batchnames.append(name.name)
    batchlist = [
            (batch + ': ' + batchnames[i])
            for i, batch in enumerate(batchids)
            ]
    batchlist.sort()
    
    session.close()
    
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('nemsdata')
    
    jerb_json = {'name':'Analysis',
            'children':[],
            }
    
    for i, analysis in enumerate(analysislist):
        jerb_json['children'].append({'name':analysis, 'children':[]})
        jerb_json['children'][i]['children'].extend([
                {'name':'batch', 'children':[
                        {'name':batch, 'leaf':1}
                        for batch in batchlist
                        ]
                }, {'name':'models', 'children':[
                        {'name':model, 'leaf':1}
                        for model in ['fake','model','list']
                        ]
                }, {'name':'data', 'children':[
                        {'name':obj.key.strip('nems_in_cache/batch291/'), 'leaf':1}
                        for i, obj in enumerate(bucket.objects.filter(
                                Prefix='nems_in_cache/batch291/'
                                ))
                        if i < 20
                        ]
                }
                ])
        
    return jerb_json
    
    
    