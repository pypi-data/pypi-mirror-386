"""JWT session handling.

This module provides the common code-base needed for consuming auth-app JWTs.

The JWT’s claims provide the following custom clams:
- a user identifier (UUID)
- per organization roles
"""

from impact_stack.jwt.decorators import required
from impact_stack.jwt.manager import manager
from impact_stack.jwt.organizations import ancestors, iterate_parents
from impact_stack.jwt.permissions import check_access, has_access
from impact_stack.jwt.session import Session, get_current_session
