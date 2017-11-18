def web_print(s):
    use_app = False
    try:
        from nems.web.nems_analysis import app
        from nems.web.nems_analysis import socketio
        use_app = True
    except Exception as e:
        print('Error when using web_print')
        print(e)
        socketio = None
        use_app = False
    if use_app:
        s = s.replace('\n', '<br>')
        socketio.emit(
                'console_update',
                {'data':s},
                namespace='/py_console',
                )
    else:
        print(s)