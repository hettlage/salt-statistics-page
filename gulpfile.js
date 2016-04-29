var argv = require('yargs').argv;
var del = require('del');
var exec = require('child_process').exec;
var fs = require('fs');
var gulp = require('gulp');
var gulpIf = require('gulp-if');
var plumber = require('gulp-plumber');
var rev = require('gulp-rev');
var revReplace = require('gulp-rev-replace');
var rsync = require('rsyncwrapper');
var runSequence = require('run-sequence');
var sass = require('gulp-sass');
var GulpSSH = require('gulp-ssh');
var useref = require('gulp-useref');
var webpack = require('webpack-stream');

var config = require('./gulp.config');

var production = argv.p || argv.production;

config.host = production ? config.HOST : config.DEV_HOST;
config.hostUsername = production ? config.HOST_USERNAME : config.DEV_HOST_USERNAME;
config.hostDir = production ? config.HOST_DIR : config.DEV_HOST_DIR;
config.restartServer = production ? config.RESTART_HOST_SERVER : config.RESTART_DEV_HOST_SERVER;
config.sshPrivateKeyFile = process.env['SSH_PRIVATE_KEY_FILE'];
config.sshPassphrase = process.env['SSH_PASSPHRASE'];


var rootFolders = {
    src: 'src/',
    dist: 'dist/'
};

var subFolders = {
    ts: 'static/ts/',
    js: 'static/js/',
    scss: 'static/scss/',
    css: 'static/css/',
    templates: 'app/templates/'
};

console.log(config.sshPrivateKeyFile);
var gulpSSH = new GulpSSH({
    ignoreErrors: false,
    sshConfig: {
        host: config.host,
        port: 22,
        username: config.hostUsername,
        privateKey: fs.readFileSync(config.sshPrivateKeyFile),
        passphrase: config.sshPassphrase
    }
});

function errorPlumber() {
    return plumber({
        errorHandler: function(err) {
            console.log(err.stack);
            this.emit('end');
        }
                   });
}

function transpileJS(watch, withSourceMaps) {
    var webpackConfig = require('./webpack.config.js');
    webpackConfig.watch = watch;
    if (withSourceMaps) {
        webpackConfig.devtool = 'eval-source-map';
    }
    return gulp.src(rootFolders.src + subFolders.ts + '**/app.ts')
            .pipe(gulpIf(watch, errorPlumber()))
            .pipe(webpack(webpackConfig))
            .pipe(gulp.dest(rootFolders.src + subFolders.js));

}

gulp.task('js:dev', function() {
    return transpileJS(true, true)
});

gulp.task('js:deploy', function() {
    if (!production) {
        return transpileJS(false, true);
    }
    else {
        return transpileJS(false, false);
    }
});

gulp.task('sass', function() {
    return gulp.src(rootFolders.src + subFolders.scss + '**/*.scss')
            .pipe(errorPlumber())
            .pipe(sass())
            .pipe(gulp.dest(rootFolders.src + subFolders.css));
});

gulp.task('css', ['sass'], function() {
    gulp.watch(rootFolders.src + subFolders.scss + '**/*.scss', ['sass']);
});

gulp.task('clean', function() {
    return del.sync([rootFolders.dist + '/**/*',
                        rootFolders.src + subFolders.js + '**/*',
                        rootFolders.src + subFolders.css + '**/*']);
});

gulp.task('clean:rev-manifest', function() {
    del([rootFolders.dist + 'rev-manifest.json']);
});

gulp.task('copy:templates', function() {
    gulp.src(rootFolders.src + subFolders.templates + '**/*')
            .pipe(gulp.dest(rootFolders.dist + subFolders.templates))
});

gulp.task('copy:py', function() {
    gulp.src(rootFolders.src + '**/*.py')
            .pipe(gulp.dest(rootFolders.dist))
});

gulp.task('copy:requirements', function() {
    gulp.src('./requirements.txt')
            .pipe(gulp.dest(rootFolders.dist));
});

gulp.task('copy', function() {
    return runSequence(['copy:py', 'copy:templates', 'copy:requirements']);
});

gulp.task('revision', function() {
    return gulp.src([rootFolders.src + '**/*.js', rootFolders.src + '**/*.css'])
            .pipe(rev())
            .pipe(gulp.dest(rootFolders.dist))
            .pipe(rev.manifest())
            .pipe(gulp.dest(rootFolders.dist));
});

gulp.task('cache-bust', ['revision'], function() {
    var manifest = gulp.src(rootFolders.dist + 'rev-manifest.json');

    return gulp.src(rootFolders.src + subFolders.templates + 'base.html')
            .pipe(revReplace({manifest: manifest}))
            .pipe(gulp.dest(rootFolders.dist + subFolders.templates));
});

gulp.task('serve', function() {
    exec('cd ' + rootFolders.src + '; ' + config.PYTHON + ' app.py',
                     function(error, stdout, stderr) {
                         console.log(stdout);
                         console.log(stderr);
                         if (error !== null) {
                             console.log('exec error: ' + error);
                         }
                     });
});

gulp.task('rsync', function(cb) {
    rsync({
              src: rootFolders.dist,
              dest: config.hostUsername + '@' + config.host + ':' + config.hostDir + '/' + rootFolders.dist,
              recursive: true,
              deleteAll: true
          }, function(err, stdout, stderr) {
        if (err) { console.log(err); }
        if (stdout) { console.log(stdout); }
        if (stderr) { console.log(stderr); }
        cb();
    })
});

gulp.task('restartServer', function() {
    return gulpSSH.shell([config.restartServer]);
});

gulp.task('deploy', function(cb) {
      runSequence('clean',
                // ['js:deploy', 'sass'],
                  'copy',
                  'cache-bust',
                  'clean:rev-manifest',
                  'rsync',
                  'restartServer',
                  cb);
});

gulp.task('default', function() {
    runSequence(['css', 'js:dev', 'serve']);
});
