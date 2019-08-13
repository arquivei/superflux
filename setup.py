from setuptools import setup, find_packages

setup(
    name             = 'superflux',
    version          = "0.0.1",
    description      = 'Library & Eventlistener for Supervisord to send events to Influxdb',
    author           = 'Ricardo Verhaeg',
    author_email     = 'ricardo@arquivei.com.br',
    url              = 'https://github.com/arquivei/superflux',
    packages         = find_packages(),
    install_requires = [ 'supervisor', 'requests', ],
    entry_points     = {
        'console_scripts': [ 'superflux = superflux.cli:main' ]
    },
)
