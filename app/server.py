from io import BytesIO

from flask import (
    Flask,
    flash,
    redirect,
    request,
    render_template,
    send_file,
    url_for
)

from letterboxd_scraper import LetterboxdUser, Collage

app = Flask(__name__)
app.secret_key = "change this later"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        return redirect(
            url_for(
                "collage",
                username=request.form["username"],
                size=request.form["size"]
        ))
    return render_template("index.html")


@app.route("/collage")
def collage():
    username = request.args.get("username", "")
    size = request.args.get("size", 25)
    if username:
        return render_template(
            "collage.html",
            username=username,
            size=size
        )
    flash("Username not provided.")
    return redirect(url_for("index"))


@app.route("/img")
def img():
    username = request.args.get("username", "")
    size = int(request.args.get("size", 25))
    if username:
        return send_file(create_collage(username, size), mimetype="image/JPG")
    flash("/img requires the parameters username and size")
    return redirect(url_for("index"))



def create_collage(username, size):
    sizes = {25: (5, 5), 50: (10, 5), 100: (10, 10)}
    collage = BytesIO()
    Collage(LetterboxdUser(username)) \
        .create(sizes[size]) \
        .save(collage, format="JPEG")
    collage.seek(0)
    return collage