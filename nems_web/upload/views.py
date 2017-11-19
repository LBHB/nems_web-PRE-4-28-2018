""" Views functions for uploading data to the server. """

from flask_login import login_required
from flask import g, render_template, request, redirect, url_for

from nems_web.nems_analysis import app
from nems_web.upload.forms import UploadForm

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    errors = ''
    form = UploadForm(request.form)
    if request.method == 'POST':
        if form.validate():
            print('made it past validation')
            # For now just takes a .mat file and adds to cache
            # TODO: What should this form actually do with the data?
            rootpath = "/auto/data/code/nems_in_cache"
            save = (
                    "{0}/batch{1}/{2}_b{1}_{3}_c{4}_fs{5}.mat"
                    .format(
                            rootpath, form.batch.data, form.cell.data,
                            form.stimfmt.data, form.chancount.data, form.fs.data,
                            )
                    )
            print('made it past formatter')
            try:
                form.file.data.save(save)
            except Exception as e:
                print('Error saving file')
                print(e)
    
            return redirect(url_for('main_view'))
        else:
            return render_template(
                    'upload/upload.html', form=form, error=form.errors,
                    )
    else:
        return render_template('upload/upload.html', form=form, errors=errors)
