"""Helpers for checking permissions on resources.

Each such resource must have a organization assigned.

Permission checking has two modes:
   - editing: Permissions apply only to the session‘s organization and sub-organizations.
   - reading: Permissions also apply to ancestor organizations.
"""

import typing as t

import werkzeug.exceptions

from impact_stack.jwt.organizations import ancestors
from impact_stack.jwt.session import Session, get_current_session


def check_access(organization, roles=None, *, edit=False):
    """Abort the request if the current user does not have access."""
    roles = roles if roles is not None else ["app", "editor"]
    if not has_access(organization, roles, edit=edit):
        raise werkzeug.exceptions.Forbidden("Not authorized.")


def has_access(organization, roles: t.Iterable[str], *, edit=False) -> bool:
    """Check whether the current user has access to data from an organization."""
    session: Session = get_current_session()
    if session.has_any_role_of(roles, organization):
        return True  # Access because one of the roles applies directly.
    orgs_inherited = ancestors(session.organizations_for_roles(roles))
    if not edit and organization in orgs_inherited:
        return True  # Read-only access for datasets of parent organizations.
    return False
