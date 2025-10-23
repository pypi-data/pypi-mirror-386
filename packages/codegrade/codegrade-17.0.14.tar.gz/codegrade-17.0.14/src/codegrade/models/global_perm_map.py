"""The module that defines the ``GlobalPermMap`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class GlobalPermMap:
    """The mapping between global permission and value for a user."""

    #: Users with this permission can add other users to the website.
    can_add_users: bool
    #: Users with this permission can create new courses.
    can_create_courses: bool
    #: Users with this permission can change the global permissions for other
    #: users on the site.
    can_manage_site_users: bool
    #: Users with this permission can search for users on the site, this means
    #: they can see all other users on the site.
    can_search_users: bool
    #: Users with this permission can impersonate users, i.e. they can login as
    #: other users.
    can_impersonate_users: bool
    #: Users with this permission can edit and list existing, and create new
    #: LTI providers.
    can_manage_lti_providers: bool
    #: Users that have this permission globally can delete any community
    #: library item. Users that have this permission only in their tenant can
    #: delete any community library item within their tenant. Users without
    #: this permission can still delete community library items they created
    #: themselves. You will always need permission to view an item to be able
    #: to delete it.
    can_delete_community_library_items: bool
    #: Users with this global permission can list hidden tenants. All users can
    #: still retrieve hidden tenants if they know the id. This permission only
    #: has effect on the global level, not tenant level.
    can_list_hidden_tenants: bool
    #: Users with this permission can create, edit, and delete Pearson
    #: templates, questions, and books.
    can_manage_pearson_templates: bool
    #: Users with this permission can see the items in the community library.
    can_view_community_library_items: bool
    #: Users with this permission can see all the items in the community
    #: library, even those not published to their tenant.
    can_view_all_community_library_items: bool
    #: Users with this permission can create new community library items.
    can_create_community_library_items: bool
    #: Users with this permission have all other permissions in all tenants and
    #: courses, even when they do not have a role within the tenant or course
    is_admin: bool
    #: Determines whether the user will see announcement reserved for non
    #: student users in the announcement center within the sidebar
    can_see_teacher_announcements: bool
    #: Users with this permission can connect new SSO Identity Providers.
    can_manage_sso_providers: bool
    #: Users with this permission can manage the settings of this CodeGrade
    #: instance
    can_manage_site_settings: bool
    #: Users with this permission can view, stop, and restart background jobs.
    can_manage_background_jobs: bool
    #: Users with this permission can create new tenants on the system.
    can_create_tenant: bool
    #: Users with this permission can create courses for other tenants than
    #: their own.
    can_create_courses_for_other_tenants: bool
    #: Users with this permission can see the statistics of their own and other
    #: tenants.
    can_see_other_tenant_statistics: bool
    #: Users with this permission can search users of other tenants.
    can_search_users_other_tenant: bool
    #: Users with this permission do not have to pay for paid courses.
    can_skip_payment: bool
    #: Users with this permission can change the pricing for courses and
    #: tenants.
    can_edit_pricing: bool
    #: Users with this permission are allowed to view all transactions from all
    #: users.
    can_see_all_transactions: bool
    #: Users with this permission can create, edit and delete pricing coupons
    #: for courses.
    can_edit_coupons: bool
    #: Users with this permission can see the pricing coupons generated for the
    #: courses they are part of.
    can_see_coupons: bool
    #: Users with this permission can use the snippets feature on the website.
    can_use_snippets: bool
    #: Users with this permission can edit their own personal information.
    can_edit_own_info: bool
    #: Users with this permission can edit their own password.
    can_edit_own_password: bool
    #: Users with this permission can get a list of all AutoTest results that
    #: have not yet started running.
    can_view_not_started_autotest_results: bool
    #: Users with this permission can see OAuth providers from tenants other
    #: than their own.
    can_see_other_tenant_oauth_providers: bool

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "can_add_users",
                rqa.SimpleValue.bool,
                doc="Users with this permission can add other users to the website.",
            ),
            rqa.RequiredArgument(
                "can_create_courses",
                rqa.SimpleValue.bool,
                doc="Users with this permission can create new courses.",
            ),
            rqa.RequiredArgument(
                "can_manage_site_users",
                rqa.SimpleValue.bool,
                doc="Users with this permission can change the global permissions for other users on the site.",
            ),
            rqa.RequiredArgument(
                "can_search_users",
                rqa.SimpleValue.bool,
                doc="Users with this permission can search for users on the site, this means they can see all other users on the site.",
            ),
            rqa.RequiredArgument(
                "can_impersonate_users",
                rqa.SimpleValue.bool,
                doc="Users with this permission can impersonate users, i.e. they can login as other users.",
            ),
            rqa.RequiredArgument(
                "can_manage_lti_providers",
                rqa.SimpleValue.bool,
                doc="Users with this permission can edit and list existing, and create new LTI providers.",
            ),
            rqa.RequiredArgument(
                "can_delete_community_library_items",
                rqa.SimpleValue.bool,
                doc="Users that have this permission globally can delete any community library item. Users that have this permission only in their tenant can delete any community library item within their tenant. Users without this permission can still delete community library items they created themselves. You will always need permission to view an item to be able to delete it.",
            ),
            rqa.RequiredArgument(
                "can_list_hidden_tenants",
                rqa.SimpleValue.bool,
                doc="Users with this global permission can list hidden tenants. All users can still retrieve hidden tenants if they know the id. This permission only has effect on the global level, not tenant level.",
            ),
            rqa.RequiredArgument(
                "can_manage_pearson_templates",
                rqa.SimpleValue.bool,
                doc="Users with this permission can create, edit, and delete Pearson templates, questions, and books.",
            ),
            rqa.RequiredArgument(
                "can_view_community_library_items",
                rqa.SimpleValue.bool,
                doc="Users with this permission can see the items in the community library.",
            ),
            rqa.RequiredArgument(
                "can_view_all_community_library_items",
                rqa.SimpleValue.bool,
                doc="Users with this permission can see all the items in the community library, even those not published to their tenant.",
            ),
            rqa.RequiredArgument(
                "can_create_community_library_items",
                rqa.SimpleValue.bool,
                doc="Users with this permission can create new community library items.",
            ),
            rqa.RequiredArgument(
                "is_admin",
                rqa.SimpleValue.bool,
                doc="Users with this permission have all other permissions in all tenants and courses, even when they do not have a role within the tenant or course",
            ),
            rqa.RequiredArgument(
                "can_see_teacher_announcements",
                rqa.SimpleValue.bool,
                doc="Determines whether the user will see announcement reserved for non student users in the announcement center within the sidebar",
            ),
            rqa.RequiredArgument(
                "can_manage_sso_providers",
                rqa.SimpleValue.bool,
                doc="Users with this permission can connect new SSO Identity Providers.",
            ),
            rqa.RequiredArgument(
                "can_manage_site_settings",
                rqa.SimpleValue.bool,
                doc="Users with this permission can manage the settings of this CodeGrade instance",
            ),
            rqa.RequiredArgument(
                "can_manage_background_jobs",
                rqa.SimpleValue.bool,
                doc="Users with this permission can view, stop, and restart background jobs.",
            ),
            rqa.RequiredArgument(
                "can_create_tenant",
                rqa.SimpleValue.bool,
                doc="Users with this permission can create new tenants on the system.",
            ),
            rqa.RequiredArgument(
                "can_create_courses_for_other_tenants",
                rqa.SimpleValue.bool,
                doc="Users with this permission can create courses for other tenants than their own.",
            ),
            rqa.RequiredArgument(
                "can_see_other_tenant_statistics",
                rqa.SimpleValue.bool,
                doc="Users with this permission can see the statistics of their own and other tenants.",
            ),
            rqa.RequiredArgument(
                "can_search_users_other_tenant",
                rqa.SimpleValue.bool,
                doc="Users with this permission can search users of other tenants.",
            ),
            rqa.RequiredArgument(
                "can_skip_payment",
                rqa.SimpleValue.bool,
                doc="Users with this permission do not have to pay for paid courses.",
            ),
            rqa.RequiredArgument(
                "can_edit_pricing",
                rqa.SimpleValue.bool,
                doc="Users with this permission can change the pricing for courses and tenants.",
            ),
            rqa.RequiredArgument(
                "can_see_all_transactions",
                rqa.SimpleValue.bool,
                doc="Users with this permission are allowed to view all transactions from all users.",
            ),
            rqa.RequiredArgument(
                "can_edit_coupons",
                rqa.SimpleValue.bool,
                doc="Users with this permission can create, edit and delete pricing coupons for courses.",
            ),
            rqa.RequiredArgument(
                "can_see_coupons",
                rqa.SimpleValue.bool,
                doc="Users with this permission can see the pricing coupons generated for the courses they are part of.",
            ),
            rqa.RequiredArgument(
                "can_use_snippets",
                rqa.SimpleValue.bool,
                doc="Users with this permission can use the snippets feature on the website.",
            ),
            rqa.RequiredArgument(
                "can_edit_own_info",
                rqa.SimpleValue.bool,
                doc="Users with this permission can edit their own personal information.",
            ),
            rqa.RequiredArgument(
                "can_edit_own_password",
                rqa.SimpleValue.bool,
                doc="Users with this permission can edit their own password.",
            ),
            rqa.RequiredArgument(
                "can_view_not_started_autotest_results",
                rqa.SimpleValue.bool,
                doc="Users with this permission can get a list of all AutoTest results that have not yet started running.",
            ),
            rqa.RequiredArgument(
                "can_see_other_tenant_oauth_providers",
                rqa.SimpleValue.bool,
                doc="Users with this permission can see OAuth providers from tenants other than their own.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "can_add_users": to_dict(self.can_add_users),
            "can_create_courses": to_dict(self.can_create_courses),
            "can_manage_site_users": to_dict(self.can_manage_site_users),
            "can_search_users": to_dict(self.can_search_users),
            "can_impersonate_users": to_dict(self.can_impersonate_users),
            "can_manage_lti_providers": to_dict(self.can_manage_lti_providers),
            "can_delete_community_library_items": to_dict(
                self.can_delete_community_library_items
            ),
            "can_list_hidden_tenants": to_dict(self.can_list_hidden_tenants),
            "can_manage_pearson_templates": to_dict(
                self.can_manage_pearson_templates
            ),
            "can_view_community_library_items": to_dict(
                self.can_view_community_library_items
            ),
            "can_view_all_community_library_items": to_dict(
                self.can_view_all_community_library_items
            ),
            "can_create_community_library_items": to_dict(
                self.can_create_community_library_items
            ),
            "is_admin": to_dict(self.is_admin),
            "can_see_teacher_announcements": to_dict(
                self.can_see_teacher_announcements
            ),
            "can_manage_sso_providers": to_dict(self.can_manage_sso_providers),
            "can_manage_site_settings": to_dict(self.can_manage_site_settings),
            "can_manage_background_jobs": to_dict(
                self.can_manage_background_jobs
            ),
            "can_create_tenant": to_dict(self.can_create_tenant),
            "can_create_courses_for_other_tenants": to_dict(
                self.can_create_courses_for_other_tenants
            ),
            "can_see_other_tenant_statistics": to_dict(
                self.can_see_other_tenant_statistics
            ),
            "can_search_users_other_tenant": to_dict(
                self.can_search_users_other_tenant
            ),
            "can_skip_payment": to_dict(self.can_skip_payment),
            "can_edit_pricing": to_dict(self.can_edit_pricing),
            "can_see_all_transactions": to_dict(self.can_see_all_transactions),
            "can_edit_coupons": to_dict(self.can_edit_coupons),
            "can_see_coupons": to_dict(self.can_see_coupons),
            "can_use_snippets": to_dict(self.can_use_snippets),
            "can_edit_own_info": to_dict(self.can_edit_own_info),
            "can_edit_own_password": to_dict(self.can_edit_own_password),
            "can_view_not_started_autotest_results": to_dict(
                self.can_view_not_started_autotest_results
            ),
            "can_see_other_tenant_oauth_providers": to_dict(
                self.can_see_other_tenant_oauth_providers
            ),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[GlobalPermMap], d: t.Dict[str, t.Any]
    ) -> GlobalPermMap:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            can_add_users=parsed.can_add_users,
            can_create_courses=parsed.can_create_courses,
            can_manage_site_users=parsed.can_manage_site_users,
            can_search_users=parsed.can_search_users,
            can_impersonate_users=parsed.can_impersonate_users,
            can_manage_lti_providers=parsed.can_manage_lti_providers,
            can_delete_community_library_items=parsed.can_delete_community_library_items,
            can_list_hidden_tenants=parsed.can_list_hidden_tenants,
            can_manage_pearson_templates=parsed.can_manage_pearson_templates,
            can_view_community_library_items=parsed.can_view_community_library_items,
            can_view_all_community_library_items=parsed.can_view_all_community_library_items,
            can_create_community_library_items=parsed.can_create_community_library_items,
            is_admin=parsed.is_admin,
            can_see_teacher_announcements=parsed.can_see_teacher_announcements,
            can_manage_sso_providers=parsed.can_manage_sso_providers,
            can_manage_site_settings=parsed.can_manage_site_settings,
            can_manage_background_jobs=parsed.can_manage_background_jobs,
            can_create_tenant=parsed.can_create_tenant,
            can_create_courses_for_other_tenants=parsed.can_create_courses_for_other_tenants,
            can_see_other_tenant_statistics=parsed.can_see_other_tenant_statistics,
            can_search_users_other_tenant=parsed.can_search_users_other_tenant,
            can_skip_payment=parsed.can_skip_payment,
            can_edit_pricing=parsed.can_edit_pricing,
            can_see_all_transactions=parsed.can_see_all_transactions,
            can_edit_coupons=parsed.can_edit_coupons,
            can_see_coupons=parsed.can_see_coupons,
            can_use_snippets=parsed.can_use_snippets,
            can_edit_own_info=parsed.can_edit_own_info,
            can_edit_own_password=parsed.can_edit_own_password,
            can_view_not_started_autotest_results=parsed.can_view_not_started_autotest_results,
            can_see_other_tenant_oauth_providers=parsed.can_see_other_tenant_oauth_providers,
        )
        res.raw_data = d
        return res
