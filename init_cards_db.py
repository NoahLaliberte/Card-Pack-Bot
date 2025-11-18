import sqlite3

DB_PATH = "cards.db"
SQL_BOOTSTRAP = "black_bolt_types_placeholders.sql"

with open(SQL_BOOTSTRAP, "r", encoding="utf-8") as f:
    sql_script = f.read()

conn = sqlite3.connect(DB_PATH)
try:
    conn.executescript(sql_script)
    conn.commit()
    print("Database initialized and cards loaded.")
finally:
    conn.close()
