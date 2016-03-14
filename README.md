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

## Setting up JavaScript

Go to the project's root directory and run the following command.

```bash
npm install
```

## Configuration

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
| PYTHON | Absolute path to the Python 3 command in your virtual environment |

In order to deploy the site, you need to be able to login to the development and production server via an ssh key.  To this end, first generate a public SSH key on your machine (if you don't have one already). See [https://help.github.com/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent/](https://help.github.com/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent/) for an explanation of how to do this.

Then login on the development server (with the user specified in the `DEV_HOST_USERNAME` property) and edit the file `~/.ssh/authorized_keys`, adding the content of the file `~/.ssh/id_rsa.pub` from your machine.

Finally, repeat the last step for the production server.

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

The Apache configuration for the statistics page looks as follows.

```apache
<VirtualHost *:80>
DocumentRoot "/path/to/project/"
ServerName your.server.address
WSGIScriptAlias / /path/to/project/wsgi.py
<Directory /path/to/project/>
Order allow,deny
Allow from all
WSGIPassAuthorization On
WSGIScriptReloading On
</Directory>
</VirtualHost>
```

`/path/to/project/` and `your.server.address` need to be replaced with the correct values, of course.

## Deployment

TBD
