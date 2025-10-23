"""The module that defines the ``QualityTestLog`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa
from cg_maybe import Maybe, Nothing
from cg_maybe.utils import maybe_from_nullable

from ..utils import to_dict
from .quality_test_log_base import QualityTestLogBase


@dataclass
class QualityTestLog(QualityTestLogBase):
    """The full log for the QualityTest step type."""

    #: Should not be used.
    points: Maybe[float] = Nothing

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: QualityTestLogBase.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.OptionalArgument(
                    "points",
                    rqa.SimpleValue.float,
                    doc="Should not be used.",
                ),
            )
        ).use_readable_describe(True)
    )

    def __post_init__(self) -> None:
        getattr(super(), "__post_init__", lambda: None)()
        self.points = maybe_from_nullable(self.points)

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "stdout": to_dict(self.stdout),
            "stderr": to_dict(self.stderr),
            "exit_code": to_dict(self.exit_code),
            "time_spend": to_dict(self.time_spend),
        }
        if self.points.is_just:
            res["points"] = to_dict(self.points.value)
        return res

    @classmethod
    def from_dict(
        cls: t.Type[QualityTestLog], d: t.Dict[str, t.Any]
    ) -> QualityTestLog:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            stdout=parsed.stdout,
            stderr=parsed.stderr,
            exit_code=parsed.exit_code,
            time_spend=parsed.time_spend,
            points=parsed.points,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    import datetime

    from .auto_test_step_log_base import AutoTestStepLogBase
