from geodata import get_geodata
from flask import session
from flask_oauth import OAuth
from flask.ext.login import LoginManager, UserMixin, login_user, logout_user,current_user
import os
import time
from flask import Flask,flash,redirect,render_template,request,send_from_directory, url_for
import logging
from database import *
from werkzeug import secure_filename
from geopy.distance import vincenty
from flask.ext.googlemaps import GoogleMaps

logging.basicConfig(filename='web.log', level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

app = Flask(__name__)

GoogleMaps(app)
lm = LoginManager(app)
lm.login_view = 'index'
db = Database('bitcamp')
categories = ['food', 'sports', 'entertainment', 'outdoors', 'stydying']
textFields = ['name','description','expires', 'lat', 'lng']
otherFields = ['categories']
app.secret_key = 'blalga'
"""
app.config['OAUTH_CREDENTIALS'] = {
    'facebook': {
        'id': '470154729788964',
        'secret': '010cc08bd4f51e34f3f3e684fbdea8a7'
    },
    'twitter': {
        'id': '08fsYxhlDtt5KoMR844zjb4oj',
        'secret': '07eFc6FkuWT8EN259NMLrkDc13N5wC8ZkVomQDxWWdERGKDcSd'
    }
}
"""
oauth = OAuth()
twitter = oauth.remote_app('twitter',
    base_url='https://api.twitter.com/1/',
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authenticate',
    consumer_key='08fsYxhlDtt5KoMR844zjb4oj',
    consumer_secret='07eFc6FkuWT8EN259NMLrkDc13N5wC8ZkVomQDxWWdERGKDcSd'
)
distance = 40
@twitter.tokengetter
def get_twitter_token(token=None):
    return session.get('twitter_token')

@app.route('/')
def index():
    if 'twitter_user' in session:
        handle = session['twitter_user']
    else:
        handle = None
    return render_template('index.html', handle = handle) 

"""
@app.route('/login/')
def login():
    return redirect(url_for('oauth_authorize', provider='twitter'))
"""
@app.route('/login/')
def login():
    return twitter.authorize(callback=url_for('oauth_authorized',
        next=request.args.get('next') or request.referrer or None))

@app.route('/logout/')
def logout():
    del session['twitter_user']
    return redirect(url_for('index'))
"""
@lm.user_loader
def load_user(id):
    return db.getUserBySocialId(id)
"""

@app.route('/oauth-authorized')
@twitter.authorized_handler
def oauth_authorized(resp):
    next_url = request.args.get('next') or url_for('index')
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)

    session['twitter_token'] = (
        resp['oauth_token'],
        resp['oauth_token_secret']
    )
    session['twitter_user'] = resp['screen_name']
    logging.info(resp)

    flash('You were signed in as %s' % resp['screen_name'])
    return redirect(next_url)
"""
@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous():
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()

@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous():
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    user = db.getUserBySocialId(social_id)
    if not user:
        user = User(social_id=social_id, nickname=username)
        user._id = db.addUser(user)
    login_user(user, remember = True)
    return redirect(url_for('index'))
"""
@app.route('/events/')
def events():
    if 'twitter_user' in session:
        handle = session['twitter_user']
    else:
        handle = None
    
    ip_address = request.access_route[0] or request.remote_addr
    geodata = get_geodata(ip_address)
    secs = int(time.time())
    
    if geodata == {}:
        flash("Couldn't read your location and display events")
        return render_template('events.html', events = [],handle=handle)
    
    events = db.getObjects('events')
    res = []

    for event in events:
        if vincenty([event['lat'],event['lng']],[geodata['latitude'],geodata['longitude']]).miles < distance:
            res.append(event)
        
        if event['expires'] <= secs:
            db.removeEvent(event['_id'])

    return render_template('events.html', events = res,  fields = ['count','name','description'], city=geodata['city'], region=geodata['region_code'], time = secs, handle = handle)

@app.route('/new_event/')
def new_event():
    if 'twitter_user' in session:
        handle = session['twitter_user']
    else:
        handle = None
    return render_template('new_event.html', categories = categories, expires = range(1,49),handle = handle)

@app.route('/add_event/', methods=['POST'])
def add_event():
    if 'twitter_user' in session:
        handle = session['twitter_user']
    else:
        handle = None
    
    input = {'count':0, 'added':time.time()}
    for name in textFields:
        input[name] = request.form[name]
        if input[name] == '' or input[name] == None:
            if name == 'lat' or name == 'lng':
                flash('Please allow browser to use your location and choose an approximate placefor the activity')
            else:
                flash('Field {} is empty. Please fill out all the fields'.format(name))
            return redirect(url_for('new_event'), handle = handle)
    input['expires'] = 3600*int(input['expires']) + input['added']
    
    #ip_address = request.access_route[0] or request.remote_addr
    #geodata = get_geodata(ip_address)
    
    #if geodata == {}:
        #flash("Couldn't read your location. Please try later")
        #return redirect(url_for('new_event'))
    
    #input['lat'] = geodata['latitude']
    #input['long'] = geodata['longitude']
    input['categories'] = request.form.getlist('categories')
    db.addEvent(input)
    return redirect(url_for('events'), handle = handle)

@app.route('/event/<id>')
def event(id):
    if 'twitter_user' in session:
        handle = session['twitter_user']
    else:
        handle = None
    
    event = db.getEvent(id)
    if event:
        return render_template('event.html',event=event, handle = handle)
    else:
        flash("User with id={} does not exit".format(id))
        return redirect(url_for('events'), handle = handle)

if __name__ == "__main__":
    app.run()
