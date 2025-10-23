"""
© Ocado Group
Created on 01/02/2024 at 14:34:04(+00:00).
"""

import typing as t

from ....request import HttpRequest
from .base import BaseBackend


class EmailBackend(BaseBackend):
    """Authenticate a user by checking their email and password."""

    def authenticate(  # type: ignore[override]
        self,
        request: t.Optional[HttpRequest],
        email: t.Optional[str] = None,
        password: t.Optional[str] = None,
        **kwargs
    ):
        if email is None or password is None:
            return None

        # pylint: disable=duplicate-code
        try:
            user = self.user_class.objects.get(email__iexact=email)
            if user.check_password(password):
                return user
        except self.user_class.DoesNotExist:
            return None
        # pylint: enable=duplicate-code

        return None
