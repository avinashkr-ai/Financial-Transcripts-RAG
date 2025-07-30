#!/bin/bash

# Financial Transcripts RAG Application - Installation Script
# This script sets up the complete development environment

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

# Function to create virtual environment
create_venv() {
    local dir=$1
    local name=$2
    
    print_status "Creating virtual environment for $name..."
    
    if [ -d "$dir/venv" ]; then
        print_warning "Virtual environment already exists in $dir, removing..."
        rm -rf "$dir/venv"
    fi
    
    cd "$dir"
    python3 -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip
    
    # Install dependencies
    if [ -f "requirements.txt" ]; then
        print_status "Installing $name dependencies..."
        pip install -r requirements.txt
    else
        print_warning "No requirements.txt found in $dir"
    fi
    
    deactivate
    cd ..
    print_success "$name environment created successfully"
}

# Function to setup data directories
setup_directories() {
    print_status "Setting up data directories..."
    
    mkdir -p data/chromadb
    mkdir -p data/embeddings
    
    print_success "Data directories created"
}

# Function to copy environment file
setup_environment() {
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            print_status "Creating .env file from env.example..."
            cp env.example .env
            print_warning "Please edit .env file and add your GOOGLE_API_KEY"
        else
            print_error "env.example file not found"
            return 1
        fi
    else
        print_success ".env file already exists"
    fi
}

# Function to validate environment
validate_environment() {
    print_status "Validating installation..."
    
    # Check backend environment
    if [ -d "backend/venv" ]; then
        cd backend
        source venv/bin/activate
        
        # Test FastAPI import
        python -c "import fastapi; print('FastAPI OK')" 2>/dev/null || {
            print_error "FastAPI installation failed"
            deactivate
            cd ..
            return 1
        }
        
        # Test ChromaDB import
        python -c "import chromadb; print('ChromaDB OK')" 2>/dev/null || {
            print_error "ChromaDB installation failed"
            deactivate
            cd ..
            return 1
        }
        
        deactivate
        cd ..
    fi
    
    # Check frontend environment
    if [ -d "frontend/venv" ]; then
        cd frontend
        source venv/bin/activate
        
        # Test Streamlit import
        python -c "import streamlit; print('Streamlit OK')" 2>/dev/null || {
            print_error "Streamlit installation failed"
            deactivate
            cd ..
            return 1
        }
        
        deactivate
        cd ..
    fi
    
    print_success "Environment validation passed"
}

# Main installation process
main() {
    echo "=============================================="
    echo "  Financial Transcripts RAG - Installation  "
    echo "=============================================="
    echo ""
    
    # Check prerequisites
    print_status "Checking prerequisites..."
    
    if ! check_python_version; then
        exit 1
    fi
    
    if ! command_exists pip; then
        print_error "pip not found. Please install pip"
        exit 1
    fi
    
    # Setup environment file
    setup_environment
    
    # Setup data directories
    setup_directories
    
    # Create virtual environments and install dependencies
    print_status "Setting up backend environment..."
    if [ -f "backend/b_install.sh" ]; then
        print_status "Using component-specific backend installation..."
        cd backend
        ./b_install.sh || {
            print_error "Backend installation failed"
            exit 1
        }
        cd ..
    else
        create_venv "backend" "Backend (FastAPI)"
    fi
    
    print_status "Setting up frontend environment..."
    if [ -f "frontend/f_install.sh" ]; then
        print_status "Using component-specific frontend installation..."
        cd frontend
        ./f_install.sh || {
            print_error "Frontend installation failed"
            exit 1
        }
        cd ..
    else
        create_venv "frontend" "Frontend (Streamlit)"
    fi
    
    # Validate installation
    validate_environment
    
    echo ""
    echo "=============================================="
    print_success "Installation completed successfully!"
    echo "=============================================="
    echo ""
    print_status "Next steps:"
    echo "1. Edit .env file and add your GOOGLE_API_KEY"
    echo "2. Run './start.sh' to start the application"
    echo ""
    print_status "URLs after starting:"
    echo "- Frontend (Streamlit): http://localhost:8501"
    echo "- Backend API: http://localhost:8000"
    echo "- API Documentation: http://localhost:8000/docs"
    echo ""
}

# Handle script arguments
case "${1:-}" in
    --clean)
        print_status "Cleaning previous installations..."
        rm -rf backend/venv frontend/venv data/chromadb data/embeddings
        ;;
    --help)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --clean    Remove existing virtual environments and data"
        echo "  --help     Show this help message"
        exit 0
        ;;
esac

# Run main installation
main 