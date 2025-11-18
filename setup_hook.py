#!/usr/bin/env python3
"""
Setup hook to automatically manage apex_item in sites/apps.txt
- Adds apex_item to apps.txt during installation
- Removes apex_item from apps.txt during uninstallation
"""

from pathlib import Path
import sys


def get_bench_root():
	"""Find bench root directory by looking for sites/ directory."""
	current = Path(__file__).resolve().parent.parent
	
	# Try different possible locations
	for _ in range(5):  # Max 5 levels up
		if (current / "sites").exists() and (current / "apps").exists():
			return current
		current = current.parent
	
	# Fallback: assume we're in apps/apex_item
	return Path(__file__).resolve().parent.parent


def ensure_app_in_apps_txt():
	"""Ensure apex_item is listed in sites/apps.txt - required for bench build and install."""
	try:
		bench_root = get_bench_root()
		apps_txt_path = bench_root / "sites" / "apps.txt"
		
		# Create sites directory if it doesn't exist
		if not apps_txt_path.parent.exists():
			apps_txt_path.parent.mkdir(parents=True, exist_ok=True)
		
		# Read current apps.txt
		apps = []
		if apps_txt_path.exists():
			with open(apps_txt_path, "r", encoding="utf-8") as f:
				apps = [line.strip() for line in f.readlines() if line.strip()]
		
		# Remove any existing apex_item entries (handle duplicates)
		apps = [app for app in apps if app != "apex_item"]
		
		# Add apex_item if not present
		if "apex_item" not in apps:
			apps.append("apex_item")
			with open(apps_txt_path, "w", encoding="utf-8") as f:
				f.write("\n".join(apps) + "\n")
			print("✅ Added apex_item to sites/apps.txt")
			return True
		else:
			return False
	except Exception as e:
		# Print error but don't fail installation
		print(f"⚠️  Warning: Could not update apps.txt: {e}")
		return False


def remove_app_from_apps_txt():
	"""Remove apex_item from sites/apps.txt during uninstallation."""
	try:
		bench_root = get_bench_root()
		apps_txt_path = bench_root / "sites" / "apps.txt"
		
		if not apps_txt_path.exists():
			return False
		
		# Read current apps.txt
		with open(apps_txt_path, "r", encoding="utf-8") as f:
			apps = [line.strip() for line in f.readlines() if line.strip()]
		
		# Remove apex_item
		original_count = len(apps)
		apps = [app for app in apps if app != "apex_item"]
		
		# Write back if changed
		if len(apps) < original_count:
			with open(apps_txt_path, "w", encoding="utf-8") as f:
				f.write("\n".join(apps) + "\n")
			print("✅ Removed apex_item from sites/apps.txt")
			return True
		
		return False
	except Exception as e:
		print(f"⚠️  Warning: Could not update apps.txt: {e}")
		return False


if __name__ == "__main__":
	if len(sys.argv) > 1 and sys.argv[1] == "remove":
		remove_app_from_apps_txt()
	else:
		ensure_app_in_apps_txt()
