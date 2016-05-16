import datetime
import functools

from bokeh.models import Range1d
from bokeh.models.formatters import PrintfTickFormatter
import numpy as np
import pandas as pd

from app import db
from app.plot.plot import DialPlot
from app.plot.queries import DateRangeQueries
from app.plot.util import bin_by_semester, daily_bar_plot, day_range, day_running_average, \
    month_range, monthly_bar_plot, month_running_average, \
    neutral_color_func, required_for_semester_average, semester,\
    value_last_night, value_last_week


class ShutterOpenEfficiencyPlots:
    """Plots displaying the shutter open efficiency.

    The shutter open efficiency is defined as the ratio of the shutter open time and the science time observed between
    end of evening twilight and beginning of morning twilight. If no science observation was done in a period, the
    shutter open efficiency for that period is undefined.

    Params:
    -------
    date : datetime.date
        Date for which the plots are generated.
    **kwargs: keyword arguments
        Additional keyword arguments are passed on to the function or constructor creating a plot.
    """

    def __init__(self, date, **kwargs):
        self.date = date
        start = self.date - datetime.timedelta(days=300)
        end = self.date + datetime.timedelta(days=150)

        self.kwargs = kwargs

        queries = DateRangeQueries(start, end, db.engine)
        df_shutter_open_time = queries.shutter_open_time()
        df_time_breakdown = queries.time_breakdown()
        self.df = pd.merge(df_shutter_open_time, df_time_breakdown, on=['Date'], how='outer')

        # ignore values with no science time
        print(self.df[(self.df.Date > datetime.date(2016, 2, 29)) & (self.df.Date < datetime.date(2016, 4, 1))][['Date', 'ShutterOpenTime', 'ScienceTime']])
        self.df = self.df[self.df.ScienceTime > 0.0001]

        # avoid NaN issues later on
        self.df.fillna(value=0, inplace=True)

    def last_night_plot(self):
        """Dial plot displaying the operation efficiency for last night."""

        shutter_open_time = value_last_night(df=self.df, date=self.date, date_column='Date',
                                             value_column='ShutterOpenTime')
        science_time = value_last_night(df=self.df, date=self.date, date_column='Date', value_column='ScienceTime')
        shutter_open_efficiency = self._shutter_open_efficiency(shutter_open_time, science_time)

        return DialPlot(values=[shutter_open_efficiency],
                        label_values=range(0, 151, 10),
                        dial_color_func=neutral_color_func,
                        display_values=[str(round(shutter_open_efficiency, 1)) + '%'])

    def week_to_date_plot(self):
        """Dial plot displaying the operation efficiency for the seven days leading up to but excluding `self.date`."""

        shutter_open_time = value_last_week(df=self.df, date=self.date, date_column='Date',
                                            value_column='ShutterOpenTime')
        science_time = value_last_week(df=self.df, date=self.date, date_column='Date', value_column='ScienceTime')
        shutter_open_efficiency = self._shutter_open_efficiency(shutter_open_time, science_time)

        return DialPlot(values=[shutter_open_efficiency],
                        label_values=range(0, 151, 10),
                        dial_color_func=neutral_color_func,
                        display_values=[str(round(shutter_open_efficiency, 1)) + '%'],
                        **self.kwargs)

    def daily_plot(self, days):
        """Bar plot displaying the shutter open efficiency per day.

        The shutter open efficiency is shown for the `days` days leading to but excluding `self.date`. A day here refers
        to the time from noon to noon. For example, 22 May 2016 refers to the period from 22 May 2016, 12:00 to 23 May
        2016, 12:00.

        Params:
        -------
        days : int
            Number of days.

        Returns:
        --------
        app.plot.plot.TimeBarPlot
            Plot of shutter open efficiency as a function of the day.
        """

        df = self.df.copy()
        df['ShutterOpenEfficiency'] = 100 * np.divide(df.ShutterOpenTime, df.ScienceTime)

        start_date, end_date = day_range(self.date, days)
        trend_func = functools.partial(day_running_average, ignore_missing_values=True)

        return daily_bar_plot(df=df,
                              start_date=start_date,
                              end_date=end_date,
                              date_column='Date',
                              y_column='ShutterOpenEfficiency',
                              y_range=Range1d(start=0, end=100),
                              trend_func=trend_func,
                              y_formatters=[PrintfTickFormatter(format='%d%%')],
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
            df['ShutterOpenEfficiency'] = 100 * np.divide(df.ShutterOpenTime, df.ScienceTime)

        return monthly_bar_plot(df=self.df,
                                start_date=start_date,
                                end_date=end_date,
                                date_column='Date',
                                month_column='Month',
                                y_column='ShutterOpenEfficiency',
                                y_range=Range1d(start=0, end=80),
                                trend_func=trend_func,
                                post_binning_func=post_binning_func,
                                **self.kwargs)

    def semester_to_date_plot(self):
        """Dial plot displaying the shutter open efficiency for the semester in which `self.date` lies.

        All dates in the semester up to but excluding `self.date` are included when calculating the shutter open
        efficiency.

        Returns:
        --------
        app.plot.plot.DialPlot
            Plot of the shutter open efficiency for the semester to date.
        """

        sem = semester(self.date)
        binned_df = bin_by_semester(df=self.df, cutoff_date=self.date, date_column='Date', semester_column='Semester')
        current_semester = binned_df[binned_df.Semester == sem]
        if len(current_semester):
            shutter_open_efficiency = self._shutter_open_efficiency(current_semester.ShutterOpenTime[0],
                                                                current_semester.ScienceTime[0])
        else:
            shutter_open_efficiency = 0

        dial_color_func = neutral_color_func

        return DialPlot(values=[shutter_open_efficiency],
                        label_values=range(0, 101, 10),
                        dial_color_func=dial_color_func,
                        display_values=['{:.1f}%'.format(shutter_open_efficiency)],
                        **self.kwargs)

    def _shutter_open_efficiency(self, obs_time, science_time):
        return 100 * obs_time / science_time if science_time else np.NaN
