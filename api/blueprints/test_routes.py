# File containing sanity checking/testing routes to ensure database live

from api import app,db
from flask import Blueprint,jsonify
test_routes = Blueprint("test_routes", __name__)

@test_routes.route("/",methods=["GET"])
def test():
    """
        GET /test
        Returns name:Dummy if user with name dummy exists
    """
    obj = db.users.find_one({"name":"Dummy"})
    return jsonify({"name":app.config["SECRET_KEY"] })

app.register_blueprint(test_routes,url_prefix="/test")