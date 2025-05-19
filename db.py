"""
This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

from peewee import Database, DatabaseError, MySQLDatabase, SqliteDatabase
from playhouse.shortcuts import ReconnectMixin
from utils import ensure_database_exists, load_credentials
from protocol_interfaces import BaseProtocolInterface
from logutils import get_logger

logger = get_logger(__name__)

DATABASE_CONFIGS = load_credentials(BaseProtocolInterface.config)


class ReconnectMySQLDatabase(ReconnectMixin, MySQLDatabase):
    """
    A custom MySQLDatabase class with automatic reconnection capability.

    This class inherits from both ReconnectMixin and MySQLDatabase
    to provide automatic reconnection functionality in case the database
    connection is lost.
    """


def connect() -> Database:
    """
    Connect to the appropriate database based on the engine configuration.

    Returns:
        Database: A connected database instance (either MySQL or SQLite).
    """
    engine = DATABASE_CONFIGS.get("engine")

    if engine == "mysql":
        return connect_to_mysql()

    return connect_to_sqlite()


@ensure_database_exists(
    DATABASE_CONFIGS["mysql"]["host"],
    DATABASE_CONFIGS["mysql"]["user"],
    DATABASE_CONFIGS["mysql"]["password"],
    DATABASE_CONFIGS["mysql"]["database"],
)
def connect_to_mysql() -> ReconnectMySQLDatabase:
    """
    Connects to the MySQL database.

    Returns:
        ReconnectMySQLDatabase: The connected MySQL database object with reconnection capability.

    Raises:
        DatabaseError: If failed to connect to the database.
    """
    logger.debug(
        "Attempting to connect to MySQL database '%s' at '%s'...",
        DATABASE_CONFIGS["mysql"]["database"],
        DATABASE_CONFIGS["mysql"]["host"],
    )
    try:
        db = ReconnectMySQLDatabase(
            DATABASE_CONFIGS["mysql"]["database"],
            user=DATABASE_CONFIGS["mysql"]["user"],
            password=DATABASE_CONFIGS["mysql"]["password"],
            host=DATABASE_CONFIGS["mysql"]["host"],
        )
        db.connect()
        return db
    except DatabaseError as error:
        logger.error(
            "Failed to connect to MySQL database '%s' at '%s': %s",
            DATABASE_CONFIGS["mysql"]["database"],
            DATABASE_CONFIGS["mysql"]["host"],
            error,
        )
        raise error


def connect_to_sqlite() -> SqliteDatabase:
    """
    Connects to the SQLite database.

    Returns:
        SqliteDatabase: The connected SQLite database object.

    Raises:
        DatabaseError: If failed to connect to the database.
    """
    db_path = DATABASE_CONFIGS["sqlite"]["database_path"]
    logger.debug("Attempting to connect to SQLite database at '%s'...", db_path)
    try:
        db = SqliteDatabase(db_path)
        db.connect()
        return db
    except DatabaseError as error:
        logger.error("Failed to connect to SQLite database at '%s': %s", db_path, error)
        raise error
