"""The module that defines the ``JsonPatchSubmitTypesAssignment`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa
from cg_maybe import Maybe, Nothing
from cg_maybe.utils import maybe_from_nullable

from .. import parsers
from ..utils import to_dict
from .webhook_configuration_disabled_as_json import (
    WebhookConfigurationDisabledAsJSON,
)
from .webhook_configuration_enabled_as_json import (
    WebhookConfigurationEnabledAsJSON,
)


@dataclass
class JsonPatchSubmitTypesAssignment:
    """ """

    #: Should students be allowed to make submissions by uploading files
    files_upload_enabled: Maybe[bool] = Nothing
    #: Should students be allowed to make submissions using git webhooks
    webhook_upload_enabled: Maybe[bool] = Nothing
    #: The configuration for the Webhook upload for this assignment
    webhook_configuration: Maybe[
        t.Union[
            WebhookConfigurationEnabledAsJSON,
            WebhookConfigurationDisabledAsJSON,
        ]
    ] = Nothing
    #: Should students be allowed to make submissions using the editor
    editor_upload_enabled: Maybe[bool] = Nothing

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.OptionalArgument(
                "files_upload_enabled",
                rqa.SimpleValue.bool,
                doc="Should students be allowed to make submissions by uploading files",
            ),
            rqa.OptionalArgument(
                "webhook_upload_enabled",
                rqa.SimpleValue.bool,
                doc="Should students be allowed to make submissions using git webhooks",
            ),
            rqa.OptionalArgument(
                "webhook_configuration",
                parsers.make_union(
                    parsers.ParserFor.make(WebhookConfigurationEnabledAsJSON),
                    parsers.ParserFor.make(WebhookConfigurationDisabledAsJSON),
                ),
                doc="The configuration for the Webhook upload for this assignment",
            ),
            rqa.OptionalArgument(
                "editor_upload_enabled",
                rqa.SimpleValue.bool,
                doc="Should students be allowed to make submissions using the editor",
            ),
        ).use_readable_describe(True)
    )

    def __post_init__(self) -> None:
        getattr(super(), "__post_init__", lambda: None)()
        self.files_upload_enabled = maybe_from_nullable(
            self.files_upload_enabled
        )
        self.webhook_upload_enabled = maybe_from_nullable(
            self.webhook_upload_enabled
        )
        self.webhook_configuration = maybe_from_nullable(
            self.webhook_configuration
        )
        self.editor_upload_enabled = maybe_from_nullable(
            self.editor_upload_enabled
        )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {}
        if self.files_upload_enabled.is_just:
            res["files_upload_enabled"] = to_dict(
                self.files_upload_enabled.value
            )
        if self.webhook_upload_enabled.is_just:
            res["webhook_upload_enabled"] = to_dict(
                self.webhook_upload_enabled.value
            )
        if self.webhook_configuration.is_just:
            res["webhook_configuration"] = to_dict(
                self.webhook_configuration.value
            )
        if self.editor_upload_enabled.is_just:
            res["editor_upload_enabled"] = to_dict(
                self.editor_upload_enabled.value
            )
        return res

    @classmethod
    def from_dict(
        cls: t.Type[JsonPatchSubmitTypesAssignment], d: t.Dict[str, t.Any]
    ) -> JsonPatchSubmitTypesAssignment:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            files_upload_enabled=parsed.files_upload_enabled,
            webhook_upload_enabled=parsed.webhook_upload_enabled,
            webhook_configuration=parsed.webhook_configuration,
            editor_upload_enabled=parsed.editor_upload_enabled,
        )
        res.raw_data = d
        return res
