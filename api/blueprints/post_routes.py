from api import db,app
from flask import Blueprint,jsonify,request
from flask_pymongo import ObjectId
from pymongo.errors import DuplicateKeyError
from flask_jwt_extended import get_jwt_identity,jwt_required
from api.blueprints.user_routes import user_routes 

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
    
    db.topics.delete_many({"post_id":id})
    db.likes.delete_many({"post_id":id})

    return jsonify(payload=True),200

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

    return jsonify(payload=found_posts)

@user_routes.get("/post/<uid>")
@jwt_required()
def see_posts(uid):
    """
        GET /user/post/<uid>
        Returns all posts by a user given user id
    """

    current_user = get_jwt_identity()
    user = db.users.find_one({"name":current_user})

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
        links = []
        if "link1" in r:
            links.append(r["link1"])
            del r["link1"]
        
        if "link2" in r:
            links.append(r["link2"])
            del r["link2"]

        r["links"] = links

        likes = db.likes.count_documents({"post_id" : str(r["_id"])})
        r["likes"] = likes

        liked = db.likes.count_documents({"user_id" : str(user["_id"]),"post_id" : str(r["_id"])})
        r["has_liked"] = 1 if liked > 0 else 0
        
        res[i] = r


    return jsonify(payload=res),200

@app.get("/post/<id>")
@jwt_required()
def see_specific_post(id):
    """
        GET /post/<id>
        Returns a specific post
    """

    current_user = get_jwt_identity()
    user = db.users.find_one({"name":current_user})

    post = db.posts.find_one({"_id":ObjectId(id)})
    res = {x:str(y) for x,y in post.items()}

    t_ids = [ObjectId(x["tag_id"]) for x in db.topics.find({"post_id":id})]
    tags = [x["name"].title() for x in db.tags.find({"_id" : {"$in":t_ids}})]
    res["tags"]=tags

    likes = db.likes.count_documents({"post_id":id})
    res["likes"]=likes

    has_liked = 1 if db.likes.count_documents({"post_id":id,"user_id":str(user["_id"])}) > 0 else 0
    res["has_liked"]=has_liked

    links = []
    if "link1" in res:
        links.append(res["link1"])
        del res["link1"]
    
    if "link2" in res:
        links.append(res["link2"])
        del res["link2"]

    res["links"] = links

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

    p_id = db.posts.insert_one(obj).inserted_id        
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