#!/bin/bash

# Financial Transcripts RAG - Frontend Startup Script
# This script starts the Streamlit frontend application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_PORT=8501
BACKEND_URL=${BACKEND_URL:-"http://localhost:8000"}

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

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1  # Port is in use
    else
        return 0  # Port is available
    fi
}

# Function to check backend connectivity
check_backend() {
    print_status "Checking backend connectivity at $BACKEND_URL..."
    
    if curl -s --connect-timeout 5 "$BACKEND_URL/health" >/dev/null 2>&1; then
        print_success "Backend is accessible at $BACKEND_URL"
        return 0
    else
        print_warning "Backend not accessible at $BACKEND_URL"
        print_warning "Frontend will still start, but queries may fail"
        print_status "Make sure backend is running with: ./b_start.sh"
        return 1
    fi
}

# Function to load environment variables
load_environment() {
    if [ -f "../.env" ]; then
        print_status "Loading environment variables from .env..."
        export $(grep -v '^#' ../.env | xargs)
        
        # Update BACKEND_URL if set in .env
        if [ ! -z "$BACKEND_URL" ]; then
            print_status "Using BACKEND_URL from .env: $BACKEND_URL"
        fi
    else
        print_warning ".env file not found, using default backend URL: $BACKEND_URL"
    fi
}

# Function to start frontend
start_frontend() {
    print_status "Starting Streamlit frontend..."
    
    # Check if port is available
    if ! check_port $FRONTEND_PORT; then
        print_error "Port $FRONTEND_PORT is already in use"
        print_status "Please stop the existing process or use a different port"
        exit 1
    fi
    
    # Check if app.py exists
    if [ ! -f "app.py" ]; then
        print_error "Frontend application file (app.py) not found"
        exit 1
    fi
    
    # Activate virtual environment if it exists, otherwise use system Python
    if [ -d "venv" ]; then
        print_status "Using virtual environment..."
        source venv/bin/activate
    else
        print_status "Using system Python installation..."
        # Check if streamlit is available
        if ! python3 -c "import streamlit" 2>/dev/null; then
            print_error "Streamlit not found. Please run './f_install.sh' first"
            exit 1
        fi
    fi
    
    print_success "Frontend environment ready"
    
    # Set backend URL for the frontend
    export BACKEND_URL="$BACKEND_URL"
    
    print_status "Starting Streamlit application..."
    print_status "Frontend will be available at: http://localhost:$FRONTEND_PORT"
    print_status "Backend URL configured as: $BACKEND_URL"
    print_status ""
    print_status "Press Ctrl+C to stop the frontend"
    print_status ""
    
    # Start Streamlit - use python3 -m streamlit if streamlit command not in PATH
    if command -v streamlit >/dev/null 2>&1; then
        streamlit run app.py \
            --server.port $FRONTEND_PORT \
            --server.headless true \
            --browser.gatherUsageStats false \
            --theme.primaryColor "#1f77b4" \
            --theme.backgroundColor "#ffffff" \
            --theme.secondaryBackgroundColor "#f0f2f6"
    else
        python3 -m streamlit run app.py \
            --server.port $FRONTEND_PORT \
            --server.headless true \
            --browser.gatherUsageStats false \
            --theme.primaryColor "#1f77b4" \
            --theme.backgroundColor "#ffffff" \
            --theme.secondaryBackgroundColor "#f0f2f6"
    fi
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Starts the Streamlit frontend for Financial Transcripts RAG"
    echo ""
    echo "Options:"
    echo "  --port PORT      Set frontend port (default: 8501)"
    echo "  --backend URL    Set backend URL (default: http://localhost:8000)"
    echo "  --check-only     Only check prerequisites and exit"
    echo "  --help           Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  BACKEND_URL      Backend API URL (can be set in .env file)"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Start with defaults"
    echo "  $0 --port 8502                       # Start on port 8502"
    echo "  $0 --backend http://api.example.com  # Use remote backend"
    echo ""
}

# Function to cleanup on script exit
cleanup() {
    echo ""
    print_status "Received interrupt signal. Stopping frontend..."
    # Streamlit handles its own cleanup
    exit 0
}

# Main execution
main() {
    # Set trap for cleanup on script interrupt
    trap cleanup SIGINT SIGTERM
    
    echo "=============================================="
    echo "   Financial Transcripts RAG - Frontend     "
    echo "             Startup Script                  "
    echo "=============================================="
    echo ""
    
    # Load environment variables
    load_environment
    
    # Check backend connectivity (non-blocking)
    check_backend || true
    
    # Start frontend
    start_frontend
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            FRONTEND_PORT="$2"
            shift 2
            ;;
        --backend)
            BACKEND_URL="$2"
            shift 2
            ;;
        --check-only)
            load_environment
            check_backend
            if [ -d "venv" ] || python3 -c "import streamlit" 2>/dev/null; then
                print_success "Frontend environment is ready"
            else
                print_error "Frontend environment not found. Run ./f_install.sh first"
                exit 1
            fi
            exit 0
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Run main function
main 