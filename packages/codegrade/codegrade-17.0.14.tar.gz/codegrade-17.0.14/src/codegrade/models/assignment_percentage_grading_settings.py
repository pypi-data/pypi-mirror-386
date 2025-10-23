"""The module that defines the ``AssignmentPercentageGradingSettings`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class AssignmentPercentageGradingSettings:
    """Representation of the percentage grading settings of an assignment."""

    #: The scale on which this assignment is graded. With 'percentage' the
    #: score can be between 0 and 100.
    scale: t.Literal["percentage"]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "scale",
                rqa.StringEnum("percentage"),
                doc="The scale on which this assignment is graded. With 'percentage' the score can be between 0 and 100.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "scale": to_dict(self.scale),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[AssignmentPercentageGradingSettings], d: t.Dict[str, t.Any]
    ) -> AssignmentPercentageGradingSettings:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            scale=parsed.scale,
        )
        res.raw_data = d
        return res
