# Copyright 2021 Vincent Texier <vit@free.fr>
#
# This software is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import sys
from collections import OrderedDict
from pathlib import Path

# Path constants
DATA_PATH = Path("~/.config/tikka")

# Standalone executable install
if getattr(sys, "frozen", False):
    PACKAGE_PATH = Path(sys.executable).parent
# Python package install
else:
    PACKAGE_PATH = Path(__file__).parents[2]

LOCALES_PATH = PACKAGE_PATH.joinpath("locales")
CONFIG_FILENAME = "config.json"
CURRENCIES_FILENAME = "currencies.yaml"
DATABASE_FILE_EXTENSION = ".sqlite3"
DATABASE_MIGRATIONS_PATH = PACKAGE_PATH.joinpath(
    "adapters/repository/database/assets/migrations"
)

# Constants
LANGUAGES = OrderedDict([("en_US", "English"), ("fr_FR", "Français")])
MNEMONIC_LANGUAGES = {"en_US": "english", "fr_FR": "french"}
MNEMONIC_WORDS_LENGTH = 12
ACCESS_TYPE_MNEMONIC = "mnemonic"
ACCESS_TYPE_CLASSIC = "classic"
WALLETS_PASSWORD_LENGTH = 6
WALLETS_NONCE_SIZE = 12
PASSWORDS_NONCE_SIZE = 12
AMOUNT_UNIT_KEY = "unit"

# default derivation path
DERIVATION_PATH_TRANSPARENT_DEFAULT = "//2"
DERIVATION_PATH_OPAQUE_DEFAULT = "//1"
DERIVATION_PATH_MEMBER = "//0"
DERIVATION_SCAN_MAX_NUMBER = 50

# preferences keys
NODES_CURRENT_ENTRY_POINT_URL_PREFERENCES_KEY = "nodes_current_entry_point_url"
INDEXERS_CURRENT_ENTRY_POINT_URL_PREFERENCES_KEY = "indexers_current_entry_point_url"

# servers
SMITH_NODE_URL = "ws://localhost:9944"
