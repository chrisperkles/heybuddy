#!/bin/bash
set -e

# heyBuddy Installation Script for Raspberry Pi 5
# This script installs and configures heyBuddy as a systemd service

echo "🤖 heyBuddy Installation Script"
echo "==============================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    echo "❌ This script should not be run as root. Please run as a regular user with sudo privileges."
    exit 1
fi

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: This script is designed for Raspberry Pi. Continuing anyway..."
fi

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    alsa-utils \
    pulseaudio \
    pulseaudio-utils \
    sqlite3 \
    git \
    curl \
    ufw \
    libasound2-dev \
    portaudio19-dev

# Create heybuddy user
echo "👤 Creating heybuddy user..."
if ! id "heybuddy" &>/dev/null; then
    sudo useradd -r -s /bin/false -d /opt/heybuddy -c "heyBuddy AI Companion" heybuddy
    sudo usermod -a -G audio heybuddy
    echo "✅ Created heybuddy user and added to audio group"
else
    echo "ℹ️  heybuddy user already exists"
fi

# Create application directories
echo "📁 Creating application directories..."
sudo mkdir -p /opt/heybuddy/{src,config,data,logs,scripts}
sudo mkdir -p /opt/heybuddy/config/systemd

# Set permissions
sudo chown -R heybuddy:heybuddy /opt/heybuddy
sudo chmod 755 /opt/heybuddy
sudo chmod 755 /opt/heybuddy/data
sudo chmod 755 /opt/heybuddy/logs

# Copy application files
echo "📋 Copying application files..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

sudo cp -r "$PROJECT_ROOT/src"/* /opt/heybuddy/src/
sudo cp -r "$PROJECT_ROOT/config"/* /opt/heybuddy/config/
sudo cp -r "$PROJECT_ROOT/scripts"/* /opt/heybuddy/scripts/
sudo cp "$PROJECT_ROOT/requirements.txt" /opt/heybuddy/

# Set file permissions
sudo chown -R heybuddy:heybuddy /opt/heybuddy
sudo chmod +x /opt/heybuddy/scripts/*.sh
sudo chmod +x /opt/heybuddy/src/main.py

# Create Python virtual environment
echo "🐍 Creating Python virtual environment..."
sudo -u heybuddy python3 -m venv /opt/heybuddy/venv
sudo -u heybuddy /opt/heybuddy/venv/bin/pip install --upgrade pip

# Install Python dependencies
echo "📚 Installing Python dependencies..."
sudo -u heybuddy /opt/heybuddy/venv/bin/pip install -r /opt/heybuddy/requirements.txt

# Create environment file
echo "⚙️  Creating environment configuration..."
if [[ ! -f /opt/heybuddy/config/.env ]]; then
    sudo -u heybuddy cat > /opt/heybuddy/config/.env << 'EOF'
# heyBuddy Configuration
ENVIRONMENT=production
SECRET_KEY=your-secret-key-here-change-this
OPENAI_API_KEY=your-openai-api-key-here
LOG_LEVEL=INFO
LOG_FILE=/opt/heybuddy/logs/heybuddy.log
ENABLE_SYSTEMD_NOTIFY=true
AUDIO_DEVICE=auto
EOF
    echo "📝 Created default environment file at /opt/heybuddy/config/.env"
    echo "⚠️  IMPORTANT: Edit /opt/heybuddy/config/.env and set your OpenAI API key!"
else
    echo "ℹ️  Environment file already exists"
fi

# Configure audio system
echo "🔊 Configuring audio system..."

# Add user to audio group
sudo usermod -a -G audio $(whoami)

# Create ALSA configuration for USB audio
sudo -u heybuddy cat > /opt/heybuddy/config/asound.conf << 'EOF'
# ALSA configuration for heyBuddy
pcm.!default {
    type pulse
}
ctl.!default {
    type pulse
}

# PowerConf S330 configuration (if available)
pcm.powerconf {
    type hw
    card 1
}
EOF

# Install systemd service
echo "🎯 Installing systemd service..."
sudo cp /opt/heybuddy/config/systemd/heybuddy.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable heybuddy.service

# Create pre-start check script
sudo -u heybuddy cat > /opt/heybuddy/scripts/pre-start-check.sh << 'EOF'
#!/bin/bash
# Pre-start health check for heyBuddy

# Check if virtual environment exists
if [[ ! -d /opt/heybuddy/venv ]]; then
    echo "ERROR: Python virtual environment not found"
    exit 1
fi

# Check if main application exists
if [[ ! -f /opt/heybuddy/src/main.py ]]; then
    echo "ERROR: Main application file not found"
    exit 1
fi

# Check if environment file exists
if [[ ! -f /opt/heybuddy/config/.env ]]; then
    echo "ERROR: Environment configuration file not found"
    exit 1
fi

# Create log directory if it doesn't exist
mkdir -p /opt/heybuddy/logs

echo "Pre-start checks passed"
exit 0
EOF

sudo chmod +x /opt/heybuddy/scripts/pre-start-check.sh

# Configure firewall
echo "🔒 Configuring firewall..."
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment "SSH"
sudo ufw allow 8080/tcp comment "heyBuddy API"

# Audio device detection
echo "🎵 Detecting audio devices..."
echo "Available audio devices:"
aplay -l 2>/dev/null || echo "No playback devices found"
arecord -l 2>/dev/null || echo "No capture devices found"

# Check for PowerConf S330
if lsusb | grep -i "anker" >/dev/null; then
    echo "✅ Anker device detected via USB"
else
    echo "⚠️  Anker PowerConf S330 not detected. Make sure it's connected."
fi

# Create startup script
sudo -u heybuddy cat > /opt/heybuddy/scripts/start.sh << 'EOF'
#!/bin/bash
cd /opt/heybuddy
source venv/bin/activate
export PYTHONPATH=/opt/heybuddy/src
python src/main.py
EOF

sudo chmod +x /opt/heybuddy/scripts/start.sh

echo ""
echo "🎉 heyBuddy installation completed!"
echo ""
echo "📋 Next steps:"
echo "1. Edit /opt/heybuddy/config/.env and set your OpenAI API key"
echo "2. Connect your Anker PowerConf S330 device"
echo "3. Start the service: sudo systemctl start heybuddy"
echo "4. Check status: sudo systemctl status heybuddy"
echo "5. View logs: sudo journalctl -u heybuddy -f"
echo ""
echo "🌐 API will be available at: http://localhost:8080"
echo "📊 Health check: http://localhost:8080/health"
echo ""
echo "⚠️  Remember to reboot to ensure all audio permissions are applied!"