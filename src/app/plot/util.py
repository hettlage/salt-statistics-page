import datetime
import math

import numpy as np
import pandas
from bokeh.models import Range1d
from bokeh.models.formatters import DatetimeTickFormatter
from dateutil import parser

from app.plot.plot import TimeBarPlot


def bin_by_date(df, date_column, agg_func=np.sum):
    """Bin data by date.

    The data is grouped by dates according to the values of the specified date column, and then the aggregation function
    is applied to all the groups. The values of the month column of the resulting dataframe are chosen to have the same
    month as the corresponding dates in the original dataframe.

    A date starts and ends at midnight. This implies that you might have to shift your dates by 12 hours before
    passing the dataframe to this function.

    Note that in the returned dataframe the date column technically will have been replaced with a new column of dates
    without a time component.

    Params:
    -------
    df : pandas.DataFrame
        Data to bin.
    date_column : string
       Name of the column containing the date values used for grouping.
    agg_func : function, optional
       Aggregation function applied to the groups of values sharing the same month. The default is to sum the values.

    Returns:
    --------
    pandas.DataFrame:
        The binned data.
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
    """Bin data by month.

    The data is grouped by month according to the values of the specified date column, and then the aggregation function
    is applied to all the groups. The values of the month column of the resulting dataframe is chosen to have the same
    month as the corresponding dates in the original dataframe.

    A month starts and ends at midnight. This implies that you might have to shift your dates by 12 hours before
    passing the dataframe to this function.

    Note that in the returned dataframe the date column will have been replaced by the month column. The dates in this
    new column have no time component.

    Params:
    -------
    df : pandas.DataFrame
        Data to bin.
    date_column : string
        Name of the column containing the date values used for grouping.
    month_column : string
        Name to use for the column of month dates.
    agg_func : function, optional
        Aggregation function applied to the groups of values sharing the same month. The default is to sum the values.

    Return:
    pandas.DataFrame
        The binned data.
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
    dm = DX_AVERAGE_MONTH
    grouped[month_column] = [(start_date + months_between(start_date, parser.parse(d)) * dm).date()
                             for d in grouped.index]

    return grouped


DX_AVERAGE_MONTH = datetime.timedelta(seconds=365.25 * 24 * 3600 / 12)  # average month length


def bin_by_semester(df, date_column, semester_column, agg_func=np.sum):
    """Bin data by semester.

    The dataframe data is grouped by semester according to the values of the specified date column, and then the
    aggregation function is applied to all the groups. The values of the semester column of the resulting dataframe
    are chosen to have the same semester as the corresponding dates in the original dataframe.

    Semesters run from 1 May to 31 October (semester 1), and from 1 November to 30 April (semester 2). They start and
    end at midnight. This implies that you might have to shift your dates by 12 hours before passing the dataframe to
    this function.

    Note that in the returned dataframe the date column will have been replaced by the semester column. This column
    contains strings of the form 'yyyy-d', with yyyy being the year and d being the semester (i.e. 1 or 2).

    Params:
    -------
    df: pandas.DataFrame
        The data to bin.
    date_column: string
        Name of the column containing the date values used for grouping.
    semester_column: string
        Name to use for the column of month dates.
    agg_func: function, optional
        Aggregation function applied to the groups of values sharing the same month. The default is to sum the values.

    Return:
    pandas.DataFrame
        The binned data.
    """

    def sem(x):
        return semester(df[date_column].loc[x])

    # group by semester
    grouped = df.groupby(sem).aggregate(agg_func)

    # add semester column
    grouped[semester_column] = [s for s in grouped.index]

    return grouped


def filter_days_to_date(df, date, days, date_column):
    """Subset for dates within the week preceding a date.

    `df` is filtered by applying the criterion that the date in the `date_column` column is one of the `days` days
    leading up to but excluding `date`.

    Params:
    -------
    df : pandas.DataFrame
        Data to filter. The dataframe must have a column with dates (i.e. `datetime.date` instances).
    date: datetime.date
        Date relative to which the data is filtered.
    days : int
        Number of days.
    date_column : str
        Name of the column containing the dates.

    Returns:
    --------
    pandas.DataFrame
        Result of the filtering.

    Examples:
    ---------
    >>> filter_days_to_date(pandas.DataFrame(dict(Date=[datetime.date(2016, 5, 1), datetime.date(2016, 5, 2),\
                                                        datetime.date(2016, 5, 3), datetime.date(2016, 5, 4)],\
                                                  Value=[5, 8, 1, 4])),\
                            datetime.date(2016, 5, 4),\
                            2,\
                            'Date')
             Date  Value
    1  2016-05-02      8
    2  2016-05-03      1
    """

    return df[(df[date_column] >= date - datetime.timedelta(days=days)) &
              (df[date_column] <= date - datetime.timedelta(days=1))]


def filter_day_before_date(df, date, date_column):
    """Subset for the day before a date.

    `df` is filtered by applying the criterion that the date in the `date_column` column is equal to the day before
    `date`.

    Params:
    -------
    df : pandas.DataFrame
        Data to filter. The dataframe must have a column with dates (i.e. `datetime.date` instances).
    date: datetime.date
        Date relative to which the data is filtered.
    date_column : str
        Name of the column containing the dates.
    """

    return filter_days_to_date(df=df, date=date, days=1, date_column=date_column)


def filter_week_to_date(df, date, date_column):
    """Subset for dates within the week preceding a date.

    `df` is filtered by applying the criterion that the date in the `date_column` column is one of the 7 days leading
    up to but excluding `date`.

    Params:
    -------
    df : pandas.DataFrame
        Data to filter. The dataframe must have a column with dates (i.e. `datetime.date` instances).
    date: datetime.date
        Date relative to which the data is filtered.
    date_column : str
        Name of the column containing the dates.
    """

    return filter_days_to_date(df=df, date=date, days=7, date_column=date_column)


def daily_bar_plot(df, start_date, end_date, date_column, y_column, y_range, alt_y_column=None, alt_y_range=None):
    """A bar plot showing data by date.

    The data may contain alternative y values. If so, you have to specify both their column name and the value range to
    use for the alternative y axis.

    Params:
    -------
    df : pandas.DataFrame
        The data to plot.
    start_date : datetime.date
        The first date to include in the plot.
    end_date : datetime.date
        The last date to include in the plot.
    date_column : string
        Name of the column containing the dates.
    y_column : string
        Name of the column containing the y values to plot.
    y_range : bokeh.models.Range1d
        The value range to use for the y axis.
    alt_y_column : string, optional
        Name of the column column containing alternative y values.
    alt_y_range : bokeh.models.Range1d, optional
         The value range to use for the alternative y axis.

    Returns:
    --------
    plot.TimeBarPlot
        The plot.
    """

    if start_date >= end_date:
        raise ValueError('The start date ({start_date}) must be before the end date ({end_date}'
                         .format(start_date=start_date, end_date=end_date))

    date_formats = dict(hours=['%d'], days=['%d'], months=['%d'], years=['%d'])
    renamed_columns = {date_column: 'x', y_column: 'y'}
    if alt_y_column:
        renamed_columns[alt_y_column] = 'alt_y'
    return TimeBarPlot(df=df.rename(columns=renamed_columns),
                       dx=datetime.timedelta(days=1),
                       x_range=Range1d(start=start_date, end=end_date),
                       y_range=y_range,
                       date_formatter=DatetimeTickFormatter(formats=date_formats),
                       label_orientation=math.pi / 2,
                       alt_y_range=alt_y_range)


def monthly_bar_plot(df, start_date, end_date, date_column, month_column, y_column, y_range, alt_y_column=None,
                     alt_y_range=None):
    """A bar plot showing data by month.

    The data may contain alternative y values. If so, you have to specify both their column name and the value range to
    use for the alternative y axis.

    Any date in the start and end month can be used to specify these months.

    Params:
    -------
    df : pandas.DataFrame
        The data to plot.
    star t_date : datetime.date
        A date in the first month to include in the plot.
    end_date : datetime.date
        A date in the last month to include in the plot.
    date_column : string
        Name of the column containing the dates.
    y_column : string
        Name of the column containing the y values to plot.
    y_range : bokeh.models.Range1d
        The value range to use for the y axis.
    alt_y_column : string, optional
        Name of the column column containing alternative y values.
    alt_y_range : bokeh.models.Range1d, optional
         The value range to use for the alternative y axis.

    Returns:
    --------
    plot.TimeBarPlot
        The plot.
    """

    if start_date >= end_date:
        raise ValueError('The start date ({start_date}) must be before the end date ({end_date}'
                         .format(start_date=start_date, end_date=end_date))

    # figure out how many months to plot
    def months_since_2000(d):
        return 12 * (d.year - 2000) + d.month
    months = months_since_2000(end_date) - months_since_2000(start_date)

    mid_end_month = datetime.date(end_date.year, end_date.month, 15)
    date_formats = dict(hours=['%b'], days=['%b'], months=['%b'], years=['%b'])
    binned_df = bin_by_month(df=df,
                             date_column=date_column,
                             month_column=month_column)
    renamed_columns = {month_column: 'x', y_column: 'y'}
    if alt_y_column:
        renamed_columns[alt_y_column] = 'alt_y'
    return TimeBarPlot(df=binned_df.rename(columns=renamed_columns),
                       dx=DX_AVERAGE_MONTH,
                       x_range=Range1d(start=mid_end_month - months * DX_AVERAGE_MONTH,
                                       end=mid_end_month),
                       y_range=y_range,
                       date_formatter=DatetimeTickFormatter(formats=date_formats),
                       alt_y_range=alt_y_range)


def day_range(date, days):
    """Start and end date of a number of days leading up to but excluding a date.

    The start date is the first in the list of the `days` consecutive days leading up to but excluding `date`. The end
    date is the last date in this list, i.e. the day before `date`.

    Params:
    -------
    date : datetime.date
        Date for which to calculate the day range.
    days: int
        Number of days.

    Returns:
    --------
    tuple of datetime.date
        Start and end date.

    Examples:
    ---------
    >>> day_range(datetime.date(2016, 8, 4), 10)
    (datetime.date(2016, 7, 25), datetime.date(2016, 8, 3))
    """

    return date - datetime.timedelta(days=days), date - datetime.timedelta(days=1)


def month_range(date, months):
    """Start and end month of a number of months leading up to a date.

    The start month is the first month in the list of `months` consecutive months ending with the month before the one
    including `date`. The end month is the month before the one including `date`.

    Params:
    -------
    date : datetime.date
        Date for which to calculate the start month.
    months : int
        Number of months.

    Returns:
    --------
    tuple of datetime.date
        The 15th of the start and end month.

    Examples:
    --------
    The month of the given date isn't included when counting months.

    >>> month_range(datetime.date(2016, 5, 3), 6)
    (datetime.date(2015, 11, 15), datetime.date(2016, 4, 15))

    The month of the given date isn't included, even if the date is right at the month end.

    >>> month_range(datetime.date(2016, 12, 31), 2)
    (datetime.date(2016, 10, 15), datetime.date(2016, 11, 15))
    """

    year = date.year
    month = date.month
    end_date = None
    for i in range(months):
        month -= 1
        if month == 0:
            month = 12
            year -= 1
        if i == 0:
            end_date = datetime.date(year, month, 15)
    start_date = datetime.date(year, month, 15)

    return start_date, end_date


def semester(date):
    """The semester containing a date.

    Semester 1 of a year starts on 1 May, semester 2 on 1 November. The semester is returned as a string of the form
    yyyy-s, with yyyy and s denoting the year and semester (1 or 2), respectively.

    Params:
    -------
    date : datetime.date
        Date in the semester.

    Returns:
    --------
    str
        Semester.

    Examples:
    ---------
    >>> semester(datetime.date(2016, 5, 1))
    '2016-1'

    >>> semester(datetime.date(2016, 10, 31))
    '2016-1'

    >>> semester(datetime.date(2016, 11, 1))
    '2016-2'

    >>> semester(datetime.date(2017, 4, 30))
    '2016-2'

    >>> semester(datetime.date(2017, 8, 4))
    '2017-1'
    """
    year = date.year
    month = date.month
    if month < 5:
        return '{0}-{1}'.format(year - 1, 2)
    elif month < 11:
        return '{0}-{1}'.format(year, 1)
    else:
        return '{0}-{1}'.format(year, 2)
