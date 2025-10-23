"""The module that defines the ``TenantPrice`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .base_price import BasePrice
from .tenant_of_tenant_price import TenantOfTenantPrice


@dataclass
class TenantPrice(BasePrice):
    """A tenant price as json."""

    #: The tenant that is connected to this price.
    tenant: TenantOfTenantPrice

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: BasePrice.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "tenant",
                    parsers.ParserFor.make(TenantOfTenantPrice),
                    doc="The tenant that is connected to this price.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "tenant": to_dict(self.tenant),
            "id": to_dict(self.id),
            "currency": to_dict(self.currency),
            "amount": to_dict(self.amount),
            "refund_period": to_dict(self.refund_period),
            "tax_behavior": to_dict(self.tax_behavior),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[TenantPrice], d: t.Dict[str, t.Any]
    ) -> TenantPrice:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            tenant=parsed.tenant,
            id=parsed.id,
            currency=parsed.currency,
            amount=parsed.amount,
            refund_period=parsed.refund_period,
            tax_behavior=parsed.tax_behavior,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    import datetime

    from .currency import Currency
    from .tax_behavior import TaxBehavior
