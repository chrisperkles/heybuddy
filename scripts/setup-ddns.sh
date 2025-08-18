#!/bin/bash
# Dynamic DNS Setup for Remote heyBuddy Access
# Allows access from anywhere via custom domain

echo "🌐 Setting up Dynamic DNS for heyBuddy Remote Access"

# Install ddclient for dynamic DNS
sudo apt-get update
sudo apt-get install -y ddclient

# Configure ddclient
sudo tee /etc/ddclient.conf > /dev/null <<EOF
# Dynamic DNS Configuration
protocol=dyndns2
use=web, web=checkip.dyndns.com/, web-skip='IP Address'
server=members.dyndns.org
login=your-dyndns-username
password='your-dyndns-password'
your-domain.dyndns.org
EOF

# Set proper permissions
sudo chmod 600 /etc/ddclient.conf
sudo chown root:root /etc/ddclient.conf

# Enable ddclient service
sudo systemctl enable ddclient
sudo systemctl start ddclient

# Configure router port forwarding (manual step)
echo "📋 Manual Steps Required:"
echo "1. Login to your router (usually 192.168.1.1)"
echo "2. Go to Port Forwarding settings"
echo "3. Forward external port 8080 to Pi IP:8080"
echo "4. Access via: http://your-domain.dyndns.org:8080"

echo "✅ Dynamic DNS setup complete!"