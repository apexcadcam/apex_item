"""
Apex Item App
This __init__.py allows the app to be imported as 'apex_item'
The actual package structure is: apex_item/apex_item/ with hooks.py, install.py, etc. at apex_item/apex_item/
"""

# Make modules from apex_item/apex_item/ accessible as apex_item.*
# Frappe expects: apex_item.hooks, apex_item.install, etc.

import sys
import importlib.util
from pathlib import Path

# Get the app directory and the package directory
_app_dir = Path(__file__).parent
_package_dir = _app_dir / "apex_item"

# Import modules directly from the package directory
# The structure is: apps/apex_item/apex_item/hooks.py
# We need to make apex_item.hooks importable

_modules_to_import = ['hooks', 'install', 'item_price_hooks', 'item_price_config', 'api']

for module_name in _modules_to_import:
    module_path = _package_dir / f"{module_name}.py"
    if module_path.exists():
        try:
            spec = importlib.util.spec_from_file_location(
                f"apex_item.{module_name}",
                module_path
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[f"apex_item.{module_name}"] = module
                spec.loader.exec_module(module)
                # Also make it available as an attribute of this module
                setattr(sys.modules[__name__], module_name, module)
        except Exception:
            # Silently fail if module can't be loaded
            pass
