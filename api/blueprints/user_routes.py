# File containing user related routes

from api import app,db,jwt
from flask import Blueprint,jsonify,redirect,request,url_for
from flask_pymongo import ObjectId
from pymongo.errors import DuplicateKeyError
from flask_jwt_extended import create_access_token,get_jwt_identity,jwt_required
from datetime import timedelta 

user_routes = Blueprint("user_routes", __name__)


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


@user_routes.post("/interests")
@jwt_required()
def add_interest():
    """
        POST /users/interests
        Add interest to user
    """

    current_user = get_jwt_identity()
    current_user = db.users.find_one({"name":current_user})

    interest = request.form.get("interest")
    interest = db.tags.find_one({"name":interest})

    if interest:
        user_id = str(current_user["_id"])
        tag_id = str(interest["_id"])

        try:
            interest_id = db.interests.insert_one({"user_id":user_id, "tag_id": tag_id}).inserted_id
            res = {x:str(y) for x,y in db.interests.find_one({"_id":interest_id}).items()}
            return jsonify({"payload":res}),200

        except DuplicateKeyError as e:
            return jsonify({"msg":"Interest already added!"}),200
    
    else:
        return jsonify({"msg":"Interest not found!"}),404

@user_routes.get("<id>/interests")
def see_interests(id):
    """
        GET /users/<id>/interests
        Returns list of interests
    """

    user = db.users.find_one({"_id":ObjectId(id)})
    if user:
        interests = db.interests.find({"user_id":str(user["_id"])})
        interest_names = []

        for i in interests:
            res = db.tags.find_one({"_id":ObjectId(i["tag_id"])})
            if res:
                interest_names.append(res["name"])

        return jsonify({"payload":interest_names}),200
    
    else:
        return jsonify({"msg":"No such user found"}),404

@user_routes.post("/following")
@jwt_required()
def add_following():
    """
        POST /users/following
        Add interest to user
    """

    current_user = get_jwt_identity()
    current_user = db.users.find_one({"name":current_user})

    other_user = request.form.get("name")
    other_user = db.users.find_one({"name":other_user})

    if other_user:
        follower_id = str(current_user["_id"])
        followed_id = str(other_user["_id"])

        try:
            followed_obj_id = db.followers.insert_one({"follower_id":follower_id, "followed_id": followed_id}).inserted_id
            res = {x:str(y) for x,y in db.followers.find_one({"_id":followed_obj_id}).items()}
            return jsonify({"payload":res}),200

        except DuplicateKeyError as e:
            return jsonify({"msg":"Follower already added!"}),400
    
    else:
        return jsonify({"msg":"User not found!"}),404
    
@user_routes.get("/followers")
@jwt_required()
def see_followers():
    """
        GET /users/<id>/followers
        Returns list of followers
    """
    current_user = get_jwt_identity()
    user = db.users.find_one({"name":current_user})
    if user:
        followers = db.followers.find({"followed_id":str(user["_id"])})
        follower_names = []

        for i in followers:
            res = db.users.find_one({"_id":ObjectId(i["follower_id"])})
            if res:
                follower_names.append(res["name"])

        return jsonify({"payload":follower_names}),200
    
    else:
        return jsonify({"msg":"No such user found"}),404


app.register_blueprint(user_routes,url_prefix="/users")