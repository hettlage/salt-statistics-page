import datetime
import math
import numpy as np

import pytz
from bokeh.embed import components
from bokeh.models import ColumnDataSource, FixedTicker, Quad, Range1d
from bokeh.models.axes import LinearAxis
from bokeh.plotting import figure


class Plot:
    """Abstract base class for plots to be displayed on the SALT statistics pages.

    The plot is created with Bokeh (http://bokeh.pydata.org), and the Figure instance for the plot is exposed as
    `self.plot`.

    Any parameters passed to the constructor will be passed on to the `bokeh.plotting.Figure` constructor.

    Methods:
    --------
    to_html(string)
         HTML for showing the plot.

    """

    def __init__(self, **kwargs):
        self.plot = figure(**kwargs)

    def to_html(self):
        """HTML for displaying the plot.

        While the HTML contains the JavaScript related to this particular plot, it doesn't contain the general Bokeh
        JavaScript. So you have to ensure that your HTML document imports the Bokeh JavaScript before this method is
        called. You may do this by including a script element

        ::
            <script src="http://cdn.pydata.org/bokeh/release/bokeh-x.y.z.min.js"></script>

        where x.y.z is the version of Bokeh used. You also need to include the Bokeh CSS in your document:

        ::
            <link rel="stylesheet" href="http://cdn.pydata.org/bokeh/release/bokeh-x.y.z.min.css">

        Again, x.y.z denotes the Bokeh version.

        A class extending this one must ensure that its constructor adds all the plot content to `self.plot`.
        """

        div, script = components(self.plot)
        return '<div class="printable plot">' + script + div + '</div>'

    def __str__(self):
        return self.to_html()

    def __unicode__(self):
        return self.to_html()


class TimeBarPlot(Plot):
    """A bar plot for plotting bars for a list of dates.

    Parameters:
    -----------
    df : pandas.DataFrame
        A data frame of the data to plot. The data frame must at least contain columns named `x` (for the dates), `y`
        (for the y values) and, if an alternative y value range is passed as parameter, `alt_y` (for the alternative y
        values). The data is assumed to be for equidistant dates, but it is perfectly acceptable to leave out dates.
    dx : datetime.timedelta
        The time difference between subsequent dates.
    x_range : bokeh.models.Range1d
        The range of dates to plot. If `x` is an item of the date column (`df['x']`), there must be integers `m`, `n`
        so that `x_range_start == x + (m + 0.5) * dx` and `x_range.end == x + (n + 0.5) * dx`.
    y_range : bokeh.models.Range1d
        The value range to use for the y axis.
    date_formatter : bokeh.models.formatters.DatetimeTickFormatter
        The formatter to use for the labels of the date axis.
    y_formatters : sequence of bokeh.models.formatters.TickFormatter
        The formatters to use for the y axes. If there are more axes than formatters, the last formatter in the
        sequence is used for the remaining axes.
    x_label_orientation : str or float, optional
        The orientation of the date axis labels. Possible values are `'horizontal'`, `'vertical'` or an angle in
        radians. The default is `'horizontal'`.
    label_font_size : str, optional
        The font size to use for the axis labels. You can use any string which would be accepted by the CSS `font-size`
        attribute. The chosen is used for both date and y axis.
    alt_y_range : bokeh.models.Range1d, optional
        The value range to use for the alternative y axis. This value must be supplied if `df` has an `alt_y` column,
        and vice versa.
    **kwargs: keyword arguments
        Additional keyword arguments are passed on the `Plot` constructor.
    """

    PRIMARY_COLOR = 'blue'

    SECONDARY_COLOR = 'firebrick'

    ODD_BOX_ANNOTATION_COLOR = 'white'

    EVEN_BOX_ANNOTATION_COLOR = 'olive'

    def __init__(self,
                 df,
                 dx,
                 x_range,
                 y_range,
                 date_formatter,
                 y_formatters=(),
                 label_orientation='horizontal',
                 label_font_size='10pt',
                 alt_y_range=None,
                 **kwargs):
        Plot.__init__(self, **kwargs)

        # consistency check
        if ('alt_y' in df and not alt_y_range) or (alt_y_range and 'alt_y' not in df):
            raise ValueError('alternate y values and alternative y range must always be used together')

        dx = self._total_milliseconds(dx)
        if 'alt_y' in df:
            offset = 0.05 * dx
            bar_width = 0.35 * dx
        else:
            offset = -0.3 * dx
            bar_width = 0.6 * dx
        offset = int(round(offset))
        bar_width = int(round(bar_width))
        x = np.array([self._milliseconds_timestamp(d) for d in df['x']])
        x1 = x - offset - bar_width
        x2 = x - offset
        y1 = np.zeros(len(x1))
        y2 = df['y']
        source_content = dict(x=x, x1=x1, y1=y1, x2=x2, y2=y2)
        if alt_y_range:
            alt_x1 = x + offset
            alt_x2 = x + offset + bar_width
            alt_y1 = np.zeros(len(alt_x1))
            alt_y2 = df['alt_y']
            source_content['alt_x1'] = alt_x1
            source_content['alt_x2'] = alt_x2
            source_content['alt_y1'] = alt_y1
            source_content['alt_y2'] = alt_y2
        self.source = ColumnDataSource(source_content)
        self.dx = dx
        self.x_range = Range1d(start=self._milliseconds_timestamp(x_range.start) - dx // 2,
                               end=self._milliseconds_timestamp(x_range.end) + dx // 2)
        self.y_range = y_range
        self.alt_y_range = alt_y_range
        self.date_formatter = date_formatter
        self.y_formatters = y_formatters
        self.x_label_orientation = label_orientation
        self.label_font_size = label_font_size

        self._init_plot()

    @staticmethod
    def _milliseconds_timestamp(d):
        """Milliseconds since the Unix epoch.

        Params:
        -------
        d: datetime.datetime or datetime.date
            Date.

        Returns:
        --------
        int: The number of milliseconds between the Unix epoch and `d`.
        """
        if isinstance(d, datetime.datetime):
            d = datetime.datetime(d.year, d.month, d.day, d.hour, d.minute, d.second, 0, tzinfo=pytz.UTC)
        else:
            d = datetime.datetime(d.year, d.month, d.day, 0, 0, 0, 0, tzinfo=pytz.UTC)
        return int(round(d.timestamp() * 1000))

    @staticmethod
    def _total_milliseconds(dt):
        """Number of milliseconds in a time difference

        Params:
        -------
        dt: datetime.timedelta
                Time difference.

        Returns:
        --------
        int
            The number of milliseconds in `dt`.
        ."""
        return int(round(dt.total_seconds() * 1000))

    def _init_plot(self):
        """Initialise the plot.

        The following glyphs are created:

        * Background stripes with alternating colours.
        * Bars for the y values as a function of the date.
        * Bars for the alternative y values, if requested.
        * Axis ticks and labels.

        No outline or grid lines are included in the plot.
        """
        p = self.plot

        # axes ranges
        p.x_range = self.x_range
        p.y_range = self.y_range
        if self.alt_y_range:
            p.extra_y_ranges = {'alt_y': self.alt_y_range}

        # background stripes with alternating color
        def add_background_stripe(x, index):
            if divmod(index, 2)[1] == 1:
                color = self.ODD_BOX_ANNOTATION_COLOR
            else:
                color = self.EVEN_BOX_ANNOTATION_COLOR
            q = Quad(left=(x - self.dx // 2),
                     bottom=0,
                     right=(x + self.dx // 2),
                     top=self.plot.y_range.end,
                     line_color=None,
                     fill_color=color,
                     fill_alpha=0.2)
            self.plot.add_glyph(q)

        # add background stripes
        x_min = self.x_range.start + self.dx // 2
        x_max = self.x_range.end - self.dx // 2
        i = 0
        while x_min + i * self.dx <= x_max:
            x = x_min + i * self.dx
            add_background_stripe(x, i)
            i += 1

        # bars for primary values
        p.quad(source=self.source,
               left='x1',
               bottom='y1',
               right='x2',
               top='y2',
               fill_color=self.PRIMARY_COLOR,
               line_color=None)

        # bars for secondary (alternative) values
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

        # twin date axis and (if necessary) y axis
        p.add_layout(LinearAxis(), 'above')
        if self.alt_y_range:
            p.add_layout(LinearAxis(y_range_name='alt_y'), 'right')

        # date axis labels
        tick_count = 1 + int(round((x_max - x_min) / self.dx))
        p.xaxis.ticker = FixedTicker(ticks=np.linspace(x_min, x_max, tick_count))
        p.xaxis.formatter = self.date_formatter
        p.xaxis.major_tick_line_color = None
        p.xaxis.major_tick_out = 0
        p.xaxis.major_label_orientation = self.x_label_orientation
        p.axis.major_label_text_font_size = self.label_font_size

        # y axes formatters
        if len(self.y_formatters):
            for i, y_axis in enumerate(p.yaxis):
                y_axis.formatter = self.y_formatters[min(i, len(self.y_formatters) - 1)]


class DialPlot(Plot):
    """A dial plot.

    The plot has one or two hands, depending on how many values are supplied.

    Params:
    -------
    values: list of float
        Values to use for the hand(s). The first value is assumed to be the primary one.
    label_values: list of str
        Values to use for the dial labels.
    label_color_func: function
        Function mapping a value to a string denoting a colour, as you would use it for the CSS color attribute. This
        function is used for deciding what color to use for the wedge sections between labels.
    display_values: list of str
        Values to show on the value display. The first value is assumed to be the primary one.
    **kwargs: keyword arguments
        Additional keyword arguments are passed on the `Plot` constructor.
    """

    def __init__(self, values, label_values, label_color_func, display_values, **kwargs):
        Plot.__init__(self, **kwargs)
        self.values = values
        self.label_values = label_values
        self.label_color_func = label_color_func
        self.display_values = display_values

        self._init_plot()

    def _init_plot(self):
        """Initialise the plot.

        The following glyphs are created.

        * Dial wedges.
        * Labels.
        * One or two hands.
        * Value display with one or two values.

        No outline, grid lines or axes are included in the plot.
        """
        # no axes, no grid lines, suitable ranges
        self.plot.axis.visible = None
        self.plot.grid.grid_line_color = None
        self.plot.outline_line_color = None
        width = 2.8
        self.plot.x_range = Range1d(start=-width / 2, end=width / 2)
        self.plot.y_range = Range1d(start=-width / 2, end=width / 2)

        # conversion from values to angles
        angle_offset = 33
        min_value = self.label_values[0]
        max_value = self.label_values[-1]
        value_range = max_value - min_value
        min_angle = math.radians(angle_offset - 90)
        max_angle = math.radians(360 - angle_offset - 90)
        angle_range = max_angle - min_angle
        angle_func = lambda x : max_angle - ((x - min_value) / value_range) * angle_range

        start_angle = [angle_func(self.label_values[i]) for i in range(0, len(self.label_values) - 1)]
        end_angle = [angle_func(self.label_values[i]) for i in range(1, len(self.label_values))]
        fill_color = [self.label_color_func(0.5 * (self.label_values[i] + self.label_values[i + 1]))
                      for i in range(0, len(self.label_values) - 1)]

        # angular segment underneath the value display
        start_angle.append(min_angle)
        end_angle.append(max_angle)
        fill_color.append('d9d9d9')

        # plot dial
        outer_radius = 1
        inner_radius = 6. / 7
        self.plot.annular_wedge(x=np.zeros(len(start_angle)),
                                y=np.zeros(len(start_angle)),
                                start_angle=start_angle,
                                end_angle=end_angle,
                                direction='clock',
                                inner_radius=inner_radius,
                                outer_radius=outer_radius,
                                fill_color=fill_color,
                                line_color='white')

        # add labels
        label_radius = 1.15
        label_x = [label_radius * math.cos(angle_func(v)) for v in self.label_values]
        label_y = [label_radius * math.sin(angle_func(v)) for v in self.label_values]
        self.plot.text(x=label_x,
                       y=label_y,
                       text=self.label_values,
                       text_align='center',
                       text_baseline='middle',
                       text_font_style='normal')

        # add value display
        display_x = 0
        display_y = -outer_radius
        display_height = 0.52
        display_width = (16. / 9) * display_height
        self.plot.rect(x=display_x,
                       y=display_y,
                       width=display_width,
                       height=display_height,
                       fill_color='#f2f2f2',
                       line_color='#b7a5b7')

        # add text to value display
        if len(self.display_values) == 1:
            self.plot.text(x=display_x,
                           y=display_y,
                           text=self.display_values,
                           text_align='center',
                           text_baseline='middle',
                           text_font_size='300%',
                           text_font_style='bold')
        else:
            self.plot.text(x=display_x,
                           y=display_y - 0.03,
                           text=[self.display_values[0]],
                           text_align='center',
                           text_baseline='bottom',
                           text_font_size='300%',
                           text_font_style='bold')
            self.plot.text(x=display_x,
                           y=display_y - 0.05,
                           text=[self.display_values[1]],
                           text_align='center',
                           text_baseline='top',
                           text_font_size='110%',
                           text_font_style='bold')

        # draw hand
        def draw_hand(value, color):
            """The hand consists of a semicircle and a triangle, both of which need to be rotated by the angle
            corresponding to the given value."""

            if value > max_value:
                value = max_value

            angle = angle_func(value)
            hand_radius = 0.04
            self.plot.wedge(x=0,
                            y=0,
                            start_angle=angle - 0.5 * math.pi,
                            end_angle=angle + 0.5 * math.pi,
                            direction='clock',
                            radius=hand_radius,
                            color=color)

            D = np.array([math.cos(angle), -math.sin(angle), math.sin(angle), math.cos(angle)]).reshape((2, 2))
            p1 = D.dot(np.array([0, hand_radius]).transpose())
            p2 = D.dot(np.array([0.8, 0]).transpose())
            p3 = D.dot(np.array([0, -hand_radius]).transpose())
            self.plot.patch(x=[p1[0], p2[0], p3[0]],
                            y=[p1[1], p2[1], p3[1]],
                            color=color)

        # draw hand for primary and (if applicable) secondary value
        draw_hand(self.values[0], '#2423ff')
        if len(self.values) > 1:
            draw_hand(self.values[1], '#ffa523')
