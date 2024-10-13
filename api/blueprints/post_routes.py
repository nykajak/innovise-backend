from api import db,app
from flask import Blueprint,jsonify,request
from flask_pymongo import ObjectId
from pymongo.errors import DuplicateKeyError
from flask_jwt_extended import get_jwt_identity,jwt_required
from api.blueprints.user_routes import user_routes 

# post_routes = Blueprint("post_routes", __name__)

# @post_routes.get("/<pid>")
# def see_specific_post(pid):
#     """
#         GET /post/<pid>
#         Returns a specific post
#     """

#     res = db.posts.aggregate([
#         {
#             "$match": {
#                 "_id": {
#                     "$eq": ObjectId(pid)
#                 }
#             }  
#         },
#         {
#             "$lookup": {
#                 "from" :
#             }
#         }
#     ])

@user_routes.get("/post/<uid>")
def see_posts(uid):
    """
        GET /user/post/<uid>
        Returns all posts by a user given user id
    """
    res = db.posts.aggregate([
        {
            "$match": {
                "user_id": {
                    "$eq": uid
                }
            }
        }
    ])  
    res = [{x:str(y) for x,y in z.items()} for z in res]
    for i in range(len(res)):
        r = res[i]
        tags = db.topics.aggregate([
            {
                "$match": {
                    "post_id" : {
                        "$eq" : r["_id"]
                    }
                }
            }
        ])
        l = [ObjectId(x["tag_id"]) for x in tags]
        tags = db.tags.aggregate([
            {
                "$match": {
                    "_id" : {
                        "$in" : l
                    }
                }
            }
        ])
        r["tags"] = [t["name"] for t in tags] 
        res[i] = r


    return jsonify(payload=res),200

@user_routes.post("/post")
@jwt_required()
def add_post():
    """
        POST /user/post
        Body:
            num = number of tags
            tag[1] = First tag
            tag[2] = second tag and so on
            content = content
            type = intership/project etc
        Adds a new post given
    """
    current_user = get_jwt_identity()
    user = db.users.find_one({"name":current_user})

    content =request.form.get("content")
    _type  =request.form.get("type")
    num = int(request.form.get("num"))

    p_id = db.posts.insert_one(
            {
                "user_id": str(user["_id"]),
                "content": content,
                "type" : _type
            }
        ).inserted_id
    
    tags = []
    for i in range(1,num+1):
        tag = request.form.get(f"tag[{i}]")
        tags.append(tag)

    t_docs = db.tags.aggregate([
        {
            "$match" : {
                "name": {
                    "$in" : tags
                }
            }
        }
    ])

    to_insert = []
    for t in t_docs:
        to_insert.append(
            {
                "post_id" : str(p_id),
                "tag_id" : str(t["_id"])
            }
        )


    t_ids = db.topics.insert_many(
            to_insert, ordered=False
        ).inserted_ids

    return jsonify(payload=len(t_ids)),200

# app.register_blueprint(post_routes,url_prefix="/post")