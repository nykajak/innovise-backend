# File containing user related routes

from api import app,db,jwt
from flask import Blueprint,jsonify,redirect,request,url_for
from flask_pymongo import ObjectId
from pymongo.errors import DuplicateKeyError
from flask_jwt_extended import create_access_token,get_jwt_identity,jwt_required,get_jwt
from datetime import timedelta 

user_routes = Blueprint("user_routes", __name__)

blockList = set()

@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload):
    return jwt_payload["jti"] in blockList

@user_routes.get("/name/<name>")
def get_id(name):
    """
        GET /users/name/<name>
        Returns id of user with name
    """

    obj = db.users.find_one({"name":name})
    if obj:
        obj = {x:str(y) for x,y in obj.items() if x in ["name","fullname", "bio", "_id"]}
        return jsonify({"payload":obj}),200
    else:
        return jsonify({"msg":"User not found!"}), 404

@user_routes.get("/")
def all_users():
    """
        GET /users
        View all users. 
    """
    users = db.users.find()
    return jsonify({"payload":[str(u["_id"]) for u in users]}),200

@user_routes.post("/")
def add_user():
    """
        POST /users 
        Add (email,name,password in request body)
        Adds a user with given data. 
    """
    email = request.form.get("email",None)
    name = request.form.get("name",None)
    password = request.form.get("password",None)
    fullname = request.form.get("fullname",name)
    bio = request.form.get("bio",None)

    if email and name and password:
        try:
            if bio:
                id = db.users.insert_one({
                    "name":name,
                    "email":email,
                    "password":password,
                    "fullname":fullname,
                    "bio":bio
                }).inserted_id

            else:
                id = db.users.insert_one({
                    "name":name,
                    "email":email,
                    "password":password,
                    "fullname":fullname,
                    "bio":"None"
                }).inserted_id

            return redirect(url_for("user_routes.get_user",id=id))

        except DuplicateKeyError as e:
            field = list(e._OperationFailure__details["keyValue"].keys())[0]
            return jsonify({"msg":"Duplicate user!", "field":field}), 400
    
    return jsonify({"msg":"Malformed Request!"}), 400

@user_routes.get("/<id>")
def get_user(id):
    """
        GET /users/<id>
        Finds a user with given id. 
    """
    obj = db.users.find_one({"_id":ObjectId(id)})
    if obj:
        obj = {x:str(y) for x,y in obj.items() if x in ["name","fullname", "bio", "_id"]}
        return jsonify({"payload":obj}),200
    else:
        return jsonify({"msg":"User not found!"}), 404

@user_routes.delete("/<id>")
def delete_user(id):
    """
        DELETE /users/<id> 
        Deletes a user with given id.
    """

    res = db.users.find_one_and_delete({"_id":ObjectId(id)})
    if res:
        res = {x:str(y) for x,y in res.items() if x in ["name","fullname", "bio", "_id"]}
        return {"payload":res},200
    
    return jsonify({"msg":"User not found!"}), 404

@user_routes.post("/login")
def login():
    """
        POST /users/login
        Returns JWT for user.
    """
    username = request.form.get("username", None)
    password = request.form.get("password", None)

    user = db.users.find_one({"name":username})
    if user and user["password"] == password:
        access_token = create_access_token(identity=username,expires_delta=timedelta(hours=1))
        return jsonify(access_token=access_token),200
    
    return jsonify({"msg": "Incorrect username or password"}), 401

@user_routes.get("/logout")
@jwt_required()
def logout():
    """
        GET /users/logout
        Add Bearer Token: JWT token
        Logout current user. 
    """
    jti = get_jwt()["jti"]
    blockList.add(jti)
    return jsonify(payload=get_jwt()["sub"]),200

@user_routes.get("/current")
@jwt_required()
def see_current():
    """
        GET /users/current
        Add Bearer Token: JWT token
        See current user. 
    """
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200


import api.blueprints.interest_routes 
import api.blueprints.follower_routes
import api.blueprints.post_routes
app.register_blueprint(user_routes,url_prefix="/users")