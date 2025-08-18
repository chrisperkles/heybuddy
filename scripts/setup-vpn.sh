#!/bin/bash
# WireGuard VPN Setup for Secure Remote Access
# Access Pi dashboard securely from anywhere

echo "🔒 Setting up WireGuard VPN for secure heyBuddy access"

# Install WireGuard
sudo apt-get update
sudo apt-get install -y wireguard

# Generate server keys
cd /etc/wireguard
sudo wg genkey | sudo tee server-private.key | wg pubkey | sudo tee server-public.key
sudo wg genkey | sudo tee client-private.key | wg pubkey | sudo tee client-public.key

# Create server config
sudo tee /etc/wireguard/wg0.conf > /dev/null <<EOF
[Interface]
PrivateKey = $(sudo cat server-private.key)
Address = 10.0.0.1/24
ListenPort = 51820
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

[Peer]
# Parent's phone/laptop
PublicKey = $(sudo cat client-public.key)
AllowedIPs = 10.0.0.2/32
EOF

# Create client config
sudo tee /etc/wireguard/client.conf > /dev/null <<EOF
[Interface]
PrivateKey = $(sudo cat client-private.key)
Address = 10.0.0.2/32
DNS = 8.8.8.8

[Peer]
PublicKey = $(sudo cat server-public.key)
Endpoint = your-home-ip:51820
AllowedIPs = 10.0.0.0/24
PersistentKeepalive = 25
EOF

# Enable IP forwarding
echo 'net.ipv4.ip_forward = 1' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Start WireGuard
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0

echo "✅ VPN setup complete!"
echo "📱 Install WireGuard app on phone and import client.conf"
echo "🌐 Access dashboard via: http://10.0.0.1:8080"