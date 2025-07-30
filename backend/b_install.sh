#!/bin/bash

# Financial Transcripts RAG - Backend Installation Script
# This script sets up the FastAPI backend environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[BACKEND]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[BACKEND]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[BACKEND]${NC} $1"
}

print_error() {
    echo -e "${RED}[BACKEND]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        local version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        local major=$(echo $version | cut -d. -f1)
        local minor=$(echo $version | cut -d. -f2)
        
        if [ "$major" -eq 3 ] && [ "$minor" -ge 8 ]; then
            print_success "Python $version found"
            return 0
        else
            print_error "Python 3.8+ required, found $version"
            return 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.8+"
        return 1
    fi
}

# Function to create or update backend virtual environment
create_backend_venv() {
    if [ -d "venv" ]; then
        print_status "Backend virtual environment already exists, updating dependencies..."
        source venv/bin/activate
        
        # Upgrade pip
        print_status "Upgrading pip..."
        python3 -m pip install --upgrade pip
        
        # Install/update backend dependencies
        if [ -f "requirements.txt" ]; then
            print_status "Updating FastAPI and backend dependencies..."
            python3 -m pip install -r requirements.txt
        else
            print_error "No requirements.txt found in backend directory"
            deactivate
            return 1
        fi
        
        deactivate
        print_success "Backend environment updated successfully"
    else
        print_status "Creating backend virtual environment..."
        python3 -m venv venv
        
        # Activate virtual environment
        source venv/bin/activate
        
        # Upgrade pip
        print_status "Upgrading pip..."
        python3 -m pip install --upgrade pip
        
        # Install backend dependencies
        if [ -f "requirements.txt" ]; then
            print_status "Installing FastAPI and backend dependencies..."
            python3 -m pip install -r requirements.txt
        else
            print_error "No requirements.txt found in backend directory"
            deactivate
            return 1
        fi
        
        deactivate
        print_success "Backend environment created successfully"
    fi
}

# Function to validate backend installation
validate_backend_installation() {
    print_status "Validating backend installation..."
    
    if [ -d "venv" ]; then
        source venv/bin/activate
        
        # Test FastAPI import
        python -c "import fastapi; print('✓ FastAPI OK')" 2>/dev/null || {
            print_error "FastAPI installation failed"
            deactivate
            return 1
        }
        
        # Test ChromaDB import
        python -c "import chromadb; print('✓ ChromaDB OK')" 2>/dev/null || {
            print_error "ChromaDB installation failed"
            deactivate
            return 1
        }
        
        # Test sentence-transformers import
        python -c "import sentence_transformers; print('✓ Sentence Transformers OK')" 2>/dev/null || {
            print_error "Sentence Transformers installation failed"
            deactivate
            return 1
        }
        
        # Test Google Generative AI import
        python -c "import google.generativeai; print('✓ Google Generative AI OK')" 2>/dev/null || {
            print_error "Google Generative AI installation failed"
            deactivate
            return 1
        }
        
        deactivate
        print_success "Backend validation passed"
        return 0
    else
        print_error "Backend virtual environment not found"
        return 1
    fi
}

# Function to setup backend directories
setup_backend_directories() {
    print_status "Setting up backend data directories..."
    
    # Create data directories relative to project root
    mkdir -p ../data/chromadb
    mkdir -p ../data/embeddings
    mkdir -p ../logs
    
    print_success "Backend directories created"
}

# Function to setup backend configuration
setup_backend_config() {
    print_status "Setting up backend configuration..."
    
    # Check if .env exists in project root
    if [ ! -f "../.env" ]; then
        if [ -f "../env.example" ]; then
            print_status "Creating .env file from env.example..."
            cp ../env.example ../.env
            print_warning "Please edit .env file and add your GOOGLE_API_KEY"
        else
            print_warning "env.example file not found, creating basic .env..."
            cat > ../.env << 'EOF'
# Google Gemini Pro API (REQUIRED)
GOOGLE_API_KEY=your_gemini_api_key_here

# ChromaDB Configuration
CHROMADB_PATH=./data/chromadb
CHROMADB_HOST=localhost
CHROMADB_PORT=8000

# Embedding Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu
BATCH_SIZE=32

# RAG Pipeline Settings
MAX_CHUNKS_PER_QUERY=5
SIMILARITY_THRESHOLD=0.7
TEMPERATURE=0.7

# FastAPI Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
API_V1_PREFIX=/api/v1
CORS_ORIGINS=["http://localhost:8501"]

# Data Paths
TRANSCRIPTS_PATH=../Transcripts
DATA_PATH=./data
EMBEDDINGS_PATH=./data/embeddings
EOF
            print_warning "Please edit .env file and add your GOOGLE_API_KEY"
        fi
    else
        print_success ".env file already exists"
    fi
    
    # Check if GOOGLE_API_KEY is configured
    if grep -q "GOOGLE_API_KEY=your_gemini_api_key_here" ../.env 2>/dev/null; then
        print_warning "GOOGLE_API_KEY not configured in .env file"
        print_status "Please get your API key from: https://makersuite.google.com/app/apikey"
        return 1
    fi
    
    return 0
}

# Function to check transcript data
check_transcript_data() {
    print_status "Checking transcript data availability..."
    
    if [ -d "../Transcripts" ]; then
        local count=$(find ../Transcripts -name "*.txt" | wc -l)
        if [ $count -gt 0 ]; then
            print_success "Found $count transcript files in Transcripts directory"
        else
            print_warning "Transcripts directory exists but no .txt files found"
        fi
    else
        print_warning "Transcripts directory not found in project root"
        print_status "Backend will still work, but you'll need transcript data for queries"
    fi
}

# Main installation process
main() {
    echo "=============================================="
    echo "   Financial Transcripts RAG - Backend      "
    echo "            Installation Script              "
    echo "=============================================="
    echo ""
    
    # Check prerequisites
    print_status "Checking prerequisites..."
    
    if ! check_python_version; then
        exit 1
    fi
    
    if ! command_exists pip && ! command_exists pip3; then
        print_error "pip or pip3 not found. Please install pip"
        exit 1
    fi
    
    # Check if we're in the backend directory
    if [ ! -f "app/main.py" ]; then
        print_error "Backend app files not found. Please run from backend directory."
        exit 1
    fi
    
    # Setup backend directories
    setup_backend_directories
    
    # Setup backend configuration
    setup_backend_config
    api_key_configured=$?
    
    # Create backend virtual environment and install dependencies
    create_backend_venv
    
    # Validate installation
    validate_backend_installation
    
    # Check transcript data
    check_transcript_data
    
    echo ""
    echo "=============================================="
    print_success "Backend installation completed successfully!"
    echo "=============================================="
    echo ""
    print_status "Next steps:"
    
    if [ $api_key_configured -ne 0 ]; then
        echo "1. Edit .env file and add your GOOGLE_API_KEY"
        echo "2. Run './b_start.sh' to start the FastAPI backend"
    else
        echo "1. Run './b_start.sh' to start the FastAPI backend"
    fi
    
    echo ""
    print_status "Backend will be available at:"
    echo "- API: http://localhost:8000"
    echo "- API Documentation: http://localhost:8000/docs"
    echo "- Health Check: http://localhost:8000/health"
    echo ""
    print_status "Optional:"
    echo "- Run 'python scripts/setup_embeddings.py' to generate embeddings"
    echo "- Run 'python scripts/health_check.py' to check system status"
    echo ""
}

# Handle script arguments
case "${1:-}" in
    --clean)
        print_status "Cleaning previous backend installation..."
        rm -rf venv ../data/chromadb ../data/embeddings ../logs
        ;;
    --help)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --clean    Remove existing backend virtual environment and data"
        echo "  --help     Show this help message"
        exit 0
        ;;
esac

# Run main installation
main 