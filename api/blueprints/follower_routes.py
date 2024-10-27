from api import app,db,fs
from flask import jsonify,redirect,request,url_for
from flask_pymongo import ObjectId
from pymongo.errors import DuplicateKeyError
from flask_jwt_extended import create_access_token,get_jwt_identity,jwt_required
from api.blueprints.user_routes import user_routes 
import base64

@user_routes.post("/following")
@jwt_required()
def manage_following():
    """
        POST /users/following
        Body:
            name: User name to follow/remove
            delete: 0 if create 1 if delete
        Makes current user follow other user
    """

    current_user = get_jwt_identity()
    current_user = db.users.find_one({"name":current_user})

    other_user = request.form.get("name")
    operation = int(request.form.get("delete"))

    other_user = db.users.find_one({"name":other_user})

    if other_user:
        follower_id = str(current_user["_id"])
        followed_id = str(other_user["_id"])

        if operation == 0: # If insertion
            try:
                followed_obj_id = db.followers.insert_one({"follower_id":follower_id, "followed_id": followed_id}).inserted_id
                res = {x:str(y) for x,y in db.followers.find_one({"_id":followed_obj_id}).items()}
                return jsonify({"payload":res}),200

            except DuplicateKeyError as e:
                return jsonify({"msg":"Follower already added!"}),400
            
        else: # if deletion
            num_deleted = db.followers.delete_one({"follower_id":follower_id, "followed_id": followed_id}).deleted_count
            if num_deleted == 1:
                return jsonify(delete=True),200
            
            return jsonify(delete=False),400
    
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
        f_ids = [ObjectId(i["follower_id"]) for i in db.followers.find({"followed_id":str(user["_id"])})]
        follower_data = [{
            "name":x["name"],
            "fullname":x["fullname"],
            "picture":base64.b64encode(fs.get(ObjectId(x["picture"])).read()).decode("utf-8")
        } for x in db.users.find({"_id":{"$in":f_ids}})]

        return jsonify({"payload":follower_data}),200
    
    else:
        return jsonify({"msg":"No such user found"}),404
        
@user_routes.get("/following/<id>")
@jwt_required()
def is_following(id):
    """
        GET /users/following/<id>
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
    
@user_routes.get("/suggestions")
@jwt_required()
def follower_suggestions():
    """
        GET /users/suggestions
    """
    current_user = get_jwt_identity()

    user = db.users.find_one({"name":current_user})
    already_followed = db.followers.find({
        "follower_id": str(user["_id"])
    })

    already_followed = [ObjectId(x["followed_id"]) for x in already_followed]

    u_ids = db.users.aggregate([
        # Stage 1 - Remove all users who are already followed and yourself
        {
            "$match" : {
                "_id" : {
                    "$nin" : already_followed,
                    "$ne" : user["_id"]
                },
            }
        },
        # Stage 2 - Find all matching interests
        { "$unwind" : "$interests" },
        {
            "$match" : {
                "interests" : {
                    "$in": user["interests"]   
                }
            }
        },
        {
            "$group" : {
                "_id" : "$_id",
                "interests" : {"$push" : "$interests"}
            }
        },
        # Stage 3 - Find number of matching interests
        {
            "$project": { 
                "interests" : { "$size" : "$interests" }
            }
        },
        # Stage 4 - Sort and return ids of 4 suggested users
        {
            "$sort" : {
                "interests": -1,
                "_id" : 1
            }
        },
        {
            "$limit":4
        }
    ])

    l = [ObjectId(x["_id"]) for x in u_ids]
    users = db.users.find({"_id":{"$in":l}}) # Find users corresponding to ids. Note: this is not sorted

    temp = {str(x["_id"]):{"name":x["name"],"fullname":x["fullname"],"picture":base64.b64encode(fs.get(ObjectId(x["picture"])).read()).decode("utf-8")} for x in users}
    users = [temp[str(i)] for i in l] # Sorted list of users

    if len(users) == 0: # if no interests provided
        u = db.users.aggregate([
            {
                "$match" : {
                    "_id" : {
                        "$nin" : already_followed,
                        "$ne" : user["_id"]
                    },
                }
            },
            {
                "$limit":4
            }
        ])
        users = [{"name":x["name"],"fullname":x["fullname"],"picture":base64.b64encode(fs.get(ObjectId(x["picture"])).read()).decode("utf-8")} for x in u]
    return jsonify(payload=users),200