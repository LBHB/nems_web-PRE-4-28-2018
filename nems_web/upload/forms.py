""" Forms for uploading data to the server. """

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired, FileField
from wtforms import TextField
from wtforms.validators import DataRequired


class UploadForm(FlaskForm):
    batch = TextField(
            'batch',
            validators=[
                    DataRequired(message="Must enter a batch number"),
                    ]
            )
    
    cell = TextField(
            'cell',
            validators=[
                    DataRequired(message="Must enter a cell name or id"),
                    ]
            )
    
    fs = TextField(
            'fs',
            validators=[
                    DataRequired(message="Must enter a sampling rate (fs)"),
                    ],
            default='200'
            )
    
    stimfmt = TextField(
            'stim format',
            validators=[
                    DataRequired(
                            message='Must specify a stimulus format (ex: ozgf)',
                            )
                    ],
            default='ozgf'
            )
    
    chancount = TextField(
            'channel count',
            validators=[
                    DataRequired(message='Must enter a channel count'),
                    ],
            default='18'
            )
    
    upload = FileField(
            'file',
            validators=[
                    FileRequired(),
                    FileAllowed(['.pkl', '.mat'],
                                'File must be .pkl or .mat'
                                ),
                    ]
            )