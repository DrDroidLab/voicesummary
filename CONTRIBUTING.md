# 🤝 Contributing to Voice Summary

Thank you for your interest in contributing to Voice Summary! This document provides guidelines and information for contributors.

## 🎯 What is Voice Summary?

Voice Summary is an **open-source AI database for voice agent transcripts** that provides advanced analytics, intelligent data extraction, and comprehensive voice processing capabilities.

## 🚀 Quick Start for Contributors

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL 12+
- Git

### Setup Development Environment

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/voicesummary.git
cd voicesummary

# Setup Python environment
uv sync

# Setup frontend
cd frontend && npm install && cd ..

# Setup database
alembic upgrade head

# Copy environment file
cp env.example .env
# Edit .env with your credentials
```

## 🎯 Areas for Contribution

### 🐛 Bug Fixes
- Audio processing issues
- API endpoint problems
- Frontend UI bugs
- Database migration issues

### ✨ New Features
- Additional AI models for transcript analysis
- New data extraction capabilities
- Enhanced audio processing features
- UI/UX improvements
- API enhancements

### 📚 Documentation
- Code documentation
- API documentation
- User guides
- Tutorial improvements

### 🧪 Testing
- Unit tests
- Integration tests
- End-to-end tests
- Performance testing

## 🔧 Development Guidelines

### Code Style

#### Python (Backend)
- Follow PEP 8 style guide
- Use type hints
- Add docstrings for functions and classes
- Maximum line length: 88 characters (Black formatter)

```bash
# Format code
black .
isort .

# Run linting
flake8 app/
```

#### TypeScript/React (Frontend)
- Use TypeScript for type safety
- Follow React best practices
- Use functional components with hooks
- Add JSDoc comments

```bash
# Format code
npm run format

# Run linting
npm run lint
```

### Git Workflow

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Commit with clear messages**
   ```bash
   git commit -m 'feat: add new AI model for sentiment analysis'
   ```
5. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```
6. **Create a Pull Request**

### Commit Message Format

Use conventional commit format:
```
type(scope): description

feat(ai): add new sentiment analysis model
fix(api): resolve audio processing timeout issue
docs(readme): update installation instructions
test(backend): add unit tests for call processing
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build/tooling changes

## 🧪 Testing

### Backend Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_audio_processor.py

# Run with coverage
pytest --cov=app
```

### Frontend Testing
```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm run test:coverage
```

## 📋 Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation is updated
- [ ] No breaking changes (or documented if necessary)
- [ ] Commit messages follow conventional format
- [ ] PR description clearly explains changes

## 🎯 Project Structure

```
voicesummary/
├── app/                    # Backend application
│   ├── api/               # API endpoints
│   ├── utils/             # Utility modules
│   ├── models.py          # Database models
│   └── main.py            # FastAPI application
├── frontend/              # React/Next.js frontend
│   ├── components/        # React components
│   └── app/               # Next.js app directory
├── config/                # Configuration files
├── tests/                 # Test files
└── docs/                  # Documentation
```

## 🐛 Reporting Issues

When reporting issues, please include:

1. **Environment details**
   - OS and version
   - Python/Node.js versions
   - Database version

2. **Steps to reproduce**
   - Clear step-by-step instructions
   - Sample data if applicable

3. **Expected vs actual behavior**
   - What you expected to happen
   - What actually happened

4. **Error messages/logs**
   - Full error traceback
   - Console logs

## 💬 Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Email**: dipesh@drdroid.io for direct contact

## 📄 License

By contributing to Voice Summary, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation

---

**Thank you for contributing to the future of voice analytics!** 🎤
