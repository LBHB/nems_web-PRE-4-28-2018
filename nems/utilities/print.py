try:
    # if getting app object throws an error, then function must have been
    # called independent of web interface.
    from nems.web.nems_analysis import app
    from nems.web.nems_analysis import socketio
    use_app = True
except:
    socketio = None
    use_app = False
    
    
def web_print(s):
    if use_app:
        s = s.replace('\n', '<br>')
        socketio.emit(
                'console_update',
                {'data':s},
                namespace='/py_console',
                )
    else:
        print(s)