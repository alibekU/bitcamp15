from geodata import get_geodata
from flask import session
from flask_oauth import OAuth
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
db = Database('bitcamp')
categories = ['food', 'sports', 'entertainment', 'outdoors', 'stydying']

textFields = ['name','description','expires', 'lat', 'lng']
otherFields = ['categories']
app.secret_key = 'blalga'
oauth = OAuth()
twitter = oauth.remote_app('twitter',
    base_url='https://api.twitter.com/1/',
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authenticate',
    consumer_key='NpWb6AedZ2W3THChRLNcWlDKO',
    consumer_secret='v47xidilYi0SzWZFLXd4P2EvriqXbAoq04VibmFlszat1JV8Dy'
)
distance = 40

@twitter.tokengetter
def get_twitter_token(token=None):
    return session.get('twitter_token')

@app.route('/oauth-authorized/')
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

    return redirect(next_url)

@app.route('/login/')
def login():
    return twitter.authorize(callback=url_for('oauth_authorized',next=request.args.get('next') or request.referrer or None))

@app.route('/')
def index():
    if 'twitter_user' in session:
        handle = session['twitter_user']
    else:
        handle = ''
    return render_template('index.html',handle=handle) 

@app.route('/logout/')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/events/')
def events():
    if 'twitter_user' in session:
        handle = session['twitter_user']
    else:
        handle = ''

    ip_address = request.access_route[0] or request.remote_addr
    geodata = get_geodata(ip_address)
    secs = int(time.time())
    
    if geodata == {}:
        flash("Couldn't read your location and display events")
        return render_template('events.html', events = [], handle = handle)
    
    events = db.getObjects('events')
    res = []

    for event in events:
        if vincenty([event['lat'],event['lng']],[geodata['latitude'],geodata['longitude']]).miles < distance:
            res.append(event)
        
        if event['expires'] <= secs:
            db.removeEvent(event['_id'])

    return render_template('events.html', events = res,  fields = ['count','name'],handle = handle, city=geodata['city'], region=geodata['region_code'], time = secs)

@app.route('/new_event/')
def new_event():
    if 'twitter_user' in session:
        handle = session['twitter_user']
    else:
        handle = ''
    return render_template('new_event.html',handle = handle, categories = categories, expires = range(1,49))

@app.route('/add_event/', methods=['POST'])
def add_event():
    if 'twitter_user' in session:
        handle = session['twitter_user']
    else:
        handle = ''
    input = {'count':0, 'added':time.time()}
    for name in textFields:
        input[name] = request.form[name]
        if input[name] == '' or input[name] == None:
            if name == 'lat' or name == 'lng':
                flash('Please allow browser to use your location and choose an approximate placefor the activity')
            else:
                flash('Field {} is empty. Please fill out all the fields'.format(name))
            return redirect(url_for('new_event', handle = handle))
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
    return redirect(url_for('events', handle = handle))

@app.route('/voted/<person>/<eventId>')
def voted(person, eventId):
    res = db.addVote(person, eventId)
    if res == 0:
        flash("An error occured, we apologize for the inconvenience")
    elif res == -1:
        flash("You already voted for this event.")
    else:
        flash("Thank you, you vote has been processed")
    return redirect(url_for('event',id=eventId))


@app.route('/event/<id>')
def event(id):
    if 'twitter_user' in session:
        handle = session['twitter_user']
    else:
        handle = ''
    event = db.getEvent(id)
    if event:
        return render_template('event.html',event=event, handle = handle, time=time.time())
    else:
        flash("User with id={} does not exit".format(id))
        return redirect(url_for('events', handle = handle))

if __name__ == "__main__":
    app.run()
