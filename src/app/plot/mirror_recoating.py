import colorsys
import datetime
import numpy as np
import pandas as pd

from bokeh.io import hplot, vform, vplot
from bokeh.models import ColumnDataSource, DataRange1d
from bokeh.models.formatters import DatetimeTickFormatter
from bokeh.models.widgets import DataTable, DateFormatter, TableColumn
from bokeh.plotting import Figure

from app import db
from app.plot.plot import Plot


def update_database(excel_spreadsheet):
    """Update the mirror recoating data in the database.

    The data is supplied as an Excel spreadsheet whose first sheet of the has at least the following two columns.

    * 'Installation date': The dates when the recoated segment was installed.
    * 'Segment': The segments.

    If a row contains a segment but no installation date it is assumed that the date hasn't changed from the previous
    row. For example, consider the following data:

    Installation date   Segment
    ---------------------------
    1-May-2016          6
                        8
    5-May-2016          11
                        15
                        21

    In this case segments 6 and 8 were installed on 1 May 2016, whereas segments 11, 15 and 21 were installed on 5 May
    2016.

    If a row contains no segment it is ignored.

    Params:
    -------
    excel_spreadsheet : file-like or input stream
        Data for updating the database. This must be an Excel spreadsheet.
    """

    data = _read_recoating_data(excel_spreadsheet)
    values = ["(DATE('{replacement_date}'), {segment_position:d})"
                .format(replacement_date=row[1].ReplacementDate.strftime('%Y-%m-%d'),
                        segment_position=int(round(row[1].SegmentPosition)))
              for row in data.iterrows()]
    values = ','.join(values)
    query = '''INSERT INTO MirrorRecoating (ReplacementDate, SegmentPosition) VALUES {values}
                      ON DUPLICATE KEY UPDATE SegmentPosition=SegmentPosition'''.format(values=values)
    db.engine.execute(query)


def _read_recoating_data(excel_spreadsheet):
    """Reads in the recoating data from an Excel spreadsheet.

    See the `update_database` method for details of what the spreadsheet must look like.

    Params:
    -------
    excel_spreadsheet : file-likec or input stream
        Excel spreadsheet with the recoating data.

    Returns:
    --------
    pandas.DataFrame
       Data frame with the recoating data. The installation dates and segments are contained in columns name 'Date' and
       'Segment'.
    """

    data = pd.read_excel(excel_spreadsheet)
    data = data.rename(columns={'Installation date': 'ReplacementDate', 'Segment Truss Position': 'SegmentPosition'})
    data = data.dropna(subset=['SegmentPosition'])
    data = data[['ReplacementDate', 'SegmentPosition']]

    # add missing dates
    replacement_dates = []
    segment_positions = []
    for row in data.iterrows():
        date = row[1].ReplacementDate
        if pd.isnull(date):
            date = replacement_dates[-1]
        replacement_dates.append(date)
        segment_positions.append(row[1].SegmentPosition)

    return pd.DataFrame(dict(ReplacementDate=replacement_dates, SegmentPosition=segment_positions))


class MirrorRecoatingPlot(Plot):
    """Figure with the table of recoating data, a plot displaying the cumulative number of recoatings since the start of
    the year, and diagram showing the status of the mirror segments.

    Params:
    -------
    now: datetime.date
        The current date.
    """

    def __init__(self, now):
        Plot.__init__(self)

        self.now = now

        self.mirror_positions = \
            [None, (0, 0.0), (0, 1.0), (1, 0.5), (1, -0.5), (0, -1.0), (-1, -0.5), (-1, 0.5), (0, 2.0), (1, 1.5),
             (2, 1.0), (2, 0.0), (2, -1.0), (1, -1.5), (0, -2.0), (-1, -1.5), (-2, -1.0), (-2, 0.0), (-2, 1.0),
             (-1, 1.5), (0, 3.0), (1, 2.5), (2, 2.0), (3, 1.5), (3, 0.5), (3, -0.5), (3, -1.5), (2, -2.0), (1, -2.5),
             (0, -3.0), (-1, -2.5), (-2, -2.0), (-3, -1.5), (-3, -0.5), (-3, 0.5), (-3, 1.5), (-2, 2.0), (-1, 2.5),
             (0, 4.0), (1, 3.5), (2, 3.0), (3, 2.5), (4, 2.0), (4, 1.0), (4, 0.0), (4, -1.0), (4, -2.0), (3, -2.5),
             (2, -3.0), (1, -3.5), (0, -4.0), (-1, -3.5), (-2, -3.0), (-3, -2.5), (-4, -2.0), (-4, -1.0), (-4, 0.0),
             (-4, 1.0), (-4, 2.0), (-3, 2.5),  (-2, 3.0), (-1, 3.5), (0, 5.0), (1, 4.5), (2, 4.0), (3, 3.5), (4, 3.0),
             (5, 2.5), (5, 1.5), (5, 0.5), (5, -0.5), (5, -1.5), (5, -2.5), (4, -3.0), (3, -3.5), (2, -4.0), (1, -4.5),
             (0, -5.0), (-1, -4.5), (-2, -4.0), (-3, -3.5), (-4, -3.0), (-5, -2.5), (-5, -1.5), (-5, -0.5), (-5, 0.5),
             (-5, 1.5), (-5, 2.5), (-4, 3.0), (-3, 3.5), (-2, 4.0), (-1, 4.5)]

        # the time after which a segment needs recoating (in days)
        self.RECOATING_PERIOD = 365

        self._init_plot()

    def _init_plot(self):
        # get recoating data
        query = "SELECT MAX(ReplacementDate) AS ReplacementDate, SegmentPosition" \
                "       FROM MirrorRecoating" \
                "       GROUP BY SegmentPosition ORDER BY ReplacementDate, SegmentPosition"
        df = pd.read_sql(query, db.engine)

        # add missing segment positions
        missing_positions = [p for p in range(1, 92) if p not in df.SegmentPosition.values]
        df_missing = pd.DataFrame(dict(SegmentPosition=missing_positions,
                                       ReplacementDate=len(missing_positions) * [datetime.date(1970, 1, 1)]))
        df = df.append(df_missing, ignore_index=True)

        # sort by date (in descending order)
        df.sort_values(by='ReplacementDate', ascending=False, inplace=True)

        # add cumulative number of replacements since one recoating period ago
        start = self.now - datetime.timedelta(self.RECOATING_PERIOD)
        recoatings = len(df[df.ReplacementDate >= start])
        df['RecoatingsSinceYearStart'] = [max(recoatings - i, 0) for i in range(0, 91)]

        # add days since recoating
        df['DaysSinceReplacement'] = [(self.now - d).days for d in df.ReplacementDate.values]

        # add segment position coordinates
        df['SegmentPositionX'] = [self.mirror_positions[m][0] for m in df.SegmentPosition]
        df['SegmentPositionY'] = [self.mirror_positions[m][1] for m in df.SegmentPosition]
        df['SegmentPositionCornerXs'] = [self._segment_corners(m)[0] for m in df.SegmentPosition]
        df['SegmentPositionCornerYs'] = [self._segment_corners(m)[1] for m in df.SegmentPosition]

        # create data source
        source = ColumnDataSource(df)

        table = self._table(source)
        replacement_plot = self._replacement_plot(source)
        segment_plot = self._segment_plot(source)

        srp = vplot(replacement_plot, segment_plot)

        self.plot = hplot(table, srp)

    def _table(self, source):
        """The table of replacement dates and segment positions.

        Params:
        -------
        source : pandas.DataFrame
            Data source.

        Returns:
        --------
        bokeh.plotting.Figure
            Table of replacement dates and segment positions.
        """
        columns = [
            TableColumn(field='ReplacementDate', title='Installation Date', formatter=DateFormatter(format='d M yy')),
            TableColumn(field='SegmentPosition', title='Segment'),
            TableColumn(field='DaysSinceReplacement', title='Days Since Installation')
        ]

        return vform(DataTable(source=source, columns=columns, row_headers=False, width=400, height=1000))

    def _segment_plot(self, source):
        """Plot showing the mirror segments.

        The plot shows the 91 segment positions with their position number. The colour of the segments indicates how
        long ago they have been recoated.

        Params:
        -------
        source: pandas.DataFrame
            Data source.

        Returns:
        --------
        bokeh.plotting.Figure
            Plot showing the mirror segments.
        """

        def segment_color(date):
            """Fill colour of a mirror segment."""
            days = (datetime.datetime.now().date() - date).days
            days = min(days, self.RECOATING_PERIOD)
            days = max(days, 0)

            def hex_value(v):
                """Convert integer into a hexadecimal string suitable for specifying an RGB value in a css rule."""
                s = format(int(round(255 * v)), 'x')
                if len(s) < 2:
                    s = '0' + s
                return s

            # The colour ranges from dark green for recently recoated segments to white for segments which need to be
            # recoated.
            h = 99
            s = 100
            l = 33 + 67 * days / self.RECOATING_PERIOD
            rgb = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)

            return '#{r}{g}{b}'.format(r=hex_value(rgb[0]),
                                       g=hex_value(rgb[1]),
                                       b=hex_value(rgb[2]))

        plot = Figure(tools='tap', toolbar_location=None)
        colors = [segment_color(d) for d in source.data['ReplacementDate']]
        plot.patches(xs='SegmentPositionCornerXs',
                     ys='SegmentPositionCornerYs',
                     source=source,
                     color=colors,
                     line_color='#dddddd')
        plot.text(x='SegmentPositionX',
                  y='SegmentPositionY',
                  text='SegmentPosition',
                  source=source,
                  text_color='black',
                  text_align='center',
                  text_baseline='middle')

        plot.grid.grid_line_color = None
        plot.axis.visible = False

        plot.min_border_top = 20
        plot.min_border_bottom = 30

        plot.outline_line_color = None

        return plot

    def _segment_corners(self, m):
        """The coordinates of a mirror segment's corners.

        The centre of the central mirror has the coordinates (0, 0). The distance between centre and corners of the
        segment is 0.45. The distance between the centers of adjacent segments lying on the same horizontal or vertical
        line is 1. This means that the 91 segments in total cover a range from roughly -5 to 5 in both x and y
        direction.

        The coordinates are returned as a tuple (xs, ys), where xs (ys) are the x (y) coordinates of the corners. These
        coordinates can be used for Bokeh's Patch or Patches glyph.

        Params:
        -------
        m: int
            Number of the segment.

        Returns:
        --------
        tuple of lists
            The x and y coordinates of the segment's corners.

        """

        r = 0.45
        angles = np.radians(np.arange(0, 301, 60))
        offset = self.mirror_positions[m]
        xs = offset[0] + r * np.cos(angles)
        ys = offset[1] + r * np.sin(angles)
        return xs.tolist(), ys.tolist()

    def _replacement_plot(self, source):
        start = self.now - datetime.timedelta(days=self.RECOATING_PERIOD)
        start_timestamp = datetime.datetime(start.year, start.month, start.day, 0, 0, 0, 0).timestamp()
        end_timestamp = datetime.datetime(self.now.year, self.now.month, self.now.day, 0, 0, 0, 0).timestamp()
        x_range = DataRange1d(start=1000 * start_timestamp, end=1000 * end_timestamp)
        y_range = DataRange1d(start=0, end=120)
        plot = Figure(x_axis_type='datetime',
                      x_range=x_range,
                      y_range=y_range,
                      tools=['tap'],
                      toolbar_location=None)

        # required recoated segments
        plot.line(x=[start, self.now],
                  y=[0, 91],
                  legend='required recoated segments',
                  line_width=2,
                  line_color='blue')

        # recoated segments
        plot.line(x='ReplacementDate',
                  y='RecoatingsSinceYearStart',
                  source=source,
                  legend='recoated segments',
                  line_width=2,
                  color='orange')
        plot.circle(x='ReplacementDate',
                    y='RecoatingsSinceYearStart',
                    source=source,
                    legend='recoated segments',
                    size=6,
                    color='orange')

        date_format = '%d %b %Y'
        formats = dict(hours=[date_format], days=[date_format], months=[date_format], years=[date_format])
        plot.xaxis[0].formatter = DatetimeTickFormatter(formats=formats)

        plot.legend.location = 'top_left'

        plot.min_border_top = 20
        plot.min_border_bottom = 30

        return plot

