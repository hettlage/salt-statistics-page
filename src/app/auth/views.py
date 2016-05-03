from flask import flash, redirect, render_template, request, url_for
from flask.ext.login import login_required, login_user, logout_user

from . import auth
from .forms import LoginForm
from .user import User


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User()
        if form.username.data == 'root' and form.password.data == 'secret':
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.home'))
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
