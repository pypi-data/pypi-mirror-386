"""Tests for the session class."""

from impact_stack import jwt


class SessionTest:
    """Unit-tests for the Session class."""

    def test_init_generates_session_id(self):
        """Test that creating a new session automatically generates a unique session id."""
        session1 = jwt.Session("user-id", {"org": []})
        session2 = jwt.Session("user-id", {"org": []})
        assert session1.session_id
        assert session2.session_id
        assert session1.session_id != session2.session_id

    def test_custom_uuid_init(self):
        """Test passing a custom session uuid in the constructor."""
        uuid = "24861915-4617-4dc9-ac0e-2326c7538abc"
        session = jwt.Session("user-id", {"org": []}, uuid)
        data = session.to_token_data()
        assert data["user_claims"]["session_id"] == uuid

    def test_create_session_from_token(self):
        """Test creating a session from a token."""
        token = {
            "identity": "7fd8ecf2-c1fa-43fa-8661-3eafaec457b0",
            "sub": "7fd8ecf2-c1fa-43fa-8661-3eafaec457b0",
            "user_claims": {
                "roles": {"org1": ["admin"]},
                "session_id": "24861915-4617-4dc9-ac0e-2326c7538abc",
            },
        }
        session = jwt.Session.from_raw_token(token)
        assert session.to_token_data() == token

    def test_has_any_role_of_inherits_permissions(self):
        """Test permission inheritance."""
        roles = {
            "root": ["root-role"],
            "root>parent": ["parent-role"],
            "root>parent>org": ["org-role"],
            "root>other-parent": ["other-role"],
            "other-root": ["other-role"],
        }
        session = jwt.Session("user-id", roles)
        assert session.has_any_role_of(["root-role"], "root>parent>org")
        assert session.has_any_role_of(["parent-role"], "root>parent>org")
        assert session.has_any_role_of(["org-role"], "root>parent>org")
        assert not session.has_any_role_of(["other-role"], "root>parent>org")
        assert session.has_any_role_of([], "root")
        assert session.has_any_role_of([], "root>parent")
        assert session.has_any_role_of([], "root>parent>org")
        assert not session.has_any_role_of([], "unknown")

    def test_organizations_for_roles(self):
        """Test that it always returns a minimal set."""
        roles = {
            "root": ["root-role"],
            "root>parent": ["parent-role"],
            "root>parent>org": ["org-role"],
            "root>other-parent": ["other-role"],
            "other-root": ["other-role"],
        }
        session = jwt.Session("user-id", roles)
        assert session.organizations_for_roles(["root-role", "other-role"]) == {
            "root",
            "other-root",
        }
        assert session.organizations_for_roles(["parent-role", "org-role"]) == {
            "root>parent",
        }
