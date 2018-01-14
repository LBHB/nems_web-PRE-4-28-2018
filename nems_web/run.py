"""Module for launching the nems_analysis flask app.

Launches the app and hosts the server at the domain/ip and port
specified. See flask documentation for additional app.run options.

Note:
-----
debug should NEVER be set to True when launching the server for a
'production' environment (i.e. when hosting for public use). Per the
flask documentation, this would allow users to run "arbitrary code" on
the server, potentially causing harm.

"""

from nems_web.nems_analysis import app #socketio
#import nems_config.NEMS_Path as np

#from OpenSSL import SSL
#context = SSL.Context(SSL.PROTOCOL_TLSv1_2)
#context.use_privatekey_file(np.path + '/nems_config/host.key')
#context.use_certificate_file(np.path + '/nems_config/host.cert')

# TODO: figure out how to correctly configure the certificate for
#       desired host name, then turn this back on for neuralprediction.
#context = (
#        np.path + '/nems_config/host.cert', np.path + '/nems_config/host.key'
#        )

app.run(
        host="0.0.0.0", port=8000, debug=True,
        use_reloader=False, #ssl_context=context
        )