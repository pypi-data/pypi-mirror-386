# Copyright (c) 2011 Citrix Systems, Inc.
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

import io

from openstack.connection import exceptions as openstack_exc


NOW_GLANCE_FORMAT = "2010-10-11T10:30:22"


class StubGlanceClient(object):

    image_data = b'this is an image'

    def __init__(self, images=None):
        self._images = []
        _images = images or []
        map(lambda image: self.create(**image), _images)

    def get_image(self, image_id):
        for image in self._images:
            if image.id == str(image_id):
                return image
        raise openstack_exc.NotFoundException(image_id)

    def download_image(self, image_id, stream=False):
        self.get_image(image_id)
        if stream:
            return io.BytesIO(self.image_data)
        else:
            return FakeImageDownload(self.image_data)


class FakeImageDownload(object):

    content = None

    def __init__(self, content):
        self.content = content


class FakeNeutronPort(dict):
    def __init__(self, **attrs):
        PORT_ATTRS = ['admin_state_up',
                      'allowed_address_pairs',
                      'binding:host_id',
                      'binding:profile',
                      'binding:vif_details',
                      'binding:vif_type',
                      'binding:vnic_type',
                      'data_plane_status',
                      'description',
                      'device_id',
                      'device_owner',
                      'dns_assignment',
                      'dns_domain',
                      'dns_name',
                      'extra_dhcp_opts',
                      'fixed_ips',
                      'id',
                      'mac_address',
                      'name', 'network_id',
                      'port_security_enabled',
                      'security_group_ids',
                      'status',
                      'tenant_id',
                      'qos_network_policy_id',
                      'qos_policy_id',
                      'tags',
                      'uplink_status_propagation']

        raw = dict.fromkeys(PORT_ATTRS)
        raw.update(attrs)
        super(FakeNeutronPort, self).__init__(raw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        if key in self:
            self[key] = value
        else:
            raise AttributeError(key)


class FakeNeutronSubnet(dict):
    def __init__(self, **attrs):
        SUBNET_ATTRS = ['id',
                        'name',
                        'network_id',
                        'cidr',
                        'tenant_id',
                        'enable_dhcp',
                        'dns_nameservers',
                        'allocation_pools',
                        'host_routes',
                        'ip_version',
                        'gateway_ip',
                        'ipv6_address_mode',
                        'ipv6_ra_mode',
                        'subnetpool_id',
                        'segment_id']

        raw = dict.fromkeys(SUBNET_ATTRS)
        raw.update(attrs)
        super(FakeNeutronSubnet, self).__init__(raw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        if key in self:
            self[key] = value
        else:
            raise AttributeError(key)


class FakeNeutronSegment(dict):
    def __init__(self, **attrs):
        SEGMENT_ATTRS = ['id',
                         'name',
                         'network_id',
                         'network_type',
                         'physical_network',
                         'segmentation_id']

        raw = dict.fromkeys(SEGMENT_ATTRS)
        raw.update(attrs)
        super(FakeNeutronSegment, self).__init__(raw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        if key in self:
            self[key] = value
        else:
            raise AttributeError(key)


class FakeNeutronNetwork(dict):
    def __init__(self, **attrs):
        NETWORK_ATTRS = ['id',
                         'name',
                         'status',
                         'tenant_id',
                         'admin_state_up',
                         'segments',
                         'shared',
                         'subnets',
                         'provider:network_type',
                         'provider:physical_network',
                         'provider:segmentation_id',
                         'router:external',
                         'availability_zones',
                         'availability_zone_hints',
                         'is_default']

        raw = dict.fromkeys(NETWORK_ATTRS)
        raw.update(attrs)
        raw.update({
            'provider_physical_network': attrs.get(
                'provider:physical_network', None)})
        super(FakeNeutronNetwork, self).__init__(raw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        if key in self:
            self[key] = value
        else:
            raise AttributeError(key)


class FakeNeutronAgent(dict):
    def __init__(self, **attrs):
        AGENT_ATTRS = ['admin_state_up',
                       'agents',
                       'agent_type',
                       'alive',
                       'availability_zone',
                       'binary',
                       'configurations',
                       'created_at',
                       'description',
                       'heartbeat_timestamp',
                       'host',
                       'id',
                       'resources_synced',
                       'started_at',
                       'topic']

        raw = dict.fromkeys(AGENT_ATTRS)
        raw.update(attrs)
        raw.update({'is_alive': attrs.get('alive', False)})
        super(FakeNeutronAgent, self).__init__(raw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        if key in self:
            self[key] = value
        else:
            raise AttributeError(key)


class FakeNeutronSecurityGroup(dict):
    def __init__(self, **attrs):
        SECURITY_GROUP_ATTRS = ['id',
                                'name',
                                'description',
                                'stateful',
                                'project_id',
                                'tenant_id',
                                'security_group_rules']

        raw = dict.fromkeys(SECURITY_GROUP_ATTRS)
        raw.update(attrs)
        super(FakeNeutronSecurityGroup, self).__init__(raw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        if key in self:
            self[key] = value
        else:
            raise AttributeError(key)
