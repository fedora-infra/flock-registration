# Copyright (C) 2012 Ian Weller <ianweller@fedoraproject.org>
# Copyright (C) 2013 Luke Macken <lmacken@redhat.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from bunch import Bunch
from datetime import datetime
import flask
from flask.ext.openid import OpenID
from flask.ext.pymongo import PyMongo
import wtforms as wtf
import logging
from pprint import pformat
import uuid
import os

app = flask.Flask(__name__)
app.config.from_pyfile('config.py')

# Set up session secret key
app.secret_key = app.config['SESSION_SECRET_KEY']

# Set up OpenID
oid = OpenID(app, app.config['OPENID_STORE'])

# Set up MongoDB
mongo = PyMongo(app)

# Set up logging
if not app.debug:
    file_handler = logging.FileHandler(app.config['LOGFILE'])
    file_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)


def generate_uuid():
    while True:
        the_uuid = str(uuid.uuid4())
        if not mongo.db.registrations.find_one({'_id': the_uuid}):
            return the_uuid


def generate_proposal_uuid():
    while True:
        the_uuid = str(uuid.uuid4())
        if not mongo.db.proposals.find_one({'_id': the_uuid}):
            return the_uuid


# Forms
def choicer(choices):
    return [(x, x) for x in choices]


class RegistrationForm(wtf.Form):
    firstname = wtf.TextField('First name', [wtf.validators.Required()])
    lastname = wtf.TextField('Last name')
    email = wtf.TextField('Email address', [wtf.validators.Required()])
    fasusername = wtf.TextField('FAS username')
    location = wtf.TextField('Location')
    invitation_letter = wtf.BooleanField('Do you need an invitation letter to attend Flock?')
    hotel_funding = wtf.BooleanField('Need hotel funding?')
    flight_funding = wtf.BooleanField('Need flight funding?')
    family = wtf.SelectField('Bringing family?', choices=choicer([
        'No', '1', '2', '3', '4', '5+'
    ]))
    volunteer = wtf.BooleanField('Willing to be a volunteer?')
    veg = wtf.SelectField('Vegan or vegetarian?', choices=choicer([
        'No', 'Vegan', 'Vegetarian'
    ]))
    size = wtf.SelectField('T-shirt size', choices=choicer([
        'No shirt', 'XS', 'S', 'M', 'L', 'XL', '2XL', '3XL'
    ]))
    roomshare = wtf.SelectField('Room share', choices=choicer([
        'No', 'Yes', 'Found roommate'
    ]))
    roommate = wtf.TextField('Roommate')
    hotel_booked = wtf.SelectField('Hotel booked?', choices=choicer([
        'No', 'Yes', 'No hotel'
    ]))
    blog = wtf.TextField('Blog')
    twitter = wtf.TextField('Twitter')
    comments = wtf.TextField('Comments')
    badge_line = wtf.TextField('Extra line on badge')

    def validate_roommate(form, field):
        if form.roomshare.data == 'Found roommate' and not form.roommate.data:
            raise wtf.ValidationError('This field is required if '
                                      '"Found roommate" is selected.')


class ConfirmationForm(wtf.Form):
    confirmbox = wtf.BooleanField('Yes, delete this')


class PresentationProposalForm(wtf.Form):
    fasusername = wtf.TextField('FAS username')
    title = wtf.TextField('Presentation title', [wtf.validators.Required()])
    category = wtf.SelectField('Category', choices=choicer([
        'Ambassadors', 'ARM', 'Cloud', 'Community', 'Design', 'Desktop',
        'Fonts', 'Games', 'Hardware', 'Infrastructure', 'Kernel', 'Marketing',
        'QA', 'Security', 'SIG', 'Other',
    ]))
    type_ = wtf.SelectField('Type', choices=choicer([
        'Talk (45 min)', 'Workshop (2 hours)',
    ]))
    abstract = wtf.TextAreaField('Presentation abstract', [wtf.validators.Required()])


# Requests
@app.before_request
def lookup_current_user():
    flask.g.user = None
    if 'openid' in flask.session:
        flask.g.user = flask.session['openid']


@app.route('/')
def index():
    registrations = mongo.db.registrations.find(sort=[('created', 1)])
    return flask.render_template('index.html', registrations=registrations,
                                 now=datetime.now())


@app.route('/favicon.ico')
def favicon():
    return flask.send_from_directory(os.path.join(app.root_path, 'static'),
                                     'favicon.ico',
                                     mimetype='image/vnd.microsoft.icon')


@app.route('/new', methods=['GET', 'POST'])
def new():
    if datetime.utcnow() > app.config['REGISTRATION_DEADLINE']:
        flask.flash('The registration period has closed')
        return flask.redirect(flask.url_for('index'))
    if flask.g.user is None:
        return flask.redirect(flask.url_for('login'))
    form = RegistrationForm()
    if form.validate_on_submit():
        registration = form.data
        registration['_id'] = generate_uuid()
        registration['openid'] = flask.g.user
        registration['created'] = datetime.utcnow()
        registration['modified'] = registration['created']
        mongo.db.registrations.insert(registration)
        #if registration['hotel_funding']:
        #    flask.flash(flask.Markup(app.config['FUNDING_PROMPT']))
        return flask.redirect(flask.url_for('index'))
    if 'id.fedoraproject.org' in flask.g.user:
        try:
            form.fasusername.data = flask.g.user.split('//')[1].split('.')[0]
        except:
            pass
    return flask.render_template('registration.html', form=form,
                                 submit_text="Submit registration")


@app.route('/proposals')
def proposals():
    proposals = mongo.db.proposals.find(sort=[('created', 1)])
    return flask.render_template('proposals.html', proposals=proposals,
                                 now=datetime.utcnow())


@app.route('/submit_proposal', methods=['GET', 'POST'])
def submit_proposal():
    if datetime.utcnow() >= app.config['SUBMISSION_DEADLINE']:
        flask.flash('The presentation submission period has closed')
        return flask.redirect(flask.url_for('proposals'))
    if flask.g.user is None:
        return flask.redirect(flask.url_for('login'))
    form = PresentationProposalForm()
    if form.validate_on_submit():
        proposal = form.data
        proposal['_id'] = generate_proposal_uuid()
        proposal['openid'] = flask.g.user
        proposal['created'] = datetime.utcnow()
        proposal['modified'] = proposal['created']
        mongo.db.proposals.insert(proposal)
        flask.flash('Proposal submitted')
        return flask.redirect(flask.url_for('proposals'))
    if 'id.fedoraproject.org' in flask.g.user:
        try:
            form.fasusername.data = flask.g.user.split('//')[1].split('.')[0]
        except:
            pass
    return flask.render_template('proposal.html', form=form,
                                 submit_text="Submit proposal")


@app.route('/edit_proposal')
def edit_proposal():
    if flask.g.user is None:
        return flask.redirect(flask.url_for('login'))
    proposals = mongo.db.proposals.find({'openid': flask.g.user},
                                        sort=[('created', 1)])
    if proposals.count(True) == 0:
        return flask.render_template('no_proposals.html')
    if proposals.count(True) == 1:
        return flask.redirect(flask.url_for('edit_one_proposal',
                                            id=proposals[0]['_id']))
    return flask.render_template('edit_proposals_list.html', proposals=proposals)


@app.route('/edit_proposal/<id>', methods=['GET', 'POST'])
def edit_one_proposal(id):
    if flask.g.user is None:
        return flask.redirect(flask.url_for('index'))
    proposal = mongo.db.proposals.find_one({
        '_id': id,
        'openid': flask.g.user
    })
    if not proposal:
        return flask.redirect(flask.url_for('index'))
    proposal = Bunch(proposal)
    form = PresentationProposalForm(obj=proposal)
    if form.validate_on_submit():
        form.populate_obj(proposal)
        proposal['modified'] = datetime.utcnow()
        mongo.db.proposals.save(proposal.toDict())
        flask.flash('Proposal updated')
        return flask.redirect(flask.url_for('proposals'))
    return flask.render_template('proposal.html', form=form,
                                 submit_text="Edit proposal",
                                 delete_text="Delete proposal",
                                 uuid=id)


@app.route('/delete_proposal/<id>', methods=['GET', 'POST'])
def delete_one_proposal(id):
    if flask.g.user is None:
        return flask.redirect(flask.url_for('index'))
    proposal = mongo.db.proposals.find_one({
        '_id': id,
        'openid': flask.g.user
    })
    if not proposal:
        return flask.redirect(flask.url_for('index'))
    form = ConfirmationForm()
    if form.validate_on_submit():
        if form.confirmbox.data:
            mongo.db.proposals.remove({'_id': id, 'openid': flask.g.user})
            flask.flash('Proposal deleted')
        else:
            flask.flash('Proposal not deleted')
        return flask.redirect(flask.url_for('proposals'))
    return flask.render_template('delete_confirm.html', form=form)


@app.route('/edit')
def edit():
    if flask.g.user is None:
        return flask.redirect(flask.url_for('login'))
    registrations = mongo.db.registrations.find({'openid': flask.g.user},
                                                sort=[('created', 1)])
    if registrations.count(True) == 0:
        return flask.render_template('no_registrations.html')
    if registrations.count(True) == 1:
        return flask.redirect(flask.url_for('edit_one',
                                            id=registrations[0]['_id']))
    return flask.render_template('edit_list.html', registrations=registrations)


@app.route('/edit/<id>', methods=['GET', 'POST'])
def edit_one(id):
    if flask.g.user is None:
        return flask.redirect(flask.url_for('index'))
    registration = mongo.db.registrations.find_one({
        '_id': id,
        'openid': flask.g.user
    })
    if not registration:
        return flask.redirect(flask.url_for('index'))
    registration = Bunch(registration)
    form = RegistrationForm(obj=registration)
    if form.validate_on_submit():
        #oldfunding = registration.funding
        form.populate_obj(registration)
        registration['modified'] = datetime.utcnow()
        mongo.db.registrations.save(registration.toDict())
        flask.flash('Registration updated')
        #if not oldfunding and registration.funding:
            #flask.flash(flask.Markup(app.config['FUNDING_PROMPT']))
        return flask.redirect(flask.url_for('index'))
    return flask.render_template('registration.html', form=form,
                                 submit_text="Edit registration",
                                 delete_text="Delete registration",
                                 uuid=id)


@app.route('/delete/<id>', methods=['GET', 'POST'])
def delete_one(id):
    if flask.g.user is None:
        return flask.redirect(flask.url_for('index'))
    registration = mongo.db.registrations.find_one({
        '_id': id,
        'openid': flask.g.user
    })
    if not registration:
        return flask.redirect(flask.url_for('index'))
    form = ConfirmationForm()
    if form.validate_on_submit():
        if form.confirmbox.data:
            mongo.db.registrations.remove({'_id': id, 'openid': flask.g.user})
            flask.flash('Registration deleted')
        else:
            flask.flash('Registration not deleted')
        return flask.redirect(flask.url_for('index'))
    return flask.render_template('delete_confirm.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if flask.g.user is not None:
        return flask.redirect(oid.get_next_url())
    if flask.request.method == 'POST':
        fasusername = flask.request.form.get('fas')
        if fasusername:
            return oid.try_login('https://id.fedoraproject.org/')
        openid = flask.request.form.get('openid')
        if openid:
            return oid.try_login(openid)
    return flask.render_template('login.html', next=oid.get_next_url(),
                                 error=oid.fetch_error())


@app.route('/logout')
def logout():
    del flask.session['openid']
    return flask.redirect(flask.request.referrer or flask.url_for('index'))


@oid.after_login
def create_or_login(resp):
    flask.session['openid'] = resp.identity_url
    user = flask.session['openid']
    if user is not None:
        flask.flash(u'Welcome, %s' % flask.session['openid'])
        flask.g.user = user
    return flask.redirect(oid.get_next_url())

if __name__ == '__main__':
    app.run()
