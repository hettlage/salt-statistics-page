import datetime
import math
import pandas as pd

from bokeh.models import Range1d
from bokeh.models.formatters import DatetimeTickFormatter
from .plot import TimeBarPlot
from .util import bin_by_month, daily_bar_plot, monthly_bar_plot
from .. import db
from ..util import SCIENCE_PROPOSAL_TYPES


class BlocksPlots:
    def __init__(self, night):
        self.night = night
        start = self.night - datetime.timedelta(days=200)
        end = self.night + datetime.timedelta(days=150)

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
        print(self.df)

    def daily_plot(self):
        return daily_bar_plot(df=self.df,
                              night=self.night,
                              date_column='Date',
                              y_column='BlockCount',
                              y_range=Range1d(start=0, end=30))


    def monthly_plot(self):
        return monthly_bar_plot(df=self.df,
                                night=self.night,
                                date_column='Date',
                                month_column='Month',
                                y_column='BlockCount',
                                y_range=Range1d(start=0, end=300))
