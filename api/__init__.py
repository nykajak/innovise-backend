import os
from flask import Flask,current_app
from flask_cors import CORS
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["MONGO_URI"] = os.getenv("CONN_STR")

with app.app_context():
    db = PyMongo(current_app).cx["innovise"]

CORS(app)

from api import routes