#!/bin/bash

# Voice Summary - Complete Setup Script
# This script sets up both frontend and backend for the Voice Summary project

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_VERSION=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        PYTHON_CMD="python"
    else
        print_error "Python is not installed. Please install Python 3.9+ and try again."
        exit 1
    fi
    
    # Check if version is 3.9 or higher
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
        print_success "Python $PYTHON_VERSION found"
    else
        print_error "Python 3.9+ is required. Found: $PYTHON_VERSION"
        exit 1
    fi
}

# Function to check Node.js version
check_node_version() {
    if ! command_exists node; then
        print_error "Node.js is not installed. Please install Node.js 18+ and try again."
        exit 1
    fi
    
    NODE_VERSION=$(node --version)
    print_success "Node.js $NODE_VERSION found"
}

# Function to check PostgreSQL
check_postgres() {
    if ! command_exists psql; then
        print_warning "PostgreSQL client not found. You'll need to install it separately."
        print_warning "On macOS: brew install postgresql"
        print_warning "On Ubuntu: sudo apt-get install postgresql-client"
        print_warning "On Windows: Download from https://www.postgresql.org/download/windows/"
    else
        print_success "PostgreSQL client found"
    fi
}

# Function to setup Python environment
setup_python_env() {
    print_status "Setting up Python environment with uv..."
    
    # Check if uv is installed
    if ! command_exists uv; then
        print_error "uv is not installed. Please install uv first:"
        print_error "  curl -LsSf https://astral.sh/uv/install.sh | sh"
        print_error "  Or visit: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
    
    print_success "uv package manager found"
    
    # Install dependencies using uv
    print_status "Installing Python dependencies..."
    uv sync
    
    print_success "Python dependencies installed"
}

# Function to setup frontend
setup_frontend() {
    print_status "Setting up frontend..."
    
    if [ ! -d "frontend" ]; then
        print_error "Frontend directory not found. Please ensure you're in the project root."
        exit 1
    fi
    
    cd frontend
    
    # Install Node.js dependencies
    print_status "Installing Node.js dependencies..."
    npm install
    
    print_success "Frontend dependencies installed"
    
    # Go back to project root
    cd ..
}

# Function to setup database
setup_database() {
    print_status "Setting up database..."
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_warning "No .env file found. Creating from template..."
        cp env.example .env
        print_warning "Please edit .env file with your database and S3 credentials before continuing."
        print_warning "Press Enter when you're ready to continue..."
        read -r
    fi
    
    # Source environment variables
    if [ -f ".env" ]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi
    
    # Check if database URL is set
    if [ -z "$DATABASE_URL" ]; then
        print_warning "DATABASE_URL not set in .env file."
        print_warning "Please set it to your PostgreSQL connection string."
        print_warning "Example: DATABASE_URL=postgresql://user:password@localhost:5432/voicesummary"
        print_warning "Press Enter when you're ready to continue..."
        read -r
    fi
    
    # Run database migrations
    print_status "Running database migrations..."
    uv run alembic upgrade head
    
    print_success "Database setup complete"
}

# Function to create start scripts
create_start_scripts() {
    print_status "Creating start scripts..."
    
    # Backend start script
    cat > start_backend.sh << 'EOF'
#!/bin/bash
# Start the backend server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
EOF
    
    # Frontend start script
    cat > start_frontend.sh << 'EOF'
#!/bin/bash
# Start the frontend development server
cd frontend
npm run dev
EOF
    
    # Make scripts executable
    chmod +x start_backend.sh start_frontend.sh
    
    print_success "Start scripts created"
}

# Function to display next steps
show_next_steps() {
    echo
    echo "=========================================="
    echo "🎉 SETUP COMPLETE! 🎉"
    echo "=========================================="
    echo
    echo "Next steps:"
    echo
    echo "1. Start the backend server:"
    echo "   ./start_backend.sh"
    echo "   (or: uv run uvicorn app.main:app --reload)"
    echo
    echo "2. Start the frontend server (in a new terminal):"
    echo "   ./start_frontend.sh"
    echo "   (or: cd frontend && npm run dev)"
    echo
    echo "3. Access your application:"
    echo "   - Frontend: http://localhost:3000"
    echo "   - Backend API: http://localhost:8000"
    echo "   - API Docs: http://localhost:8000/docs"
    echo
    echo "4. For data ingestion, see the README.md file for:"
    echo "   - Direct API calls with S3 access"
    echo "   - Bolna platform integration"
    echo
    echo "Happy coding! 🚀"
    echo
}

# Main setup function
main() {
    echo "=========================================="
    echo "🎤 Voice Summary - Complete Setup"
    echo "=========================================="
    echo
    
    print_status "Checking prerequisites..."
    
    # Check Python
    check_python_version
    
    # Check Node.js
    check_node_version
    
    # Check PostgreSQL
    check_postgres
    
    echo
    print_status "Starting setup..."
    
    # Setup Python environment
    setup_python_env
    
    # Setup frontend
    setup_frontend
    
    # Setup database
    setup_database
    
    # Create start scripts
    create_start_scripts
    
    # Show next steps
    show_next_steps
}

# Run main function
main "$@"
