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