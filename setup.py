from setuptools import setup

setup(
    name='fudcon-registration',
    version='0.1',
    description='A Flask-based application for handling FUDCon registrations',
    author='Ian Weller',
    author_email='ianweller@fedoraproject.org',
    url='http://fedoraproject.org/wiki/FUDCon',
    install_requires=['Flask', 'Flask-OpenID', 'Flask-PyMongo', 'Flask-WTF', 'bunch'],
)
