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

# Read secrets
remote_host=$(read_first_line_of_file "secrets/.ssh-host")
ssh_key_path=$(read_first_line_of_file "secrets/.ssh-privkey-path")

echo "Copying nginx configuration to $remote_host..."

# First, copy nginx.conf to remote server's home directory
scp -i "$ssh_key_path" configs/nginx.conf "$remote_host":~/nginx.conf

# Then execute configuration commands
ssh -t -t -i "$ssh_key_path" "$remote_host" << 'EOF'
    # Get container IPs
    WEB_CONTAINER_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' xrouter-web)
    WEBHOOK_CONTAINER_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' xrouter-webhook-proxy)

    if [ -z "$WEB_CONTAINER_IP" ]; then
        echo "Error: Could not get xrouter-web container IP"
        exit 1
    fi

    if [ -z "$WEBHOOK_CONTAINER_IP" ]; then
        echo "Error: Could not get xrouter-webhook-proxy container IP"
        exit 1
    fi

    echo "Web container IP: $WEB_CONTAINER_IP"
    echo "Webhook container IP: $WEBHOOK_CONTAINER_IP"

    # Replace proxy_pass with container IPs
    sed -i "s|http://xrouter-web:3000|http://$WEB_CONTAINER_IP:3000|g" nginx.conf
    sed -i "s|http://xrouter-webhook-proxy:8000|http://$WEBHOOK_CONTAINER_IP:8000|g" nginx.conf

    # Deploy updated configuration
    sudo cp nginx.conf /etc/nginx/sites-available/xrouter-web && \
    sudo ln -sf /etc/nginx/sites-available/xrouter-web /etc/nginx/sites-enabled/ && \
    sudo rm -f /etc/nginx/sites-enabled/default && \
    sudo nginx -t && \
    sudo systemctl restart nginx
EOF

echo "Nginx configuration deployment completed!"
