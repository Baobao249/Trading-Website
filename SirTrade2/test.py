from flask import Flask
import requests

app = Flask(__name__)
@app.route("/")
def home():
    return "<H1>Welcome to OBKD Subject</H1>"