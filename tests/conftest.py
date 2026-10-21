import pytest
from app import app as flask_app
from database import init_db, get_db
@pytest.fixture()
def app(tmp_path):
    flask_app.config.update(TESTING=True, DATABASE_PATH=str(tmp_path/"test.db"), SECRET_KEY="test")
    with flask_app.app_context():
        init_db()
    yield flask_app
@pytest.fixture()
def client(app):
    return app.test_client()
