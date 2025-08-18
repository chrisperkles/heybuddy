# 🤖 heyBuddy - Comprehensive Technical Documentation

**Ein vollständiger Leitfaden für Installation, Entwicklung und Wartung des deutschen KI-Begleiters für Kinder**

---

## 📖 Dokumentations-Übersicht

Diese umfassende Dokumentation erklärt alle Aspekte von heyBuddy - vom technischen Aufbau bis zur praktischen Nutzung.

---

## 🏗️ System-Architektur

### Überblick
heyBuddy ist eine modulare, Python-basierte Anwendung, die auf Raspberry Pi 5 läuft und sichere KI-Interaktionen für deutsche Kinder bereitstellt.

```
┌─────────────────────────────────────────────────────────────┐
│                    heyBuddy Architecture                    │
├─────────────────────────────────────────────────────────────┤
│  Web Dashboard (German)    │    Debug Dashboard             │
│  - Eltern Interface        │    - Entwickler Tools          │
│  - Real-time Monitoring    │    - System Monitoring         │
│  - Alerts & Notifications  │    - Remote Debugging          │
├─────────────────────────────────────────────────────────────┤
│                    FastAPI REST API                         │
│  /conversation/* │ /debug/* │ /health │ WebSocket /ws/*     │
├─────────────────────────────────────────────────────────────┤
│     German AI Core        │      Safety & Moderation       │
│  - Deutsche Prompts       │   - German Content Filter      │
│  - Cultural Context       │   - Emotional Support          │
│  - Story Generation       │   - OpenAI Moderation          │
├─────────────────────────────────────────────────────────────┤
│  Audio System             │         Database                │
│  - PowerConf S330         │   - SQLite Local Storage       │
│  - Mock for Development   │   - Encrypted Conversations    │
│  - Real-time Processing   │   - Metadata Only Approach     │
├─────────────────────────────────────────────────────────────┤
│              System Services (systemd)                      │
│  - heybuddy.service       │  - heybuddy-updater.service    │
│  - Auto-restart           │  - OTA Updates                 │
│  - Health Monitoring      │  - Rollback Capability         │
└─────────────────────────────────────────────────────────────┘
```

### Core-Komponenten

#### 1. German AI System (`src/core/german_ai.py`)
```python
class GermanContentFilter:
    """Deutsche Inhaltsfilterung mit kulturellem Kontext"""
    
    BLOCKED_TOPICS = [
        "Gewalt", "Waffen", "Tod", "Monster", "Horror",
        "Erwachsenenthemen", "Politik", "Drogen", "Alkohol"
    ]
    
    EMOTIONAL_KEYWORDS = [
        "traurig", "ängstlich", "wütend", "einsam", 
        "frustriert", "verzweifelt", "beunruhigt"
    ]
    
    SAFE_TOPICS = {
        "young": ["Tiere", "Märchen", "Spielzeug", "Familie"],
        "school": ["Hausaufgaben", "Sport", "Freunde", "Hobbys"]
    }

class GermanAIPersona:
    """Deutsche KI-Persönlichkeiten für verschiedene Altersgruppen"""
    
    @staticmethod
    def get_german_system_prompt(age: int, context: str) -> str:
        """Generiert altersgerechte deutsche System-Prompts"""
        base = """Du bist heyBuddy, ein freundlicher KI-Begleiter 
        für deutsche Kinder. Du verwendest deutsche Kultur-Referenzen,
        Märchen und Traditionen."""
        
        if age <= 6:
            return base + """Verwende sehr einfache deutsche Wörter.
            Beziehe Kinderlieder und Märchen ein."""
        else:
            return base + """Hilf bei deutschen Hausaufgaben.
            Diskutiere deutsche Traditionen."""
```

#### 2. Audio Pipeline (`src/core/audio.py`)
```python
class AudioManager:
    """Audio-Verarbeitung mit Hardware-Abstraktion"""
    
    def __init__(self, device_type: str = "auto"):
        if device_type == "powerconf":
            self.device = PowerConfS330Device()
        elif device_type == "mock":
            self.device = MockAudioDevice()  # Für Entwicklung
        else:
            self.device = self._detect_audio_device()
    
    async def record_audio(self, duration: float = 5.0) -> bytes:
        """Nimmt Audio auf und gibt PCM-Daten zurück"""
        
    async def play_audio(self, audio_data: bytes):
        """Spielt Audio-Daten ab"""
        
    async def is_device_available(self) -> bool:
        """Prüft Hardware-Verfügbarkeit"""
```

#### 3. Safety System (`src/core/safety.py`)
```python
class SafetyManager:
    """Multi-Layer Sicherheitssystem"""
    
    async def validate_interaction(
        self, 
        user_id: str, 
        content: str, 
        age: int
    ) -> Dict[str, Any]:
        """Validiert Benutzer-Interaktionen"""
        
        # 1. OpenAI Moderation API
        moderation = await self.moderate_content(content)
        
        # 2. German Content Filter  
        german_check = self.german_filter.check_appropriateness(content, age)
        
        # 3. Emotional Support Detection
        emotional_state = self.detect_emotional_distress(content)
        
        # 4. Parent Notification
        if emotional_state["needs_support"]:
            await self.notify_parents(user_id, emotional_state)
            
        return {
            "safe": moderation["safe"] and german_check["safe"],
            "emotional_support_needed": emotional_state["needs_support"],
            "blocked_reasons": [...]
        }
```

#### 4. Database System (`src/database/local_db.py`)
```python
class LocalDatabase:
    """DSGVO-konforme lokale Datenhaltung"""
    
    def __init__(self):
        self.encryption = EncryptionManager()
        self.db_path = settings.database_url
    
    async def store_conversation(
        self, 
        user_id: str, 
        conversation_data: Dict[str, Any]
    ):
        """Speichert Gespräche verschlüsselt"""
        
        # Nur Metadaten speichern, nicht Inhalte
        metadata = {
            "user_id": user_id,
            "timestamp": datetime.now(),
            "topic_summary": conversation_data["topics"],
            "emotional_indicators": conversation_data["emotions"],
            "safety_flags": conversation_data["safety"]
        }
        
        encrypted_data = self.encryption.encrypt(json.dumps(metadata))
        await self.save_to_sqlite(encrypted_data)
```

---

## 🔧 Installation & Setup

### Komplette Installation auf Raspberry Pi

#### Schritt 1: System Vorbereitung
```bash
# System aktualisieren
sudo apt update && sudo apt upgrade -y

# Grundlegende Abhängigkeiten
sudo apt install -y \
    python3 python3-pip python3-venv \
    git curl wget \
    sqlite3 \
    portaudio19-dev \
    alsa-utils \
    systemd

# Benutzer für heyBuddy erstellen
sudo useradd -r -s /bin/false -d /opt/heybuddy heybuddy
sudo mkdir -p /opt/heybuddy
sudo chown heybuddy:heybuddy /opt/heybuddy
```

#### Schritt 2: Audio Hardware Setup
```bash
# PowerConf S330 USB Audio Device konfigurieren
# Gerät anschließen und erkennen
lsusb | grep -i anker

# ALSA Konfiguration
cat > ~/.asoundrc << EOF
pcm.!default {
    type asym
    playback.pcm "powerconf"
    capture.pcm "powerconf"
}

pcm.powerconf {
    type hw
    card PowerConf
}
EOF

# Audio-Test
arecord -D powerconf -d 5 test.wav
aplay -D powerconf test.wav
```

#### Schritt 3: heyBuddy Installation
```bash
# Als heybuddy user
sudo -u heybuddy -i

# Repository klonen
cd /opt/heybuddy
git clone https://github.com/chrisperkles/heybuddy.git .

# Python Environment
python3 -m venv venv
source venv/bin/activate

# Dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### Schritt 4: Konfiguration
```bash
# Konfigurationsdatei erstellen
cp .env.example .env

# OpenAI API Key setzen
nano .env
# OPENAI_API_KEY=your-openai-api-key-here
# LANGUAGE=de
# AUDIO_DEVICE=powerconf
```

#### Schritt 5: Systemd Services
```bash
# Services installieren
sudo cp config/systemd/heybuddy.service /etc/systemd/system/
sudo cp config/systemd/heybuddy-updater.service /etc/systemd/system/
sudo cp config/systemd/heybuddy-updater.timer /etc/systemd/system/

# Services aktivieren
sudo systemctl daemon-reload
sudo systemctl enable heybuddy
sudo systemctl enable heybuddy-updater.timer

# Starten
sudo systemctl start heybuddy
```

#### Schritt 6: Verifizierung
```bash
# Service Status
sudo systemctl status heybuddy

# Health Check
curl http://localhost:8080/health

# Audio Test
python scripts/test-audio.py

# German AI Test
python test_german_ai.py
```

### Entwicklungs-Setup (ohne Hardware)

```bash
# Repository klonen
git clone https://github.com/chrisperkles/heybuddy.git
cd heybuddy

# Virtual Environment
python3 -m venv venv
source venv/bin/activate

# Development Dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Environment für Entwicklung
export ENVIRONMENT=development
export DEBUG=true
export AUDIO_DEVICE=mock
export LANGUAGE=de

# Entwicklungsserver starten
python src/main.py
```

---

## 🎮 Nutzung & Bedienung

### Für Kinder - Grundlegende Interaktion

#### Gespräch starten
```
Kind: "Hallo heyBuddy!"

heyBuddy: "Hallo! Schön, dass du da bist! Ich bin dein 
Freund heyBuddy. Wie geht es dir denn heute?"
```

#### Geschichten hören
```
Kind: "Erzähl mir eine Geschichte!"

heyBuddy: "Gerne! Möchtest du eine Geschichte über mutige 
Tiere hören? Wie wäre es mit den Bremer Stadtmusikanten?"

Kind: "Ja, bitte!"

heyBuddy: "Es war einmal ein Esel, ein Hund, eine Katze 
und ein Hahn. Sie waren alle alt geworden und ihre 
Besitzer wollten sie nicht mehr..."
```

#### Bei Hausaufgaben helfen
```
Kind: "Ich brauche Hilfe bei Mathe"

heyBuddy: "Natürlich helfe ich dir gerne bei Mathe! 
Was für eine Aufgabe hast du denn? Ist es Plus und Minus, 
oder etwas anderes?"

Kind: "Ich soll 15 + 27 rechnen"

heyBuddy: "Das ist eine tolle Aufgabe! Lass uns das 
zusammen machen. Wir nehmen erst die 15, und dann 
zählen wir 27 dazu..."
```

#### Emotionale Unterstützung
```
Kind: "Ich bin heute traurig"

heyBuddy: "Oh, es tut mir leid, dass du traurig bist. 
Das ist ein ganz normales Gefühl, und es ist okay, 
manchmal traurig zu sein. Magst du mir erzählen, 
warum du traurig bist? Manchmal hilft es, darüber 
zu sprechen."

# System erkennt emotionale Belastung und:
# 1. Benachrichtigt Eltern via Dashboard
# 2. Aktiviert empathische Unterstützung
# 3. Schlägt beruhigende Aktivitäten vor
```

### Für Eltern - Dashboard Nutzung

#### Dashboard Zugang
```bash
# IP-Adresse des Raspberry Pi finden
hostname -I

# Dashboard im Browser öffnen
http://192.168.1.xxx:8080
```

#### Funktionen im Eltern-Dashboard

**1. Live-Überwachung**
- Aktueller Gesprächsstatus
- Online/Offline Status des Systems
- Aktive Sitzungsdauer
- Anzahl Nachrichten heute

**2. Emotionale Support Alerts**
```
🚨 Emotionale Unterstützung Geleistet
Kind äußerte: traurig, besorgt
Zeit: 14:23 | Dauer: 5 Minuten
Empfehlung: Gespräch mit Anna über Schule führen
```

**3. Gesprächs-Zusammenfassungen**
```
📊 Heutige Gespräche (3 Sitzungen)
• Themen: Hausaufgaben, Freunde, Märchen
• Emotionen: überwiegend positiv, 1x Unterstützung
• Lernfortschritt: Mathe-Hilfe erfolgreich
```

**4. Ziel-Tracking**
```
🎯 Wochenziele
✅ Täglich Zähne putzen (6/7 Tage)
🔄 3 Bücher lesen (2/3 abgeschlossen)  
✅ Freundlich zu Geschwistern (Woche erfüllt)
```

### Für Entwickler - API & Tools

#### REST API Nutzung
```bash
# Text-Konversation
curl -X POST "http://localhost:8080/conversation/text" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Hallo heyBuddy, mir ist langweilig",
       "user_id": "anna_mueller", 
       "age": 8
     }'

# Response:
{
  "success": true,
  "response": "Oh, dir ist langweilig? Das können wir ändern! 
             Soll ich dir ein Rätsel aufgeben oder möchtest du 
             lieber eine kleine Geschichte hören?",
  "language": "de",
  "emotional_support": {
    "emotional_support_needed": false,
    "emotional_keywords": []
  }
}
```

#### Debug Dashboard Zugang
```bash
# Debug Tools öffnen (nur in development)
http://localhost:8080/debug/

# System-Monitoring via API
curl http://localhost:8080/debug/system | jq .
curl http://localhost:8080/debug/services | jq .
curl http://localhost:8080/debug/network | jq .
```

#### Testing Framework
```bash
# Komplette Test-Suite
python tests/integration/test_pi_deployment.py

# Spezifische Tests
pytest tests/integration/ -k "german"
pytest tests/integration/ -k "audio"  
pytest tests/integration/ -k "safety"

# Performance Tests
pytest tests/performance/ -v
```

---

## 🔒 Sicherheit & Privatsphäre

### DSGVO/GDPR Compliance

#### Datenminimierung
```python
# Nur Metadaten werden gespeichert, nicht Gesprächsinhalte
stored_data = {
    "conversation_id": "uuid4()",
    "user_id": "child_id",
    "timestamp": "2025-01-15T10:30:00Z",
    "duration_minutes": 5,
    "topics": ["hausaufgaben", "freunde"],
    "emotional_indicators": ["positiv"],
    "safety_flags": [],
    "parental_notification": False
}

# Gesprächsinhalte werden NICHT gespeichert
# conversation_content = "..." # NICHT gespeichert!
```

#### Verschlüsselung
```python
class EncryptionManager:
    """AES-256 Verschlüsselung für lokale Daten"""
    
    def __init__(self):
        # Schlüssel wird lokal auf Pi generiert
        self.key = self.load_or_generate_key()
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        """Verschlüsselt Daten mit AES-256"""
        encrypted = self.cipher.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Entschlüsselt Daten"""
        decoded = base64.b64decode(encrypted_data.encode())
        decrypted = self.cipher.decrypt(decoded)
        return decrypted.decode()
```

#### Datenlöschung (Right to Erasure)
```python
async def delete_user_data(self, user_id: str):
    """DSGVO Artikel 17 - Recht auf Löschung"""
    
    # 1. Alle Konversations-Metadaten löschen
    await self.database.execute(
        "DELETE FROM conversations WHERE user_id = ?", 
        (user_id,)
    )
    
    # 2. Benutzer-Profile löschen
    await self.database.execute(
        "DELETE FROM user_profiles WHERE id = ?", 
        (user_id,)
    )
    
    # 3. Logs bereinigen
    await self.cleanup_logs(user_id)
    
    # 4. Bestätigung an Eltern
    return {"deleted": True, "user_id": user_id}
```

### Multi-Layer Content Filtering

#### Layer 1: OpenAI Moderation API
```python
async def moderate_with_openai(self, content: str) -> Dict[str, Any]:
    """OpenAI's professionelle Content-Moderation"""
    response = await self.openai_client.moderations.create(input=content)
    
    return {
        "flagged": response.results[0].flagged,
        "categories": response.results[0].categories,
        "safe": not response.results[0].flagged
    }
```

#### Layer 2: German Cultural Filter
```python
def check_german_appropriateness(self, content: str, age: int) -> Dict:
    """Deutsche kulturelle und sprachliche Filter"""
    
    blocked_words = []
    for word in self.GERMAN_BLOCKED_TOPICS:
        if word.lower() in content.lower():
            blocked_words.append(word)
    
    emotional_keywords = []
    for keyword in self.GERMAN_EMOTIONAL_KEYWORDS:
        if keyword.lower() in content.lower():
            emotional_keywords.append(keyword)
    
    return {
        "safe": len(blocked_words) == 0,
        "blocked_words": blocked_words,
        "emotional_support_needed": len(emotional_keywords) > 0,
        "emotional_keywords": emotional_keywords
    }
```

#### Layer 3: Age-Appropriate Filtering
```python
def validate_age_appropriateness(self, content: str, age: int) -> bool:
    """Altersgerechte Inhaltsvalidierung"""
    
    if age <= 6:
        # Sehr einfache, kindgerechte Themen
        safe_topics = ["tiere", "farben", "spielzeug", "familie"]
        return any(topic in content.lower() for topic in safe_topics)
    
    elif age <= 12:
        # Schulalter - erweiterte Themen
        safe_topics = ["schule", "hausaufgaben", "sport", "hobbys", "freunde"]
        return any(topic in content.lower() for topic in safe_topics)
    
    return True
```

### Emergency Response System

#### Crisis Detection
```python
class EmergencyDetector:
    """Erkennung von Krisensituationen"""
    
    CRISIS_INDICATORS = [
        "niemand liebt mich", "ich will nicht mehr leben",
        "alle hassen mich", "ich bin wertlos", 
        "selbstverletzung", "weglaufen von zuhause"
    ]
    
    async def check_for_crisis(self, content: str, user_id: str) -> Dict:
        """Prüft auf Krisensignale"""
        
        crisis_detected = any(
            indicator in content.lower() 
            for indicator in self.CRISIS_INDICATORS
        )
        
        if crisis_detected:
            # Sofortige Eltern-Benachrichtigung
            await self.notify_parents_immediately(user_id)
            
            # Deutsche Notfall-Kontakte vorschlagen
            emergency_response = """
            Es ist wichtig, dass du mit einem Erwachsenen sprichst.
            
            Du kannst anrufen:
            • Nummer gegen Kummer: 116 111
            • Telefonseelsorge: 0800 111 0 111
            
            Oder sprich mit deinen Eltern, Lehrern oder anderen 
            Erwachsenen, denen du vertraust.
            """
            
            return {
                "crisis_detected": True,
                "emergency_response": emergency_response,
                "parents_notified": True
            }
        
        return {"crisis_detected": False}
```

---

## 🔄 OTA Updates & Wartung

### Over-the-Air Update System

#### Automatische Updates
```python
class OTAUpdater:
    """Sichere Over-the-Air Updates"""
    
    async def check_for_updates(self) -> Optional[Dict]:
        """Prüft GitHub auf neue Releases"""
        
        response = await aiohttp.get(
            f"https://api.github.com/repos/chrisperkles/heybuddy/releases/latest"
        )
        
        if response.status == 200:
            release = await response.json()
            latest_version = release["tag_name"].lstrip("v")
            
            if self.is_newer_version(latest_version, self.current_version):
                return {
                    "version": latest_version,
                    "download_url": release["tarball_url"],
                    "release_notes": release["body"],
                    "published_at": release["published_at"]
                }
        
        return None
    
    async def perform_update(self) -> Dict[str, Any]:
        """Führt kompletten Update-Prozess durch"""
        
        # 1. Health Check vor Update
        if not await self.pre_update_health_check():
            return {"success": False, "error": "System nicht bereit"}
        
        # 2. Download und Verifikation
        update_file = await self.download_and_verify_update()
        
        # 3. Backup erstellen
        backup_path = await self.create_backup()
        
        # 4. Update anwenden
        await self.apply_update(update_file)
        
        # 5. System testen
        if await self.test_updated_system():
            # Update erfolgreich
            await self.cleanup_old_backups()
            return {"success": True, "version": new_version}
        else:
            # Rollback bei Problemen
            await self.rollback_to_backup(backup_path)
            return {"success": False, "error": "Update failed, rolled back"}
```

#### Update-Prozess Schritt für Schritt

**1. Automatischer Update-Check (täglich)**
```bash
# Systemd Timer führt Update-Check aus
sudo systemctl status heybuddy-updater.timer

# Manuelle Prüfung
/opt/heybuddy/scripts/check-updates.sh
```

**2. Update-Download und Verifikation**
```bash
# Download von GitHub Release
curl -L https://api.github.com/repos/chrisperkles/heybuddy/tarball/v0.2.0 -o update.tar.gz

# Verifikation der Integrität
tar -tzf update.tar.gz > /dev/null
```

**3. Backup-Erstellung**
```bash
# Vollständiges Backup der aktuellen Installation
cp -r /opt/heybuddy /opt/heybuddy.backup.$(date +%Y%m%d_%H%M%S)

# Backup-Metadaten
echo '{"version": "0.1.0", "created": "2025-01-15T10:00:00Z"}' > backup_info.json
```

**4. Update-Anwendung**
```bash
# Service stoppen
sudo systemctl stop heybuddy

# Update extrahieren und anwenden  
tar -xzf update.tar.gz -C /tmp/heybuddy-update --strip-components=1
rsync -av --exclude=data --exclude=logs /tmp/heybuddy-update/ /opt/heybuddy/

# Permissions korrigieren
sudo chown -R heybuddy:heybuddy /opt/heybuddy
```

**5. System-Test**
```bash
# Service starten
sudo systemctl start heybuddy

# Health Check
sleep 10
curl -f http://localhost:8080/health || {
    echo "Update failed, rolling back..."
    # Rollback-Prozess
}
```

**6. Rollback bei Problemen**
```bash
# Automatisches Rollback
sudo systemctl stop heybuddy
rm -rf /opt/heybuddy
mv /opt/heybuddy.backup.latest /opt/heybuddy
sudo systemctl start heybuddy
```

### System Monitoring & Maintenance

#### Health Monitoring
```python
class SystemHealthMonitor:
    """Überwacht System-Gesundheit kontinuierlich"""
    
    async def comprehensive_health_check(self) -> Dict:
        """Vollständiger Gesundheits-Check"""
        
        health = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "checks": {}
        }
        
        # 1. Service Status
        health["checks"]["services"] = await self.check_services()
        
        # 2. System Resources
        health["checks"]["resources"] = await self.check_resources()
        
        # 3. Audio Hardware
        health["checks"]["audio"] = await self.check_audio_hardware()
        
        # 4. Network Connectivity
        health["checks"]["network"] = await self.check_connectivity()
        
        # 5. Database Integrity
        health["checks"]["database"] = await self.check_database()
        
        # 6. AI API Availability
        health["checks"]["openai"] = await self.check_openai_api()
        
        # Gesamtstatus bestimmen
        failed_checks = [
            name for name, check in health["checks"].items() 
            if not check.get("healthy", True)
        ]
        
        if failed_checks:
            health["overall_status"] = "degraded" if len(failed_checks) < 3 else "unhealthy"
            health["failed_checks"] = failed_checks
        
        return health
```

#### Automated Maintenance Tasks
```bash
# Tägliche Maintenance (Cron Job)
#!/bin/bash
# /etc/cron.daily/heybuddy-maintenance

set -e

echo "[$(date)] Starting heyBuddy daily maintenance"

# 1. Log Rotation
find /opt/heybuddy/logs -name "*.log" -size +100M -exec logrotate {} \;

# 2. Database Optimization
sqlite3 /opt/heybuddy/data/heybuddy.db "VACUUM; ANALYZE;"

# 3. Cleanup Old Backups (keep last 7)
find /opt/heybuddy.backups -maxdepth 1 -type d -name "backup_*" \
     -mtime +7 -exec rm -rf {} \;

# 4. System Resource Check
MEMORY_USAGE=$(free | awk '/^Mem:/{printf("%.2f"), $3/$2*100}')
if (( $(echo "$MEMORY_USAGE > 90" | bc -l) )); then
    echo "WARNING: High memory usage: ${MEMORY_USAGE}%"
    systemctl restart heybuddy
fi

# 5. Health Check & Notification
curl -f http://localhost:8080/debug/health > /tmp/health.json
if ! jq -e '.overall_status == "healthy"' /tmp/health.json; then
    echo "WARNING: System health check failed"
    # Send notification to admin
fi

echo "[$(date)] Maintenance completed"
```

---

## 🧪 Testing & Quality Assurance

### Comprehensive Test Suite

#### Integration Tests
```python
class TestGermanAIIntegration:
    """Tests für deutsche KI-Integration"""
    
    @pytest.mark.asyncio
    async def test_german_conversation_flow(self):
        """Testet kompletten deutschen Gesprächsablauf"""
        
        ai_client = AIClient(language="de")
        await ai_client.initialize()
        
        # Test 1: Begrüßung
        result = await ai_client.process_conversation(
            user_input="Hallo heyBuddy!",
            user_id="test_kind",
            age=8
        )
        
        assert result["success"] is True
        assert result["language"] == "de"
        assert "hallo" in result["response"].lower()
        
        # Test 2: Emotionale Unterstützung
        result = await ai_client.process_conversation(
            user_input="Ich bin heute sehr traurig",
            user_id="test_kind", 
            age=8
        )
        
        assert result["success"] is True
        assert result.get("emotional_support", {}).get("emotional_support_needed") is True
        assert "traurig" in result["emotional_support"]["emotional_keywords"]
        
        # Test 3: Unangemessene Inhalte blockieren
        result = await ai_client.process_conversation(
            user_input="Erzähl mir von Gewalt",
            user_id="test_kind",
            age=8
        )
        
        assert result["success"] is False
        assert "german_inappropriate" in result.get("error", "")
        
        await ai_client.cleanup()
```

#### Performance Tests
```python
class TestPerformanceConstraints:
    """Performance-Tests für Raspberry Pi Limits"""
    
    @pytest.mark.asyncio
    async def test_conversation_response_time(self):
        """Testet Antwortzeiten unter Pi-Bedingungen"""
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8080/conversation/text",
                json={
                    "message": "Hallo heyBuddy!",
                    "user_id": "performance_test",
                    "age": 8
                }
            ) as response:
                assert response.status == 200
                data = await response.json()
                
        end_time = time.time()
        response_time = end_time - start_time
        
        # Antwortzeit sollte unter 8 Sekunden auf Pi sein
        assert response_time < 8.0, f"Response too slow: {response_time:.2f}s"
        assert data["success"] is True
    
    @pytest.mark.asyncio  
    async def test_memory_stability(self):
        """Testet Speicher-Stabilität bei mehreren Gesprächen"""
        
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # 20 Gespräche simulieren
        ai_client = AIClient(language="de")
        await ai_client.initialize()
        
        for i in range(20):
            await ai_client.process_conversation(
                user_input=f"Test Nachricht Nummer {i}",
                user_id="memory_test",
                age=8
            )
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        # Speicherverbrauch sollte nicht um mehr als 50MB steigen
        assert memory_increase < 50, f"Memory leak detected: +{memory_increase:.1f}MB"
        
        await ai_client.cleanup()
```

#### Audio System Tests
```python
class TestAudioPipeline:
    """Tests für Audio-Verarbeitung"""
    
    @pytest.mark.asyncio
    async def test_powerconf_s330_integration(self):
        """Testet PowerConf S330 Audio-Hardware"""
        
        if os.getenv("AUDIO_DEVICE") == "mock":
            pytest.skip("Mock audio device in use")
        
        audio_manager = AudioManager(device_type="powerconf")
        await audio_manager.initialize()
        
        # Test 1: Hardware Detection
        assert await audio_manager.is_device_available() is True
        
        # Test 2: Audio Recording
        audio_data = await audio_manager.record_audio(duration=2.0)
        assert len(audio_data) > 0
        assert isinstance(audio_data, bytes)
        
        # Test 3: Audio Playback
        await audio_manager.play_audio(audio_data)
        
        # Test 4: Audio Quality Check
        sample_rate = audio_manager.get_sample_rate()
        assert sample_rate >= 16000, "Sample rate too low"
        
        await audio_manager.cleanup()
```

### Automated Testing Pipeline
```bash
# Komplettes Test-Suite ausführen
#!/bin/bash
# scripts/run-all-tests.sh

set -e

echo "🧪 Starting heyBuddy Test Suite..."

# 1. Unit Tests
echo "Running unit tests..."
python -m pytest tests/unit/ -v --tb=short

# 2. Integration Tests  
echo "Running integration tests..."
python -m pytest tests/integration/ -v --tb=short --asyncio-mode=auto

# 3. German Language Tests
echo "Testing German AI functionality..."
python test_german_ai.py

# 4. Performance Tests
echo "Running performance tests..."
python -m pytest tests/performance/ -v --tb=short

# 5. API Tests
echo "Testing API endpoints..."
python -m pytest tests/api/ -v --tb=short

# 6. Security Tests
echo "Running security tests..."
python -m pytest tests/security/ -v --tb=short

# 7. Hardware Tests (if not mock)
if [ "$AUDIO_DEVICE" != "mock" ]; then
    echo "Testing hardware integration..."
    python -m pytest tests/hardware/ -v --tb=short
fi

echo "✅ All tests completed successfully!"

# Test Summary
echo "📊 Test Summary:"
pytest --collect-only -q | grep "test session starts" -A 10
```

---

## 🔍 Debug & Monitoring Tools

### Real-time Debug Dashboard

#### System Monitoring Interface
Das Debug Dashboard (`http://pi-ip:8080/debug/`) bietet:

**1. Live System Metrics**
```javascript
// Echtzeit-Systemdaten
{
  "cpu": {
    "usage_percent": 23.5,
    "temperature_celsius": 45.2,
    "cores": 4,
    "frequency_mhz": 1800
  },
  "memory": {
    "total_gb": 8.0,
    "used_percent": 67.3,
    "available_gb": 2.6
  },
  "disk": {
    "total_gb": 64.0,
    "used_percent": 45.8,
    "free_gb": 34.7
  }
}
```

**2. Service Status Monitoring**
```javascript
// Service-Status Überwachung
{
  "heybuddy": {
    "active": true,
    "status": "running", 
    "uptime": "2 days, 14 hours",
    "memory_usage": "156MB",
    "restart_count": 0
  },
  "heybuddy-updater": {
    "active": true,
    "last_check": "2025-01-15T06:00:00Z",
    "next_check": "2025-01-16T06:00:00Z"
  }
}
```

**3. Live Log Streaming**
```bash
# WebSocket-basiertes Log Streaming
[2025-01-15 14:30:15] INFO - New conversation started: user=anna_mueller
[2025-01-15 14:30:18] INFO - German AI response generated successfully
[2025-01-15 14:30:20] INFO - Emotional support detected: keywords=[traurig]
[2025-01-15 14:30:20] INFO - Parent notification sent via WebSocket
[2025-01-15 14:30:22] INFO - Conversation ended: duration=2min safety=ok
```

#### Remote Debugging Commands
```bash
# System Health Check
curl http://pi-ip:8080/debug/snapshot | jq .

# Service Management
curl -X POST http://pi-ip:8080/debug/services/heybuddy/restart

# Network Diagnostics  
curl http://pi-ip:8080/debug/network | jq .connectivity

# Performance Metrics
curl http://pi-ip:8080/debug/system | jq '.cpu, .memory'

# Database Status
curl http://pi-ip:8080/debug/database | jq .
```

### Log Analysis Tools

#### Structured Logging
```python
# Strukturierte Log-Ausgaben für bessere Analyse
import structlog

logger = structlog.get_logger()

# Conversation Logging
logger.info(
    "conversation_completed",
    user_id="anna_mueller",
    duration_seconds=120,
    message_count=8,
    topics=["hausaufgaben", "freunde"],
    emotional_support_provided=True,
    safety_flags=[],
    language="de"
)

# Performance Logging
logger.info(
    "ai_response_generated", 
    response_time_ms=2340,
    token_count=87,
    model="gpt-4",
    language="de",
    content_filtered=False
)

# Error Logging
logger.error(
    "audio_device_error",
    device_type="powerconf",
    error_code="DEVICE_NOT_FOUND",
    suggested_action="check_usb_connection"
)
```

#### Log Analysis Scripts
```bash
# Fehler-Analyse
#!/bin/bash
# scripts/analyze-errors.sh

LOGFILE="/opt/heybuddy/logs/app.log"

echo "🔍 heyBuddy Error Analysis"
echo "========================="

# Top Fehler der letzten 24h
echo "Most common errors (last 24h):"
grep "ERROR" $LOGFILE | grep "$(date -d '24 hours ago' '+%Y-%m-%d')" | \
    awk '{print $4}' | sort | uniq -c | sort -nr | head -10

# Audio-Probleme
echo -e "\nAudio device issues:"
grep -i "audio\|powerconf" $LOGFILE | grep "ERROR\|WARNING" | tail -10

# German AI Probleme  
echo -e "\nGerman AI issues:"
grep -i "german\|deutsch" $LOGFILE | grep "ERROR\|WARNING" | tail -10

# Performance Warnungen
echo -e "\nPerformance warnings:"
grep -i "slow\|timeout\|memory" $LOGFILE | grep "WARNING" | tail -10
```

---

## 📱 Mobile & Web Interfaces

### Progressive Web App (PWA)
```html
<!-- manifest.json für Mobile App Experience -->
{
  "name": "heyBuddy Eltern Dashboard",
  "short_name": "heyBuddy",
  "description": "Überwachung und Kontrolle des KI-Begleiters",
  "start_url": "/",
  "display": "standalone",
  "theme_color": "#2563eb",
  "background_color": "#ffffff",
  "icons": [
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    }
  ]
}
```

### Responsive Design Features
```css
/* Mobile-optimierte Dashboard-Elemente */
@media (max-width: 768px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .metric-cards {
    flex-direction: column;
  }
  
  .conversation-alerts {
    position: fixed;
    bottom: 20px;
    left: 20px;
    right: 20px;
    z-index: 1000;
  }
}

/* Touch-optimierte Bedienelemente */
.touch-button {
  min-height: 44px;
  min-width: 44px;
  padding: 12px;
  border-radius: 8px;
}
```

### Push Notifications
```javascript
// Service Worker für Push Notifications
self.addEventListener('push', function(event) {
  const data = event.data.json();
  
  if (data.type === 'emotional_support') {
    const options = {
      body: `${data.child_name} benötigt emotionale Unterstützung: ${data.keywords.join(', ')}`,
      icon: '/icons/support-icon.png',
      badge: '/icons/badge.png',
      tag: 'emotional-support',
      requireInteraction: true,
      actions: [
        {
          action: 'view',
          title: 'Dashboard öffnen'
        },
        {
          action: 'dismiss', 
          title: 'Schließen'
        }
      ]
    };
    
    event.waitUntil(
      self.registration.showNotification('heyBuddy - Unterstützung benötigt', options)
    );
  }
});
```

---

## 🌍 Internationalization & Localization

### German Language Implementation

#### Cultural Context Integration
```python
GERMAN_CULTURAL_CONTEXT = {
    "fairy_tales": [
        "Bremer Stadtmusikanten", "Rotkäppchen", "Hänsel und Gretel",
        "Aschenputtel", "Dornröschen", "Schneewittchen", "Froschkönig"
    ],
    "traditions": [
        "Weihnachten", "Ostern", "Sankt Martin", "Nikolaus",
        "Karneval", "Oktoberfest", "Advent", "Schultüte"
    ],
    "songs": [
        "Alle meine Entchen", "Backe backe Kuchen", "Ein Männlein steht im Walde",
        "Hänschen klein", "Hoppe hoppe Reiter", "Schlaf Kindlein schlaf"
    ],
    "values": [
        "Freundlichkeit", "Hilfsbereitschaft", "Ehrlichkeit", 
        "Respekt", "Teamwork", "Geduld"
    ]
}
```

#### Regional Adaptations
```python
class GermanRegionalSupport:
    """Unterstützung für verschiedene deutsche Regionen"""
    
    REGIONAL_VARIATIONS = {
        "DE": {  # Deutschland
            "emergency_numbers": ["110", "112", "116 111"],
            "school_system": "grundschule_gymnasium",
            "holidays": ["Tag der Deutschen Einheit"]
        },
        "AT": {  # Österreich  
            "emergency_numbers": ["133", "144", "147"],
            "school_system": "volksschule_gymnasium", 
            "holidays": ["Nationalfeiertag"]
        },
        "CH": {  # Schweiz
            "emergency_numbers": ["117", "144", "147"],
            "school_system": "primarschule_gymnasium",
            "holidays": ["Bundesfeiertag"]
        }
    }
```

---

## 💡 Advanced Features & Extensions

### Future Roadmap Implementation

#### 1. Voice Training & Personalization
```python
class VoicePersonalization:
    """Personalisierte Stimm-Erkennung und -Ausgabe"""
    
    async def train_voice_profile(self, user_id: str, audio_samples: List[bytes]):
        """Trainiert personalisiertes Stimm-Profil"""
        
    async def generate_personalized_voice(self, text: str, user_id: str) -> bytes:
        """Generiert personalisierte Sprachausgabe"""
```

#### 2. Advanced Emotional AI
```python
class AdvancedEmotionalAI:
    """Erweiterte emotionale KI mit Langzeit-Gedächtnis"""
    
    async def analyze_emotional_patterns(self, user_id: str) -> Dict:
        """Analysiert emotionale Muster über Zeit"""
        
    async def provide_proactive_support(self, user_id: str) -> Optional[str]:
        """Bietet proaktive emotionale Unterstützung"""
```

#### 3. Multi-Child Family Support  
```python
class FamilyManager:
    """Verwaltung mehrerer Kinder pro Familie"""
    
    async def manage_sibling_interactions(self, family_id: str):
        """Koordiniert Geschwister-Interaktionen"""
        
    async def generate_family_insights(self, family_id: str) -> Dict:
        """Erstellt Familie-weite Einblicke"""
```

---

## 📞 Support & Community

### Getting Help

#### 1. Self-Diagnosis Tools
```bash
# Automatische Problem-Diagnose
/opt/heybuddy/scripts/diagnose-issues.sh

# Ausgabe:
✅ System Services: All running
❌ Audio Device: PowerConf S330 not detected
✅ Network: Internet connectivity OK  
❌ OpenAI API: Rate limit exceeded
⚠️  Memory: Usage at 85% (consider restart)

Recommendations:
1. Check USB connection for audio device
2. Wait 60 minutes for OpenAI rate limit reset
3. Consider restarting service: sudo systemctl restart heybuddy
```

#### 2. Log Collection for Support
```bash
# Support-Paket erstellen
/opt/heybuddy/scripts/create-support-bundle.sh

# Erstellt support-bundle-2025-01-15.tar.gz mit:
# - System logs (keine Gesprächsinhalte!)
# - Configuration (ohne API keys)
# - Health check results
# - Hardware diagnostics
# - Network connectivity tests
```

#### 3. Community Resources
- **GitHub Discussions**: Allgemeine Fragen und Diskussionen
- **GitHub Issues**: Bug Reports und Feature Requests
- **Wiki**: Community-basierte Dokumentation
- **Discord Server**: Real-time Hilfe und Community

### Contributing Guidelines

#### Code Contributions
```bash
# Development Workflow
git clone https://github.com/chrisperkles/heybuddy.git
cd heybuddy

# Feature Branch
git checkout -b feature/amazing-feature

# Development Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install

# Code & Test
# ... Implementierung ...
pytest tests/
black src/
flake8 src/

# Commit & Push
git commit -m "feat: add amazing feature for German kids"
git push origin feature/amazing-feature

# Pull Request erstellen
```

#### Documentation Contributions
- **Übersetzungen**: Dokumentation in andere Sprachen
- **Tutorials**: Schritt-für-Schritt Anleitungen
- **Best Practices**: Erfahrungsberichte und Optimierungen
- **FAQ**: Häufig gestellte Fragen und Lösungen

---

## ⚖️ Legal & Compliance

### DSGVO/GDPR Compliance Checklist

#### ✅ Datenschutz-Grundsätze
- [x] **Rechtmäßigkeit**: Einverständnis der Eltern erforderlich
- [x] **Zweckbindung**: Daten nur für KI-Begleitung verwendet
- [x] **Datenminimierung**: Nur Metadaten gespeichert, keine Inhalte
- [x] **Richtigkeit**: Mechanismen für Datenkorrektur vorhanden
- [x] **Speicherbegrenzung**: Automatische Löschung alter Daten
- [x] **Sicherheit**: AES-256 Verschlüsselung, lokale Speicherung

#### ✅ Betroffenenrechte
- [x] **Auskunft** (Art. 15): API für Datenauskunft
- [x] **Berichtigung** (Art. 16): Korrektur-Funktionen
- [x] **Löschung** (Art. 17): Vollständige Datenlöschung
- [x] **Einschränkung** (Art. 18): Datenverarbeitung pausieren
- [x] **Übertragbarkeit** (Art. 20): Datenexport-Funktionen
- [x] **Widerspruch** (Art. 21): Service-Deaktivierung

#### ✅ Technische Maßnahmen
- [x] **Pseudonymisierung**: Keine Klarnamen in Logs
- [x] **Verschlüsselung**: AES-256 für lokale Daten
- [x] **Zugriffskontrolle**: Eltern-Dashboard mit Authentifizierung
- [x] **Logging**: DSGVO-konforme Protokollierung
- [x] **Backup**: Verschlüsselte Backups mit Löschfristen

### Impressum & Datenschutzerklärung

#### Datenschutzerklärung (Auszug)
```
DATENSCHUTZERKLÄRUNG für heyBuddy

1. VERANTWORTLICHER
   [Ihre Kontaktdaten hier]

2. DATENVERARBEITUNG
   heyBuddy verarbeitet folgende Daten:
   - Gesprächs-Metadaten (Themen, Dauer, Zeitstempel)
   - Emotionale Indikatoren (zur Sicherheit des Kindes)
   - System-Logs (ohne Gesprächsinhalte)
   
   NICHT verarbeitet werden:
   - Vollständige Gesprächsinhalte
   - Audiodateien (nur temporär zur Verarbeitung)
   - Personenbezogene Details

3. RECHTSGRUNDLAGE
   Art. 6 Abs. 1 lit. a DSGVO (Einwilligung der Eltern)
   Art. 6 Abs. 1 lit. f DSGVO (Schutz des Kindeswohls)

4. IHRE RECHTE
   Sie haben jederzeit das Recht auf:
   - Auskunft über die Datenverarbeitung
   - Berichtigung unrichtiger Daten  
   - Löschung der Daten
   - Einschränkung der Verarbeitung
   - Datenübertragbarkeit
   - Widerspruch gegen die Verarbeitung

   Kontakt: [Datenschutzbeauftragter]
```

---

## 🎓 Training & Education

### Für Eltern: Sicher Nutzung

#### Erste Einrichtung
1. **System-Verständnis**: Wie heyBuddy funktioniert
2. **Sicherheitseinstellungen**: Content-Filter konfigurieren  
3. **Dashboard-Nutzung**: Monitoring und Alerts verstehen
4. **Notfallprotokoll**: Was tun bei emotionalen Krisen

#### Regelmäßige Wartung
1. **Wöchentliche Reviews**: Gesprächs-Zusammenfassungen prüfen
2. **Einstellungen anpassen**: Alter und Interessen aktualisieren
3. **System-Updates**: Automatische Updates überwachen
4. **Backup-Überprüfung**: Datensicherung kontrollieren

### Für Entwickler: Extension Development

#### Plugin-System
```python
class HeyBuddyPlugin:
    """Base class for heyBuddy Extensions"""
    
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
    
    async def on_conversation_start(self, user_id: str, context: Dict):
        """Called when conversation starts"""
        pass
    
    async def on_conversation_end(self, user_id: str, summary: Dict):
        """Called when conversation ends"""
        pass
    
    async def on_emotional_support_needed(self, user_id: str, emotions: List[str]):
        """Called when emotional support is detected"""
        pass

# Beispiel Plugin
class HomeworkHelperPlugin(HeyBuddyPlugin):
    """Plugin für erweiterte Hausaufgaben-Hilfe"""
    
    async def on_conversation_start(self, user_id: str, context: Dict):
        if "hausaufgaben" in context.get("message", "").lower():
            return {
                "enhance_persona": "homework_helper",
                "additional_context": "Focus on German school curriculum"
            }
```

#### API Extensions
```python
# Custom API Endpoints
@router.post("/plugins/{plugin_name}/webhook")
async def plugin_webhook(plugin_name: str, data: Dict):
    """Generic webhook endpoint for plugins"""
    
    plugin = plugin_manager.get_plugin(plugin_name)
    if plugin and plugin.enabled:
        return await plugin.handle_webhook(data)
    
    raise HTTPException(404, f"Plugin {plugin_name} not found")
```

---

## 🔮 Vision & Future

### Long-term Roadmap

#### 2025 - Foundation Year
- ✅ German Language Integration Complete
- ✅ OTA Update System Operational  
- ✅ Debug & Monitoring Tools
- 🔄 Mobile Parent App (PWA)
- 🔄 WhatsApp Integration
- 🔄 Advanced Emotional AI

#### 2026 - Expansion Year  
- 🔮 Multi-Language Support (AT, CH variants)
- 🔮 Teacher Dashboard & School Integration
- 🔮 Offline Mode with Local AI
- 🔮 Hardware Sensors Integration (health monitoring)
- 🔮 Voice Personalization per Child
- 🔮 Advanced Learning Analytics

#### 2027 - Intelligence Year
- 🔮 Custom AI Model Training 
- 🔮 Predictive Emotional Support
- 🔮 Cross-Family Learning Networks
- 🔮 AR/VR Integration for Stories
- 🔮 Advanced Privacy-Preserving Analytics
- 🔮 Open Source Community Ecosystem

### Technical Vision

#### Next-Generation Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                 heyBuddy 2.0 Vision                         │
├─────────────────────────────────────────────────────────────┤
│  AR/VR Interface  │  Mobile Native App  │  Voice-Only Mode  │
├─────────────────────────────────────────────────────────────┤
│              Federated Learning Network                     │
│  Privacy-Preserving ML │ Collective Intelligence │ Insights │
├─────────────────────────────────────────────────────────────┤
│                   Hybrid AI System                          │
│  Local Tiny AI Model │ Cloud AI (Optional) │ Offline Mode   │
├─────────────────────────────────────────────────────────────┤
│               Advanced Sensor Integration                   │
│  Emotion Recognition │ Health Monitoring │ Environmental    │
├─────────────────────────────────────────────────────────────┤
│                     Edge Computing                          │
│  Raspberry Pi 6+ │ AI Accelerator │ Local GPU │ 5G/WiFi 7  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📚 Appendix

### Glossar

**DSGVO**: Datenschutz-Grundverordnung (EU GDPR)  
**OTA**: Over-The-Air Updates  
**PowerConf S330**: Anker USB-Audio-Konferenzgerät  
**Systemd**: Linux Service Manager  
**WebSocket**: Bidirektionale Echtzeit-Kommunikation  
**FastAPI**: Python Web Framework  
**SQLite**: Lokale Dateninbank  
**Raspberry Pi**: Einplatinen-Computer  
**PWA**: Progressive Web App  

### Abkürzungen

**API**: Application Programming Interface  
**AI**: Artificial Intelligence  
**CI/CD**: Continuous Integration/Continuous Deployment  
**CLI**: Command Line Interface  
**CPU**: Central Processing Unit  
**CRUD**: Create, Read, Update, Delete  
**GPIO**: General Purpose Input/Output  
**HTTP**: HyperText Transfer Protocol  
**JSON**: JavaScript Object Notation  
**REST**: Representational State Transfer  
**SSH**: Secure Shell  
**TTS**: Text-to-Speech  
**URL**: Uniform Resource Locator  
**USB**: Universal Serial Bus  
**UUID**: Universally Unique Identifier  
**VM**: Virtual Machine  

### Hardware-Spezifikationen

#### Minimum Requirements
- **Raspberry Pi 4B**: 4GB RAM, 32GB MicroSD
- **Audio**: USB Audio Device oder 3.5mm Jack
- **Netzwerk**: WiFi oder Ethernet
- **Stromversorgung**: 5V/3A USB-C

#### Empfohlene Konfiguration  
- **Raspberry Pi 5**: 8GB RAM, 64GB MicroSD Class 10
- **Audio**: Anker PowerConf S330 USB
- **Netzwerk**: WiFi 6 oder Gigabit Ethernet  
- **Stromversorgung**: Official Pi 5 Power Supply
- **Gehäuse**: Kühlung mit Lüfter für Dauerbetrieb

#### Unterstützte Audio-Hardware
- **Anker PowerConf S330** (empfohlen)
- **Standard USB Audio Devices**
- **Pi HAT Audio Boards** (HiFiBerry, IQAudio)  
- **3.5mm Analog** (eingeschränkte Qualität)

### Software-Dependencies

#### Python Packages (requirements.txt)
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
openai>=1.3.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
sqlalchemy>=2.0.0
aiofiles>=23.0.0
websockets>=12.0
psutil>=5.9.0
aiohttp>=3.9.0
cryptography>=41.0.0
```

#### System Dependencies (apt packages)  
```
python3 python3-pip python3-venv
portaudio19-dev libasound2-dev
sqlite3 curl wget git
systemd alsa-utils
build-essential pkg-config
```

### Network Ports

| Port | Service | Beschreibung |
|------|---------|-------------|
| 8080 | HTTP API | Main application interface |
| 8080 | WebSocket | Real-time parent dashboard |
| 22 | SSH | Remote administration (optional) |
| 80 | HTTP | Web dashboard (production) |
| 443 | HTTPS | Secure web dashboard (production) |

### File System Layout

```
/opt/heybuddy/
├── src/                    # Application source code
├── config/                 # Configuration files  
│   ├── .env               # Environment variables
│   ├── systemd/           # Service definitions
│   └── audio/             # Audio device configs
├── data/                  # Local database & user data
│   ├── heybuddy.db       # SQLite database
│   └── encryption.key    # Local encryption key
├── logs/                  # Application logs
├── scripts/               # Maintenance scripts
├── web_dashboard/         # Web interface files
├── backups/               # OTA update backups
├── venv/                  # Python virtual environment
└── tmp/                   # Temporary files
```

---

**© 2025 heyBuddy Project | Made with ❤️ for German families**

*Diese Dokumentation wird kontinuierlich aktualisiert. Letzte Aktualisierung: Januar 2025*