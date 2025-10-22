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

from pyroute2 import AsyncIPRoute
from network_manager_provider.helpers.pyroute2 import execute_ndb_function


DEFAULT_LINK_READ_OPTIONS = ["state", "index"]


async def read(name, read_args=None):
    read_options = {
        "ifname": name,
    }

    pyroute_action = ["get"]
    response = {}
    async with AsyncIPRoute() as ipr:
        success, msg = await execute_ndb_function(
            ipr, "link", *pyroute_action, **read_options
        )
        if not success:
            response["msg"] = f"Failed to read link, err: {msg}"
            return False, response
        response["msg"] = f"Read link: {name}"
        link = msg[0]
        response["link"] = {}
        for option in read_args or DEFAULT_LINK_READ_OPTIONS:
            if option in link:
                response["link"][option] = link[option]
            elif link.get(f"IFLA_{option}", None):
                response["link"][option] = link.get(f"IFLA_{option}")
            else:
                response["link"][option] = "Option not found"

        response["link"]["name"] = link.get("IFLA_IFNAME", None)
        return True, response
    return False, response
