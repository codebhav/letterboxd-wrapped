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
                size=request.form["size"],
                hide_shorts= False if request.form.get("shorts", default=False) else True,
                hide_tv= False if request.form.get("tv", default=False) else True,
                hide_docs= False if request.form.get("docs", default=False) else True,
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
    diary_filters = {
        "hide-shorts": True if request.args.get("hide_shorts") == "True" else False,
        "hide-tv": True if request.args.get("hide_tv") == "True" else False,
        "hide-docs":True if request.args.get("hide_docs") == "True" else False
    }
    if username:
        return send_file(
            create_collage(username, size, diary_filters),
            mimetype="image/JPG"
        )
    flash("/img requires the parameters username and size")
    return redirect(url_for("index"))



def create_collage(username, size, diary_filters):
    sizes = {25: (5, 5), 50: (10, 5), 100: (10, 10)}
    collage = BytesIO()
    Collage(LetterboxdUser(username, diary_filters)) \
        .create(sizes[size]) \
        .save(collage, format="JPEG")
    collage.seek(0)
    return collage