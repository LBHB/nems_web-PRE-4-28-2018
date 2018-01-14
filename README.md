# README #

NEMS is the Neural Encoding Model System, a set of tools for fitting computational models for the neural encoding of sensory stimuli.  Written in Python, migrated from a Matlab tool designed to do something similar (NARF).

NEMS_WEB is a GUI that accompanies the core NEMS software in the form of a web server. NEMS must be installed in order for NEMS_WEB to function.

### Technical overview ###

General Overview:

1. NEMS models are described by keyword strings, e.g. 'fb18ch100_wc03_fir10_dexp_fit01_nested10'. These keywords tell the fitter how to load the data, which model functions to include in the model, and how to fit the model.

2. The NEMS models are essentially a modified stack, with each level of the stack being the output of a function applied to the previous element of the stack.

3. Models can be fit locally using the core NEMS software, through the NEMS_WEB interface at neuralprediction.org, or through a locally-hosted instance of the NEMS_WEB server (typically at localhost:8000).


Ongoing: expand this information in [NEMS Wiki](https://bitbucket.org/lbhb/nems/wiki/Home)

### Core NEMS_WEB components ###

* TODO

### How do I get set up? ###

* Dependencies
    * NEMS package available at https://bitbucket.org/lbhb/nems and its dependencies.
    * Additional NEMS_WEB-specific dependencies: pandas, flask, mpld3, bokeh, flask-socketio, eventlet, flask-login, flask-WTF, bcrypt, boto3, seaborn, gevent
    flask-assets

* Demos
    * A sample database will be downloaded on first launch if no database information is provided. This sample contains a limited amount of fitting results that can be used to explore the NEMS_WEB interface. A sample data file that corresponds to the first cell and first model in the selection lists can be used to fit models.

### Who do I talk to? ###

* LBHB team
