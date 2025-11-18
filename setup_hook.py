#!/usr/bin/env python3
"""
Post-install hook to ensure apex_item is in sites/apps.txt
This script runs automatically after pip install -e
"""

from pathlib import Path

def ensure_app_in_apps_txt():
	"""Ensure apex_item is listed in sites/apps.txt - required for bench build."""
	try:
		# Find bench root (go up from apps/apex_item/)
		current_dir = Path(__file__).parent.parent
		apps_txt_path = current_dir / "sites" / "apps.txt"
		
		if not apps_txt_path.exists():
			apps_txt_path.parent.mkdir(parents=True, exist_ok=True)
		
		# Read current apps.txt
		apps = []
		if apps_txt_path.exists():
			with open(apps_txt_path, "r", encoding="utf-8") as f:
				apps = [line.strip() for line in f.readlines() if line.strip()]
		
		# Add apex_item if not present
		if "apex_item" not in apps:
			apps.append("apex_item")
			with open(apps_txt_path, "w", encoding="utf-8") as f:
				f.write("\n".join(apps) + "\n")
			print("✅ Added apex_item to sites/apps.txt")
	except Exception as e:
		# Silently fail - this is a helper function
		pass

if __name__ == "__main__":
	ensure_app_in_apps_txt()

