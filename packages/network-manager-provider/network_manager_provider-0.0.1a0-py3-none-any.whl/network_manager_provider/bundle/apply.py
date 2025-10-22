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
from pyroute2 import AsyncIPRoute
from network_manager_provider.defaults import BUNDLE
from network_manager_provider.helpers.pyroute2 import execute_ndb_function
from network_manager_provider.storage.dictdatabase import DictDatabase
from network_manager_provider.interface.create import create as create_interface
from network_manager_provider.interface.read import read
from network_manager_provider.interface.update import update as update_interface
from network_manager_provider.route.create import create as create_route
from network_manager_provider.namespace.create import create as create_namespace


async def provision_link(name, settings):
    interface_type = settings.get("type", None)
    if not interface_type:
        return False, {
            "msg": "The interface 'type' is required on interface: {}.".format(name)
        }
    found, _ = await read(name, interface_type)
    if found:
        return False, {
            "msg": "An interface with the name: {} already exists.".format(name)
        }
    return await create_interface(name, interface_type, create_kwargs=settings)


async def provision_links(links):
    interface_tasks = [
        provision_link(name, settings) for name, settings in links.items()
    ]
    results = await asyncio.gather(*interface_tasks)
    successes = [response for success, response in results if success]
    failures = [response for success, response in results if not success]
    return successes, failures


async def assign_link_to_bridge(link_name, bridge_name):
    found, _ = await read(link_name, read_args=["index"])
    if not found:
        return False, {"msg": f"Link: {link_name} does not exist."}
    found, bridge = await read(bridge_name, read_args=["index"])
    if not found:
        return False, {"msg": f"Bridge: {bridge_name} does not exist."}

    if "link" not in bridge:
        return False, {"msg": f"Failed to get link details for bridge: {bridge}"}

    if "index" not in bridge["link"]:
        return False, {"msg": f"Failed to get index for bridge: {bridge}"}

    update_kwargs = {"master": bridge["link"]["index"]}
    return await update_interface(link_name, update_kwargs=update_kwargs)


async def assign_links_to_bridge(links, bridge_name):
    interface_tasks = [assign_link_to_bridge(name, bridge_name) for name in links]
    results = await asyncio.gather(*interface_tasks)
    successes = [response for success, response in results if success]
    failures = [response for success, response in results if not success]
    return successes, failures


async def provision_route(to, via, **kwargs):
    return await create_route(to, via, create_kwargs=kwargs)


async def provision_routes(routes):
    provision_routes_tasks = [
        provision_route(route.pop("to"), route.pop("via"), **route) for route in routes
    ]
    provision_routes_results = await asyncio.gather(*provision_routes_tasks)
    successes = [response for success, response in provision_routes_results if success]
    failures = [
        response for success, response in provision_routes_results if not success
    ]
    return successes, failures


async def provision_namespace(name, settings):
    interfaces = settings.get("interfaces", {})
    regular_interfaces = {
        name: settings
        for name, settings in interfaces.items()
        if settings.get("type") != "veth"
    }

    peer_interfaces = {
        name: settings
        for name, settings in interfaces.items()
        if settings.get("type") == "veth" and settings.get("peer", None)
    }

    namespace_successes, namespace_failures = [], []
    create_namespace_success, create_namespace_response = await create_namespace(name)
    if not create_namespace_success:
        namespace_failures.append(create_namespace_response)
        return namespace_successes, namespace_failures
    namespace_successes.append(create_namespace_response)

    interfaces_success, interfaces_failures = await provision_links(regular_interfaces)
    namespace_successes.extend(interfaces_success)
    namespace_failures.extend(interfaces_failures)

    # Move interface to namespace
    # TODO, unify with the existing interface module
    async with AsyncIPRoute() as ipr:
        for peer_name, _ in peer_interfaces.items():
            # Move to namespace
            peer_indices = await ipr.link_lookup(ifname=peer_name)
            success, msg = await execute_ndb_function(
                ipr, "link", "set", index=peer_indices[0], net_ns_fd=name
            )
            if not success:
                namespace_failures.append(
                    {
                        "msg": f"Failed to move interface: {peer_name} to namespace: {name}, err: {msg}"
                    }
                )
            namespace_successes.append(
                {"msg": f"Moved interface: {peer_name} to namespace: {name}"}
            )

    # routes = settings.get("routes", [])
    # routes_success, routes_failures = await provision_routes(routes)
    return namespace_successes, namespace_failures


async def provision_namespaces(namespaces):
    provision_namespace_tasks = [
        provision_namespace(name, settings) for name, settings in namespaces.items()
    ]
    provision_successes, provision_failures = zip(
        *await asyncio.gather(*provision_namespace_tasks)
    )
    provision_successes = [success for success in provision_successes if success]
    provision_failures = [failure for failure in provision_failures if failure]
    return provision_successes, provision_failures


async def apply(bundle_id, directory=None):
    response = {}

    bundle_db = DictDatabase(BUNDLE, directory=directory)
    if not await bundle_db.exists():
        if not await bundle_db.touch():
            response["msg"] = (
                "The Bundle database: {} did not exist in directory: {}, and it could not be created.".format(
                    bundle_db.name, directory
                )
            )
            return False, response

    bundle = await bundle_db.get(bundle_id)
    if not bundle:
        response["msg"] = (
            "Failed to find a Bundle inside the database with name: {} to update.".format(
                bundle_id
            )
        )
        return False, response

    # Interfaces
    interfaces = bundle["config"].get("interfaces", {})
    interface_success, interface_failures = await provision_links(interfaces)
    response["interfaces"] = {
        "successes": interface_success,
        "failures": interface_failures,
    }

    # Bridges
    bridges = bundle["config"].get("bridges", {})
    bridge_success, bridge_failures = await provision_links(bridges)
    response["bridges"] = {"successes": bridge_success, "failures": bridge_failures}

    # Assign links to bridges
    bridge_links = {
        bridge_name: bridge_settings.get("interfaces", [])
        for bridge_name, bridge_settings in bridges.items()
        if bridge_settings.get("interfaces", [])
    }

    for bridge_name, links in bridge_links.items():
        assign_success, assign_failures = await assign_links_to_bridge(
            links, bridge_name
        )
        response["bridges"][bridge_name] = {
            "assign_successes": assign_success,
            "assign_failures": assign_failures,
        }

    # Namespaces
    namespaces = bundle["config"].get("namespaces", {})
    namespace_successes, namespace_failures = await provision_namespaces(namespaces)

    response["id"] = bundle_id
    response["namespaces"] = {
        "successes": namespace_successes,
        "failures": namespace_failures,
    }

    if bridge_failures or interface_failures or namespace_failures:
        return False, response
    return True, response
