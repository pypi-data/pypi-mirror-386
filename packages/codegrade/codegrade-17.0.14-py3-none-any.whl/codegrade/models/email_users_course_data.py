"""The module that defines the ``EmailUsersCourseData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .user_input import UserInput


@dataclass
class EmailUsersCourseData:
    """Input data required for the `Course::EmailUsers` operation."""

    #: The subject of the email
    subject: str
    #: The plain text body of the email
    body: str
    #: Email all users of the course except those specified in `usernames`. If
    #: `false` we will email only the users specified in `usernames`.
    email_all_users: bool
    #: The usernames of the users to email (or not to email, depending on the
    #: value of `email_all_users`).
    users: t.Sequence[UserInput]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "subject",
                rqa.SimpleValue.str,
                doc="The subject of the email",
            ),
            rqa.RequiredArgument(
                "body",
                rqa.SimpleValue.str,
                doc="The plain text body of the email",
            ),
            rqa.RequiredArgument(
                "email_all_users",
                rqa.SimpleValue.bool,
                doc="Email all users of the course except those specified in `usernames`. If `false` we will email only the users specified in `usernames`.",
            ),
            rqa.RequiredArgument(
                "users",
                rqa.List(parsers.ParserFor.make(UserInput)),
                doc="The usernames of the users to email (or not to email, depending on the value of `email_all_users`).",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "subject": to_dict(self.subject),
            "body": to_dict(self.body),
            "email_all_users": to_dict(self.email_all_users),
            "users": to_dict(self.users),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[EmailUsersCourseData], d: t.Dict[str, t.Any]
    ) -> EmailUsersCourseData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            subject=parsed.subject,
            body=parsed.body,
            email_all_users=parsed.email_all_users,
            users=parsed.users,
        )
        res.raw_data = d
        return res
