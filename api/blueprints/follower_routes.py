from api import app,db,jwt
from flask import jsonify,redirect,request,url_for
from flask_pymongo import ObjectId
from pymongo.errors import DuplicateKeyError
from flask_jwt_extended import create_access_token,get_jwt_identity,jwt_required
from api.blueprints.user_routes import user_routes 


@user_routes.post("/following")
@jwt_required()
def add_following():
    """
        POST /users/following
        Makes current user follow other user
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
    
@user_routes.get("/following/<id>")
@jwt_required()
def is_following(id):
    """
        GET /users/followers/<id>
        Returns true if current user follows user
    """

    current_user = get_jwt_identity()
    user = db.users.find_one({"name":current_user})

    if user:
        following = db.followers.find_one({"follower_id":str(user["_id"]),"followed_id":id})
        if following:
            return jsonify(payload=True),200
        
        return jsonify(payload=False),200
    
    else:
        return jsonify({"msg":"No such user found"}),404
