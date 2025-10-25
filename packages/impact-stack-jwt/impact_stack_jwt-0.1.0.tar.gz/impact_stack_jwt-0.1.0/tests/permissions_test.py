"""Tests for the permissions utilities."""

from unittest import mock

import pytest
import werkzeug.exceptions

from impact_stack import jwt


@pytest.mark.usefixtures("protected_app")
def test_has_access_gives_read_access_to_parent_orgs(jwt_inject_session):
    """Check access to data of parent organizations."""
    session = jwt.Session("user-id", {"impact-stack>example": ["editor"]})
    with jwt_inject_session(session):
        jwt.required(["editor"])(lambda: None)()
        assert not jwt.has_access("impact-stack", ["editor"], edit=True)
        assert jwt.has_access("impact-stack", ["editor"], edit=False)
        assert jwt.has_access("impact-stack>example", ["editor"], edit=True)


@mock.patch("impact_stack.jwt.permissions.has_access")
def test_check_access(has_access_mock: mock.MagicMock):
    """Test exceptions thrown by check access."""
    has_access_mock.return_value = False
    with pytest.raises(werkzeug.exceptions.Forbidden):
        jwt.check_access("org", ["editor"], edit=True)
    assert has_access_mock.call_count == 1
    assert has_access_mock.mock_calls[0] == mock.call("org", ["editor"], edit=True)

    has_access_mock.return_value = True
    jwt.check_access("org", ["editor"], edit=True)
    assert has_access_mock.call_count == 2
