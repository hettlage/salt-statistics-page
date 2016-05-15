import datetime
import math

import numpy as np
import pandas
from bokeh.models import Line, Range1d
from bokeh.models.formatters import DatetimeTickFormatter
from dateutil import parser

from app.plot.plot import TimeBarPlot


def bin_by_date(df, date_column, agg_func=np.sum):
    """Bin data by date.

    The data is grouped by dates according to the values of the specified date column, and then the aggregation function
    is applied to all the groups. The values of the month column of the resulting data frame are chosen to have the same
    month as the corresponding dates in the original data frame.

    A date starts and ends at midnight. This implies that you might have to shift your dates by 12 hours before
    passing the data frame to this function.

    Note that in the returned data frame the date column technically will have been replaced with a new column of dates
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
    is applied to all the groups. The values of the month column of the resulting data frame is chosen to have the same
    month as the corresponding dates in the original data frame.

    A month starts and ends at midnight. This implies that you might have to shift your dates by 12 hours before
    passing the data frame to this function.

    Note that in the returned data frame the date column will have been replaced by the month column. The dates in this
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

    The data frame data is grouped by semester according to the values of the specified date column, and then the
    aggregation function is applied to all the groups. The values of the semester column of the resulting data frame
    are chosen to have the same semester as the corresponding dates in the original data frame.

    Semesters run from 1 May to 31 October (semester 1), and from 1 November to 30 April (semester 2). They start and
    end at midnight. This implies that you might have to shift your dates by 12 hours before passing the data frame to
    this function.

    Note that in the returned data frame the date column will have been replaced by the semester column. This column
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
        Data to filter. The data frame must have a column with dates (i.e. `datetime.date` instances).
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
        Data to filter. The data frame must have a column with dates (i.e. `datetime.date` instances).
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
        Data to filter. The data frame must have a column with dates (i.e. `datetime.date` instances).
    date: datetime.date
        Date relative to which the data is filtered.
    date_column : str
        Name of the column containing the dates.
    """

    return filter_days_to_date(df=df, date=date, days=7, date_column=date_column)


def value_last_night(df, date, date_column, value_column):
    """Aggregate value of a data frame column for the date preceding a given date.

    The data frame is filtered to only have rows with the date preceding `date`, and the values of the `value_column`
    column are summed for the remaining rows.

    Params:
    -------
    df : pandas.DataFrame
        Data.
    date : datetime.date
        Date.
    date_column : str
        Name of the column containing the dates.
    value_column : str
        Name of the column containing the values to consider.

    Returns:
    --------
    float
        The aggregate value for the date preceding `date`.
    """

    last_night = filter_day_before_date(df=df, date=date, date_column=date_column)
    return np.sum(last_night[value_column])


def value_last_week(df, date, date_column, value_column):
    """Aggregate value of a data frame column for the seven days leading up to but excluding a given date.

    The data frame is filtered to only have rows with the date within the seven days preceding `date`, and the values of
    the `value_column` column are summed for the remaining rows.

    Params:
    -------
    df : pandas.DataFrame
        Data.
    date : datetime.date
        Date.
    date_column : str
        Name of the column containing the dates.
    value_column : str
        Name of the column containing the values to consider.

    Returns:
    --------
    float
        The aggregate value for the seven days preceding `date`.
    """

    last_week = filter_week_to_date(df=df, date=date, date_column=date_column)
    return np.sum(last_week[value_column])


def daily_bar_plot(df, start_date, end_date, date_column, y_column, y_range, trend_func, y_formatters=(),
                   alt_y_column=None, alt_y_range=None):
    """A bar plot showing data by date.

    The data may contain alternative y values. If so, you have to specify both their column name and the value range to
    use for the alternative y axis.

    An example for `trend_func` would be `functools.partial(day_running_average, ignore_missing_values=False)`. Pass
    None if there should be no trend line.

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
    trend_func: function
        Function to use for calculating trend values. This function must accept a Pandas data frame (having columns
        named 'x' and 'y') and an x value as its arguments.
    y_formatters : sequence of bokeh.models.formatters.TickFormatter, optional
        The formatters to use for the y axes. If there are more axes than formatters, the last formatter in the
        sequence is used for the remaining axes.
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

    if y_column == alt_y_column:
        raise ValueError('The values of y_column and the alt_y_column must not be the same.')

    date_formats = dict(hours=['%d'], days=['%d'], months=['%d'], years=['%d'])
    renamed_columns = {date_column: 'x', y_column: 'y'}
    if alt_y_column:
        renamed_columns[alt_y_column] = 'alt_y'
    renamed_df = df.rename(columns=renamed_columns)
    x_range = Range1d(start=start_date, end=end_date)
    dx = datetime.timedelta(days=1)
    plot = TimeBarPlot(df=renamed_df,
                       dx=dx,
                       x_range=x_range,
                       y_range=y_range,
                       date_formatter=DatetimeTickFormatter(formats=date_formats),
                       y_formatters=y_formatters,
                       label_orientation=math.pi / 2,
                       alt_y_range=alt_y_range)

    if trend_func:
        add_trend_curve(plot=plot.plot,
                        df=renamed_df,
                        x_min=x_range.start,
                        x_max=x_range.end,
                        dx=dx,
                        trend_func=trend_func)

    return plot


def monthly_bar_plot(df, start_date, end_date, date_column, month_column, y_column, y_range, trend_func,
                     post_binning_func=None, y_formatters=(), alt_y_column=None, alt_y_range=None, **kwargs):
    """A bar plot showing data by month.

    The data may contain alternative y values. If so, you have to specify both their column name and the value range to
    use for the alternative y axis.

    Any date in the start and end month can be used to specify these months.

    An example for `trend_func` would be `functools.partial(month_running_average, ignore_missing_values=False)`. Pass
    None if there should be no trend line.

    The `post_binning_func` function is applied to the data frame after binning, but before plotting it. One example
    where to use it is if you are considering a ratio of a values in two columns a and b. In this case the ration for
    a month should calculated by dividing the binned values for a and b. This can be achieved by passing the followingf
    function as `post_binning_func`.::

        def f(df):
            df['ratio'] = np.divide(df.a, df.b)

    'ratio' would then be used a value of the `y_column` parameter.

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
    trend_func: function
        Function to use for calculating trend values. This function must accept a Pandas data frame (having columns
        named 'x' and 'y') and an x value as its arguments.
    post_binning_func: function
        Function for modfifying the binned data frame. The function should accept a data frame as its only argument.
        The default is `None`, which means that the binned data frame isn't modified.
    y_formatters : sequence of bokeh.models.formatters.TickFormatter
        The formatters to use for the y axes. If there are more axes than formatters, the last formatter in the
        sequence is used for the remaining axes.
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

    # apply post binning function
    if post_binning_func:
        post_binning_func(binned_df)

    renamed_columns = {month_column: 'x', y_column: 'y'}
    binned_df = binned_df.rename(columns=renamed_columns)
    if alt_y_column:
        renamed_columns[alt_y_column] = 'alt_y'
    x_range = Range1d(start=mid_end_month - months * DX_AVERAGE_MONTH, end=mid_end_month)
    dx = DX_AVERAGE_MONTH
    plot = TimeBarPlot(df=binned_df,
                       dx=dx,
                       x_range=x_range,
                       y_range=y_range,
                       date_formatter=DatetimeTickFormatter(formats=date_formats),
                       y_formatters=y_formatters,
                       alt_y_range=alt_y_range)

    if trend_func:
        add_trend_curve(plot=plot.plot,
                        df=binned_df,
                        x_min=x_range.start,
                        x_max=x_range.end,
                        dx=dx,
                        trend_func=trend_func)

    return plot


def add_trend_curve(plot, df, x_min, x_max, dx, trend_func):
    """Add trend curve to a plot.

    Starting with the value `x_min`, trend values are calculated by means of `trend_func` for the values `x + n * dx`
    in [`x_min`, `x_max`]. Note that it is not guaranteed that any of these values exist in `df`. Thus `trend_func`
    should calculate meaningful trend values even if its second argument is not contained in `df`.

    Params:
    -------
    plot: bokeh.plotting.Figure
        Plot to which the trend curve is added.
    df : pandas.DataFrame
        Data for which the trend curve is generated. The data frame must have columns named x and y.
    x_min : number-like
        Minimum x value for which to calculate a trend. Must be sortable.
    x_max : number-like
        Maximum x value for which to calculate a trend. Must be sortable.
    dx : number-like
        Spacing between subsequent x values in the trend curve.
    trend_func: function
        Trend value. The function must accept a Pandas data frame and another object as its two arguments. `df` is passed
        as the first, and an x value as the second argument.
    """

    if x_min >= x_max:
        raise ValueError('x_min ({x_min}) must be less than x_max ({x_max}'.format(x_min=x_min, x_max=x_max))

    x_arr = []
    x = x_min
    while x <= x_max:
        x_arr.append(x)
        x += dx
    trend_arr = [trend_func(df, x) for x in x_arr]

    plot.line(x=x_arr, y=trend_arr, line_color='green', line_width=3)


def running_average_window(date, window_half_width, dt, now):
    """The window to use for calculating a running average.

    The window is taken to extend from `date - window_half_width` to `date + window_half_width`. However, if the end
    of this window is equal to or later than `now`, the end is taken to be `now`. If both the start and end are equal to
    or later than `now`, None is returned.

    Note that `now` is not necessarily the same as `datetime.now().date()`. For example, when dealing with months it
    should rather be the beginning of the current month.

    Params:
    -------
    date: datetime.date
        Date for which the window is calculated.
    window_half_width: datetime.timedelta
        Half the width of the window period. For example, if the window extends over four months, `window_half_width`
        must be 2.
    dt: datetime.timedelta
        Stepsize by which to decrease the window size while the window conflicts with `now`.
    now: datetime.date
        The "current date", i.e. the date from which onward no data exists.

    Returns:
    --------
    tuple of datetime.date
        The start and end date of the window.

    Examples:
    ---------
    The window lies completely in the past.

    >>> running_average_window(date=datetime.date(2016, 5, 11),\
                               window_half_width=datetime.timedelta(days=3),\
                               dt=datetime.timedelta(days=1),\
                               now=datetime.date(2016, 5, 15))
    (datetime.date(2016, 5, 8), datetime.date(2016, 5, 14))

    The window lies partly in the future.

    >>> running_average_window(date=datetime.date(2016, 5, 11),\
                               window_half_width=datetime.timedelta(days=3),\
                               dt=datetime.timedelta(days=1),\
                               now=datetime.date(2016, 5, 14))
    (datetime.date(2016, 5, 8), datetime.date(2016, 5, 13))

    The window lies completely in the future.

    >>> running_average_window(date=datetime.date(2016, 5, 11),\
                               window_half_width=datetime.timedelta(days=3),\
                               dt=datetime.timedelta(days=1),\
                               now=datetime.date(2016, 5, 8))\
        is None
    True
    """

    if dt <= datetime.timedelta(seconds=0):
        raise ValueError('dt ({dt}) must be positive.'.format(dt=dt))

    window_start = date - window_half_width
    window_end = date + window_half_width

    # the future has no bearing on the trend
    if now <= window_start:
        return None
    while now <= window_end:
        window_end -= dt

    return window_start, window_end


def month_running_average(df, date, ignore_missing_values):
    """Running average for monthly bins.

    Params:
    -------
    df : pandas.DataFrame
        Data from which to calculate the running average at `date`. The data frame must have columns named 'x' and 'y',
        and the x column must contain dates.
    date: datetime.date
        Date for which to calculate the running average.
    ignore_missing_values: bool
        Whether to ignore missing values or to assume their y value is 0.
    """

    now = datetime.datetime.now().date()
    current_month_start = datetime.date(now.year, now.month, 1)
    dt = DX_AVERAGE_MONTH
    window = running_average_window(date=date,
                                    window_half_width=dt,
                                    dt=dt,
                                    now=current_month_start)
    return running_bin_average(df=df,
                               window=window,
                               dx=dt,
                               ignore_missing_values=ignore_missing_values)


def day_running_average(df, date, ignore_missing_values):
    """Running average for daily bins.

    Params:
    -------
    df : pandas.DataFrame
        Data from which to calculate the running average at `date`. The data frame must have columns named 'x' and 'y',
        and the x column must contain dates.
    date: datetime.date
        Date for which to calculate the running average.
    ignore_missing_values: bool
        Whether to ignore missing values or to assume their y value is 0.

    Return:
    -------
    float
        Running average.
    """

    now = datetime.datetime.now().date()
    dt = datetime.timedelta(days=1)
    window = running_average_window(date=date,
                                    window_half_width=7 * dt,
                                    dt=dt,
                                    now=now)
    return running_bin_average(df=df,
                               window=window,
                               dx=dt,
                               ignore_missing_values=ignore_missing_values)


def running_bin_average(df, window, dx, ignore_missing_values):
    """Running average of binned data.

    It is assumed that the x values are equidistant, with a distance `dx` between neighbouring values, even though some
    of these values might be missing in `df`.

    The average is calculated by summing all y values in the interval `[window[0] - 0.1 * dx, window[1] + 0.1 * dx]`
    and then dividing through the number B of bins in that interval.

    The meaning of B depends on the value of the `ignore_missing_values` flag, If the latter is `True`, B is the
    number of rows in df whose x column value lies in the interval. Otherwise it is equal to
    `int(math.round(window / dx)) + 1`. In other words, if `ignore_missing_values` missing x values are assumed to have
    zero as corresponding y value.

    If the bin count B is zero, 0 is returned as running average.

    Params:
    -------
    df : pandas.DataFrame
        Data from which to calculate the running average at `x`. The data frame must have columns named 'x' and 'y', and
        the x column must contain dates.
    window: tuple of number-like
        Start and end of the window over which is averaged.
    dx : number-like
        Distance between subsequent x values.
    ignore_missing_values : bool
        Whether to ignore missing values or to assume their y value is 0.

    Returns:
    --------
    float
        Running average

    Examples:
    ---------
    Don't ignore missing values, but treat them as having 0 as y value.

    >>> running_bin_average(df=pandas.DataFrame(dict(x=[1, 3, 5, 9, 11, 15], y=[4, 3, 5, 1, 3, 1])),\
                            dx=2,\
                            window=(5, 13),\
                            ignore_missing_values=False)
    1.8

    Ignore missing values.

    >>> running_bin_average(df=pandas.DataFrame(dict(x=[1, 3, 5, 9, 11, 15], y=[4, 3, 5, 1, 3, 1])),\
                            dx=2,\
                            window=(5, 13),\
                            ignore_missing_values=True)
    3.0

    If there are no values, 0 is returned.

    >>> running_bin_average(df=pandas.DataFrame(dict(x=[], y=[])),\
                            dx=2,\
                            window=(5, 13),\
                            ignore_missing_values=True)
    0
    """

    start = window[0]
    end = window[1]
    if start >= end:
        raise ValueError('The window start ({start}) must be less than the end ({end}).'.format(start=start, end=end))

    extended_start = start - 0.1 * dx   # the 0.1 * dx is added/subtracted to avoid rounding issues
    extended_end = end + 0.1 * dx

    window_df = df[(df.x >= extended_start) & (df.x <= extended_end)]
    if ignore_missing_values:
        bin_count = len(window_df)
    else:
        bin_count = 1 + int(round((end - start) / dx))

    if bin_count == 0:
        return 0

    return np.sum(window_df.y) / bin_count


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


def good_mediocre_bad_color_func(good_limit, bad_limit):
    """Generate the function for deciding what color to use for good, mediocre and bad values.

    Params:
    -------
    good_limit : float
        Largest or smallest (depending on whether `bad_limit` is larger than `good_limit`) value for which values
        are considered to be good.
    bad_limit : float
        Largest or smallest (depending on whether `good_limit` is larger than `bad_limit`) value for which values
        are considered to be bad.

    Returns:
    --------
    function:
        Function for mapping a value to a color.
    """

    good_color = '#19af54'
    mediocre_color = '#fdbf2d'
    bad_color = '#fc0d1b'

    if good_limit < bad_limit:
        first_limit = good_limit
        second_limit = bad_limit
        first_color = good_color
        second_color = mediocre_color
        third_color = bad_color
    else:
        first_limit = bad_limit
        second_limit = good_limit
        first_color = bad_color
        second_color = mediocre_color
        third_color = good_color

    def f(x):
        if x < first_limit:
            return first_color
        elif x < second_limit:
            return second_color
        else:
            return third_color

    return f
