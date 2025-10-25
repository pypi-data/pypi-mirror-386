"""Define common pytest fixtures."""

import flask
import pytest

from impact_stack import jwt


@pytest.fixture(name="protected_app")
def fixture_protected_app():
    """Create an app with one JWT protected route."""
    app = flask.Flask("test")
    app.config["JWT_SECRET_KEY"] = "test-secret-key"
    jwt.manager.init_app(app)

    @app.route("/", methods=["GET", "OPTIONS"])
    @jwt.required(admitted_roles=["app"])
    def dump_session():
        session = jwt.get_current_session()
        return flask.jsonify(session.to_token_data())

    @app.route("/optional")
    @jwt.required(optional=True)
    def dump_session2():
        session = jwt.get_current_session()
        return flask.jsonify(session.to_token_data())

    with app.app_context():
        yield app
