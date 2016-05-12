import datetime

from bokeh.models import Range1d
from bokeh.models.formatters import DatetimeTickFormatter
from flask.ext.login import login_required
from flask import render_template
import numpy as np
import pandas as pd

from ..main import main
from ..plot.block_visits import BlockVisitPlots
from ..plot.plot import TimeBarPlot, DialPlot


@main.route('/', methods=['GET'])
@login_required
def home():
    # dp = DialPlot(values=[15, 24],
    #               label_values=[0, 10, 20, 30],
    #               label_color_func=lambda x : 'green' if x < 20 else 'red',
    #               display_values=['15 %', '456'])
    # return render_template('dummy.html', db=dp)

    bp = BlockVisitPlots(datetime.date(2016, 4, 4))
    plot = bp.monthly_plot(months=6)
    return render_template('dummy.html', db=bp.daily_plot(31), mb=plot)
