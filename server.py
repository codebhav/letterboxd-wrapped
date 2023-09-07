from io import BytesIO
from flask import (
    Flask,
    redirect,
    request,
    render_template,
    send_file,
    url_for
)
from LBscraper import scraper
from LBscraper import collage as collager


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        return redirect(url_for("collage", username=request.form["username"]))

    return render_template("index.html")


@app.route("/collage")
def collage():
    username = request.args.get("username", "")
    if username:
        return render_template(
            "collage.html",
            username=username
        )
    return "Username not provided."


@app.route("/img")
def img():
    username = request.args.get("username", "")
    if username:
        entries = scraper.get_user_diary_entries(username, 1)
        urls = [e["movie_poster_url"] for e in entries]
        collage_bytesio = BytesIO()
        img_collage = collager.create_collage(urls)
        img_collage.save(collage_bytesio, format="JPEG")
        collage_bytesio.seek(0)
        return send_file(collage_bytesio, mimetype="image/JPG")
    return "Username not provided."


@app.route("/user-diary")
def user_diary():
    username = request.args.get("username", "")
    if username:
        return scraper.get_last_n_days_of_movies_in_diary(username, 30)
    return "Username not provided."
