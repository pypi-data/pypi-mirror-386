"""The module that defines the ``BaseCouponWithoutCode`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict
from .base_coupon import BaseCoupon


@dataclass
class BaseCouponWithoutCode(BaseCoupon):
    """A coupon where you don't have the permission to see the code."""

    #: This is a coupon without a code.
    type: t.Literal["coupon-without-code"]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: BaseCoupon.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "type",
                    rqa.StringEnum("coupon-without-code"),
                    doc="This is a coupon without a code.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "type": to_dict(self.type),
            "id": to_dict(self.id),
            "created_at": to_dict(self.created_at),
            "limit": to_dict(self.limit),
            "used_amount": to_dict(self.used_amount),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[BaseCouponWithoutCode], d: t.Dict[str, t.Any]
    ) -> BaseCouponWithoutCode:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            type=parsed.type,
            id=parsed.id,
            created_at=parsed.created_at,
            limit=parsed.limit,
            used_amount=parsed.used_amount,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    import datetime
