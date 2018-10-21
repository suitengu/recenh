import os
from flask import Flask, flash, request, redirect, url_for
from flask import send_from_directory

app = Flask(__name__)

app.config['SECRET_KEY'] = 'not a very secret string'
#  TODO: hide this somewhere, I guess
app.config['LFM_API_KEY'] = '' # api key goes here

from app import routes
