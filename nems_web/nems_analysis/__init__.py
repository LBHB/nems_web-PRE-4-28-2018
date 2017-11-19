import sys
from io import StringIO
import threading

from flask import Flask, url_for
from flask_socketio import SocketIO
from flask_assets import Environment, Bundle

from nems.utilities.output import SplitOutput

app = Flask(__name__)
app.config.from_object('nems_config.defaults.FLASK_DEFAULTS')

assets = Environment(app)

js = Bundle(
        'js/analysis_select.js', 'js/account_management/account_management.js',
        'js/modelpane/modelpane.js', output='gen/packed.%(version)s.js'
        )

# disabled for now because css files are overwriting each other, so styles
# for different pages end up merging. need to add classes/ids to individual
# css files so they don't conflict.
#css = Bundle(
#        'css/main.css', 'css/account_management/account_management.css',
#        'css/modelpane/modelpane.css', output='gen/packed.css'
#        )

#assets.register('css_all', css)
assets.register('js_all', js)

#try:
#    app.config.from_object('nems_config.Flask_Config')
#    
#except:
#    app.config.from_object('nems_config.defaults.FLASK_DEFAULTS')
#    print('No flask config file detected, using default settings')
#    pass

socketio = SocketIO(app, async_mode='threading')
thread = None

if app.config['COPY_PRINTS']:
    stringio = StringIO()
    orig_stdout = sys.stdout
    sys.stdout = SplitOutput(stringio, orig_stdout)

# redirect output of stdout to py_console div in web browser
def py_console():
    while app.config['COPY_PRINTS']:
        # Set sampling rate for console reader in seconds
        socketio.sleep(1)
        try:
            data = stringio.getvalue()
            lines = data.split('\n')
            stringio.truncate(0)
            for line in lines:
                if line:
                    # adds timestamp, which is nice, but messes with line break
                    #now = datetime.datetime.now()
                    #line = '{0}:{1}:{2}: {3}'.format(
                    #            now.hour, now.minute, now.second, line,
                    #            )
                    line = line.replace('\n', '<br>')
                    socketio.emit(
                            'console_update',
                            {'data':line},
                            namespace='/py_console',
                            )
        except Exception as e:
            print(e)
            pass
        
# start looping py_console() in the background when socket is connected
# but only if COPY_PRINTS is set to true
@socketio.on('connect', namespace='/py_console')
def start_logging():
    if not app.config['COPY_PRINTS']:
        return
    global thread
    if thread is None:
        print('Initializing console reader...')
        thread = socketio.start_background_task(target=py_console)
    socketio.emit(
            'console_update',
            {'data':'console connected or re-connected'},
            namespace='/py_console',
            )

def track_thread_count():
    while True:
        socketio.sleep(180)
        if threading.active_count() >= 10:
            print("current thread count: ")
            print(threading.active_count())
            print("active threads: ")
            for t in threading.enumerate():
                print(t.name)
        
socketio.start_background_task(target=track_thread_count)

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