# Copyright 2024 CS Group
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Init the FastAPI application."""

import warnings

# Import the database table modules before initializing the FastAPI,
# that will init the database session and create the tables.
# pylint: disable=unused-import, import-outside-toplevel
# flake8: noqa
from rs_server_adgs import __version__
from rs_server_adgs.api.adgs_search import MockPgstacAdgs
from rs_server_adgs.fastapi.adgs_routers import adgs_routers
from rs_server_common.fastapi_app import init_app
from rs_server_common.utils.error_handlers import register_stac_exception_handlers

# Used to supress stac_pydantic userwarnings related to serialization
warnings.filterwarnings("ignore", category=UserWarning, module="stac_pydantic")

# Init the FastAPI application with the adgs routers.
app = init_app(__version__, adgs_routers, router_prefix="/auxip")

# Set properties for the adgs service
app.state.get_connection = MockPgstacAdgs.get_connection
app.state.readpool = MockPgstacAdgs.readpool()

register_stac_exception_handlers(app)
