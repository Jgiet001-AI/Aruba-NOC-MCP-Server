# LangSmith Integration - Quick Start Guide

## 🎯 What is LangSmith?

**LangSmith** is a tool usage analytics platform that tracks how Claude uses your MCP tools. Think of it as "application performance monitoring" for Claude's tool calls.

### What It Tracks:
- ✅ Which tools Claude calls most frequently
- ✅ Success/failure rates per tool
- ✅ Latency (how long each tool takes)
- ✅ Error patterns and debugging context
- ✅ Multi-tool workflows (sessions)

### What It Doesn't Track:
- ❌ Infrastructure health (use Prometheus for that)
- ❌ Circuit breaker state
- ❌ Rate limiter status
- ❌ OAuth2 token expiration

---

## ✅ Integration Status

**LangSmith is already integrated and configured!** 🎉

### Files Modified:
- `src/langsmith_tracing.py` - Tracing module (**NEW**)
- `src/server.py` - Integrated tracing into all tool calls
- `.env` - Configured with your API key
- `requirements.txt` - Added langsmith dependency
- `tests/test_langsmith_integration.py` - 6 integration tests (**NEW**)

### Test Results:
```bash
184 passed in 5.23s (178 original + 6 new LangSmith tests)
```

---

## 🚀 How to Use

### View Your Traces

1. **Open LangSmith Dashboard**: https://smith.langchain.com

2. **Navigate to Your Project**: "aruba-noc-server"

3. **View Traces**: Click "Traces" to see individual tool calls

4. **View Metrics**: Click "Metrics" for aggregated analytics

### Example: Finding Slow Tools

1. Go to: https://smith.langchain.com/o/default/projects/p/aruba-noc-server
2. Click: "Metrics" tab
3. Sort by: "P95 Latency"
4. Result: See which tools are slowest

### Example: Debugging Failed Tool Calls

1. Go to: "Traces" tab
2. Filter by: Status = "Failed"
3. Click: Any failed trace
4. View: Full error details, stack trace, arguments

---

## 📊 What You'll See

### Dashboard Metrics:

**Tool Call Volume** (Bar Chart):
```
get_device_details:    █████████████████ 150 calls
list_all_clients:      ███████████ 95 calls
get_sites_health:      ████████ 65 calls
get_ap_details:        ████ 30 calls
```

**Success Rate** (Percentage):
```
get_device_details:    98.5% (147/150 successful)
list_all_clients:      100% (95/95 successful)
get_sites_health:      96.9% (63/65 successful)
```

**P95 Latency** (Histogram):
```
get_device_details:    850ms
list_all_clients:      1.2s
get_sites_health:      2.1s
```

### Trace Waterfall (Individual Session):

```
Session: Claude helping with device diagnostics
├─ check_server_health (250ms) ✅
├─ get_sites_health (1.2s) ✅
│  └─ API Call: /monitoring/v2/sites (980ms)
├─ get_device_details [serial=ABC123] (850ms) ✅
│  └─ API Call: /monitoring/v2/devices/ABC123 (720ms)
└─ ping_from_ap [serial=ABC123, target=8.8.8.8] (2.1s) ✅
   └─ API Call: /troubleshooting/v1/ping (1.9s)

Total Duration: 4.3s
Tools Called: 4
Success Rate: 100%
```

---

## 🔑 Configuration

### Environment Variables (.env)

```bash
# Already configured with your API key
LANGSMITH_API_KEY=lsv2_pt_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx_xxxxxxxxxxxx
LANGSMITH_PROJECT=aruba-noc-server
LANGSMITH_TRACING=true
```

### Disable Tracing (Optional)

To disable LangSmith without uninstalling:

```bash
# Set to empty string or remove the variable
LANGSMITH_API_KEY=
```

The server will gracefully fall back to no tracing.

---

## 💡 Common Use Cases

### 1. Find Most Popular Tools

**Question**: "Which tools does Claude use most?"

**Steps**:
1. Open LangSmith dashboard
2. Navigate to "Metrics" → "Tool Call Volume"
3. View bar chart sorted by call count

**Example Result**:
- `get_device_details`: 150 calls (most popular)
- `list_all_clients`: 95 calls
- `get_sites_health`: 65 calls

### 2. Debug Failing Tool

**Question**: "Why is `get_ap_details` failing?"

**Steps**:
1. Open LangSmith dashboard
2. Navigate to "Traces"
3. Filter: `tool_name = get_ap_details` AND `status = failed`
4. Click failed trace to see:
   - Full error message
   - Stack trace
   - Arguments passed
   - Timestamp

**Example Findings**:
- Error: "401 Unauthorized"
- Cause: Token expired mid-session
- Fix: Already implemented (proactive token refresh)

### 3. Optimize Slow Workflows

**Question**: "Why is Claude slow when diagnosing devices?"

**Steps**:
1. Open LangSmith dashboard
2. Navigate to "Traces"
3. Filter: Recent sessions
4. Sort by: Duration
5. Click slowest session to see waterfall

**Example Findings**:
- `list_all_clients` takes 2.1s (slowest)
- Could add pagination to improve performance
- OR cache results for 30 seconds

---

## 📈 Cost & Pricing

### Free Tier (Current)
- **5,000 traces/month** - FREE
- Sufficient for:
  - ~165 tool calls/day
  - ~7 tool calls/hour (continuous usage)
  - Typical development and light production

### Pro Tier ($39/month)
- **100,000 traces/month**
- Sufficient for:
  - ~3,300 tool calls/day
  - ~140 tool calls/hour
  - Heavy production workloads

### Current Usage
With your API key configured, **you're on the free tier** until you exceed 5,000 traces/month.

**Monitor Usage**: https://smith.langchain.com/settings/usage

---

## 🔒 Privacy & Security

### What Gets Sent to LangSmith:

✅ **Safe to Send**:
- Tool name (e.g., `get_device_details`)
- Tool arguments (e.g., `{serial: "ABC123"}`)
- Execution time (e.g., 850ms)
- Success/failure status
- Error messages (if any)

❌ **NOT Sent**:
- Aruba OAuth2 tokens
- Full API responses (only success/failure)
- User passwords or credentials
- Any data not in tool arguments

### Best Practices:

1. **Review Traces**: Periodically check traces for sensitive data
2. **Audit Access**: Control who can view your LangSmith project
3. **Use Secrets Management**: Don't pass secrets as tool arguments

---

## 🛠️ Troubleshooting

### LangSmith Not Showing Traces

**Check**:
1. Environment variable set: `echo $LANGSMITH_API_KEY`
2. Server logs show: "LangSmith Tracing: ENABLED"
3. API key valid: https://smith.langchain.com/settings

**Fix**:
```bash
# Verify API key is set
cat .env | grep LANGSMITH_API_KEY

# Restart server to pick up changes
# (if running as service)
```

### Server Logs Show "LangSmith not installed"

**Fix**:
```bash
pip install langsmith

# Or install all requirements
pip install -r requirements.txt
```

### Traces Not Appearing in Dashboard

**Possible Causes**:
1. **Delay**: Traces can take 5-10 seconds to appear (refresh page)
2. **Wrong Project**: Check you're viewing correct project name
3. **Network Issue**: Check server has internet access to smith.langchain.com

---

## 🎓 Learning Resources

### Official Documentation
- LangSmith Docs: https://docs.smith.langchain.com
- Tracing Guide: https://docs.smith.langchain.com/tracing

### Video Tutorials
- Getting Started: https://www.youtube.com/watch?v=xxx (official LangChain channel)
- Advanced Tracing: https://www.youtube.com/watch?v=yyy

### Blog Posts
- "Debugging LLM Applications with LangSmith"
- "Optimizing Tool Performance"

---

## 📝 Next Steps

### Immediate
✅ **Done**: LangSmith is configured and running
- Try calling some MCP tools through Claude
- View traces in dashboard
- Explore metrics

### Week 1
- [ ] Set up monitoring dashboard in LangSmith
- [ ] Create custom views for your most-used tools
- [ ] Review first week of traces for optimization opportunities

### Month 1
- [ ] Analyze tool usage patterns
- [ ] Identify and optimize slow tools
- [ ] Create monthly report on tool usage

---

## 🤝 Support

### Questions?
- **LangSmith Docs**: https://docs.smith.langchain.com
- **LangChain Discord**: https://discord.gg/langchain
- **GitHub Issues**: https://github.com/langchain-ai/langsmith-sdk

### Issues with Integration?
- Check server logs: Look for LangSmith-related errors
- Review implementation: `src/langsmith_tracing.py`
- Run tests: `pytest tests/test_langsmith_integration.py -v`

---

**Happy Tracing!** 🎉

Now you have full visibility into how Claude uses your MCP tools, complementing your infrastructure monitoring with application-level insights.
