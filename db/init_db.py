import os
import pathlib
import psycopg2  # lets Python run SQL commands
from dotenv import load_dotenv

# Load environment variables from .env (at project root)
load_dotenv(pathlib.Path(__file__).resolve().parents[1] / ".env")

# Get absolute path to this script’s folder
ROOT = pathlib.Path(__file__).resolve().parent

def main():
    # Connect to PostgreSQL using credentials from .env
    with psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")  # corrected name
    ) as conn:
        # Create a cursor for executing SQL commands
        with conn.cursor() as cur:
            schema_path = ROOT / "schema.sql"
            with open(schema_path, "r", encoding="utf-8") as f:
                sql_commands = f.read()
                cur.execute(sql_commands)
                print(f"✅ Executed schema: {schema_path.name}")

    print("✅ Database initialized successfully!")

if __name__ == "__main__":
    main()
