import datetime

from bokeh.models import Range1d
from bokeh.models.formatters import DatetimeTickFormatter
from flask.ext.login import login_required
from flask import render_template
import numpy as np
import pandas as pd

from ..main import main
from ..plot.plot import TimeBarPlot


@main.route('/', methods=['GET'])
@login_required
def home():
    from_date = datetime.datetime(2016, 4, 1, 12, 0, 0, 0)
    to_date = from_date + datetime.timedelta(days=30)
    dx = datetime.timedelta(days=1)
    x = np.array([from_date + i * dx for i in range(0, 31)])
    to_date = x[-1]
    y = 100000 * np.random.random(len(x))
    alt_y = np.random.random(len(x))
    df = pd.DataFrame(dict(x=x, y=y, alt_y=alt_y))
    f = DatetimeTickFormatter(formats=dict(hours=['%d'], days=['%d'], months=['%d'], years=['%d']))
    p = TimeBarPlot(df=df,
                    dx=dx,
                    x_range=Range1d(from_date - 0.5 * dx, to_date + 0.5 * dx),
                    y_range=Range1d(0, 100000),
                    date_formatter=f,
                    alt_y_range=Range1d(0, 2),
                    width=1200)

    return render_template('dummy.html', dummy=p)