import datetime
import functools

import numpy as np

from bokeh.models import Range1d
from bokeh.models.formatters import PrintfTickFormatter
from app import db
from app.plot.plot import DialPlot
from app.plot.queries import DateRangeQueries
from app.plot.util import bin_by_semester, daily_bar_plot, day_range, day_running_average, \
    good_mediocre_bad_color_func, monthly_bar_plot, month_range, month_running_average, \
    required_for_semester_average, semester, value_last_night, value_last_week


class ScienceTimePlots:
    """Plots displaying the science time.

    Params:
    -------
    date : datetime.date
        The date for which to generate the plots.
    **kwargs: keyword arguments
        Additional keyword arguments are passed on to the function or constructor creating a plot.
    """

    def __init__(self, date, **kwargs):
        self.date = date
        start = self.date - datetime.timedelta(days=300)
        end = self.date + datetime.timedelta(days=150)

        self.kwargs = kwargs

        self.df = DateRangeQueries(start, end, db.engine).time_breakdown()[['Date', 'NightLength', 'ScienceTime']]

    def last_night_plot(self):
        """Dial plot displaying the science time for the date preceding `self.date`.

        The science time is displayed as a percentage relative to the night length. In addition its absolute value
        is displayed in minutes.

        Returns:
        --------
        app.plot.plot.DialPlot
            Plot displaying the science time for last night.
        """

        science_time = value_last_night(df=self.df, date=self.date, date_column='Date', value_column='ScienceTime')
        night_length = value_last_night(df=self.df, date=self.date, date_column='Date', value_column='NightLength')
        science_time_percentage = 100 * science_time / night_length

        dial_color_func = good_mediocre_bad_color_func(good_limit=47, bad_limit=37)

        return DialPlot(values=[science_time_percentage],
                        label_values=[0, 10, 20, 30, 37, 47, 60, 70, 80, 90, 100],
                        dial_color_func=dial_color_func,
                        display_values=['{:.1f}%'.format(science_time_percentage),
                                        '{:d}m'.format(int(science_time / 60))],
                        **self.kwargs)

    def week_to_date_plot(self):
        """Dial plot displaying the science time for the seven days leading up to but excluding `self.date`.

        The science time is displayed as a percentage relative to the night length. In addition its absolute value
        is displayed in minutes.

        Returns:
        --------
        app.plot.plot.DialPlot
            Plot displaying the science time for the last seven days.
        """

        science_time = value_last_week(df=self.df, date=self.date, date_column='Date', value_column='ScienceTime')
        night_length = value_last_week(df=self.df, date=self.date, date_column='Date', value_column='NightLength')
        science_time_percentage = 100 * science_time / night_length

        dial_color_func = good_mediocre_bad_color_func(good_limit=47, bad_limit=37)

        return DialPlot(values=[science_time_percentage],
                        label_values=[0, 10, 20, 30, 37, 47, 60, 70, 80, 90, 100],
                        dial_color_func=dial_color_func,
                        display_values=['{:.1f}%'.format(science_time_percentage),
                                        '{:d}m'.format(int(science_time / 60))],
                        **self.kwargs)

    def daily_plot(self, days):
        """Bar plot displaying the number of block visits per day.

        The number of block visits is shown for the `days` days leading to but excluding `self.date`. A day here refers
        to the time from noon to noon. For example, 22 May 2016 refers to the period from 22 May 2016, 12:00 to 23 May
        2016, 12:00.

        Params:
        -------
        days : int
            Number of days.

        Returns:
        --------
        app.plot.plot.TimeBarPlot
            Plot of number of block visits as a function of the day.
        """

        start_date, end_date = day_range(self.date, days)
        trend_func = functools.partial(day_running_average, ignore_missing_values=False)

        df = self.df.copy()
        df['ScienceTimePercentage'] = 100 * np.divide(df.ScienceTime, df.NightLength)
        df['ScienceTime'] /= 60

        return daily_bar_plot(df=df,
                              start_date=start_date,
                              end_date=end_date,
                              date_column='Date',
                              y_column=['ScienceTime', 'ScienceTimePercentage'],
                              y_range=[Range1d(start=0, end=700), Range1d(start=0, end=100)],
                              y_formatters=[PrintfTickFormatter(format='%.0fm'), PrintfTickFormatter(format='%.0f%%')],
                              trend_func=trend_func,
                              **self.kwargs)

    def monthly_plot(self, months):
        """Bar plot displaying the shutter open efficiency per momth.

        The operation efficiency is shown for the `months` months leading to but excluding the month containing
        `self.date`. A month here refers start at noon of the first of the month. For example, May 2016 refers to the
        period from 1 May 2016, 12:00 to 1 June 2016, 12:00.

        Params:
        -------
        months : int
            Number of months.

        Returns:
        --------
        app.plot.plot.TimeBarPlot
            Plot of shutter open efficiency as a function of the month.
        """

        start_date, end_date = month_range(self.date, months)
        trend_func = functools.partial(month_running_average, ignore_missing_values=False)

        def post_binning_func(df):
            df['ScienceTimePercentage'] = 100 * np.divide(df.ScienceTime, df.NightLength)
            df.ScienceTime /= 3600

        return monthly_bar_plot(df=self.df,
                                start_date=start_date,
                                end_date=end_date,
                                date_column='Date',
                                month_column='Month',
                                y_column=['ScienceTime', 'ScienceTimePercentage'],
                                y_range=[Range1d(start=0, end=200), Range1d(start=0, end=70)],
                                y_formatters=[PrintfTickFormatter(format='%.0fh'),
                                              PrintfTickFormatter(format='%.0f%%')],
                                trend_func=trend_func,
                                post_binning_func=post_binning_func,
                                **self.kwargs)

    def semester_to_date_plot(self):
        """Dial plot displaying the science time for the semester in which `self.date` lies.

        All dates in the semester up to but excluding `self.date` are included when calculating the shutter open
        efficiency.

        The science time is displayed as a percentage relative to the night length. A second hand shows the average
        percentage which must be achieved in the remaining time of the semester in order to achieve the target
        percentage.

        In addition its absolute value is displayed in hours.

        Returns:
        --------
        app.plot.plot.DialPlot
            Plot of the shutter open efficiency for the semester to date.
        """

        sem = semester(self.date)
        binned_df = bin_by_semester(df=self.df, cutoff_date=self.date, date_column='Date', semester_column='Semester')
        current_semester = binned_df[binned_df.Semester == sem]
        target_percentage = 55
        if len(current_semester):
            science_time_percentage = 100 * current_semester.ScienceTime[0] / current_semester.NightLength[0]
            required_percentage = required_for_semester_average(self.date, science_time_percentage, target_percentage)
            science_time = current_semester.ScienceTime[0] / 3600
        else:
            science_time_percentage = 0
            required_percentage = target_percentage
            science_time = 0

        dial_color_func = good_mediocre_bad_color_func(good_limit=49, bad_limit=40)

        return DialPlot(values=[science_time_percentage, required_percentage],
                        label_values=[v for v in range(0, 46, 5)] + [49] + [v for v in range(55, 76, 5)],
                        dial_color_func=dial_color_func,
                        display_values=['{:.1f}%'.format(science_time_percentage),
                                        '{:.1f}h'.format(science_time)],
                        **self.kwargs)
