# File containing user related routes

from api import app,db,jwt
from flask import Blueprint,jsonify,redirect,request,url_for
from flask_pymongo import ObjectId
from pymongo.errors import DuplicateKeyError
from flask_jwt_extended import create_access_token,get_jwt_identity,jwt_required

user_routes = Blueprint("user_routes", __name__)

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

    if email and name and password:
        try:
            id = db.users.insert_one({
                "name":name,
                "email":email,
                "password":password
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
        obj = {x:str(y) for x,y in obj.items()}
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
        res = {x:str(y) for x,y in res.items()}
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
        access_token = create_access_token(identity=username)
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


app.register_blueprint(user_routes,url_prefix="/users")