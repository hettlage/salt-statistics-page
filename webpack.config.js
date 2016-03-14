var path = require('path');

var cwd = process.cwd();

module.exports = {
    entry: './src/static/ts/app.ts',
    output: {
        path: path.resolve(cwd, "src/static/js"),
        filename: 'bundle.js'
    },
    resolve: {
        extensions: ['', '.ts', '.js', '.css']
    },
    module: {
        loaders: [
            { test: /\.ts$/, loader: 'ts-loader' }
        ]
    }
};
