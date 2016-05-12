import datetime
import functools
import numpy as np
import pandas as pd

from bokeh.models import Range1d
from app import db
from app.plot.plot import DialPlot
from app.plot.util import daily_bar_plot, day_range, day_running_average, filter_week_to_date, filter_day_before_date,\
                          monthly_bar_plot, month_range, month_running_average
from app.util import SCIENCE_PROPOSAL_TYPES


class BlockVisitPlots:
    """Plots displaying the number of block visits.

    Params:
    -------
    date : datetime.date
        The date for which to generate the plots.
    """

    def __init__(self, date):
        self.date = date
        start = self.date - datetime.timedelta(days=300)
        end = self.date + datetime.timedelta(days=150)

        sql = """SELECT ni.Date AS Date,
        COUNT(BlockVisit_Id) AS BlockCount
    FROM NightInfo AS ni
    JOIN BlockVisit AS bv USING (NightInfo_Id)
    JOIN Block AS b USING (Block_Id)
    JOIN Proposal AS p USING (Proposal_Id)
    JOIN ProposalType AS pt USING (ProposalType_Id)
    WHERE bv.Accepted=1
    AND pt.ProposalType IN {proposal_types}
    AND (ni.Date BETWEEN DATE('{start_date}') AND DATE('{end_date}'))
    GROUP BY DATE
       """.format(proposal_types=SCIENCE_PROPOSAL_TYPES,
                  start_date=start.strftime('%Y-%m-%d'),
                  end_date=end.strftime('%Y-%m-%d'))
        self.df = pd.read_sql(sql, db.engine)

    def last_night_plot(self):
        """Dial plot displaying the number of block visits for last night."""

        last_night = filter_day_before_date(self.df, self.date, 'Date')
        block_visits = np.sum(last_night.BlockCount)

        return DialPlot(values=[block_visits],
                        label_values=range(0, 13),
                        label_color_func=lambda d: '#7f7f7f',
                        display_values=[str(block_visits)])

    def week_to_date_plot(self):
        """Dial plot displaying the number of block visits in the last week."""

        week_to_date = filter_week_to_date(self.df, self.date, 'Date')
        block_visits = np.sum(week_to_date.BlockCount)

        return DialPlot(values=[block_visits],
                        label_values=range(0, 71, 10),
                        label_color_func=lambda d: '#7f7f7f',
                        display_values=[str(block_visits)])

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

        return daily_bar_plot(df=self.df,
                              start_date=start_date,
                              end_date=end_date,
                              date_column='Date',
                              y_column='BlockCount',
                              y_range=Range1d(start=0, end=30),
                              trend_func=trend_func)

    def monthly_plot(self, months):
        """Bar plot displaying the number of block visits per momth.

        The number of block visits is shown for the `months` months leading to but excluding the month containing
        `self.date`. A month here refers start at noon of the first of the month. For May 2016 refers to the period from
        1 May 2016, 12:00 to 1 June 2016, 12:00.

        Params:
        -------
        months : int
            Number of months.

        Returns:
        --------
        app.plot.plot.TimeBarPlot
            Plot of number of block visits as a function of the month.
        """

        start_date, end_date = month_range(self.date, months)
        trend_func = functools.partial(month_running_average, ignore_missing_values=False)
        return monthly_bar_plot(df=self.df,
                                start_date=start_date,
                                end_date=end_date,
                                date_column='Date',
                                month_column='Month',
                                y_column='BlockCount',
                                y_range=Range1d(start=0, end=300),
                                trend_func=trend_func)
