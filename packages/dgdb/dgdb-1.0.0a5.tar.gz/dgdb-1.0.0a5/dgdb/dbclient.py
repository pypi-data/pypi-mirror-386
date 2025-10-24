"""
Database Client (dgdb) - A flexible SQLAlchemy-based database client

Features:
- Multiple database support (PostgreSQL, MySQL, Oracle, SQL Server)
- Connection pooling and management
- SQL template processing
- Automatic retry on connection failures
- Configuration validation
- Context manager support
- Sync and async interfaces
- Comprehensive logging
- Automatic reconnection on connection failures

Example usage:
    >>> db_config = {
    ...     'dialect': 'postgresql',
    ...     'db_user': 'user',
    ...     'db_pass': 'password',
    ...     'db_host': 'localhost',
    ...     'db_port': 5432,
    ...     'db_name': 'mydb'
    ... }
    >>> client = DBClient(db_config)
    >>> data = client.get_data("SELECT * FROM users WHERE id = :id", params={'id': 1})
"""

import logging
import os
from contextlib import contextmanager
from string import Template
from time import perf_counter, sleep
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    Generator,
)

import sqlalchemy.exc
from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import (
    DatabaseError,
    ResourceClosedError,
    ProgrammingError,
    SQLAlchemyError,
    OperationalError,
    DisconnectionError,
)
from sqlalchemy.engine.base import Connection as SQLAlchemyConnection
from sqlalchemy.orm import Session

from .db_connection_config import DBConnectionConfig
from .common_vars import ConnectionFields, SQLSource


class DBConnectionError(Exception):
    """Custom exception for database connection issues."""
    pass


class DBClient:
    """Database client for managing connections and executing queries."""

    def __init__(
            self,
            db_conn: dict[str, Any] | DBConnectionConfig,
            future: bool = True,
            do_initialize: bool = True,
            auto_reconnect: bool = True,
            reconnect_attempts: int = 3,
            reconnect_delay: float = 5.0,
            *args,
            **kwargs,
    ):
        """Initialize the database client.

        Args:
            db_conn: Database connection parameters as dict or DBConnectionConfig
            future: Use SQLAlchemy 2.0 style APIs
            do_initialize: Initialize connection immediately
            auto_reconnect: Enable automatic reconnection
            reconnect_attempts: Number of reconnection attempts
            reconnect_delay: Delay between reconnection attempts in seconds
            *args: Additional arguments for create_engine
            **kwargs: Additional keyword arguments for create_engine
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.args = args
        self.kwargs = kwargs
        self.future = future
        self.auto_reconnect = auto_reconnect
        self.reconnect_attempts = reconnect_attempts
        self.reconnect_delay = reconnect_delay

        # Validate and store connection config
        if isinstance(db_conn, dict):
            self.db_conn = DBConnectionConfig(**db_conn)
        else:
            self.db_conn = db_conn

        # Connection attributes
        self.engine: Optional[Engine] = None
        self.conn: Optional[SQLAlchemyConnection] = None
        self.metadata: Optional[MetaData] = None
        self._session: Optional[Session] = None

        if do_initialize:
            self.create_engine()

    def get_conn_str(self) -> str:
        """Generate connection string from configuration."""
        if self.db_conn.dialect == "mssql+pytds":
            from sqlalchemy.dialects import registry

            registry.register("mssql.pytds", "sqlalchemy_pytds.dialect", "MSDialect_pytds")

        if self.db_conn.db_host and self.db_conn.db_port:
            if "oracle" in self.db_conn.dialect.lower() and ".orcl" in self.db_conn.db_name:
                return (
                    f"{self.db_conn.dialect}://{self.db_conn.db_user}:{self.db_conn.db_pass}@"
                    f"{self.db_conn.db_host}:{self.db_conn.db_port}/?service_name={self.db_conn.db_name}"
                )
            return (
                f"{self.db_conn.dialect}://{self.db_conn.db_user}:{self.db_conn.db_pass}@"
                f"{self.db_conn.db_host}:{self.db_conn.db_port}/{self.db_conn.db_name}"
            )
        return f"{self.db_conn.dialect}://{self.db_conn.db_user}:{self.db_conn.db_pass}@{self.db_conn.db_name}"

    def create_engine(self) -> None:
        """Create SQLAlchemy engine with connection pooling."""
        connect_str = self.get_conn_str()
        try:
            self.engine = create_engine(
                connect_str,
                future=self.future,
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_size=5,
                max_overflow=10,
                *self.args,
                **self.kwargs,
            )
            self.logger.info(f"Created engine for {self.db_conn.dialect}")
        except sqlalchemy.exc.ArgumentError as e:
            self.logger.error(f"Failed to create engine: {str(e)}")
            # Fallback for SQLAlchemy>=2.0.0
            self.engine = create_engine(connect_str, future=True, *self.args, **self.kwargs)

    def create_conn(self) -> None:
        """Create a new database connection."""
        if not self.conn or self.conn.closed:
            self.conn = self.engine.connect()
            self.logger.debug("Created new database connection")

    def create_raw_conn(self) -> None:
        """Create a raw DBAPI connection."""
        if not self.conn or self.conn.closed:
            self.conn = self.engine.raw_connection()
            self.logger.debug("Created raw DBAPI connection")

    def create_metadata(self) -> None:
        """Initialize SQLAlchemy metadata."""
        if not self.metadata:
            self.create_conn()
            self.metadata = MetaData()
            self.logger.debug("Initialized database metadata")

    def set_args(self, *args, **kwargs) -> None:
        """Update engine creation arguments."""
        self.args = args
        self.kwargs = kwargs
        self.logger.debug("Updated engine creation arguments")

    def set_conn(self) -> None:
        """Create connection for SQLAlchemy."""
        self.create_engine()
        self.create_conn()
        self.create_metadata()
        self.logger.info("Initialized SQLAlchemy connection")

    def set_raw_conn(self) -> None:
        """Create raw connection for SQLAlchemy."""
        self.engine = create_engine(self.get_conn_str(), *self.args, **self.kwargs)
        self.conn = self.engine.raw_connection()
        self.metadata = MetaData(bind=self.conn)
        self.logger.info("Initialized raw DBAPI connection")

    def get_conn(
            self, fields: Union[ConnectionFields, List[ConnectionFields]] = "conn"
    ) -> Union[Optional[Any], Tuple[Optional[Any], ...]]:
        """Get connection components.

        Args:
            fields: Single field name or list of fields to return

        Returns:
            Requested connection components
        """
        if isinstance(fields, str):
            return self.__dict__.get(fields)
        if isinstance(fields, list):
            return tuple([self.__dict__.get(x) for x in fields])
        raise ValueError("Fields must be string or list of strings")

    def close_conn(self) -> None:
        """Close connection and dispose engine."""
        if self._session:
            try:
                self._session.close()
            except Exception as e:
                self.logger.warning(f"Error closing session: {str(e)}")
            finally:
                self._session = None

        if self.conn:
            try:
                self.conn.close()
            except Exception as e:
                self.logger.warning(f"Error closing connection: {str(e)}")
            finally:
                self.conn = None

        if self.engine:
            try:
                self.engine.dispose()
            except Exception as e:
                self.logger.warning(f"Error disposing engine: {str(e)}")
            finally:
                self.engine = None

        self.logger.info("Closed connection and disposed engine")

    def reconnect(self) -> None:
        """Reconnect to the database."""
        self.logger.info("Attempting to reconnect to database...")
        self.close_conn()
        sleep(self.reconnect_delay)
        self.set_conn()
        self.logger.info("Reconnected to database successfully")

    def ensure_connection(self) -> None:
        """Ensure database connection is alive, reconnect if necessary."""
        if not self.auto_reconnect:
            return

        try:
            self.check_connection_status()
        except (DBConnectionError, OperationalError, DisconnectionError) as e:
            self.logger.warning(f"Connection lost: {str(e)}. Attempting to reconnect...")
            self.reconnect()

    def check_connection_status(self) -> None:
        """Verify database connection is alive."""
        try:
            if not self.engine:
                raise DBConnectionError("Engine not initialized")

            # Use pool_pre_ping or execute simple query
            with self.engine.connect() as test_conn:
                if "oracle" in self.db_conn.dialect.lower():
                    result = test_conn.execute(text("select dummy from dual"))
                else:
                    result = test_conn.execute(text("select 'x' as dummy"))

                row = result.mappings().first()
                if not row or row.get("dummy") != "x":
                    raise DBConnectionError("Connection test failed")

        except Exception as e:
            self.logger.warning(f"Connection check failed: {str(e)}")
            raise DBConnectionError(f"Database connection is not alive: {str(e)}")

    @staticmethod
    def get_sql(filename: SQLSource, encoding: str = "utf-8") -> str:
        """Read SQL from file.

        Args:
            filename: Path to SQL file
            encoding: File encoding

        Returns:
            SQL content as string
        """
        with open(filename, "r", encoding=encoding) as file:
            return file.read()

    @contextmanager
    def session_scope(self) -> Generator[SQLAlchemyConnection, None, None]:
        """Provide transactional scope around series of operations.

        Example:
            with dgdb.session_scope() as session:
                session.execute(text("SELECT 1"))
        """
        session = None
        for attempt in range(1, self.reconnect_attempts + 1):
            try:
                self.ensure_connection()
                session = self.engine.connect()

                try:
                    yield session
                    session.commit()
                    self.logger.debug("Transaction committed")
                    break
                except Exception as e:
                    session.rollback()
                    self.logger.error(f"Transaction rolled back: {str(e)}")

                    # Handle "transaction has been rolled back" error
                    if "has been rolled back" in str(e) and attempt < self.reconnect_attempts:
                        self.logger.warning(f"Transaction error, retrying (attempt {attempt + 1})...")
                        self.reconnect()
                        continue
                    raise

            except (OperationalError, DisconnectionError, DBConnectionError) as e:
                self.logger.warning(f"Database error in session (attempt {attempt}): {str(e)}")
                if attempt < self.reconnect_attempts:
                    self.reconnect()
                    continue
                raise
            finally:
                if session:
                    session.close()
                    self.logger.debug("Session closed")

    def get_data(
            self,
            sql: SQLSource,
            params: Optional[Dict] = None,
            encoding: str = "utf-8",
            print_script: bool = False,
            max_attempts: int = 5,
            **kwargs,
    ) -> List[Dict]:
        """Execute query and return results as list of dictionaries.

        Args:
            sql: SQL file path or query string
            params: Parameters for parameterized query
            encoding: File encoding if sql is a file path
            print_script: Print the executed SQL to console
            max_attempts: Maximum retry attempts on failure
            kwargs: Template substitution variables

        Returns:
            List of dictionaries representing query results
        """
        for attempt in range(1, max_attempts + 1):
            try:
                self.ensure_connection()
                if not self.conn or self.conn.closed:
                    self.create_conn()

                script = self._prepare_script(sql, encoding, **kwargs)

                if print_script:
                    print(script)

                return self._execute_with_retry(script, params, attempt, max_attempts)

            except (OperationalError, DisconnectionError, DBConnectionError) as e:
                self.logger.warning(f"Connection error (attempt {attempt}/{max_attempts}): {str(e)}")
                if attempt < max_attempts:
                    self.reconnect()
                    sleep(self.reconnect_delay)
                    continue
                raise

    def get_data_row(
            self,
            sql: SQLSource,
            index: int = 0,
            params: Optional[Dict] = None,
            encoding: str = "utf-8",
            print_script: bool = False,
            max_attempts: int = 5,
            **kwargs,
    ) -> Optional[Dict]:
        """Get single row from query results.

        Args:
            sql: SQL file path or query string
            index: Row index to return
            params: Parameters for parameterized query
            encoding: File encoding if sql is a file path
            print_script: Print the executed SQL to console
            max_attempts: Maximum retry attempts on failure
            kwargs: Template substitution variables

        Returns:
            Dictionary representing the requested row or None if not found
        """
        result = self.get_data(sql, params, encoding, print_script, max_attempts, **kwargs)
        return result[index] if result and len(result) > index else None

    def run_script(
            self,
            sql: SQLSource,
            encoding: str = "utf-8",
            print_script: bool = False,
            max_attempts: int = 5,
            **kwargs,
    ) -> None:
        """Execute SQL script without returning results.

        Args:
            sql: SQL file path or query string
            encoding: File encoding if sql is a file path
            print_script: Print the executed SQL to console
            max_attempts: Maximum retry attempts on failure
            kwargs: Template substitution variables
        """
        self.get_data(sql, None, encoding, print_script, max_attempts, **kwargs)

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists in database.

        Args:
            table_name: Name of table to check

        Returns:
            True if table exists, False otherwise
        """
        for attempt in range(1, self.reconnect_attempts + 1):
            try:
                self.ensure_connection()
                self.create_metadata()
                return table_name in self.metadata.tables
            except (OperationalError, DisconnectionError, DBConnectionError) as e:
                self.logger.warning(f"Connection error checking table (attempt {attempt}): {str(e)}")
                if attempt < self.reconnect_attempts:
                    self.reconnect()
                    continue
                raise

    def get_table(self, table_name: str) -> Table:
        """Get SQLAlchemy Table object.

        Args:
            table_name: Name of table to retrieve

        Returns:
            SQLAlchemy Table object
        """
        for attempt in range(1, self.reconnect_attempts + 1):
            try:
                self.ensure_connection()
                self.create_metadata()
                return Table(table_name, self.metadata, autoload_with=self.engine)
            except (OperationalError, DisconnectionError, DBConnectionError) as e:
                self.logger.warning(f"Connection error getting table (attempt {attempt}): {str(e)}")
                if attempt < self.reconnect_attempts:
                    self.reconnect()
                    continue
                raise

    def commit(self, transaction=None) -> None:
        """Commit transaction."""
        try:
            if transaction:
                transaction.commit()
            elif self.conn:
                self.conn.commit()
            self.logger.debug("Transaction committed")
        except SQLAlchemyError as e:
            self.logger.error(f"Error committing transaction: {str(e)}")
            raise

    def rollback(self, transaction=None) -> None:
        """Rollback transaction."""
        try:
            if transaction:
                transaction.rollback()
            elif self.conn:
                self.conn.rollback()
            self.logger.debug("Transaction rolled back")
        except SQLAlchemyError as e:
            self.logger.error(f"Error rolling back transaction: {str(e)}")
            raise

    def begin_transaction(self):
        """Begin a new transaction."""
        self.logger.debug("Beginning new transaction")
        self.ensure_connection()
        return self.engine.begin()

    def _prepare_script(self, sql: SQLSource, encoding: str, **kwargs) -> str:
        """Prepare SQL script from file or string with template substitution."""
        if os.path.exists(sql):
            script_t = Template(self.get_sql(sql, encoding))
        else:
            script_t = Template(str(sql))
        return script_t.safe_substitute(**kwargs)

    def _execute_with_retry(self, script: str, params: Optional[Dict], attempt: int, max_attempts: int) -> List[Dict]:
        """Execute SQL script with retry logic for transaction errors."""
        result = []
        transaction = None
        start_time = perf_counter()

        try:
            if not self.future:
                transaction = self.conn.begin()

            self.logger.debug(f"Executing query (attempt {attempt}/{max_attempts})")
            res = self.conn.execute(text(script), params or {})

            try:
                result = [dict(row) for row in res.mappings()]
            except ResourceClosedError:
                result = []

            self.commit(transaction)
            self.logger.debug(f"Query executed in {perf_counter() - start_time:.2f}s")

        except ProgrammingError as ex:
            self.logger.error(f"SQL Error: {str(ex)}")
            self.rollback(transaction)
            raise
        except DatabaseError as ex:
            self.logger.warning(f"Database error (attempt {attempt}): {str(ex)}")
            self.rollback(transaction)

            # Handle "transaction has been rolled back" error specifically
            if "has been rolled back" in str(ex) and attempt < max_attempts:
                self.logger.info("Transaction rolled back, reconnecting and retrying...")
                self.reconnect()
                raise DBConnectionError("Transaction rolled back, need to retry") from ex

            if attempt == max_attempts:
                self.logger.error(f"Max attempts reached. Last error: {str(ex)}")
                raise
            else:
                raise DBConnectionError(f"Database error: {str(ex)}") from ex

        return result

    def _execute(self, script: str, params: Optional[Dict], max_attempts: int) -> List[Dict]:
        """Backward compatibility wrapper."""
        return self._execute_with_retry(script, params, 1, max_attempts)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    config = {
        "dialect": "postgresql",
        "db_user": "user",
        "db_pass": "password",
        "db_host": "localhost",
        "db_port": 5432,
        "db_name": "testdb"
    }

    client = DBClient(config, auto_reconnect=True, reconnect_attempts=3, reconnect_delay=5)

    try:
        # Using context manager with automatic reconnection
        with client.session_scope() as session:
            result = session.execute(text("SELECT 1 AS test"))
            print(result.scalar())

        # Regular query with automatic reconnection
        data = client.get_data("SELECT * FROM users WHERE id = :id", params={"id": 1})
        print(data)

        # Test connection resilience
        print("Connection status:", client.check_connection_status())

    except Exception as e:
        print(f"Operation failed: {e}")
    finally:
        client.close_conn()