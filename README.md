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

The configuration files for the Flask server must be included in the `config` folder. Examples are provided for production, development and testing. *Do not put the configuration files under version control.*

Essentially, the following property needs to be defined in each of the configuration files.

| Property | Description | Example |
| -- | -- |
| DEBUG | Run the server in debug mode? |  False |

For security reasons the database URI and secret key are supplied as environment variables rather than being set in the configuration files. This implies that you must set the following environment variables.

| Environment variable | Description | Example |
| -- | -- |
| SALTSTATS_SECRET_KEY | Secret key for encryption in production mode | secretkey42 |
| SALTSTATS_DEV_SECRET_KEY | Secret key for encryption in development mode | anothersecretkey43 |
| SALTSTATS_TEST_SECRET_KEY | Secret key for encryption in testing mode | yetanothersecretkey44 |
| SALTSTATS_DATABASE_URI | Database URI for production mode | mysql://username:password@your.database.server/database |
| SALTSTATS_DEV_DATABASE_URI | Database URI for development mode | mysql://username:password@your.dev.database.server/database |
| SALTSTATS_TEST_DATABASE_URI | Database URI for testing mode | sqlite:////path.to.database.file.sqlite3 |

If you don't use a mode, there is no need to supply the corresponding configuration file or environment variables.

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
| RESTART_HOST_SERVER | Shall command for restarting the server on the production host |
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

In order to run the Flask server, you may activate your virtual environment and launch the server from the command line in the project's root directory.

*Note: Details are likely to change in future!*

```bash
python3 app.py
```

Alternatively, you can run the Python file from an IDE of your choice. The is accessible at the following URL:

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

The following requirements must be met.

* Apache 2 is installed and running.
* `mod_wsgi` must be installed and enabled. *Remember that mod_wsgi must be compiled against the Python compiler you will be using. So if installed with a tool  like apt-get, mod_wsgi presumably won't work with compilers like Anaconda. Also make sure that you install mod_wsgi for the correct version of Python.*
* You must have a virtual environment.

How to set up a virtual environment depends on the operating system and on the version of Python you are using. If you are using Python 3 (which is the formal requirement for this project) on a Mac, it should be as simple as running

```bash
python3 -m venv venv
```

On Ubuntu 14, you'll have to do something like

```bash
apt-get python3-pip
pip3 install virtualenv
python3 -m virtualenv venv
```

You may choose a name other than `venv` for your virtual environment.

The Apache configuration for the statistics page looks as follows.

```apache
<VirtualHost *:80>
WSGIDaemonProcess saltstats python-path=/path/to/project/dist:/path/to/packages/in/venv
WSGIProcessGroup saltstats
WSGIScriptAlias / /var/www/saltstats.cape.saao.ac.za/wsgi.py
WSGIPassAuthorization On
WSGIScriptReloading On

DocumentRoot "/path/to/project/dist"
ServerName your.server.address
WSGIScriptAlias / /path/to/project/wsgi.py
<Directory /path/to/project/>
Order allow,deny
Allow from all
</Directory>

ErrorLog ${APACHE_LOG_DIR}/your.server.address-error.log
CustomLog ${APACHE_LOG_DIR}/your.server.address-access.log combined
</VirtualHost>
```

`/path/to/project/` and `your.server.address` need to be replaced with the correct values, of course. `/path/to/packages/in/venv` must be replaced with the path to the lib directory of the virtual environment you are intending to use. This path will look similar to `/path/to/venv/lib/python3.4/site-packages`.

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

