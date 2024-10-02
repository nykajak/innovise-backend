from api import app,db

@app.route("/",methods=["GET"])
def home():
    return db.comments.find_one()["name"]