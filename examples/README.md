# 📚 Examples

This directory contains example scripts and code snippets to help you get started with Voice Summary.

## 🚀 Quick Examples

### 1. Simple Data Ingestion
**File**: `simple_ingestion.py`

A basic example showing how to ingest call data via the REST API.

```bash
# Make sure your backend is running
./start_backend.sh

# Run the example
python examples/simple_ingestion.py
```

**What it does:**
- Creates sample call data with realistic conversation turns
- Tests API connectivity
- Ingests sample calls into the system
- Shows how to structure call data

**Use case**: Perfect for testing your setup or learning the API structure.

---

## 🔧 Customization Examples

### Modifying Sample Data

Edit `simple_ingestion.py` to create your own call scenarios:

```python
# Change the conversation content
turns = [
    {
        "role": "AGENT",
        "content": "Your custom agent message here",
        "timestamp": call_time.isoformat()
    },
    {
        "role": "USER", 
        "content": "Your custom user message here",
        "timestamp": (call_time.replace(second=call_time.second + 2)).isoformat()
    }
]

# Add custom metadata
call_data["metadata"]["call_type"] = "sales_call"
call_data["metadata"]["priority"] = "high"
```

### Adding Audio Files

To include audio files with your calls:

```python
# Add S3 audio URL
call_data["audio_file_url"] = "https://your-bucket.s3.amazonaws.com/audio/call_123.mp3"

# Or use local file path (will be uploaded to S3 automatically)
call_data["audio_file_path"] = "/path/to/local/audio.wav"
```

---

## 📡 API Integration Examples

### Using Different HTTP Clients

**Requests (Python)**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/calls/",
    json=call_data,
    headers={"Content-Type": "application/json"}
)
```

**cURL (Command Line)**
```bash
curl -X POST "http://localhost:8000/api/calls/" \
  -H "Content-Type: application/json" \
  -d '{"call_id": "test_001", "transcript": {...}}'
```

**JavaScript/Node.js**
```javascript
const response = await fetch('http://localhost:8000/api/calls/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(callData)
});
```

---

## 🎯 Real-World Use Cases

### 1. Customer Support Calls
```python
call_data = {
    "call_id": "support_001",
    "transcript": {
        "turns": [
            {"role": "AGENT", "content": "Hello, support desk..."},
            {"role": "USER", "content": "I need help with..."}
        ]
    },
    "metadata": {
        "call_type": "customer_support",
        "priority": "medium",
        "category": "technical_issue"
    }
}
```

### 2. Sales Calls
```python
call_data = {
    "call_id": "sales_001", 
    "transcript": {...},
    "metadata": {
        "call_type": "sales",
        "lead_source": "website",
        "product_interest": "enterprise_plan"
    }
}
```

### 3. Quality Assurance
```python
call_data = {
    "call_id": "qa_001",
    "transcript": {...},
    "metadata": {
        "call_type": "quality_assurance",
        "agent_id": "agent_123",
        "supervisor_notes": "Good call handling"
    }
}
```

---

## 🔍 Testing Your Setup

### 1. Health Check
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

### 2. List All Calls
```bash
curl http://localhost:8000/api/calls/
# Returns JSON array of all calls
```

### 3. Get Specific Call
```bash
curl http://localhost:8000/api/calls/call_123
# Returns details for call_123
```

---

## 🚨 Troubleshooting

### Common Issues

**"Connection refused"**
- Make sure backend is running: `./start_backend.sh`
- Check if port 8000 is available

**"Invalid JSON"**
- Verify your call data structure matches the schema
- Check for missing required fields

**"Database error"**
- Ensure PostgreSQL is running
- Check your `.env` file configuration
- Run migrations: `alembic upgrade head`

---

## 📖 Next Steps

1. **Run the examples** to understand the system
2. **Modify the code** to match your use case
3. **Check the API docs** at http://localhost:8000/docs
4. **Explore the frontend** at http://localhost:3000
5. **Read the main README** for comprehensive documentation

---

## 🤝 Contributing Examples

Have a great example to share? 

1. Create a new Python file in this directory
2. Add clear documentation and comments
3. Include sample data and use cases
4. Update this README with your example
5. Submit a pull request!

---

**Happy coding! 🎤✨**
