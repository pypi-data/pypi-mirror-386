"""A client library for accessing CodeGrade

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

import typing as _t
from functools import wraps as _wraps

from . import paginated as paginated
from .client import AuthenticatedClient, Client

try:
    from typing import ParamSpec as _ParamSpec
except ImportError:
    from typing_extensions import (  # type: ignore[assignment]
        ParamSpec as _ParamSpec,
    )

__all__ = ("login", "AuthenticatedClient", "Client", "login_from_cli")
__version__ = "17.0.14"

_P = _ParamSpec("_P")
_T = _t.TypeVar("_T")


def _copy_func(func: _t.Callable[_P, _T]) -> _t.Callable[_P, _T]:
    @_wraps(func)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
        return func(*args, **kwargs)

    return wrapper


login = _copy_func(AuthenticatedClient.get)

login_from_cli = _copy_func(AuthenticatedClient.get_from_cli)

login_from_cli_for_course = _copy_func(
    AuthenticatedClient.get_from_cli_for_course
)


login.__name__ = "login"
login.__doc__ = """Get an :class:`.AuthenticatedClient` by logging in with your
    username and password.

    .. code-block:: python

        with codegrade.login(
            username='my-username',
            password=os.getenv('CG_PASS'),
            tenant='My University',
        ) as client:
            print('Hi I am {}'.format(client.user.get().name)

    :param username: Your CodeGrade username.
    :param password: Your CodeGrade password, if you do not know your
        password you can set it by following `these steps.
        <https://help.codegrade.com/faq/setting-up-a-password-for-my-account>`_
    :param tenant: The id or name of your tenant in CodeGrade. This is the
        name you click on the login screen.
    :param host: The CodeGrade instance you want to use.

    :returns: A client that you can use to do authenticated requests to
              CodeGrade. We advise you to use it in combination with a
              ``with`` block (i.e. as a contextmanager) for the highest
              efficiency.
    """

login_from_cli.__name__ = "login_from_cli"
login_from_cli.__doc__ = """Get an :class:`.AuthenticatedClient` by logging in through command
    line interface.

    .. code-block::

        >>> import codegrade
        >>> codegrade.login_from_cli()
        Your instance [default: https://app.codegra.de]: https://app.codegra.de
        [ 1] CodeGrade Sandbox
        [ 2] Academy of Interactive Entertainment
        ...
        Select your tenant: 1
        Selecting CodeGrade Sandbox
        Your username: my-username
        Your password:
        <codegrade.client.AuthenticatedClient object at 0x106f139a0>

    :returns: A client that you can use to do authenticated requests to
              CodeGrade. We advise you to use it in combination with a
              ``with`` block (i.e. as a contextmanager) for the highest
              efficiency.
    """

login_from_cli_for_course.__name__ = "login_from_cli_for_course"
login_from_cli_for_course.__doc__ = """Get an :class:`.AuthenticatedClient` with permissions restricted to a single
    course by logging in through command line interface.

    .. code-block::

        >>> import codegrade
        >>> codegrade.login_from_cli_for_course()
        Your instance [default: https://app.codegra.de]: https://app.codegra.de
        [ 1] CodeGrade Sandbox
        [ 2] Academy of Interactive Entertainment
        ...
        Select your tenant: 1
        Selecting CodeGrade Sandbox
        Your username: my-username
        Your password:
        [ 1] Introduction to Programming
        [ 2] Advanced Operating Systems
        ...
        Select your course: 2
        <codegrade.client.AuthenticatedClient object at 0x106f139a0>

    :returns: A client that you can use to do authenticated requests to
              CodeGrade, limited in scope to a single course. We advise
              you to use it in combination with a ``with`` block (i.e.
              as a contextmanager) for the highest efficiency.
    """
