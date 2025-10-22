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

import asyncio
import re
from pyroute2 import AsyncIPRoute
from network_manager_provider.route.delete import delete


async def flush(to_regex, via=None, flush_kwargs=None):
    if not flush_kwargs:
        flush_kwargs = {}

    delete_actions = []
    async with AsyncIPRoute() as ipr:
        async for route in await ipr.get_routes():
            route_dst = route.get_attr("RTA_DST")
            route_dst_len = route.get("dst_len")
            route_via = route.get_attr("RTA_GATEWAY")

            if not route_dst:
                continue

            if route_dst_len:
                existing_route_to = f"{route_dst}/{route_dst_len}"
            else:
                existing_route_to = route_dst

            if re.match(to_regex, existing_route_to):
                delete_actions.append(
                    delete(
                        existing_route_to,
                        route_via,
                        delete_kwargs=flush_kwargs,
                    )
                )

    response = {"results": []}
    for success, delete_response in await asyncio.gather(*delete_actions):
        response["results"].append(delete_response)
    return True, response
