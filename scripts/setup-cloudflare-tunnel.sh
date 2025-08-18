#!/bin/bash
# Cloudflare Tunnel Setup for heyBuddy
# Secure remote access without port forwarding

echo "☁️ Setting up Cloudflare Tunnel for heyBuddy"

# Download cloudflared
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared-linux-arm64.deb

# Create tunnel configuration
mkdir -p ~/.cloudflared
tee ~/.cloudflared/config.yml > /dev/null <<EOF
tunnel: heybuddy-tunnel
credentials-file: ~/.cloudflared/cert.json

ingress:
  # Main dashboard
  - hostname: heybuddy-dashboard.your-domain.com
    service: http://localhost:8080
    
  # Debug dashboard  
  - hostname: heybuddy-debug.your-domain.com
    service: http://localhost:8080/debug/
    
  # Catch-all
  - service: http_status:404
EOF

echo "📋 Manual Steps:"
echo "1. Login to Cloudflare: cloudflared tunnel login"
echo "2. Create tunnel: cloudflared tunnel create heybuddy-tunnel"
echo "3. Route DNS: cloudflared tunnel route dns heybuddy-tunnel heybuddy-dashboard.your-domain.com"
echo "4. Install service: cloudflared service install"
echo "5. Start tunnel: sudo systemctl start cloudflared"
echo ""
echo "🌐 Access via: https://heybuddy-dashboard.your-domain.com"
echo "🔒 Automatically HTTPS secured!"