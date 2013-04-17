import os
import os.path

# XXX Fill this with something random. This is important!
SESSION_SECRET_KEY = ''

FUDCON_NAME = "FUDCon Lawrence"
FUDCON_DATES = "January 18-20"
FUDCON_YEAR = "2013"
FUDCON_URL = "http://fedoraproject.org/wiki/FUDCon:Lawrence_2013"

# These settings are all pretty good defaults when running on OpenShift.
LOGFILE = os.path.join(os.getenv('OPENSHIFT_PYTHON_LOG_DIR'), 'flask_log')
OPENID_STORE = os.path.join(os.getenv('OPENSHIFT_DATA_DIR'), 'openid_store')

MONGO_HOST = os.getenv('OPENSHIFT_MONGODB_DB_HOST')
MONGO_DBNAME = 'fudcon-registrations'
MONGO_USERNAME = os.getenv('OPENSHIFT_MONGODB_DB_USERNAME')
MONGO_PASSWORD = os.getenv('OPENSHIFT_MONGODB_DB_PASSWORD')

FUNDING_PROMPT = '<strong>Please visit <a href="https://fedorahosted.org/fudcon-planning/wiki/FundingRequest">the FUDCon ticket tracker</a> to make a funding request</strong>'
