"""
This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

from functools import wraps
import json
import os
import pymysql
from logutils import get_logger

logger = get_logger(__name__)


def load_credentials(configs):
    """Load database credentials from config file."""

    creds_config = configs.get("credentials", {})
    creds_path = os.path.expanduser(creds_config.get("path", ""))
    credentials = None

    if not creds_path:
        logger.warning(
            "No credentials path specified, using default SQLite configuration"
        )
        credentials = {
            "engine": "sqlite",
            "sqlite": {"database_path": "./reliability_test.db"},
            "mysql": {"host": "", "user": "", "password": "", "database": ""},
        }
        return credentials

    if not os.path.isabs(creds_path):
        creds_path = os.path.join(os.path.dirname(__file__), creds_path)

    with open(creds_path, encoding="utf-8") as f:
        creds = json.load(f)

    def get_env_value(value):
        """Get value from environment if it starts with $"""
        if isinstance(value, str) and value.startswith("$"):
            env_var = value[1:]
            return os.environ.get(env_var, value)
        return value

    if creds.get("engine") == "mysql":
        mysql_config = creds.get("mysql", {})
        credentials = {
            "engine": "mysql",
            "mysql": {
                "host": get_env_value(mysql_config.get("host", "")),
                "user": get_env_value(mysql_config.get("user", "")),
                "password": get_env_value(mysql_config.get("password", "")),
                "database": get_env_value(mysql_config.get("database", "")),
            },
            "sqlite": {"database_path": ""},
        }
    elif creds.get("engine") == "sqlite":
        sqlite_config = creds.get("sqlite", {})
        credentials = {
            "engine": "sqlite",
            "sqlite": {
                "database_path": get_env_value(sqlite_config.get("database_path", "")),
            },
            "mysql": {"host": "", "user": "", "password": "", "database": ""},
        }
    else:
        logger.warning(
            "Unsupported database engine specified in credentials, "
            "using default SQLite configuration"
        )
        credentials = {
            "engine": "sqlite",
            "sqlite": {"database_path": "./reliability_test.db"},
            "mysql": {"host": "", "user": "", "password": "", "database": ""},
        }
    return credentials


def ensure_database_exists(host, user, password, database_name):
    """
    Decorator that ensures a MySQL database exists before executing a function.

    Args:
        host (str): The host address of the MySQL server.
        user (str): The username for connecting to the MySQL server.
        password (str): The password for connecting to the MySQL server.
        database_name (str): The name of the database to ensure existence.

    Returns:
        function: Decorated function.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                connection = pymysql.connect(
                    host=host,
                    user=user,
                    password=password,
                    charset="utf8mb4",
                    collation="utf8mb4_unicode_ci",
                )
                with connection.cursor() as cursor:
                    sql = "CREATE DATABASE IF NOT EXISTS " + database_name
                    cursor.execute(sql)

                logger.debug(
                    "Database %s created successfully (if it didn't exist)",
                    database_name,
                )

            except pymysql.MySQLError as error:
                logger.error("Failed to create database: %s", error)

            finally:
                connection.close()

            return func(*args, **kwargs)

        return wrapper

    return decorator
