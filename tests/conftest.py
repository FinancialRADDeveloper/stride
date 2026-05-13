import pytest

from stride.db import get_connection, run_migrations


@pytest.fixture
def db():
    conn = get_connection(":memory:")
    run_migrations(conn)
    yield conn
    conn.close()
