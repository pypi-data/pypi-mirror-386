"""
Schema tools for PostgreSQL MCP Server
"""

import logging
from typing import Any, Dict, List, Callable, Coroutine
from mcp import Tool

from ..database import DatabaseManager, DatabaseError
from ..config import load_config

logger = logging.getLogger(__name__)


# Tool definitions for schema operations
get_tables = Tool(
    name="get_tables",
    description="Get list of all tables in the PostgreSQL database",
    inputSchema={
        "type": "object",
        "properties": {
            "schema": {
                "type": "string",
                "description": ("Schema name to filter tables (default: 'public')"),
                "default": "public",
            }
        },
        "required": [],
    },
)


get_table_schema = Tool(
    name="get_table_schema",
    description="Get detailed schema information for a specific table",
    inputSchema={
        "type": "object",
        "properties": {
            "table_name": {
                "type": "string",
                "description": "Name of the table to get schema for",
            },
            "schema": {
                "type": "string",
                "description": "Schema name (default: 'public')",
                "default": "public",
            },
        },
        "required": ["table_name"],
    },
)


get_database_info = Tool(
    name="get_database_info",
    description="Get database metadata and version information",
    inputSchema={"type": "object", "properties": {}, "required": []},
)


# Tool handlers
async def handle_get_tables(schema: str = "public") -> Dict[str, Any]:
    """Handle get_tables tool execution"""
    try:
        config = load_config()
        db_manager = DatabaseManager(config.postgres)

        # Connect to database
        db_manager.connection.connect()

        # Use existing get_tables method
        result = db_manager.get_tables()

        # Disconnect from database
        db_manager.connection.disconnect()

        return result

    except DatabaseError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in get_tables: {e}")
        return {"success": False, "error": f"Internal server error: {str(e)}"}


async def handle_get_table_schema(
    table_name: str, schema: str = "public"
) -> Dict[str, Any]:
    """Handle get_table_schema tool execution"""
    try:
        config = load_config()
        db_manager = DatabaseManager(config.postgres)

        # Connect to database
        db_manager.connection.connect()

        # Query to get table schema information
        query = """
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length,
            numeric_precision,
            numeric_scale
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
        """

        results = db_manager.connection.execute_query(
            query, {"schema": schema, "table_name": table_name}
        )

        # Get table constraints
        constraints_query = """
        SELECT
            tc.constraint_name,
            tc.constraint_type,
            kcu.column_name
        FROM information_schema.table_constraints tc
        LEFT JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
            AND tc.table_name = kcu.table_name
        WHERE tc.table_schema = %s AND tc.table_name = %s
        ORDER BY tc.constraint_type, tc.constraint_name
        """

        constraints = db_manager.connection.execute_query(
            constraints_query, {"schema": schema, "table_name": table_name}
        )

        # Disconnect from database
        db_manager.connection.disconnect()

        return {
            "success": True,
            "table_name": table_name,
            "schema": schema,
            "columns": results,
            "constraints": constraints,
        }

    except DatabaseError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in get_table_schema: {e}")
        return {"success": False, "error": f"Internal server error: {str(e)}"}


async def handle_get_database_info() -> Dict[str, Any]:
    """Handle get_database_info tool execution"""
    try:
        config = load_config()
        db_manager = DatabaseManager(config.postgres)

        # Connect to database
        db_manager.connection.connect()

        # Get database version
        version_result = db_manager.connection.execute_query("SELECT version();")
        version = version_result[0]["version"] if version_result else "Unknown"

        # Get database name and current user
        db_info_result = db_manager.connection.execute_query(
            "SELECT current_database(), current_user, current_schema();"
        )
        db_info = db_info_result[0] if db_info_result else {}

        # Get database size
        size_result = db_manager.connection.execute_query(
            (
                "SELECT pg_size_pretty(pg_database_size(current_database())) "
                "as database_size;"
            )
        )
        database_size = size_result[0]["database_size"] if size_result else "Unknown"

        # Get number of tables
        tables_count_result = db_manager.connection.execute_query(
            (
                "SELECT COUNT(*) as table_count FROM information_schema.tables "
                "WHERE table_schema = 'public';"
            )
        )
        table_count = (
            tables_count_result[0]["table_count"] if tables_count_result else 0
        )

        # Disconnect from database
        db_manager.connection.disconnect()

        return {
            "success": True,
            "database_info": {
                "version": version,
                "database_name": db_info.get("current_database", "Unknown"),
                "current_user": db_info.get("current_user", "Unknown"),
                "current_schema": db_info.get("current_schema", "Unknown"),
                "database_size": database_size,
                "table_count": table_count,
            },
        }

    except DatabaseError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in get_database_info: {e}")
        return {"success": False, "error": f"Internal server error: {str(e)}"}


# Tool registry
def get_schema_tools() -> List[Tool]:
    """Get all schema tools"""
    return [
        get_tables,
        get_table_schema,
        get_database_info,
    ]


def get_schema_handlers() -> (
    Dict[str, Callable[..., Coroutine[Any, Any, Dict[str, Any]]]]
):
    """Get tool handlers for schema operations"""
    return {
        "get_tables": handle_get_tables,
        "get_table_schema": handle_get_table_schema,
        "get_database_info": handle_get_database_info,
    }
