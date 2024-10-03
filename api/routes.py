from api import app,db
from flask import jsonify,request
import json

@app.route("/",methods=["GET"])
def test():
    obj = db.users.find_one({"name":"Dummy"})
    return jsonify({"name":obj["name"]})

# @app.route("/users",methods=["POST"])
# def add_user():
#     print(request.form)
#     return jsonify(request.form.to_dict())