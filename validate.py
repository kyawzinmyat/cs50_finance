from cs50 import SQL
from helpers import lookup, apology
from flask import session
import string
from werkzeug.security import check_password_hash, generate_password_hash


class Validate:
    def __init__(self, db):
        self.db = db
        self.password_length = 8
        self.password_char = string.ascii_letters + string.digits + string.punctuation

    def validate_username(self, username):
        command = "SELECT * FROM users WHERE username = ?"
        if username:
            if not self.db.execute(command, username):
                if username.find('') == -1:
                    return "USERNAME CANNOT BE INCLUDED SPACE"
                return None
            return "USERNAME ALREADY EXISTS"
        return "USERNAME CANNOT BE BLANK"

    def validate_password(self, pass1, pass2):
        if pass1 or pass2:
            if pass1 == pass2:
                return self.validate_password_char(pass1)
            return "PASSWORDS DO NOT MATCH"
        return "PASSWORD CANNOT BE EMPTY"

    def validate_password_char(self, pass1):
        if any(cha not in self.password_char for cha in pass1):
            return "PASSWORD MUST INCLUDE ONE UPPERCASE, SPECIAL SYMBOL, NUMBER"

    def validate_user_pass(self, username, pass1, pass2):
        message = self.validate_username(username)
        if message:
            return message
        message = self.validate_password(pass1, pass2)
        if message:
            return message

    def validate_shares(self, shares):
        try:
            shares = int(shares)
            if shares < 0:
                return False
            return True
        except:
            return False

    def validate_cash_and_price(self, shares, lookup_data):
        shares = int(shares)
        current_price = lookup_data['price']
        user_cash = self.db.execute("""
                SELECT cash FROM users
                WHERE id = (?)
              """, session['user_id'])
        if user_cash:
            user_cash = user_cash[0]['cash']
            if shares * current_price > user_cash:
                return "Not enough Balance !"

    def validate_buy(self, symbol, price):
        if self.validate_shares(price):
            price = int(price)
            if not symbol:
                return "Symbol cannot be blank"
            if not lookup(symbol):
                return "Invalid symbol"
        else:
            return "INVALID SHARES"

    def validate_change_password(self, old_pass, new_pass):
        old_hash = self.db.execute("SELECT hash FROM users WHERE id = ?", session['user_id'])[0]['hash']
        if not check_password_hash(old_hash, old_pass):
            return "WRONG PASSWORD!"
        message = self.validate_password_char(new_pass)
        if message:
            return message
        self.db.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(new_pass), session['user_id'])

    def validate_sell(self, symbol, shares):
        if symbol:
            if self.validate_shares(shares):
                data = self.db.execute("""
                SELECT sum(shares) FROM history WHERE symbol = ? AND user_id = ?
                """, symbol, session['user_id'])
                shares = int(shares)
                if data[0].values():
                    db_shares = int(data[0]['sum(shares)'])
                    if shares > db_shares:
                        return "TOO MANY SHARES"
                    return
                return "INVALID SYMBOL"
            return "INVALID SHARES"
        return "MISSING SYMBOL"

