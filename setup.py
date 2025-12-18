from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# Filter out empty lines and comments
install_requires = [req.strip() for req in install_requires if req.strip() and not req.strip().startswith("#")]

import os
import re

# get version from __version__ variable in apex_item/__init__.py
version_file = os.path.join(os.path.dirname(__file__), "apex_item", "__init__.py")
with open(version_file, "r") as f:
    version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', f.read())
    if version_match:
        version = version_match.group(1)
    else:
        version = "0.0.1"

setup(
	name="apex_item",
	version=version,
	description="Item pricing tools",
	author="Gaber",
	author_email="gaber@example.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)


