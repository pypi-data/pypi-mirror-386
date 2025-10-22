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


async def create(name, kind, create_kwargs=None):
    if not create_kwargs:
        create_kwargs = {}

    create_kwargs["ifname"] = name
    create_kwargs["kind"] = kind

    pyroute_action = ["add"]
    response = {}
    async with AsyncIPRoute() as ipr:
        success, msg = await execute_ndb_function(
            ipr, "link", *pyroute_action, **create_kwargs
        )
        if not success:
            response["msg"] = f"Failed to add link, err: {msg}"
            return False, response
        response["msg"] = f"Added link: {name}, of type: {kind}"
        return True, response
    return False, response
