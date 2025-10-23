"""The module that defines the ``PatchSnippetData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class PatchSnippetData:
    """Input data required for the `Snippet::Patch` operation."""

    #: The key of the new or existing snippet.
    key: str
    #: The new value of the snippet.
    value: str

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "key",
                rqa.SimpleValue.str,
                doc="The key of the new or existing snippet.",
            ),
            rqa.RequiredArgument(
                "value",
                rqa.SimpleValue.str,
                doc="The new value of the snippet.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "key": to_dict(self.key),
            "value": to_dict(self.value),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[PatchSnippetData], d: t.Dict[str, t.Any]
    ) -> PatchSnippetData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            key=parsed.key,
            value=parsed.value,
        )
        res.raw_data = d
        return res
