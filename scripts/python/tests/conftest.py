import os
import sys
import logging
import pytest


sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

LOGGER = logging.getLogger(__name__)

pytest_plugins = ["fixtures.parsing_fixtures",
                  "fixtures.config_fixtures",
                  "fixtures.ostore_fixtures"]

testSession = None
