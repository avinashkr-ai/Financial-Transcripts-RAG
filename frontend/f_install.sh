#!/bin/bash

# Financial Transcripts RAG - Frontend Installation Script
# This script sets up the Streamlit frontend environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[FRONTEND]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[FRONTEND]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[FRONTEND]${NC} $1"
}

print_error() {
    echo -e "${RED}[FRONTEND]${NC} $1"
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

# Function to create or update frontend virtual environment
create_frontend_venv() {
    if [ -d "venv" ]; then
        print_status "Frontend virtual environment already exists, updating dependencies..."
        source venv/bin/activate
        
        # Upgrade pip
        print_status "Upgrading pip..."
        python3 -m pip install --upgrade pip
        
        # Install/update frontend dependencies
        if [ -f "requirements.txt" ]; then
            print_status "Updating Streamlit and frontend dependencies..."
            python3 -m pip install -r requirements.txt
        else
            print_error "No requirements.txt found in frontend directory"
            deactivate
            return 1
        fi
        
        deactivate
        print_success "Frontend environment updated successfully"
    else
        print_status "Creating frontend virtual environment..."
        python3 -m venv venv
        
        # Activate virtual environment
        source venv/bin/activate
        
        # Upgrade pip
        print_status "Upgrading pip..."
        python3 -m pip install --upgrade pip
        
        # Install frontend dependencies
        if [ -f "requirements.txt" ]; then
            print_status "Installing Streamlit and frontend dependencies..."
            python3 -m pip install -r requirements.txt
        else
            print_error "No requirements.txt found in frontend directory"
            deactivate
            return 1
        fi
        
        deactivate
        print_success "Frontend environment created successfully"
    fi
}

# Function to validate frontend installation
validate_frontend_installation() {
    print_status "Validating frontend installation..."
    
    if [ -d "venv" ]; then
        source venv/bin/activate
        
        # Test Streamlit import
        python -c "import streamlit; print('✓ Streamlit OK')" 2>/dev/null || {
            print_error "Streamlit installation failed"
            deactivate
            return 1
        }
        
        # Test requests import
        python -c "import requests; print('✓ Requests OK')" 2>/dev/null || {
            print_error "Requests installation failed"
            deactivate
            return 1
        }
        
        # Test plotly import
        python -c "import plotly; print('✓ Plotly OK')" 2>/dev/null || {
            print_error "Plotly installation failed"
            deactivate
            return 1
        }
        
        deactivate
        print_success "Frontend validation passed"
        return 0
    else
        print_error "Frontend virtual environment not found"
        return 1
    fi
}

# Function to setup frontend configuration
setup_frontend_config() {
    print_status "Setting up frontend configuration..."
    
    # Check if .env exists in project root
    if [ ! -f "../.env" ]; then
        if [ -f "../env.example" ]; then
            print_status "Creating .env file from env.example..."
            cp ../env.example ../.env
            print_warning "Please edit .env file and add your GOOGLE_API_KEY"
        else
            print_warning "env.example file not found, creating basic .env..."
            cat > ../.env << 'EOF'
# Backend URL for frontend to connect to
BACKEND_URL=http://localhost:8000

# Google Gemini Pro API (required for backend)
GOOGLE_API_KEY=your_gemini_api_key_here
EOF
            print_warning "Please edit .env file and configure BACKEND_URL and GOOGLE_API_KEY"
        fi
    else
        print_success ".env file already exists"
    fi
    
    # Ensure BACKEND_URL is set in .env
    if ! grep -q "BACKEND_URL" ../.env; then
        echo "BACKEND_URL=http://localhost:8000" >> ../.env
        print_status "Added BACKEND_URL to .env file"
    fi
}

# Main installation process
main() {
    echo "=============================================="
    echo "   Financial Transcripts RAG - Frontend     "
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
    
    # Check if we're in the frontend directory
    if [ ! -f "app.py" ]; then
        print_error "Frontend app files not found. Please run from frontend directory."
        exit 1
    fi
    
    # Setup frontend configuration
    setup_frontend_config
    
    # Create frontend virtual environment and install dependencies
    create_frontend_venv
    
    # Validate installation
    validate_frontend_installation
    
    echo ""
    echo "=============================================="
    print_success "Frontend installation completed successfully!"
    echo "=============================================="
    echo ""
    print_status "Next steps:"
    echo "1. Make sure the backend is running (use ./b_start.sh)"
    echo "2. Run './f_start.sh' to start the Streamlit frontend"
    echo ""
    print_status "Frontend will be available at:"
    echo "- Streamlit UI: http://localhost:8501"
    echo ""
    print_status "Configuration:"
    echo "- Edit .env file to set BACKEND_URL if backend is on different host/port"
    echo ""
}

# Handle script arguments
case "${1:-}" in
    --clean)
        print_status "Cleaning previous frontend installation..."
        rm -rf venv
        ;;
    --help)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --clean    Remove existing frontend virtual environment"
        echo "  --help     Show this help message"
        exit 0
        ;;
esac

# Run main installation
main 