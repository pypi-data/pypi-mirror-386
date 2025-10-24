#!/bin/bash
set -e

# The python:3.11-slim container doesn't have git, which flit needs to build the package.
echo "Installing git..."
apt-get update -y && apt-get install -y git --no-install-recommends

# Ensure python dependencies are installed first
pip install requests --quiet

# Read version directly from pyproject.toml
PACKAGE_NAME="kaggle-environments" # Define package name for reuse
VERSION_FROM_PYPROJECT=$(grep -E "^version\s*=\s*\"[0-9]+\.[0-9]+\.[0-9]+\"$" pyproject.toml | cut -d '"' -f 2)
CLOUD_RUN_REQS_PATH="docker/cloud-run-source/requirements.txt"

if [ -z "$VERSION_FROM_PYPROJECT" ]; then
  echo "❌ Could not find version in pyproject.toml. Exiting."
  exit 1
fi

echo "Found version $VERSION_FROM_PYPROJECT in pyproject.toml. Checking against PyPI."

# (Your Python script to check for existing version remains the same)
cat > /tmp/check_pypi.py << EOL
import sys
import requests
package_name = '$PACKAGE_NAME'
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
  echo "⏩ Version $VERSION_FROM_PYPROJECT already exists on PyPI. Skipping publish."
else
  echo "🚀 Version $VERSION_FROM_PYPROJECT not found on PyPI. Publishing..."
  pip install flit --quiet
  export FLIT_USERNAME=__token__
  export FLIT_PASSWORD=$PYPI_TOKEN

  flit publish
  
  # --- RETRY LOGIC START ---
  echo "Verifying that package '$PACKAGE_NAME==$VERSION_FROM_PYPROJECT' is available from PyPI..."
  MAX_RETRIES=10
  RETRY_DELAY_SECONDS=30
  SUCCESS=false

  for i in $(seq 1 $MAX_RETRIES)
  do
    # Use 'pip install' with --no-cache-dir as the check. This is the most reliable method.
    if python -m pip install --no-cache-dir "$PACKAGE_NAME==$VERSION_FROM_PYPROJECT" --quiet; then
      echo "✅ Successfully found and installed package from PyPI."
      SUCCESS=true
      break
    else
      echo "Attempt $i/$MAX_RETRIES: Package not yet available. Waiting ${RETRY_DELAY_SECONDS}s..."
      sleep $RETRY_DELAY_SECONDS
    fi
  done

  if [ "$SUCCESS" != "true" ]; then
    echo "❌ Failed to find package on PyPI after $MAX_RETRIES attempts. Aborting."
    exit 1
  fi
  # --- RETRY LOGIC END ---

  echo "Successfully published and verified. Updating Cloud Run requirements at $CLOUD_RUN_REQS_PATH..."
  
  # Use sed to replace the placeholder with the actual version
  sed -i "s/VERSION_FROM_CICD_DEPLOY/${VERSION_FROM_PYPROJECT}/" "$CLOUD_RUN_REQS_PATH"
  
  echo "Cloud Run requirements.txt updated."

  # Create a flag file to signal success
  echo "true" > /workspace/published_new_version.flag
fi
