# heyBuddy - AI Companion for Learning and Growth

A privacy-first AI companion designed for children's emotional development and learning, deployable on Raspberry Pi 5 with Anker PowerConf S330.

## Quick Start

### Local Development (No Hardware Required)

1. **Clone and Setup**
   ```bash
   git clone <your-repo>
   cd HeyBuddy
   
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

## Raspberry Pi 5 Deployment

### Prerequisites
- Raspberry Pi 5 with Raspberry Pi OS
- Anker PowerConf S330 USB speakerphone
- Internet connection
- OpenAI API key

### Installation

1. **Transfer Files**
   ```bash
   # Copy project to Pi
   scp -r HeyBuddy/ pi@your-pi-ip:~/
   ```

2. **Run Installation Script**
   ```bash
   ssh pi@your-pi-ip
   cd HeyBuddy
   ./scripts/install.sh
   ```

3. **Configure API Key**
   ```bash
   sudo nano /opt/heybuddy/config/.env
   # Set OPENAI_API_KEY=your-key-here
   ```

4. **Start Service**
   ```bash
   sudo systemctl start heybuddy
   sudo systemctl status heybuddy
   ```

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

## API Endpoints

### Health & Status
- `GET /health` - Health check with audio device status
- `GET /status` - Basic system information
- `GET /` - Welcome message and API info

### Audio Testing
- `POST /audio/test` - Test audio recording and playback

### Coming Soon
- `POST /conversation` - Start AI conversation
- `GET /conversations` - List conversation history
- `PUT /settings` - Update user settings
- `GET /goals` - Goal tracking endpoints

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

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes with tests
4. Run tests: `pytest`
5. Submit pull request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Privacy & Safety

heyBuddy is designed with privacy-first principles:
- No data sold to third parties
- GDPR compliant data handling
- Parental controls and oversight
- Regular security audits
- Transparent AI interactions

For questions about privacy or safety, please contact [your-email].