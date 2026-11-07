from mcp.server.mcpserver import MCPServer
from mcp_server.resources.database_schema import get_db_schema_resource
from mcp_server.tools.query_tools import sql_db_query, sql_db_query_checker
from mcp_server.tools.schema_tools import sql_db_list_tables, sql_db_schema

mcp = MCPServer(
    "Text2SQL",
    description="A tool to convert natural language to SQL queries and execute them on a SQLite database.",
)


@mcp.resource("schema://sqlite/main")
async def database_schema_resource() -> str:
    """Returns the schema of the database as a string, including table names and their corresponding CREATE TABLE statements."""
    return get_db_schema_resource()


@mcp.tool(
    name="sql_db_list_tables",
    description="List all tables in the SQLite database.",
)
async def tool_list_tables() -> str:
    return sql_db_list_tables()


@mcp.tool(
    name="sql_db_schema",
    description="Get the schema of a specific table in the SQLite database.",
)
async def tool_db_schema(table_names: str) -> str:
    return sql_db_schema(table_names)


@mcp.tool(
    name="sql_db_query",
    description="Execute a SQL query on the SQLite database and return the results.",
)
async def tool_db_query(query: str) -> str:
    return sql_db_query(query)


@mcp.tool(
    name="sql_db_query_checker",
    description="Check a SQL query for common mistakes before executing it.",
)
async def tool_db_query_checker(query: str) -> str:
    return sql_db_query_checker(query)


if __name__ == "__main__":
    mcp.run(transport="stdio")
