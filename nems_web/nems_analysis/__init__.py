import logging
import os
import pkg_resources as pkg

from flask import Flask
from flask_assets import Environment, Bundle

log = logging.getLogger(__name__)
werk = logging.getLogger('werkzeug')
werk.setLevel(logging.ERROR)

app = Flask(__name__)
# Specify environment variables that are allowed for flask config.
# Could pass os.environ directly to app.config.update(), but not
# sure if that would be safe / might cause conflicts with
# environment variables set for other reasons.
defined = ['DEBUG', 'CSRF_ENABLED', 'CSRF_SESSION_KEY', 'SECRET_KEY']
config = {k: os.environ[k] for k in defined if k in os.environ.keys()}
app.config.update(config)

assets = Environment(app)

js = Bundle(
        'js/analysis_select.js', 'js/account_management/account_management.js',
        'js/modelpane/modelpane.js', output='gen/packed.%(version)s.js'
        )

# TODO
# disabled for now because css files are overwriting each other, so styles
# for different pages end up merging. need to add classes/ids to individual
# css files so they don't conflict.
#css = Bundle(
#        'css/main.css', 'css/account_management/account_management.css',
#        'css/modelpane/modelpane.css', output='gen/packed.css'
#        )

#assets.register('css_all', css)
assets.register('js_all', js)

# get current bokeh version. all html templates should use this
# inside the bokeh cdn url to make sure versions stay synced after updates.
bokeh_version = pkg.get_distribution("bokeh").version

# these don't get used for anything within this module,
# just have to be loaded when app is initiated
import nems_web.nems_analysis.views
import nems_web.reports.views
import nems_web.plot_functions.views
import nems_web.model_functions.views
import nems_web.modelpane.views
import nems_web.account_management.views
import nems_web.upload.views
import nems_web.table_details.views
import nems_web.run_custom.views
import nems_web.admin.views
