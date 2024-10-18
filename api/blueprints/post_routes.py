from api import db,app
from flask import Blueprint,jsonify,request
from flask_pymongo import ObjectId
from pymongo.errors import DuplicateKeyError
from flask_jwt_extended import get_jwt_identity,jwt_required
from api.blueprints.user_routes import user_routes 

@user_routes.get("/post/suggestions")
@jwt_required()
def suggest_posts():
    """
        GET /users/post/suggestions
        Returns a list of post suggestions for logged in user. Can't be their own posts.
    """
    current_user = get_jwt_identity()
    user = db.users.find_one({"name":current_user})
    
    own_posts = db.posts.find({"user_id":str(user["_id"])})
    own_posts = [str(x["_id"]) for x in own_posts]
    interests = db.interests.find({"user_id":str(user["_id"])})
    l = [x["tag_id"] for x in interests]
    
    res = db.topics.aggregate([
        {
            "$match" : {
                "post_id": {
                    "$nin": own_posts
                },
                "tag_id" : {
                    "$in" : l
                },
            }
        },
        {
            "$group": {
                "_id" : "$post_id",
                "total" : {"$sum" : 1} 
            }
        },
        {
            "$sort" : {
                "total" : -1
            }
        },
        {
            "$limit":4
        }
    ])


    l = [ObjectId(x["_id"]) for x in res]
    posts = db.posts.find({"_id":{"$in":l}})
    temp = {str(x["_id"]):{a:str(b) for a,b in x.items()} for x in posts}
    posts = [temp[str(i)] for i in l]
    found_posts = []
    for p in posts:    
        t_ids = [ObjectId(x["tag_id"]) for x in db.topics.find({"post_id":str(p["_id"])})]

        post_tags = db.tags.aggregate([
            {
                "$match": {
                    "_id": {
                        "$in" : t_ids
                    }
                }
            }
        ])
        post_tags = [x["name"].title() for x in post_tags]
        d = {x:str(y) for x,y in p.items()}
        d["tags"] = post_tags
        found_posts.append(d)

    return jsonify(payload=found_posts)

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
        r["tags"] = [t["name"].title() for t in tags] 
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
        tags.append(tag.lower())

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