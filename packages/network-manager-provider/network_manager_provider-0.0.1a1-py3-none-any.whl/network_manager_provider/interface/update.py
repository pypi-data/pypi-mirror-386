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


integer_options = [
    "mtu",
    "txqlen",
    "vlan",
    "vf",
    "vlan_id",
    "ipip_ttl",
    "index",
    "IFLA_MTU",
    "cost",
    "index",
    "master",
]


async def update(name_or_index, update_kwargs=None):
    if not update_kwargs:
        update_kwargs = {}

    if isinstance(name_or_index, int):
        update_kwargs["index"] = name_or_index
    elif isinstance(name_or_index, str):
        update_kwargs["ifname"] = name_or_index
    else:
        return False, {"msg": "name_or_index must be a string or integer"}

    for option in integer_options:
        if option in update_kwargs:
            update_kwargs[option] = int(update_kwargs[option])

    pyroute_action = ["set"]
    response = {}
    async with AsyncIPRoute() as ipr:
        success, msg = await execute_ndb_function(
            ipr, "link", *pyroute_action, **update_kwargs
        )
        if not success:
            response["msg"] = f"Failed to update link, err: {msg}"
            return False, response
        response["msg"] = f"Updated link: {name_or_index}"
        return True, response
    return False, response
