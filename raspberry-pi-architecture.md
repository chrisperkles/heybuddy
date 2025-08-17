# heyBuddy Raspberry Pi 5 System Architecture

## Hardware Setup

### Core Components
- **Raspberry Pi 5** (4GB+ RAM recommended)
- **Anker PowerConf S330** USB speakerphone (microphone + speaker)
- **64GB+ microSD card** for OS and local content storage
- **Official Raspberry Pi 5 power supply** (27W USB-C)
- **USB-C to USB-A adapter** (included with PowerConf S330)

### Hardware Compatibility
- **Pi 5 Audio**: No 3.5mm jack (removed from Pi 4), requires USB audio solution
- **USB Audio**: Pi 5 supports plug-and-play USB audio devices via standard Linux drivers
- **PowerConf S330**: Confirmed working with Linux/Raspberry Pi systems via standard USB audio class drivers
- **Power Requirements**: PowerConf S330 requires 5V/2A+ from USB port (Pi 5 can provide this)

## Software Stack

### Operating System
```
Raspberry Pi OS (Debian-based)
├── Python 3.11+ runtime environment
├── ALSA/PulseAudio for audio management
├── systemd for service management
└── UFW firewall for security
```

### Core Application Architecture
```
heyBuddy Application
├── Audio Processing Layer
│   ├── Speech Recognition (Whisper API/local)
│   ├── Text-to-Speech (OpenAI TTS/local)
│   └── Audio Device Management (ALSA)
├── AI Interaction Layer
│   ├── OpenAI ChatGPT API client
│   ├── Content moderation (OpenAI Moderation API)
│   ├── Safety filtering and validation
│   └── Response caching system
├── Security Layer
│   ├── API key encryption and management
│   ├── Request rate limiting
│   ├── Input/output sanitization
│   └── Network security (TLS/HTTPS only)
├── Companion App Interface
│   ├── REST API server (Flask/FastAPI)
│   ├── WebSocket for real-time updates
│   ├── Authentication and authorization
│   └── Parental controls backend
└── Local Storage
    ├── SQLite database (user profiles, settings)
    ├── Encrypted conversation logs
    ├── Offline content library (stories, songs)
    └── System configuration files
```

## Safety Implementation

### Multi-layered Content Filtering
```python
# Input Processing Pipeline
User Input → Speech-to-Text → Input Validation → Moderation API → ChatGPT API

# Output Processing Pipeline  
ChatGPT Response → Moderation API → Content Filtering → Safety Check → TTS → Audio Output
```

### Safety Measures
1. **OpenAI Moderation API**: Free real-time content filtering for all inputs and outputs
2. **Custom Content Filters**: Additional filtering for age-appropriate content
3. **Rate Limiting**: Prevent API abuse and excessive usage
4. **Request Logging**: Track interactions for safety monitoring (with privacy controls)
5. **Parental Oversight**: Dashboard for monitoring topics and conversation summaries

### Content Categories Monitored
- Hate speech and threats
- Self-harm content
- Sexual content (especially involving minors)
- Violence and graphic content
- Inappropriate language
- Adult themes

## Network Architecture

### Internet Connectivity
```
Internet → Router → WiFi → Raspberry Pi 5
                           ├── OpenAI ChatGPT API (HTTPS)
                           ├── OpenAI Moderation API (HTTPS)
                           ├── OpenAI Whisper API (HTTPS)
                           ├── OpenAI TTS API (HTTPS)
                           └── Companion App (Local Network)
```

### API Security
- **TLS 1.3 encryption** for all external communications
- **API key rotation** with secure local storage
- **Certificate pinning** for OpenAI endpoints
- **Request signing** for companion app communications

## Local Storage Architecture

### Database Schema (SQLite)
```sql
-- User profiles with encrypted personal data
users (id, name_encrypted, age, settings_json, created_at)

-- Conversation metadata (no full transcripts by default)
conversations (id, user_id, topic_summary, duration, timestamp)

-- Goals and achievements tracking
goals (id, user_id, description, status, created_at, completed_at)

-- Offline content library
content (id, type, title, audio_path, metadata_json)

-- System logs for troubleshooting
system_logs (id, level, message, timestamp)
```

### File System Structure
```
/opt/heybuddy/
├── app/                    # Main application code
├── config/                 # Configuration files
├── data/                   # SQLite databases
├── audio/                  # Offline audio content
├── logs/                   # Application logs
├── certs/                  # SSL certificates
└── scripts/                # Utility scripts

/etc/systemd/system/
└── heybuddy.service        # System service configuration
```

## Audio Processing Pipeline

### Hardware Audio Flow
```
Child's Voice → PowerConf S330 → USB → Raspberry Pi 5
                                        ↓
                                   Audio Processing
                                        ↓
AI Response → TTS → Audio Output → USB → PowerConf S330 → Speaker
```

### Software Audio Configuration
```bash
# ALSA configuration for PowerConf S330
sudo nano /etc/asound.conf

pcm.!default {
    type hw
    card 1  # PowerConf S330 USB audio device
}

ctl.!default {
    type hw
    card 1
}
```

## Companion App Integration

### Mobile App Communication
- **Local Network Discovery**: mDNS/Bonjour for automatic device discovery
- **Secure Authentication**: JWT tokens with device pairing
- **Real-time Updates**: WebSocket connection for live status
- **Offline Functionality**: Local caching when network unavailable

### Parental Control Features
- **Activity Dashboard**: High-level conversation summaries
- **Content Filters**: Customizable topic restrictions
- **Time Limits**: Usage scheduling and duration controls
- **Goal Setting**: Parent-defined objectives and tracking
- **Privacy Controls**: Data retention and deletion settings

## Security Hardening

### System Security
```bash
# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable avahi-daemon

# Configure firewall
sudo ufw enable
sudo ufw deny incoming
sudo ufw allow 8080/tcp  # Companion app API
sudo ufw allow 22/tcp    # SSH (change default port)

# Automatic security updates
sudo apt install unattended-upgrades
```

### Application Security
- **Input sanitization**: All user inputs validated and escaped
- **API key encryption**: Stored encrypted at rest
- **Process isolation**: Run with minimal privileges
- **Secure updates**: Signed update packages with verification

## Deployment Strategy

### Initial Setup Script
```bash
#!/bin/bash
# heyBuddy installation script

# System updates
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3-pip python3-venv alsa-utils pulseaudio sqlite3 -y

# Create application user
sudo useradd -r -s /bin/false heybuddy

# Setup application directory
sudo mkdir -p /opt/heybuddy
sudo chown heybuddy:heybuddy /opt/heybuddy

# Install Python dependencies
pip3 install openai flask pydub pygame cryptography

# Configure audio
sudo usermod -a -G audio heybuddy

# Setup systemd service
sudo systemctl enable heybuddy.service
sudo systemctl start heybuddy.service
```

### Configuration Management
- **Environment variables** for sensitive configuration
- **Config file validation** on startup
- **Automatic backup** of user data
- **Remote monitoring** capabilities for troubleshooting

## Performance Optimization

### Memory Management
- **Lazy loading** of audio content
- **Response caching** for common queries
- **Memory limits** for safety (prevent memory leaks)
- **Garbage collection** optimization

### Network Optimization
- **Request batching** where possible
- **Compression** for audio data
- **Connection pooling** for API calls
- **Offline fallback** for common responses

## Monitoring and Maintenance

### Health Monitoring
- **System resource usage** (CPU, memory, disk)
- **API response times** and error rates
- **Audio device status** and quality metrics
- **Network connectivity** and latency

### Logging Strategy
- **Application logs**: Errors, warnings, and audit trail
- **System logs**: Hardware and OS events
- **Performance logs**: Response times and resource usage
- **Security logs**: Authentication attempts and blocked content

### Update Mechanism
- **Automatic security updates** for OS
- **Controlled application updates** with rollback capability
- **Content library updates** for offline stories/songs
- **Configuration sync** with companion app

This architecture provides a secure, scalable, and maintainable foundation for running heyBuddy on Raspberry Pi 5 with the Anker PowerConf S330, ensuring child safety while delivering a rich interactive experience.