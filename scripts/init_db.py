import os
from backend.db.connection import get_conn

SCHEMA_PATH = os.path.join("backend", "db", "schema.sql")

def main():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = f.read()

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(schema)
        conn.commit()
        print("✅ Database initialized successfully.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
