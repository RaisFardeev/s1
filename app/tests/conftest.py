import pytest
from .. import app as flask_app


@pytest.fixture
def app():
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()