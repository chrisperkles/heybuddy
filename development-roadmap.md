# heyBuddy Development Roadmap

## Phase 1: Foundation & Local Development (Week 1-2)

### 1.1 Project Structure Setup
```
heybuddy/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── audio.py          # Audio processing & device management
│   │   ├── ai_client.py      # OpenAI API integration
│   │   ├── safety.py         # Content moderation & filtering
│   │   └── config.py         # Configuration management
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py           # Flask/FastAPI companion app
│   │   ├── routes.py        # API endpoints
│   │   └── auth.py          # Authentication & security
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py        # SQLite data models
│   │   └── migrations.py    # Database setup
│   ├── services/
│   │   ├── __init__.py
│   │   ├── conversation.py  # Conversation management
│   │   ├── goals.py         # Goal tracking
│   │   └── content.py       # Offline content management
│   └── main.py              # Application entry point
├── tests/
│   ├── unit/
│   ├── integration/
│   └── mocks/               # Mock hardware for testing
├── config/
│   ├── development.yaml
│   ├── production.yaml
│   └── systemd/
│       └── heybuddy.service
├── scripts/
│   ├── install.sh           # Installation script
│   ├── deploy.sh            # Deployment script
│   └── test_audio.py        # Audio testing utilities
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile               # For containerized testing
├── docker-compose.yml       # Local development stack
└── README.md
```

### 1.2 Local Development Strategy (No Pi Required)
- **Audio Mocking**: Use pygame/PyAudio for local audio simulation
- **Hardware Simulation**: Mock PowerConf S330 with system microphone/speakers
- **Docker Environment**: Containerized testing environment
- **Cross-platform**: Works on macOS/Linux/Windows for development

## Phase 2: Core Components (Week 2-3)

### 2.1 Audio Processing Layer
- Mock audio devices for local testing
- Speech recognition pipeline (Whisper API)
- Text-to-speech integration (OpenAI TTS)
- Audio quality monitoring

### 2.2 AI Integration
- OpenAI ChatGPT API client with rate limiting
- Multi-layered content moderation
- Response caching system
- Error handling and fallbacks

### 2.3 Safety Framework
- Input/output sanitization
- Age-appropriate content filtering
- Conversation logging (privacy-compliant)
- Parental override systems

## Phase 3: Data & API Layer (Week 3-4)

### 3.1 Database Implementation
- SQLite schema and models
- User profile management
- Conversation metadata storage
- Goal tracking system

### 3.2 Companion App API
- REST API with Flask/FastAPI
- Authentication and authorization
- Real-time WebSocket updates
- Parental control endpoints

## Phase 4: System Integration (Week 4-5)

### 4.1 Systemd Service
- Service configuration and management
- Auto-restart on failure
- Logging and monitoring
- Resource management

### 4.2 Security Hardening
- API key encryption
- Network security
- Process isolation
- Update mechanisms

## Phase 5: Testing & Deployment (Week 5-6)

### 5.1 Testing Strategy
- Unit tests for all components
- Integration tests with mocked hardware
- Load testing for API endpoints
- Security penetration testing

### 5.2 Deployment Pipeline
- Automated installation scripts
- Configuration management
- Health monitoring
- Rollback capabilities

## Development Workflow

### Local Development (No Hardware)
1. **Use system audio** instead of PowerConf S330
2. **Mock GPIO/hardware** interactions
3. **Docker containers** for isolated testing
4. **Pytest framework** for comprehensive testing
5. **GitHub Actions** for CI/CD

### Hardware Testing (When Pi Available)
1. **Staged deployment** to Raspberry Pi
2. **Hardware-in-the-loop** testing
3. **Performance profiling** on actual hardware
4. **End-to-end integration** testing

## Technical Decisions

### Framework Choices
- **Backend**: Python 3.11+ with asyncio for performance
- **API Framework**: FastAPI (modern, fast, automatic docs)
- **Database**: SQLite (embedded, no server required)
- **Audio**: PyAudio + pygame for cross-platform development
- **Testing**: Pytest + Docker for comprehensive coverage

### Architecture Patterns
- **Dependency Injection**: Easy mocking and testing
- **Event-driven**: Async audio processing
- **Layered Security**: Multiple validation layers
- **Configuration-driven**: Environment-specific settings

## Testing Without Pi Hardware

### 1. Audio Simulation
```python
# Mock audio device for development
class MockAudioDevice:
    def record(self, duration=5):
        # Return test audio file or silence
        return "test_audio.wav"
    
    def play(self, audio_data):
        # Use system speakers
        pygame.mixer.Sound(audio_data).play()
```

### 2. Docker Development Environment
```yaml
# docker-compose.yml
version: '3.8'
services:
  heybuddy:
    build: .
    ports:
      - "8080:8080"
    environment:
      - AUDIO_DEVICE=mock
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data:/app/data
  
  test-audio:
    build: .
    command: python tests/test_audio_pipeline.py
```

### 3. Hardware Abstraction Layer
```python
# Abstract interface for hardware
class AudioInterface:
    def record(self): pass
    def play(self, audio): pass

class PowerConfS330(AudioInterface):
    # Real hardware implementation
    pass

class MockAudioDevice(AudioInterface):
    # Development/testing implementation
    pass
```

## Systemd Integration

### Service Configuration
```ini
[Unit]
Description=heyBuddy AI Companion
After=network.target sound.target
Wants=network.target

[Service]
Type=notify
User=heybuddy
Group=heybuddy
WorkingDirectory=/opt/heybuddy
ExecStart=/opt/heybuddy/venv/bin/python /opt/heybuddy/src/main.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=PYTHONPATH=/opt/heybuddy/src

# Security hardening
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/heybuddy/data

[Install]
WantedBy=multi-user.target
```

### Health Monitoring
```python
# Built-in health checks
class HealthMonitor:
    def __init__(self):
        self.audio_ok = False
        self.api_ok = False
        self.db_ok = False
    
    async def check_health(self):
        # Notify systemd of status
        import systemd.daemon
        if self.all_systems_ok():
            systemd.daemon.notify('READY=1')
        else:
            systemd.daemon.notify('STATUS=Health check failed')
```

## Next Steps to Start Coding

### Immediate Actions:
1. **Create project structure** with proper Python package layout
2. **Set up virtual environment** and dependencies
3. **Implement core configuration** system
4. **Create mock audio interfaces** for development
5. **Build basic OpenAI integration** with safety filters

### Development Environment Setup:
```bash
# Create virtual environment
python3 -m venv heybuddy-env
source heybuddy-env/bin/activate

# Install development dependencies
pip install fastapi uvicorn pytest pytest-asyncio pygame pyaudio openai

# Set up pre-commit hooks for code quality
pip install pre-commit black flake8
pre-commit install
```

This roadmap provides a clear path from local development to production deployment, with testing strategies that don't require Pi hardware and systemd integration for reliable operation.