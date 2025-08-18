#!/bin/bash
# heyBuddy Quick Installation Script for Raspberry Pi 5
# This script installs heyBuddy AI companion from scratch

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ASCII Art
echo -e "${BLUE}"
cat << "EOF"
    __                ____            __    __      
   / /_  ___  __  __/ __ )__  ______/ /___/ /_  __ 
  / __ \/ _ \/ / / / __  / / / / __  / __  / / / / 
 / / / /  __/ /_/ / /_/ / /_/ / /_/ / /_/ / /_/ /  
/_/ /_/\___/\__, /_____/\__,_/\__,_/\__,_/\__, /   
           /____/                        /____/    
                                                   
    AI Companion for Children - Quick Installer
EOF
echo -e "${NC}"

echo -e "${GREEN}🚀 Starting heyBuddy installation on Raspberry Pi 5...${NC}"
echo -e "${YELLOW}⏱️  Estimated time: 10-15 minutes${NC}"
echo

# Check if running on Raspberry Pi
if [[ ! -f /proc/device-tree/model ]] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo -e "${RED}❌ Error: This script is designed for Raspberry Pi only${NC}"
    exit 1
fi

# Check for Raspberry Pi 5
PI_MODEL=$(tr -d '\0' < /proc/device-tree/model)
echo -e "${BLUE}🥧 Detected: $PI_MODEL${NC}"

# Function to print step headers
step() {
    echo -e "\n${BLUE}📋 Step $1: $2${NC}"
}

# Function to check command success
check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1 completed successfully${NC}"
    else
        echo -e "${RED}❌ Error: $1 failed${NC}"
        exit 1
    fi
}

# Step 1: System Update
step 1 "Updating system packages"
sudo apt update && sudo apt upgrade -y
check_success "System update"

# Step 2: Install Dependencies  
step 2 "Installing system dependencies"
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    sqlite3 \
    alsa-utils \
    portaudio19-dev \
    libffi-dev \
    libasound2-dev \
    curl \
    wget \
    systemd \
    ufw
check_success "Dependency installation"

# Step 3: Create heyBuddy user and directories
step 3 "Setting up heyBuddy user and directories"
sudo useradd -r -s /bin/false heybuddy 2>/dev/null || true
sudo mkdir -p /opt/heybuddy/{data,logs,backups,config}
sudo chown -R heybuddy:heybuddy /opt/heybuddy/
check_success "User and directory setup"

# Step 4: Clone heyBuddy repository
step 4 "Downloading heyBuddy from GitHub"
cd /tmp
if [ -d "heybuddy" ]; then
    rm -rf heybuddy
fi
git clone https://github.com/chrisperkles/heybuddy.git
check_success "Repository clone"

# Step 5: Install heyBuddy
step 5 "Installing heyBuddy application"
sudo cp -r heybuddy/* /opt/heybuddy/
sudo chown -R heybuddy:heybuddy /opt/heybuddy/
cd /opt/heybuddy
check_success "Application installation"

# Step 6: Create Python virtual environment
step 6 "Setting up Python environment"
sudo -u heybuddy python3 -m venv /opt/heybuddy/venv
sudo -u heybuddy /opt/heybuddy/venv/bin/pip install --upgrade pip
sudo -u heybuddy /opt/heybuddy/venv/bin/pip install -r /opt/heybuddy/requirements.txt
check_success "Python environment setup"

# Step 7: Install systemd service
step 7 "Installing system service"
sudo cp /opt/heybuddy/config/systemd/heybuddy.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable heybuddy
check_success "System service installation"

# Step 8: Create configuration file
step 8 "Creating initial configuration"
if [ ! -f /opt/heybuddy/.env ]; then
    sudo cp /opt/heybuddy/.env.example /opt/heybuddy/.env
    sudo chown heybuddy:heybuddy /opt/heybuddy/.env
    
    # Auto-detect audio device
    AUDIO_DEVICE="mock"
    if lsusb | grep -i anker; then
        AUDIO_DEVICE="auto"
        echo -e "${GREEN}🎵 Anker PowerConf S330 detected!${NC}"
    fi
    
    # Update configuration with detected settings
    sudo sed -i "s/AUDIO_DEVICE=.*/AUDIO_DEVICE=${AUDIO_DEVICE}/" /opt/heybuddy/.env
    sudo sed -i "s/ENVIRONMENT=.*/ENVIRONMENT=production/" /opt/heybuddy/.env
    sudo sed -i "s/LANGUAGE=.*/LANGUAGE=de/" /opt/heybuddy/.env
fi
check_success "Configuration setup"

# Step 9: Configure audio permissions
step 9 "Configuring audio permissions"
sudo usermod -a -G audio heybuddy
sudo usermod -a -G dialout heybuddy
check_success "Audio permissions"

# Step 10: Setup log rotation
step 10 "Setting up log rotation"
sudo tee /etc/logrotate.d/heybuddy > /dev/null << 'EOF'
/opt/heybuddy/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 heybuddy heybuddy
    postrotate
        systemctl reload heybuddy || true
    endscript
}
EOF
check_success "Log rotation setup"

# Step 11: Configure firewall
step 11 "Configuring firewall"
sudo ufw allow 8080/tcp comment "heyBuddy API"
sudo ufw allow ssh comment "SSH access"
if ! sudo ufw status | grep -q "Status: active"; then
    echo -e "${YELLOW}⚠️  Firewall not enabled. Run 'sudo ufw enable' after setup.${NC}"
fi
check_success "Firewall configuration"

# Step 12: Final system configuration
step 12 "Final system configuration"

# Enable I2C and SPI for potential hardware expansion
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0

# Set GPU memory split for better audio performance
sudo raspi-config nonint do_memory_split 64

check_success "Final system configuration"

# Installation complete
echo -e "\n${GREEN}🎉 heyBuddy installation completed successfully!${NC}"
echo -e "${BLUE}────────────────────────────────────────────────────${NC}"

# Display next steps
echo -e "\n${YELLOW}📋 Next Steps:${NC}"
echo -e "1. ${BLUE}Configure OpenAI API key:${NC}"
echo -e "   sudo nano /opt/heybuddy/.env"
echo -e "   # Set OPENAI_API_KEY=your-key-here"
echo

echo -e "2. ${BLUE}Start heyBuddy service:${NC}"
echo -e "   sudo systemctl start heybuddy"
echo

echo -e "3. ${BLUE}Check service status:${NC}"
echo -e "   sudo systemctl status heybuddy"
echo

echo -e "4. ${BLUE}Test API health:${NC}"
echo -e "   curl http://localhost:8080/health"
echo

echo -e "5. ${BLUE}Access dashboard from phone/computer:${NC}"
PI_IP=$(hostname -I | awk '{print $1}')
echo -e "   http://${PI_IP}:8080"
echo

# Audio test instructions
if lsusb | grep -i anker; then
    echo -e "${GREEN}🎵 Anker PowerConf S330 detected and configured!${NC}"
else
    echo -e "${YELLOW}🎵 Audio Hardware Setup:${NC}"
    echo -e "   Connect your Anker PowerConf S330 via USB"
    echo -e "   Then restart the service: sudo systemctl restart heybuddy"
fi
echo

# Show system info
echo -e "${BLUE}📊 System Information:${NC}"
echo -e "   Pi Model: $PI_MODEL"
echo -e "   IP Address: $PI_IP"
echo -e "   Installation Path: /opt/heybuddy/"
echo -e "   Service Name: heybuddy"
echo -e "   Log Files: /opt/heybuddy/logs/"
echo

# Final warnings and tips
echo -e "${YELLOW}⚠️  Important Notes:${NC}"
echo -e "   • You MUST set your OpenAI API key before first use"
echo -e "   • OpenAI API costs ~$5-10/month for typical child usage"
echo -e "   • All conversations are stored locally and encrypted"
echo -e "   • Access the debug dashboard at: http://${PI_IP}:8080/debug/"
echo -e "   • Check logs with: sudo journalctl -u heybuddy -f"
echo

echo -e "${GREEN}🎯 Installation completed in $(($SECONDS / 60))m $(($SECONDS % 60))s${NC}"
echo -e "${BLUE}📚 Full documentation: /opt/heybuddy/PI_SETUP_GUIDE.md${NC}"
echo -e "${GREEN}✨ Your child's AI companion is ready to be configured!${NC}"