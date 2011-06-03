# -*- coding: utf-8 -*-

# Copyright © 2010 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

import os

from pulp.client.cli.base import PulpCLI
from pulp.client.credentials import Consumer
from pulp.client.core.utils import system_exit
from pulp.client import server
from pulp.client.config import Config

_cfg = Config()

class ClientCLI(PulpCLI):

    def setup_credentials(self):
        """
        User the super-class credentials then fallback to the consumer
        credentials if present.
        """
        super(ClientCLI, self).setup_credentials()
        if self._server.has_credentials_set():
            return
        consumer = Consumer()
        certfile = consumer.crtpath()
        if os.access(certfile, os.R_OK):
            self._server.set_ssl_credentials(certfile)
        elif None not in (self.opts.username, self.opts.password):
            self._server.set_basic_auth_credentials(self.opts.username, self.opts.password)
            
    def setup_server(self):
        """
        Setup the active server connection.
        """
        host = _cfg.server.host or 'localhost.localdomain'
        port = _cfg.server.port or '443'
        scheme = _cfg.server.scheme or 'https'
        path = _cfg.server.path or '/pulp/api'
        #print >> sys.stderr, 'server information: %s, %s, %s, %s' % \
        #        (host, port, scheme, path)
        self._server = server.PulpServer(host, int(port), scheme, path)
        server.set_active_server(self._server)