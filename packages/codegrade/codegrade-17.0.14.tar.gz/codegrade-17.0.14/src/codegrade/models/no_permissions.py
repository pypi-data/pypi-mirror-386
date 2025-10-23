"""The module that defines the ``NoPermissions`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class NoPermissions:
    """Value returned when a user does not have a role within a tenant."""

    #: Whether the user has permissions within this tenant.
    has_perms: t.Literal[False]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "has_perms",
                rqa.LiteralBoolean(False),
                doc="Whether the user has permissions within this tenant.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "has_perms": to_dict(self.has_perms),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[NoPermissions], d: t.Dict[str, t.Any]
    ) -> NoPermissions:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            has_perms=parsed.has_perms,
        )
        res.raw_data = d
        return res
