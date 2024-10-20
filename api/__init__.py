import os
from flask import Flask,current_app
from flask_cors import CORS
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from gridfs import GridFS

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["MONGO_URI"] = os.getenv("CONN_STR")
app.config["SECRET_KEY"] = "verysecretkey" # To be changed

with app.app_context():
    db = PyMongo(current_app).cx["innovise"]
    jwt = JWTManager(current_app)
    fs = GridFS(db)

CORS(app,origins=["http://localhost:3000"],supports_credentials=True)

from api import routes