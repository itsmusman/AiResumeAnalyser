from sqlalchemy import text

from db import engine


def run_migration():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR(100)"))
            conn.commit()
            print("Successfully added full_name column to users table.")
        except Exception as e:
            print("Migration skipped or failed:", e)


if __name__ == "__main__":
    run_migration()
