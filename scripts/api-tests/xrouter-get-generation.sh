#!/bin/bash

# Default values
# HOST=${HOST:-"https://ai.xrouter.chat"}
HOST=${HOST:-"http://localhost:8400"}

# Check for required token
if [ -z "$USER_TOKEN" ]; then
    echo "Error: USER_TOKEN environment variable is required"
    exit 1
fi

# Default generation ID if not provided
GENERATION_ID=${GENERATION_ID:-"aa9076f7-3942-47c1-a991-ad82df6c9567"}

# Get generation details
echo "Raw response:"
# curl -X GET "${HOST}/api/v1/generation?id=${GENERATION_ID}" \
curl -X GET "${HOST}/api/v1/analytics/generation?id=${GENERATION_ID}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${USER_TOKEN}" | tee >(echo -e "\nFormatted response:"; jq '.')
