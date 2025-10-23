"""The module that defines the ``ExtendedAssignment`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import datetime
import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .assignment import Assignment
from .assignment_anonymization_algo import AssignmentAnonymizationAlgo
from .assignment_peer_feedback_settings import AssignmentPeerFeedbackSettings
from .assignment_percentage_grading_settings import (
    AssignmentPercentageGradingSettings,
)
from .assignment_points_grading_settings import AssignmentPointsGradingSettings
from .assignment_submission_mode import AssignmentSubmissionMode
from .cg_ignore_version import CGIgnoreVersion
from .group_set import GroupSet
from .submission_validator_input_data import SubmissionValidatorInputData
from .webhook_configuration_disabled_as_json import (
    WebhookConfigurationDisabledAsJSON,
)
from .webhook_configuration_enabled_as_json import (
    WebhookConfigurationEnabledAsJSON,
)


@dataclass
class ExtendedAssignment(Assignment):
    """The full version of an assignment."""

    #: The cginore.
    cgignore: t.Optional[t.Union[SubmissionValidatorInputData, str]]
    #: The version of the cignore file.
    cgignore_version: t.Optional[CGIgnoreVersion]
    #: Should we send login links to all users before the `available_at` time.
    send_login_links: bool
    #: The fixed value for the maximum that can be achieved in a rubric. This
    #: can be higher and lower than the actual max. Will be `None` if unset.
    fixed_max_rubric_points: t.Optional[float]
    #: The maximum grade you can get for this assignment. This is based around
    #: the idea that a 10 is a 'perfect' score. So if this value is 12 a user
    #: can score 2 additional bonus points. If this value is `None` it is unset
    #: and regarded as a 10.
    max_grade: float
    #: Settings that influence how the grade for a submission can be
    #: determined. TODO: Should we also move `max_grade` and/or
    #: `fixed_max_rubric_points` to the grading object?
    grading: t.Union[
        AssignmentPointsGradingSettings, AssignmentPercentageGradingSettings
    ]
    #: The group set of this assignment. This is `None` if this assignment is
    #: not a group assignment.
    group_set: t.Optional[GroupSet]
    #: The id of the AutoTest configuration connected to this assignment. This
    #: will always be given if there is a configuration connected to this
    #: assignment, even if you do not have permission to see the configuration
    #: itself.
    auto_test_id: t.Optional[int]
    #: Can you upload files to this assignment.
    files_upload_enabled: bool
    #: Settings for the git connection to this assignment.
    webhook_configuration: t.Union[
        WebhookConfigurationEnabledAsJSON, WebhookConfigurationDisabledAsJSON
    ]
    #: Can you use the editor for this assignment.
    editor_upload_enabled: bool
    #: The maximum amount of submission a student may create, inclusive. The
    #: value `null` indicates that there is no limit.
    max_submissions: t.Optional[int]
    #: The time period in which a person can submit at most
    #: `amount_in_cool_off_period` amount.
    cool_off_period: datetime.timedelta
    #: The maximum amount of time a user can submit within
    #: `amount_in_cool_off_period`. This value is always greater than or equal
    #: to 0, if this value is 0 a user can submit an unlimited amount of time.
    amount_in_cool_off_period: int
    #: The moment reminder emails will be sent. This will be `None` if you
    #: don't have the permission to see this or if it is unset.
    reminder_time: t.Optional[datetime.datetime]
    #: The LMS providing this LTI assignment.
    lms_name: t.Optional[str]
    #: The peer feedback settings for this assignment. If `null` this
    #: assignment is not a peer feedback assignment.
    peer_feedback_settings: t.Optional[AssignmentPeerFeedbackSettings]
    #: The kind of reminder that will be sent. If you don't have the permission
    #: to see this it will always be `null`. If this is not set it will also be
    #: `null`.
    done_type: t.Optional[str]
    #: The email where the done email will be sent to. This will be `null` if
    #: you do not have permission to see this information.
    done_email: t.Optional[str]
    #: The assignment id of the assignment that determines the grader division
    #: of this assignment. This will be `null` if you do not have permissions
    #: to see this information, or if no such parent is set.
    division_parent_id: t.Optional[int]
    #: The anonymization algorithm used for this assignment.
    anonymized_grading: t.Optional[AssignmentAnonymizationAlgo]
    #: Optionally a glob for a file that should be loaded first in the file
    #: viewer. There is no guarantee that any file actually matches this glob.
    file_to_load_first: t.Optional[str]
    #: Which submission mode is set for the assignment.
    submission_mode: AssignmentSubmissionMode

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: Assignment.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "cgignore",
                    rqa.Nullable(
                        parsers.make_union(
                            parsers.ParserFor.make(
                                SubmissionValidatorInputData
                            ),
                            rqa.SimpleValue.str,
                        )
                    ),
                    doc="The cginore.",
                ),
                rqa.RequiredArgument(
                    "cgignore_version",
                    rqa.Nullable(rqa.EnumValue(CGIgnoreVersion)),
                    doc="The version of the cignore file.",
                ),
                rqa.RequiredArgument(
                    "send_login_links",
                    rqa.SimpleValue.bool,
                    doc="Should we send login links to all users before the `available_at` time.",
                ),
                rqa.RequiredArgument(
                    "fixed_max_rubric_points",
                    rqa.Nullable(rqa.SimpleValue.float),
                    doc="The fixed value for the maximum that can be achieved in a rubric. This can be higher and lower than the actual max. Will be `None` if unset.",
                ),
                rqa.RequiredArgument(
                    "max_grade",
                    rqa.SimpleValue.float,
                    doc="The maximum grade you can get for this assignment. This is based around the idea that a 10 is a 'perfect' score. So if this value is 12 a user can score 2 additional bonus points. If this value is `None` it is unset and regarded as a 10.",
                ),
                rqa.RequiredArgument(
                    "grading",
                    parsers.make_union(
                        parsers.ParserFor.make(
                            AssignmentPointsGradingSettings
                        ),
                        parsers.ParserFor.make(
                            AssignmentPercentageGradingSettings
                        ),
                    ),
                    doc="Settings that influence how the grade for a submission can be determined. TODO: Should we also move `max_grade` and/or `fixed_max_rubric_points` to the grading object?",
                ),
                rqa.RequiredArgument(
                    "group_set",
                    rqa.Nullable(parsers.ParserFor.make(GroupSet)),
                    doc="The group set of this assignment. This is `None` if this assignment is not a group assignment.",
                ),
                rqa.RequiredArgument(
                    "auto_test_id",
                    rqa.Nullable(rqa.SimpleValue.int),
                    doc="The id of the AutoTest configuration connected to this assignment. This will always be given if there is a configuration connected to this assignment, even if you do not have permission to see the configuration itself.",
                ),
                rqa.RequiredArgument(
                    "files_upload_enabled",
                    rqa.SimpleValue.bool,
                    doc="Can you upload files to this assignment.",
                ),
                rqa.RequiredArgument(
                    "webhook_configuration",
                    parsers.make_union(
                        parsers.ParserFor.make(
                            WebhookConfigurationEnabledAsJSON
                        ),
                        parsers.ParserFor.make(
                            WebhookConfigurationDisabledAsJSON
                        ),
                    ),
                    doc="Settings for the git connection to this assignment.",
                ),
                rqa.RequiredArgument(
                    "editor_upload_enabled",
                    rqa.SimpleValue.bool,
                    doc="Can you use the editor for this assignment.",
                ),
                rqa.RequiredArgument(
                    "max_submissions",
                    rqa.Nullable(rqa.SimpleValue.int),
                    doc="The maximum amount of submission a student may create, inclusive. The value `null` indicates that there is no limit.",
                ),
                rqa.RequiredArgument(
                    "cool_off_period",
                    rqa.RichValue.TimeDelta,
                    doc="The time period in which a person can submit at most `amount_in_cool_off_period` amount.",
                ),
                rqa.RequiredArgument(
                    "amount_in_cool_off_period",
                    rqa.SimpleValue.int,
                    doc="The maximum amount of time a user can submit within `amount_in_cool_off_period`. This value is always greater than or equal to 0, if this value is 0 a user can submit an unlimited amount of time.",
                ),
                rqa.RequiredArgument(
                    "reminder_time",
                    rqa.Nullable(rqa.RichValue.DateTime),
                    doc="The moment reminder emails will be sent. This will be `None` if you don't have the permission to see this or if it is unset.",
                ),
                rqa.RequiredArgument(
                    "lms_name",
                    rqa.Nullable(rqa.SimpleValue.str),
                    doc="The LMS providing this LTI assignment.",
                ),
                rqa.RequiredArgument(
                    "peer_feedback_settings",
                    rqa.Nullable(
                        parsers.ParserFor.make(AssignmentPeerFeedbackSettings)
                    ),
                    doc="The peer feedback settings for this assignment. If `null` this assignment is not a peer feedback assignment.",
                ),
                rqa.RequiredArgument(
                    "done_type",
                    rqa.Nullable(rqa.SimpleValue.str),
                    doc="The kind of reminder that will be sent. If you don't have the permission to see this it will always be `null`. If this is not set it will also be `null`.",
                ),
                rqa.RequiredArgument(
                    "done_email",
                    rqa.Nullable(rqa.SimpleValue.str),
                    doc="The email where the done email will be sent to. This will be `null` if you do not have permission to see this information.",
                ),
                rqa.RequiredArgument(
                    "division_parent_id",
                    rqa.Nullable(rqa.SimpleValue.int),
                    doc="The assignment id of the assignment that determines the grader division of this assignment. This will be `null` if you do not have permissions to see this information, or if no such parent is set.",
                ),
                rqa.RequiredArgument(
                    "anonymized_grading",
                    rqa.Nullable(rqa.EnumValue(AssignmentAnonymizationAlgo)),
                    doc="The anonymization algorithm used for this assignment.",
                ),
                rqa.RequiredArgument(
                    "file_to_load_first",
                    rqa.Nullable(rqa.SimpleValue.str),
                    doc="Optionally a glob for a file that should be loaded first in the file viewer. There is no guarantee that any file actually matches this glob.",
                ),
                rqa.RequiredArgument(
                    "submission_mode",
                    rqa.EnumValue(AssignmentSubmissionMode),
                    doc="Which submission mode is set for the assignment.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "cgignore": to_dict(self.cgignore),
            "cgignore_version": to_dict(self.cgignore_version),
            "send_login_links": to_dict(self.send_login_links),
            "fixed_max_rubric_points": to_dict(self.fixed_max_rubric_points),
            "max_grade": to_dict(self.max_grade),
            "grading": to_dict(self.grading),
            "group_set": to_dict(self.group_set),
            "auto_test_id": to_dict(self.auto_test_id),
            "files_upload_enabled": to_dict(self.files_upload_enabled),
            "webhook_configuration": to_dict(self.webhook_configuration),
            "editor_upload_enabled": to_dict(self.editor_upload_enabled),
            "max_submissions": to_dict(self.max_submissions),
            "cool_off_period": to_dict(self.cool_off_period),
            "amount_in_cool_off_period": to_dict(
                self.amount_in_cool_off_period
            ),
            "reminder_time": to_dict(self.reminder_time),
            "lms_name": to_dict(self.lms_name),
            "peer_feedback_settings": to_dict(self.peer_feedback_settings),
            "done_type": to_dict(self.done_type),
            "done_email": to_dict(self.done_email),
            "division_parent_id": to_dict(self.division_parent_id),
            "anonymized_grading": to_dict(self.anonymized_grading),
            "file_to_load_first": to_dict(self.file_to_load_first),
            "submission_mode": to_dict(self.submission_mode),
            "id": to_dict(self.id),
            "name": to_dict(self.name),
            "created_at": to_dict(self.created_at),
            "course_id": to_dict(self.course_id),
            "has_multiple_timeframes": to_dict(self.has_multiple_timeframes),
            "is_lti": to_dict(self.is_lti),
            "has_description": to_dict(self.has_description),
            "restrictions": to_dict(self.restrictions),
            "timeframe": to_dict(self.timeframe),
            "grade_availability": to_dict(self.grade_availability),
            "kind": to_dict(self.kind),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[ExtendedAssignment], d: t.Dict[str, t.Any]
    ) -> ExtendedAssignment:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            cgignore=parsed.cgignore,
            cgignore_version=parsed.cgignore_version,
            send_login_links=parsed.send_login_links,
            fixed_max_rubric_points=parsed.fixed_max_rubric_points,
            max_grade=parsed.max_grade,
            grading=parsed.grading,
            group_set=parsed.group_set,
            auto_test_id=parsed.auto_test_id,
            files_upload_enabled=parsed.files_upload_enabled,
            webhook_configuration=parsed.webhook_configuration,
            editor_upload_enabled=parsed.editor_upload_enabled,
            max_submissions=parsed.max_submissions,
            cool_off_period=parsed.cool_off_period,
            amount_in_cool_off_period=parsed.amount_in_cool_off_period,
            reminder_time=parsed.reminder_time,
            lms_name=parsed.lms_name,
            peer_feedback_settings=parsed.peer_feedback_settings,
            done_type=parsed.done_type,
            done_email=parsed.done_email,
            division_parent_id=parsed.division_parent_id,
            anonymized_grading=parsed.anonymized_grading,
            file_to_load_first=parsed.file_to_load_first,
            submission_mode=parsed.submission_mode,
            id=parsed.id,
            name=parsed.name,
            created_at=parsed.created_at,
            course_id=parsed.course_id,
            has_multiple_timeframes=parsed.has_multiple_timeframes,
            is_lti=parsed.is_lti,
            has_description=parsed.has_description,
            restrictions=parsed.restrictions,
            timeframe=parsed.timeframe,
            grade_availability=parsed.grade_availability,
            kind=parsed.kind,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    from .assignment_kind import AssignmentKind
    from .assignment_restriction import AssignmentRestriction
    from .fixed_grade_availability import FixedGradeAvailability
    from .timeframe_like import TimeframeLike
