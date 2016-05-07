import datetime
import math

import numpy as np
from bokeh.models import Range1d
from bokeh.models.formatters import DatetimeTickFormatter
from dateutil import parser

from .plot import TimeBarPlot

def bin_by_date(df, date_column, agg_func=np.sum):
    """Bin dataframe data by date.

    The dataframe data is grouped by dates according to the values of the specified date column, and then the
    aggregation function is applied to all the groups. The values of the month column of the resulting dataframe are
    chosen to have the same month as the corresponding dates in the original dataframe.

    A date starts and ends at midnight. This implies that you might have to shift your dates by 12 hours before
    passing the dataframe to this function.

    Note that in the returned dataframe the date column technically will have been replaced with a new column of dates
    without a time component.

    Params:
    df: Pandas dataframe
    date_column: name of the column containing the date values used for grouping
    agg_func: aggregation function applied to the groups of values sharing the same month

    Return:
    A dataframe with the data binned by date
    """

    def night(x):
        d = df[date_column].loc[x]
        return '{0}-{1}-{2}'.format(d.year, d.month, d.day)

    # group by date
    grouped = df.groupby(night).aggregate(agg_func)

    # add date column
    grouped[date_column] = [parser.parse(d).date() for d in grouped.index]

    return grouped


def bin_by_month(df, date_column, month_column, agg_func=np.sum):
    """Bin dataframe data by month.

    The dataframe data is grouped by month according to the values of the specified date column, and then the
    aggregation function is applied to all the groups. The values of the month column of the resulting dataframe is
    are chosen to have the same month as the corresponding dates in the original dataframe.

    A month starts and ends at midnight. This implies that you might have to shift your dates by 12 hours before
    passing the dataframe to this function.

    Note that in the returned dataframe the date column will have been replaced by the month column. The dates in this
    new column have no time component.

    Params:
    df: Pandas dataframe
    date_column: name of the column containing the date values used for grouping
    month_column: name to use for the column of month dates
    agg_func: aggregation function applied to the groups of values sharing the same month

    Return:
    A dataframe with the data binned by month
    """

    def month(x):
        d = df[date_column].loc[x]
        return '{0}-{1}-15'.format(d.year, d.month)

    # group by month
    grouped = df.groupby(month).aggregate(agg_func)

    # months between two dates
    def months_between(d1, d2):
        def months_since_2000(d):
            return (d.year - 2000) * 12 + d.month
        return months_since_2000(d2) - months_since_2000(d1)

    # add month column
    start_date = parser.parse(grouped.index[0])
    dm = DX_MONTH
    grouped[month_column] = [(start_date + months_between(start_date, parser.parse(d)) * dm).date()
                             for d in grouped.index]

    return grouped


DX_MONTH = datetime.timedelta(seconds=365.25 * 24 * 3600 / 12)  # average month length


def bin_by_semester(df, date_column, semester_column, agg_func=np.sum):
    """Bin dataframe data by semester.

    The dataframe data is grouped by semester according to the values of the specified date column, and then the
    aggregation function is applied to all the groups. The values of the semester column of the resulting dataframe
    are chosen to have the same semester as the corresponding dates in the original dataframe.

    Semesters run from 1 May to 31 October (semester 1), and from 1 November to 30 April (semester 2). They start and
    end at midnight. This implies that you might have to shift your dates by 12 hours before passing the dataframe to
    this function.

    Note that in the returned dataframe the date column will have been replaced by the semester column. This column
    contains strings of the form 'yyyy-d', with yyyy being the year and d being the semester (i.e. 1 or 2).

    Params:
    df: Pandas dataframe
    date_column: name of the column containing the date values used for grouping
    semester_column: name to use for the column of month dates
    agg_func: aggregation function applied to the groups of values sharing the same month

    Return:
    A dataframe with the data binned by month
    """

    def semester(x):
        d = df[date_column].loc[x]
        year = d.year
        month = d.month
        if month < 5:
            return '{0}-{1}'.format(year - 1, 2)
        elif month < 11:
            return '{0}-{1}'.format(year, 1)
        else:
            return '{0}-{1}'.format(year, 2)

    # group by month
    grouped = df.groupby(semester).aggregate(agg_func)

    # add semester column
    grouped[semester_column] = [s for s in grouped.index]

    return grouped


def daily_bar_plot(df, night, date_column, y_column, y_range):
    date_formats = dict(hours=['%d'], days=['%d'], months=['%d'], years=['%d'])
    return TimeBarPlot(df=df.rename(columns={date_column: 'x', y_column: 'y'}),
                       dx=datetime.timedelta(days=1),
                       x_range=Range1d(start=night - datetime.timedelta(days=31),
                                   end=night- datetime.timedelta(days=1)),
                       y_range=y_range,
                       date_formatter=DatetimeTickFormatter(formats=date_formats),
                       label_orientation=math.pi / 2)


def monthly_bar_plot(df, night, date_column, month_column, y_column, y_range):
    mid_month = datetime.date(night.year, night.month, 15)
    date_formats = dict(hours=['%b'], days=['%b'], months=['%b'], years=['%b'])
    binned_df = bin_by_month(df=df,
                             date_column=date_column,
                             month_column=month_column)
    return TimeBarPlot(df=binned_df.rename(columns={month_column: 'x', y_column: 'y'}),
                       dx=DX_MONTH,
                       x_range=Range1d(start=mid_month - 6 * DX_MONTH,
                                       end=mid_month - 1 * DX_MONTH),
                       y_range=y_range,
                       date_formatter=DatetimeTickFormatter(formats=date_formats))
