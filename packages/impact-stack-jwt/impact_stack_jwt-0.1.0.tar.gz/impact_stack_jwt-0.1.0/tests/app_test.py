"""Test behaviour of the test flask app."""

import flask_jwt_extended

from impact_stack import jwt


def test_getting_session_data_in_authorized_request(protected_app):
    """Send an authorized request to the endpoint."""
    session = jwt.Session("user-id", {"organization": ["app"]})
    with protected_app.app_context():
        token = flask_jwt_extended.create_access_token(session)

    with protected_app.test_client() as client:
        response = client.get("/", headers={"Authorization": "Bearer " + token})
    assert response.status_code == 200
    assert response.json["identity"] == "user-id"
    assert response.json["user_claims"]["roles"] == {"organization": ["app"]}
    assert response.json["user_claims"]["session_id"]


def test_getting_injected_session_data(protected_app, jwt_inject_session):
    """Inject session using the settings."""
    session = jwt.Session("user-id", {"organization": ["app"]})

    with jwt_inject_session(session):
        with protected_app.test_client() as client:
            response = client.get("/")

    assert response.status_code == 200
    assert response.json["identity"] == "user-id"
    assert response.json["user_claims"]["roles"] == {"organization": ["app"]}


def test_denying_access_without_an_admitted_role(protected_app, jwt_inject_session):
    """Test the error response given when the JWT doesn’t have any of the admitted roles."""
    session = jwt.Session("user-id", {"organization": "not-app"})

    with jwt_inject_session(session):
        with protected_app.test_client() as client:
            response = client.get("/")

    assert response.status_code == 403
    assert "The user has none of the admitted roles" in response.data.decode()


def test_exempt_request_method_for_non_optional_wrapper(protected_app):
    """Test that OPTION requests get an anonymous session on protected routes."""
    with protected_app.test_client() as client:
        response = client.options("/")

    assert response.status_code == 403


def test_anonymous_session_with_optional(protected_app):
    """Test that a session is created on-the-fly for anonymous users."""
    with protected_app.test_client() as client:
        response = client.get("/optional")
    assert response.status_code == 200
    assert response.json["identity"] is None
    assert response.json["user_claims"]["roles"] == {}


def test_anonymous_session_with_organization(protected_app):
    """Test that sessions for anonymous requests read the x-ist-org header."""
    with protected_app.test_client() as client:
        # Showcase that the header name is not case-sensitive.
        response = client.get("/optional", headers={"X-IsT-OrG": "test-org"})
    assert response.status_code == 200
    assert response.json["identity"] is None
    assert response.json["user_claims"]["roles"] == {"test-org": []}
