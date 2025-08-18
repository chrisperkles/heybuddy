# 🤖 heyBuddy - AI Companion for Children's Learning and Growth

> **A German-first AI companion that helps children learn, grow, and navigate emotions safely**

heyBuddy is a privacy-first AI companion specifically designed for children aged 4-12, running on Raspberry Pi 5 with professional audio hardware. It provides safe, educational conversations in German while giving parents complete oversight and control.

## 🌟 Key Features

### 🧠 **German AI Companion**
- **Native German conversations** with cultural context and fairy tale references
- **Age-appropriate responses** tailored to child development stages
- **Educational focus** on science, nature, learning, and creativity
- **Emotional support** with automatic parent notifications when needed
- **Story generation** with German fairy tales and moral lessons

### 🛡️ **Safety & Privacy First**
- **Multi-layer content filtering** using OpenAI Moderation API + German-specific filters
- **Local data storage** - conversations never leave your home
- **No always-listening** - button activation only for privacy
- **Parental oversight** with real-time monitoring dashboard
- **DSGVO/GDPR compliant** data handling

### 📱 **Parent Dashboard & Monitoring**
- **Real-time conversation monitoring** via web dashboard
- **Mobile-friendly interface** accessible from any device on your network
- **Conversation history** and analytics
- **Emotional support alerts** sent directly to parents
- **System health monitoring** with automatic updates

### 🔧 **Production-Ready Deployment**
- **One-command installation** on Raspberry Pi 5
- **Automatic audio configuration** for Anker PowerConf S330
- **Systemd service** with auto-restart and health monitoring
- **Over-the-Air updates** with automatic rollback on failure
- **Remote debugging** tools for maintenance

## 🎯 **Perfect For**

- **German-speaking families** wanting safe AI interaction for children
- **Parents** seeking educational screen-time alternatives  
- **Homeschooling families** needing interactive learning support
- **Children** who need emotional support and patient conversation partners
- **Tech-savvy parents** wanting full control over their child's AI interactions

## 📊 **What Makes heyBuddy Special**

| Traditional AI | heyBuddy |
|----------------|----------|
| ❌ English-only | ✅ German-first with cultural context |
| ❌ Cloud-dependent | ✅ Local processing & storage |
| ❌ Always listening | ✅ Button-activated privacy |
| ❌ No parental control | ✅ Complete oversight dashboard |
| ❌ Generic responses | ✅ Child development focused |
| ❌ Complex setup | ✅ 30-minute Pi installation |

## 🚀 **Quick Start - Get heyBuddy Running in 30 Minutes**

### 🥧 **Raspberry Pi 5 Installation (Recommended)**

**From unboxing to first conversation in 30-45 minutes:**

1. **Flash Raspberry Pi OS** (64-bit regular version)
2. **Connect hardware**: Pi 5 + Anker PowerConf S330 + power
3. **Run one command**: 
   ```bash
   curl -fsSL https://raw.githubusercontent.com/chrisperkles/heybuddy/main/scripts/quick-install.sh | bash
   ```
4. **Add your OpenAI API key**:
   ```bash
   sudo nano /opt/heybuddy/.env
   # Set OPENAI_API_KEY=your-key-here
   ```
5. **Start heyBuddy**:
   ```bash
   sudo systemctl start heybuddy
   ```
6. **Access parent dashboard**: `http://your-pi-ip:8080`

📚 **Detailed setup guide**: [PI_SETUP_GUIDE.md](PI_SETUP_GUIDE.md)

### 💻 **Local Development (No Hardware Required)**

1. **Clone and Setup**
   ```bash
   git clone https://github.com/chrisperkles/heybuddy.git
   cd heybuddy
   
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements-dev.txt
   ```

2. **Configure Environment**
   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit .env and set your OpenAI API key
   nano .env
   ```

3. **Run Application**
   ```bash
   # Set Python path
   export PYTHONPATH=$(pwd)/src
   
   # Run with mock audio (no hardware needed)
   python src/main.py
   ```

4. **Test API**
   ```bash
   # Health check
   curl http://localhost:8080/health
   
   # Audio test with mock device
   curl -X POST http://localhost:8080/audio/test
   ```

### Docker Development

```bash
# Copy environment file
cp .env.example .env
# Edit .env with your settings

# Start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f heybuddy

# Test audio
docker-compose run audio-test
```

## 💰 **Cost & Requirements**

### **Hardware Requirements**
- **Raspberry Pi 5** (4GB or 8GB) - €70-90
- **Anker PowerConf S330** USB speakerphone - €130-150
- **MicroSD card** (32GB+, Class 10) - €10-15
- **Power supply** (Official 27W USB-C) - €8-12
- **Total hardware**: ~€220-280

### **Ongoing Costs**
- **OpenAI API**: ~€5-15/month (depends on child's usage)
- **No subscription fees** - you own and control everything

### **What Your Child Can Ask heyBuddy**

🔬 **Science & Learning**
```
"Wie funktioniert ein Regenbogen?"
"Warum ist der Himmel blau?"
"Wie lernen Babys sprechen?"
```

📚 **Stories & Creativity**
```
"Erzähl mir eine Geschichte über einen mutigen Pinguin"
"Ich möchte ein Märchen über Freundschaft hören"
"Erfinde eine Geschichte mit einem Drachen"
```

💙 **Emotional Support**
```
"Ich bin heute traurig"
"Ich habe Angst vor der Schule"
"Warum ärgert mich mein Bruder?"
```

🌿 **Nature & Animals**
```
"Wie schlafen Delfine?"
"Warum sind Blätter grün?"
"Wo leben Pinguine?"
```

## 🛠️ **Advanced Features**

### **German Cultural Integration**
- References to German fairy tales (Grimm Brothers)
- German educational context and cultural values
- Age-appropriate German vocabulary development
- Support for regional German dialects and expressions

### **Real-Time Monitoring**
- Live conversation transcripts in parent dashboard
- Emotional state detection with keyword analysis
- Automatic alerts for concerning topics
- Weekly conversation summaries and insights

### **System Administration**
- Remote debugging via web interface
- Automatic system health monitoring
- Over-the-air updates with rollback capability
- Mobile-responsive dashboard for monitoring anywhere

## Raspberry Pi 5 Deployment

### Prerequisites
- Raspberry Pi 5 with Raspberry Pi OS (64-bit regular version)
- Anker PowerConf S330 USB speakerphone
- Internet connection
- OpenAI API key

### Installation

**Use the quick installation script (recommended):**

```bash
# Download and run the installer
curl -fsSL https://raw.githubusercontent.com/chrisperkles/heybuddy/main/scripts/quick-install.sh | bash

# Configure your OpenAI API key
sudo nano /opt/heybuddy/.env
# Set OPENAI_API_KEY=your-key-here

# Start the service
sudo systemctl start heybuddy
sudo systemctl status heybuddy
```

**📋 Complete setup guide**: [PI_SETUP_GUIDE.md](PI_SETUP_GUIDE.md)
**🛒 Hardware shopping list**: [HARDWARE_CHECKLIST.md](HARDWARE_CHECKLIST.md)

### Service Management

```bash
# Check status
sudo systemctl status heybuddy

# View logs
sudo journalctl -u heybuddy -f

# Restart service
sudo systemctl restart heybuddy

# Stop service
sudo systemctl stop heybuddy

# Disable auto-start
sudo systemctl disable heybuddy
```

## Testing Without Hardware

The application includes comprehensive mocking for development:

- **Mock Audio Device**: Simulates PowerConf S330 using system audio
- **Offline Mode**: Works without internet for basic functions
- **Docker Environment**: Containerized testing with health checks

### Test Audio Pipeline
```bash
# Test mock audio recording/playback
python tests/test_audio.py

# Test API endpoints
pytest tests/integration/

# Run all tests
pytest
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | Required | Your OpenAI API key |
| `AUDIO_DEVICE` | `auto` | `auto`, `mock`, or `powerconf` |
| `ENVIRONMENT` | `development` | `development` or `production` |
| `API_PORT` | `8080` | API server port |
| `LOG_LEVEL` | `INFO` | Logging level |

### Audio Device Selection

- **`auto`**: Automatically detect PowerConf S330, fallback to mock
- **`mock`**: Use system audio for development
- **`powerconf`**: Force PowerConf S330 hardware

## Architecture

```
heyBuddy/
├── src/
│   ├── core/           # Core functionality
│   │   ├── audio.py    # Audio processing & device management
│   │   ├── config.py   # Configuration management
│   │   └── ai_client.py # OpenAI integration (TODO)
│   ├── api/            # REST API for companion app
│   └── main.py         # Application entry point
├── config/
│   └── systemd/        # Systemd service configuration
├── scripts/
│   └── install.sh      # Raspberry Pi installation script
└── tests/              # Test suite
```

## Safety Features

- **Content Moderation**: OpenAI Moderation API for all interactions
- **Privacy Controls**: No always-listening, button activation only
- **Parental Oversight**: Companion app for monitoring
- **Secure Storage**: Encrypted conversation logs
- **Age-Appropriate**: Configurable content filtering

## 🔌 **API Endpoints**

### **Conversation API**
```bash
# Start a German conversation
POST /conversation/text
{
  "message": "Hallo heyBuddy, wie geht es dir?",
  "user_id": "my_child", 
  "age": 8
}

# Generate a German story
POST /conversation/story
{
  "theme": "Ein mutiger kleiner Pinguin",
  "user_id": "my_child",
  "age": 6
}

# Get conversation history
GET /conversation/history/my_child

# Get conversation summary
GET /conversation/summary/my_child
```

### **Health & Monitoring**
```bash
# Check system health
GET /health

# Get detailed system info  
GET /debug/system

# Monitor service status
GET /debug/services

# Access debug dashboard
GET /debug/
```

### **Dashboard & WebSocket**
```bash
# Parent dashboard
GET /

# Real-time updates via WebSocket
WS /ws/default

# Debug WebSocket for system monitoring
WS /debug/ws/{session_id}
```

## Development Workflow

1. **Local Development**: Use mock audio for rapid iteration
2. **Integration Testing**: Docker environment with health checks
3. **Hardware Testing**: Deploy to Raspberry Pi for full testing
4. **Production**: Systemd service with monitoring

## Troubleshooting

### Audio Issues
```bash
# Check audio devices
aplay -l
arecord -l

# Test PowerConf S330
lsusb | grep -i anker

# Check audio permissions
groups $USER | grep audio
```

### Service Issues
```bash
# Check service logs
sudo journalctl -u heybuddy --no-pager

# Check pre-start script
sudo /opt/heybuddy/scripts/pre-start-check.sh

# Manual start for debugging
sudo -u heybuddy /opt/heybuddy/scripts/start.sh
```

### API Issues
```bash
# Test local connection
curl -v http://localhost:8080/health

# Check firewall
sudo ufw status

# Check process
ps aux | grep heybuddy
```

## 📂 **Project Structure**

```
heyBuddy/
├── 📋 PI_SETUP_GUIDE.md          # Complete Pi installation guide
├── 🛒 HARDWARE_CHECKLIST.md      # Shopping list and requirements
├── 📚 COMPREHENSIVE_DOCUMENTATION.md  # Technical documentation
├── 🧠 GERMAN_IMPLEMENTATION_COMPLETE.md  # German AI details
├── 🛠️ DEVELOPMENT_FRAMEWORK_COMPLETE.md  # Debugging tools
├── 
├── src/
│   ├── core/
│   │   ├── ai_client.py          # OpenAI integration with German support
│   │   ├── german_ai.py          # German language processing
│   │   ├── audio.py              # PowerConf S330 audio management
│   │   └── config.py             # Configuration management
│   ├── api/
│   │   ├── routes.py             # Conversation API endpoints
│   │   ├── debug_routes.py       # System monitoring APIs
│   │   └── websocket.py          # Real-time communication
│   ├── services/
│   │   ├── ota_updater.py        # Over-the-air update system
│   │   └── remote_debug.py       # Remote debugging tools
│   └── database/
│       └── local_db.py           # Local SQLite with encryption
├── web_dashboard/
│   ├── index.html                # Parent monitoring dashboard
│   └── debug.html                # System administration interface
├── mobile_dashboard/
│   └── index.html                # Mobile PWA dashboard
├── config/systemd/
│   └── heybuddy.service          # Production systemd service
├── scripts/
│   └── quick-install.sh          # One-command Pi installation
└── tests/
    └── integration/
        └── test_pi_deployment.py # Complete system tests
```

## 🌐 **Remote Access Options**

| Method | Complexity | Security | Best For |
|--------|------------|----------|----------|
| **Local WiFi** | ⭐ Easy | 🔒 High | Home use |
| **Cloudflare Tunnel** | ⭐⭐ Medium | 🔒🔒 Very High | Remote monitoring |
| **VPN** | ⭐⭐⭐ Advanced | 🔒🔒 Very High | Security focused |
| **Dynamic DNS** | ⭐⭐ Medium | 🔒 Medium | Simple remote access |

## 🧪 **Testing & Quality**

- **Integration tests** for complete Pi deployment
- **German conversation** validation
- **Audio pipeline** testing with mock hardware
- **Performance benchmarks** for Pi constraints
- **Safety filtering** verification
- **OTA update** testing with rollback

Run tests:
```bash
python tests/integration/test_pi_deployment.py
```

## 🤝 **Contributing**

We welcome contributions from the community! Whether you're:

- **Parents** with feedback on child interactions
- **Developers** wanting to improve German language support
- **Educators** with curriculum suggestions  
- **Security experts** helping with safety features

### **How to Contribute**
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes with tests
4. Run tests: `python tests/integration/test_pi_deployment.py`
5. Submit pull request

### **Areas We Need Help With**
- 🇩🇪 German language improvements and cultural context
- 🛡️ Additional safety filters and content moderation
- 🎨 UI/UX improvements for parent dashboard
- 📱 Mobile app development
- 🧪 Additional testing scenarios
- 📖 Documentation translation

## 🆘 **Support & Community**

### **Getting Help**
- 📋 **Setup issues**: Check [PI_SETUP_GUIDE.md](PI_SETUP_GUIDE.md)
- 🔧 **Technical problems**: Use the debug dashboard at `http://your-pi:8080/debug/`
- 🐛 **Bug reports**: Open an issue on GitHub
- 💡 **Feature requests**: Start a discussion

### **Resources**
- **Complete documentation**: [COMPREHENSIVE_DOCUMENTATION.md](COMPREHENSIVE_DOCUMENTATION.md)
- **German AI details**: [GERMAN_IMPLEMENTATION_COMPLETE.md](GERMAN_IMPLEMENTATION_COMPLETE.md)  
- **Development tools**: [DEVELOPMENT_FRAMEWORK_COMPLETE.md](DEVELOPMENT_FRAMEWORK_COMPLETE.md)
- **Hardware guide**: [HARDWARE_CHECKLIST.md](HARDWARE_CHECKLIST.md)

## 📄 **License**

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🛡️ **Privacy & Safety**

heyBuddy is built with privacy-first principles:

- **🏠 Local processing**: Conversations stored only on your Pi
- **🔒 DSGVO/GDPR compliant**: European privacy standards
- **👨‍👩‍👧‍👦 Parental control**: Complete oversight of all interactions
- **🛡️ Multi-layer safety**: OpenAI + custom German content filters
- **🔍 Transparency**: Open source - see exactly how it works
- **📱 Real-time alerts**: Immediate parent notifications when needed

### **Data Handling**
- **No cloud storage** - all data stays on your Raspberry Pi
- **Encrypted local storage** using AES-256 encryption  
- **No tracking or analytics** sent to third parties
- **OpenAI API only** - for generating responses (required for AI functionality)
- **Complete data portability** - export or delete anytime

---

## ⭐ **Star this Project**

If heyBuddy helps your family, please **star this repository** to help other German families discover it!

**Built with ❤️ for German families who want safe, educational AI for their children**

**🤖 Created to help children learn, grow, and explore the world safely in their native language**