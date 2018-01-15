from .widget import Widget


# TODO: more appropriate to just keep this in widget module?
#       Put here b/c considering organizing modules by ui section, ex
#       panels.py, table.py, plots.py, console.py
# TODO: Might also want to be able to embed widgets in each other?
#       ex: AnalysisPanel could have TagButton and StatusButton Widgets
#           instead of just tag and status lists. Not sure if that would
#           be helpful or just arbitrary abstraction.
class AnalysisPanel(Widget):

    def _my_contents(self):
        self._expected_contents = ['names, ids, tags, status']

    def _generate_html(self):
        # TODO: Finish/redo this after updating the main template.
        #       Just a mockup for now.

        html = ("<div id='AnalysisPanel' class='Widget'>"
                "    <select id='analysis_selector' class='ui_selector'>")
        for name, a_id in zip(self.names, self.ids):
            html.append("<option name='{0}' value='{1}'> {0} </option>"
                        .format(name, a_id))
        html.append("    </select>"
                    "<div id='AnalysisPanelButtons' class='WidgetButtons'>"
                    "    <button id='tags' class='ui_button'> Tags </button>"
                    "    <button id='status' class='ui_button'>"
                    "        Status </button>"
                    "</div>"
                    "<script> #TODO: functions to open tags and status modals"
                    "</script>")

        self._html_string = html


# Example views function using new format
from flask import jsonify, request
from sqlalchemy import or_

from . import app
from nems.db import Session, NarfAnalysis

@app.route('/update_analysis')
def update_analysis():
    user = 'get current user'
    ui = user.ui_state
    analysis = ui['AnalysisPanel']
    session = Session()
    # TODO: Need to start using post, the gets are causing
    #       issues with other server apps (request string too long)
    tags = request.args.getlist('tags')
    # skipping some steps that are mirrored or the same as before
    new_analysis = (
            session.query(NarfAnalysis)
            .filter(or_(NarfAnalysis.tags.ilike('stuff based on tags')))
            .all()
            )
    analysis.names, analysis.ids = [a.name for a in new_analysis],\
                                   [a.id for a in new_analysis]

    session.close()
    return jsonify(html=analysis.html)