from flask import session
from helpers import lookup


def update_user_cash(shares, price_of_share, db):
    user_current_cash = db.execute("SELECT cash FROM users WHERE id = ?", session['user_id'])[0]['cash']
    prices_of_shares = (price_of_share * -shares)
    added_cash = user_current_cash + prices_of_shares
    db.execute("UPDATE users SET cash = ? WHERE id = ?", added_cash, session['user_id'])
    return added_cash, prices_of_shares


def add_reduced_shares(shares, symbol, db):
    import datetime
    lookup_data = lookup(symbol.lower())
    current_price = lookup_data['price']
    name = lookup_data['name']
    data = db.execute("""
        INSERT INTO history(user_id, symbol, name, shares, price, date_time)
        VALUES (?, ?, ?, ?, ?, ?)
    """, session['user_id'], symbol.upper(), name, shares, current_price, datetime.datetime.now())
    return update_user_cash(shares, current_price, db)