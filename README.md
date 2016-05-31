# SALT statistics page

This project provides a Flask-based website for displaying statistical information about the Southern African Large Telescope (SALT).

## Downloading the code

Make sure Node, npm and Gulp are installed globally on your machine.

Clone this repository into a directory of your choice.

## Setting up Python

Python 3 has to be installed on your machine, which you can check by running

```bash
python3 -v
```

It is highly recommended that you use a virtual environment for running Python. You may create this virtual environment in any directory you like. So cd to a suitable directory and run the following commands.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

On Ubuntu 14, you might have to install pip3 and virtualenv first,

```bash
apt-get python3-pip
pip3 install virtualenv
```

and you create a virtual environment by running

python3 -m virtualenv venv

## Setting up JavaScript

Go to the project's root directory and run the following command.

```bash
npm install
```

## Configuration for the Flask server

The configuration files (`production.py`, `development.py` and `testing.py`) for the Flask server must be included in the `config` folder. Examples are provided for production, development and testing. *Do not put the configuration files under version control.*

Essentially, the following property needs to be defined in each of the configuration files.

| Property | Description | Example |
| -- | -- |
| DEBUG | Run the server in debug mode? |  False |
| SECRET_KEY | Key used by Flask for encryption | top_secret |
| SQLALCHEMY_DATABASE_URI | URI for accessing the database | mysql://username:password@your.database.server/database |
| LDAP_SERVER | LDAP server used for authentication | your.ldap.server |

For security reasons the database URI and secret key should be supplied as environment variables rather than being set in the configuration files. This implies that if you use the provided example configurations, you must set the following environment variables.

| Environment variable | Description | Example |
| -- | -- |
| SALTSTATS_SECRET_KEY | Secret key for encryption in production mode | secretkey42 |
| SALTSTATS_DEV_SECRET_KEY | Secret key for encryption in development mode | anothersecretkey43 |
| SALTSTATS_TEST_SECRET_KEY | Secret key for encryption in testing mode | yetanothersecretkey44 |
| SALTSTATS_DATABASE_URI | Database URI for production mode | mysql://username:password@your.database.server/database |
| SALTSTATS_DEV_DATABASE_URI | Database URI for development mode | mysql://username:password@your.dev.database.server/database |
| SALTSTATS_TEST_DATABASE_URI | Database URI for testing mode | sqlite:////path.to.database.file.sqlite3 |

If you don't use a mode (testing, development or production), there is no need to supply the corresponding configuration file or environment variables.

## Configuration for deployment

In the project's root directory copy the file `gulp.config.example.js` to `gulp.config.js`.

```bash
cp gulp.config.example.js gulp.config.js
```

Edit the configuration file `gulp.config.js` as required. The following table gives an overview of its properties.

| Property | Explanation |
| --- | --- | 
| `HOST` | Address of the production server |
| `DEV_HOST` | Address of the development host |
| `HOST_USERNAME` | Username on the production server. The user must have the permission to make changes in the directory specified by the property `HOST_DIR` |
| `DEV_HOST_USERNAME` | Username on the development server. The user must have the permission to make changes in the directory specified by the property `DEV_HOST_DIR`. |
| HOST_DIR | Absolute path to the project's root directory on the production host |
| DEV_HOST_DIR | Absolute path to the project's root directory on the development host |
| RESTART_HOST_SERVER | Shell command for restarting the server on the production host |
| RESTART_DEV_HOST_SERVER | Shell command for restarting the server on the development host |

In order to deploy the site, you need to be able to login to the development and production server via an ssh key.  To this end, first generate a public SSH key on your machine (if you don't have one already). See [https://help.github.com/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent/](https://help.github.com/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent/) for an explanation of how to do this.

Then login on the development server (with the user specified in the `DEV_HOST_USERNAME` property) and edit the file `~/.ssh/authorized_keys`, adding the content of the file `~/.ssh/id_rsa.pub` from your machine.

Finally, repeat the last step for the production server.

You also need to set two environment variables on your machine.

| Environment variable | Explanation |
| --- | --- |
| SSH_PRIVATE_KEY_FILE | Path to the file containing your private ssh key |
| SSH_PASSPHRASE | Passphrase for accessing your SSH key |

The passphrase is the password you chose when generating your ssh key.

## Parts that are off limits

The following directories should never be edited.

* `static/js`. The files in this directory are generated from the TypeScript files in `static/ts` as well as from the imported npm modules.
* `static/css`. The files in this directory are generated from the SASS files in `static/scss`.
* `dist`. The files in this directory are generated during deployment.

All content in these directories may be deleted when Gulp tasks are executed.

## Running the server during development

You need to set up the configuration files (see the section "Configuration for the Flask server" above), and you need access to the SALT Science Database, or a development copy of it.

In order to run the Flask server, you may activate your virtual environment and launch the server from the command line in the project's root directory.

*Note: Details are likely to change in future!*

```bash
python3 manage.py runserver
```

Alternatively, you can run the Python file from an IDE of your choice. The site then is accessible at the following URL:

http://127.0.0.1:5000/

If you are editing the TypeScript files, you may use the Gulp task `js:dev`.

```bash
gulp js:dev
```

If you are just editing the SASS files, you may use the Gulp task `css`.

```bash
gulp css
```

Of course you still need to launch the Flask server, as described above.

As an alternative, you may use the default Gulp task, which automatically launches the Flask server and keeps the JavaScript and CSS files up to date.

```bash
gulp
```

Either way, you will have to refresh the browser when you have made changes to the source code, and it might take a few seconds before the changes become effective.

## Server configuration

The following outlines how to get the site up-and-running on an Ubuntu 14 server. We assume that the server is called saltstats.cape.saao.ac.za.

First, virtualenv  must be installed for Python 3.

```bash
apt-get python3-pip
pip3 install virtualenv
cd /var/www/saltstats.cape.saao.ac.za
python3 -m virtualenv venv
```

You may choose a name other than `venv` for your virtual environment, but then you'll have to modify the subsequent steps accordingly.

Deploy the site content to the server, as described in the next section, and ensure all the Python requirements are met.

```bash
cd /var/www/saltstats.cape.saao.ac.za
source venv/bin/activate
pip install -r dist/requirements.txt
```

Add a configuration file for launching Tornado whenever the system is booted. To this end, create a file `/etc/init/saltstats-flask.conf` with the following content.

```
description "Tornado application server running Flask for saltstats.cape.saao.ac.za"

start on runlevel [2345]
stop on runlevel [!2345]

respawn
setuid www-data
setgid www-data

env SALTSTATS_FLASK_CONFIG=production
env SALTSTATS_SECRET_KEY='some-secret-key'
env SALTSTATS_DATABASE_URI='mysql://piptquerytool:password@devsdb.cape.saao.ac.za/sdb_copy'

script
    cd /var/www/saltstats.cape.saao.ac.za/dist
    /var/www/saltstats.cape.saao.ac.za/venv/bin/python tornado_server.py
end script
```

If the server doesn't start after rebooting, you should check whether an error has been logged in `/var/log/upstart/saltstats-flask.log`.

Reboot the server.

```bash
reboot
```

Try whether the Tornado server is up-and-running.

```bash
wget -O - http://127.0.0.1:8000
```

Install nginx.

```bash
apt-get install nginx
```

On Ubuntu, you should add the configuration file in the folder `/etc/nginx/sites-available/`, and it should have the following content.

```
upstream tornado_app {
    server 127.0.0.1:8000;
}

server {
    listen *:80;
    server_name your.server.address;

    access_log  /var/log/nginx/access.log;
    error_log  /var/log/nginx/error.log;

    location / {
        try_files $uri @tornado;
    }

    location @tornado {
        proxy_pass http://tornado_app;
        proxy_redirect off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

You can then enable the configuration,

```bash
ln -s /etc/nginx/sites-available/saltstats.cape.saao.ac.za.conf /etc/nginx/sites-enabled/saltstats.cape.saao.ac.za.conf

and restart the server.

```bash
service nginx restart
```

On a non-Ubuntu system you might have to provide the full configuration file for nginx:

```
events {
}

http {
    ... configuration content as for Ubuntu ...
}
```

## Deployment

In order to deploy to the development server, run

```bash
gulp deploy
```

In order to deploy to the production server, run

```bash
gulp deploy --production
```

or just

```bash
gulp deploy -p
```

Apache will automatically be restarted on the server. However, the required Python libraries aren't installed. So if necessary you should login to the server, go the root directory of the deployed project and run

```bash
source venv/bin/activate
pip install -r dist/requirements.txt
```

You have to modify the first line if your virtual environment isn't located in your project's root directory or if it has a name other than venv.

## Adding a new plot

*This is going to change.*

Create a class extending the class `app.plot.plot.Plot`.  This class inherits `self.plot`, which is a Bokeh Figure instance. You have to add all your plot content to this field.

```python
from app.plot.plot import Plot

class MyNewPlot(Plot):
    def __init__(self, **kwargs):
        Plot.__init__(self, **kwargs)

        x = [1, 2, 3]
        y = [2, 4, 6]
        self.plot.line(x, y)
```

Go to the `home` function in `app/main/views.py`, create an instance of your plot class and assign it to a variable (`my_new_plot`, say).

```python
my_new_plot = MyNewPlot()
```

Pass this as a named argument to the `render_template` method.

```python
render_template('dashboard.html',
                             my_new_plot=my_new_plot,
                             ...)
 ```
 
 Add the following to the file `app/templates/dashboard.html` wherte you want the plot to be displayed.
 
 ```
 {{ my_new_plot | safe }}
 ```
 
 The dashboard page should now show your plot.