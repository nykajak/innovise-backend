from api import db
from flask import jsonify,request
from flask_pymongo import ObjectId
from pymongo.errors import DuplicateKeyError
from flask_jwt_extended import get_jwt_identity,jwt_required
from api.blueprints.user_routes import user_routes 

@user_routes.get("/tags")
def all_interests():
    """
        Return set of all interests
    """
    payload = []
    for x in db.tags.find():
        payload.append(x["name"].title())
    return jsonify(payload=payload)


@user_routes.post("/interests")
@jwt_required()
def add_interest():
    """
        POST /users/interests
        Body:
            num: Integer number of entries
            interest[1]: First Interest
            interest[2]: Second interest
            ....
        Add interest to user
    """

    current_user = get_jwt_identity()
    current_user = db.users.find_one({"name":current_user})

    n = int(request.form.get("num"))
    num_success = 0
    for i in range(1,n+1):
        interest = request.form.get(f"interest[{i}]")
        interest = db.tags.find_one({"name":interest.lower()})

        if interest:
            user_id = str(current_user["_id"])
            tag_id = str(interest["_id"])

            try:
                interest_id = db.interests.insert_one({"user_id":user_id, "tag_id": tag_id}).inserted_id
                res = {x:str(y) for x,y in db.interests.find_one({"_id":interest_id}).items()}
                num_success += 1

            except DuplicateKeyError as e:
                pass
    
    return jsonify(payload=num_success),200

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
                interest_names.append(res["name"].title())

        return jsonify({"payload":interest_names}),200
    
    else:
        return jsonify({"msg":"No such user found"}),404
