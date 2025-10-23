#!/bin/bash
set -e

# The python:3.11-slim container doesn't have git, which flit needs to build the package.
echo "Installing git..."
apt-get update -y && apt-get install -y git --no-install-recommends

# Ensure python dependencies are installed first
pip install requests --quiet

# Read version directly from pyproject.toml
VERSION_FROM_PYPROJECT=$(grep -E "^version\s*=\s*\"[0-9]+\.[0-9]+\.[0-9]+\"$" pyproject.toml | cut -d '"' -f 2)

if [ -z "$VERSION_FROM_PYPROJECT" ]; then
  echo "Could not find version in pyproject.toml. Exiting."
  exit 1
fi

echo "Found version $VERSION_FROM_PYPROJECT in pyproject.toml. Checking against PyPI."

cat > /tmp/check_pypi.py << EOL
import sys
import requests

package_name = 'kaggle-environments'
version_to_check = sys.argv[1]

response = requests.get(f'https://pypi.org/pypi/{package_name}/json')

if response.status_code == 200:
    data = response.json()
    if version_to_check in data.get('releases', {}):
        print('true')
    else:
        print('false')
elif response.status_code == 404:
    print('false')
else:
    print(f'Error checking PyPI: {response.status_code}', file=sys.stderr)
    sys.exit(1)
EOL

VERSION_EXISTS=$(python3 /tmp/check_pypi.py "$VERSION_FROM_PYPROJECT")

if [ "$VERSION_EXISTS" = "true" ]; then
  echo "Version $VERSION_FROM_PYPROJECT already exists on PyPI. Skipping publish."
else
  echo "Version $VERSION_FROM_PYPROJECT not found on PyPI. Publishing..."
  pip install flit --quiet
  export FLIT_USERNAME=__token__
  # PYPI_TOKEN is passed as an environment variable from cloudbuild
  export FLIT_PASSWORD=$PYPI_TOKEN
  flit publish
fi
