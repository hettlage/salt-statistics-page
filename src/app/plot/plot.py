from bokeh.embed import components
from bokeh.models import ColumnDataSource, FixedTicker, Quad, Range1d
from bokeh.models.axes import LinearAxis
from bokeh.models.formatters import DatetimeTickFormatter
from bokeh.plotting import figure
import math
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


class TimeBarPlot(Plot):
    """A bar plot for plotting bars for times.
    """

    PRIMARY_COLOR = 'blue'

    SECONDARY_COLOR = 'firebrick'

    ODD_BOX_ANNOTATION_COLOR = 'white'

    EVEN_BOX_ANNOTATION_COLOR = 'olive'

    def __init__(self, df, dx, x_range, y_range, date_formatter, label_font_size='10pt', alt_y_range=None, **kwargs):
        Plot.__init__(self, **kwargs)

        # consistency check
        if ('alt_y' in df and not alt_y_range) or (alt_y_range and 'alt_y' not in df):
            raise ValueError('alternate y values and alternative y range must always be used together')

        if 'alt_y' in df:
            offset = 0.05 * dx
            bar_width = 0.35 * dx
        else:
            offset = -0.3 * dx
            bar_width = 0.6 * dx
        x = df['x']
        x1 = [d.timestamp() * 1000 for d in x - offset - bar_width]
        x2 = [d.timestamp() * 1000 for d in x - offset]
        y1 = np.zeros(len(x1))
        y2 = df['y']
        source_content = dict(x=x, x1=x1, y1=y1, x2=x2, y2=y2)
        if alt_y_range:
            alt_x1 = [d.timestamp() * 1000 for d in x + offset]
            alt_x2 = [d.timestamp() * 1000 for d in x + offset + bar_width]
            alt_y1 = np.zeros(len(alt_x1))
            alt_y2 = df['alt_y']
            source_content['alt_x1'] = alt_x1
            source_content['alt_x2'] = alt_x2
            source_content['alt_y1'] = alt_y1
            source_content['alt_y2'] = alt_y2
        self.source = ColumnDataSource(source_content)
        self.dx = dx
        self.x_range = x_range
        self.y_range = y_range
        self.alt_y_range = alt_y_range
        self.date_formatter = date_formatter
        self.label_font_size = label_font_size

        self.init_plot()

    def init_plot(self):
        p = self.plot

        p.y_range = self.y_range
        if self.alt_y_range:
            p.extra_y_ranges = {'alt_y': self.alt_y_range}

        def add_background_stripe(x, index):
            if divmod(index, 2)[1] == 1:
                color = self.ODD_BOX_ANNOTATION_COLOR
            else:
                color = self.EVEN_BOX_ANNOTATION_COLOR
            q = Quad(left=(x - 0.5 * self.dx).timestamp() * 1000,
                     bottom=0,
                     right=(x + 0.5 * self.dx).timestamp() * 1000,
                     top=self.plot.y_range.end,
                     line_color=None,
                     fill_color=color,
                     fill_alpha=0.2)
            self.plot.add_glyph(q)

        x_min = self.source.data['x'].iloc[0] - 0.5 * self.dx
        x_max = self.source.data['x'].iloc[-1] + 0.5 * self.dx
        x_arr = self.source.data['x']
        first_x_in_range = x_arr[x_arr > self.x_range.start][0]
        i = 0
        while first_x_in_range - i * self.dx >= x_min:
            x = first_x_in_range - i * self.dx
            add_background_stripe(x, i)
            i += 1
        i = 1
        while first_x_in_range + i * self.dx < x_max:
            x = first_x_in_range + i * self.dx
            add_background_stripe(x, i)
            i += 1

        p.quad(source=self.source,
               left='x1',
               bottom='y1',
               right='x2',
               top='y2',
               fill_color=self.PRIMARY_COLOR,
               line_color=None)
        if self.alt_y_range:
            p.quad(source=self.source,
                   y_range_name='alt_y',
                   left='alt_x1',
                   bottom='alt_y1',
                   right='alt_x2',
                   top='alt_y2',
                   fill_color=self.SECONDARY_COLOR,
                   line_color=None)

        p.xgrid.grid_line_color = None

        p.add_layout(LinearAxis(), 'above')
        if self.alt_y_range:
            p.add_layout(LinearAxis(y_range_name='alt_y'), 'right')

        p.xaxis.ticker = FixedTicker(ticks=[1000 * d.timestamp() for d in self.source.data['x']])
        p.xaxis.formatter = self.date_formatter
        p.xaxis.major_tick_line_color = None
        p.xaxis.major_tick_out = 0
        p.xaxis.major_label_orientation = math.pi / 2
        p.axis.major_label_text_font_size = self.label_font_size
