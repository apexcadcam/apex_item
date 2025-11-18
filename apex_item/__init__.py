__version__ = "1.0.0"

# Import required modules at the top level
from pathlib import Path
import sys
import importlib.util

# Run setup hook immediately when module is imported
try:
	# Find setup_hook.py in the app root (apps/apex_item/)
	app_root = Path(__file__).parent.parent.parent
	setup_hook = app_root / "setup_hook.py"
	
	if setup_hook.exists():
		# Import and run the hook
		sys.path.insert(0, str(app_root))
		from setup_hook import ensure_app_in_apps_txt
		ensure_app_in_apps_txt()
		sys.path.pop(0)
except Exception:
	# Silently fail - this is a helper function
	pass

# Import key modules that Frappe needs
# This ensures apex_item.hooks, apex_item.install, etc. are available
# The modules are in the same directory as this __init__.py
# IMPORTANT: Register modules in sys.modules BEFORE loading to prevent import errors
_package_dir = Path(__file__).parent
_modules_to_import = ['hooks', 'install', 'item_price_hooks', 'item_price_config', 'api']

# Pre-register module names in sys.modules to prevent import errors
import types
for module_name in _modules_to_import:
	module_path = _package_dir / f"{module_name}.py"
	if module_path.exists():
		module_full_name = f"apex_item.{module_name}"
		try:
			spec = importlib.util.spec_from_file_location(
				module_full_name,
				module_path
			)
			if spec and spec.loader:
				module = importlib.util.module_from_spec(spec)
				# Register in sys.modules immediately
				sys.modules[module_full_name] = module
				# Load the module
				spec.loader.exec_module(module)
				# Make it available as an attribute of this module
				setattr(sys.modules[__name__], module_name, module)
		except Exception:
			# Silently fail if module can't be loaded
			pass

