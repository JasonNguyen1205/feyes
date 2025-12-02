# Visual AOI Client-Server Architecture

## Overview

The Visual AOI system has been transformed from a monolithic application into a distributed client-server architecture. This new design allows multiple client applications to connect to a central processing server, enabling scalable inspection operations across multiple devices and locations.

## Architecture Components

### 1. API Server (`server/simple_api_server.py`)
- **Purpose**: Central processing hub that handles all inspection logic
- **Technology**: Flask RESTful API with CORS support
- **Features**:
  - Session management with UUID-based sessions
  - Base64 image encoding/decoding
  - Multi-device inspection processing
  - Product configuration management
  - Asynchronous inspection processing
  - Session cleanup and timeout handling

### 2. Client Application (`client/client_app.py`)
- **Purpose**: Local image capture and result display interface
- **Technology**: Tkinter GUI with camera integration
- **Features**:
  - Server connection management
  - Local camera control (TIS cameras)
  - Image capture and transmission
  - Real-time result visualization
  - Device-grouped result display
  - Export functionality

### 3. Test Suite (`test_client_server.py`)
- **Purpose**: Comprehensive API testing and validation
- **Features**:
  - Health check verification
  - Session lifecycle testing
  - Inspection processing validation
  - Performance measurement
  - Error handling verification

## API Endpoints

### Health & Status
- `GET /api/health` - Server health check
- `GET /api/status` - Detailed server status
- `POST /api/initialize` - Initialize AI models and systems

### Product Management
- `GET /api/products` - List available products
- Products loaded from `config/products/*.json`

### Session Management
- `POST /api/session/create` - Create new inspection session
- `GET /api/session/{id}/status` - Get session status  
- `POST /api/session/{id}/close` - Close session
- `GET /api/sessions` - List all active sessions

### Inspection Processing
- `POST /api/session/{id}/inspect` - Run inspection on uploaded image
- Base64 image encoding for transmission
- Returns comprehensive results with ROI details and device summaries

## Multi-Device Support

The system maintains full multi-device inspection capabilities:

### ROI Structure (9-field format)
```python
(idx, type, coords, focus, exposure, ai_threshold, feature_method, rotation, device_location)
```
- Device locations: 1, 2, 3, or 4
- Each device processes its assigned ROIs independently

### Device Results Processing
- **Per-device barcode tracking**: Each device has unique barcode
- **Individual pass/fail determination**: Device passes only if ALL its ROIs pass
- **Grouped result display**: Results organized by device location
- **Device summaries**: Comprehensive statistics per device

### Result Format
```json
{
  "overall_result": {
    "passed": true,
    "total_rois": 8,
    "passed_rois": 8,
    "failed_rois": 0
  },
  "device_summaries": {
    "1": {
      "device_passed": true,
      "total_rois": 4,
      "passed_rois": 4,
      "barcode": "ABC123",
      "results": [...]
    }
  },
  "roi_results": [...],
  "processing_time": 1.23
}
```

## Getting Started

### Prerequisites
- Python 3.8+
- Virtual environment configured
- Required dependencies installed

### Quick Start
```bash
# 1. Start both server and client
./start_client_server.sh

# 2. Start server only
./start_client_server.sh server

# 3. Start client only
./start_client_server.sh client

# 4. Run tests
./start_client_server.sh test
```

### Manual Startup
```bash
# Start API server
python server/simple_api_server.py --host 0.0.0.0 --port 5000

# Start client application
python client/client_app.py

# Run tests
python test_client_server.py
```

## Configuration

### Server Configuration
- Host: Default 0.0.0.0 (all interfaces)
- Port: Default 5000
- Debug mode: Available via --debug flag
- Session timeout: 1 hour (configurable)

### Client Configuration  
- Server URL: Configurable in GUI (default: http://localhost:5000)
- Camera settings: TIS camera support with fallback
- Theme: Integrated with existing Visual AOI theme system
- Export formats: JSON result export

### Product Configuration
Products are loaded from `config/products/*.json`:
```json
{
  "product_name": "sample_product",
  "description": "Sample product configuration",
  "rois": [...],
  "settings": {...}
}
```

## Development & Testing

### Running Tests
The test suite validates all API functionality:
```bash
python test_client_server.py
```

Test coverage includes:
- Server health and initialization
- Product listing and loading
- Session creation and management
- Image inspection processing
- Result validation and formatting
- Error handling and edge cases

### Development Mode
```bash
# Start server in debug mode
python server/simple_api_server.py --debug

# Server auto-reloads on code changes
# Detailed error messages and stack traces
```

### Adding New Features

#### Server-side Extensions
1. Add new endpoints in `simple_api_server.py`
2. Implement business logic in appropriate modules
3. Update API documentation
4. Add corresponding tests

#### Client-side Extensions
1. Modify `client_app.py` GUI components
2. Add API communication methods
3. Update result display logic
4. Test with server integration

## Performance Considerations

### Server Performance
- **Asynchronous Processing**: Inspection runs in simulation mode (1s processing time)
- **Session Management**: Automatic cleanup of expired sessions
- **Memory Management**: Base64 encoding/decoding handled efficiently
- **Concurrent Requests**: Flask threaded mode supports multiple simultaneous inspections

### Client Performance
- **Image Transmission**: JPEG compression with 85% quality
- **UI Responsiveness**: Non-blocking API calls with progress indicators
- **Memory Usage**: Efficient image handling and display scaling
- **Camera Integration**: Optimized TIS camera capture pipeline

### Scalability
- **Horizontal Scaling**: Multiple clients can connect to single server
- **Load Distribution**: Server can handle multiple simultaneous sessions
- **Geographic Distribution**: Clients can be located remotely from server
- **Resource Isolation**: Each session operates independently

## Security Considerations

### API Security
- **CORS Enabled**: Cross-origin requests supported
- **Session Management**: UUID-based session identification
- **Input Validation**: Base64 image data validation
- **Error Handling**: Secure error messages without sensitive information

### Network Security
- **HTTP Protocol**: Currently using HTTP (HTTPS recommended for production)
- **Access Control**: No authentication (should be added for production)
- **Data Transmission**: Base64 encoding for image data

### Deployment Recommendations
- Use HTTPS in production environments
- Implement authentication and authorization
- Add rate limiting for API endpoints
- Configure proper firewall rules
- Use production WSGI server (not Flask development server)

## Troubleshooting

### Common Issues

#### Server Won't Start
- Check port availability: `netstat -tlnp | grep 5000`
- Verify virtual environment: `which python`
- Check dependencies: `pip list | grep flask`

#### Client Can't Connect
- Verify server is running: `curl http://localhost:5000/api/health`
- Check firewall settings
- Confirm server URL in client configuration

#### Inspection Fails
- Check server logs for error details
- Verify image encoding format
- Confirm session is active
- Validate product configuration

#### Performance Issues
- Monitor server resources: CPU, memory usage
- Check network latency between client and server
- Optimize image size and compression
- Review session cleanup frequency

### Debug Mode
Enable detailed logging:
```bash
# Server debug mode
python server/simple_api_server.py --debug

# Client debug mode (check console output)
python client/client_app.py
```

### Log Files
- Server logs: Console output with timestamps
- Client logs: Console output with INFO level
- Error tracking: Detailed stack traces in debug mode

## Migration Guide

### From Monolithic to Client-Server

The transformation maintains full backward compatibility:

1. **ROI Processing**: All existing ROI types supported (compare, barcode, OCR)
2. **Multi-Device Logic**: Complete device location and grouping functionality
3. **UI Components**: Theme system and display logic preserved
4. **Configuration**: Product files and settings remain compatible

### Migration Steps
1. Install new dependencies: `pip install flask flask-cors`
2. Start server: `python server/simple_api_server.py`
3. Use client instead of monolithic app: `python client/client_app.py`
4. Update any external integrations to use REST API

## Future Enhancements

### Planned Features
- **Authentication System**: User login and role-based access
- **Database Integration**: Persistent session and result storage  
- **Real-time Updates**: WebSocket support for live inspection monitoring
- **Load Balancing**: Multiple server instances with load distribution
- **Cloud Deployment**: Docker containers and cloud-native architecture
- **Advanced Analytics**: Historical data analysis and reporting
- **Mobile Client**: Tablet/phone applications for remote monitoring

### Integration Possibilities
- **Enterprise Systems**: ERP/MES integration via REST API
- **Quality Management**: QMS system data exchange
- **Monitoring Tools**: Grafana/Prometheus metrics collection
- **Notification Systems**: Email/SMS alerts for failures
- **File Storage**: Cloud storage for images and results
- **Backup Systems**: Automated backup and disaster recovery

## Conclusion

The client-server architecture provides a robust, scalable foundation for the Visual AOI system. By separating processing logic from user interfaces, the system can now support multiple inspection stations, remote monitoring, and integration with larger manufacturing systems.

The RESTful API design ensures compatibility with future enhancements and third-party integrations, while maintaining all the existing multi-device inspection capabilities that make the Visual AOI system effective for simultaneous quality control across multiple production units.
