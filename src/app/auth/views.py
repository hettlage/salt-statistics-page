from flask import current_app, flash, redirect, render_template, request, url_for
from flask.ext.login import login_required, login_user, logout_user
from ldap3 import Server, Connection, SUBTREE
from ldap3.core.exceptions import LDAPBindError

from . import auth
from .forms import LoginForm
from .user import User


def find_user(username, password):
    """Query the LDAP server for the user with the given user credentials. The username, first name
    and surname are returned as a dictionary with the keys :code:`username`, :code:`first_name` and
    :code:`surname`.

    If the user doesn't exist (or the password is wrong), :code:`None` is returned.
    """

    server = Server(current_app.config['LDAP_SERVER'])
    try:
        conn = Connection(server, 'uid={0}, ou=people, dc=saao'.format(username), password, auto_bind=True)
        results = conn.extend.standard.paged_search(search_base='dc=saao',
                                                    search_scope=SUBTREE,
                                                    search_filter='(uid={0})'.format(username),
                                                    attributes=['givenName', 'sn'],
                                                    generator=False)
        # TO DO: store user in database, so that load_user can use it
        return User()
        # return User(username=username,
        #             first_name=results[0]['attributes']['givenName'][0],
        #             surname=results[0]['attributes']['surname'][0])
    except LDAPBindError:
        return None


    #
    # auth_method = current_app.config['AUTH_METHOD']
    #
    # # LDAP
    # if auth_method == 'LDAP':
    #     conn = ldap.initialize(current_app.config['LDAP_URI'])
    #     try:
    #         conn.simple_bind_s("uid=%s,ou=people,dc=saao" % username, password)
    #         result = conn.search_s("dc=saao", ldap.SCOPE_SUBTREE, '(uid=%s)' % username)[0][1]
    #         return {
    #             'username': result['uid'][0],
    #             'first_name': result['givenName'][0],
    #             'surname': result['sn'][0]
    #         }
    #     except Exception:
    #         return None
    #
    # # no authentication
    # elif auth_method == 'None':
    #     return {
    #         'username': 'guest',
    #         'first_name': 'Guest',
    #         'surname': 'Guest'
    #     }


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = find_user(form.username.data, form.password.data)
        if user:
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.home'))
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
