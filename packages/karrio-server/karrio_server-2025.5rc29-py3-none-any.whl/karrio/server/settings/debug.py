# type: ignore
import sys
import importlib.util
from karrio.server.settings.base import *

TESTING = sys.argv[1:2] == ["test"]

if (
    DEBUG is True
    and TESTING is False
    and importlib.util.find_spec("debug_toolbar") is not None
):
    INTERNAL_IPS = [
        "127.0.0.1",
        "0.0.0.0",
    ]
    INSTALLED_APPS += [
        "debug_toolbar",
    ]
    MIDDLEWARE.insert(0, "karrio.server.core.middleware.NonHtmlDebugToolbarMiddleware")
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
