"""
Apex Item App
This __init__.py allows the app to be imported as 'apex_item'
The actual package structure is: apex_item/apex_item/ with hooks.py, install.py, etc. at apex_item/apex_item/
"""

# Make modules from apex_item/apex_item/ accessible as apex_item.*
# Frappe expects: apex_item.hooks, apex_item.install, etc.

import sys
from pathlib import Path

# Get the app directory and the package directory
_app_dir = Path(__file__).parent
_package_dir = _app_dir / "apex_item"

# Add package directory to Python path if not already there
if str(_package_dir) not in sys.path:
    sys.path.insert(0, str(_package_dir))

# Import key modules that Frappe needs
# These are at apex_item/apex_item/hooks.py, etc.
try:
    from apex_item import hooks
    sys.modules["apex_item.hooks"] = hooks
except ImportError:
    pass

try:
    from apex_item import install
    sys.modules["apex_item.install"] = install
except ImportError:
    pass

try:
    from apex_item import item_price_hooks
    sys.modules["apex_item.item_price_hooks"] = item_price_hooks
except ImportError:
    pass

try:
    from apex_item import item_price_config
    sys.modules["apex_item.item_price_config"] = item_price_config
except ImportError:
    pass

try:
    from apex_item import api
    sys.modules["apex_item.api"] = api
except ImportError:
    pass

