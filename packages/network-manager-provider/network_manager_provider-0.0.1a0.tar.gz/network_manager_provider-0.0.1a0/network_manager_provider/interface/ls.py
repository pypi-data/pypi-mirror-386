# Copyright (C) 2024  rasmunk
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import re
from pyroute2 import AsyncIPRoute
from network_manager_provider.helpers.pyroute2 import execute_ndb_function


async def ls(regex=None, ip_route_init_kwargs=None):
    response = {}
    async with AsyncIPRoute(**(ip_route_init_kwargs or {})) as ipr:
        success, msg = await execute_ndb_function(ipr, "get_links")
        if not success:
            response["msg"] = f"Failed to list interfaces, err: {msg}"
            return False, response
        interfaces = msg
        response["interfaces"] = []

        async for interface in interfaces:
            interface_name = interface.get("IFLA_IFNAME")
            if not regex:
                response["interfaces"].append(interface_name)
            if regex and re.match(regex, interface_name):
                response["interfaces"].append(interface_name)

    if not response["interfaces"]:
        response["msg"] = "No interfaces found"
    else:
        response["msg"] = "Found interfaces"
    return True, response
