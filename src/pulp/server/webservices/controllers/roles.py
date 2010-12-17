# -*- coding: utf-8 -*-

# Copyright © 2010 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#
# Red Hat trademarks are not licensed under GPLv2. No permission is
# granted to use or replicate Red Hat trademarks that are incorporated
# in this software or its documentation.

from gettext import gettext as _

import web

from pulp.server.api.role import RoleAPI
from pulp.server.auth import authorization
from pulp.server.webservices.controllers.base import JSONController


_role_api = RoleAPI()

# roles collection controller -------------------------------------------------

class Roles(JSONController):

    @JSONController.error_handler
    @JSONController.auth_required(super_user_only=True)
    def GET(self):
        roles = [r['name'] for r in _role_api.roles(fields=['name'])]
        return self.ok(roles)

    @JSONController.error_handler
    @JSONController.auth_required(super_user_only=True)
    def POST(self):
        try:
            role_name = self.params()['rolename']
        except KeyError:
            msg = _('expected parameters: rolename')
            return self.bad_request(msg)
        try:
            role = authorization.create_role(role_name)
            return self.ok(role)
        except authorization.PulpAuthorizationError, e:
            return self.bad_request(e.args[0])

    PUT = POST

# individual role controller --------------------------------------------------

class Role(JSONController):

    @JSONController.error_handler
    @JSONController.auth_required(super_user_only=True)
    def GET(self, role_name):
        role = _role_api.role(role_name)
        if role is None:
            return self.not_found(_('no such role: %s') % role_name)
        # XXX should this be in a deferred field?
        role['users'] = [u['login'] for u in
                         authorization._get_users_belonging_to_role(role)]
        return self.ok(role)

    @JSONController.error_handler
    @JSONController.auth_required(super_user_only=True)
    def DELETE(self, role_name):
        role = _role_api.role(role_name)
        if role is None:
            return self.not_found(_('no such role: %s') % role_name)
        val = authorization.delete_role(role_name)
        return self.ok(val)

# role actions controller -----------------------------------------------------

class RoleActions(JSONController):

    exposed_actions = (
        'add',
        'remove',
    )

    def add(self, role_name):
        try:
            user_name = self.params()['username']
        except KeyError:
            msg = _('expected parameter: username')
            return self.bad_request(msg)
        try:
            val = authorization.add_user_to_role(role_name, user_name)
        except authorization.PulpAuthorizationError, e:
            return self.bad_request(e.args[0])
        else:
            return self.ok(val)

    def remove(self, role_name):
        try:
            user_name = self.params()['username']
        except KeyError:
            msg = _('expected parameter: username')
            return self.bad_request(msg)
        try:
            val = authorization.remove_user_from_role(role_name, user_name)
        except authorization.PulpAuthorizationError, e:
            return self.bad_request(e.args[0])
        else:
            return self.ok(val)

    @JSONController.error_handler
    @JSONController.auth_required(super_user_only=True)
    def POST(self, role_name, action_name):
        role = _role_api.role(role_name)
        if role is None:
            return self.not_found(_('no such role: %s') % role_name)
        action = getattr(self, action_name, None)
        if action is None:
            msg = _('no implementation for %s found')
            return self.internal_server_error(msg % action_name)
        return action(role_name)

# web.py application ----------------------------------------------------------

urls = (
    '/$', 'Roles',
    '/([^/]+)/$', 'Role',
    '/([^/]+)/(%s)/$' % '|'.join(RoleActions.exposed_actions), 'RoleActions',
)

application = web.application(urls, globals())
