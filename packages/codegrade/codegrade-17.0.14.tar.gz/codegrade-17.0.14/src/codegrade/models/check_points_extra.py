"""The module that defines the ``CheckPointsExtra`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .check_points_data import CheckPointsData


@dataclass
class CheckPointsExtra:
    """The extra attrs of a CheckPoints step."""

    #: This is a CheckPoints step.
    type: t.Literal["check_points"]
    #: The data for the run program step.
    data: CheckPointsData

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "type",
                rqa.StringEnum("check_points"),
                doc="This is a CheckPoints step.",
            ),
            rqa.RequiredArgument(
                "data",
                parsers.ParserFor.make(CheckPointsData),
                doc="The data for the run program step.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "type": to_dict(self.type),
            "data": to_dict(self.data),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[CheckPointsExtra], d: t.Dict[str, t.Any]
    ) -> CheckPointsExtra:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            type=parsed.type,
            data=parsed.data,
        )
        res.raw_data = d
        return res
