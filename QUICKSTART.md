# 🚀 Quick Start Guide

**Get Voice Summary running in 5 minutes!**

## ⚡ Super Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/yourusername/voicesummary.git
cd voicesummary
./setup.sh
```

### 2. Start Everything
```bash
# Terminal 1: Start backend
./start_backend.sh

# Terminal 2: Start frontend  
./start_frontend.sh
```

### 3. Open Your Browser
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

**That's it!** 🎉

---

## 🔧 What You Need

### Prerequisites (Install these first)
- **Python 3.9+**: [Download here](https://www.python.org/downloads/)
- **Node.js 18+**: [Download here](https://nodejs.org/)
- **PostgreSQL**: [Install guide](https://www.postgresql.org/download/)
- **AWS S3 Bucket**: [Create here](https://aws.amazon.com/s3/)

### Quick Prerequisites Check
```bash
# Check Python
python3 --version  # Should show 3.9+

# Check Node.js  
node --version     # Should show 18+

# Check PostgreSQL
psql --version     # Should show PostgreSQL version
```

---

## 📝 Configuration

### 1. Create Environment File
```bash
cp env.example .env
```

### 2. Edit .env File
```bash
# Required: Database
DATABASE_URL=postgresql://username:password@localhost:5432/voicesummary

# Required: AWS S3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_NAME=your-bucket-name
AWS_REGION=us-east-1
```

### 3. Create Database
```bash
createdb voicesummary
```

---

## 🎯 First Steps

### 1. Test the API
```bash
# Health check
curl http://localhost:8000/health

# Should return: {"status": "healthy"}
```

### 2. Create Your First Call
```bash
curl -X POST "http://localhost:8000/api/calls/" \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "test_001",
    "transcript": {
      "turns": [
        {
          "role": "AGENT",
          "content": "Hello! How can I help you today?",
          "timestamp": "2025-01-01T10:00:00Z"
        }
      ]
    },
    "timestamp": "2025-01-01T10:00:00Z"
  }'
```

### 3. View in Frontend
- Open http://localhost:3000
- You should see your test call listed

---

## 🚨 Common Issues & Fixes

### "Python not found"
```bash
# Install Python 3.9+
# macOS: brew install python@3.9
# Ubuntu: sudo apt install python3.9
# Windows: Download from python.org
```

### "Node.js not found"
```bash
# Install Node.js 18+
# macOS: brew install node
# Ubuntu: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
# Windows: Download from nodejs.org
```

### "PostgreSQL connection failed"
```bash
# Start PostgreSQL service
# macOS: brew services start postgresql
# Ubuntu: sudo systemctl start postgresql
# Windows: Start from Services app

# Create database
createdb voicesummary
```

### "AWS credentials error"
```bash
# Verify your .env file has correct AWS credentials
# Test with AWS CLI
aws sts get-caller-identity
```

### "Port already in use"
```bash
# Kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Kill process using port 3000  
lsof -ti:3000 | xargs kill -9
```

---

## 🔍 What's Happening?

### Backend (Port 8000)
- **FastAPI server** serving the API
- **PostgreSQL database** storing call data
- **S3 integration** for audio file storage
- **Audio processing** with AI analysis

### Frontend (Port 3000)
- **Next.js app** with React components
- **Real-time timeline** visualization
- **Audio player** for call playback
- **Transcript viewer** with enhanced data

---

## 📚 Next Steps

### Learn More
- **Full Documentation**: [README.md](README.md)
- **API Reference**: http://localhost:8000/docs
- **Code Examples**: See `examples/` folder

### Customize
- **Add your own audio processing** in `app/utils/`
- **Extend the frontend** in `frontend/components/`
- **Modify database schema** in `app/models.py`

### Deploy
- **Production setup**: See [README.md#deployment](README.md#deployment)
- **Docker deployment**: See [README.md#docker](README.md#docker)

---

## 🆘 Need Help?

- **GitHub Issues**: [Create an issue](https://github.com/yourusername/voicesummary/issues)
- **Discussions**: [Join the conversation](https://github.com/yourusername/voicesummary/discussions)
- **Documentation**: Check the [main README](README.md)

---

**Happy voice analyzing! 🎤✨**
