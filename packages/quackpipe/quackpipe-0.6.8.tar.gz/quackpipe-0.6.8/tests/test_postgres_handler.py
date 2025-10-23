"""
tests/test_postgres_handler.py

This file contains pytest tests for the PostgresHandler class in quackpipe.
The tests are written as standalone functions, leveraging pytest features
like parametrize and fixtures for setup.
"""
import os

import pytest

import quackpipe
from quackpipe import configure_secret_provider
from quackpipe.sources.postgres import PostgresHandler


@pytest.fixture(scope="function")
def postgres_env_vars(monkeypatch) -> dict[str, str]:
    secret_name = 'pg_creds'
    # Use monkeypatch to set the environment variables for the secret bundle.
    monkeypatch.setenv(f"{secret_name.upper()}_DATABASE", "testdb")
    monkeypatch.setenv(f"{secret_name.upper()}_USER", "pguser")
    monkeypatch.setenv(f"{secret_name.upper()}_PASSWORD", "pgpass")
    monkeypatch.setenv(f"{secret_name.upper()}_HOST", "localhost")
    # has set the environment variables. This ensures the provider reads the
    # correct state for this specific test run.
    configure_secret_provider(env_file=None)
    return dict(os.environ)


def test_postgres_handler_properties(postgres_env_vars):
    """Verify that the handler correctly reports its static properties."""
    # Arrange
    handler = PostgresHandler({
        "connection_name": "pg_test",
        "secret_name": "pg_creds",
        "port": 5433
        # read_only defaults to True
    })

    # Assert
    assert handler.required_plugins == ["postgres"]
    assert handler.source_type == "postgres"


@pytest.mark.parametrize(
    "test_id, context, expected_sql_parts, unexpected_sql_parts",
    [
        (
                "basic_config_is_readonly",
                {
                    "connection_name": "pg_test",
                    "secret_name": "pg_creds",
                    "port": 5433
                    # read_only defaults to True
                },
                [
                    "CREATE OR REPLACE SECRET pg_test_secret",
                    "ATTACH 'dbname=testdb' AS pg_test (TYPE POSTGRES, SECRET 'pg_test_secret', READ_ONLY);"
                ],
                []  # No unexpected parts
        ),
        (
                "read_write_config",
                {
                    "connection_name": "pg_rw",
                    "secret_name": "pg_creds",
                    "port": 5432,
                    "read_only": False  # Explicitly set to read-write
                },
                [
                    "CREATE OR REPLACE SECRET pg_rw_secret",
                    "ATTACH 'dbname=testdb' AS pg_rw (TYPE POSTGRES, SECRET 'pg_rw_secret');"
                ],
                ["READ_ONLY"]  # Should NOT contain the READ_ONLY flag
        ),
        (
                "with_table_views",
                {
                    "connection_name": "pg_views",
                    "secret_name": "pg_creds",
                    "port": 5432,
                    "tables": ["users", "products"]
                },
                [
                    "CREATE OR REPLACE SECRET pg_views_secret",
                    "ATTACH 'dbname=testdb' AS pg_views",
                    "READ_ONLY",  # Default is read-only
                    "CREATE OR REPLACE VIEW pg_views_users AS SELECT * FROM pg_views.users;",
                    "CREATE OR REPLACE VIEW pg_views_products AS SELECT * FROM pg_views.products;"
                ],
                []
        ),
    ]
)
def test_postgres_render_sql(postgres_env_vars, test_id, context, expected_sql_parts, unexpected_sql_parts):
    """
    Tests that the PostgresHandler's render_sql method correctly generates
    a CREATE SECRET statement followed by an ATTACH statement.
    """
    handler = PostgresHandler(context)

    # Act
    generated_sql = handler.render_sql()

    # Assert
    # Normalize whitespace for robust comparison
    normalized_sql = " ".join(generated_sql.split())

    for part in expected_sql_parts:
        normalized_part = " ".join(part.split())
        assert normalized_part in normalized_sql

    for part in unexpected_sql_parts:
        assert part not in normalized_sql


def test_postgres_handler_render_sql():
    """Test PostgresHandler SQL rendering."""

    context = {
        'database': 'testdb',
        'user': 'testuser',
        'password': 'testpass',
        'host': 'localhost',
        'port': 5432,
        'connection_name': 'pg_main',
        'read_only': True,
        'tables': ['users', 'orders']
    }
    handler = PostgresHandler(context)

    sql = handler.render_sql()

    assert "ATTACH" in sql
    assert "pg_main" in sql
    assert "POSTGRES" in sql
    assert "READ_ONLY" in sql
    assert "CREATE OR REPLACE VIEW pg_main_users" in sql
    assert "CREATE OR REPLACE VIEW pg_main_orders" in sql


def test_postgres_handler_no_tables():
    """Test PostgresHandler without tables."""

    context = {
        'database': 'testdb',
        'user': 'testuser',
        'password': 'testpass',
        'host': 'localhost',
        'port': 5432,
        'connection_name': 'pg_main',
        'read_only': False
    }

    sql = PostgresHandler(context).render_sql()

    assert "ATTACH" in sql
    assert "READ_ONLY" not in sql
    assert "CREATE OR REPLACE VIEW" not in sql


def test_integration_with_postgres_e2e(quackpipe_with_pg_source, postgres_container_with_data):
    with quackpipe_with_pg_source.session() as con:
        # the name of the source 'pg_source' should match the value of POSTGRES_SOURCE_NAME in the fixtures
        results = con.execute(
            "FROM pg_source.company.employees"
        ).fetchall()
        assert len(results) == 5

        results = con.execute(
            "FROM pg_source.company.employees WHERE department='Engineering'"
        ).fetchall()
        assert len(results) == 2
        assert results[0][1] == "Alice"
        assert results[1][1] == "Diana"

        results = con.execute('FROM pg_source.vessels').fetchall()
        assert len(results) == 5


@pytest.fixture(params=["all_env", "mixed", "all_config"])
def pg_case(request, postgres_container, quackpipe_config_files):
    """
    Parametrized fixture that prepares different config/env setups
    for Postgres. Expands host/port dynamically from the running container.
    """
    host = postgres_container.get_container_host_ip()
    port = str(postgres_container.get_exposed_port(5432))

    if request.param == "all_env":
        source_config = {"read_only": False}
        env_vars = {
            "MY_DB_DATABASE": "test",
            "MY_DB_USER": "test",
            "MY_DB_PASSWORD": "test",
            "MY_DB_HOST": host,
            "MY_DB_PORT": port,
        }
    elif request.param == "mixed":
        source_config = {"database": "test", "host": host, "port": port, "read_only": False}
        env_vars = {"MY_DB_USER": "test", "MY_DB_PASSWORD": "test"}
    elif request.param == "all_config":
        source_config = {
            "database": "test",
            "user": "test",
            "password": "test",
            "host": host,
            "port": port,
            "read_only": False,
        }
        env_vars = {}
    else:
        raise ValueError(f"Unknown case {request.param}")

    return quackpipe_config_files(source_config, env_vars, source_name="my_postgres", source_type="postgres", secret_name="my_db")


def test_postgres_configs(pg_case):
    config_file, env_file = pg_case

    with quackpipe.session(
        config_path=str(config_file),
        env_file=str(env_file),
        sources=["my_postgres"],
    ) as con:
        con.execute("CREATE TABLE my_postgres.tbl (id INTEGER, name VARCHAR);")
        con.execute("INSERT INTO my_postgres.tbl VALUES (42, 'DuckDB');")
        assert len(con.execute("FROM my_postgres.tbl").df()) == 1
        con.execute("DROP TABLE my_postgres.tbl;")
