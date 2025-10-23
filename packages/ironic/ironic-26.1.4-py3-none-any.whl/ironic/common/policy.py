# Copyright (c) 2011 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Policy Engine For Ironic."""

import itertools
import sys

from oslo_concurrency import lockutils
from oslo_config import cfg
from oslo_log import log
from oslo_log import versionutils
from oslo_policy import opts
from oslo_policy import policy

from ironic.common import exception

_ENFORCER = None
CONF = cfg.CONF
LOG = log.getLogger(__name__)


# TODO(gmann): Remove overriding the default value of config options
# 'policy_file' once oslo_policy change its default value to what
# is overridden here.
DEFAULT_POLICY_FILE = 'policy.yaml'
opts.set_defaults(
    cfg.CONF,
    DEFAULT_POLICY_FILE)

# Generic policy check string for system administrators. These are the people
# who need the highest level of authorization to operate the deployment.
# They're allowed to create, read, update, or delete any system-specific
# resource. They can also operate on project-specific resources where
# applicable (e.g., cleaning up baremetal hosts)
SYSTEM_ADMIN = 'role:admin and system_scope:all'

# Generic policy check string for system users who don't require all the
# authorization that system administrators typically have. This persona, or
# check string, typically isn't used by default, but it's existence is useful
# in the event a deployment wants to offload some administrative action from
# system administrator to system members.
# The rule:service_role match here is to enable an elevated level of API
# access for a specialized service role and users with appropriate
# service role access.
SYSTEM_MEMBER = '(role:member and system_scope:all) or rule:service_role'  # noqa

# Generic policy check string for read-only access to system-level
# resources. This persona is useful for someone who needs access
# for auditing or even support. These users are also able to view
# project-specific resources where applicable (e.g., listing all
# volumes in the deployment, regardless of the project they belong to).
# The rule:service_role match here is to enable an elevated level of API
# access for a specialized service role and users with appropriate
# role access, specifically because 'service" role is outside of the RBAC
# model defaults and does not imply reader access.
SYSTEM_READER = '(role:reader and system_scope:all) or (role:service and system_scope:all) or rule:service_role'  # noqa

# This check string is reserved for actions that require the highest level of
# authorization on a project or resources within the project (e.g., setting the
# default volume type for a project)
PROJECT_ADMIN = ('role:admin and '
                 'project_id:%(node.owner)s')
# This check string is reserved for an intermediate point between
# a Project Admin and a Project Member. This is an outcome of the
# revised Yoga Secure RBAC community goal.
# The advantage here may be that this rule *does* match against node owners
# and lessees.
PROJECT_MANAGER = ('role:manager and '
                   '(project_id:%(node.owner)s or project_id:%(node.lessee)s)')
# This check string is the primary use case for typical end-users, who are
# working with resources that belong to a project (e.g., creating volumes and
# backups).
PROJECT_MEMBER = ('role:member and '
                  '(project_id:%(node.owner)s or project_id:%(node.lessee)s)')

# This check string should only be used to protect read-only project-specific
# resources. It should not be used to protect APIs that make writable changes
# (e.g., updating a volume or deleting a backup).
PROJECT_READER = ('role:reader and '
                  '(project_id:%(node.owner)s or project_id:%(node.lessee)s)')

# This check string is used for granting access to other services which need
# to communicate with Ironic, for example, Nova-Compute to provision nodes,
# or Ironic-Inspector to create nodes. The idea behind a service role is
# one which has restricted access to perform operations, that are limited
# to remote automated and inter-operation processes.
SYSTEM_SERVICE = ('role:service and system_scope:all')
PROJECT_SERVICE = ('role:service and project_id:%(node.owner)s')

# The following are common composite check strings that are useful for
# protecting APIs designed to operate with multiple scopes (e.g., a system
# administrator should be able to delete any baremetal host in the deployment,
# a project member should only be able to delete hosts in their project).
SYSTEM_OR_PROJECT_MEMBER = (
    '(' + SYSTEM_MEMBER + ') or (' + PROJECT_MEMBER + ') or (' + SYSTEM_SERVICE + ')'  # noqa
)
SYSTEM_OR_PROJECT_READER = (
    '(' + SYSTEM_READER + ') or (' + PROJECT_READER + ') or (' + PROJECT_SERVICE + ')'  # noqa
)

PROJECT_OWNER_ADMIN = ('role:admin and project_id:%(node.owner)s')
PROJECT_OWNER_MANAGER = ('role:manager and project_id:%(node.owner)s')
PROJECT_OWNER_MEMBER = ('role:member and project_id:%(node.owner)s')
PROJECT_OWNER_READER = ('role:reader and project_id:%(node.owner)s')
PROJECT_LESSEE_ADMIN = ('role:admin and project_id:%(node.lessee)s')
PROJECT_LESSEE_MANAGER = ('role:manager and project_id:%(node.lessee)s')

# Not used - Members can create/destroy their allocations.
ALLOCATION_OWNER_ADMIN = ('role:admin and project_id:%(allocation.owner)s')
# Not used - Members can create/destroy their allocations.
ALLOCATION_OWNER_MANAGER = ('role:manager and project_id:%(allocation.owner)s')

ALLOCATION_OWNER_MEMBER = ('role:member and project_id:%(allocation.owner)s')
ALLOCATION_OWNER_READER = ('role:reader and project_id:%(allocation.owner)s')

# Members can create/destroy their runbooks.
RUNBOOK_OWNER_ADMIN = ('role:admin and project_id:%(runbook.owner)s')
RUNBOOK_OWNER_MANAGER = ('role:manager and project_id:%(runbook.owner)s')
RUNBOOK_OWNER_MEMBER = ('role:member and project_id:%(runbook.owner)s')
RUNBOOK_OWNER_READER = ('role:reader and project_id:%(runbook.owner)s')

RUNBOOK_ADMIN = (
    '(' + SYSTEM_MEMBER + ') or (' + RUNBOOK_OWNER_MANAGER + ') or role:service' # noqa
)

RUNBOOK_READER = (
    '(' + SYSTEM_READER + ') or (' + RUNBOOK_OWNER_READER + ') or role:service' # noqa
)

RUNBOOK_CREATOR = (
    '(' + SYSTEM_MEMBER + ') or role:manager or role:service' # noqa
)

# Used for general operations like changing provision state.
SYSTEM_OR_OWNER_MEMBER_AND_LESSEE_ADMIN = (
    '(' + SYSTEM_MEMBER + ') or (' + SYSTEM_SERVICE + ') or (' + PROJECT_OWNER_MEMBER + ') or (' + PROJECT_LESSEE_ADMIN + ') or (' + PROJECT_LESSEE_MANAGER + ') or (' + PROJECT_SERVICE + ')'  # noqa
)

# Used for creation and deletion of network ports.
SYSTEM_ADMIN_OR_OWNER_ADMIN = (
    '(' + SYSTEM_ADMIN + ') or (' + SYSTEM_SERVICE + ') or (' + PROJECT_OWNER_ADMIN + ') or (' + PROJECT_OWNER_MANAGER + ') or (' + PROJECT_SERVICE + ')'  # noqa
)

# Used to map system members, and owner admins to the same access rights.
# This is actions such as update driver interfaces, delete ports.
SYSTEM_MEMBER_OR_OWNER_ADMIN = (
    '(' + SYSTEM_MEMBER + ') or (' + SYSTEM_SERVICE + ') or (' + PROJECT_OWNER_ADMIN + ') or (' + PROJECT_OWNER_MANAGER + ') or (' + PROJECT_SERVICE + ')'  # noqa
)

# Used to map "member" only rights, i.e. those of "users using a deployment"
SYSTEM_MEMBER_OR_OWNER_MEMBER = (
    '(' + SYSTEM_MEMBER + ') or (' + SYSTEM_SERVICE + ') or (' + PROJECT_OWNER_MEMBER + ') or (' + PROJECT_SERVICE + ')'  # noqa
)

# Used throughout to map where authenticated readers
# should be able to read API objects.
SYSTEM_OR_OWNER_READER = (
    '(' + SYSTEM_READER + ') or (' + SYSTEM_SERVICE + ') or (' + PROJECT_OWNER_READER + ') or (' + PROJECT_SERVICE + ')'  # noqa
)

# Mainly used for targets/connectors
SYSTEM_MEMBER_OR_OWNER_LESSEE_ADMIN = (
    '(' + SYSTEM_MEMBER + ') or (' + SYSTEM_SERVICE + ') or (' + PROJECT_OWNER_ADMIN + ') or (' + PROJECT_OWNER_MANAGER + ') or (' + PROJECT_LESSEE_ADMIN + ') or (' + PROJECT_LESSEE_MANAGER + ') or (' + PROJECT_SERVICE + ')'  # noqa
)


# The system has rights to manage the allocations for users, in a sense
# a delegated management since they are not creating a real object or asset,
# but allocations of assets.
ALLOCATION_MEMBER = (
    '(' + SYSTEM_MEMBER + ') or (' + ALLOCATION_OWNER_MEMBER + ')'
)

ALLOCATION_READER = (
    '(' + SYSTEM_READER + ') or (' + ALLOCATION_OWNER_READER + ')'
)

ALLOCATION_CREATOR = (
    '(' + SYSTEM_MEMBER + ') or (role:member)'
)

# Special purpose aliases for things like "ability to access the API
# as a reader, or permission checking that does not require node
# owner relationship checking
API_READER = ('(role:reader) or (role:service)')

# Used for ability to view target properties of a volume, which is
# considered highly restricted.
TARGET_PROPERTIES_READER = (
    '(' + SYSTEM_READER + ') or (role:admin)'
)

pre_rbac_deprecated_reason = 'Pre-RBAC default rule. This rule does not support scoping system scoping and as such is deprecated.' # noqa

default_policies = [
    # Legacy setting, don't remove. Likely to be overridden by operators who
    # forget to update their policy.json configuration file.
    # This gets rolled into the new "is_admin" rule below.
    policy.RuleDefault('admin_api',
                       'role:admin or role:administrator',
                       description='Legacy rule for cloud admin access',
                       deprecated_for_removal=True,
                       deprecated_since=versionutils.deprecated.WALLABY,
                       deprecated_reason=pre_rbac_deprecated_reason
                       ),
    # is_public_api is set in the environment from AuthPublicRoutes
    # TODO(TheJulia): Once legacy policy rules are removed, is_public_api
    # can be removed from the code base.
    policy.RuleDefault('public_api',
                       'is_public_api:True',
                       description='Internal flag for public API routes'),
    # Generic default to hide passwords in node driver_info
    # NOTE(tenbrae): the 'show_password' policy setting hides secrets in
    #             driver_info. However, the name exists for legacy
    #             purposes and can not be changed. Changing it will cause
    #             upgrade problems for any operators who have customized
    #             the value of this field
    policy.RuleDefault('show_password',
                       '!',
                       description='Show or mask secrets within node driver information in API responses. This setting should be used with the utmost care as its use can present a security risk.'),  # noqa
    # Generic default to hide instance secrets
    policy.RuleDefault('show_instance_secrets',
                       '!',
                       description='Show or mask secrets within instance information in API responses. This setting should be used with the utmost care as its use can present a security risk.'),  # noqa
    # NOTE(TheJulia): This is a special rule to allow customization of the
    # service role check. The config.service_project_name is a reserved
    # target check field which is loaded from configuration to the
    # check context in ironic/common/context.py.
    policy.RuleDefault('service_role',
                       'role:service and project_name:%(config.service_project_name)s',  # noqa
                       description='Rule to match service role usage with a service project, delineated as a separate rule to enable customization.'),  # noqa
    # Roles likely to be overridden by operator
    # TODO(TheJulia): Lets nuke demo from high orbit.
    policy.RuleDefault('is_member',
                       '(project_domain_id:default or project_domain_id:None) and (project_name:demo or project_name:baremetal)',  # noqa
                       description='May be used to restrict access to specific projects',  # noqa
                       deprecated_for_removal=True,
                       deprecated_since=versionutils.deprecated.WALLABY,
                       deprecated_reason=pre_rbac_deprecated_reason),
    policy.RuleDefault('is_observer',
                       'rule:is_member and (role:observer or role:baremetal_observer)',  # noqa
                       description='Read-only API access',
                       deprecated_for_removal=True,
                       deprecated_since=versionutils.deprecated.WALLABY,
                       deprecated_reason=pre_rbac_deprecated_reason),
    policy.RuleDefault('is_admin',
                       'rule:admin_api or (rule:is_member and role:baremetal_admin)',  # noqa
                       description='Full read/write API access',
                       deprecated_for_removal=True,
                       deprecated_since=versionutils.deprecated.WALLABY,
                       deprecated_reason=pre_rbac_deprecated_reason),
    policy.RuleDefault('is_node_owner',
                       'project_id:%(node.owner)s',
                       description='Owner of node',
                       deprecated_for_removal=True,
                       deprecated_since=versionutils.deprecated.WALLABY,
                       deprecated_reason=pre_rbac_deprecated_reason),
    policy.RuleDefault('is_node_lessee',
                       'project_id:%(node.lessee)s',
                       description='Lessee of node',
                       deprecated_for_removal=True,
                       deprecated_since=versionutils.deprecated.WALLABY,
                       deprecated_reason=pre_rbac_deprecated_reason),
    policy.RuleDefault('is_allocation_owner',
                       'project_id:%(allocation.owner)s',
                       description='Owner of allocation',
                       deprecated_for_removal=True,
                       deprecated_since=versionutils.deprecated.WALLABY,
                       deprecated_reason=pre_rbac_deprecated_reason),
]

# NOTE(tenbrae): to follow policy-in-code spec, we define defaults for
#             the granular policies in code, rather than in policy.json.
#             All of these may be overridden by configuration, but we can
#             depend on their existence throughout the code.

# TODO(TheJulia): Since the OpenStack community appears to be
# coalescing around taking a very long term deprecation path,
# and is actually seeking to suppress the warnings being generated
# for the time being, I've changed the warning below to remove
# reference to the Xena cycle. This should be changed once we
# determine when the old policies will be fully removed.
deprecated_node_reason = """
The baremetal node API is now aware of system scope and default roles.
Capability to fallback to legacy admin project policy configuration
will be removed in a future release of Ironic.
"""

deprecated_node_create = policy.DeprecatedRule(
    name='baremetal:node:create',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_get = policy.DeprecatedRule(
    name='baremetal:node:get',
    check_str='rule:is_admin or rule:is_observer',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_list = policy.DeprecatedRule(
    name='baremetal:node:list',
    check_str='rule:baremetal:node:get',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_list_all = policy.DeprecatedRule(
    name='baremetal:node:list_all',
    check_str='rule:baremetal:node:get',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_update = policy.DeprecatedRule(
    name='baremetal:node:update',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_update_extra = policy.DeprecatedRule(
    name='baremetal:node:update_extra',
    check_str='rule:baremetal:node:update',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_update_instance_info = policy.DeprecatedRule(
    name='baremetal:node:update_instance_info',
    check_str='rule:baremetal:node:update',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_update_owner_provisioned = policy.DeprecatedRule(
    name='baremetal:node:update_owner_provisioned',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_delete = policy.DeprecatedRule(
    name='baremetal:node:delete',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_validate = policy.DeprecatedRule(
    name='baremetal:node:validate',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_set_maintenance = policy.DeprecatedRule(
    name='baremetal:node:set_maintenance',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_clear_maintenance = policy.DeprecatedRule(
    name='baremetal:node:clear_maintenance',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_get_boot_device = policy.DeprecatedRule(
    name='baremetal:node:get_boot_device',
    check_str='rule:is_admin or rule:is_observer',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_set_boot_device = policy.DeprecatedRule(
    name='baremetal:node:set_boot_device',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_get_indicator_state = policy.DeprecatedRule(
    name='baremetal:node:get_indicator_state',
    check_str='rule:is_admin or rule:is_observer',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_set_indicator_state = policy.DeprecatedRule(
    name='baremetal:node:set_indicator_state',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_inject_nmi = policy.DeprecatedRule(
    name='baremetal:node:inject_nmi',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_get_states = policy.DeprecatedRule(
    name='baremetal:node:get_states',
    check_str='rule:is_admin or rule:is_observer',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_set_power_state = policy.DeprecatedRule(
    name='baremetal:node:set_power_state',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_set_provision_state = policy.DeprecatedRule(
    name='baremetal:node:set_provision_state',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_set_raid_state = policy.DeprecatedRule(
    name='baremetal:node:set_raid_state',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_get_console = policy.DeprecatedRule(
    name='baremetal:node:get_console',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_set_console_state = policy.DeprecatedRule(
    name='baremetal:node:set_console_state',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_vif_list = policy.DeprecatedRule(
    name='baremetal:node:vif:list',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_vif_attach = policy.DeprecatedRule(
    name='baremetal:node:vif:attach',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_vif_detach = policy.DeprecatedRule(
    name='baremetal:node:vif:detach',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_traits_list = policy.DeprecatedRule(
    name='baremetal:node:traits:list',
    check_str='rule:is_admin or rule:is_observer',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_traits_set = policy.DeprecatedRule(
    name='baremetal:node:traits:set',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_traits_delete = policy.DeprecatedRule(
    name='baremetal:node:traits:delete',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_node_bios_get = policy.DeprecatedRule(
    name='baremetal:node:bios:get',
    check_str='rule:is_admin or rule:is_observer',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_bios_disable_cleaning = policy.DeprecatedRule(
    name='baremetal:node:disable_cleaning',
    check_str='rule:baremetal:node:update',
    deprecated_reason=deprecated_node_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)

node_policies = [
    policy.DocumentedRuleDefault(
        name='baremetal:node:create',
        check_str='(' + SYSTEM_ADMIN + ') or (' + SYSTEM_SERVICE + ')',
        scope_types=['system', 'project'],
        description='Create Node records',
        operations=[{'path': '/nodes', 'method': 'POST'}],
        deprecated_rule=deprecated_node_create
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:create:self_owned_node',
        check_str=('(role:admin) or (role:service)'),
        scope_types=['system', 'project'],
        description='Create node records which will be tracked '
                    'as owned by the associated user project.',
        operations=[{'path': '/nodes', 'method': 'POST'}],
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:list',
        check_str=API_READER,
        scope_types=['system', 'project'],
        description='Retrieve multiple Node records, filtered by '
                    'an explicit owner or the client project_id',
        operations=[{'path': '/nodes', 'method': 'GET'},
                    {'path': '/nodes/detail', 'method': 'GET'}],
        deprecated_rule=deprecated_node_list
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:list_all',
        check_str=SYSTEM_READER,
        scope_types=['system', 'project'],
        description='Retrieve multiple Node records',
        operations=[{'path': '/nodes', 'method': 'GET'},
                    {'path': '/nodes/detail', 'method': 'GET'}],
        deprecated_rule=deprecated_node_list_all
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:get',
        check_str=SYSTEM_OR_PROJECT_READER,
        scope_types=['system', 'project'],
        description='Retrieve a single Node record',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'GET'}],
        deprecated_rule=deprecated_node_get
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:get:filter_threshold',
        check_str=SYSTEM_READER,
        scope_types=['system', 'project'],
        description='Filter to allow operators to govern the threshold '
                    'where information should be filtered. Non-authorized '
                    'users will be subjected to additional API policy '
                    'checks for API content response bodies.',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'GET'}],
        # This rule fallsback to deprecated_node_get in order to provide a
        # mechanism so the additional policies only engage in an updated
        # operating context.
        deprecated_rule=deprecated_node_get
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:get:last_error',
        check_str=SYSTEM_OR_OWNER_READER,
        scope_types=['system', 'project'],
        description='Governs if the node last_error field is masked from API '
                    'clients with insufficient privileges.',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'GET'}],
        deprecated_rule=deprecated_node_get
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:get:reservation',
        check_str=SYSTEM_OR_OWNER_READER,
        scope_types=['system', 'project'],
        description='Governs if the node reservation field is masked from API '
                    'clients with insufficient privileges.',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'GET'}],
        deprecated_rule=deprecated_node_get
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:get:driver_internal_info',
        check_str=SYSTEM_OR_OWNER_READER,
        scope_types=['system', 'project'],
        description='Governs if the node driver_internal_info field is '
                    'masked from API clients with insufficient privileges.',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'GET'}],
        deprecated_rule=deprecated_node_get
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:get:driver_info',
        check_str=SYSTEM_OR_OWNER_READER,
        scope_types=['system', 'project'],
        description='Governs if the driver_info field is masked from API '
                    'clients with insufficient privileges.',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'GET'}],
        deprecated_rule=deprecated_node_get
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:update:driver_info',
        check_str=SYSTEM_MEMBER_OR_OWNER_MEMBER,
        scope_types=['system', 'project'],
        description='Governs if node driver_info field can be updated via '
                    'the API clients.',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'PATCH'}],
        deprecated_rule=deprecated_node_update
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:update:properties',
        check_str=SYSTEM_MEMBER_OR_OWNER_MEMBER,
        scope_types=['system', 'project'],
        description='Governs if node properties field can be updated via '
                    'the API clients.',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'PATCH'}],
        deprecated_rule=deprecated_node_update
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:update:chassis_uuid',
        check_str=SYSTEM_ADMIN,
        scope_types=['system', 'project'],
        description='Governs if node chassis_uuid field can be updated via '
                    'the API clients.',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'PATCH'}],
        deprecated_rule=deprecated_node_update
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:update:instance_uuid',
        check_str=SYSTEM_MEMBER_OR_OWNER_MEMBER,
        scope_types=['system', 'project'],
        description='Governs if node instance_uuid field can be updated via '
                    'the API clients.',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'PATCH'}],
        deprecated_rule=deprecated_node_update
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:update:lessee',
        check_str=SYSTEM_MEMBER_OR_OWNER_MEMBER,
        scope_types=['system', 'project'],
        description='Governs if node lessee field can be updated via '
                    'the API clients.',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'PATCH'}],
        deprecated_rule=deprecated_node_update
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:update:owner',
        check_str=SYSTEM_MEMBER,
        scope_types=['system', 'project'],
        description='Governs if node owner field can be updated via '
                    'the API clients.',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'PATCH'}],
        deprecated_rule=deprecated_node_update
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:update:driver_interfaces',
        check_str=SYSTEM_MEMBER_OR_OWNER_ADMIN,
        scope_types=['system', 'project'],
        description='Governs if node driver and driver interfaces field '
                    'can be updated via the API clients.',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'PATCH'}],
        deprecated_rule=deprecated_node_update
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:update:network_data',
        check_str=SYSTEM_MEMBER_OR_OWNER_MEMBER,
        scope_types=['system', 'project'],
        description='Governs if node driver_info field can be updated via '
                    'the API clients.',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'PATCH'}],
        deprecated_rule=deprecated_node_update
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:update:conductor_group',
        check_str=SYSTEM_MEMBER,
        scope_types=['system', 'project'],
        description='Governs if node conductor_group field can be updated '
                    'via the API clients.',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'PATCH'}],
        deprecated_rule=deprecated_node_update
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:update:name',
        check_str=SYSTEM_MEMBER_OR_OWNER_MEMBER,
        scope_types=['system', 'project'],
        description='Governs if node name field can be updated via '
                    'the API clients.',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'PATCH'}],
        deprecated_rule=deprecated_node_update
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:update:retired',
        check_str=SYSTEM_MEMBER_OR_OWNER_MEMBER,
        scope_types=['system', 'project'],
        description='Governs if node retired and retired reason '
                    'can be updated by API clients.',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'PATCH'}],
        deprecated_rule=deprecated_node_update
    ),

    # If this role is denied we should likely roll into the other rules
    # Like, this rule could match "SYSTEM_MEMBER" by default and then drill
    # further into each field, which would maintain what we do today, and
    # enable further testing.
    policy.DocumentedRuleDefault(
        name='baremetal:node:update',
        check_str=SYSTEM_OR_PROJECT_MEMBER,
        scope_types=['system', 'project'],
        description='Generalized update of node records',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'PATCH'}],
        deprecated_rule=deprecated_node_update
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:update_extra',
        check_str=SYSTEM_OR_PROJECT_MEMBER,
        scope_types=['system', 'project'],
        description='Update Node extra field',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'PATCH'}],
        deprecated_rule=deprecated_node_update_extra
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:update_instance_info',
        check_str=SYSTEM_OR_OWNER_MEMBER_AND_LESSEE_ADMIN,
        scope_types=['system', 'project'],
        description='Update Node instance_info field',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'PATCH'}],
        deprecated_rule=deprecated_node_update_instance_info
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:update_owner_provisioned',
        check_str=SYSTEM_ADMIN,
        scope_types=['system'],
        description='Update Node owner even when Node is provisioned',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'PATCH'}],
        deprecated_rule=deprecated_node_update_owner_provisioned
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:delete',
        check_str=SYSTEM_ADMIN,
        scope_types=['system', 'project'],
        description='Delete Node records',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'DELETE'}],
        deprecated_rule=deprecated_node_delete
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:delete:self_owned_node',
        check_str=PROJECT_ADMIN,
        scope_types=['system', 'project'],
        description='Delete node records which are associated with '
                    'the requesting project.',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'DELETE'}],
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:validate',
        check_str=SYSTEM_OR_OWNER_MEMBER_AND_LESSEE_ADMIN,
        scope_types=['system', 'project'],
        description='Request active validation of Nodes',
        operations=[
            {'path': '/nodes/{node_ident}/validate', 'method': 'GET'}
        ],
        deprecated_rule=deprecated_node_validate
    ),

    policy.DocumentedRuleDefault(
        name='baremetal:node:set_maintenance',
        check_str=SYSTEM_OR_OWNER_MEMBER_AND_LESSEE_ADMIN,
        scope_types=['system', 'project'],
        description='Set maintenance flag, taking a Node out of service',
        operations=[
            {'path': '/nodes/{node_ident}/maintenance', 'method': 'PUT'}
        ],
        deprecated_rule=deprecated_node_set_maintenance
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:clear_maintenance',
        check_str=SYSTEM_OR_OWNER_MEMBER_AND_LESSEE_ADMIN,
        scope_types=['system', 'project'],
        description=(
            'Clear maintenance flag, placing the Node into service again'
        ),
        operations=[
            {'path': '/nodes/{node_ident}/maintenance', 'method': 'DELETE'}
        ],
        deprecated_rule=deprecated_node_clear_maintenance
    ),

    # NOTE(TheJulia): This should likely be deprecated and be replaced with
    # a cached object.
    policy.DocumentedRuleDefault(
        name='baremetal:node:get_boot_device',
        check_str=SYSTEM_MEMBER_OR_OWNER_ADMIN,
        scope_types=['system', 'project'],
        description='Retrieve Node boot device metadata',
        operations=[
            {'path': '/nodes/{node_ident}/management/boot_device',
             'method': 'GET'},
            {'path': '/nodes/{node_ident}/management/boot_device/supported',
             'method': 'GET'}
        ],
        deprecated_rule=deprecated_node_get_boot_device
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:set_boot_device',
        check_str=SYSTEM_MEMBER_OR_OWNER_ADMIN,
        scope_types=['system', 'project'],
        description='Change Node boot device',
        operations=[
            {'path': '/nodes/{node_ident}/management/boot_device',
             'method': 'PUT'}
        ],
        deprecated_rule=deprecated_node_set_maintenance
    ),

    policy.DocumentedRuleDefault(
        name='baremetal:node:get_indicator_state',
        check_str=SYSTEM_OR_PROJECT_READER,
        scope_types=['system', 'project'],
        description='Retrieve Node indicators and their states',
        operations=[
            {'path': '/nodes/{node_ident}/management/indicators/'
                     '{component}/{indicator}',
             'method': 'GET'},
            {'path': '/nodes/{node_ident}/management/indicators',
             'method': 'GET'}
        ],
        deprecated_rule=deprecated_node_get_indicator_state
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:set_indicator_state',
        check_str=SYSTEM_MEMBER_OR_OWNER_MEMBER,
        scope_types=['system', 'project'],
        description='Change Node indicator state',
        operations=[
            {'path': '/nodes/{node_ident}/management/indicators/'
                     '{component}/{indicator}',
             'method': 'PUT'}
        ],
        deprecated_rule=deprecated_node_set_indicator_state
    ),

    policy.DocumentedRuleDefault(
        name='baremetal:node:inject_nmi',
        check_str=SYSTEM_MEMBER_OR_OWNER_ADMIN,
        scope_types=['system', 'project'],
        description='Inject NMI for a node',
        operations=[
            {'path': '/nodes/{node_ident}/management/inject_nmi',
             'method': 'PUT'}
        ],
        deprecated_rule=deprecated_node_inject_nmi
    ),

    policy.DocumentedRuleDefault(
        name='baremetal:node:get_states',
        check_str=SYSTEM_OR_PROJECT_READER,
        scope_types=['system', 'project'],
        description='View Node power and provision state',
        operations=[{'path': '/nodes/{node_ident}/states', 'method': 'GET'}],
        deprecated_rule=deprecated_node_get_states
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:set_power_state',
        check_str=SYSTEM_OR_PROJECT_MEMBER,
        scope_types=['system', 'project'],
        description='Change Node power status',
        operations=[
            {'path': '/nodes/{node_ident}/states/power', 'method': 'PUT'}
        ],
        deprecated_rule=deprecated_node_set_power_state
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:set_boot_mode',
        check_str=SYSTEM_OR_PROJECT_MEMBER,
        scope_types=['system', 'project'],
        description='Change Node boot mode',
        operations=[
            {'path': '/nodes/{node_ident}/states/boot_mode', 'method': 'PUT'}
        ],
        deprecated_rule=deprecated_node_set_power_state
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:set_secure_boot',
        check_str=SYSTEM_OR_PROJECT_MEMBER,
        scope_types=['system', 'project'],
        description='Change Node secure boot state',
        operations=[
            {'path': '/nodes/{node_ident}/states/secure_boot', 'method': 'PUT'}
        ],
        deprecated_rule=deprecated_node_set_power_state
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:set_provision_state',
        check_str=SYSTEM_OR_OWNER_MEMBER_AND_LESSEE_ADMIN,
        scope_types=['system', 'project'],
        description='Change Node provision status',
        operations=[
            {'path': '/nodes/{node_ident}/states/provision', 'method': 'PUT'}
        ],
        deprecated_rule=deprecated_node_set_provision_state
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:set_provision_state:clean_steps',
        check_str=SYSTEM_OR_OWNER_MEMBER_AND_LESSEE_ADMIN,
        scope_types=['system', 'project'],
        description='Allow execution of arbitrary steps on a node',
        operations=[
            {'path': '/nodes/{node_ident}/states/provision', 'method': 'PUT'}
        ],
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:set_provision_state:service_steps',
        check_str=SYSTEM_OR_OWNER_MEMBER_AND_LESSEE_ADMIN,
        scope_types=['system', 'project'],
        description='Allow execution of arbitrary steps on a node',
        operations=[
            {'path': '/nodes/{node_ident}/states/provision', 'method': 'PUT'}
        ],
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:set_raid_state',
        check_str=SYSTEM_MEMBER_OR_OWNER_MEMBER,
        scope_types=['system', 'project'],
        description='Change Node RAID status',
        operations=[
            {'path': '/nodes/{node_ident}/states/raid', 'method': 'PUT'}
        ],
        deprecated_rule=deprecated_node_set_raid_state
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:get_console',
        check_str=SYSTEM_MEMBER_OR_OWNER_MEMBER,
        scope_types=['system', 'project'],
        description='Get Node console connection information',
        operations=[
            {'path': '/nodes/{node_ident}/states/console', 'method': 'GET'}
        ],
        deprecated_rule=deprecated_node_get_console
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:set_console_state',
        check_str=SYSTEM_MEMBER_OR_OWNER_MEMBER,
        scope_types=['system', 'project'],
        description='Change Node console status',
        operations=[
            {'path': '/nodes/{node_ident}/states/console', 'method': 'PUT'}
        ],
        deprecated_rule=deprecated_node_set_console_state
    ),

    policy.DocumentedRuleDefault(
        name='baremetal:node:vif:list',
        check_str=SYSTEM_OR_PROJECT_READER,
        scope_types=['system', 'project'],
        description='List VIFs attached to node',
        operations=[{'path': '/nodes/{node_ident}/vifs', 'method': 'GET'}],
        deprecated_rule=deprecated_node_vif_list
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:vif:attach',
        check_str=SYSTEM_OR_OWNER_MEMBER_AND_LESSEE_ADMIN,
        scope_types=['system', 'project'],
        description='Attach a VIF to a node',
        operations=[{'path': '/nodes/{node_ident}/vifs', 'method': 'POST'}],
        deprecated_rule=deprecated_node_vif_attach
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:vif:detach',
        check_str=SYSTEM_OR_OWNER_MEMBER_AND_LESSEE_ADMIN,
        scope_types=['system', 'project'],
        description='Detach a VIF from a node',
        operations=[
            {'path': '/nodes/{node_ident}/vifs/{node_vif_ident}',
             'method': 'DELETE'}
        ],
        deprecated_rule=deprecated_node_vif_detach
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:traits:list',
        check_str=SYSTEM_OR_PROJECT_READER,
        scope_types=['system', 'project'],
        description='List node traits',
        operations=[{'path': '/nodes/{node_ident}/traits', 'method': 'GET'}],
        deprecated_rule=deprecated_node_traits_list
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:traits:set',
        check_str=SYSTEM_MEMBER_OR_OWNER_ADMIN,
        scope_types=['system', 'project'],
        description='Add a trait to, or replace all traits of, a node',
        operations=[
            {'path': '/nodes/{node_ident}/traits', 'method': 'PUT'},
            {'path': '/nodes/{node_ident}/traits/{trait}', 'method': 'PUT'}
        ],
        deprecated_rule=deprecated_node_traits_set
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:traits:delete',
        check_str=SYSTEM_MEMBER_OR_OWNER_ADMIN,
        scope_types=['system', 'project'],
        description='Remove one or all traits from a node',
        operations=[
            {'path': '/nodes/{node_ident}/traits', 'method': 'DELETE'},
            {'path': '/nodes/{node_ident}/traits/{trait}',
                     'method': 'DELETE'}
        ],
        deprecated_rule=deprecated_node_traits_delete
    ),

    policy.DocumentedRuleDefault(
        name='baremetal:node:bios:get',
        check_str=SYSTEM_OR_PROJECT_READER,
        scope_types=['system', 'project'],
        description='Retrieve Node BIOS information',
        operations=[
            {'path': '/nodes/{node_ident}/bios', 'method': 'GET'},
            {'path': '/nodes/{node_ident}/bios/{setting}', 'method': 'GET'}
        ],
        deprecated_rule=deprecated_node_bios_get
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:disable_cleaning',
        check_str=SYSTEM_ADMIN,
        scope_types=['system'],
        description='Disable Node disk cleaning',
        operations=[
            {'path': '/nodes/{node_ident}', 'method': 'PATCH'}
        ],
        deprecated_rule=deprecated_bios_disable_cleaning
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:history:get',
        check_str=SYSTEM_OR_OWNER_READER,
        scope_types=['system', 'project'],
        description='Filter to allow operators to retrieve history records '
                    'for a node.',
        operations=[
            {'path': '/nodes/{node_ident}/history', 'method': 'GET'},
            {'path': '/nodes/{node_ident}/history/{event_ident}',
             'method': 'GET'}
        ],
        # This rule fallsback to deprecated_node_get in order to provide a
        # mechanism so the additional policies only engage in an updated
        # operating context.
        deprecated_rule=deprecated_node_get
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:inventory:get',
        check_str=SYSTEM_OR_OWNER_READER,
        scope_types=['system', 'project'],
        description='Retrieve introspection data for a node.',
        operations=[
            {'path': '/nodes/{node_ident}/inventory', 'method': 'GET'},
        ],
        # This rule fallsback to deprecated_node_get in order to provide a
        # mechanism so the additional policies only engage in an updated
        # operating context.
        deprecated_rule=deprecated_node_get
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:update:shard',
        check_str=SYSTEM_ADMIN,
        scope_types=['system', 'project'],
        description='Governs if node shard field can be updated via '
                    'the API clients.',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'PATCH'}],
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:shards:get',
        check_str=SYSTEM_READER,
        scope_types=['system', 'project'],
        description='Governs if shards can be read via the API clients.',
        operations=[{'path': '/shards', 'method': 'GET'}],
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:update:parent_node',
        check_str=SYSTEM_MEMBER,
        scope_types=['system', 'project'],
        description='Governs if node parent_node field can be updated via '
                    'the API clients.',
        operations=[{'path': '/nodes/{node_ident}', 'method': 'PATCH'}],
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:firmware:get',
        check_str=SYSTEM_OR_PROJECT_READER,
        scope_types=['system', 'project'],
        description='Retrieve Node Firmware components information',
        operations=[
            {'path': '/nodes/{node_ident}/firmware', 'method': 'GET'}
        ],
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:vmedia:attach',
        check_str=SYSTEM_OR_PROJECT_MEMBER,
        scope_types=['system', 'project'],
        description='Attach a virtual media device to a node',
        operations=[
            {'path': '/nodes/{node_ident}/vmedia', 'method': 'POST'}\
        ],
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:vmedia:detach',
        check_str=SYSTEM_OR_PROJECT_MEMBER,
        scope_types=['system', 'project'],
        description='Detach a virtual media device from a node',
        operations=[
            {'path': '/nodes/{node_ident}/vmedia', 'method': 'DELETE'}
        ],
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:node:vmedia:get',
        check_str=SYSTEM_OR_PROJECT_READER,
        scope_types=['system', 'project'],
        description='Get virtual media device details from a node',
        operations=[
            {'path': '/nodes/{node_ident}/vmedia', 'method': 'GET'}
        ],
    ),
]

deprecated_port_reason = """
The baremetal port API is now aware of system scope and default roles.
"""
deprecated_port_get = policy.DeprecatedRule(
    name='baremetal:port:get',
    check_str='rule:is_admin or rule:is_observer',
    deprecated_reason=deprecated_port_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_port_list = policy.DeprecatedRule(
    name='baremetal:port:list',
    check_str='rule:baremetal:port:get',
    deprecated_reason=deprecated_port_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_port_list_all = policy.DeprecatedRule(
    name='baremetal:port:list_all',
    check_str='rule:baremetal:port:get',
    deprecated_reason=deprecated_port_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_port_create = policy.DeprecatedRule(
    name='baremetal:port:create',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_port_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_port_delete = policy.DeprecatedRule(
    name='baremetal:port:delete',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_port_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_port_update = policy.DeprecatedRule(
    name='baremetal:port:update',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_port_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)

port_policies = [
    policy.DocumentedRuleDefault(
        name='baremetal:port:get',
        check_str=SYSTEM_OR_PROJECT_READER,
        scope_types=['system', 'project'],
        description='Retrieve Port records',
        operations=[
            {'path': '/ports/{port_id}', 'method': 'GET'},
            {'path': '/nodes/{node_ident}/ports', 'method': 'GET'},
            {'path': '/nodes/{node_ident}/ports/detail', 'method': 'GET'},
            {'path': '/portgroups/{portgroup_ident}/ports', 'method': 'GET'},
            {'path': '/portgroups/{portgroup_ident}/ports/detail',
             'method': 'GET'}
        ],
        deprecated_rule=deprecated_port_get
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:port:list',
        check_str=API_READER,
        scope_types=['system', 'project'],
        description='Retrieve multiple Port records, filtered by owner',
        operations=[
            {'path': '/ports', 'method': 'GET'},
            {'path': '/ports/detail', 'method': 'GET'}
        ],
        deprecated_rule=deprecated_port_list
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:port:list_all',
        check_str=SYSTEM_READER,
        scope_types=['system', 'project'],
        description='Retrieve multiple Port records',
        operations=[
            {'path': '/ports', 'method': 'GET'},
            {'path': '/ports/detail', 'method': 'GET'}
        ],
        deprecated_rule=deprecated_port_list_all
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:port:create',
        check_str=SYSTEM_ADMIN_OR_OWNER_ADMIN,
        scope_types=['system', 'project'],
        description='Create Port records',
        operations=[{'path': '/ports', 'method': 'POST'}],
        deprecated_rule=deprecated_port_create
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:port:delete',
        check_str=SYSTEM_ADMIN_OR_OWNER_ADMIN,
        scope_types=['system', 'project'],
        description='Delete Port records',
        operations=[{'path': '/ports/{port_id}', 'method': 'DELETE'}],
        deprecated_rule=deprecated_port_delete
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:port:update',
        check_str=SYSTEM_MEMBER_OR_OWNER_ADMIN,
        scope_types=['system', 'project'],
        description='Update Port records',
        operations=[{'path': '/ports/{port_id}', 'method': 'PATCH'}],
        deprecated_rule=deprecated_port_update
    ),
]


deprecated_portgroup_reason = """
The baremetal port groups API is now aware of system scope and default roles.
"""
deprecated_portgroup_get = policy.DeprecatedRule(
    name='baremetal:portgroup:get',
    check_str='rule:is_admin or rule:is_observer',
    deprecated_reason=deprecated_portgroup_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_portgroup_create = policy.DeprecatedRule(
    name='baremetal:portgroup:create',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_portgroup_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_portgroup_delete = policy.DeprecatedRule(
    name='baremetal:portgroup:delete',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_portgroup_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_portgroup_update = policy.DeprecatedRule(
    name='baremetal:portgroup:update',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_portgroup_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)

portgroup_policies = [
    policy.DocumentedRuleDefault(
        name='baremetal:portgroup:get',
        check_str=SYSTEM_OR_PROJECT_READER,
        scope_types=['system', 'project'],
        description='Retrieve Portgroup records',
        operations=[
            {'path': '/portgroups', 'method': 'GET'},
            {'path': '/portgroups/detail', 'method': 'GET'},
            {'path': '/portgroups/{portgroup_ident}', 'method': 'GET'},
            {'path': '/nodes/{node_ident}/portgroups', 'method': 'GET'},
            {'path': '/nodes/{node_ident}/portgroups/detail', 'method': 'GET'},
        ],
        deprecated_rule=deprecated_portgroup_get
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:portgroup:create',
        check_str=SYSTEM_ADMIN_OR_OWNER_ADMIN,
        scope_types=['system', 'project'],
        description='Create Portgroup records',
        operations=[{'path': '/portgroups', 'method': 'POST'}],
        deprecated_rule=deprecated_portgroup_create
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:portgroup:delete',
        check_str=SYSTEM_ADMIN_OR_OWNER_ADMIN,
        scope_types=['system', 'project'],
        description='Delete Portgroup records',
        operations=[
            {'path': '/portgroups/{portgroup_ident}', 'method': 'DELETE'}
        ],
        deprecated_rule=deprecated_portgroup_delete
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:portgroup:update',
        check_str=SYSTEM_MEMBER_OR_OWNER_ADMIN,
        scope_types=['system', 'project'],
        description='Update Portgroup records',
        operations=[
            {'path': '/portgroups/{portgroup_ident}', 'method': 'PATCH'}
        ],
        deprecated_rule=deprecated_portgroup_update
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:portgroup:list',
        check_str=API_READER,
        scope_types=['system', 'project'],
        description='Retrieve multiple Port records, filtered by owner',
        operations=[
            {'path': '/portgroups', 'method': 'GET'},
            {'path': '/portgroups/detail', 'method': 'GET'}
        ],
        deprecated_rule=deprecated_portgroup_get
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:portgroup:list_all',
        check_str=SYSTEM_READER,
        scope_types=['system', 'project'],
        description='Retrieve multiple Port records',
        operations=[
            {'path': '/portgroups', 'method': 'GET'},
            {'path': '/portgroups/detail', 'method': 'GET'}
        ],
        deprecated_rule=deprecated_portgroup_get
    ),
]


deprecated_chassis_reason = """
The baremetal chassis API is now aware of system scope and default roles.
"""
deprecated_chassis_get = policy.DeprecatedRule(
    name='baremetal:chassis:get',
    check_str='rule:is_admin or rule:is_observer',
    deprecated_reason=deprecated_chassis_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_chassis_create = policy.DeprecatedRule(
    name='baremetal:chassis:create',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_chassis_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_chassis_delete = policy.DeprecatedRule(
    name='baremetal:chassis:delete',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_chassis_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_chassis_update = policy.DeprecatedRule(
    name='baremetal:chassis:update',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_chassis_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)

chassis_policies = [
    policy.DocumentedRuleDefault(
        name='baremetal:chassis:get',
        check_str=SYSTEM_READER,
        scope_types=['system'],
        description='Retrieve Chassis records',
        operations=[
            {'path': '/chassis', 'method': 'GET'},
            {'path': '/chassis/detail', 'method': 'GET'},
            {'path': '/chassis/{chassis_id}', 'method': 'GET'}
        ],
        deprecated_rule=deprecated_chassis_get
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:chassis:create',
        check_str=SYSTEM_ADMIN,
        scope_types=['system'],
        description='Create Chassis records',
        operations=[{'path': '/chassis', 'method': 'POST'}],
        deprecated_rule=deprecated_chassis_create
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:chassis:delete',
        check_str=SYSTEM_ADMIN,
        scope_types=['system'],
        description='Delete Chassis records',
        operations=[{'path': '/chassis/{chassis_id}', 'method': 'DELETE'}],
        deprecated_rule=deprecated_chassis_delete
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:chassis:update',
        check_str=SYSTEM_MEMBER,
        scope_types=['system'],
        description='Update Chassis records',
        operations=[{'path': '/chassis/{chassis_id}', 'method': 'PATCH'}],
        deprecated_rule=deprecated_chassis_update
    ),
]


deprecated_driver_reason = """
The baremetal driver API is now aware of system scope and default roles.
"""
deprecated_driver_get = policy.DeprecatedRule(
    name='baremetal:driver:get',
    check_str='rule:is_admin or rule:is_observer',
    deprecated_reason=deprecated_driver_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_driver_get_properties = policy.DeprecatedRule(
    name='baremetal:driver:get_properties',
    check_str='rule:is_admin or rule:is_observer',
    deprecated_reason=deprecated_driver_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_driver_get_raid_properties = policy.DeprecatedRule(
    name='baremetal:driver:get_raid_logical_disk_properties',
    check_str='rule:is_admin or rule:is_observer',
    deprecated_reason=deprecated_driver_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)

driver_policies = [
    policy.DocumentedRuleDefault(
        name='baremetal:driver:get',
        check_str=SYSTEM_READER,
        scope_types=['system'],
        description='View list of available drivers',
        operations=[
            {'path': '/drivers', 'method': 'GET'},
            {'path': '/drivers/{driver_name}', 'method': 'GET'}
        ],
        deprecated_rule=deprecated_driver_get
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:driver:get_properties',
        check_str=SYSTEM_READER,
        scope_types=['system'],
        description='View driver-specific properties',
        operations=[
            {'path': '/drivers/{driver_name}/properties', 'method': 'GET'}
        ],
        deprecated_rule=deprecated_driver_get_properties
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:driver:get_raid_logical_disk_properties',
        check_str=SYSTEM_READER,
        scope_types=['system'],
        description='View driver-specific RAID metadata',
        operations=[
            {'path': '/drivers/{driver_name}/raid/logical_disk_properties',
             'method': 'GET'}
        ],
        deprecated_rule=deprecated_driver_get_raid_properties
    ),
]


deprecated_vendor_reason = """
The baremetal vendor passthru API is now aware of system scope and default
roles.
"""
deprecated_node_passthru = policy.DeprecatedRule(
    name='baremetal:node:vendor_passthru',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_vendor_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_driver_passthru = policy.DeprecatedRule(
    name='baremetal:driver:vendor_passthru',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_vendor_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)

vendor_passthru_policies = [
    policy.DocumentedRuleDefault(
        name='baremetal:node:vendor_passthru',
        check_str=SYSTEM_ADMIN,
        # NOTE(TheJulia): Project scope listed, but not a project scoped role
        # as some operators may find it useful to provide access to say owner
        # admins.
        scope_types=['system', 'project'],
        description='Access vendor-specific Node functions',
        operations=[
            {'path': 'nodes/{node_ident}/vendor_passthru/methods',
             'method': 'GET'},
            {'path': 'nodes/{node_ident}/vendor_passthru?method={method_name}',
             'method': 'GET'},
            {'path': 'nodes/{node_ident}/vendor_passthru?method={method_name}',
             'method': 'PUT'},
            {'path': 'nodes/{node_ident}/vendor_passthru?method={method_name}',
             'method': 'POST'},
            {'path': 'nodes/{node_ident}/vendor_passthru?method={method_name}',
             'method': 'PATCH'},
            {'path': 'nodes/{node_ident}/vendor_passthru?method={method_name}',
             'method': 'DELETE'},
        ],
        deprecated_rule=deprecated_node_passthru
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:driver:vendor_passthru',
        check_str=SYSTEM_ADMIN,
        scope_types=['system'],
        description='Access vendor-specific Driver functions',
        operations=[
            {'path': 'drivers/{driver_name}/vendor_passthru/methods',
             'method': 'GET'},
            {'path': 'drivers/{driver_name}/vendor_passthru?'
                     'method={method_name}',
             'method': 'GET'},
            {'path': 'drivers/{driver_name}/vendor_passthru?'
                     'method={method_name}',
             'method': 'PUT'},
            {'path': 'drivers/{driver_name}/vendor_passthru?'
                     'method={method_name}',
             'method': 'POST'},
            {'path': 'drivers/{driver_name}/vendor_passthru?'
                     'method={method_name}',
             'method': 'PATCH'},
            {'path': 'drivers/{driver_name}/vendor_passthru?'
                     'method={method_name}',
             'method': 'DELETE'}
        ],
        deprecated_rule=deprecated_driver_passthru
    ),
]


deprecated_utility_reason = """
The baremetal utility API is now aware of system scope and default
roles.
"""
deprecated_ipa_heartbeat = policy.DeprecatedRule(
    name='baremetal:node:ipa_heartbeat',
    check_str='rule:public_api',
    deprecated_reason=deprecated_utility_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_ipa_lookup = policy.DeprecatedRule(
    name='baremetal:driver:ipa_lookup',
    check_str='rule:public_api',
    deprecated_reason=deprecated_utility_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)

# NOTE(TheJulia): Empty check strings basically mean nothing to apply,
# and the request is permitted.
utility_policies = [
    policy.DocumentedRuleDefault(
        name='baremetal:node:ipa_heartbeat',
        check_str='',
        description='Receive heartbeats from IPA ramdisk',
        operations=[{'path': '/heartbeat/{node_ident}', 'method': 'POST'}],
        deprecated_rule=deprecated_ipa_heartbeat
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:driver:ipa_lookup',
        check_str='',
        description='Access IPA ramdisk functions',
        operations=[{'path': '/lookup', 'method': 'GET'}],
        deprecated_rule=deprecated_ipa_lookup
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:driver:ipa_continue_inspection',
        check_str='',
        description='Receive inspection data from the ramdisk',
        operations=[{'path': '/continue_inspection', 'method': 'POST'}],
    ),
]


deprecated_volume_reason = """
The baremetal volume API is now aware of system scope and default
roles.
"""
deprecated_volume_get = policy.DeprecatedRule(
    name='baremetal:volume:get',
    check_str='rule:is_admin or rule:is_observer',
    deprecated_reason=deprecated_volume_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_volume_create = policy.DeprecatedRule(
    name='baremetal:volume:create',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_volume_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_volume_delete = policy.DeprecatedRule(
    name='baremetal:volume:delete',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_volume_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_volume_update = policy.DeprecatedRule(
    name='baremetal:volume:update',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_volume_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)

volume_policies = [
    policy.DocumentedRuleDefault(
        name='baremetal:volume:list_all',
        check_str=SYSTEM_READER,
        scope_types=['system', 'project'],
        description=('Retrieve a list of all Volume connector and target '
                     'records'),
        operations=[
            {'path': '/volume/connectors', 'method': 'GET'},
            {'path': '/volume/targets', 'method': 'GET'},
            {'path': '/nodes/{node_ident}/volume/connectors', 'method': 'GET'},
            {'path': '/nodes/{node_ident}/volume/targets', 'method': 'GET'}
        ],
        deprecated_rule=deprecated_volume_get
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:volume:list',
        check_str=API_READER,
        scope_types=['system', 'project'],
        description='Retrieve a list of Volume connector and target records',
        operations=[
            {'path': '/volume/connectors', 'method': 'GET'},
            {'path': '/volume/targets', 'method': 'GET'},
            {'path': '/nodes/{node_ident}/volume/connectors', 'method': 'GET'},
            {'path': '/nodes/{node_ident}/volume/targets', 'method': 'GET'}
        ],
        deprecated_rule=deprecated_volume_get
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:volume:get',
        check_str=SYSTEM_OR_PROJECT_READER,
        scope_types=['system', 'project'],
        description='Retrieve Volume connector and target records',
        operations=[
            {'path': '/volume', 'method': 'GET'},
            {'path': '/volume/connectors', 'method': 'GET'},
            {'path': '/volume/connectors/{volume_connector_id}',
             'method': 'GET'},
            {'path': '/volume/targets', 'method': 'GET'},
            {'path': '/volume/targets/{volume_target_id}', 'method': 'GET'},
            {'path': '/nodes/{node_ident}/volume', 'method': 'GET'},
            {'path': '/nodes/{node_ident}/volume/connectors', 'method': 'GET'},
            {'path': '/nodes/{node_ident}/volume/targets', 'method': 'GET'}
        ],
        deprecated_rule=deprecated_volume_get
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:volume:create',
        check_str=SYSTEM_MEMBER_OR_OWNER_LESSEE_ADMIN,
        scope_types=['system', 'project'],
        description='Create Volume connector and target records',
        operations=[
            {'path': '/volume/connectors', 'method': 'POST'},
            {'path': '/volume/targets', 'method': 'POST'}
        ],
        deprecated_rule=deprecated_volume_create
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:volume:delete',
        check_str=SYSTEM_MEMBER_OR_OWNER_LESSEE_ADMIN,
        scope_types=['system', 'project'],
        description='Delete Volume connector and target records',
        operations=[
            {'path': '/volume/connectors/{volume_connector_id}',
             'method': 'DELETE'},
            {'path': '/volume/targets/{volume_target_id}',
             'method': 'DELETE'}
        ],
        deprecated_rule=deprecated_volume_delete
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:volume:update',
        check_str=SYSTEM_OR_OWNER_MEMBER_AND_LESSEE_ADMIN,
        scope_types=['system', 'project'],
        description='Update Volume connector and target records',
        operations=[
            {'path': '/volume/connectors/{volume_connector_id}',
             'method': 'PATCH'},
            {'path': '/volume/targets/{volume_target_id}',
             'method': 'PATCH'}
        ],
        deprecated_rule=deprecated_volume_update
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:volume:view_target_properties',
        check_str=TARGET_PROPERTIES_READER,
        scope_types=['system', 'project'],
        description='Ability to view volume target properties',
        operations=[
            {'path': '/volume/connectors/{volume_connector_id}',
             'method': 'GET'},
            {'path': '/volume/targets/{volume_target_id}',
             'method': 'GET'}
        ],
        deprecated_rule=deprecated_volume_update
    ),
]


deprecated_conductor_reason = """
The baremetal conductor API is now aware of system scope and default
roles.
"""
deprecated_conductor_get = policy.DeprecatedRule(
    name='baremetal:conductor:get',
    check_str='rule:is_admin or rule:is_observer',
    deprecated_reason=deprecated_conductor_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)

conductor_policies = [
    policy.DocumentedRuleDefault(
        name='baremetal:conductor:get',
        check_str=SYSTEM_READER,
        scope_types=['system', 'project'],
        description='Retrieve Conductor records',
        operations=[
            {'path': '/conductors', 'method': 'GET'},
            {'path': '/conductors/{hostname}', 'method': 'GET'}
        ],
        deprecated_rule=deprecated_conductor_get
    ),
]


deprecated_allocation_reason = """
The baremetal allocation API is now aware of system scope and default
roles.
"""
deprecated_allocation_get = policy.DeprecatedRule(
    name='baremetal:allocation:get',
    check_str='rule:is_admin or rule:is_observer',
    deprecated_reason=deprecated_allocation_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_allocation_list = policy.DeprecatedRule(
    name='baremetal:allocation:list',
    check_str='rule:baremetal:allocation:get',
    deprecated_reason=deprecated_allocation_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_allocation_list_all = policy.DeprecatedRule(
    name='baremetal:allocation:list_all',
    check_str='rule:baremetal:allocation:get and is_admin_project:True',
    deprecated_reason=deprecated_allocation_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_allocation_create = policy.DeprecatedRule(
    name='baremetal:allocation:create',
    check_str='rule:is_admin and is_admin_project:True',
    deprecated_reason=deprecated_allocation_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_allocation_create_restricted = policy.DeprecatedRule(
    name='baremetal:allocation:create_restricted',
    check_str='rule:baremetal:allocation:create',
    deprecated_reason=deprecated_allocation_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_allocation_delete = policy.DeprecatedRule(
    name='baremetal:allocation:delete',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_allocation_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_allocation_update = policy.DeprecatedRule(
    name='baremetal:allocation:update',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_allocation_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)

allocation_policies = [
    policy.DocumentedRuleDefault(
        name='baremetal:allocation:get',
        check_str=ALLOCATION_READER,
        scope_types=['system', 'project'],
        description='Retrieve Allocation records',
        operations=[
            {'path': '/allocations/{allocation_id}', 'method': 'GET'},
            {'path': '/nodes/{node_ident}/allocation', 'method': 'GET'}
        ],
        deprecated_rule=deprecated_allocation_get
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:allocation:list',
        check_str=API_READER,
        scope_types=['system', 'project'],
        description='Retrieve multiple Allocation records, filtered by owner',
        operations=[{'path': '/allocations', 'method': 'GET'}],
        deprecated_rule=deprecated_allocation_list
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:allocation:list_all',
        check_str=SYSTEM_READER,
        scope_types=['system', 'project'],
        description='Retrieve multiple Allocation records',
        operations=[{'path': '/allocations', 'method': 'GET'}],
        deprecated_rule=deprecated_allocation_list_all
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:allocation:create',
        check_str=ALLOCATION_CREATOR,
        scope_types=['system', 'project'],
        description='Create Allocation records',
        operations=[{'path': '/allocations', 'method': 'POST'}],
        deprecated_rule=deprecated_allocation_create
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:allocation:create_restricted',
        check_str=SYSTEM_MEMBER,
        scope_types=['system', 'project'],
        description=(
            'Create Allocation records with a specific owner.'
        ),
        operations=[{'path': '/allocations', 'method': 'POST'}],
        deprecated_rule=deprecated_allocation_create_restricted
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:allocation:delete',
        check_str=ALLOCATION_MEMBER,
        scope_types=['system', 'project'],
        description='Delete Allocation records',
        operations=[
            {'path': '/allocations/{allocation_id}', 'method': 'DELETE'},
            {'path': '/nodes/{node_ident}/allocation', 'method': 'DELETE'}],
        deprecated_rule=deprecated_allocation_delete
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:allocation:update',
        check_str=ALLOCATION_MEMBER,
        scope_types=['system', 'project'],
        description='Change name and extra fields of an allocation',
        operations=[
            {'path': '/allocations/{allocation_id}', 'method': 'PATCH'},
        ],
        deprecated_rule=deprecated_allocation_update
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:allocation:create_pre_rbac',
        # NOTE(TheJulia): First part of the check string is for classical
        # administrative rights with someone using a baremetal project.
        # The latter is more for projects and services using admin project
        # rights. Specific checking because of the expanded rights of
        # this functionality.
        check_str=('(rule:is_member and role:baremetal_admin) or (is_admin_project:True and role:admin)'),  # noqa
        scope_types=['project'],
        description=('Logical restrictor to prevent legacy allocation rule '
                     'missuse - Requires blank allocations to originate from '
                     'the legacy baremetal_admin.'),
        operations=[
            {'path': '/allocations/{allocation_id}', 'method': 'PATCH'},
        ],
        deprecated_reason=deprecated_allocation_reason
    ),

]


deprecated_event_reason = """
The baremetal event API is now aware of system scope and default
roles.
"""
deprecated_event_create = policy.DeprecatedRule(
    name='baremetal:events:post',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_event_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)

event_policies = [
    policy.DocumentedRuleDefault(
        name='baremetal:events:post',
        check_str=SYSTEM_ADMIN,
        scope_types=['system'],
        description='Post events',
        operations=[{'path': '/events', 'method': 'POST'}],
        deprecated_rule=deprecated_event_create
    )
]


deprecated_template_reason = """
The baremetal deploy template API is now aware of system scope and
default roles.
"""
deprecated_deploy_template_get = policy.DeprecatedRule(
    name='baremetal:deploy_template:get',
    check_str='rule:is_admin or rule:is_observer',
    deprecated_reason=deprecated_template_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_deploy_template_create = policy.DeprecatedRule(
    name='baremetal:deploy_template:create',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_template_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_deploy_template_delete = policy.DeprecatedRule(
    name='baremetal:deploy_template:delete',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_template_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_deploy_template_update = policy.DeprecatedRule(
    name='baremetal:deploy_template:update',
    check_str='rule:is_admin',
    deprecated_reason=deprecated_template_reason,
    deprecated_since=versionutils.deprecated.WALLABY
)

deploy_template_policies = [
    policy.DocumentedRuleDefault(
        name='baremetal:deploy_template:get',
        check_str=SYSTEM_READER,
        scope_types=['system', 'project'],
        description='Retrieve Deploy Template records',
        operations=[
            {'path': '/deploy_templates', 'method': 'GET'},
            {'path': '/deploy_templates/{deploy_template_ident}',
             'method': 'GET'}
        ],
        deprecated_rule=deprecated_deploy_template_get
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:deploy_template:create',
        check_str=SYSTEM_ADMIN,
        scope_types=['system', 'project'],
        description='Create Deploy Template records',
        operations=[{'path': '/deploy_templates', 'method': 'POST'}],
        deprecated_rule=deprecated_deploy_template_create
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:deploy_template:delete',
        check_str=SYSTEM_ADMIN,
        scope_types=['system', 'project'],
        description='Delete Deploy Template records',
        operations=[
            {'path': '/deploy_templates/{deploy_template_ident}',
             'method': 'DELETE'}
        ],
        deprecated_rule=deprecated_deploy_template_delete
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:deploy_template:update',
        check_str=SYSTEM_ADMIN,
        scope_types=['system', 'project'],
        description='Update Deploy Template records',
        operations=[
            {'path': '/deploy_templates/{deploy_template_ident}',
             'method': 'PATCH'}
        ],
        deprecated_rule=deprecated_deploy_template_update
    ),
]

runbook_policies = [
    policy.DocumentedRuleDefault(
        name='baremetal:runbook:get',
        check_str=RUNBOOK_READER,
        scope_types=['system', 'project'],
        description='Retrieve a single runbook record',
        operations=[
            {'path': '/runbooks/{runbook_ident}', 'method': 'GET'}
        ],
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:runbook:list',
        check_str=API_READER,
        scope_types=['system', 'project'],
        description='Retrieve multiple runbook records, filtered by '
                    'an explicit owner or the client project_id',
        operations=[
            {'path': '/runbooks', 'method': 'GET'}
        ],
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:runbook:list_all',
        check_str=SYSTEM_READER,
        scope_types=['system', 'project'],
        description='Retrieve all runbook records',
        operations=[
            {'path': '/runbooks', 'method': 'GET'}
        ],
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:runbook:create',
        check_str=RUNBOOK_CREATOR,
        scope_types=['system', 'project'],
        description='Create Runbook records',
        operations=[{'path': '/runbooks', 'method': 'POST'}],
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:runbook:delete',
        check_str=RUNBOOK_ADMIN,
        scope_types=['system', 'project'],
        description='Delete a runbook record',
        operations=[
            {'path': '/runbooks/{runbook_ident}', 'method': 'DELETE'}
        ],
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:runbook:update',
        check_str=RUNBOOK_ADMIN,
        scope_types=['system', 'project'],
        description='Update a runbook record',
        operations=[
            {'path': '/runbooks/{runbook_ident}', 'method': 'PATCH'}
        ],
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:runbook:update:public',
        check_str=SYSTEM_MEMBER,
        scope_types=['system', 'project'],
        description='Set and unset a runbook as public',
        operations=[
            {'path': '/runbooks/{runbook_ident}/public', 'method': 'PATCH'}
        ],
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:runbook:update:owner',
        check_str=SYSTEM_MEMBER,
        scope_types=['system', 'project'],
        description='Set and unset the owner of a runbook',
        operations=[
            {'path': '/runbooks/{runbook_ident}/owner', 'method': 'PATCH'}
        ],
    ),
    policy.DocumentedRuleDefault(
        name='baremetal:runbook:use',
        check_str=RUNBOOK_ADMIN,
        scope_types=['system', 'project'],
        description='Allowed to use a runbook for node operations',
        operations=[
            {'path': '/nodes/{node_ident}/states/provision', 'method': 'PUT'}
        ],
    )
]


def list_policies():
    policies = itertools.chain(
        default_policies,
        node_policies,
        port_policies,
        portgroup_policies,
        chassis_policies,
        driver_policies,
        vendor_passthru_policies,
        utility_policies,
        volume_policies,
        conductor_policies,
        allocation_policies,
        event_policies,
        deploy_template_policies,
        runbook_policies,
    )
    return policies


@lockutils.synchronized('policy_enforcer')
def init_enforcer(policy_file=None, rules=None,
                  default_rule=None, use_conf=True):
    """Synchronously initializes the policy enforcer

       :param policy_file: Custom policy file to use, if none is specified,
                           `CONF.oslo_policy.policy_file` will be used.
       :param rules: Default dictionary / Rules to use. It will be
                     considered just in the first instantiation.
       :param default_rule: Default rule to use,
                            CONF.oslo_policy.policy_default_rule will
                            be used if none is specified.
       :param use_conf: Whether to load rules from config file.

    """
    global _ENFORCER

    if _ENFORCER:
        return

    # NOTE(tenbrae): Register defaults for policy-in-code here so that they are
    # loaded exactly once - when this module-global is initialized.
    # Defining these in the relevant API modules won't work
    # because API classes lack singletons and don't use globals.
    _ENFORCER = policy.Enforcer(
        CONF, policy_file=policy_file,
        rules=rules,
        default_rule=default_rule,
        use_conf=use_conf)
    # NOTE(melwitt): Explicitly disable the warnings for policies
    # changing their default check_str. During policy-defaults-refresh
    # work, all the policy defaults have been changed and warning for
    # each policy started filling the logs limit for various tool.
    # Once we move to new defaults only world then we can enable these
    # warning again.
    # TODO(TheJulia): *When* we go to enable warnings to be indicated
    # we need to update the notice in the logs to indicate *when* the
    # support for older policies will be removed.
    _ENFORCER.suppress_default_change_warnings = True
    _ENFORCER.register_defaults(list_policies())


def get_enforcer():
    """Provides access to the single instance of Policy enforcer."""

    if not _ENFORCER:
        init_enforcer()

    return _ENFORCER


def get_oslo_policy_enforcer():
    # This method is for use by oslopolicy CLI scripts. Those scripts need the
    # 'output-file' and 'namespace' options, but having those in sys.argv means
    # loading the Ironic config options will fail as those are not expected to
    # be present. So we pass in an arg list with those stripped out.

    conf_args = []
    # Start at 1 because cfg.CONF expects the equivalent of sys.argv[1:]
    i = 1
    while i < len(sys.argv):
        if sys.argv[i].strip('-') in ['namespace', 'output-file']:
            i += 2
            continue
        conf_args.append(sys.argv[i])
        i += 1

    cfg.CONF(conf_args, project='ironic')

    return get_enforcer()


# NOTE(tenbrae): We can't call these methods from within decorators because the
# 'target' and 'creds' parameter must be fetched from the call time
# context-local pecan.request magic variable, but decorators are compiled
# at module-load time.


def authorize(rule, target, creds, *args, **kwargs):
    """A shortcut for policy.Enforcer.authorize()

    Checks authorization of a rule against the target and credentials, and
    raises an exception if the rule is not defined.
    Always returns true if CONF.auth_strategy is not keystone.
    """
    if CONF.auth_strategy != 'keystone':
        return True
    enforcer = get_enforcer()
    try:
        return enforcer.authorize(rule, target, creds, do_raise=True,
                                  *args, **kwargs)
    except policy.PolicyNotAuthorized as e:
        LOG.error('Rejecting authorization: %(error)s',
                  {'error': e})
        raise exception.HTTPForbidden(resource=rule)


def check(rule, target, creds, *args, **kwargs):
    """A shortcut for policy.Enforcer.enforce()

    Checks authorization of a rule against the target and credentials
    and returns True or False.
    """
    enforcer = get_enforcer()
    return enforcer.enforce(rule, target, creds, *args, **kwargs)


def check_policy(rule, target, creds, *args, **kwargs):
    """Configuration aware role policy check wrapper.

    Checks authorization of a rule against the target and credentials
    and returns True or False.
    Always returns true if CONF.auth_strategy is not keystone.
    """
    if CONF.auth_strategy != 'keystone':
        return True
    enforcer = get_enforcer()
    return enforcer.enforce(rule, target, creds, *args, **kwargs)
