from geodata import get_geodata
from flask.ext.login import LoginManager, UserMixin, login_user, logout_user,current_user
from oauth import OAuthSignIn
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

distance = 40


@app.route('/')
def index():
    return render_template('index.html') 

@app.route('/login/')
def login():
    return redirect(url_for('oauth_authorize', provider='twitter'))

@app.route('/logout/')
def logout():
    logout_user()
    return redirect(url_for('index'))

@lm.user_loader
def load_user(id):
    return db.getUser(id)

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
    login_user(user, True)
    return redirect(url_for('index'))

@app.route('/events/')
def events():
    ip_address = request.access_route[0] or request.remote_addr
    geodata = get_geodata(ip_address)
    secs = int(time.time())
    
    if geodata == {}:
        flash("Couldn't read your location and display events")
        return render_template('events.html', events = [])
    
    events = db.getObjects('events')
    res = []

    for event in events:
        if vincenty([event['lat'],event['lng']],[geodata['latitude'],geodata['longitude']]).miles < distance:
            res.append(event)
        
        if event['expires'] <= secs:
            db.removeEvent(event['_id'])

    return render_template('events.html', events = res,  fields = ['count','name','description'], city=geodata['city'], region=geodata['region_code'], time = secs)

@app.route('/new_event/')
def new_event():
    return render_template('new_event.html', categories = categories, expires = range(1,49))

@app.route('/add_event/', methods=['POST'])
def add_event():
    input = {'count':0, 'added':time.time()}
    for name in textFields:
        input[name] = request.form[name]
        if input[name] == '' or input[name] == None:
            if name == 'lat' or name == 'lng':
                flash('Please allow browser to use your location and choose an approximate placefor the activity')
            else:
                flash('Field {} is empty. Please fill out all the fields'.format(name))
            return redirect(url_for('new_event'))
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
    return redirect(url_for('events'))

@app.route('/event/<id>')
def event(id):
    event = db.getEvent(id)
    if event:
        return render_template('event.html',event=event)
    else:
        flash("User with id={} does not exit".format(id))
        return redirect(url_for('events'))

if __name__ == "__main__":
    app.run()
