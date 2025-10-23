"""The module that defines the ``AnyAutoTestStepAsJSON`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict
from .auto_test_step_base_as_json import AutoTestStepBaseAsJSON


@dataclass
class AnyAutoTestStepAsJSON(AutoTestStepBaseAsJSON):
    """The base output JSON for a step."""

    #: The id of this step
    id: int
    #: Description template for this step that is shown to students.
    description: t.Optional[str]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: AutoTestStepBaseAsJSON.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "id",
                    rqa.SimpleValue.int,
                    doc="The id of this step",
                ),
                rqa.RequiredArgument(
                    "description",
                    rqa.Nullable(rqa.SimpleValue.str),
                    doc="Description template for this step that is shown to students.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "id": to_dict(self.id),
            "description": to_dict(self.description),
            "name": to_dict(self.name),
            "weight": to_dict(self.weight),
            "hidden": to_dict(self.hidden),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[AnyAutoTestStepAsJSON], d: t.Dict[str, t.Any]
    ) -> AnyAutoTestStepAsJSON:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            id=parsed.id,
            description=parsed.description,
            name=parsed.name,
            weight=parsed.weight,
            hidden=parsed.hidden,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    pass
