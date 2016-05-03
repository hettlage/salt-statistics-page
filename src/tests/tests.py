import datetime
import unittest

from dateutil import parser
import numpy as np
import pandas as pd

from app.plot.util import bin_by_date, bin_by_month, bin_by_semester


class TestPlot(unittest.TestCase):
    def test_bin_by_day(self):
        dates = [parser.parse('2015-12-31 11:17:00'),
                 parser.parse('2015-12-31 22:17:00'),
                 parser.parse('2016-01-01 0:00:00'),
                 parser.parse('2016-01-01 08:00:00'),
                 datetime.date(2016, 1, 1),
                 parser.parse('2016-01-04 23:59:59'),
                 parser.parse('2016-03-05 17:21:57'),
                 parser.parse('2016-04-15 01:02:03'),
                 parser.parse('2016-04-15 11:59:59'),
                 parser.parse('2030-04-30 23:02:03')]
        df = pd.DataFrame(dict(dates=dates,
                               a=[i for i in range(0, len(dates))],
                               b=[2 * i for i in range(0, len(dates))]))

        def day(d):
            return '{0}-{1}-{2}'.format(d.year, d.month, d.day)

        # default aggregation function
        binned = bin_by_date(df, date_column='dates')
        self.assertEqual(6, len(binned['dates']))
        self.assertEqual('2015-12-31', day(binned['dates'].iloc[0]))
        self.assertEqual('2016-1-1', day(binned['dates'].iloc[1]))
        self.assertEqual('2016-1-4', day(binned['dates'].iloc[2]))
        self.assertEqual('2016-3-5', day(binned['dates'].iloc[3]))
        self.assertEqual('2016-4-15', day(binned['dates'].iloc[4]))
        self.assertEqual('2030-4-30', day(binned['dates'].iloc[5]))
        self.assertEqual([1, 9, 5, 6, 15, 9], binned['a'].values.tolist())
        self.assertEqual([2, 18, 10, 12, 30, 18], binned['b'].values.tolist())

        # np.sum as aggregation function
        binned = bin_by_date(df, agg_func=np.sum, date_column='dates')
        self.assertEqual(6, len(binned['dates']))
        self.assertEqual('2015-12-31', day(binned['dates'].iloc[0]))
        self.assertEqual('2016-1-1', day(binned['dates'].iloc[1]))
        self.assertEqual('2016-1-4', day(binned['dates'].iloc[2]))
        self.assertEqual('2016-3-5', day(binned['dates'].iloc[3]))
        self.assertEqual('2016-4-15', day(binned['dates'].iloc[4]))
        self.assertEqual('2030-4-30', day(binned['dates'].iloc[5]))
        self.assertEqual([1, 9, 5, 6, 15, 9], binned['a'].values.tolist())
        self.assertEqual([2, 18, 10, 12, 30, 18], binned['b'].values.tolist())

        # np.mean as aggregation function
        binned = bin_by_date(df, agg_func=np.mean, date_column='dates')
        self.assertEqual(6, len(binned['dates']))
        self.assertEqual('2015-12-31', day(binned['dates'].iloc[0]))
        self.assertEqual('2016-1-1', day(binned['dates'].iloc[1]))
        self.assertEqual('2016-1-4', day(binned['dates'].iloc[2]))
        self.assertEqual('2016-3-5', day(binned['dates'].iloc[3]))
        self.assertEqual('2016-4-15', day(binned['dates'].iloc[4]))
        self.assertEqual('2030-4-30', day(binned['dates'].iloc[5]))
        self.assertEqual([0.5, 3, 5, 6, 7.5, 9], binned['a'].values.tolist())
        self.assertEqual([1, 6, 10, 12, 15, 18], binned['b'].values.tolist())

    def test_bin_by_month(self):
        dates = [parser.parse('2016-01-01 0:00:00'),
                 parser.parse('2016-01-02 12:00:00'),
                 parser.parse('2016-01-30 02:00:00'),
                 parser.parse('2016-01-31 23:59:59'),
                 datetime.date(2016, 3, 5),
                 parser.parse('2016-04-15 01:02:03'),
                 parser.parse('2016-04-28 22:14:57'),
                 parser.parse('2030-04-30 23:02:03')]
        df = pd.DataFrame(dict(dates=dates,
                               a=[i for i in range(0, len(dates))],
                               b=[2 * i for i in range(0, len(dates))]))

        def year_and_month(d):
            return '{0}-{1}'.format(d.year, d.month)

        # default aggregation function
        binned = bin_by_month(df, date_column='dates', month_column='months')
        self.assertEqual(4, len(binned['months']))
        self.assertEqual('2016-1', year_and_month(binned['months'].iloc[0]))
        self.assertEqual('2016-3', year_and_month(binned['months'].iloc[1]))
        self.assertEqual('2016-4', year_and_month(binned['months'].iloc[2]))
        self.assertEqual('2030-4', year_and_month(binned['months'].iloc[3]))
        self.assertEqual([6, 4, 11, 7], binned['a'].values.tolist())
        self.assertEqual([12, 8, 22, 14], binned['b'].values.tolist())

        # np.sum as aggregation function
        binned = bin_by_month(df, agg_func=np.sum, date_column='dates', month_column='months')
        self.assertEqual(4, len(binned['months']))
        self.assertEqual('2016-1', year_and_month(binned['months'].iloc[0]))
        self.assertEqual('2016-3', year_and_month(binned['months'].iloc[1]))
        self.assertEqual('2016-4', year_and_month(binned['months'].iloc[2]))
        self.assertEqual('2030-4', year_and_month(binned['months'].iloc[3]))
        self.assertEqual([6, 4, 11, 7], binned['a'].values.tolist())
        self.assertEqual([12, 8, 22, 14], binned['b'].values.tolist())

        # np.mean as aggregation function
        binned = bin_by_month(df, agg_func=np.mean, date_column='dates', month_column='months')
        self.assertEqual(4, len(binned['months']))
        self.assertEqual('2016-1', year_and_month(binned['months'].iloc[0]))
        self.assertEqual('2016-3', year_and_month(binned['months'].iloc[1]))
        self.assertEqual('2016-4', year_and_month(binned['months'].iloc[2]))
        self.assertEqual('2030-4', year_and_month(binned['months'].iloc[3]))
        self.assertEqual([1.5, 4, 5.5, 7], binned['a'].values.tolist())
        self.assertEqual([3, 8, 11, 14], binned['b'].values.tolist())

    def test_bin_by_semester(self):
        dates = [parser.parse('2015-10-31 23:59:59'),
                 parser.parse('2015-11-01 0:00:00'),
                 parser.parse('2015-12-31 23:59:59'),
                 parser.parse('2016-01-01 0:00:00'),
                 parser.parse('2016-03-23 13:00:00'),
                 parser.parse('2016-04-30 23:59:59'),
                 parser.parse('2016-05-01 0:00:00'),
                 parser.parse('2016-08-23 04:05:06'),
                 parser.parse('2016-10-31 23:59:59'),
                 parser.parse('2016-11-01 0:00:00'),
                 parser.parse('2023-05-01 0:00:00')]
        df = pd.DataFrame(dict(dates=dates,
                               a=[i for i in range(0, len(dates))],
                               b=[2 * i for i in range(0, len(dates))]))

        # default aggregation function
        binned = bin_by_semester(df, date_column='dates', semester_column='semesters')
        self.assertEqual(5, len(binned['semesters']))
        self.assertEqual('2015-1', binned['semesters'].iloc[0])
        self.assertEqual('2015-2', binned['semesters'].iloc[1])
        self.assertEqual('2016-1', binned['semesters'].iloc[2])
        self.assertEqual('2016-2', binned['semesters'].iloc[3])
        self.assertEqual('2023-1', binned['semesters'].iloc[4])
        self.assertEqual([0, 15, 21, 9, 10], binned['a'].values.tolist())
        self.assertEqual([0, 30, 42, 18, 20], binned['b'].values.tolist())

        # np.sum as aggregation function
        binned = bin_by_semester(df, agg_func=np.sum, date_column='dates', semester_column='semesters')
        self.assertEqual(5, len(binned['semesters']))
        self.assertEqual('2015-1', binned['semesters'].iloc[0])
        self.assertEqual('2015-2', binned['semesters'].iloc[1])
        self.assertEqual('2016-1', binned['semesters'].iloc[2])
        self.assertEqual('2016-2', binned['semesters'].iloc[3])
        self.assertEqual('2023-1', binned['semesters'].iloc[4])
        self.assertEqual([0, 15, 21, 9, 10], binned['a'].values.tolist())
        self.assertEqual([0, 30, 42, 18, 20], binned['b'].values.tolist())

        # np.mean aggregation function
        binned = bin_by_semester(df, agg_func=np.mean,  date_column='dates', semester_column='semesters')
        self.assertEqual(5, len(binned['semesters']))
        self.assertEqual('2015-1', binned['semesters'].iloc[0])
        self.assertEqual('2015-2', binned['semesters'].iloc[1])
        self.assertEqual('2016-1', binned['semesters'].iloc[2])
        self.assertEqual('2016-2', binned['semesters'].iloc[3])
        self.assertEqual('2023-1', binned['semesters'].iloc[4])
        self.assertEqual([0, 3, 7, 9, 10], binned['a'].values.tolist())
        self.assertEqual([0, 6, 14, 18, 20], binned['b'].values.tolist())
