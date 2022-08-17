import os
from validate import Validate
from buy import buy_shares
from cs50 import SQL
import datetime
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from get_index import get_index
from helpers import apology, login_required, lookup, usd
from sell import *
from dotenv import load_dotenv


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


validate = Validate(db)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    datas, user_cash, total_cash = get_index()
    datas = sorted(datas.items())
    user_cash = db.execute("""
        SELECT cash FROM users WHERE id = ?
    """, session['user_id'])[0]['cash']

    total_cash = user_cash + total_cash
    return render_template("index.html",
                           datas=datas,
                           user_cash=user_cash,
                           total_cash=total_cash)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get('shares')
        message = validate.validate_buy(symbol, shares)
        if message:
            return apology(message, 400)
        data = lookup(symbol)
        message = validate.validate_cash_and_price(shares, data)
        if message:
            return apology(message, 400)
        cash, total = buy_shares(symbol, shares, data, db)
        cache_user_symbols(symbol)
        flash('Bought!', 'success')

        return render_template("bought.html", total=total, cash=cash)
    return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    column = ['Symbol', 'Shares', 'Price', 'Transacted']
    data = db.execute("""
        SELECT * FROM history WHERE user_id = ?
    """, session['user_id'])
    return render_template("history.html", datas=data, columns=column)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        data = lookup(symbol)
        if data:
            return render_template("quote.html", result=True, data=data)
        return apology("Invalid symbol", 400)
    return render_template("quote.html", result=False)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        pass1 = request.form.get("password")
        pass2 = request.form.get("confirmation")
        message = validate.validate_user_pass(username, pass1, pass2)
        if message:
            return apology(message)

        db.execute("""
            INSERT INTO users(username, hash) VALUES
            (?, ?)
        """, username, generate_password_hash(pass1))
        return redirect("/")

    return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    options = get_user_symbol()
    if request.method == "POST":
        shares = request.form.get("shares")
        symbol = request.form.get("symbol")
        #if symbol:
        message = validate.validate_sell(symbol, shares)
        if message:
                return apology(message)
        else:
                shares = int(shares)
        cash, total = add_reduced_shares(-shares, symbol, db)
        remove_cache(symbol)
        return render_template("sell2.html", cash=cash, total=total)
    return render_template("sell.html", options=options)


@app.route("/reset_password", methods=["GET", "POST"])
@login_required
def reset_password():
    if request.method == "POST":
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        message = validate.validate_change_password(old_password, new_password)
        if message:
            return apology(message)
        return render_template("success_password__change.html")
    return render_template("reset_password.html")


@app.route("/topup", methods=["GET", "POST"])
@login_required
def topup():
    if request.method == "POST":
        data = db.execute("SELECT * FROM users WHERE id = ?", session['user_id'])
        hash = data[0]['hash']
        current_cash = data[0]['cash']
        if check_password_hash(hash, request.form.get("password")):
            amount = request.form.get("amount")
            db.execute("UPDATE users SET cash = ? WHERE id = ?", int(current_cash) + int(amount), session['user_id'])
            return render_template("topup_success.html")
        return apology("WRONG PASSWORD")
    return render_template("topup.html")

def cache_user_symbols(symbol):
    if "user_symbols" in session and symbol not in session["user_symbols"]:
            session["user_symbols"].append(symbol.upper())
    else:
            session["user_symbols"] = [symbol.upper()]

def remove_cache(symbol):
    if not db.execute("SELECT * FROM history WHERE symbol = ?", symbol.upper()):
        session["user_symbols"].remove(symbol.upper())

def get_user_symbol():
    options = db.execute("""
            SELECT DISTINCT(symbol) FROM history WHERE user_id = ?
        """, session['user_id'])
    results = []
    for row in options:
        if db.execute("SELECT SUM(shares) FROM history WHERE symbol = ? AND user_id = ?", row['symbol'], session["user_id"])[0]['SUM(shares)']:
            results.append(row['symbol'])
    return results

@app.route("/lookup", methods = ["POST"])
def look_up():
    user_symbols = get_user_symbol()
    data = {}
    for symbol in user_symbols:
        bought_price = db.execute("SELECT AVG(price) FROM history WHERE symbol = ? AND user_id = ?", symbol, session['user_id'])[0]['AVG(price)']
        data[symbol] = [lookup(symbol)['price'], bought_price]
    return data