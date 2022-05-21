import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import datetime

from helpers import apology, login_required, list_to_string, string_to_list, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///homade.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET"])
@login_required
def index():
    return render_template("index.html")


@app.route("/Menu", methods=["GET"])
@login_required
def Menu():
        return render_template("products.html")

@app.route("/Reserve", methods=["GET", "POST"])
@login_required
def Reserve():
    id = session["user_id"]
    if request.method=="GET":
        available_slots = db.execute("SELECT * FROM slots WHERE user_id IS NULL")
        return render_template("cart.html", slots=available_slots)

    elif request.method=="POST":
        slot_id = request.form.get("slot")
        db.execute("UPDATE slots SET user_id = :user_id WHERE slot_id = :slot_id", user_id=id, slot_id=slot_id)
        return redirect("/Bookings")

@app.route("/Bookings")
@login_required
def Bookings():
    id = session["user_id"]
    bookings = db.execute("SELECT * FROM slots WHERE user_id = :id", id=id)
    if not bookings:
        flash("You do not have any appointments!")
    return render_template("historys.html", bookings=bookings)

@app.route("/cancel", methods=["GET","POST"])
def cancel():
    if request.method=="GET":
        return render_template("historys.html")
    else:
        slot_id = request.form.get("cancel")
        db.execute("UPDATE slots SET user_id = NULL WHERE slot_id=:slot_id", slot_id=slot_id)
        flash("Reservation cancelled!")
        return redirect ("/Bookings")

@app.route("/Customers_Booking", methods=["GET", "POST"])
def Customers_Booking():
    id = session["user_id"]
    if request.method=="GET":
        slots = db.execute("SELECT * FROM slots WHERE user_id = user_id")
        users = db.execute("SELECT name, contact FROM users WHERE id = id")
        available_slots = db.execute("SELECT * FROM slots WHERE user_id IS NULL")
        return render_template("orders.html", slots=slots, users=users, available_slots=available_slots)

    elif request.method=="POST":
        date = request.form.get("date")
        timeslot = request.form.get("timeslot")

        db.execute("INSERT INTO slots (date, time) VALUES (:date, :timeslot)", date=date, timeslot=timeslot)
        flash("New timeslot created!")
        return render_template("orders.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("name"):
            return apology("must provide name", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE name = ?", request.form.get("name"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        if rows[0]["isAdmin"] == 1:
            session["Admin"] = True

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/Home", methods=["GET"])
@login_required
def Home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("Register.html")

    else:
       name = request.form.get("name")
       contact = request.form.get("name")
       password = request.form.get("password")
       confirmation = request.form.get("confirmation")

        # Ensure username was submitted
       if not name:
           return apology("must provide name", 400)

       if not contact:
           return apology("must provide contact", 400)

        # Ensure password was submitted
       if not password:
           return apology("must provide password", 400)

       if not confirmation:
           return apology("must provide confirm_password", 400)

       if password != confirmation:
           return apology("password confimation wrong", 400)

       hash = generate_password_hash(password)

       new_user = db.execute("INSERT INTO users(name, hash, contact) VALUES(?, ?, ?)", name, hash, contact)

       session["user_id"] = new_user

       return redirect("/")
