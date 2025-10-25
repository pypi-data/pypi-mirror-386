"""Define access check decorators."""

import functools
import typing as t

import flask
import flask_jwt_extended
import werkzeug.exceptions

from impact_stack.jwt.manager import manager
from impact_stack.jwt.session import Session, get_current_session


def check_roles(session: Session, admitted_roles: t.Iterable[str], org: str | None = None):
    """Check whether the session has any of the admitted roles."""
    if not session.has_any_role_of(admitted_roles, org):
        raise werkzeug.exceptions.Forbidden("The user has none of the admitted roles.")


def required(admitted_roles: t.Iterable[str] | None = None, optional=False, **kwargs):
    """Require JWT authentication for a route.

    This decorator is a replacement for all of the flask_jwt_extended decorators.

    If you decorate an endpoint with this, it will ensure that the requester
    has a valid access token before allowing the endpoint to be called.

    The behaviour can be configured using the keyword parameters:
    - admitted_roles: Only allow session with any of these roles to access the route.
    """
    decorator_kwargs = kwargs

    def wrap(wrapped_fn):
        @functools.wraps(wrapped_fn)
        def wrapper(*args, **kwargs):
            if flask_jwt_extended.verify_jwt_in_request(optional=optional, **decorator_kwargs):
                session = get_current_session()
            else:  # Authentication is optional or the request method is exempt.
                session = Session.create_anonymous_session()
                # pylint: disable=protected-access
                flask.g._jwt_extended_jwt_user = {"loaded_user": session}
            manager.push_context(session)
            if session and admitted_roles is not None:
                check_roles(session, admitted_roles)
            return wrapped_fn(*args, **kwargs)

        return wrapper

    return wrap
