from api import db,app,fs
from flask import Blueprint,jsonify,request
from flask_pymongo import ObjectId
from pymongo.errors import DuplicateKeyError
from flask_jwt_extended import get_jwt_identity,jwt_required
from api.blueprints.user_routes import user_routes 
import base64


def fetch_posts(user,p_ids,page=1,count=10):
    page = int(page)
    p_ids = p_ids[(page - 1) * count:(page - 1) * count + 10]
    posts = db.posts.aggregate([
        {
            "$match" : {
                "_id":{"$in":p_ids}
            }
        }
    ])
    temp = {str(p["_id"]):p for p in posts}
    posts = [temp[str(i)] for i in p_ids]

    mapping = {}

    found_posts = []
    for p in posts:    
        t_ids = [ObjectId(x) for x in p["topics"]]

        post_tags = db.tags.find({"_id": {"$in" : t_ids}})
        post_tags = [x["name"].title() for x in post_tags]

        d = {x:y for x,y in p.items()}
        d["_id"] = str(d["_id"])

        specific_user = db.users.find_one({"_id" : ObjectId(d["user_id"])})
        d["user_name"] = specific_user["name"]
        d["user_fullname"] = specific_user["fullname"]
        d["user_bio"] = specific_user["bio"]

        if str(specific_user["_id"]) not in mapping:
            mapping[str(specific_user["_id"])] = base64.b64encode(fs.get(ObjectId(specific_user["picture"])).read()).decode("utf-8")

        d["tags"] = post_tags
        del d["topics"]
        links = []
        if "link1" in d:
            links.append(d["link1"])
            del d["link1"]
        
        if "link2" in d:
            links.append(d["link2"])
            del d["link2"]

        d["links"] = links

        likes = db.likes.count_documents({"post_id" : str(d["_id"])})
        d["likes"] = likes

        liked = db.likes.count_documents({"user_id" : str(user["_id"]),"post_id" : str(d["_id"])})
        d["has_liked"] = 1 if liked > 0 else 0
        found_posts.append(d)

    return found_posts,mapping

@app.delete("/post/<id>")
@jwt_required()
def delete_posts(id):
    """
        DELETE /post/<id>
        Deletes a post with given id.
    """
    current_user = get_jwt_identity()
    user = db.users.find_one({"name":current_user})
    
    count = db.posts.delete_one({"user_id":str(user["_id"]),"_id":ObjectId(id)}).deleted_count
    if count == 0:
        return jsonify(msg="Insufficient permissions / unavailable resource"),400
    
    db.likes.delete_many({"post_id":id})

    return jsonify(payload=True),200

@user_routes.get("/post/suggestions")
@jwt_required()
def suggest_posts():
    """
        GET /users/post/suggestions
        Returns a list of post suggestions for logged in user. Can't be their own posts.
        args:
            page = page no
    """
    current_user = get_jwt_identity()
    user = db.users.find_one({"name":current_user})
    
    page = request.args.get("page",1)
    own_posts = db.posts.find({"user_id":str(user["_id"])})
    own_posts = [x["_id"] for x in own_posts]

    res = db.posts.aggregate([
        # Stage 1 - Remove all own posts
        {
            "$match" : {
                "_id": {
                    "$nin": own_posts
                }
            }
        },
        # Stage 2 - Find all matching interests
        { "$unwind" : "$topics" },
        {
            "$match" : {
                "topics" : {
                    "$in": user["interests"]   
                }
            }
        },
        {
            "$group" : {
                "_id" : "$_id",
                "topics" : {"$push" : "$topics"}
            }
        },
        # Stage 3 - Find number of matching interests
        {
            "$project": { 
                "topics" : { "$size" : "$topics" }
            }
        },
        # Stage 4 - Sort and return posts
        {
            "$sort" : {
                "topics": -1,
                "_id" : 1
            }
        },
    ])


    l = [ObjectId(x["_id"]) for x in res]

    found_posts,mapping = fetch_posts(user,l,page=page)
    return jsonify(payload=found_posts,mapping=mapping, pages = len(l))

@user_routes.get("/post/<uid>")
@jwt_required()
def see_posts(uid):
    """
        GET /user/post/<uid>
        Returns all posts by a user given user id
        args
            page=page no
    """

    current_user = get_jwt_identity()
    user = db.users.find_one({"name":current_user})
    page = request.args.get("page",1)
    res = db.posts.aggregate([
        {
            "$match": {
                "user_id": {
                    "$eq": uid
                }
            }
        }
    ])  
    l = [x["_id"] for x in res]
    found_posts,mapping = fetch_posts(user,l,page=page)
    return jsonify(payload=found_posts,mapping=mapping, pages = len(l))

@app.get("/post/<id>")
@jwt_required()
def see_specific_post(id):
    """
        GET /post/<id>
        Returns a specific post
    """

    current_user = get_jwt_identity()
    user = db.users.find_one({"name":current_user})
    res,mapping = fetch_posts(user,[ObjectId(id)])

    return jsonify(payload=res,mapping=mapping,pages=1),200

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
            link[1] = first link
            link[2] = second link
        Adds a new post given
    """
    current_user = get_jwt_identity()
    user = db.users.find_one({"name":current_user})

    content =request.form.get("content")
    _type  =request.form.get("type")
    num = int(request.form.get("num"))
    link1 = request.form.get("link[1]",None)
    link2 = request.form.get("link[2]",None)

    obj = {
        "user_id": str(user["_id"]),
        "content": content,
        "type" : _type,
    }

    if link1:
        obj["link1"] = link1
    if link2:
        obj["link2"] = link2

    tags = []
    for i in range(1,num+1):
        tag = request.form.get(f"tag[{i}]")
        tags.append(tag.lower())

    t_docs = [str(x["_id"]) for x in db.tags.find({"name": { "$in" : tags}})]
    obj["topics"] = t_docs
    p_id = db.posts.insert_one(obj).inserted_id        

    return jsonify(payload=str(p_id)),200

@user_routes.post("/like")
@jwt_required()
def manage_like():
    """
        POST /user/like
        Body:
            post_id = id of post to like
            like = 1 if like 0 to remove like
    """

    current_user = get_jwt_identity()
    user = db.users.find_one({"name":current_user})

    post_id = request.form.get("post_id",None)
    mode = request.form.get("like",None)

    if post_id is None or mode is None:
        return jsonify(msg="Malformed request!"),400
    
    if int(mode) == 1:
        try:
            db.likes.insert_one({
                "user_id":str(user["_id"]),
                "post_id":post_id,
            })

            return jsonify(payload=True),200
        
        except DuplicateKeyError as e:
            return jsonify(msg="Liked an already liked post!"),400
    
    else:
        db.likes.delete_one({
                "user_id":str(user["_id"]),
                "post_id":post_id,
        })

    return jsonify(payload=True),200

@user_routes.post("/post/filter")
@jwt_required()
def filter_posts():
    """
        Returns filtered posts
        POST /users/post/filter
        Body:
            type: Type of post
            num: Number of tags
            tag[1] : First tag
            tag[2] : Second tag
            owner : name of user to filter. Leave blank otherwise
            following: 1 if filter by following leave blank otherwise
            page: page no
    """
    current_user = get_jwt_identity()
    user = db.users.find_one({"name":current_user})

    _type = request.form.get("type",None)
    num = int(request.form.get("num",0))
    owner = request.form.get("owner",None)
    following = int(request.form.get("following",0))
    tags = []
    
    if owner is None and following == 0:
        own_posts = db.posts.find({"user_id":str(user["_id"])})
        own_posts = [x["_id"] for x in own_posts]
        pipeline = [
            {
                "$match" : {"_id": {"$nin": own_posts}}
            }
        ]

    elif owner:
        target_user = db.users.find_one({"_id":ObjectId(owner)})
        if target_user is None:
            return jsonify(msg="No such user found"),400
        
        owned_posts = db.posts.find({"user_id":str(target_user["_id"])})
        owned_posts = [x["_id"] for x in owned_posts]
        pipeline = [
            {
                "$match" : {"_id": {"$in": owned_posts}}
            }
        ]
    
    elif following == 1:
        following = [ObjectId(x["followed_id"]) for x in db.followers.find({"follower_id":str(user["_id"])})]
        target_users = [str(x["_id"]) for x in db.users.find({"_id":{"$in":following}})]

        owned_posts = db.posts.find({"user_id":{"$in":target_users}})
        owned_posts = [x["_id"] for x in owned_posts]
        pipeline = [
            {
                "$match" : {"_id": {"$in": owned_posts}}
            }
        ]

    if _type:
        pipeline.append({
            "$match" : {"type": _type.lower()}
        })
    
    if num > 0:
        tags = []
        for i in range(num):
            tags.append(request.form.get(f"tag[{i+1}]").lower())
        
        t_ids = [str(x["_id"]) for x in db.tags.find({"name": { "$in" : tags}})]

        pipeline.extend([
            {
                "$unwind" : "$topics"
            },
            {
                "$match" : {
                    "topics" : {
                        "$in" : t_ids
                    }
                }
            },
            {
                "$group" : {
                    "_id" : "$_id",
                    "topics" : {"$push" : "$topics"}
                }
            },
            {
                "$project": { 
                    "topics" : { "$size" : "$topics" }
                }
            },
            {
                "$match" : {
                    "topics" : len(t_ids)
                }
            }
        ])
    res = db.posts.aggregate(pipeline)
    p_ids = [x["_id"] for x in res]
    posts,mapping = fetch_posts(user,p_ids,page = request.form.get("page",1))
    return jsonify(payload=posts,mapping=mapping,pages=len(p_ids)),200