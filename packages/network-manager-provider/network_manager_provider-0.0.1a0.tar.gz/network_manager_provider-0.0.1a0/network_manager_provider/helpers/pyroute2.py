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
import inspect


async def execute_ndb_function(ndb_object, nbd_func_name, *args, **kwargs):
    ndb_func = getattr(ndb_object, nbd_func_name)
    try:
        if inspect.iscoroutinefunction(ndb_func):
            return_code = await ndb_func(*args, **kwargs)
        else:
            return_code = ndb_func(*args, **kwargs)
        return True, return_code
    except Exception as err:
        return False, str(err)
    return False, "Failed to execute function: {}, unknown error".format(nbd_func_name)
