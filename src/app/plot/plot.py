from bokeh.embed import components
from bokeh.plotting import figure
import numpy as np

class Plot:
    """Abstract base class for plots to be displayed on the SALT statistics pages.
    """

    def __init__(self, **kwargs):
        self.plot = figure(**kwargs)

    def to_html(self):
        div, script = components(self.plot)
        return '<div class="printable plot">' + script + div + '</div>'

    def __str__(self):
        return self.to_html()

    def __unicode__(self):
        return self.to_html()


class DummyPlot(Plot):
    def __init__(self, **kwargs):
        Plot.__init__(self, **kwargs)

        x = np.linspace(0, 5, 20)
        y = np.sin(x)
        self.plot.line(x=x, y=y)
