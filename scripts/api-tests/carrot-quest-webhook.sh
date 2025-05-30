#!/bin/bash

# Default values
# Use WEBHOOK_HOST if set, otherwise default to localhost:8220
if [ -z "$WEBHOOK_HOST" ]; then
    # WEBHOOK_HOST="http://localhost:8220"
    WEBHOOK_HOST="https://rorotools.com"
fi
HOST="$WEBHOOK_HOST"

# Get token from .env if not provided
if [ -z "$WEBHOOK_TOKEN" ]; then
    # Try to extract from .env file
    WEBHOOK_TOKEN=$(grep CARROT_QUEST_WEBHOOK_TOKEN .env | cut -d '"' -f 2)
    if [ -z "$WEBHOOK_TOKEN" ]; then
        WEBHOOK_TOKEN="service-token"  # Default from .env
    fi
fi

# Send the webhook request exactly as in the example
echo "Sending webhook to $HOST/webhook/carrot-quest/conversations"
curl -X POST "${HOST}/webhook/carrot-quest/conversations" \
  -H "User-Agent: Carrotquest Webhook 1.0" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "conversation={
\"direction\": \"u2a\",
\"conversation_closed\": false,
\"conversation_tags\": [],
\"type\": \"reply_user\",
\"id\": 78183798,
\"body\": \"ewfwfwef\",
\"assignee\": {
\"type\": \"admin\",
\"name\": \"inkov\",
\"avatar\": \"https://files.carrotquest.io/avatars/default-v2.png\",
\"id\": 111},
\"sent_via\": \"web_user\",
\"created\": 1492604036,
\"random_id\": \"132466821\",
\"conversation\": 64558819,
\"from\": 85648207
}" \
  -d "type=conversation" \
  -d "token=$WEBHOOK_TOKEN" \
  -d "user_id=85648207" \
  -d "user={\"id\": 85648207, \"user_id\": \"85648207\", \"props_custom\": {}}" \
  -v
