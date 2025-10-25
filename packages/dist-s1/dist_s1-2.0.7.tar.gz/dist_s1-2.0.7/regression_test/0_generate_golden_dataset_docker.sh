#!/bin/bash

# Script to generate golden dataset using Docker on M1 Mac
# Uses the pre-built image from GitHub Container Registry
# Run this script from the regression_test directory

set -e  # Exit on any error

# Configuration
DOCKER_IMAGE_NAME="ghcr.io/opera-adt/dist-s1:latest"
CONTAINER_WORK_DIR="/home/ops/dist-s1-data"

echo "Pulling latest Docker image from GitHub Container Registry..."
docker pull "${DOCKER_IMAGE_NAME}"

echo "Docker image pulled successfully: ${DOCKER_IMAGE_NAME}"

# Check if ~/.netrc exists
if [ ! -f ~/.netrc ]; then
    echo "Error: ~/.netrc file not found. Please create it with your earthdata credentials:"
    echo "machine urs.earthdata.nasa.gov"
    echo "    login <username>"
    echo "    password <password>"
    exit 1
fi

# Extract credentials from .netrc as backup
EARTHDATA_USERNAME=$(grep -A2 "machine urs.earthdata.nasa.gov" ~/.netrc | grep "login" | awk '{print $2}')
EARTHDATA_PASSWORD=$(grep -A2 "machine urs.earthdata.nasa.gov" ~/.netrc | grep "password" | awk '{print $2}')

if [ -z "$EARTHDATA_USERNAME" ] || [ -z "$EARTHDATA_PASSWORD" ]; then
    echo "Warning: Could not extract credentials from .netrc. Make sure it's properly formatted."
fi

# Clean up any existing output directories to avoid permission issues
echo "Cleaning up existing output directories..."
rm -rf product_0 golden_dataset out_0 out_1

echo "Running golden dataset generation in Docker container..."
echo "Working directory: $(pwd)"
echo "Container work directory: ${CONTAINER_WORK_DIR}"

# Run the container with:
# - Current directory (regression_test) mounted to container work directory
# - ~/.netrc file mounted for authentication
# - Interactive terminal
# - Remove container after completion
# - Override entrypoint to run python script directly
# - Platform specification for M1 Mac compatibility
# - Run as current user to avoid permission issues
docker run -ti --rm \
    --platform linux/amd64 \
    --user "$(id -u):$(id -g)" \
    -e EARTHDATA_USERNAME="${EARTHDATA_USERNAME}" \
    -e EARTHDATA_PASSWORD="${EARTHDATA_PASSWORD}" \
    -v "$(pwd)":"${CONTAINER_WORK_DIR}" \
    -v ~/.netrc:/.netrc:ro \
    --entrypoint "/bin/bash" \
    "${DOCKER_IMAGE_NAME}" \
    -l -c "source /opt/conda/etc/profile.d/conda.sh && conda activate dist-s1-env && cd ${CONTAINER_WORK_DIR} && python 0_generate_golden_dataset.py"

echo "Golden dataset generation completed!"
echo "Check the current directory for outputs:"
echo "- product_0/ (initial product)"
echo "- golden_dataset/ (final golden dataset)"
echo "- out_0/ and out_1/ (intermediate processing outputs)"