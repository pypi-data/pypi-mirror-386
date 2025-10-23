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

"""
Version 1 of the Ironic API

Specification can be found at doc/source/webapi/v1.rst
"""

from http import client as http_client

import pecan
from webob import exc

from ironic import api
from ironic.api.controllers import base
from ironic.api.controllers import link
from ironic.api.controllers.v1 import allocation
from ironic.api.controllers.v1 import chassis
from ironic.api.controllers.v1 import conductor
from ironic.api.controllers.v1 import deploy_template
from ironic.api.controllers.v1 import driver
from ironic.api.controllers.v1 import event
from ironic.api.controllers.v1 import node
from ironic.api.controllers.v1 import port
from ironic.api.controllers.v1 import portgroup
from ironic.api.controllers.v1 import ramdisk
from ironic.api.controllers.v1 import runbook
from ironic.api.controllers.v1 import shard
from ironic.api.controllers.v1 import utils
from ironic.api.controllers.v1 import versions
from ironic.api.controllers.v1 import volume
from ironic.api.controllers import version
from ironic.api import method
from ironic.common.i18n import _

BASE_VERSION = versions.BASE_VERSION


def min_version():
    return base.Version(
        {base.Version.string: versions.min_version_string()},
        versions.min_version_string(), versions.max_version_string())


def max_version():
    return base.Version(
        {base.Version.string: versions.max_version_string()},
        versions.min_version_string(), versions.max_version_string())


def make_controller_links(name):
    return [
        link.make_link('self', api.request.public_url, name, ''),
        link.make_link('bookmark', api.request.public_url, name, '',
                       bookmark=True)
    ]


VERSIONED_CONTROLLERS = {
    'portgroups': utils.allow_portgroups,
    'volume': utils.allow_volume,
    'lookup': utils.allow_ramdisk_endpoints,
    'heartbeat': utils.allow_ramdisk_endpoints,
    'conductors': utils.allow_expose_conductors,
    'allocations': utils.allow_allocations,
    'events': utils.allow_expose_events,
    'deploy_templates': utils.allow_deploy_templates,
    'shards': utils.allow_shards_endpoint,
    'runbooks': utils.allow_runbooks,
    # NOTE(dtantsur): continue_inspection is available in 1.1 as a
    # compatibility hack to make it usable with IPA without changes.
    # Hide this fact from consumers since it was not actually available
    # back in Kilo.
    'continue_inspection': utils.new_continue_inspection_endpoint,
}


def v1():
    v1 = {
        'id': "v1",
        'links': [
            link.make_link('self', api.request.public_url,
                           'v1', '', bookmark=True),
            link.make_link('describedby',
                           'https://docs.openstack.org',
                           '/ironic/latest/contributor/',
                           'webapi.html',
                           bookmark=True, type='text/html')
        ],
        'media_types': {
            'base': 'application/json',
            'type': 'application/vnd.openstack.ironic.v1+json'
        },
        'chassis': make_controller_links('chassis'),
        'nodes': make_controller_links('nodes'),
        'ports': make_controller_links('ports'),
        'drivers': make_controller_links('drivers'),
        'version': version.default_version(),
    }
    for link_name, check_func in VERSIONED_CONTROLLERS.items():
        if check_func():
            v1[link_name] = make_controller_links(link_name)
    return v1


class Controller(object):
    """Version 1 API controller root."""

    _subcontroller_map = {
        'nodes': node.NodesController(),
        'ports': port.PortsController(),
        'portgroups': portgroup.PortgroupsController(),
        'chassis': chassis.ChassisController(),
        'drivers': driver.DriversController(),
        'volume': volume.VolumeController(),
        'lookup': ramdisk.LookupController(),
        'heartbeat': ramdisk.HeartbeatController(),
        'conductors': conductor.ConductorsController(),
        'allocations': allocation.AllocationsController(),
        'events': event.EventsController(),
        'deploy_templates': deploy_template.DeployTemplatesController(),
        'shards': shard.ShardController(),
        'continue_inspection': ramdisk.ContinueInspectionController(),
        'runbooks': runbook.RunbooksController()
    }

    @method.expose()
    def index(self):
        # NOTE: The reason why v1() it's being called for every
        #       request is because we need to get the host url from
        #       the request object to make the links.
        if api.request.method not in ('GET', 'HEAD'):
            pecan.abort(http_client.METHOD_NOT_ALLOWED)

        return v1()

    def _check_version(self, version, headers=None):
        if headers is None:
            headers = {}
        # ensure that major version in the URL matches the header
        if version.major != BASE_VERSION:
            raise exc.HTTPNotAcceptable(_(
                "Mutually exclusive versions requested. Version %(ver)s "
                "requested but not supported by this service. The supported "
                "version range is: [%(min)s, %(max)s].") %
                {'ver': version, 'min': versions.min_version_string(),
                 'max': versions.max_version_string()},
                headers=headers)
        # ensure the minor version is within the supported range
        if version < min_version() or version > max_version():
            raise exc.HTTPNotAcceptable(_(
                "Version %(ver)s was requested but the minor version is not "
                "supported by this service. The supported version range is: "
                "[%(min)s, %(max)s].") %
                {'ver': version, 'min': versions.min_version_string(),
                 'max': versions.max_version_string()},
                headers=headers)

    def add_version_attributes(self):
        v = base.Version(api.request.headers, versions.min_version_string(),
                         versions.max_version_string())

        # Always set the min and max headers
        api.response.headers[base.Version.min_string] = (
            versions.min_version_string())
        api.response.headers[base.Version.max_string] = (
            versions.max_version_string())

        # assert that requested version is supported
        self._check_version(v, api.response.headers)
        api.response.headers[base.Version.string] = str(v)
        api.request.version = v

    @pecan.expose()
    def _lookup(self, primary_key, *remainder):

        controller = self._subcontroller_map.get(primary_key)
        if not controller:
            pecan.abort(http_client.NOT_FOUND)

        return controller, remainder


__all__ = ('Controller',)
