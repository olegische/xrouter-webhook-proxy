#!/bin/bash

read_first_line_of_file() {
  local file="$1"
  if [ -e "$file" ]; then
    read -r line < "$file"
    echo "$line"
  else
    echo "File $file does not exist."
    exit 1
  fi
}

# Load environment variables
set -a
source .env
set +a

# Read secrets
remote_host=$(read_first_line_of_file "secrets/.ssh-host")
ssh_key_path=$(read_first_line_of_file "secrets/.ssh-privkey-path")
docker_token=$(read_first_line_of_file "secrets/.docker-oauth-token")
docker_username=$(read_first_line_of_file "secrets/.docker-login-username")

echo "Deploying to $remote_host..."

# First set proper permissions to allow copying
ssh -t -t -i "$ssh_key_path" "$remote_host" << EOF
    # Temporarily set more permissive permissions for copying
    sudo chown -R root:docker /opt/xrouter-webhook-proxy
    sudo chmod -R 770 /opt/xrouter-webhook-proxy
EOF

# Copy files to remote host
echo "Copying files to remote host..."
scp -i "$ssh_key_path" docker-compose.prod.yml .env.prod "$remote_host:/opt/xrouter-webhook-proxy/"

# Then execute deployment commands
ssh -t -t -i "$ssh_key_path" "$remote_host" << EOF
    cd /opt/xrouter-webhook-proxy

    # Load environment variables
    set -a
    source .env.prod
    set +a

    # Login to Yandex Container Registry
    echo "$docker_token" | docker login --username "$docker_username" --password-stdin cr.yandex

    # Pull latest images
    echo "Pulling latest images..."
    docker compose -f docker-compose.prod.yml pull

    # Logout from registry
    docker logout cr.yandex

    # Set final permissions
    sudo chown -R root:docker /opt/xrouter-webhook-proxy
    sudo chmod -R 660 /opt/xrouter-webhook-proxy
    # Ensure execute permission on directories
    sudo find /opt/xrouter-webhook-proxy -type d -exec chmod 770 {} \;

    # Stop and remove existing containers
    echo "Stopping existing containers..."
    docker compose -f docker-compose.prod.yml down

    # Start containers
    echo "Starting containers..."
    docker compose -f docker-compose.prod.yml up -d

    # Show running containers
    echo "Current running containers:"
    docker ps
EOF

echo "Deployment completed!"
