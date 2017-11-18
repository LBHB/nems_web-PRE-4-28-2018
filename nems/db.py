#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

nems_db library

Created on Fri Jun 16 05:20:07 2017

@author: svd
"""

import os
import sys
import datetime

import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base
import pandas as pd
import pandas.io.sql as psql

import nems_config.defaults
from nems.utilities.print import web_print

try:
    import nems_config.Storage_Config as sc
    AWS = sc.USE_AWS
    #if AWS:
        #from nems.EC2_Mgmt import check_instance_count
except Exception as e:
    print(e)
    sc = nems_config.defaults.STORAGE_DEFAULTS
    AWS = False

# Database settings
# To specify database settings, store a file named Database_Info.py in the
# nems_config directory (inside the top-level package folder) with this format:
#   host = 'hosturl'
#   user = 'username'
#   passwd = 'password'
#   database = 'database'
# Order doesn't matter.
try:
    import nems_config.Database_Info as db
    db_uri = 'mysql+pymysql://{0}:{1}@{2}/{3}'.format(
                    db.user,db.passwd,db.host,db.database
                    )
except Exception as e:
    print('No database info detected')
    print(e)
    path = os.path.dirname(nems_config.defaults.__file__)
    i = path.find('nems/nems_config')
    db_path = (path[:i+5] + 'nems_sample/demo_db.db')
    db_uri = 'sqlite:///' + db_path + '?check_same_thread=False'
    nems_config.defaults.DEMO_MODE = True
    print('Using demo mode: {0}'.format(nems_config.defaults.DEMO_MODE))

try:
    import nems_config.Cluster_Database_Info as clst_db
    # format:      dialect+driver://username:password@host:port/database
    # to-do default port = 3306
    if not hasattr(clst_db, 'port'):
        print("No port specified for cluster db info, using default port")
        port = 3306
    else:
        port = clst_db.port
        
    clst_db_uri = 'mysql+pymysql://{0}:{1}@{2}:{3}/{4}'.format(
                        clst_db.user, clst_db.passwd, clst_db.host,
                        port, clst_db.database,
                        )
    
except Exception as e:
    print('No cluster database info detected')
    print(e)
    path = os.path.dirname(nems_config.defaults.__file__)
    i = path.find('nems/nems_config')
    db_path = (path[:i+5] + 'nems_sample/demo_db.db')
    clst_db_uri = 'sqlite:///' + db_path + '?check_same_thread=False'

    
# sets how often sql alchemy attempts to re-establish connection engine
# TODO: query db for time-out variable and set this based on some fraction of that
POOL_RECYCLE = 7200;

# create a database connection engine
engine = create_engine(db_uri, pool_recycle=POOL_RECYCLE)

#create base class to mirror existing database schema
Base = automap_base()
Base.prepare(engine, reflect=True)

NarfUsers = Base.classes.NarfUsers
NarfAnalysis = Base.classes.NarfAnalysis
NarfBatches = Base.classes.NarfBatches
NarfResults = Base.classes.NarfResults
tQueue = Base.classes.tQueue
tComputer = Base.classes.tComputer
sCellFile = Base.classes.sCellFile
sBatch = Base.classes.sBatch
gCellMaster = Base.classes.gCellMaster

# import this when another module needs to use the database connection.
# used like a class - ex: 'session = Session()'
Session = sessionmaker(bind=engine)


# Same as above, but duplicated for use w/ cluster
cluster_engine = create_engine(
        clst_db_uri, pool_recycle=POOL_RECYCLE,
        )

cluster_Base = automap_base()
cluster_Base.prepare(cluster_engine, reflect=True)

cluster_tQueue = cluster_Base.classes.tQueue
cluster_tComputer = cluster_Base.classes.tComputer

cluster_Session = sessionmaker(bind=cluster_engine)


def enqueue_models(
        celllist, batch, modellist, force_rerun=False,
        user=None, codeHash="master",
        ):
    """Call enqueue_single_model for every combination of cellid and modelname
    contained in the user's selections.
    
    Arguments:
    ----------
    celllist : list
        List of cellid selections made by user.
    batch : string
        batch number selected by user.
    modellist : list
        List of modelname selections made by user.
    
    Returns:
    --------
    pass_fail : list
        List of strings indicating success or failure for each job that
        was supposed to be queued.
        
    See Also:
    ---------
    . : enqueue_single_model
    Narf_Analysis : enqueue_models_callback
    
    """
    # Not yet ready for testing - still need to coordinate the supporting
    # functions with the model queuer.
    session = Session()
    cluster_session = cluster_Session()
    
    pass_fail = []
    for model in modellist:
        for cell in celllist:
            queueid, message = _enqueue_single_model(
                        cell, batch, model, force_rerun, user,
                        session, cluster_session, codeHash,
                        )
            if queueid:
                pass_fail.append(
                        '\n queueid: {0},'
                        '\n message: {1}'
                        .format(queueid, message)
                        )
            else:
                pass_fail.append(
                        '\nFailure: {0}, {1}, {2}'
                        .format(cell, batch, model)
                        )
                
    # Can return pass_fail instead if prefer to do something with it in views
    print('\n'.join(pass_fail))
    
    session.close()
    cluster_session.close()
    return


def _enqueue_single_model(
        cellid, batch, modelname, force_rerun, user,
        session, cluster_session, codeHash,
        ):
    
    """Adds a particular model to the queue to be fitted.
    
    Returns:
    --------
    queueid : int
        id (primary key) that was assigned to the new tQueue entry, or -1.
    message : str
        description of the action taken, to be reported to the console by
        the calling enqueue_models function.
        
    See Also:
    ---------
    Narf_Analysis : enqueue_single_model
    
    """

    
    # TODO: anything else needed here? this is syntax for nems_fit_single
    #       command prompt wrapper in main nems folder.
    commandPrompt = (
            "/home/nems/anaconda3/bin/python "
            "/home/nems/nems/nems_fit_single.py {0} {1} {2}"
            .format(cellid, batch, modelname)
            )

    note = "%s/%s/%s"%(cellid,batch,modelname)
    
    result = (
            session.query(NarfResults)
            .filter(NarfResults.cellid == cellid)
            .filter(NarfResults.batch == batch)
            .filter(NarfResults.modelname == modelname)
            .first()
            )
    if result and not force_rerun:
        web_print("Entry in NarfResults already exists for: %s, skipping.\n"%note)
        session.close()
        cluster_session.close()
        return -1, 'skip'
    
    #query tQueue to check if entry with same cell/batch/model already exists
    qdata = (
            cluster_session.query(cluster_tQueue)
            .filter(cluster_tQueue.note == note)
            .first()
            )
    
    job = None
    message = None
    
    if qdata and (int(qdata.complete) <= 0):
        #TODO:
        #incomplete entry for note already exists, skipping
        #update entry with same note? what does this accomplish?
        #moves it back into queue maybe?
        message = "Incomplete entry for: %s already exists, skipping.\n"%note
        job = qdata
    elif qdata and (int(qdata.complete) == 2):
        #TODO:
        #dead queue entry for note exists, resetting
        #update complete and progress status each to 0
        #what does this do? doesn't look like the sql is sent right away,
        #instead gets assigned to [res,r]
        message = "Dead queue entry for: %s already exists, resetting.\n"%note
        qdata.complete = 0
        qdata.progress = 0
        job = qdata
    elif qdata and (int(qdata.complete) == 1):
        #TODO:
        #resetting existing queue entry for note
        #update complete and progress status each to 0
        #same as above, what does this do?
        message = "Resetting existing queue entry for: %s\n"%note
        qdata.complete = 0
        qdata.progress = 0
        job = qdata
    else:
        #result must not have existed, or status value was greater than 2
        # add new entry
        message = "Adding job to queue for: %s\n"%note
        job = _add_model_to_queue(commandPrompt, note, user, codeHash)
        cluster_session.add(job)
        
    cluster_session.commit()
    queueid = job.id
    
    if AWS:
        # TODO: turn this back on if/when automated cluster management is
        #       implemented.
        pass
        #check_instance_count()
    else:
        pass

    return queueid, message
    
def _add_model_to_queue(
        commandPrompt, note, user, codeHash, priority=1, rundataid=0,
        ):
    """
    Returns:
    --------
    job : tQueue object instance
        tQueue object with variables assigned inside function based on
        arguments.
        
    See Also:
    ---------
    Narf_Analysis: dbaddqueuemaster
    
    """
    
    #TODO: does user need to be able to specificy priority and rundataid somewhere
    #       in web UI?
    
    #TODO: why is narf version checking for list vs string on prompt and note?
    #       won't they always be a string passed from enqueue function?
    #       or want to be able to add multiple jobs manually from command line?
    #       will need to rewrite with for loop to to add this functionality in the
    #       future if desired
    
    job = cluster_tQueue()
    
    if user:
        user = user
    else:
        user = 'None'
    linux_user = 'nems'
    allowqueuemaster=1
    waitid = 0
    dt = str(datetime.datetime.now().replace(microsecond=0))
    
    job.rundataid = rundataid
    job.progname = commandPrompt
    job.priority = priority
    job.parmstring = ''
    job.queuedate = dt
    job.allowqueuemaster = allowqueuemaster
    job.user = user
    job.linux_user = linux_user
    job.note = note
    job.waitid = waitid
    job.codeHash = codeHash
    
    return job

def update_job_complete(queueid):
    # mark job complete
    # svd old-fashioned way of doing
    #sql="UPDATE tQueue SET complete=1 WHERE id={}".format(queueid)
    #result = conn.execute(sql)
    #conn.close()
    conn = cluster_engine.connect()
    # tick off progress, job is live
    sql = (
            "UPDATE tQueue SET complete=1 WHERE id={}"
            .format(queueid)
            )
    r = conn.execute(sql)
    conn.close()
    return r
    """
    cluster_session = cluster_Session()
    # also filter based on note? - should only be one result to match either
    # filter, but double checks to make sure there's no conflict
    #note = "{0}/{1}/{2}".format(cellid, batch, modelname)
    #.filter(tQueue.note == note)
    qdata = (
            cluster_session.query(cluster_tQueue)
            .filter(cluster_tQueue.id == queueid)
            .first()
            )
    if not qdata:
        # Something went wrong - either no matching id, no matching note,
        # or mismatch between id and note
        print("Invalid query result when checking for queueid & note match")
        print("/n for queueid: %s"%queueid)
    else:
        qdata.complete = 1
        cluster_session.commit()
       
    cluster_session.close()
    """
    
def update_job_start(queueid):
    conn = cluster_engine.connect()
    # mark job as active and progress set to 1
    sql = (
            "UPDATE tQueue SET complete=-1,progress=1 WHERE id={}"
            .format(queueid)
            )
    r = conn.execute(sql)
    conn.close()
    return r

def update_job_tick(queueid):
    conn = cluster_engine.connect()
    # tick off progress, job is live
    sql = (
            "UPDATE tQueue SET progress=progress+1 WHERE id={}"
            .format(queueid)
            )
    r = conn.execute(sql)
    conn.close()
    return r

def save_results(stack, preview_file, queueid=None):
    session = Session()
    cluster_session = cluster_Session()
    
    # Can't retrieve user info without queueid, so if none was passed
    # use the default blank user info
    if queueid:
        job = (
                cluster_session.query(cluster_tQueue)
                .filter(cluster_tQueue.id == queueid)
                .first()
                )
        username = job.user
        narf_user = (
                session.query(NarfUsers)
                .filter(NarfUsers.username == username)
                .first()
                )
        labgroup = narf_user.labgroup
    else:
        username = ''
        labgroup = 'SPECIAL_NONE_FLAG'

    results_id = update_results_table(stack, preview_file, username, labgroup)
    
    session.close()
    cluster_session.close()
    
    return results_id

def update_results_table(stack, preview, username, labgroup):
    session = Session()
    
    cellid = stack.meta['cellid']
    batch = stack.meta['batch']
    modelname = stack.meta['modelname']
    
    r = (
            session.query(NarfResults)
            .filter(NarfResults.cellid == cellid)
            .filter(NarfResults.batch == batch)
            .filter(NarfResults.modelname == modelname)
            .first()
            )
    collist = ['%s'%(s) for s in NarfResults.__table__.columns]
    attrs = [s.replace('NarfResults.', '') for s in collist]
    removals = [
            'id', 'figurefile', 'lastmod', 'public', 'labgroup', 'username'
            ]
    for col in removals:
        attrs.remove(col)
        
    if not r:
        r = NarfResults()
        r.figurefile = preview
        r.username = username
        if not labgroup == 'SPECIAL_NONE_FLAG':
            try:
                if not labgroup in r.labgroup:
                    r.labgroup += ', %s'%labgroup
            except TypeError:
                # if r.labgroup is none, ca'nt check if user.labgroup is in it
                r.labgroup = labgroup
        fetch_meta_data(stack, r, attrs)
        session.add(r)
    else:
        r.figurefile = preview
        # TODO: This overrides any existing username or labgroup assignment.
        #       Is this the desired behavior?
        r.username = username
        if not labgroup == 'SPECIAL_NONE_FLAG':
            try:
                if not labgroup in r.labgroup:
                    r.labgroup += ', %s'%labgroup
            except TypeError:
                # if r.labgroup is none, can't check if labgroup is in it
                r.labgroup = labgroup
        fetch_meta_data(stack, r, attrs)
    
    session.commit()
    results_id = r.id
    session.close()
    
    return results_id
    
def fetch_meta_data(stack, r, attrs):
    """Assign attributes from model fitter object to NarfResults object.
    
    Arguments:
    ----------
    stack : nems_modules.stack
        Stack containing meta data, modules, module names et cetera
        (see nems_modules).
    r : sqlalchemy ORM object instance
        NarfResults object, either a blank one that was created before calling
        this function or one that was retrieved via a query to NarfResults.
        
    Returns:
    --------
    Nothing. Attributes of 'r' are modified in-place.
        
    """
    
    r.lastmod = datetime.datetime.now().replace(microsecond=0)
    
    for a in attrs:
        # list of non-numerical attributes, should be blank instead of 0.0
        if a in ['modelpath', 'modelfile', 'githash']:
            default = ''
        else:
            default = 0.0
        # TODO: hard coded fix for now to match up stack.meta names with 
        # narfresults names.
        # Either need to maintain hardcoded list of fields instead of pulling
        # from NarfResults, or keep meta names in fitter matched to columns
        # some other way if naming rules change.
        if 'fit' in a:
            k = a.replace('fit','est')
        elif 'test' in a:
            k = a.replace('test','val')
        else:
            k = a
        setattr(r, a, _fetch_attr_value(stack, k, default))

def _fetch_attr_value(stack,k,default=0.0):
    """Return the value of key 'k' of stack.meta, or default. Internal use."""
    
    # if stack.meta[k] is a string, return it.
    # if it's an ndarray or anything else with indicies, get the first index;
    # otherwise, just get the value. Then convert to scalar if np data type.
    # or if key doesn't exist at all, return the default value.
    if k in stack.meta:
        if stack.meta[k]:
            if not isinstance(stack.meta[k], str):
                try:
                    v = stack.meta[k][0]
                except:
                    v = stack.meta[k]
                finally:
                    try:
                        v = np.asscalar(v)
                    except:
                        pass
            else:
                v = stack.meta[k]
        else:
            v = default
    else:
        v = default
        
    
    return v
        
    
def get_batch_cells(batch=None, cellid=None):
    # eg, sql="SELECT * from NarfBatches WHERE batch=301"

    sql="SELECT * FROM NarfBatches WHERE 1"
    if not batch is None:
        sql+=" AND batch={}".format(batch)
        
    if not cellid is None:
       sql+=" AND cellid like '{}'".format(cellid)
    
    d=pd.read_sql(sql=sql,con=engine)
    
    return d

def get_data_parms(rawid=None,parmfile=None):
    # get parameters stored in gData associated with a rawfile

    if rawid is not None:
        sql="SELECT gData.* FROM gData INNER JOIN gDataRaw ON gData.rawid=gDataRaw.id WHERE gDataRaw.id={0}".format(rawid)
        #sql="SELECT * FROM gData WHERE rawid={0}".format(rawid)
    elif parmfile is not None:
        sql="SELECT gData.* FROM gData INNER JOIN gDataRaw ON gData.rawid=gDataRaw.id WHERE gDataRaw.parmfile = '{0}'".format(parmfile)
        print(sql)
    else:
        pass

    d=pd.read_sql(sql=sql,con=cluster_engine)

    return d

def batch_comp(batch,modelnames=[],cellids=['%']):
    
    modelnames=['parm100pt_wcg02_fir15_pupgainctl_fit01_nested5',
               'parm100pt_wcg02_fir15_pupgain_fit01_nested5',
               'parm100pt_wcg02_fir15_stategain_fit01_nested5'
               ]
    batch=301
    cellids=['%']
    
    session = Session()

    #     .filter(NarfResults.cellid.in_(cellids))
    results = psql.read_sql_query(
        session.query(NarfResults)
        .filter(NarfResults.batch == batch)
        .filter(NarfResults.modelname.in_(modelnames))
        .statement,
        session.bind
        )
    
    session.close()

    return results
