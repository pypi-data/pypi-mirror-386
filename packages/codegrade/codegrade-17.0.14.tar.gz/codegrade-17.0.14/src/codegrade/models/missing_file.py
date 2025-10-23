"""The module that defines the ``MissingFile`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .file_type import FileType


@dataclass
class MissingFile:
    """A file that was required but is missing."""

    #: The type of rule.
    file_type: FileType
    #: The filename of the missing required file.
    name: str
    #: The type of the rule.
    rule_type: t.Literal["require"]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "file_type",
                rqa.EnumValue(FileType),
                doc="The type of rule.",
            ),
            rqa.RequiredArgument(
                "name",
                rqa.SimpleValue.str,
                doc="The filename of the missing required file.",
            ),
            rqa.RequiredArgument(
                "rule_type",
                rqa.StringEnum("require"),
                doc="The type of the rule.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "file_type": to_dict(self.file_type),
            "name": to_dict(self.name),
            "rule_type": to_dict(self.rule_type),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[MissingFile], d: t.Dict[str, t.Any]
    ) -> MissingFile:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            file_type=parsed.file_type,
            name=parsed.name,
            rule_type=parsed.rule_type,
        )
        res.raw_data = d
        return res
