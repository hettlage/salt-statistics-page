var exec = require('child_process').exec;
var del = require('del');
var gulp = require('gulp');
var gulpIf = require('gulp-if');
var plumber = require('gulp-plumber');
var rev = require('gulp-rev');
var revReplace = require('gulp-rev-replace');
var sass = require('gulp-sass');
var useref = require('gulp-useref');
var runSequence = require('run-sequence');
var webpack = require('webpack-stream');

var config = require('./gulp.config');

var rootFolders = {
    src: 'src/',
    dist: 'dist/'
};
var subFolders = {
    ts: 'static/ts/',
    js: 'static/js/',
    scss: 'static/scss/',
    css: 'static/css/',
    templates: 'templates/'
};

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

gulp.task('js:deploy:dev', function() {
    return transpileJS(false, true);
});

gulp.task('js:deploy:production', function() {
    return transpileJS(false, false);
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

gulp.task('copy:js', function() {
    gulp.src(rootFolders.src + subFolders.js + '**/*.js')
            .pipe(gulp.dest(rootFolders.dist + subFolders.js));
});

gulp.task('copy:css', function() {
    gulp.src(rootFolders.src + subFolders.css + '**/*.css')
            .pipe(gulp.dest(rootFolders.dist + subFolders.css));
});

gulp.task('copy:templates', function() {
    gulp.src(rootFolders.src + subFolders.templates + '**/*')
            .pipe(gulp.dest(rootFolders.dist + subFolders.templates))
});

gulp.task('copy:py', function() {
    gulp.src(rootFolders.src + '**/*.py')
            .pipe(gulp.dest(rootFolders.dist))
});

gulp.task('copy', function() {
    return runSequence(['copy:js', 'copy:css', 'copy:py', 'copy:templates']);
});

gulp.task('revision', function() {
    return gulp.src([rootFolders.dist + subFolders.js + '**/*.js', rootFolders.dist + subFolders.css + '**/*.css'])
            .pipe(rev())
            .pipe(gulp.dest(rootFolders.dist))
            .pipe(rev.manifest())
            .pipe(gulp.dest(rootFolders.dist));
});

gulp.task('cache-bust', ['revision'], function() {
    var manifest = gulp.src("./dist/rev-manifest.json");

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

gulp.task('deploy:dev', function() {
    return runSequence('clean',
                       ['js:deploy:dev', 'css'],
                       'copy',
                       'cache-bust');
});

gulp.task('default', function() {
    runSequence(['css', 'js:dev', 'serve']);
});
