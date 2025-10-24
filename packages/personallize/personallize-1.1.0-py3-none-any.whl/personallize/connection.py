from dataclasses import dataclass
from typing import Literal

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""


@dataclass
class Credentials:
    """
    Database credentials container.

    Attributes:
        db_type: Type of database (sqlite, mysql, postgres, sql_server)
        host: Database host (not needed for sqlite)
        port: Database port (not needed for sqlite)
        user: Database user (not needed for sqlite)
        password: Database password (not needed for sqlite)
        database: Database name (not needed for sqlite)
        database_path: Path to SQLite database file
        odbc_driver: ODBC driver version for SQL Server (default: 17)
    """

    db_type: Literal["sqlite", "mysql", "postgres", "sql_server"]
    host: str | None = None
    port: int | None = None
    user: str | None = None
    password: str | None = None
    database: str | None = None
    database_path: str | None = None
    odbc_driver: int | str | None = None

    @classmethod
    def sqlite(cls, database_path: str | None = None) -> "Credentials":
        """Create SQLite credentials."""
        return cls(db_type="sqlite", database_path=database_path)

    @classmethod
    def mysql(cls, host: str, port: int, user: str, password: str, database: str) -> "Credentials":
        """Create MySQL credentials."""
        return cls(
            db_type="mysql", host=host, port=port, user=user, password=password, database=database
        )

    @classmethod
    def postgres(
        cls, host: str, port: int, user: str, password: str, database: str
    ) -> "Credentials":
        """Create PostgreSQL credentials."""
        return cls(
            db_type="postgres",
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
        )

    @classmethod
    def sql_server(
        cls,
        host: str,
        user: str,
        password: str,
        database: str,
        odbc_driver: int | str | None = None,
    ) -> "Credentials":
        """
        Create SQL Server credentials.

        Args:
            host: SQL Server host
            user: Username
            password: Password
            database: Database name
            odbc_driver: ODBC driver version (17, 13) or driver name ("SQL Server").
                        If None, will auto-detect the best available driver.
        """
        return cls(
            db_type="sql_server",
            host=host,
            user=user,
            password=password,
            database=database,
            odbc_driver=odbc_driver,
        )


class Connection:
    """
    Database connection manager with context manager support.

    Supports multiple database types with simplified credential management.

    Usage with Credentials class:
        # SQLite
        creds = Credentials.sqlite("test.db")
        with Connection(creds) as db:
            result = db.session.execute(text("SELECT 1"))
            db.session.commit()

        # MySQL
        creds = Credentials.mysql("localhost", 3306, "user", "pass", "mydb")
        with Connection(creds) as db:
            result = db.session.execute(text("SELECT * FROM users"))
            db.session.commit()

        # PostgreSQL
        creds = Credentials.postgres("localhost", 5432, "user", "pass", "mydb")
        with Connection(creds) as db:
            result = db.session.execute(text("SELECT * FROM users"))
            db.session.commit()

        # SQL Server
        creds = Credentials.sql_server("server", "user", "pass", "mydb")
        with Connection(creds) as db:
            result = db.session.execute(text("SELECT * FROM users"))
            db.session.commit()

        # SQL Server with specific ODBC driver
        creds = Credentials.sql_server("server", "user", "pass", "mydb", odbc_driver=17)
        with Connection(creds) as db:
            result = db.session.execute(text("SELECT * FROM users"))
            db.session.commit()

    Get engine directly:
        conn = Connection(Credentials.sqlite("test.db"))
        engine = conn.get_engine()
    """

    def __init__(self, credentials: Credentials) -> None:
        """
        Initialize database connection.

        Args:
            credentials: Credentials object containing database connection details
        """
        self.db_type = credentials.db_type
        self.host = credentials.host
        self.port = credentials.port
        self.user = credentials.user
        self.password = credentials.password
        self.database = credentials.database
        self.database_path = credentials.database_path
        self.odbc_driver = credentials.odbc_driver

        self._engine: Engine | None = None
        self._connection_string: str | None = None
        self.session: Session | None = None

        # Test connection on initialization
        self._test_connection()

    def _create_connection_string(self) -> str:
        """Create database connection string based on db_type."""
        msg_requirements = "{} requires user, password, host, port, and database"
        msg_unsupported = "Unsupported database type."
        if self.db_type == "sqlite":
            return f"sqlite:///{self.database_path}" if self.database_path else "sqlite:///:memory:"

        if self.db_type == "mysql":
            if not all([self.user, self.password, self.host, self.port, self.database]):
                raise ValueError(msg_requirements.format("MySQL"))
            return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

        if self.db_type == "postgres":
            if not all([self.user, self.password, self.host, self.port, self.database]):
                raise ValueError(msg_requirements.format("PostgreSQL"))
            return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

        if self.db_type == "sql_server":
            if not all([self.user, self.password, self.host, self.database]):
                raise ValueError(msg_requirements.format("SQL Server"))

            # Auto-detect ODBC driver if not specified
            driver = self.odbc_driver if self.odbc_driver else self._detect_odbc_driver()
            connection_string = (
                f"DRIVER={{{driver}}};SERVER={self.host};"
                f"DATABASE={self.database};UID={self.user};PWD={self.password};"
            )
            return f"mssql+pyodbc:///?odbc_connect={connection_string}"

        raise ValueError(msg_unsupported)

    def _detect_odbc_driver(self) -> str:
        """
        Auto-detect available ODBC driver for SQL Server.

        Tests drivers in order of preference: 17, 13, "SQL Server"

        Returns:
            str: The first available ODBC driver string

        Raises:
            ConnectionError: If no compatible ODBC driver is found
        """
        not_specific_drive = (
            "No compatible ODBC driver found. Please install one of: "
            "ODBC Driver 17 for SQL Server, ODBC Driver 13 for SQL Server, or SQL Server driver"
        )

        drivers_to_test = [
            "ODBC Driver 17 for SQL Server",
            "ODBC Driver 13 for SQL Server",
            "SQL Server",
        ]

        for driver in drivers_to_test:
            try:
                # Test connection string with this driver
                test_connection_string = (
                    f"DRIVER={{{driver}}};SERVER={self.host};"
                    f"DATABASE={self.database};UID={self.user};PWD={self.password};"
                )
                test_url = f"mssql+pyodbc:///?odbc_connect={test_connection_string}"

                # Try to create engine and test connection
                test_engine = create_engine(
                    test_url, pool_pre_ping=True, pool_recycle=3600, echo=False
                )

                # Test the connection
                with test_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))

                # If we get here, the driver works
                test_engine.dispose()
                return driver
            except Exception as e:
                # This driver doesn't work, try the next one
                continue

        # If no driver worked, raise an error
        raise ConnectionError(not_specific_drive)

    def _create_engine(self) -> Engine:
        """Create SQLAlchemy engine."""
        if not self._engine:
            self._connection_string = self._create_connection_string()

            connect_args = {}
            if self.db_type == "sqlite":
                connect_args = {"check_same_thread": False}

            self._engine = create_engine(
                self._connection_string,
                connect_args=connect_args,
                pool_pre_ping=True,  # Verify connections before use
            )

        return self._engine

    def get_engine(self) -> Engine:
        """Get SQLAlchemy engine instance."""
        if not self._engine:
            self._create_engine()
        return self._engine

    def _test_connection(self) -> None:
        """
        Test database connection silently.
        Only raises exception if connection fails.
        """
        error_msg = "Failed to connect to {} database: {}"
        try:
            engine = self._create_engine()

            with engine.connect() as connection:
                # Simple test query for all database types
                connection.execute(text("SELECT 1"))

        except Exception as e:
            raise ConnectionError(error_msg.format(self.db_type, e)) from e

    def __enter__(self) -> "Connection":
        """Enter context manager - create session."""
        if not self._engine:
            self._create_engine()

        session_maker = sessionmaker(bind=self._engine)
        self.session = session_maker()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager - cleanup session and engine."""
        if self.session:
            if exc_type:
                self.session.rollback()
            else:
                self.session.commit()
            self.session.close()
            self.session = None

        # Keep engine alive for reuse, only dispose on explicit cleanup
        # self._engine remains available for future use

    def close(self) -> None:
        """Explicitly close and dispose of the engine."""
        if self.session:
            self.session.close()
            self.session = None

        if self._engine:
            self._engine.dispose()
            self._engine = None
