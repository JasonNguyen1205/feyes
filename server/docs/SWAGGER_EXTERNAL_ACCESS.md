# Swagger External Access Configuration

**Date:** October 3, 2025  
**Status:** ✅ Configured for External Access  
**Server IP:** 10.100.10.156  
**Port:** 5000

---

## 🎯 Issue Resolved

**Problem:** Swagger UI was showing `localhost:5000` in curl examples, which doesn't work for external clients.

**Solution:** Removed hardcoded `host` field from Swagger template to allow dynamic hostname resolution based on the browser's current URL.

---

## ✅ Configuration Status

### Server Binding
- ✅ **Binding:** `0.0.0.0:5000` (all network interfaces)
- ✅ **Accessible on:**
  - `http://127.0.0.1:5000` (localhost)
  - `http://10.100.10.156:5000` (network IP)
  - `http://<hostname>:5000` (hostname)

### Firewall Configuration
- ✅ **UFW Status:** Inactive (no blocking)
- ✅ **iptables:** Default ACCEPT policy (no blocking)
- ✅ **Port 5000:** Open for external access

### Swagger Configuration
- ✅ **Host field:** Removed (dynamic resolution)
- ✅ **Swagger UI:** Uses browser's current hostname
- ✅ **OpenAPI Spec:** `"host": null` for dynamic behavior
- ✅ **Schemes:** Both `http` and `https` supported

---

## 🌐 Access URLs

### For Local Access
```
Swagger UI:     http://localhost:5000/apidocs/
OpenAPI Spec:   http://localhost:5000/apispec_1.json
API Endpoints:  http://localhost:5000/api/*
```

### For External Access (LAN)
```
Swagger UI:     http://10.100.10.156:5000/apidocs/
OpenAPI Spec:   http://10.100.10.156:5000/apispec_1.json
API Endpoints:  http://10.100.10.156:5000/api/*
```

### For External Access (Hostname)
```
Swagger UI:     http://<hostname>:5000/apidocs/
OpenAPI Spec:   http://<hostname>:5000/apispec_1.json
API Endpoints:  http://<hostname>:5000/api/*
```

---

## 🔧 Technical Changes

### File: `server/simple_api_server.py`

#### Before (Hardcoded Host)
```python
swagger_template = {
    "swagger": "2.0",
    "info": {...},
    "host": "localhost:5000",  # ❌ Hardcoded localhost
    "basePath": "/",
    "schemes": ["http", "https"]
}
```

#### After (Dynamic Host)
```python
swagger_template = {
    "swagger": "2.0",
    "info": {...},
    # ✅ No host field - Swagger UI uses browser's hostname
    "basePath": "/",
    "schemes": ["http", "https"]
}
```

### How It Works

When the `host` field is not set (or set to `null`), Swagger UI automatically:

1. **Detects the current browser URL** (e.g., `http://10.100.10.156:5000/apidocs/`)
2. **Extracts the hostname and port** (`10.100.10.156:5000`)
3. **Uses that for all API calls** in the "Try it out" feature
4. **Shows correct URLs** in curl examples

This means:
- ✅ If accessed via `localhost` → curl shows `localhost`
- ✅ If accessed via `10.100.10.156` → curl shows `10.100.10.156`
- ✅ If accessed via hostname → curl shows hostname
- ✅ Works automatically for any access method

---

## 🧪 Verification

### 1. Verify Server is Bound to All Interfaces
```bash
# Check server listening addresses
netstat -tuln | grep 5000

# Expected output:
# tcp   0   0 0.0.0.0:5000   0.0.0.0:*   LISTEN
```

### 2. Verify Swagger Spec Has No Hardcoded Host
```bash
# Check OpenAPI spec
curl -s http://localhost:5000/apispec_1.json | jq '.host'

# Expected output:
# null
```

### 3. Verify External Access
```bash
# From another machine on the same network
curl http://10.100.10.156:5000/api/status

# Expected: JSON response with server status
```

### 4. Verify Firewall Status
```bash
# Check UFW status
sudo ufw status

# Expected: Status: inactive (or port 5000 allowed if active)

# Check iptables
sudo iptables -L -n | grep 5000

# Expected: No blocking rules
```

### 5. Test Swagger UI from External Machine
```
1. Open browser on another machine
2. Navigate to: http://10.100.10.156:5000/apidocs/
3. Check curl examples in any endpoint
4. Should show: http://10.100.10.156:5000/api/...
5. Click "Try it out" and "Execute"
6. Should work correctly
```

---

## 📊 Network Configuration

### Server Network Information
```
Hostname:        FVN-ML-001
Primary IP:      10.100.10.156
Server Port:     5000
Binding:         0.0.0.0 (all interfaces)
Firewall:        Inactive (no restrictions)
```

### Network Interfaces
```bash
# Check all network interfaces
ip addr show | grep "inet "

# Output includes:
# inet 127.0.0.1/8 scope host lo (localhost)
# inet 10.100.10.156/24 brd 10.100.27.255 scope global (network)
```

---

## 🔒 Security Considerations

### Current Configuration
- ⚠️ **No Authentication:** API endpoints are publicly accessible
- ⚠️ **No Firewall:** Port 5000 is open to all
- ⚠️ **HTTP Only:** No TLS/SSL encryption (production should use HTTPS)
- ⚠️ **Debug Mode:** Running development server (not production-ready)

### Recommendations for Production

1. **Enable Firewall Rules**
   ```bash
   sudo ufw enable
   sudo ufw allow from 10.100.27.0/24 to any port 5000 comment 'Visual AOI API'
   ```

2. **Add Authentication**
   ```python
   # Add JWT or API key authentication
   from flask_jwt_extended import JWTManager
   
   app.config['JWT_SECRET_KEY'] = 'your-secret-key'
   jwt = JWTManager(app)
   ```

3. **Use Production WSGI Server**
   ```bash
   # Install gunicorn
   pip install gunicorn
   
   # Run with gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 server.simple_api_server:app
   ```

4. **Enable HTTPS**
   ```bash
   # Use nginx as reverse proxy with SSL
   # Or use self-signed certificate for testing
   ```

5. **Rate Limiting**
   ```python
   from flask_limiter import Limiter
   
   limiter = Limiter(app, key_func=get_remote_address)
   ```

---

## 🐛 Troubleshooting

### Issue: Can't Access from External Machine

**Check 1: Server is running**
```bash
ps aux | grep simple_api_server
# Should show running process
```

**Check 2: Port is listening**
```bash
netstat -tuln | grep 5000
# Should show 0.0.0.0:5000 LISTEN
```

**Check 3: Firewall rules**
```bash
sudo ufw status
sudo iptables -L -n
# Check for blocking rules
```

**Check 4: Network connectivity**
```bash
# From external machine
ping 10.100.10.156
# Should respond
```

**Check 5: Test API endpoint**
```bash
# From external machine
curl http://10.100.10.156:5000/api/status
# Should return JSON
```

### Issue: Swagger UI Still Shows localhost

**Solution:** Clear browser cache and reload
```
1. Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R on Mac)
2. Or clear browser cache
3. Close and reopen Swagger UI page
4. Verify apispec_1.json shows "host": null
```

### Issue: "Try it out" Doesn't Work

**Check:** Browser's same-origin policy
```
If Swagger UI is accessed via IP but tries to call localhost:
1. Ensure you're accessing Swagger UI via the same address
2. Use http://10.100.10.156:5000/apidocs/ not localhost
3. Check browser console for CORS errors
```

---

## 📖 Related Documentation

- **[SWAGGER_DOCUMENTATION.md](SWAGGER_DOCUMENTATION.md)** - Complete Swagger guide
- **[SWAGGER_PUBLICATION_SUMMARY.md](SWAGGER_PUBLICATION_SUMMARY.md)** - Publication summary
- **[SCHEMA_API_ENDPOINTS.md](SCHEMA_API_ENDPOINTS.md)** - Schema endpoint details
- **[PROJECT_INSTRUCTIONS.md](PROJECT_INSTRUCTIONS.md)** - Application logic

---

## ✨ Summary

### What Was Fixed
✅ Removed hardcoded `localhost:5000` from Swagger configuration  
✅ Swagger UI now dynamically uses browser's hostname  
✅ Works correctly for local access (`localhost`)  
✅ Works correctly for LAN access (`10.100.10.156`)  
✅ Works correctly for hostname access  
✅ Curl examples show the correct URL automatically  
✅ "Try it out" feature works for external users  

### Current Status
✅ **Server Binding:** 0.0.0.0:5000 (all interfaces)  
✅ **Firewall:** No blocking (port 5000 open)  
✅ **Swagger Config:** Dynamic host resolution  
✅ **Network IP:** 10.100.10.156  
✅ **External Access:** Fully functional  

### Access URLs
- **Local:** http://localhost:5000/apidocs/
- **LAN:** http://10.100.10.156:5000/apidocs/
- **Hostname:** http://FVN-ML-001:5000/apidocs/

All URLs will show correct curl examples matching the access method used!

---

**Status:** ✅ Configured for External Access  
**Updated:** October 3, 2025  
**Tested:** Local and LAN access verified  
**Firewall:** No restrictions on port 5000
