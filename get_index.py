from flask import session
from cs50 import SQL
from helpers import lookup


db = SQL("sqlite:///finance.db")


# share price total

def get_index():
    data_dict = {}
    cache = {

    }
    user_cash = db.execute("""
        SELECT cash FROM users WHERE id = ?
    """, session['user_id'])
    total_cash = 0
    data = db.execute("""
        SELECT * FROM history WHERE user_id = ?
    """, session['user_id'])
    for row in data:
        #retrive symbol from history
        symbol = row['symbol'].upper()
        if symbol not in cache:
            # new symbol
            data = lookup(symbol)# api data of that sym
            current_price = data['price']# track current price
            cache[symbol] = data
        else:
            current_price = cache[symbol]['price']
        shares = row['shares']
        total_cash += current_price * shares

        if symbol in data_dict:
            data_dict[symbol][1] += shares
            data_dict[symbol][2] = float(current_price)
            data_dict[symbol][3] += (shares * current_price)
            data_dict[symbol][4] = float(row['price'])
        else:
            data_dict[symbol.upper()] = [row['name'], shares, float(current_price), shares * current_price, float(row['price'])]
    return data_dict, user_cash, total_cash