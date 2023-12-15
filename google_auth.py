
import os
import pathlib
from flask import Flask, session, abort, redirect, request as flask_request  # Rename 'request' to 'flask_request'
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
import requests as http_requests  # Rename 'requests' to something else
from route import app 
from route import dashboard
from route import signin




app.secret_key = "sourcemonq@1234"
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

goole_client_id ="710643255963-6lv624ak9v7kdjmahfcdc4stnasmcgc3.apps.googleusercontent.com"    # this is dowload in google console
client_secrets_file = os.path.join(pathlib.Path(__file__).parents[0], "client_secret.json")




flow = Flow.from_client_secrets_file(             # it should be name of same in downloading of google file
                 client_secrets_file=client_secrets_file,
                 scopes=["https://www.googleapis.com/auth/userinfo.profile","https://www.googleapis.com/auth/userinfo.email","openid"],
                 redirect_uri="http://127.0.0.1:5000/callback")





def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:          #it is useing for the authorization 
            return abort(401)                    # if it is own user or not 
        else :
            return function(*args, **kwargs)
    return wrapper


@app.route("/login")  # Add a leading slash
def login():
    authorization_url, state =flow.authorization_url()
    session["state"]=state
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=flask_request.url, session=http_requests.Session())  # Use flask_request and http_requests

    if not session["state"] == flask_request.args["state"]:
        abort(500)      # state does not match

    credentials = flow.credentials
    access_token = credentials.token  # Extract the access token

    # Use the access token to verify the ID token
    Id_info = id_token.verify_oauth2_token(
        id_token=credentials.id_token,
        request=google.auth.transport.requests.Request(),  # Use google.auth.transport.requests.Request()
        audience=goole_client_id,
    )

    session["google_id"] = Id_info.get("sub")
    session["name"] = Id_info.get("name")
    return redirect(dashboard)




@app.route("/logout")  # Add a leading slash
def logout():
    session.clear()
    return redirect(signin)


# @app.route("/home")  # Add a leading slash
# def home():
#     return "hello world"



# @app.route("/inside")  # Add a leading slash
# @login_is_required     # Is is the wapper function for the authication 
# def inside():
#     return "you are in your id"

