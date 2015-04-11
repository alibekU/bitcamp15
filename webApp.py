import os
import time
from flask import Flask,flash,redirect,render_template,request,send_from_directory, url_for
import logging
from database import *
from werkzeug import secure_filename

logging.basicConfig(filename='web.log', level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
app = Flask(__name__)
db = Database('bitcamp')

app.secret_key = 'blalga'

@app.route('/')
def index():
    l = db.getObjects('users')
    d = []
    for x in l:
        d.append(x)
    return "Hello world {}".format(str(d))

if __name__ == "__main__":
    app.run()
