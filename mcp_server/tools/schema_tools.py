import sqlite3

from config.settings import get_settings


def sql_db_list_tables() -> str:
    """Input is an empty string, output is a comma-separated list of tables in the database."""

    settings = get_settings()
    db_path = settings.DB_PATH

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()

        if not tables:
            return "No tables found in the database."

        table_names = [table[0] for table in tables]
        return ", ".join(table_names)
    except Exception as e:
        return f"Error accessing the database: {str(e)}"
    finally:
        if conn:
            conn.close()


def sql_db_schema(table_names: str) -> str:
    """Input to this tool is a comma-separated list of tables, output is the schema and sample rows for those tables.
    Be sure that the tables actually exist by calling sql_db_list_tables first!
    Example Input: table1, table2, table3"""
    con = None
    settings = get_settings()
    db_path = settings.DB_PATH

    try:
        con = sqlite3.connect(db_path)
        cursor = con.cursor()

        # Fetch actual table (and view) names and map lowercase -> canonical name
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table', 'view');"
        )
        canonical_map = {row[0].lower(): row[0] for row in cursor.fetchall()}

        print(f"Canonical map of tables/views: {canonical_map}")
        results = []
        for raw_table in table_names.split(","):
            table_token = raw_table.strip()
            if not table_token:
                continue

            # Case-insensitive resolution
            table = canonical_map.get(table_token.lower())
            if not table:
                results.append(
                    f"Error: table_name {table_token!r} not found in database"
                )
                continue

            cursor.execute(
                "SELECT sql FROM sqlite_master WHERE type IN ('table', 'view') AND name=?;",
                (table,),
            )
            schema_row = cursor.fetchone()
            if schema_row and schema_row[0]:
                results.append(schema_row[0])

                try:
                    quoted_table = '"' + table.replace('"', '""') + '"'
                    cursor.execute(f"SELECT * FROM {quoted_table} LIMIT 3;")
                    rows = cursor.fetchall()
                    if rows:
                        col_names = [desc[0] for desc in cursor.description]
                        results.append(
                            f"/*\n3 rows from {table} table:\n"
                            + "\t".join(col_names)
                            + "\n"
                            + "\n".join("\t".join(str(x) for x in row) for row in rows)
                            + "\n*/"
                        )
                except Exception as e:
                    results.append(f"Error fetching sample rows for {table}: {e}")

        return "\n\n".join(results)
    finally:
        if con:
            con.close()


def main():
    # Example usage of the tools
    # print("Listing tables in the database:")
    # print(sql_db_list_tables())

    print("\nGetting schema and sample rows for 'Artist' table:")
    print(sql_db_schema("Album"))

    # print("\nChecking a SQL query for common mistakes:")
    # query_to_check = (
    #     "SELECT * FROM Album WHERE ArtistId NOT IN (SELECT ArtistId FROM Artist);"
    # )
    # print(sql_db_query_checker(query_to_check))


if __name__ == "__main__":
    main()
