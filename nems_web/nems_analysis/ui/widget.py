from functools import partialmethod

class Widget:
    """Base class for user-interface elements for the NEMS web interface.

    Each Widget defines a set of attributes representing its to-be
    contents in the web interface. For example, an AnalysisPanel
    Widget might define .analysis_names and .analysis_ids. A Widget
    also has a @property-decorated "html" method for fetching its
    representation as an HTML-string.

    Arguments:
        contents : dict
            Ui data that will be used to populate the HTML string.
            Ex: {analysis_names: ['nemstest', 'jaketest', 'myanalysis'],
                 analysis_ids: [9202983, 2223444, 0830100]}

        *AND/OR*

        kwargs :
            Same as contents, but in keyword argument form.
            Ex: x = Widget(analysis_names=['nemstest'], analysis_ids=[404929])

        If both forms are present, kwargs will add to (and overwrite)
        attributes specified in the contents dictionary. For example, if
        both define 'analysis_names', then the definition provided by
        kwargs will be used. If attributes a, b, and c are given by contents
        while kwargs provides attribute d, then all four attributes will
        be used.

    """

    # Gets set to True whenever the Widget's ui contents get
    # modified. If True, .html will re-generate the html string.
    # Otherwise, the existing string will be returned.
    flagged = False
    # Raw HTML string to be rendered in the web page
    # *SHOULD NOT BE REFERENCED DIRECTLY UNDER NORMAL CIRCUMSTANCES*
    # Direct references to .html instread (see the class method below)
    _html_string = None

    def __init__(self, contents=None, **kwargs):
        self.contents = contents if contents else None
        self.kwargs = kwargs if kwargs else None
        self._my_contents()
        self._setup_contents()

    def _my_contents(self):
        """Sets _expected_contents attribute.

        Only separated so that __init__ should normally not need to be
        redefined in sub-classes, to simplify code.

        """

        self._expected_contents = ['example_attr_one', 'example_attr_two']

    def _attr_setter(self, attr, value):
        setattr(self, attr, value)
        self.flagged = True
        # TODO: Could add self._generate_html() here and eliminate html prop,
        # but then it might get called multiple times per UI update
        # (ex. if both names and ids get changed)
        # even though the new HTML only needs to be returned
        # one time. Not sure which approach is better.

    def _setup_contents(self):
        if self.contents:
            for attr, val in self.contents.items():
                setattr(self, attr, val)
        if self.kwargs:
            for attr, val in self.kwargs.items():
                setattr(self, attr, val)
        for attr in self._expected_contents:
            assert hasattr(self, attr), ("This Widget's contents"
                                        " must include >> {0}".format(attr))
            # Sets content attributes to be properties that flag the
            # widget as changed any time they are set manually after
            # initialization.
            # Ex: Widget starts with names=['one','apple']. Later,
            #     the UI updates names to ['one', 'banana', 'seven'],
            #     at which point self.flagged is set to True, signalling
            #     that html needs to be regenerated.
            setattr(self, attr, property(
                            fset=partialmethod(self._attr_setter, attr)
                            ))

        self._generate_html()

    def _generate_html(self):
        """Generates the html string for this Widget based on attributes
        defined in contents.

        Each Widget subclass will need to overwrite
        this method according to its own needs, but it should always
        return a string and not need to take any arguments.
        (If arguments are absolutely positively needed for some reason,
        the html property will need to be redefined as well to pass those
        arguments to this method).

        Webpage templates will handle setting up the template/framework
        that the html is embedded in, so html returned by Widgets should
        not try to interact with the Bootstrap grid or other layout
        mechanics (unless they are internal to the Widget, like
        organizing somee butons).

        """

        html = ("<div class='ExampleWidget'>"
                    "<h1> These are my contents: </h1>")
        for item in self.example_attribute_one:
            html.append("<ol class=ex_one_item value='{0}'> {0} </ol>"
                        .format(item))
        html.append("</div>")

        self._html_string = html

    @property
    def html(self):
        if not self.flagged:
            return self._html_string
        else:
            self._generate_html()
            self.flagged = False
            return self._html_string
