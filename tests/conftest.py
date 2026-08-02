"""
Shared pytest fixtures for the PrepPath test suite.

The `client` fixture spins up the Flask app against a fresh, temporary
SQLite database for every test, so tests never touch the real
preppath.db and never affect each other.
"""
import os
import sys
import sqlite3
import tempfile

import pytest

# Make sure app.py (in the project root) can be imported from tests/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as flask_app_module


@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()

    def get_test_db():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # Point the app at the temporary test database instead of the real one
    flask_app_module.get_db = get_test_db

    flask_app_module.app.config["TESTING"] = True
    flask_app_module.app.config["WTF_CSRF_ENABLED"] = False  # off by default; re-enabled in the CSRF test

    flask_app_module.init_db()

    with flask_app_module.app.test_client() as test_client:
        yield test_client

    os.close(db_fd)
    os.unlink(db_path)