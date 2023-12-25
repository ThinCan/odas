from flask import Flask 
from flask_cors import CORS
from flask import request, jsonify, redirect
import sqlite3
from waitress import serve
from flask_jwt_extended import get_jwt_identity, jwt_required, JWTManager, create_access_token, set_access_cookies, get_jwt
from datetime import timedelta

# config =  json.load(open("./config.json", "r"))
app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost*", "https://localhost*"])

app.config["JWT_SECRET_KEY"] = "secret1"
app.config["JWT_COOKIE_SECURE"] = True
# app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(seconds=5)
jwt = JWTManager(app)

db = sqlite3.connect("jwt_blacklist_db", check_same_thread=False)
dbcur = db.cursor()
dbcur.execute("""
CREATE TABLE IF NOT EXISTS revoked_jwt(jti)  
""")
dbcur.execute("""
CREATE TABLE IF NOT EXISTS users(
    email TEXT, 
    password TEXT
)  
""")

@jwt.token_in_blocklist_loader
def abc(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    res = dbcur.execute("SELECT jti FROM revoked_jwt WHERE jti=?", (jti,)).fetchone()
    print(res)
    return res is not None

@app.get("/api/<id>")
def index(id):
    print(id)
    return id, 200

@app.post("/api/login")
def login():
    json_data = request.get_json()
    print(json_data)
    at = create_access_token(identity=json_data["email"])
    response = jsonify({"data": "login successful"})
    print("Acess token: " + at)
    set_access_cookies(response, at)
    return response

@app.get("/api/logout")
@jwt_required(locations=["cookies"])
def logout():
    cu = get_jwt()["jti"]
    dbcur.execute("INSERT INTO revoked_jwt VALUES (?)", (cu,))
    db.commit()
    
    return "OK", 200
    

@app.get("/api/jwt")
@jwt_required(locations=["cookies"])
def protected():
    print("a")
    cu = get_jwt_identity()
    response = jsonify(logged_in_as=cu)

    return response, 200

@app.post("/api/register/validate")
def register_validate():
    json = request.get_json()
    result = dbcur.execute("SELECT COUNT(*) FROM users WHERE email == ?", (json["email"],)).fetchone()[0]
    if(result != 0):
        return {"message": "Incorrect email or password.", "result": False}, 401
    return {"message": "Everything's good.", "result": True}, 200


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8080, url_scheme="https")

    # con = sqlite3.connect("tutorial.db")
    # cur = con.cursor()
    # cur.execute("CREATE TABLE movie(title, year, score)")
    # cur.execute("INSERT into movie values ('a', 'b', 'c')")
    # return app
