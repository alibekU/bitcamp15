import os
import time
from flask import Flask,flash,redirect,render_template,request,send_from_directory, url_for
import logging
from database import *
from werkzeug import secure_filename

logging.basicConfig(filename='web.log', level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
app = Flask(__name__)
db = Database('bitcamp')
fields = ['name','description']
app.secret_key = 'blalga'

@app.route('/')
def index():
    return render_template('index.html') 

@app.route('/events/')
def events():
    events = db.getObjects('events')
    return render_template('events.html', events = events)

@app.route('/new_event/')
def new_event():
    return render_template('new_event.html')

@app.route('/add_event/', methods=['POST'])
def add_event():
    input = {}
    for name in fields:
        input[name] = request.form[name]
        if input[name] == None:
            return "Field {} is not present!".format(name)
        if input[name] == '':
            flash('Field {} is empty. Please fill out all the fields'.format(name))
            return redirect(url_for('new_event'))
    db.addEvent(input)
    flash("Added a new event")
    return redirect(url_for('events'))

if __name__ == "__main__":
    app.run()
