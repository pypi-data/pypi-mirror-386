# IPC/RPC Testing Tools

**Production-grade load testing and debugging tools for Django-CFG RPC system.**

---

## 🎯 Overview

The IPC app now includes comprehensive testing tools for validating RPC communication between Django and WebSocket servers:

- **Test RPC Client** - Send individual RPC requests with response inspection
- **Load Testing Tool** - Emulate production load with concurrent requests
- **Real-time Monitoring** - Track test progress and performance metrics
- **Beautiful UI** - Tab-based interface with Material Design

---

## 📁 Architecture

### Template Structure

```
templates/django_cfg_ipc/
├── layout/
│   └── base.html                    # Base template with navbar
├── pages/
│   └── dashboard.html               # Main dashboard page
├── components/
│   ├── stat_cards.html              # Statistics overview cards
│   ├── system_status.html           # Redis/Stream health indicators
│   ├── tab_navigation.html          # Tab switcher with badges
│   ├── overview_content.html        # Overview tab content
│   ├── requests_content.html        # Recent requests table
│   ├── notifications_content.html   # Notification statistics
│   ├── methods_content.html         # Method statistics table
│   └── testing_tools.html           # Testing tools tab
├── widgets/
└── partials/
```

### Backend Structure

```
views/
├── __init__.py                      # Exports all viewsets
├── dashboard.py                     # Dashboard view
├── monitoring.py                    # RPCMonitorViewSet
└── testing.py                       # RPCTestingViewSet
```

---

## 🧪 Test RPC Client

### Purpose

Send individual RPC requests for:
- Debugging method implementations
- Validating parameter schemas
- Measuring response times
- Inspecting response payloads

### Features

- **Method Selection**: Dropdown with available RPC methods
- **Timeout Configuration**: 1-60 seconds
- **JSON Parameter Editor**: Syntax-highlighted textarea
- **Response Inspection**: Formatted JSON output
- **Error Handling**: Clear error messages with stack traces

### Usage Example

1. Navigate to **Testing** tab
2. Select RPC method (e.g., `notification.send`)
3. Edit parameters JSON:
   ```json
   {
     "user_id": "test-123",
     "type": "test",
     "title": "Test Notification",
     "message": "This is a test message"
   }
   ```
4. Set timeout (default: 10s)
5. Click **Send Request**
6. Inspect response:
   - Success: Green badge + response JSON
   - Failed: Red badge + error message
   - Duration: Response time in milliseconds

### API Endpoint

```http
POST /cfg/ipc/test/send
Content-Type: application/json

{
  "method": "notification.send",
  "params": {
    "user_id": "test-123",
    "type": "test",
    "title": "Test Notification",
    "message": "Hello"
  },
  "timeout": 10
}
```

**Response:**

```json
{
  "success": true,
  "duration_ms": 45.23,
  "response": {
    "sent": true,
    "message_id": "abc-123"
  },
  "error": null,
  "correlation_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
}
```

---

## 🔥 Load Testing Tool

### Purpose

Emulate production traffic to:
- Validate system performance under load
- Identify bottlenecks
- Test concurrent request handling
- Measure throughput (RPS)

### Features

- **Configurable Volume**: 1-10,000 requests
- **Concurrency Control**: 1-100 concurrent requests
- **Method Selection**: Test any RPC method
- **Real-time Progress**: Progress bar + statistics
- **Live Metrics**:
  - Success/Failed counts
  - Average response time
  - Requests per second (RPS)
  - Elapsed time

### Usage Example

1. Navigate to **Testing** tab → **Load Testing Tool**
2. Configure test parameters:
   - **Total Requests**: 100
   - **Concurrent Requests**: 10
   - **Test Method**: `notification.send`
3. Click **Start Load Test**
4. Monitor progress:
   - Progress bar (0/100 → 100/100)
   - Success: Green counter
   - Failed: Red counter
   - Avg Time: Purple badge (ms)
   - RPS: Purple badge (requests/sec)
5. Click **Stop Test** to abort early (optional)

### API Endpoints

#### Start Load Test

```http
POST /cfg/ipc/test/load/start
Content-Type: application/json

{
  "method": "notification.send",
  "total_requests": 100,
  "concurrency": 10,
  "params": {
    "user_id": "load-test",
    "type": "test"
  }
}
```

**Response:**

```json
{
  "test_id": "abc123ef",
  "started": true,
  "message": "Load test started with 100 requests at 10 concurrency"
}
```

#### Get Load Test Status

```http
GET /cfg/ipc/test/load/status
```

**Response:**

```json
{
  "test_id": "abc123ef",
  "running": true,
  "progress": 45,
  "total": 100,
  "success_count": 43,
  "failed_count": 2,
  "avg_duration_ms": 52.34,
  "elapsed_time": 4.56,
  "rps": 9.87
}
```

#### Stop Load Test

```http
POST /cfg/ipc/test/load/stop
```

**Response:**

```json
{
  "message": "Load test stopped",
  "progress": 45,
  "total": 100
}
```

---

## 📊 Metrics & Statistics

### Real-time Stats

The load testing tool provides 4 live metrics:

| Metric | Description | Color |
|--------|-------------|-------|
| **Success** | Successful RPC calls | Blue |
| **Failed** | Failed RPC calls | Red |
| **Avg Time** | Average response time (ms) | Green |
| **RPS** | Requests per second | Purple |

### Performance Benchmarks

Typical performance on standard hardware:

- **Single Request**: 20-50ms
- **10 Concurrent**: ~30-60ms avg
- **100 Concurrent**: ~50-100ms avg
- **Throughput**: 50-200 RPS (depends on method)

### Error Tracking

Failed requests log:
- Error type (timeout, connection, remote error)
- Error message
- Duration until failure
- Stack trace (in Django logs)

---

## 🔒 Security & Permissions

### Authentication

All testing endpoints require:
- **Django Admin Access**: `IsAdminUser` permission
- **Staff Status**: `request.user.is_staff = True`

### Rate Limiting

To prevent abuse:
- **Max Total Requests**: 10,000 per test
- **Max Concurrency**: 100 simultaneous requests
- **Global Limit**: One active load test at a time

### Safety Features

1. **Thread Isolation**: Load tests run in background threads
2. **Graceful Shutdown**: Stop button terminates test safely
3. **Resource Cleanup**: Daemon threads auto-cleanup on exit
4. **Error Boundaries**: Exceptions don't crash test runner

---

## 🧩 Integration with RPC Logging

All test requests are logged to `RPCLog` model if logging is enabled:

```python
# View logs in Django Admin
/admin/django_cfg_ipc/rpclog/

# Filter by test runs
RPCLog.objects.filter(params___test_id='abc123ef')

# Analyze performance
stats = RPCLog.objects.stats_by_method()
```

Benefits:
- Full request/response history
- Performance metrics per method
- Error analysis
- User attribution

---

## 🎨 UI Components

### Tab Navigation

5 tabs with badge counters:
- **Overview**: System summary
- **Recent Requests**: Last 50 RPC calls
- **Notifications**: Notification statistics
- **Methods**: Method-level stats
- **Testing**: Test tools (new!)

### Testing Tools Tab

Two sections:
1. **RPC Test Client** (top)
2. **Load Testing Tool** (bottom)

### Material Icons

Icons used:
- `send` - Send request
- `science` - Testing tools
- `speed` - Load testing
- `play_arrow` - Start test
- `stop` - Stop test
- `check_circle` - Success
- `error` - Failed

---

## 📝 JavaScript Integration

### API Client Usage

```javascript
// Import generated API client
import { api } from '/static/js/api/index.mjs';

// Send test RPC request
const result = await api.ipcTestSendCreate({
  method: 'notification.send',
  params: { user_id: '123' },
  timeout: 10
});

// Start load test
const test = await api.ipcTestLoadStartCreate({
  method: 'notification.send',
  total_requests: 100,
  concurrency: 10,
  params: {}
});

// Poll status
setInterval(async () => {
  const status = await api.ipcTestLoadStatusRetrieve();
  updateUI(status);
}, 500);

// Stop test
await api.ipcTestLoadStopCreate();
```

### Event Handlers

```javascript
// Send Test Request
document.getElementById('send-test-rpc').addEventListener('click', async () => {
  const method = document.getElementById('test-method').value;
  const params = JSON.parse(document.getElementById('test-params').value);
  const timeout = parseInt(document.getElementById('test-timeout').value);

  const result = await api.ipcTestSendCreate({ method, params, timeout });

  displayResult(result);
});

// Start Load Test
document.getElementById('start-load-test').addEventListener('click', async () => {
  const method = document.getElementById('load-method').value;
  const total_requests = parseInt(document.getElementById('load-total-requests').value);
  const concurrency = parseInt(document.getElementById('load-concurrency').value);

  await api.ipcTestLoadStartCreate({
    method,
    total_requests,
    concurrency,
    params: {}
  });

  startPolling();
});
```

---

## 🚀 Best Practices

### 1. Start Small

Begin with:
- 10 total requests
- 2-5 concurrency
- Simple methods (e.g., `notification.send`)

Gradually increase load.

### 2. Monitor System Resources

Watch for:
- Redis memory usage
- WebSocket server CPU
- Django process count
- Network bandwidth

Use `htop`, `redis-cli INFO`, Docker stats.

### 3. Test in Isolation

Avoid load testing in production during:
- Peak traffic hours
- Active user sessions
- Critical operations

### 4. Analyze Results

After each test:
1. Review RPC logs in admin
2. Check error messages
3. Identify bottlenecks
4. Optimize slow methods

### 5. Cleanup

After testing:
```python
# Delete test logs
RPCLog.objects.filter(params___test_id__isnull=False).delete()

# Clear Redis stream (optional)
# WARNING: Deletes all pending requests!
```

---

## 🐛 Troubleshooting

### Load Test Not Starting

**Symptoms**: 409 Conflict error

**Cause**: Previous test still running

**Fix**:
```http
POST /cfg/ipc/test/load/stop
```

### Timeout Errors

**Symptoms**: All requests timeout

**Causes**:
- WebSocket server not running
- Redis connection issues
- Network problems

**Fix**:
1. Check WebSocket server logs
2. Verify Redis connectivity
3. Test with single request first

### High Failure Rate

**Symptoms**: >50% failed requests

**Causes**:
- Method not implemented
- Invalid parameters
- Server overload

**Fix**:
1. Test method with single request
2. Validate parameter schema
3. Reduce concurrency

---

## 📚 Reference

### Available RPC Methods

| Method | Purpose | Avg Duration |
|--------|---------|--------------|
| `notification.send` | Send notification to user | 20-50ms |
| `notification.broadcast` | Broadcast to all users | 30-80ms |
| `workspace.file_changed` | Notify file change | 15-40ms |
| `session.message` | Send session message | 20-45ms |

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Request processed |
| 400 | Bad Request | Check parameters |
| 409 | Conflict | Stop existing test |
| 500 | Server Error | Check server logs |
| 503 | Service Unavailable | Check Redis/WebSocket |

---

## 🔮 Future Enhancements

Planned features:
- [ ] Test result history
- [ ] Export test reports (CSV/JSON)
- [ ] Custom parameter templates
- [ ] Scheduled load tests
- [ ] Performance regression alerts
- [ ] WebSocket connection testing
- [ ] Stress testing mode (max load)

---

**Status**: ✅ Production Ready
**Django-CFG Version**: 2.0+
**Python Version**: 3.10+
**Last Updated**: 2025-10-23
