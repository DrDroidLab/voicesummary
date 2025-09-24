# 🎤 Voice Summary

**Open Source AI Database for Voice Agent Transcripts**

A comprehensive AI-powered database and analytics platform for storing, analyzing, and extracting insights from voice agent call transcripts. Built with FastAPI, React/Next.js, and PostgreSQL, featuring advanced AI analysis, transcript enhancement, and intelligent data extraction.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org)
[![Next.js](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-blue.svg)](https://postgresql.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-orange.svg)](https://openai.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/DrDroidLab/voicesummary)](https://github.com/DrDroidLab/voicesummary/stargazers)
[![Forks](https://img.shields.io/github/forks/DrDroidLab/voicesummary)](https://github.com/DrDroidLab/voicesummary/network)
[![Issues](https://img.shields.io/github/issues/DrDroidLab/voicesummary)](https://github.com/DrDroidLab/voicesummary/issues)

## 🎯 What is Voice Summary?

Voice Summary is an **open-source AI database** specifically designed for **voice agent transcripts** and **call analytics**. It provides:

- 🤖 **AI-Powered Transcript Analysis** - Advanced machine learning for call outcome analysis
- 📊 **Intelligent Data Extraction** - Automatic extraction of customer information and business insights
- 🏷️ **Smart Classification & Labeling** - AI-driven call categorization and sentiment analysis
- 🎵 **Advanced Audio Processing** - Voice analysis with pause detection and conversation health scoring
- ☁️ **Cloud-Ready Architecture** - Built with FastAPI, React, PostgreSQL, and AWS S3 integration

Perfect for **call centers**, **voice bot developers**, **customer service teams**, and **AI researchers** who need comprehensive voice analytics and transcript management.

## 📋 Table of Contents

- [✨ Features](#-features)
- [🖼️ What you will get](#️-what-you-will-get)
- [🚀 Quick Start](#-quick-start)
- [📥 Data Ingestion](#-data-ingestion)
- [🔍 AI-Powered Data Extraction Pipeline](#-ai-powered-data-extraction-pipeline)
- [🔌 API Endpoints](#-api-endpoints)
- [🎯 Use Cases](#-use-cases)
- [🏗️ Project Structure](#️-project-structure)
- [🛠️ Development](#️-development)
- [🚀 Deployment](#-deployment)
- [🤝 Contributing](#-contributing)
- [📚 Documentation](#-documentation)
- [🐛 Troubleshooting](#-troubleshooting)
- [📄 License](#-license)

## ✨ Features

- **🤖 AI-Powered Transcript Analysis**: Advanced AI models for call outcome analysis, quality assessment, and performance evaluation
- **📊 Intelligent Data Extraction**: Automatic extraction of customer information, call reasons, and business insights from transcripts
- **🏷️ Smart Classification & Labeling**: AI-driven call categorization, sentiment analysis, and business action labeling
- **📝 Enhanced Transcript Processing**: Automatic timestamp alignment, turn-by-turn conversation analysis, and transcript normalization
- **🎵 Advanced Audio Analysis**: AI-powered voice analysis with pause detection, speech segmentation, and conversation health scoring
- **☁️ S3 Integration**: Secure audio file storage with automatic format detection
- **🌐 Modern Web UI**: Beautiful React/Next.js frontend with real-time timeline visualization
- **🔌 Flexible Data Ingestion**: Support for both direct API calls and Bolna platform integration
- **🚀 FastAPI Backend**: High-performance async API with automatic documentation
- **🗄️ PostgreSQL Database**: Robust data storage with Alembic migrations
- **⚡ Asynchronous Processing**: Real-time API responses with background AI processing

## 🖼️ What you will get 
### Samples for an appointment booking bot

### Calls List
![Main Dashboard](docs/images/main.png)

### Call Insights  
![Call Insights](docs/images/analysis.png)

### Transcript
![Transcript](docs/images/transcript.png)

### Transcript Analysis
![Transcript Analysis](docs/images/transcript_analysis.png)

### Audio Analysis
![Audio Analysis](docs/images/audio_analysis.png)

### Extracted Data
![Extracted data](docs/images/extraction.png)

### Labelling & Classification
![Labelling & Classification](docs/images/labels_n_classification.png)

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+**
- **Node.js 18+**
- **PostgreSQL 12+**
- **AWS S3 bucket** (for audio storage)
- **OpenAI API key** (for AI-powered analysis)

### One-Command Setup

```bash
# Clone the repository
git clone https://github.com/DrDroidLab/voicesummary.git
cd voicesummary

# Run the complete setup script
./setup.sh
```

The setup script will:
- ✅ Check all prerequisites
- ✅ Create Python virtual environment
- ✅ Install Python dependencies
- ✅ Install Node.js dependencies
- ✅ Set up database and run migrations
- ✅ Create convenient start scripts

### Manual Setup

If you prefer manual setup:

```bash
# 1. Clone and navigate
git clone https://github.com/DrDroidLab/voicesummary.git
cd voicesummary

# 2. Setup Python backend
uv sync

# 3. Setup frontend
cd frontend
npm install
cd ..

# 4. Configure environment
cp env.example .env
# Edit .env with your credentials

# 5. Setup database
alembic upgrade head
```

## 🏃‍♂️ Running the Application

### Start Backend Server

```bash
# Option 1: Use the generated script
./start_backend.sh

# Option 2: Manual start
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend Server

```bash
# Option 1: Use the generated script (in new terminal)
./start_frontend.sh

# Option 2: Manual start
cd frontend
npm run dev
```

### Access Your Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Interactive API**: http://localhost:8000/redoc

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/voicesummary

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-audio-bucket

# OpenAI API (required for AI-powered analysis)
OPENAI_API_KEY=your_openai_api_key

# Optional: Bolna API (if using Bolna platform)
BOLNA_API_KEY=your_bolna_api_key
```

### Database Setup

```bash
# Create PostgreSQL database
createdb voicesummary

# Run migrations
alembic upgrade head
```

## 📥 Data Ingestion

Voice Summary supports two main data ingestion methods for voice agent transcripts:

### ⚠️ Important: OpenAI API Key Required

**For full AI functionality, you need to add your OpenAI API key to the environment variables:**

```bash
OPENAI_API_KEY=your_openai_api_key
```

**What happens with OpenAI API key:**
- ✅ **AI Transcript Analysis**: Intelligent call outcome analysis, quality assessment, and improvement areas
- ✅ **Agent Performance Evaluation**: AI-powered goal achievement analysis and script adherence evaluation
- ✅ **Executive Summaries**: Intelligent call summaries with key insights and recommendations
- ✅ **Data Extraction Pipeline**: Automatic extraction, classification, and labeling of call data using AI

**What happens without OpenAI API key:**
- ✅ **Audio Analysis**: Pause detection, speech segmentation, conversation health scoring
- ✅ **Basic Processing**: Audio file processing and S3 storage
- ❌ **No AI Transcript Analysis**: Call outcome, quality metrics, and improvement areas won't be generated
- ❌ **No Agent Evaluation**: Performance analysis and script adherence won't be available
- ❌ **No Data Extraction**: Structured data extraction, classification, and labeling won't be available

### Method 1: Direct API Calls (Recommended for Custom Integrations)

Use the REST API to directly ingest voice agent call data with your own S3 storage:

```bash
# Create a new call record
curl -X POST "http://localhost:8000/api/calls/" \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "call_123",
    "transcript": {
      "turns": [
        {
          "role": "AGENT",
          "content": "Hello, how can I help you?",
          "timestamp": "2025-01-01T10:00:00Z"
        },
        {
          "role": "USER", 
          "content": "I need help with my order",
          "timestamp": "2025-01-01T10:00:01Z"
        }
      ]
    },
    "audio_file_url": "https://your-s3-bucket.s3.amazonaws.com/audio/call_123.mp3",
    "timestamp": "2025-01-01T10:00:00Z"
  }'
```

**Benefits:**
- ✅ Full control over S3 storage
- ✅ Custom audio processing pipelines
- ✅ Integration with any voice agent platform
- ✅ Real-time data ingestion
- ✅ AI-powered analysis and insights

### Method 2: Bolna Platform Integration

Use the built-in Bolna integration for automatic voice agent call processing:

```bash
# Run the Bolna fetcher
python app/integrations/fetch_bolna_calls_simple.py
```

**Benefits:**
- ✅ Automatic call discovery and processing
- ✅ Built-in audio analysis and enhancement
- ✅ Transcript normalization and timestamp alignment
- ✅ Seamless S3 upload and storage
- ✅ AI-powered insights and analysis

## 🔍 AI-Powered Data Extraction Pipeline

Voice Summary includes a sophisticated AI-driven data extraction pipeline that automatically processes voice agent call transcripts to extract structured information, classify calls, and apply relevant business labels.

### 🎯 Pipeline Features

#### **AI Data Extraction**
- **Customer Information**: Name, email, phone, account number, customer ID
- **Product Mentions**: Products and services discussed during the call
- **Call Reasons**: Primary and secondary reasons for the call
- **Resolution Info**: How the call was resolved and follow-up requirements

#### **AI Call Classification**
- **Call Category**: customer_support, technical_support, billing_inquiry, sales_inquiry, etc.
- **Sentiment Analysis**: positive, neutral, negative, mixed
- **Complexity Level**: simple, moderate, complex, very_complex

#### **AI Smart Labeling**
- **Urgency**: urgent, escalation_required, follow_up_needed
- **Business Actions**: satisfaction_survey, training_opportunity, upsell_opportunity

### ⚙️ Configuration

The AI pipeline is configured through `config/agent_prompts.yaml`. You can easily add new extraction, classification, or labeling prompts:

```yaml
# Add new extraction prompt
extraction:
  call_duration:
    prompt: |
      Extract call duration and timing information from this transcript: {transcript}
      
      Return only a JSON object with: total_duration_seconds, agent_speaking_time, customer_speaking_time

# Add new classification prompt
classification:
  language_detected:
    prompt: |
      Detect the primary language used in this call.
      
      Categories: english, spanish, french, other
      
      Return only the category name.
      
      Transcript: {transcript}

# Add new labeling prompt
labeling:
  - label: "high_value_customer"
    prompt: |
      Determine if this call involves a high-value customer.
      High-value indicators: premium account, large transactions, VIP status
      
      Return only "yes" or "no".
      
      Transcript: {transcript}
```

### 🚀 Usage

#### **Automatic AI Processing**
The AI pipeline runs automatically when calls are created via the API.

#### **Manual AI Processing**
```bash
# Process a specific call through AI pipeline
curl -X POST "http://localhost:8000/api/calls/{call_id}/process-data-pipeline" \
  -H "Content-Type: application/json" \
  -d '{"call_id": "call_123", "force_reprocess": false}'

# Get AI-extracted data
curl "http://localhost:8000/api/calls/{call_id}/extracted-data"

# Check AI processing status
curl "http://localhost:8000/api/calls/{call_id}/extracted-data/status"
```

#### **Frontend Interface**
- Navigate to any call detail page
- Click on the "Extracted Data" tab
- View AI processing status, extracted information, classifications, and labels
- Reprocess data if needed

#### **Batch AI Processing**
```bash
# Process all existing calls through AI pipeline
python test_all_calls_pipeline.py

# Force reprocess all calls (including already processed ones)
python test_all_calls_pipeline.py --force

# Show help
python test_all_calls_pipeline.py --help
```

### 📊 Example AI Results

```json
{
  "extraction_data": {
    "customer_info": {
      "customer_name": "John Smith",
      "account_number": "123456789",
      "customer_email": null
    },
    "call_reason": {
      "primary_reason": "billing inquiry",
      "urgency_level": "medium",
      "call_type": "inquiry"
    }
  },
  "classification_data": {
    "call_category": "billing_inquiry",
    "sentiment_analysis": "positive",
    "complexity_level": "simple"
  },
  "labeling_data": {
    "urgent": false,
    "satisfaction_survey": true,
    "follow_up_needed": false
  }
}
```

### 🔧 Customization

- **Add New AI Prompts**: Simply add new sections to `config/agent_prompts.yaml`
- **No Code Changes**: New AI prompts are automatically picked up by the pipeline
- **Error Handling**: Missing prompts are gracefully skipped
- **Parallel Processing**: All AI prompts run simultaneously for maximum efficiency

## 🏗️ Project Structure

```
voicesummary/
├── app/                          # Backend application
│   ├── api/                      # API endpoints
│   │   └── calls.py             # Call management API
│   ├── integrations/             # External platform integrations
│   │   └── fetch_bolna_calls_simple.py  # Bolna integration
│   ├── utils/                    # Utility modules
│   │   ├── audio_processor.py    # Audio analysis & processing
│   │   ├── improved_voice_analyzer.py  # AI voice analysis
│   │   ├── call_data_pipeline.py # AI data extraction pipeline
│   │   └── s3.py                # S3 operations
│   ├── models.py                 # Database models
│   ├── schemas.py                # API schemas
│   └── main.py                   # FastAPI application
├── frontend/                     # React/Next.js frontend
│   ├── app/                      # Next.js app directory
│   ├── components/               # React components
│   │   ├── AudioPlayer.tsx       # Audio playback
│   │   ├── EnhancedTimeline.tsx  # Timeline visualization
│   │   ├── ExtractedData.tsx    # AI data extraction display
│   │   └── TranscriptViewer.tsx  # Transcript display
│   └── types/                    # TypeScript type definitions
├── config/                       # Configuration files
│   └── agent_prompts.yaml       # AI data extraction pipeline prompts
├── alembic/                      # Database migrations
├── setup.sh                      # Complete setup script
├── start_backend.sh              # Backend start script
├── start_frontend.sh             # Frontend start script
└── requirements.txt               # Python dependencies
```

## 🔌 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/calls/` | Create new call record |
| `GET` | `/api/calls/` | List all calls (paginated) |
| `GET` | `/api/calls/{call_id}` | Get call details |
| `GET` | `/api/calls/{call_id}/audio` | Download audio file |
| `GET` | `/api/calls/{call_id}/transcript` | Get transcript JSON |
| `PUT` | `/api/calls/{call_id}` | Update call record |
| `DELETE` | `/api/calls/{call_id}` | Delete call record |

### Audio Processing

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/calls/{call_id}/process-audio` | Process audio file |

### AI Data Extraction Pipeline

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/calls/{call_id}/process-data-pipeline` | Process call through AI data extraction pipeline |
| `GET` | `/api/calls/{call_id}/extracted-data` | Get AI-extracted data for a call |
| `GET` | `/api/calls/{call_id}/extracted-data/status` | Get AI processing status of extracted data |

## 🎯 Use Cases

### Voice Agent Analytics & AI Insights
- **AI-Powered Call Quality Assessment**: Intelligent analysis of conversation health, pause patterns, and interruption rates
- **Agent Performance Monitoring**: AI-driven tracking of agent response times and conversation flow
- **Issue Detection**: AI identification of call termination problems and audio quality issues
- **Intelligent Call Classification**: Automatic categorization of calls by type, sentiment, and complexity
- **Business Intelligence Extraction**: AI-powered extraction of customer information and call reasons

### Research & Development
- **AI Speech Analysis**: Advanced conversation pattern analysis and speech characteristics
- **Machine Learning Training**: Use AI-enhanced transcripts for training ML models
- **Quality Assurance**: AI-powered monitoring and improvement of voice agent performance

### Business Intelligence & AI Analytics
- **AI Call Analytics**: Generate intelligent reports on call volumes, durations, and outcomes
- **Customer Experience Analysis**: AI-powered conversation sentiment and satisfaction metrics
- **Operational Insights**: AI identification of bottlenecks and optimization opportunities
- **Data Extraction**: Automatically extract structured data from call transcripts using AI
- **Smart Labeling**: Apply AI-driven business-relevant labels for follow-up actions

## 🛠️ Development

### Backend Development

```bash
# Run with auto-reload
uv run uvicorn app.main:app --reload

# Run tests
pytest

# Format code
black .
isort .
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 🚀 Deployment

### Production Setup

```bash
# Install production dependencies
uv sync --frozen

# Set production environment variables
export ENVIRONMENT=production

# Run production server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Build frontend
cd frontend && npm run build
```

### Environment Variables for Production

```bash
# Required
DATABASE_URL=postgresql://user:pass@host:5432/db
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET_NAME=your_bucket

# OpenAI API (required for AI-powered analysis)
OPENAI_API_KEY=your_openai_api_key

# Optional
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Commit your changes**: `git commit -m 'Add amazing feature'`
5. **Push to the branch**: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript for frontend code
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting

## 📚 Documentation

- **API Reference**: http://localhost:8000/docs (when running)
- **AI Audio Processing**: See `app/utils/audio_processor.py`
- **AI Data Extraction**: See `app/utils/call_data_pipeline.py`
- **Frontend Components**: See `frontend/components/`
- **Database Models**: See `app/models.py`

## 🐛 Troubleshooting

### Common Issues

#### Backend Won't Start
```bash
# Check Python version
python3 --version  # Should be 3.9+

# Verify uv installation
uv --version  # Should show uv version

# Check dependencies
pip list | grep fastapi
```

#### Frontend Won't Start
```bash
# Check Node.js version
node --version  # Should be 18+

# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

#### Database Connection Issues
```bash
# Test PostgreSQL connection
psql $DATABASE_URL -c "SELECT 1"

# Check if database exists
psql -l | grep voicesummary

# Run migrations
alembic upgrade head
```

#### S3 Access Issues
```bash
# Test AWS credentials
aws sts get-caller-identity

# Verify bucket permissions
aws s3 ls s3://your-bucket-name
```

#### OpenAI API Issues
```bash
# Test OpenAI API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# Check API key in environment
echo $OPENAI_API_KEY
```

### Getting Help

- **Issues**: Create a GitHub issue with detailed error information
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Reachout**: Reach out to the author at dipesh@drdroid.io

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** for the excellent web framework
- **Next.js** for the powerful React framework
- **PostgreSQL** for reliable data storage
- **AWS S3** for scalable file storage
- **OpenAI** for AI-powered analysis capabilities
- **Librosa** for audio processing capabilities

## 🌟 Star History

If you find this project useful, please give it a ⭐️ on GitHub!

---

## 🔍 Key Technologies & Keywords

**Voice Analytics**: AI-powered call analysis, transcript processing, voice agent analytics  
**Call Center Solutions**: Customer service analytics, call quality assessment, performance monitoring  
**AI Database**: Machine learning, natural language processing, intelligent data extraction  
**Voice Bot Analytics**: Conversation intelligence, speech analytics, chatbot performance  
**Open Source**: Free, community-driven, extensible voice analytics platform  
**FastAPI**: High-performance Python web framework for voice data APIs  
**React/Next.js**: Modern frontend for voice analytics dashboard  
**PostgreSQL**: Robust database for voice transcript storage and analysis  
**OpenAI Integration**: Advanced AI models for transcript analysis and insights

---

**Built with ❤️ for the voice agent community**

*Voice Summary - The Open Source AI Database for Voice Agent Transcripts*
