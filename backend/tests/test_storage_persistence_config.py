from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("DEER_FLOW_CONFIG_PATH", str(Path(__file__).resolve().parents[2] / "config.example.yaml"))

from store.config.storage_config import StorageConfig
from store.persistence.factory import _create_database_url, storage_config_from_database_config


def test_database_sqlite_config_maps_to_storage_config(tmp_path):
    database = SimpleNamespace(
        backend="sqlite",
        sqlite_dir=str(tmp_path),
        echo_sql=True,
        pool_size=9,
    )

    storage = storage_config_from_database_config(database)

    assert storage == StorageConfig(
        driver="sqlite",
        sqlite_dir=str(tmp_path),
        echo_sql=True,
        pool_size=9,
    )
    assert storage.sqlite_storage_path == str(tmp_path / "deerflow.db")


def test_database_memory_config_is_not_a_storage_backend():
    database = SimpleNamespace(backend="memory")

    with pytest.raises(ValueError, match="Unsupported database backend"):
        storage_config_from_database_config(database)


def test_database_postgres_config_preserves_url_and_pool_options():
    database = SimpleNamespace(
        backend="postgres",
        postgres_url="postgresql://user:pass@db.example:5544/deerflow",
        echo_sql=True,
        pool_size=11,
    )

    storage = storage_config_from_database_config(database)
    url = _create_database_url(storage)

    assert storage.driver == "postgres"
    assert storage.database_url == "postgresql://user:pass@db.example:5544/deerflow"
    assert storage.username == "user"
    assert storage.password == "pass"
    assert storage.host == "db.example"
    assert storage.port == 5544
    assert storage.db_name == "deerflow"
    assert storage.echo_sql is True
    assert storage.pool_size == 11
    assert url.drivername == "postgresql+asyncpg"
    assert url.database == "deerflow"


def test_database_postgres_requires_url():
    database = SimpleNamespace(backend="postgres", postgres_url="")

    with pytest.raises(ValueError, match="database.postgres_url is required"):
        storage_config_from_database_config(database)


def test_unsupported_database_backend_rejected():
    database = SimpleNamespace(backend="oracle")

    with pytest.raises(ValueError, match="Unsupported database backend"):
        storage_config_from_database_config(database)
