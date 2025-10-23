#   Copyright 2025 Red Hat, Inc.
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
Websocket proxy that is compatible with OpenStack Ironic
noVNC consoles. Leverages websockify.py by Joel Martin
"""

import sys

from oslo_config import cfg
from oslo_log import log
import oslo_middleware.cors as cors_middleware

from ironic.common import exception
from ironic.common import service as ironic_service
from ironic.console import novncproxy_service


CONF = cfg.CONF

LOG = log.getLogger(__name__)


def main():

    # register [cors] config options
    cors_middleware.CORS(None, CONF)

    # Parse config file and command line options, then start logging
    ironic_service.prepare_service('ironic_vncproxy', sys.argv)

    if not CONF.vnc.enabled:
        raise exception.ConfigInvalid("To allow this service to start, set "
                                      "[vnc]enabled = True")

    # Build and start the websocket proxy
    launcher = ironic_service.process_launcher()
    server = novncproxy_service.NoVNCProxyService()
    launcher.launch_service(server)
    sys.exit(launcher.wait())


if __name__ == '__main__':
    sys.exit(main())
