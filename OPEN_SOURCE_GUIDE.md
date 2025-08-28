# 🌟 Open Source Guide

**Voice Summary - Open Source Voice Agent Analytics Platform**

Welcome to the Voice Summary project! This guide will help you understand how to use, contribute to, and extend this open source platform.

## 🎯 What is Voice Summary?

Voice Summary is a comprehensive platform for analyzing, storing, and visualizing voice call data. It's designed to help developers, researchers, and businesses understand and improve their voice agent interactions.

### Key Features
- **🎵 AI-Powered Audio Analysis**: Advanced voice analysis with pause detection and speech segmentation
- **📝 Transcript Enhancement**: Automatic timestamp alignment and conversation analysis
- **☁️ S3 Integration**: Secure audio file storage with automatic format detection
- **🌐 Modern Web UI**: Beautiful React/Next.js frontend with real-time visualization
- **🔌 Flexible Data Ingestion**: Support for both direct API calls and platform integrations

## 🚀 Getting Started

### Quick Setup (5 minutes)
```bash
# Clone the repository
git clone https://github.com/yourusername/voicesummary.git
cd voicesummary

# Run the complete setup script
./setup.sh

# Start the application
./start_backend.sh    # Terminal 1
./start_frontend.sh   # Terminal 2
```

### What You Get
- **Backend API**: http://localhost:8000
- **Frontend App**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Database**: PostgreSQL with automatic migrations
- **S3 Integration**: Ready for audio file storage

## 📚 Documentation Structure

### Core Documentation
- **[README.md](README.md)**: Comprehensive project overview and setup
- **[QUICKSTART.md](QUICKSTART.md)**: 5-minute setup guide
- **[OPEN_SOURCE_GUIDE.md](OPEN_SOURCE_GUIDE.md)**: This guide for contributors

### Code Examples
- **[examples/](examples/)**: Working code samples and integration examples
- **[examples/README.md](examples/README.md)**: Detailed examples documentation

### API Reference
- **Interactive Docs**: http://localhost:8000/docs (when running)
- **Schema Definitions**: `app/schemas.py`
- **Endpoint Implementation**: `app/api/calls.py`

## 🏗️ Architecture Overview

### Backend (Python/FastAPI)
```
app/
├── api/                    # REST API endpoints
├── integrations/           # External platform integrations
├── utils/                  # Core utilities and audio processing
├── models.py               # Database models
├── schemas.py              # API request/response schemas
└── main.py                 # FastAPI application entry point
```

### Frontend (React/Next.js)
```
frontend/
├── app/                    # Next.js app directory
├── components/             # React components
├── types/                  # TypeScript type definitions
└── package.json            # Dependencies and scripts
```

### Key Components
- **Audio Processor**: `app/utils/audio_processor.py`
- **Voice Analyzer**: `app/utils/improved_voice_analyzer.py`
- **S3 Manager**: `app/utils/s3.py`
- **Timeline Component**: `frontend/components/EnhancedTimeline.tsx`

## 🔌 Data Ingestion Methods

### Method 1: Direct API Integration
Perfect for custom voice platforms and integrations:

```python
import requests

# Create a call record
response = requests.post("http://localhost:8000/api/calls/", json={
    "call_id": "call_123",
    "transcript": {
        "turns": [
            {"role": "AGENT", "content": "Hello!", "timestamp": "2025-01-01T10:00:00Z"},
            {"role": "USER", "content": "Hi there!", "timestamp": "2025-01-01T10:00:01Z"}
        ]
    },
    "timestamp": "2025-01-01T10:00:00Z"
})
```

**Benefits:**
- ✅ Full control over data structure
- ✅ Real-time ingestion
- ✅ Custom metadata support
- ✅ Integration with any voice platform

### Method 2: Bolna Platform Integration
Built-in integration for Bolna users:

```bash
# Run the Bolna fetcher
python app/integrations/fetch_bolna_calls_simple.py
```

**Benefits:**
- ✅ Automatic call discovery
- ✅ Built-in audio processing
- ✅ Transcript normalization
- ✅ Seamless S3 integration

## 🛠️ Development Workflow

### Setting Up Development Environment
```bash
# 1. Clone and setup
git clone https://github.com/yourusername/voicesummary.git
cd voicesummary
./setup.sh

# 2. Create feature branch
git checkout -b feature/amazing-feature

# 3. Start development servers
./start_backend.sh    # Terminal 1
./start_frontend.sh   # Terminal 2

# 4. Make your changes
# 5. Test your changes
# 6. Commit and push
git add .
git commit -m "Add amazing feature"
git push origin feature/amazing-feature
```

### Code Quality Standards
- **Python**: Follow PEP 8, use type hints, add docstrings
- **TypeScript**: Use strict mode, proper typing, component documentation
- **Testing**: Add tests for new features
- **Documentation**: Update relevant docs when changing functionality

## 🎯 Common Use Cases

### 1. Voice Agent Analytics
```python
# Analyze call quality and performance
call_data = {
    "call_id": "agent_performance_001",
    "transcript": {...},
    "metadata": {
        "agent_id": "agent_123",
        "call_type": "customer_support",
        "performance_metrics": {
            "response_time": 2.5,
            "customer_satisfaction": 4.8
        }
    }
}
```

### 2. Research & Development
```python
# Study conversation patterns
call_data = {
    "call_id": "research_001",
    "transcript": {...},
    "metadata": {
        "research_study": "conversation_flow_analysis",
        "participant_id": "P001",
        "study_phase": "baseline"
    }
}
```

### 3. Quality Assurance
```python
# Monitor call quality
call_data = {
    "call_id": "qa_001",
    "transcript": {...},
    "metadata": {
        "qa_score": 95,
        "supervisor_notes": "Excellent call handling",
        "improvement_areas": ["greeting", "closing"]
    }
}
```

## 🔧 Customization & Extension

### Adding New Audio Analysis Features
```python
# Extend the voice analyzer
class CustomVoiceAnalyzer(ImprovedVoiceAnalyzer):
    def analyze_emotion(self, audio_path: str) -> Dict[str, float]:
        """Add emotion detection to your analysis."""
        # Your custom emotion analysis logic
        return {"happiness": 0.8, "frustration": 0.1}

# Use in audio processor
analyzer = CustomVoiceAnalyzer(audio_path=audio_file_path)
emotion_results = analyzer.analyze_emotion(audio_file_path)
```

### Creating New Frontend Components
```typescript
// Add new visualization components
interface CallMetricsProps {
  callId: string;
  metrics: CallMetrics;
}

export const CallMetrics: React.FC<CallMetricsProps> = ({ callId, metrics }) => {
  return (
    <div className="call-metrics">
      <h3>Call Performance</h3>
      <div className="metrics-grid">
        <MetricCard title="Duration" value={metrics.duration} />
        <MetricCard title="Quality Score" value={metrics.qualityScore} />
      </div>
    </div>
  );
};
```

### Extending the Database Schema
```python
# Add new fields to models
class AudioCall(Base):
    __tablename__ = "audio_calls"
    
    # Existing fields...
    call_id = Column(String, primary_key=True)
    
    # New custom fields
    sentiment_score = Column(Float, nullable=True)
    language_detected = Column(String, nullable=True)
    custom_metadata = Column(JSON, nullable=True)

# Create and run migration
# alembic revision --autogenerate -m "Add sentiment analysis"
# alembic upgrade head
```

## 🚀 Deployment Options

### Local Development
```bash
# Already covered by setup.sh
./start_backend.sh
./start_frontend.sh
```

### Production Deployment
```bash
# Install production dependencies
pip install -r requirements.txt

# Set production environment
export ENVIRONMENT=production
export DEBUG=false

# Start production server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Build frontend
cd frontend && npm run build
```

### Docker Deployment
```bash
# Use existing Docker setup
docker-compose up --build -d
```

## 🤝 Contributing Guidelines

### How to Contribute
1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** following the code quality standards
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Commit your changes**: `git commit -m 'Add amazing feature'`
7. **Push to your branch**: `git push origin feature/amazing-feature`
8. **Open a Pull Request** with detailed description

### What We're Looking For
- **Bug fixes** and improvements
- **New audio analysis features**
- **Frontend component enhancements**
- **Performance optimizations**
- **Documentation improvements**
- **Test coverage additions**

### Code Review Process
- All contributions require review
- Maintainers will review within 48 hours
- Address feedback promptly
- Ensure all tests pass
- Update documentation as needed

## 🐛 Troubleshooting & Support

### Common Issues
- **Setup problems**: Check [QUICKSTART.md](QUICKSTART.md)
- **API errors**: Review [examples/](examples/) and API docs
- **Database issues**: Verify PostgreSQL and migrations
- **S3 problems**: Check AWS credentials and permissions

### Getting Help
- **GitHub Issues**: Create detailed issue reports
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check all README files
- **Examples**: Run example scripts to test functionality

### Debugging Tips
```bash
# Check backend logs
./start_backend.sh  # Look for error messages

# Check frontend logs
./start_frontend.sh  # Look for build errors

# Test API endpoints
curl http://localhost:8000/health

# Check database
psql $DATABASE_URL -c "SELECT COUNT(*) FROM audio_calls;"
```

## 🌟 Success Stories

### What Users Are Building
- **Customer Support Analytics**: Track call quality and agent performance
- **Research Platforms**: Study conversation patterns and speech characteristics
- **Quality Assurance Tools**: Monitor and improve voice agent interactions
- **Business Intelligence**: Generate insights from call data
- **AI Training**: Use enhanced transcripts for machine learning

### Community Contributions
- **Audio format support**: Added support for new audio formats
- **Analysis algorithms**: Enhanced voice analysis capabilities
- **Frontend components**: New visualization and interaction components
- **Integration modules**: Support for additional voice platforms

## 📈 Roadmap & Future Plans

### Upcoming Features
- **Real-time streaming**: Live audio analysis during calls
- **Multi-language support**: Internationalization and language detection
- **Advanced analytics**: Machine learning-powered insights
- **Mobile app**: React Native mobile application
- **API rate limiting**: Production-ready API management

### Long-term Vision
- **Voice agent marketplace**: Platform for voice agent developers
- **Enterprise features**: Advanced security and compliance
- **AI model training**: Custom voice analysis models
- **Global deployment**: Multi-region infrastructure

## 🎉 Recognition & Acknowledgments

### Contributors
- **Core Team**: Project maintainers and architects
- **Community Contributors**: Open source contributors
- **Beta Testers**: Early adopters and feedback providers

### Technologies
- **FastAPI**: Modern, fast web framework
- **Next.js**: React framework for production
- **PostgreSQL**: Reliable database system
- **AWS S3**: Scalable file storage
- **Librosa**: Audio processing library

## 📄 License & Legal

### Open Source License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Contributing Agreement
By contributing to this project, you agree that your contributions will be licensed under the same MIT License.

### Code of Conduct
We are committed to providing a welcoming and inspiring community for all. Please read our [Code of Conduct](CODE_OF_CONDUCT.md) for details.

---

## 🚀 Ready to Get Started?

1. **Clone the repository**: `git clone https://github.com/yourusername/voicesummary.git`
2. **Run the setup**: `./setup.sh`
3. **Start building**: `./start_backend.sh` and `./start_frontend.sh`
4. **Join the community**: Star the repo, open issues, contribute code!

**Happy voice analyzing! 🎤✨**

---

*Voice Summary - Making voice analytics accessible to everyone*

*Built with ❤️ for the voice agent community*
