import datetime

from flask import flash, redirect, render_template, url_for
from flask.ext.login import login_required
from flask.ext.wtf import Form
from wtforms import FileField, SubmitField
from wtforms.validators import DataRequired

from ..main import main
from ..plot.block_visits import BlockVisitPlots
from ..plot.engineering_time import EngineeringTimePlots
from ..plot.operation_efficiency import OperationEfficiencyPlots
from ..plot.science_time import ScienceTimePlots
from ..plot.shutter_open_efficiency import ShutterOpenEfficiencyPlots
from ..plot.telescope_downtime import TelescopeDowntimePlots
from ..plot.weather_downtime import WeatherDowntimePlots

from ..plot.mirror_recoating import MirrorRecoatingPlot, update_database


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


class RecoatingForm(Form):
    data_file = FileField('Excel spreadsheet', validators=[DataRequired()])
    submit = SubmitField('Update Database')


@main.route('/recoating', methods=['GET', 'POST'])
@login_required
def mirror_recoating():
    """View for a mirror recoating plot, as well as a file upload form for updating the database.
    """

    form = RecoatingForm()
    if form.validate_on_submit():
        file = form.data_file.data
        form.data_file.data = None
        try:
            update_database(file)
        except BaseException as e:
            flash('The database could not be updated: {message}'.format(message=e))
        return redirect(url_for('main.mirror_recoating'))

    now = datetime.date(2016, 4, 15) # datetime.datetime.now().date()
    mirror_recoating = MirrorRecoatingPlot(now)

    return render_template('recoating.html', mirror_recoating=mirror_recoating, form=form)

