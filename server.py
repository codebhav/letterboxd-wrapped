from flask import Flask, redirect, request, render_template, url_for
from LBscraper import scraper


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        return redirect(url_for("collage", username=request.form["username"]))

    return render_template("index.html")


@app.route("/collage/")
@app.route("/collage")
def collage():
    username = request.args.get("username", "")
    if username:
        return render_template(
            "collage.html",
            username=username
        )
    return "Username not provided."


@app.route("/user-diary/")
@app.route("/user-diary")
def user_diary():
    username = request.args.get("username", "")
    if username:
        return scraper.get_user_diary_entries(username, 1)
    return "Username not provided."
