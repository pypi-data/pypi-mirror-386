"""The module that defines the ``ImportIntoCourseData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class ImportIntoCourseData:
    """Input data required for the `Course::ImportInto` operation."""

    #: The id of the course from which you want to import.
    from_course_id: int

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "from_course_id",
                rqa.SimpleValue.int,
                doc="The id of the course from which you want to import.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "from_course_id": to_dict(self.from_course_id),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[ImportIntoCourseData], d: t.Dict[str, t.Any]
    ) -> ImportIntoCourseData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            from_course_id=parsed.from_course_id,
        )
        res.raw_data = d
        return res
