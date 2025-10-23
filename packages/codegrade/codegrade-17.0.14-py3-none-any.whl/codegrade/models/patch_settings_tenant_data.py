"""The module that defines the ``PatchSettingsTenantData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .site_setting_input import SiteSettingInput, SiteSettingInputParser


@dataclass
class PatchSettingsTenantData:
    """Input data required for the `Tenant::PatchSettings` operation."""

    #: The items you want to update
    updates: t.Sequence[SiteSettingInput]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "updates",
                rqa.List(SiteSettingInputParser),
                doc="The items you want to update",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "updates": to_dict(self.updates),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[PatchSettingsTenantData], d: t.Dict[str, t.Any]
    ) -> PatchSettingsTenantData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            updates=parsed.updates,
        )
        res.raw_data = d
        return res
