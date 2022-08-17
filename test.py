from cs50 import SQL

db = SQL("sqlite:///finance.db")

data = db.execute("SELECT   AVG(price) FROM history WHERE symbol = 'F' and user_id = 42")

print(data)