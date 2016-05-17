import datetime
import pandas as pd

from app.util import SCIENCE_PROPOSAL_TYPES


class DateRangeQueries:
    """Statistics queries for a range of dates.

    All the queries return a data frame which contains the queried data for each date between (and including) `start` and
    `end`.

    You need to supply a SQLAlchemny database connection/engine or a database URI. If you are using Flask, the easiest
    might be to use a Flask-SQLAlchemy instance `db` and to pass `db.engine`.

    Params:
    -------
    start: datetime.Date
        First date to include in the query results.
    end: datetime.Date
        Last date to include in the query results.
    con: SQLAlchemy connectable(engine/connection) or database string URI
        Database connection to use for the queries.
    """

    def __init__(self, start, end, con):
        if start >= end:
            raise ValueError('The start date ({start}) must be earlier than the end date ({end}).'
                             .format(start=start, end=end))

        self.start = start
        self.end = end
        self.con = con

    def observation_time(self):
        """Get the observation time for a range of dates.

        The data is given per date. A date refers to the night starting on the date. For example, the 22 May 2016 refers
        to the periods from 22 May 2016, 12:00 to 23 May 2016, 12:00.

        A data frame with the following columns is returned.

        - Date: Date when the night starts.
        - ObsTime: Observation time. This is the sum of the time required (as calculated by the PIPT) for all accepted
          block visits accomplished during the night for science (and science verification) proposals. Commissioning and
          engineering proposals aren't included. Blocks are included even if they are observed before end of evening
          twilight or after start of morning twilight.

        Returns:
        --------
        pandas.DataFrame
            The observation times.
        """

        sql = """SELECT ni.Date AS Date,
                            SUM(b.ObsTime) AS ObsTime
                     FROM NightInfo AS ni
                     JOIN BlockVisit AS bv USING (NightInfo_Id)
                     JOIN Block AS b USING (Block_Id)
                     JOIN Proposal AS p USING (Proposal_Id)
                     JOIN ProposalType AS pt USING (ProposalType_Id)
                     WHERE bv.Accepted = 1
                           AND pt.ProposalType IN {proposal_types}
                           AND (ni.Date BETWEEN DATE('{start_date}') AND DATE('{end_date}'))
                     GROUP BY ni.NightInfo_Id
                     ORDER BY ni.Date""" \
            .format(proposal_types=SCIENCE_PROPOSAL_TYPES,
                    start_date=self.start.strftime('%Y-%m-%d'),
                    end_date=self.end.strftime('%Y-%m-%d'))

        return pd.read_sql(sql, self.con)

    def time_breakdown(self):
        """Get the time breakdown for a range of dates.

        The data is given per date. A date refers to the night starting on the date. For example, the 22 May 2016 refers
        to the periods from 22 May 2016, 12:00 to 23 May 2016, 12:00.

        A data frame with the following columns is returned.

        - Date: Date when the night starts.
        - TimeLostToWeather: Time (in seconds) lost due to bad weather.
        - TimeLostToProblems: Time (in seconds) lost due to technical or operational issues.
        - EngineeringTime: Time (in seconds) spent on engineering work.
        - ScienceTime: Time (in seconds) spent on science observations.
        - NightLength: The length of the night (in seconds), i.e. the time between end of evening twilight and start of
          morning twilight.

        All times are limited to the period between end of evening twilight and start of morning twilight.

        Params:
        -------
        start: datetime.Date
            First date to include in the query results.
        end: datetime.Date
            Last date to include in the query results.

        Returns:
        --------
        pandas.DataFrame
            The time breakdown.
        """

        sql = """SELECT ni.Date AS Date,
                            ni.TimeLostToWeather AS TimeLostToWeather,
                            ni.TimeLostToProblems AS TimeLostToProblems,
                            ni.EngineeringTime AS EngineeringTime,
                            ni.ScienceTime AS ScienceTime,
                            TIMESTAMPDIFF(SECOND, ni.EveningTwilightEnd, ni.MorningTwilightStart) AS NightLength
                     FROM NightInfo AS ni
                     WHERE ni.Date BETWEEN DATE('{start_date}') AND DATE('{end_date}')
                     ORDER BY ni.Date""" \
            .format(start_date=self.start.strftime('%Y-%m-%d'),
                    end_date=self.end.strftime('%Y-%m-%d'))

        return pd.read_sql(sql, self.con)

    def subsystem_loss_breakdown(self):
        """Get the subsystem breakdown of lost time for a range of dates.

        The data is given per date. A date refers to the night starting on the date. For example, the 22 May 2016 refers
        to the periods from 22 May 2016, 12:00 to 23 May 2016, 12:00.

        A data frame with the following columns is returned.

        - Date: Date when the night starts.
        - SaltSubsystem: Subsystem causing the loss of time.
        - TimeLost: Time (in seconds) lost due to problems with the subsystem.

        Params:
        -------
        start: datetime.Date
            First date to include in the query results.
        end: datetime.Date
            Last date to include in the query results.

        Returns:
        --------
        pandas.DataFrame
            The subsystem breakdown of lost time.
        """

        sql = """SELECT ni.Date AS Date,
                            s.SaltSubsystem AS SaltSubsystem,
                            SUM(TimeLost) as "Time"
                            FROM Fault AS f
                            JOIN NightInfo AS ni USING (NightInfo_Id)
                            JOIN SaltSubsystem AS s USING (SaltSubsystem_Id)
                            WHERE f.Deleted=0 AND Timelost IS NOT NULL
                                  AND (ni.Date BETWEEN DATE('{start_date}') AND DATE('{end_date}'))
                            GROUP BY ni.Date, s.SaltSubsystem""" \
            .format(start_date=self.start.strftime('%Y-%m-%d'),
                    end_date=self.end.strftime('%Y-%m-%d'))

        return pd.read_sql(sql, self.con)

    def shutter_open_time(self):
        """Get the shutter open time for a range of dates.

        The data is given per date. A date refers to the night starting on the date. For example, the 22 May 2016 refers
        to the periods from 22 May 2016, 12:00 to 23 May 2016, 12:00.

        A data frame with the following columns is returned.

        - Date: Date when the night starts.
        - ShutterOpenTime: The exposure time (in seconds) spent on science (including science verification) and
          commissioning proposals. Exposure times are included even if the observations are done before end of evening
          twilight or after start of morning twilight.

        Returns:
        --------
        pandas.DataFrame:
            The shutter open time.
        """

        sql = """SELECT DATE(DATE_SUB(UTStart, INTERVAL 12 HOUR)) AS Date,
                            SUM(NExposures*ExposureTime) AS ShutterOpenTime
                            FROM FileData AS fd
                            JOIN ProposalCode AS pc using (ProposalCode_Id)
                            JOIN FitsHeaderImage AS fhi using (FileData_Id)
                            WHERE (fd.UTStart >= '{start_date} 12:00:00' AND fd.UTStart <= '{end_date} 12:00:00')
                                  AND (fd.FileName LIKE 'S%%'
                                      OR fd.FileName LIKE 'P%%'
                                      OR fd.FileName LIKE 'H%%fits')
                                  AND (pc.Proposal_Code like '%%SCI%%'
                                      OR pc.Proposal_Code like '%%MLT%%'
                                      OR pc.Proposal_Code like '%%DDT%%'
                                      OR pc.Proposal_Code like '%%COM%%'
                                      OR pc.Proposal_Code LIKE '%%SVP%%')
                                  AND (fhi.OBSTYPE='OBJECT' OR fhi.OBSTYPE='SCIENCE')
                            GROUP BY Date""" \
            .format(start_date=self.start.strftime('%Y-%m-%d'),
                    end_date=(self.end + datetime.timedelta(days=1)).strftime('%Y-%m-%d'))

        return pd.read_sql(sql, self.con)

    def block_visits(self):
        """Get the number of accepted block visits for a range of dates.

        The data is given per date. A date refers to the night starting on the date. For example, the 22 May 2016 refers
        to the periods from 22 May 2016, 12:00 to 23 May 2016, 12:00.

        A data frame with the following columns is returned.

        - Date: Date when the night starts.
        - BlockCount: Number of block visits.

        Returns:
        --------
        pandas.DataFrame
            The number of block visits.
        """

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
        GROUP BY DATE""" \
            .format(proposal_types=SCIENCE_PROPOSAL_TYPES,
                      start_date=self.start.strftime('%Y-%m-%d'),
                      end_date=self.end.strftime('%Y-%m-%d'))

        return pd.read_sql(sql, self.con)

    def publications(self):
        """Get the number of publications for a range of dates.

        The number of publications is given per month. `self.start` and `self.end` are assumed to be dates in the first
        and last month to include in the query.

        A data frame with the following columns is returned.

        - Year: Year.
        - Month: Month.
        - Publications: Number of publications.

        Returns:
        --------
        pandas.DataFrame
            The number of publications.
        """

        sql = """SELECT Year, Month, Publications
                 FROM Publications
                 WHERE ({start_year}<Year OR ({start_year}=Year AND {start_month}<=Month))
                       AND ({end_year}>Year OR ({end_year}=YEAR AND {end_month}>=Month))""" \
             .format(start_year=self.start.year,
                     start_month=self.start.month,
                     end_year=self.end.year,
                     end_month=self.end.month)

        return pd.read_sql(sql, self.con)

    def coated_segments(self):
        """Get the dates when mirror segments were coated.

        A data frame with the following columns is returned:

        - Segment: Number of the segment.
        - Date: Date when the segment was coated.

        Returns:
        --------
        pandas.DataFrame
            The dates.
        """

        sql = """SELECT Segment, Date
                 FROM SegmentCoating
                 WHERE Date BETWEEN DATE('{start_date}') AND DATE('{end_date}')""" \
             .format(start_date=self.start,
                     end_date=self.end)

        return pd.read_sql(sql, self.con)