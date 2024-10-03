from api import app,db
from flask import jsonify,request,redirect
from flask_pymongo import ObjectId
import json

@app.route("/",methods=["GET"])
def test():
    obj = db.users.find_one({"name":"Dummy"})
    return jsonify({"name":obj["name"]})

@app.route("/user/<id>",methods=["GET"])
def get_user(id):
    obj = db.users.find_one({"_id":ObjectId(id)})
    obj = {x:str(y) for x,y in obj.items()}
    return jsonify({"payload":obj})

@app.route("/users",methods=["POST"])
def add_user():
    email = request.form.get("email")
    name = request.form.get("name")
    password = request.form.get("password")

    id = db.users.insert_one({
        "name":name,
        "email":email,
        "password":password
    }).inserted_id

    return redirect(f"/user/{id}")