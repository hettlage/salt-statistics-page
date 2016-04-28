var config = {
    // deployment
    HOST: 'your.production.host',
    DEV_HOST: 'your.dev.host',
    HOST_USERNAME: 'production-user',
    DEV_HOST_USERNAME: 'dev-user',
    HOST_DIR: '/path/to/repository/on/production/host',
    DEV_HOST_DIR: '/path/to/repository/on/dev/host',
    RESTART_HOST_SERVER: 'apachectl graceful',
    RESTART_DEV_HOST_SERVER: 'apachectl graceful',

    // Python
    PYTHON: '/path/to/venv/bin/python3'
};

module.exports = config;