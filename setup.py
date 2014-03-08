from setuptools import setup

setup(
    name='flock-registration',
    version='0.1',
    license='GPLv2+',
    description='A Flask-based application for handling Fedora Flock registrations',
    author='Ian Weller, Luke Macken',
    author_email='ianweller@fedoraproject.org',
    url='http://fedoraproject.org/wiki/FUDCon',
    install_requires=['Flask',
                      'Flask-OpenID',
                      'Flask-PyMongo',
                      'Flask-WTF',
                      'bunch',
                      'Flask-Babel',
                      'Flask-Script'],
)
