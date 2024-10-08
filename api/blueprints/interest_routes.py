from api import db
from flask import jsonify,request
from flask_pymongo import ObjectId
from pymongo.errors import DuplicateKeyError
from flask_jwt_extended import get_jwt_identity,jwt_required
from api.blueprints.user_routes import user_routes 


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
