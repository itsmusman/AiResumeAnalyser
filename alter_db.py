from db import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text('ALTER TABLE users MODIFY password VARCHAR(255)'))
    conn.commit()
print("Table altered successfully.")
