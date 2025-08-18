# 🛒 heyBuddy Hardware Shopping List & Setup Checklist

## 📦 **Required Components**

### **Core Hardware**
- [ ] **Raspberry Pi 5 (4GB or 8GB)** - €70-90
  - 4GB sufficient for most children
  - 8GB recommended for multiple children or heavy usage
  
- [ ] **Anker PowerConf S330 USB Speakerphone** - €130-150
  - 360° voice pickup
  - Excellent echo cancellation
  - USB-A plug & play
  - Alternative: Any USB speakerphone with good pickup

### **Power & Storage**
- [ ] **Official Raspberry Pi 27W USB-C Power Supply** - €8-12
  - Essential for stable operation
  - Don't use phone chargers
  
- [ ] **High-quality MicroSD Card (32GB+ Class 10/U3)** - €10-15
  - SanDisk Extreme or Samsung EVO Select recommended
  - 32GB minimum, 64GB recommended for logs/data

### **Setup Accessories (temporary)**
- [ ] **Micro HDMI to HDMI Cable** - €5-8
  - Only needed for initial setup
  - Can borrow or use existing TV cable
  
- [ ] **USB Keyboard & Mouse** - €15-25
  - Only needed for initial setup
  - Can use existing or borrow

### **Network Connection**
- [ ] **WiFi Access** (built into Pi 5) OR
- [ ] **Ethernet Cable** - €5-10
  - WiFi is usually sufficient
  - Ethernet more reliable if available

## 💰 **Total Cost Breakdown**
- **Minimum Setup**: ~€220-280
- **Recommended Setup**: ~€250-320
- **Monthly OpenAI API**: ~€5-15 (depends on usage)

## 🛍️ **Where to Buy**

### **Germany**
- **Raspberry Pi Official**: https://rpi.org/products/
- **reichelt elektronik**: Complete Pi bundles
- **Amazon DE**: Quick delivery, all components
- **Conrad Electronic**: Local pickup available

### **International**
- **Adafruit**: High-quality components
- **Pimoroni**: Pi specialists with bundles
- **Amazon**: Universal availability

## 🔧 **Assembly Checklist**

### **Before You Start**
- [ ] All components acquired
- [ ] Clean workspace prepared  
- [ ] Have OpenAI account ready
- [ ] Home WiFi password available
- [ ] Phone/computer for dashboard access

### **Physical Setup Order**
1. [ ] Insert MicroSD card into Pi
2. [ ] Connect Anker PowerConf S330 to USB port
3. [ ] Connect HDMI cable to monitor
4. [ ] Connect keyboard and mouse
5. [ ] Connect ethernet cable (optional)
6. [ ] Connect power supply LAST
7. [ ] Pi should boot automatically

### **Software Setup Checklist**
- [ ] Raspberry Pi OS installed and booted
- [ ] Initial setup wizard completed
- [ ] WiFi connected and tested
- [ ] SSH enabled (for remote management)
- [ ] Audio devices detected (PowerConf S330)
- [ ] System updated to latest packages

### **heyBuddy Installation**
- [ ] Quick install script downloaded and run
- [ ] OpenAI API key configured
- [ ] Service started and healthy
- [ ] Dashboard accessible from phone
- [ ] First conversation test successful
- [ ] Audio input/output working

## ⚠️ **Common Issues & Solutions**

### **Power Issues**
- **Problem**: Pi randomly restarts or won't boot
- **Solution**: Use official 27W power supply, check cable quality

### **Audio Issues**
- **Problem**: Anker PowerConf not detected
- **Solution**: Check USB connection, try different port, verify with `lsusb`

### **Network Issues**
- **Problem**: Can't access dashboard from phone
- **Solution**: Ensure phone on same WiFi, find Pi IP with `hostname -I`

### **SD Card Issues**
- **Problem**: Slow performance or corruption
- **Solution**: Use Class 10/U3 card, avoid cheap brands

### **API Issues**
- **Problem**: Conversations not working
- **Solution**: Verify OpenAI API key, check internet connection

## 📱 **Dashboard Access Methods**

### **Local Network** (Same WiFi)
```
http://[PI-IP-ADDRESS]:8080
Example: http://192.168.1.100:8080
```

### **Find Pi IP Address**
```bash
# On Pi terminal
hostname -I

# From another computer on same network
nmap -sn 192.168.1.0/24 | grep -i raspberry
```

### **Mobile App Installation**
1. Open dashboard URL on phone browser
2. Tap "Add to Home Screen" (iOS) or "Install App" (Android)
3. Creates app icon for quick access

## 🎯 **Performance Expectations**

### **Response Times**
- **Local processing**: ~1-2 seconds
- **AI conversation**: ~3-8 seconds (depends on internet)
- **Story generation**: ~5-15 seconds

### **System Resources**
- **Memory usage**: ~500MB-1GB typical
- **CPU usage**: ~10-30% during conversations
- **Storage**: ~2GB for system + logs

### **Battery Life** (if using UPS)
- **Typical consumption**: ~15W
- **With 10000mAh power bank**: ~4-6 hours

## ✅ **Success Indicators**

After setup, you should have:
- [ ] Pi boots automatically when powered
- [ ] heyBuddy service starts automatically
- [ ] Dashboard accessible from phone
- [ ] German conversations working
- [ ] Audio input/output clear
- [ ] Parent monitoring active
- [ ] Over-the-air updates enabled

**🎉 Your child's AI companion is ready to help them learn and grow!**