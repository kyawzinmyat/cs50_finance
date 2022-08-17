from cs50 import SQL
from helpers import lookup
from flask import session
import datetime


def buy_shares(symbol, shares, lookup_data, db):
    current_cash = db.execute(
        """
            SELECT cash FROM users WHERE id = ?
        """, session["user_id"])
    if current_cash:
        shares = int(shares)
        current_cash = current_cash[0]['cash']
        shares_total_price = shares * lookup_data['price']
        db.execute("""
            UPDATE users SET
         cash = ? WHERE id = ?
            """, current_cash - shares_total_price, session['user_id'])
        add_log(symbol, shares, lookup_data, db)
        return current_cash - shares_total_price, shares_total_price
    return None, None


def add_log(symbol, shares, lookup_data, db):
    db.execute("""
        INSERT INTO history (user_id, symbol, name, shares, price, date_time)
        VALUES
        (
            ?, ?, ?, ?, ?, ?
        )
    """, session['user_id'], symbol.upper(), lookup_data['name'], shares, lookup_data['price'], datetime.datetime.now())

