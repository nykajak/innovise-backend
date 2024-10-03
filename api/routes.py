from api import app,db
from flask import jsonify

@app.route("/",methods=["GET"])
def home():
    obj = db.comments.find_one()

    return jsonify({"name":obj["name"]})