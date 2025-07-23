from io import BytesIO
import traceback
from datetime import datetime
from calendar import month_name

from flask import (
    Flask,
    flash,
    redirect,
    request,
    render_template,
    send_file,
    url_for,
    jsonify
)

from letterboxd_scraper import LetterboxdUser, LetterboxdWrapped

app = Flask(__name__)
app.secret_key = "letterboxd-wrapped-secret-key"

@app.route("/", methods=["GET", "POST"])
def index():
    current_month = datetime.now().month
    current_year = datetime.now().year  # Back to current year
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        if not username:
            flash("Please enter a username")
            months = [(i, month_name[i]) for i in range(1, 13)]
            years = list(range(current_year, current_year - 5, -1))
            return render_template("wrapped_index.html", 
                                 months=months, 
                                 years=years,
                                 current_month=current_month,
                                 current_year=current_year)
        
        month = int(request.form.get("month", current_month))
        year = int(request.form.get("year", current_year))
            
        return redirect(
            url_for(
                "wrapped",
                username=username,
                month=month,
                year=year
        ))
    
    # Prepare month options for the form
    months = [(i, month_name[i]) for i in range(1, 13)]
    years = list(range(current_year, current_year - 5, -1))  # Current year to 5 years back
    
    return render_template("wrapped_index.html", 
                         months=months, 
                         years=years,
                         current_month=current_month,
                         current_year=current_year)

@app.route("/wrapped")
def wrapped():
    username = request.args.get("username", "").strip()
    month = int(request.args.get("month", datetime.now().month))
    year = int(request.args.get("year", datetime.now().year))
    
    if username:
        return render_template(
            "wrapped_result.html",
            username=username,
            month=month,
            year=year,
            month_name=month_name[month]
        )
    
    flash("Username not provided.")
    return redirect(url_for("index"))

@app.route("/wrapped-img")
def wrapped_img():
    username = request.args.get("username", "").strip()
    if not username:
        return jsonify({"error": "Username is required"}), 400
        
    try:
        month = int(request.args.get("month", datetime.now().month))
        year = int(request.args.get("year", datetime.now().year))
        
        wrapped_io = create_wrapped_image(username, month, year)
        return send_file(
            wrapped_io,
            mimetype="image/jpeg",
            as_attachment=False
        )
    except Exception as e:
        print(f"Error creating wrapped image: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

def create_wrapped_image(username, month, year):
    wrapped_io = BytesIO()
    
    try:
        user = LetterboxdUser(username)
        wrapped = LetterboxdWrapped(user, month=month, year=year)
        wrapped_image = wrapped.create()
        wrapped_image.save(wrapped_io, format="JPEG", quality=95)
        wrapped_io.seek(0)
        return wrapped_io
    except Exception as e:
        print(f"Error in create_wrapped_image: {e}")
        raise

if __name__ == "__main__":
    app.run(debug=True)