"""Session class and helpers."""

import typing as t
import uuid

import flask
import flask_jwt_extended

from impact_stack.jwt.organizations import iterate_parents


class Session:
    """Object that represents a user’s session for a specific organization."""

    @classmethod
    def from_raw_token(cls, token: dict):
        """Create a session from raw JWT token data."""
        claims = token["user_claims"]
        return cls(token["identity"], claims["roles"], claims["session_id"])

    @classmethod
    def create_anonymous_session(cls):
        """Create an anonymous session from the request headers."""
        org = flask.request.headers.get("x-ist-org", None)
        return cls(None, {org: []} if org else {})

    def __init__(
        self,
        identity: str | None,
        roles: t.Mapping[str, t.Iterable[str]] | None = None,
        custom_uuid: str | None = None,
    ):
        """Create a new session instance."""
        self.identity = identity
        self.roles = {org: frozenset(r) for org, r in roles.items()} if roles else {}
        self.session_id = custom_uuid or str(uuid.uuid4())

    def has_any_role_of(self, roles: t.Iterable[str], org: str | None = None) -> bool:
        """Check if the session has any of the given roles for the organization.

        Args:
            roles: The admitted roles. If empty then any list of roles will pass the check.
            org: Check roles for this organization or its parents. If None is passed the method
            returns True if the session has any of the roles for any organization.
        """
        roles = frozenset(roles)
        orgs = iterate_parents(org, include_self=True) if org is not None else self.roles.keys()
        return any(not roles or self.roles[o] & roles for o in orgs if o in self.roles)

    def organizations_for_roles(self, admitted_roles: t.Iterable[str]) -> frozenset[str]:
        """Get organizations for which the session has at least one of the given roles.

        This method is usually used to determine which ressources the session should have
        access to.

        Note that passing an empty list of admitted_roles means that any list of roles for an
        organization satisfies the condition, even an empty one.

        Returns:
            A set of organizations for which the session has any of the given roles. If both a
            parent and a parent>sub organization would be part of the set, then only the parent is
            returned.
            This is the minimal set of organizations so that has_any_role_of() would return True
            for all of them and any of their sub-organizations.
        """
        roles = frozenset(admitted_roles)
        orgs = frozenset(o for o, r in self.roles.items() if not roles or r & roles)
        cleaned = frozenset(o for o in orgs if not any(p in orgs for p in iterate_parents(o)))
        return cleaned

    def to_token_data(self):
        """Return the session object turned into the token data structure.

        This is the inverse of from_raw_token().
        """
        return {
            "identity": self.identity,
            "sub": self.identity,
            "user_claims": {
                "session_id": self.session_id,
                "roles": {org: list(roles) for org, roles in self.roles.items()},
            },
        }


get_current_session: t.Callable[[], Session] = flask_jwt_extended.get_current_user
