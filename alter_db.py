from sqlalchemy import text

from db import engine

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE users MODIFY password VARCHAR(255)"))
    conn.commit()
print("Table altered successfully.")
