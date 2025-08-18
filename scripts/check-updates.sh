#!/bin/bash
# heyBuddy OTA Update Check Script
# Runs via systemd timer for automatic updates

set -e

LOG_FILE="/opt/heybuddy/logs/update.log"
PID_FILE="/var/run/heybuddy-update.pid"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if already running
if [ -f "$PID_FILE" ]; then
    if ps -p "$(cat $PID_FILE)" > /dev/null; then
        log "Update check already running (PID: $(cat $PID_FILE))"
        exit 0
    else
        rm -f "$PID_FILE"
    fi
fi

# Create PID file
echo $$ > "$PID_FILE"

# Cleanup on exit
cleanup() {
    rm -f "$PID_FILE"
}
trap cleanup EXIT

log "🔍 Starting heyBuddy update check..."

# Check system health before update
if ! systemctl is-active --quiet heybuddy; then
    log "❌ heyBuddy service is not running, skipping update check"
    exit 1
fi

if ! curl -f -s http://localhost:8080/health > /dev/null; then
    log "❌ heyBuddy health check failed, skipping update check"
    exit 1
fi

log "✅ System health check passed"

# Change to heyBuddy directory
cd /opt/heybuddy

# Activate virtual environment
source venv/bin/activate

# Set Python path
export PYTHONPATH=/opt/heybuddy/src

# Check for updates
log "📡 Checking for updates..."
UPDATE_RESULT=$(python src/services/ota_updater.py --check 2>&1)

if echo "$UPDATE_RESULT" | grep -q "Update available"; then
    NEW_VERSION=$(echo "$UPDATE_RESULT" | grep -o "Update available: [0-9.]*" | cut -d' ' -f3)
    log "🚀 Update available: $NEW_VERSION"
    
    # Check if auto-update is enabled
    if grep -q "AUTO_UPDATE=true" /opt/heybuddy/config/.env 2>/dev/null; then
        log "🔄 Auto-update enabled, starting update process..."
        
        # Perform update
        UPDATE_OUTPUT=$(python src/services/ota_updater.py --update 2>&1)
        
        if echo "$UPDATE_OUTPUT" | grep -q '"success": true'; then
            log "✅ Update to $NEW_VERSION completed successfully"
            
            # Send notification to parents (if WebSocket connected)
            curl -s -X POST http://localhost:8080/api/notify \
                -H "Content-Type: application/json" \
                -d "{\"type\": \"system_update\", \"message\": \"heyBuddy wurde auf Version $NEW_VERSION aktualisiert\"}" \
                > /dev/null || true
        else
            log "❌ Update failed: $UPDATE_OUTPUT"
            
            # Send failure notification
            curl -s -X POST http://localhost:8080/api/notify \
                -H "Content-Type: application/json" \
                -d "{\"type\": \"update_failed\", \"message\": \"Update auf $NEW_VERSION fehlgeschlagen\"}" \
                > /dev/null || true
        fi
    else
        log "📢 Update available but auto-update disabled. Manual update required."
        
        # Notify parents of available update
        curl -s -X POST http://localhost:8080/api/notify \
            -H "Content-Type: application/json" \
            -d "{\"type\": \"update_available\", \"message\": \"heyBuddy Update $NEW_VERSION verfügbar\"}" \
            > /dev/null || true
    fi
else
    log "✅ No updates available - system is up to date"
fi

log "🏁 Update check completed"