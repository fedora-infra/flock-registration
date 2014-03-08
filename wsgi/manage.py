# -*- coding: utf-8 -*-
import os
from flask.ext.script import Manager
from registration import app

manager = Manager(app)

mongoexport = 'mongoexport'
mongo = 'mongo'


@manager.command
def export_registrations_as_json():
    """ Export registrations as json """
    os.system(mongoexport + (' --host $OPENSHIFT_MONGODB_DB_HOST'
                             ' --port $OPENSHIFT_MONGODB_DB_PORT'
                             ' --username $OPENSHIFT_MONGODB_DB_USERNAME'
                             ' --password $OPENSHIFT_MONGODB_DB_PASSWORD'
                             ' --db flock --collection registrations'
                             ' --out /tmp/flock-registrations.json'))


@manager.command
def export_proposals_as_json():
    """ Export presentation proposals as json """
    os.system(mongoexport + (' --host $OPENSHIFT_MONGODB_DB_HOST'
                             ' --port $OPENSHIFT_MONGODB_DB_PORT'
                             ' --username $OPENSHIFT_MONGODB_DB_USERNAME'
                             ' --password $OPENSHIFT_MONGODB_DB_PASSWORD'
                             ' --db flock --collection proposals'
                             ' --out /tmp/flock-proposals.json'))


@manager.command
def drop_database():
    """ Drop database """
    os.system(mongo + (' --host $OPENSHIFT_MONGODB_DB_HOST'
                       ' --port $OPENSHIFT_MONGODB_DB_PORT'
                       ' -u $OPENSHIFT_MONGODB_DB_USERNAME'
                       ' -p $OPENSHIFT_MONGODB_DB_PASSWORD'
                       ' --eval "db.dropDatabase();" flock'))

if __name__ == '__main__':
    manager.run()
