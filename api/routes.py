from api import app,db
from flask import jsonify

@app.route("/",methods=["GET"])
def home():
    obj = db.users.find_one({"name":"Dummy"})

    return jsonify({"name":obj["name"]})