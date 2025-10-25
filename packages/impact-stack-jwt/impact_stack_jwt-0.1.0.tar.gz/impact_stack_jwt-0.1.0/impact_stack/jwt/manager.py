"""Define a custom JWTManager instance."""

import flask
import flask_jwt_extended

from impact_stack.jwt.session import Session


class Manager(flask_jwt_extended.JWTManager):
    """A JWTManager subclass with a bit of custom behaviour."""

    @staticmethod
    def _push_context_callback(session: Session, context):  # pylint: disable=method-hidden
        """Implement a default push context callback doing nothing."""

    def push_context(self, session):
        """Push data to the request context."""
        self._push_context_callback(session, flask.g)

    def push_context_callback(self, callback):
        """Register a callback for pushing data to the request context.

        Most commonly this callback would load a user or organization object from the database to be
        used later in the request. The callback can throw werkzeug.exceptions to interrupt the
        request handling.
        """
        self._push_context_callback = callback


manager = Manager()


@manager.user_lookup_loader
def create_session(_jwt_header, jwt_data):
    """Create a session object from token data.

    The session is made available in either of:
    - flask_jwt_extended.current_user
    - flask_jwt_extended.get_current_user()
    - moflask.jwt.get_current_session()
    with the latter being considered the most idiomatic.
    """
    return Session.from_raw_token(jwt_data)


@manager.additional_claims_loader
def session_to_token(session: Session):
    """Generate JWT claims that represent the session."""
    return session.to_token_data()


# Deactivate the default callback. session_to_token takes care of everything.
manager.user_identity_loader(lambda session: None)
