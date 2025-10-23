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

"""This will be used to configure dataretriever used for cadip"""

import os
import os.path as osp
from functools import lru_cache
from pathlib import Path

from rs_server_common.authentication.authentication_to_external import (
    load_external_auth_config,
)
from rs_server_common.data_retrieval.eodag_provider import EodagProvider
from rs_server_common.data_retrieval.provider import CreateProviderFailed
from rs_server_common.settings import env_bool

if env_bool("RSPY_USE_MODULE_FOR_STATION_TOKEN", default=False):
    DEFAULT_EODAG_CONFIG = (
        Path(osp.realpath(osp.dirname(__file__))).parent / "config" / "cadip_ws_config_token_module.yaml"
    )
else:
    DEFAULT_EODAG_CONFIG = Path(osp.realpath(osp.dirname(__file__))).parent / "config" / "cadip_ws_config.yaml"


@lru_cache
def init_cadip_provider(station: str) -> EodagProvider:
    """Initialize the cadip provider for the given station.

    It initializes an eodag provider for the given station.
    The EODAG configuration file is read from the path given in the EODAG_CADIP_CONFIG var env if set.
    It is read from the path config/cadip_ws_config.yaml otherwise.

    If the station is unknown or if the cadip station configuration reading fails,
    a specific exception is raised to inform the caller of the issue.

    Args:
        station: the station to interact with: ns, mps, mti, nsg, sgs, cadip(?)

    Returns:
        the EodagProvider initialized
    """
    station = station.lower()
    try:
        # Get the cadip_ws_config.yaml file path for eodag.
        # Check if the config file path is overriden in the environment variables
        eodag_config = Path(os.environ.get("EODAG_CADIP_CONFIG", DEFAULT_EODAG_CONFIG))

        # Read the station authentication from rs-server.yaml file or RSPY__TOKEN__xxx env vars
        ext_auth_config = load_external_auth_config(station, "cadip")

        # default to eodag, stations may be ins, mps, mti, nsg, sgs, cadip(?)
        return EodagProvider(ext_auth_config, eodag_config, station)

    except Exception as exception:
        raise CreateProviderFailed(f"Failed to setup eodag for CADIP station {station}") from exception
