from flask import render_template

from ..main import main
from ..plot.plot import DummyPlot

@main.route('/', methods=['GET'])
def home():
    p = DummyPlot()
    return render_template('dummy.html', dummy=p)