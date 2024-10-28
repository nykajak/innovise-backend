from api import db
from flask import jsonify,request
from flask_pymongo import ObjectId
from pymongo.errors import DuplicateKeyError,BulkWriteError
from flask_jwt_extended import get_jwt_identity,jwt_required
from api.blueprints.user_routes import user_routes 

@user_routes.get("/tags")
def all_interests():
    """
        GET /users/tags
        Return set of all interests
    """
    payload = []
    for x in db.tags.find():
        payload.append(x["name"].title())
    payload.sort()
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
    
    interests = []
    for i in range(1,n+1):
        interest = request.form.get(f"interest[{i}]")
        interests.append(interest.lower())
    
    t_ids = [str(x["_id"]) for x in db.tags.find({"name":{
        "$in" : interests
    }})]
    
    # Warning - Bad Pattern! (set)
    db.users.update_one({"_id":current_user["_id"]},{"$set":{"interests":list(set(current_user["interests"]+t_ids))}})
    
    return jsonify(payload=True),200

@user_routes.get("<id>/interests")
def see_interests(id):
    """
        GET /users/<id>/interests
        Returns list of interests
    """

    user = db.users.find_one({"_id":ObjectId(id)})
    if user:
        interests = [ObjectId(x) for x in user["interests"]]
        interest_names = [x["name"].title() for x in db.tags.find({"_id":{"$in":interests}})]

        return jsonify({"payload":interest_names}),200
    
    else:
        return jsonify({"msg":"No such user found"}),404
