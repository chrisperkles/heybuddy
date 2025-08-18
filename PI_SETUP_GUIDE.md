# 🥧 Raspberry Pi 5 heyBuddy Setup Guide
## From Unboxing to Your Child's First Conversation

This guide takes you from opening the Pi box to having heyBuddy ready for your child. Total setup time: **30-45 minutes**.

---

## 📦 **Step 1: Hardware Setup (5 minutes)**

### **What You Need:**
- ✅ Raspberry Pi 5 (4GB or 8GB)
- ✅ Anker PowerConf S330 USB Speakerphone
- ✅ MicroSD card (32GB+ recommended)
- ✅ USB-C power supply (27W official Pi adapter)
- ✅ HDMI cable (for initial setup only)
- ✅ USB keyboard & mouse (for initial setup only)
- ✅ Ethernet cable OR WiFi access

### **Physical Setup:**
1. **Insert MicroSD card** into Pi slot
2. **Connect Anker PowerConf S330** via USB-A port
3. **Connect HDMI** to monitor/TV
4. **Connect keyboard & mouse** via USB ports
5. **Connect Ethernet** (optional - WiFi works too)
6. **Connect power last** - Pi will boot immediately

---

## 💽 **Step 2: Install Raspberry Pi OS (10 minutes)**

### **Option A: Pre-configured Image (Recommended)**
```bash
# Download heyBuddy Pi image (when available)
# Flash to SD card using Raspberry Pi Imager
# Skip to Step 4
```

### **Option B: Fresh Installation**

**On your computer:**

1. **Download Raspberry Pi Imager**
   - Visit: https://www.raspberrypi.org/software/
   - Install on Windows/Mac/Linux

2. **Flash Raspberry Pi OS**
   ```
   - Open Raspberry Pi Imager
   - Choose OS: "Raspberry Pi OS (64-bit)" - Regular version (NOT Lite, NOT Full)
     • 64-bit for Pi 5 performance
     • Regular version has desktop + essential apps
     • Lite = no desktop (harder to setup)
     • Full = bloated with unnecessary software
   - Choose Storage: Your MicroSD card
   - Click gear icon ⚙️ for advanced options:
     ✅ Enable SSH
     ✅ Set username: pi
     ✅ Set password: your-secure-password
     ✅ Configure WiFi (optional)
     ✅ Set locale: Germany (if applicable)
   - Click WRITE
   ```

3. **Wait for flash to complete** (~5-10 minutes)

4. **Insert SD card** into Pi and power on

---

## 🔌 **Step 3: First Boot & Basic Setup (5 minutes)**

1. **Pi boots up** - wait for desktop to appear
2. **Complete initial setup wizard:**
   - Set country, language, timezone
   - Connect to WiFi (if not done during flash)
   - Update software (recommended)

3. **Enable SSH & Audio** (if not done during flash):
   ```bash
   sudo raspi-config
   # Interface Options → SSH → Enable
   # Advanced Options → Audio → Force 3.5mm jack
   # Finish and reboot
   ```

4. **Test audio hardware:**
   ```bash
   # List audio devices
   aplay -l
   arecord -l
   
   # Should see PowerConf S330 listed
   ```

---

## 🤖 **Step 4: Install heyBuddy (15 minutes)**

### **Quick Install Script**

1. **Open terminal** on Pi

2. **Download and run installer:**
   ```bash
   # Download heyBuddy installer
   curl -fsSL https://raw.githubusercontent.com/chrisperkles/heybuddy/main/scripts/quick-install.sh -o install-heybuddy.sh
   
   # Make executable and run
   chmod +x install-heybuddy.sh
   ./install-heybuddy.sh
   ```

### **Manual Installation (if script fails):**

1. **Install dependencies:**
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip git sqlite3 alsa-utils portaudio19-dev
   ```

2. **Clone heyBuddy:**
   ```bash
   cd /opt
   sudo git clone https://github.com/chrisperkles/heybuddy.git
   sudo chown -R pi:pi heybuddy/
   cd heybuddy
   ```

3. **Install Python dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Create directories:**
   ```bash
   sudo mkdir -p /opt/heybuddy/{data,logs,backups}
   sudo chown -R pi:pi /opt/heybuddy/
   ```

5. **Install systemd service:**
   ```bash
   sudo cp config/systemd/heybuddy.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable heybuddy
   ```

---

## 🔑 **Step 5: Configuration (5 minutes)**

1. **Get OpenAI API Key:**
   - Visit: https://platform.openai.com/api-keys
   - Create account and get API key
   - Note: ~$5-10/month for typical child usage

2. **Configure heyBuddy:**
   ```bash
   cd /opt/heybuddy
   cp .env.example .env
   nano .env
   ```

3. **Edit configuration:**
   ```env
   # Required
   OPENAI_API_KEY=your-openai-api-key-here
   
   # Audio settings
   AUDIO_DEVICE=auto
   SAMPLE_RATE=44100
   
   # Language & Safety
   LANGUAGE=de
   ENABLE_MODERATION=true
   MAX_CONVERSATION_LENGTH=20
   
   # System
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   API_PORT=8080
   
   # Child settings
   DEFAULT_CHILD_AGE=8
   PARENT_EMAIL=your-email@example.com
   ```

4. **Test configuration:**
   ```bash
   source venv/bin/activate
   export PYTHONPATH=/opt/heybuddy/src
   python src/main.py --test-config
   ```

---

## 🚀 **Step 6: Start heyBuddy (2 minutes)**

1. **Start the service:**
   ```bash
   sudo systemctl start heybuddy
   ```

2. **Check status:**
   ```bash
   sudo systemctl status heybuddy
   ```

3. **View logs:**
   ```bash
   sudo journalctl -u heybuddy -f
   ```

4. **Test API:**
   ```bash
   curl http://localhost:8080/health
   # Should return: {"status":"healthy",...}
   ```

---

## 📱 **Step 7: Access Dashboard**

### **Find Pi IP Address:**
```bash
hostname -I
# Example output: 192.168.1.100
```

### **Access from phone/computer:**
```
Parent Dashboard: http://192.168.1.100:8080
Debug Dashboard:  http://192.168.1.100:8080/debug/
```

### **Install Mobile App:**
1. Visit dashboard on phone
2. Tap "Add to Home Screen"
3. Get app-like experience

---

## 🎯 **Step 8: First Conversation Test**

1. **Test German conversation:**
   ```bash
   curl -X POST http://localhost:8080/conversation/text \
     -H "Content-Type: application/json" \
     -d '{"message": "Hallo heyBuddy, wie geht es dir?", "user_id": "test_child", "age": 8}'
   ```

2. **Expected response:**
   ```json
   {
     "success": true,
     "response": "Hallo! Mir geht es gut, danke der Nachfrage! Wie kann ich dir heute helfen?",
     "safety_info": {"input_safe": true, "output_safe": true}
   }
   ```

3. **Test story generation:**
   ```bash
   curl -X POST http://localhost:8080/conversation/story \
     -H "Content-Type: application/json" \
     -d '{"theme": "Ein mutiger kleiner Hase", "user_id": "test_child", "age": 6}'
   ```

---

## ✅ **Step 9: Final Configuration**

### **Audio Test:**
```bash
# Test microphone
arecord -D plughw:1,0 -d 5 test.wav
aplay test.wav

# Test speakers  
speaker-test -D plughw:1,0 -t wav
```

### **Auto-start Configuration:**
```bash
# Ensure service starts on boot
sudo systemctl enable heybuddy

# Test reboot
sudo reboot
# Wait 2 minutes, then test: curl http://pi-ip:8080/health
```

### **Security Setup:**
```bash
# Change default password
passwd

# Update system
sudo apt update && sudo apt upgrade -y

# Configure firewall (optional)
sudo ufw allow 8080
sudo ufw enable
```

---

## 🎉 **You're Done!**

### **What You Have Now:**
- ✅ heyBuddy AI companion running on Pi
- ✅ German language support
- ✅ Anker PowerConf S330 audio working
- ✅ Parent dashboard accessible on phone
- ✅ Real-time monitoring and safety features
- ✅ Over-the-air updates enabled

### **Your Child Can Now:**
- Talk to heyBuddy in German
- Ask questions about science, nature, learning
- Request stories and fairy tales  
- Get emotional support when needed
- Learn through interactive conversations

### **You Can:**
- Monitor all conversations in real-time
- Receive alerts for emotional support situations
- View conversation history and analytics
- Update system remotely
- Access debug tools if needed

---

## 📞 **Quick Commands Reference**

```bash
# Service management
sudo systemctl start heybuddy      # Start
sudo systemctl stop heybuddy       # Stop  
sudo systemctl restart heybuddy    # Restart
sudo systemctl status heybuddy     # Status

# Logs
sudo journalctl -u heybuddy -f     # Live logs
sudo journalctl -u heybuddy --since "1 hour ago"  # Recent logs

# Health check
curl http://localhost:8080/health

# Configuration  
sudo nano /opt/heybuddy/.env       # Edit config
sudo systemctl restart heybuddy    # Apply changes

# Updates
cd /opt/heybuddy
git pull origin main               # Get updates
sudo systemctl restart heybuddy    # Apply updates
```

---

## 🆘 **Troubleshooting**

### **Service won't start:**
```bash
# Check logs
sudo journalctl -u heybuddy --no-pager

# Check configuration
cd /opt/heybuddy
source venv/bin/activate
python src/main.py --test-config
```

### **Audio not working:**
```bash
# List devices
aplay -l
arecord -l

# Test Anker device
aplay -D plughw:1,0 /usr/share/sounds/alsa/Front_Left.wav
```

### **API not responding:**
```bash
# Check if running
ps aux | grep python
netstat -tlnp | grep 8080

# Check firewall
sudo ufw status
```

### **Dashboard not accessible:**
```bash
# Check Pi IP
hostname -I

# Test from Pi
curl http://localhost:8080/health

# Check WiFi connection
ping google.com
```

**Need help?** Check the troubleshooting guide or create an issue on GitHub.

**🎯 Total setup time: 30-45 minutes from unboxing to first conversation!**