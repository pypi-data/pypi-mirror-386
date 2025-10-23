"""The module that defines the ``CustomOutputAsJSON`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict
from .any_non_redacted_auto_test_step_as_json import (
    AnyNonRedactedAutoTestStepAsJSON,
)
from .custom_output_extra import CustomOutputExtra


@dataclass
class CustomOutputAsJSON(AnyNonRedactedAutoTestStepAsJSON, CustomOutputExtra):
    """A CustomOutput step as JSON."""

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: AnyNonRedactedAutoTestStepAsJSON.data_parser.parser.combine(
            CustomOutputExtra.data_parser.parser
        )
        .combine(rqa.FixedMapping())
        .use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "redacted": to_dict(self.redacted),
            "id": to_dict(self.id),
            "description": to_dict(self.description),
            "name": to_dict(self.name),
            "weight": to_dict(self.weight),
            "hidden": to_dict(self.hidden),
            "type": to_dict(self.type),
            "data": to_dict(self.data),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[CustomOutputAsJSON], d: t.Dict[str, t.Any]
    ) -> CustomOutputAsJSON:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            redacted=parsed.redacted,
            id=parsed.id,
            description=parsed.description,
            name=parsed.name,
            weight=parsed.weight,
            hidden=parsed.hidden,
            type=parsed.type,
            data=parsed.data,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    from .any_auto_test_step_as_json import AnyAutoTestStepAsJSON
    from .auto_test_step_base_as_json import AutoTestStepBaseAsJSON
    from .custom_output_data import CustomOutputData
