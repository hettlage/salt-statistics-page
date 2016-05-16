import datetime
import functools

from bokeh.models import Range1d
from bokeh.models.formatters import PrintfTickFormatter
import numpy as np
import pandas as pd

from app import db
from app.plot.plot import DialPlot
from app.plot.queries import DateRangeQueries
from app.plot.util import bin_by_semester, daily_bar_plot, day_range, day_running_average,\
                          month_range, monthly_bar_plot, month_running_average,\
                          good_mediocre_bad_color_func, semester, required_for_semester_average,\
                          value_last_night, value_last_week


class OperationEfficiencyPlots:
    """Plots displaying the operation efficiency.

    The operation efficiency is defined as the ratio of the observing time for all accepted block visits, as calculated
    by the PIPT, and the science time observed between end of evening twilight and beginning of morning twilight. If no
    science observation was done in a period, the operation efficiency for that period is undefined.

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
        df_obs_time = queries.observation_time()
        df_time_breakdown = queries.time_breakdown()
        self.df = pd.merge(df_obs_time, df_time_breakdown, on=['Date'], how='outer')

        # ignore values with no science time
        print(self.df[(self.df.Date > datetime.date(2016, 4, 30)) & (self.df.Date < datetime.date(2016, 6, 1))])
        self.df = self.df[self.df.ScienceTime > 0.0001]

        # avoid NaN issues later on
        self.df.fillna(value=0, inplace=True)

    def last_night_plot(self):
        """Dial plot displaying the operation efficiency for last night, i.e. for the date preceding `self.date`.

        Returns:
        --------
        app.plot.plot.DialPlot
            Plot displaying the operation efficiency for last night.
        """

        obs_time = value_last_night(df=self.df, date=self.date, date_column='Date', value_column='ObsTime')
        science_time = value_last_night(df=self.df, date=self.date, date_column='Date', value_column='ScienceTime')
        operation_efficiency = self._observation_efficiency(obs_time, science_time)

        label_color_func = good_mediocre_bad_color_func(bad_limit=80, good_limit=90)

        return DialPlot(values=[operation_efficiency],
                        label_values=range(0, 151, 10),
                        label_color_func=label_color_func,
                        display_values=['{:.1f}%'.format(operation_efficiency)],
                        **self.kwargs)

    def week_to_date_plot(self):
        """Dial plot displaying the operation efficiency for the seven days leading up to but excluding `self.date`.

        Returns:
        --------
        app.plot.plot.DialPlot
            Plot displaying the operation efficiency for the last seven days.
        """

        obs_time = value_last_week(df=self.df, date=self.date, date_column='Date', value_column='ObsTime')
        science_time = value_last_week(df=self.df, date=self.date, date_column='Date', value_column='ScienceTime')
        operation_efficiency = self._observation_efficiency(obs_time, science_time)

        label_color_func = good_mediocre_bad_color_func(bad_limit=80, good_limit=90)

        return DialPlot(values=[operation_efficiency],
                        label_values=range(0, 151, 10),
                        label_color_func=label_color_func,
                        display_values=['{:.1f}%'.format(operation_efficiency)],
                        **self.kwargs)

    def daily_plot(self, days):
        """Bar plot displaying the operation efficiency per day.

        The operation efficiency is shown for the `days` days leading to but excluding `self.date`. A day here refers
        to the time from noon to noon. For example, 22 May 2016 refers to the period from 22 May 2016, 12:00 to 23 May
        2016, 12:00.

        Params:
        -------
        days : int
            Number of days.

        Returns:
        --------
        app.plot.plot.TimeBarPlot
            Plot of operation efficiency as a function of the day.
        """

        df = self.df.copy()
        df['OperationEfficiency'] = 100 * np.divide(df.ObsTime, df.ScienceTime)

        start_date, end_date = day_range(self.date, days)
        trend_func = functools.partial(day_running_average, ignore_missing_values=True)

        return daily_bar_plot(df=df,
                              start_date=start_date,
                              end_date=end_date,
                              date_column='Date',
                              y_column='OperationEfficiency',
                              y_range=Range1d(start=0, end=140),
                              trend_func=trend_func,
                              y_formatters=[PrintfTickFormatter(format='%d%%')],
                              **self.kwargs)

    def monthly_plot(self, months):
        """Bar plot displaying the operation efficiency per momth.

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
            Plot of operation efficiency as a function of the month.
        """

        start_date, end_date = month_range(self.date, months)
        trend_func = functools.partial(month_running_average, ignore_missing_values=False)

        def post_binning_func(df):
            df['OperationEfficiency'] = 100 * np.divide(df.ObsTime, df.ScienceTime)

        return monthly_bar_plot(df=self.df,
                                start_date=start_date,
                                end_date=end_date,
                                date_column='Date',
                                month_column='Month',
                                y_column='OperationEfficiency',
                                y_range=Range1d(start=0, end=120),
                                trend_func=trend_func,
                                post_binning_func=post_binning_func,
                                **self.kwargs)

    def semester_to_date_plot(self):
        """Dial plot displaying the operation efficiency for the semester in which `self.date` lies.

        All dates in the semester up to but excluding `self.date` are included when calculating the operation
        efficiency.

        Returns:
        --------
        app.plot.plot.DialPlot
            Plot of the operation efficiency for the semester to date.
        """

        sem = semester(self.date)
        binned_df = bin_by_semester(df=self.df, cutoff_date=self.date, date_column='Date', semester_column='Semester')
        current_semester = binned_df[binned_df.Semester == sem]
        if len(current_semester):
            operation_efficiency = self._observation_efficiency(current_semester.ObsTime[0],
                                                                current_semester.ScienceTime[0])
        else:
            operation_efficiency = 0

        label_color_func = good_mediocre_bad_color_func(good_limit=90, bad_limit=80)

        required_operation_efficiency = required_for_semester_average(date=self.date,
                                                                      average=operation_efficiency,
                                                                      target_average=90)

        return DialPlot(values=[operation_efficiency, required_operation_efficiency],
                        label_values=range(0, 101, 10),
                        label_color_func=label_color_func,
                        display_values=['{:.1f}%'.format(operation_efficiency)],
                        **self.kwargs)

    def _observation_efficiency(self, obs_time, science_time):
        return 100 * obs_time / science_time if science_time else np.NaN
