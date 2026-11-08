import sqlite3
from langchain.tools import tool
from text2sql.llm_factory import LLMFactory
from config.settings import get_settings


@tool
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


@tool
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


@tool
def sql_db_query(query: str) -> str:
    """Input to this tool is a detailed and correct SQL query, output is a result from the database.
    If the query is not correct, an error message will be returned.
    If an error is returned, rewrite the query, check the query, and try again.
    If you encounter an issue with Unknown column 'xxxx' in 'field list', use sql_db_schema to query the correct table fields.
    """
    settings = get_settings()
    db_path = settings.DB_PATH

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.commit()
        conn.close()

        if not rows:
            return "Query executed successfully, but no results were returned."

        col_names = [desc[0] for desc in cursor.description]
        result_str = "\t".join(col_names) + "\n"
        result_str += "\n".join("\t".join(str(x) for x in row) for row in rows)
        return result_str
    except Exception as e:
        return f"Error executing query: {str(e)}"
    finally:
        if conn:
            conn.close()


@tool
def sql_db_query_checker(query: str) -> str:
    """Use this tool to double check if your query is correct before executing it.
    Always use this tool before executing a query with sql_db_query!"""
    trigger_prompt = """{query}
Double check the sqlite query above for common mistakes, including:
- Using NOT IN with NULL values
- Using UNION when UNION ALL should have been used
- Using BETWEEN for exclusive ranges
- Data type mismatch in predicates
- Properly quoting identifiers
- Using the correct number of arguments for functions
- Casting to the correct data type
- Using the proper columns for joins

If there are any of the above mistakes, rewrite the query. If there are no mistakes, just reproduce the original query.

Output the final SQL query only.

SQL Query: """.format(query=query)

    settings = get_settings()

    kwargs = {
        "model_name": settings.CHAT_MODEL_NAME,
        "max_retries": settings.max_retries,
        "temperature": settings.temperature,
        "api_key": settings.GROQ_API_KEY,
    }

    model = LLMFactory.create_llm(model_type=settings.llm_type, **kwargs)

    response = model.invoke(trigger_prompt)
    return response.text.strip()


def main():
    # Example usage of the tools
    # print("Listing tables in the database:")
    # print(sql_db_list_tables())

    # print("\nGetting schema and sample rows for 'Artist' table:")
    # print(sql_db_schema("Album"))

    print("\nExecuting a SQL query:")
    query = """SELECT a.*  FROM Album AS a 
LEFT JOIN Artist AS ar ON a.ArtistId = ar.ArtistId 
WHERE ar.ArtistId IS NULL;"""
    print(sql_db_query(query))

    # print("\nChecking a SQL query for common mistakes:")
    # query_to_check = (
    #     "SELECT * FROM Album WHERE ArtistId NOT IN (SELECT ArtistId FROM Artist);"
    # )
    # print(sql_db_query_checker(query_to_check))


if __name__ == "__main__":
    main()
