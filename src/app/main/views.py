import datetime

from flask.ext.login import login_required
from flask import render_template

from ..main import main
from ..plot.block_visits import BlockVisitPlots
from ..plot.engineering_time import EngineeringTimePlots
from ..plot.operation_efficiency import OperationEfficiencyPlots
from ..plot.science_time import ScienceTimePlots
from ..plot.shutter_open_efficiency import ShutterOpenEfficiencyPlots
from ..plot.telescope_downtime import TelescopeDowntimePlots
from ..plot.weather_downtime import WeatherDowntimePlots


@main.route('/', methods=['GET'])
@login_required
def home():
    date = datetime.date(2016, 3, 29)

    block_visits = BlockVisitPlots(date)
    science_time = ScienceTimePlots(date)
    weather_downtime = WeatherDowntimePlots(date)
    telescope_downtime = TelescopeDowntimePlots(date)
    engineering_time = EngineeringTimePlots(date)
    shutter_open_efficiency = ShutterOpenEfficiencyPlots(date)
    operation_efficiency = OperationEfficiencyPlots(date)

    return render_template('dashboard.html',
                           block_visits=block_visits,
                           science_time=science_time,
                           weather_downtime=weather_downtime,
                           telescope_downtime=telescope_downtime,
                           engineering_time=engineering_time,
                           shutter_open_efficiency=shutter_open_efficiency,
                           operation_efficiency=operation_efficiency)
