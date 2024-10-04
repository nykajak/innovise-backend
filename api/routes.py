from api import app,db,jwt
from flask import jsonify,request,redirect
from flask_pymongo import ObjectId
from flask_jwt_extended import create_access_token,get_jwt_identity,jwt_required

@app.route("/",methods=["GET"])
def test():
    obj = db.users.find_one({"name":"Dummy"})
    return jsonify({"name":obj["name"]})

@app.route("/test",methods=["GET"])
@jwt_required()
def test2():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", None)
    password = request.form.get("password", None)

    user = db.users.find_one({"name":username})
    if user and user["password"] == password:
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token)
    
    return jsonify({"msg": "Bad username or password"}), 401

@app.route("/users",methods=["GET"])
def all_users():
    users = db.users.find()
    return jsonify({"payload":[str(u["_id"]) for u in users]})

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