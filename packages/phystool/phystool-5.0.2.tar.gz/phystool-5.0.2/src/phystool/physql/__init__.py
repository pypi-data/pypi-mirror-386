from contextlib import contextmanager
from logging import getLogger
from pathlib import Path
from typing import Generator

from sqlalchemy.engine.base import Engine
from sqlalchemy.engine.create import create_engine
from sqlalchemy.event.api import listens_for
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.orm.session import close_all_sessions


logger = getLogger(__name__)


@listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, _):
    # the sqlite3 driver will not set PRAGMA foreign_keys
    # if autocommit=False; set to True temporarily
    ac = dbapi_connection.autocommit
    dbapi_connection.autocommit = True

    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

    # restore previous autocommit setting
    dbapi_connection.autocommit = ac


class _PhysQL:
    def __init__(self) -> None:
        self._path: Path | None = None
        self._engine: Engine | None = None
        self._session: sessionmaker[Session] | None = None

    @contextmanager
    def __call__(self) -> Generator[Session, None, None]:
        if self._session is None:
            raise ValueError("The database session is not configured")
        session = self._session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def setup(self, path: Path) -> bool:
        """Set the path of the SQL file and return true if it exists"""
        self.close()
        self._path = path
        self._engine = create_engine(
            f"sqlite:///{self._path}",
            connect_args={"autocommit": False},
            echo=False,
        )
        self._session = sessionmaker(self._engine)
        logger.debug(f"SQLite connection to {self._path} successful")
        return self._path.exists()

    def close(self) -> None:
        if self._engine:
            self._engine.dispose()

    def remove(self) -> None:
        if self._path:
            self._path.unlink(missing_ok=True)

    def create_tables(self) -> None:
        if self._engine is None:
            raise ValueError("The database engine is not configured")
        BaseModel.metadata.create_all(self._engine)


class BaseModel(DeclarativeBase):
    pass


physql_db = _PhysQL()
