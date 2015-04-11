from geodata import get_geodata
import os
import time
from flask import Flask,flash,redirect,render_template,request,send_from_directory, url_for
import logging
from database import *
from werkzeug import secure_filename
from geopy.distance import vincenty

logging.basicConfig(filename='web.log', level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
app = Flask(__name__)
db = Database('bitcamp')
categories = ['food', 'sports', 'entertainment', 'outdoors', 'stydying']
textFields = ['name','description','expires']
otherFields = ['categories']
app.secret_key = 'blalga'
distance = 20

@app.route('/')
def index():
    return render_template('index.html') 

@app.route('/events/')
def events():
    ip_address = request.access_route[0] or request.remote_addr
    geodata = get_geodata(ip_address)
    
    if geodata == {}:
        flash("Couldn't read your location and display events")
        return render_template('events.html', events = [])
    
    events = db.getObjects('events')
    res = []

    for event in events:
        if vincenty([event['lat'],event['long']],[geodata['latitude'],geodata['longitude']]).miles < distance:
            res.append(event)

    return render_template('events.html', events = res, time = time.time(), fields = ['count','name','description'], city=geodata['city'], region=geodata['region_code'])

@app.route('/new_event/')
def new_event():
    return render_template('new_event.html', categories = categories, expires = range(1,49))

@app.route('/add_event/', methods=['POST'])
def add_event():
    input = {'count':0, 'added':time.time()}
    for name in textFields:
        input[name] = request.form[name]
        if input[name] == None:
            return "Field {} is not present!".format(name)
        if input[name] == '':
            flash('Field {} is empty. Please fill out all the fields'.format(name))
            return redirect(url_for('new_event'))
    input['expires'] = 3600*int(input['expires']) + input['added']
    
    ip_address = request.access_route[0] or request.remote_addr
    geodata = get_geodata(ip_address)
    
    if geodata == {}:
        flash("Couldn't read your location. Please try later")
        return redirect(url_for('new_event'))
    
    input['lat'] = geodata['latitude']
    input['long'] = geodata['longitude']
    input['categories'] = request.form.getlist('categories')
    db.addEvent(input)
    return redirect(url_for('events'))

if __name__ == "__main__":
    app.run()
