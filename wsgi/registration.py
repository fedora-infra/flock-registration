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
from flask import request
from flask.ext.babel import Babel
from flask.ext.babel import gettext, ngettext
from flask.ext.babel import lazy_gettext
from config import LANGUAGES
import wtforms as wtf
import logging
import uuid
import os

app = flask.Flask(__name__)
app.config.from_pyfile('config.py')

from flask_wtf.csrf import CsrfProtect
csrf = CsrfProtect()
csrf.init_app(app)

# Set up babel for translations
babel = Babel(app)

# Set up session secret key
app.secret_key = app.config['SESSION_SECRET_KEY']

# Set up OpenID
oid = OpenID(app, fs_store_path=app.config['OPENID_STORE'], safe_roots=[])

# Set up MongoDB
mongo = PyMongo(app)

# Set up logging
if not app.debug:
    file_handler = logging.FileHandler(app.config['LOGFILE'])
    file_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(LANGUAGES.keys())


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
    firstname = wtf.TextField(lazy_gettext('First (Given) Name'),
                              [wtf.validators.Required()])
    middlename = wtf.TextField(lazy_gettext('Middle Name'))
    lastname = wtf.TextField(lazy_gettext('Last (Family) Name'))
    email = wtf.TextField(lazy_gettext('Email address'),
                          [wtf.validators.Required()])
    fasusername = wtf.TextField(lazy_gettext('FAS username'))
    location = wtf.TextField(lazy_gettext('Location'))
    invitation_letter = wtf.BooleanField(
        lazy_gettext('Do you need an invitation letter to attend Flock?'))
    hotel_funding = wtf.BooleanField(lazy_gettext('Need hotel funding?'))
    flight_funding = wtf.BooleanField(lazy_gettext('Need flight funding?'))
    near_westford = wtf.BooleanField(
        lazy_gettext('Are you located in/near Westford, MA?'))

    month_of_birth = wtf.TextField(lazy_gettext('Month of Birth'))
    day_of_birth = wtf.TextField(lazy_gettext('Day of Birth'))
    year_of_birth = wtf.TextField(lazy_gettext('Year of Birth'))
    mailing_address = wtf.TextAreaField(lazy_gettext('Mailing Address'))
    phone_number = wtf.TextField(lazy_gettext('Phone Number'))
    gender = wtf.SelectField(lazy_gettext('Gender'),
                             choices=choicer([lazy_gettext('Male'),
                             lazy_gettext('Female')]))
    passport_country = wtf.TextField(lazy_gettext('Passport Country'))
    passport_number = wtf.TextField(lazy_gettext('Passport Number'))
    departure_airport = wtf.TextField(
        lazy_gettext('Preferred Departure Airport'))
    return_airport = wtf.TextField(lazy_gettext('Preferred Return Airport'))
    other_notes = wtf.TextAreaField(
        lazy_gettext('Other notes relating to flight subsidy preferences'))

    family = wtf.SelectField(
        lazy_gettext('Bringing family?'),
        choices=choicer([lazy_gettext('No'), '1', '2', '3', '4', '5+']))

    volunteer = wtf.BooleanField(lazy_gettext('Willing to be a volunteer?'))
    veg = wtf.SelectField(
        lazy_gettext('Vegan or vegetarian?'),
        choices=choicer([lazy_gettext('No'),
                         lazy_gettext('Vegan'),
                         lazy_gettext('Vegetarian')]))
    size = wtf.SelectField(
        lazy_gettext('T-shirt size'),
        choices=choicer([lazy_gettext('No shirt'),
                         lazy_gettext('XS'),
                         lazy_gettext('S'),
                         lazy_gettext('M'),
                         lazy_gettext('L'),
                         lazy_gettext('XL'),
                         lazy_gettext('2XL'),
                         lazy_gettext('3XL'),
                         lazy_gettext('Womens S'),
                         lazy_gettext('Womens M'),
                         lazy_gettext('Womens L'),
                         lazy_gettext('Womens XL'),
                         ]))
    roomshare = wtf.SelectField(
        lazy_gettext('Room share'),
        choices=choicer([lazy_gettext('No'),
                         lazy_gettext('Yes'),
                         lazy_gettext('Found roommate')]))
    roommate = wtf.TextField('Roommate')
    hotel_booked = wtf.SelectField(
        lazy_gettext('Hotel booked?'),
        choices=choicer([lazy_gettext('No'),
                         lazy_gettext('Yes'),
                         lazy_gettext('No hotel')]))
    blog = wtf.TextField(lazy_gettext('Blog'))
    twitter = wtf.TextField(lazy_gettext('Twitter'))
    comments = wtf.TextField(lazy_gettext('Comments'))
    badge_line = wtf.TextField(lazy_gettext('Extra line on badge'))

    def validate_roommate(form, field):
        if form.roomshare.data == 'Found roommate' and not form.roommate.data:
            raise wtf.ValidationError(lazy_gettext('This field is required if '
                                      '"Found roommate" is selected.'))


class ConfirmationForm(wtf.Form):
    confirmbox = wtf.BooleanField(lazy_gettext('Yes, delete this'))


class PresentationProposalForm(wtf.Form):
    fasusername = wtf.TextField(lazy_gettext('FAS username'))
    title = wtf.TextField(
        lazy_gettext('Presentation title'),
        [wtf.validators.Required()])
    # I think that this choices shouldn't be translated.
    category = wtf.SelectField(lazy_gettext('Category'), choices=choicer([
        'Ambassadors', 'ARM', 'Cloud', 'Community', 'Design', 'Desktop',
        'Fonts', 'Games', 'Hardware', 'Infrastructure', 'Kernel', 'Marketing',
        'QA', 'Security', 'SIG', 'Other',
    ]))
    type_ = wtf.SelectField(lazy_gettext('Type'), choices=choicer([
        lazy_gettext('Talk (45 min)'), lazy_gettext('Workshop (2 hours)'),
    ]))
    abstract = wtf.TextAreaField(
        lazy_gettext('Presentation abstract'),
        [wtf.validators.Required()])


# Requests
@app.before_request
def lookup_current_user():
    flask.g.user = None
    flask.g.fasusername = None
    if 'openid' in flask.session:
        flask.g.user = flask.session['openid']
        if 'id.fedoraproject.org' in flask.g.user:
            try:
                flask.g.fasusername = flask.g.user.split('//')[1].split('.')[0]
            except:
                pass


@app.route('/')
def index():
    notice = app.config.get('NOTICE')
    if notice:
        flask.flash(notice)
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
        flask.flash(gettext(gettext('The registration period has closed')))
        return flask.redirect(flask.url_for('index'))
    if flask.g.user is None:
        return flask.redirect(flask.url_for('login'))
    form = RegistrationForm(flask.request.form)
    if flask.request.method == 'POST' and form.validate():
        registration = form.data
        registration['_id'] = generate_uuid()
        registration['openid'] = flask.g.user
        registration['created'] = datetime.utcnow()
        registration['modified'] = registration['created']
        mongo.db.registrations.insert(registration)
        #if registration['hotel_funding']:
        #    flask.flash(flask.Markup(app.config['FUNDING_PROMPT']))
        return flask.redirect(flask.url_for('index'))
    if flask.g.fasusername:
        form.fasusername.data = flask.g.fasusername
    return flask.render_template('registration.html', form=form,
                                 submit_text=gettext("Submit registration"))


@app.route('/proposals')
def proposals():
    proposals = mongo.db.proposals.find(sort=[('created', 1)])
    admin = flask.g.fasusername in app.config['ADMINS']
    return flask.render_template('proposals.html', proposals=proposals,
                                 now=datetime.utcnow(), admin=admin)


@app.route('/admin/<action>/<id>')
def admin(action, id):
    """ An admin view to accept/reject proposals """
    if flask.g.fasusername not in app.config['ADMINS']:
        flask.abort(401)
    if action not in ('accept', 'reject'):
        flask.abort(400)
    proposal = mongo.db.proposals.find_one({'_id': id})
    if not proposal:
        flask.flash('Cannot find proposal %r' % id)
        return flask.redirect(flask.url_for('proposals'))
    if action == 'reject':
        proposal['rejected'] = True
        openid = proposal['openid']
        app.logger.info('Removing all registrations for %s' % openid)
        mongo.db.registrations.remove({'openid': openid})
    else:
        proposal['rejected'] = False
    mongo.db.proposals.save(proposal)
    msg = 'Proposal "%s" %sed' % (proposal['title'], action)
    flask.flash(msg)
    app.logger.info(msg)
    return flask.redirect(flask.url_for('proposals'))


@app.route('/admin/proposals.txt')
def admin_proposals_txt():
    """ An admin view to list all proposals mapped to usernames """
    if flask.g.fasusername not in app.config['ADMINS']:
        flask.abort(401)
    proposals = mongo.db.proposals.find().sort('fasusername', 1)
    txt = '\n'.join(['%(fasusername)s %(title)s' % p for p in proposals])
    resp = flask.make_response(txt)
    resp.mimetype = 'text/plain'
    return resp


@app.route('/admin/proposal-submitters.txt')
def proposal_submitters():
    """ An admin view to list usernames mappeed to email address of people who
    submitted proposals """
    if flask.g.fasusername not in app.config['ADMINS']:
        flask.abort(401)

    txt = []
    proposals = mongo.db.proposals.find().sort('fasusername', 1)
    for proposal in proposals:
        for username in proposal['fasusername'].replace(',', ' ').split():
            reg = mongo.db.registrations.find_one({'fasusername': str(username)})
            if not reg:
                app.logger.error('Cannot find registration for user: %r' % username)
                app.logger.error(repr(proposal))
                continue
            line = '%(fasusername)s %(email)s' % reg
            if line not in txt:
                txt.append(line)

    resp = flask.make_response('\n'.join(txt))
    resp.mimetype = 'text/plain'
    return resp


@app.route('/admin/proposals/rejected')
def admin_rejected_proposals():
    """ An admin view to list reject proposals """
    if flask.g.fasusername not in app.config['ADMINS']:
        flask.abort(401)
    proposals = mongo.db.proposals.find({'rejected': True})
    usernames = [p.fasusername for p in proposals]
    return flask.jsonify(usernames=usernames)


@app.route('/submit_proposal', methods=['GET', 'POST'])
def submit_proposal():
    if datetime.utcnow() >= app.config['SUBMISSION_DEADLINE']:
        flask.flash(gettext('The presentation submission period has closed'))
        return flask.redirect(flask.url_for('proposals'))
    if flask.g.user is None:
        return flask.redirect(flask.url_for('login'))

    # Force people to register before submitting proposals
    registrations = mongo.db.registrations.find({'openid': flask.g.user},
                                                sort=[('created', 1)])
    if registrations.count(True) == 0:
        flask.flash(
            gettext('You must register before you can submit a proposal'))
        return flask.redirect(flask.url_for('new'))

    form = PresentationProposalForm(flask.request.form)
    if flask.request.method == 'POST' and form.validate():
        proposal = form.data
        proposal['_id'] = generate_proposal_uuid()
        proposal['openid'] = flask.g.user
        proposal['created'] = datetime.utcnow()
        proposal['modified'] = proposal['created']
        proposal['rejected'] = False
        mongo.db.proposals.insert(proposal)
        flask.flash(gettext('Proposal submitted'))
        return flask.redirect(flask.url_for('proposals'))
    if flask.g.fasusername:
        form.fasusername.data = flask.g.fasusername
    return flask.render_template('proposal.html', form=form,
                                 submit_text=gettext('Submit proposal'))


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
    return flask.render_template('edit_proposals_list.html',
                                 proposals=proposals)


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
    form = PresentationProposalForm(flask.request.form, obj=proposal)
    if flask.request.method == 'POST' and form.validate():
        form.populate_obj(proposal)
        proposal['modified'] = datetime.utcnow()
        mongo.db.proposals.save(proposal.toDict())
        flask.flash(gettext('Proposal updated'))
        return flask.redirect(flask.url_for('proposals'))
    return flask.render_template('proposal.html', form=form,
                                 submit_text=gettext('Edit proposal'),
                                 delete_text=gettext('Delete proposal'),
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
    form = ConfirmationForm(flask.request.form)
    if flask.request.method == 'POST' and form.validate():
        if form.confirmbox.data:
            mongo.db.proposals.remove({'_id': id, 'openid': flask.g.user})
            flask.flash(gettext('Proposal deleted'))
        else:
            flask.flash(gettext('Proposal not deleted'))
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
    form = RegistrationForm(flask.request.form, obj=registration)
    if flask.request.method == 'POST' and form.validate():
        #oldfunding = registration.funding
        form.populate_obj(registration)
        registration['modified'] = datetime.utcnow()
        mongo.db.registrations.save(registration.toDict())
        flask.flash(gettext('Registration updated'))
        #if not oldfunding and registration.funding:
            #flask.flash(flask.Markup(app.config['FUNDING_PROMPT']))
        return flask.redirect(flask.url_for('index'))
    return flask.render_template('registration.html', form=form,
                                 submit_text=gettext('Edit registration'),
                                 delete_text=gettext('Delete registration'),
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
    form = ConfirmationForm(flask.request.form)
    if flask.request.method == 'POST' and form.validate():
        if form.confirmbox.data:
            mongo.db.registrations.remove({'_id': id, 'openid': flask.g.user})
            flask.flash(gettext('Registration deleted'))
        else:
            flask.flash(gettext('Registration not deleted'))
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
        flask.flash(gettext(u'Welcome'), '%s' % flask.session['openid'])
        flask.g.user = user
    return flask.redirect(oid.get_next_url())

if __name__ == '__main__':
    app.run(debug=True)
