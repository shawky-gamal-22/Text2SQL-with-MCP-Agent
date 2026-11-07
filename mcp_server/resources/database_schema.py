import sqlite3
from config.settings import get_settings


def get_db_schema_resource() -> str:
    """Returns the schema of the database as a string, including table names and their corresponding CREATE TABLE statements.
    This function queries the sqlite_master table to retrieve the names and SQL definitions of all tables and
    """
    settings = get_settings()
    conn = sqlite3.connect(settings.DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name, sql FROM sqlite_master WHERE type IN ('table', 'view');"
    )
    rows = cursor.fetchall()
    conn.close()

    schema_text = []
    for table_name, ddl in rows:
        if ddl:
            schema_text.append(f"-- Table: {table_name}\n{ddl};")

    return "\n\n".join(schema_text)


def main():
    print(get_db_schema_resource())


if __name__ == "__main__":
    main()
