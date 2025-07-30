#!/bin/bash

# Financial Transcripts RAG - Backend Startup Script
# This script starts the FastAPI backend application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=8000
BACKEND_HOST="0.0.0.0"
BACKEND_PID_FILE=".backend.pid"
LOG_DIR="logs"

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

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1  # Port is in use
    else
        return 0  # Port is available
    fi
}

# Function to load environment variables
load_environment() {
    if [ -f "../.env" ]; then
        print_status "Loading environment variables from .env..."
        export $(grep -v '^#' ../.env | xargs)
        
        # Update configuration from environment
        BACKEND_PORT=${BACKEND_PORT:-8000}
        BACKEND_HOST=${BACKEND_HOST:-"0.0.0.0"}
    else
        print_warning ".env file not found, using default configuration"
    fi
}

# Function to check configuration
check_configuration() {
    print_status "Checking backend configuration..."
    
    # Check if Google API key is configured
    if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" = "your_gemini_api_key_here" ]; then
        print_error "GOOGLE_API_KEY not configured in .env file"
        print_status "Please edit .env and add your Google Gemini Pro API key"
        print_status "Get your API key from: https://makersuite.google.com/app/apikey"
        return 1
    fi
    
    print_success "Configuration looks good"
    return 0
}

# Function to check transcript data
check_transcript_data() {
    local transcripts_path=${TRANSCRIPTS_PATH:-"../Transcripts"}
    
    if [ -d "$transcripts_path" ]; then
        local count=$(find "$transcripts_path" -name "*.txt" 2>/dev/null | wc -l)
        if [ $count -gt 0 ]; then
            print_success "Found $count transcript files"
        else
            print_warning "No transcript files found in $transcripts_path"
        fi
    else
        print_warning "Transcript directory not found: $transcripts_path"
        print_status "You can still start the backend, but you'll need data for queries"
    fi
}

# Function to start backend
start_backend() {
    print_status "Starting FastAPI backend..."
    
    # Check if port is available
    if ! check_port $BACKEND_PORT; then
        print_error "Port $BACKEND_PORT is already in use"
        print_status "Please stop the existing process or use a different port"
        exit 1
    fi
    
    # Check if main.py exists
    if [ ! -f "app/main.py" ]; then
        print_error "Backend application file (main.py) not found"
        exit 1
    fi
    
    # Create logs directory
    mkdir -p "../$LOG_DIR"
    
    # Activate virtual environment if it exists, otherwise use system Python
    if [ -d "venv" ]; then
        print_status "Using virtual environment..."
        source venv/bin/activate
    else
        print_status "Using system Python installation..."
        # Check if fastapi is available
        if ! python3 -c "import fastapi" 2>/dev/null; then
            print_error "FastAPI not found. Please run './b_install.sh' first"
            exit 1
        fi
    fi
    
    print_success "Backend environment ready"
    print_status "Starting uvicorn server..."
    print_status "Backend will be available at: http://localhost:$BACKEND_PORT"
    print_status "API Documentation: http://localhost:$BACKEND_PORT/docs"
    print_status "Health Check: http://localhost:$BACKEND_PORT/health"
    print_status ""
    print_status "Press Ctrl+C to stop the backend"
    print_status ""
    
    # Start FastAPI with uvicorn - use python3 -m uvicorn if uvicorn command not in PATH
    if command -v uvicorn >/dev/null 2>&1; then
        uvicorn app.main:app \
            --host "$BACKEND_HOST" \
            --port "$BACKEND_PORT" \
            --reload \
            --log-level info \
            --access-log
    else
        python3 -m uvicorn app.main:app \
            --host "$BACKEND_HOST" \
            --port "$BACKEND_PORT" \
            --reload \
            --log-level info \
            --access-log
    fi
}

# Function to start backend in background
start_backend_background() {
    print_status "Starting FastAPI backend in background..."
    
    # Check if port is available
    if ! check_port $BACKEND_PORT; then
        print_error "Port $BACKEND_PORT is already in use"
        return 1
    fi
    
    # Create logs directory
    mkdir -p "../$LOG_DIR"
    
    # Activate virtual environment if it exists, otherwise use system Python
    if [ -d "venv" ]; then
        print_status "Using virtual environment..."
        source venv/bin/activate
    else
        print_status "Using system Python installation..."
        # Check if fastapi is available
        if ! python3 -c "import fastapi" 2>/dev/null; then
            print_error "FastAPI not found. Please run './b_install.sh' first"
            return 1
        fi
    fi
    
    # Start backend in background - use python3 -m uvicorn if uvicorn command not in PATH
    if command -v uvicorn >/dev/null 2>&1; then
        nohup uvicorn app.main:app \
            --host "$BACKEND_HOST" \
            --port "$BACKEND_PORT" \
            --reload > "../$LOG_DIR/backend.log" 2>&1 &
    else
        nohup python3 -m uvicorn app.main:app \
            --host "$BACKEND_HOST" \
            --port "$BACKEND_PORT" \
            --reload > "../$LOG_DIR/backend.log" 2>&1 &
    fi
    
    local backend_pid=$!
    echo $backend_pid > "../$BACKEND_PID_FILE"
    
    deactivate
    
    print_success "Backend started in background with PID $backend_pid"
    print_status "Backend available at: http://localhost:$BACKEND_PORT"
    print_status "Logs available at: $LOG_DIR/backend.log"
    
    return 0
}

# Function to stop backend
stop_backend() {
    print_status "Stopping backend..."
    
    if [ -f "../$BACKEND_PID_FILE" ]; then
        local backend_pid=$(cat "../$BACKEND_PID_FILE")
        if kill -0 $backend_pid 2>/dev/null; then
            print_status "Stopping backend (PID: $backend_pid)..."
            kill $backend_pid
            rm -f "../$BACKEND_PID_FILE"
            print_success "Backend stopped"
        else
            print_warning "Backend process not running (stale PID file)"
            rm -f "../$BACKEND_PID_FILE"
        fi
    else
        print_warning "No PID file found"
    fi
    
    # Stop any remaining uvicorn processes
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
}

# Function to show backend status
show_status() {
    print_status "Backend Status:"
    
    if [ -f "../$BACKEND_PID_FILE" ]; then
        local backend_pid=$(cat "../$BACKEND_PID_FILE")
        if kill -0 $backend_pid 2>/dev/null; then
            print_success "Running (PID: $backend_pid) - http://localhost:$BACKEND_PORT"
        else
            print_warning "Not running (stale PID file)"
            rm -f "../$BACKEND_PID_FILE"
        fi
    else
        print_warning "Not running"
    fi
}

# Function to show logs
show_logs() {
    if [ -f "../$LOG_DIR/backend.log" ]; then
        print_status "Backend logs (last 50 lines):"
        tail -50 "../$LOG_DIR/backend.log"
    else
        print_warning "No log file found at $LOG_DIR/backend.log"
    fi
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Starts the FastAPI backend for Financial Transcripts RAG"
    echo ""
    echo "Options:"
    echo "  --port PORT      Set backend port (default: 8000)"
    echo "  --host HOST      Set backend host (default: 0.0.0.0)"
    echo "  --background     Start in background mode"
    echo "  --stop           Stop background backend"
    echo "  --status         Show backend status"
    echo "  --logs           Show backend logs"
    echo "  --check-only     Only check prerequisites and exit"
    echo "  --help           Show this help message"
    echo ""
    echo "Environment variables (set in .env file):"
    echo "  GOOGLE_API_KEY   Google Gemini Pro API key (required)"
    echo "  BACKEND_HOST     Backend host address"
    echo "  BACKEND_PORT     Backend port number"
    echo ""
    echo "Examples:"
    echo "  $0                          # Start in foreground"
    echo "  $0 --background             # Start in background"
    echo "  $0 --port 8001              # Start on port 8001"
    echo "  $0 --stop                   # Stop background process"
    echo ""
}

# Function to cleanup on script exit
cleanup() {
    echo ""
    print_status "Received interrupt signal. Stopping backend..."
    # uvicorn handles its own cleanup when run in foreground
    exit 0
}

# Main execution
main() {
    # Set trap for cleanup on script interrupt (only for foreground mode)
    trap cleanup SIGINT SIGTERM
    
    echo "=============================================="
    echo "   Financial Transcripts RAG - Backend      "
    echo "             Startup Script                  "
    echo "=============================================="
    echo ""
    
    # Load environment variables
    load_environment
    
    # Check configuration
    if ! check_configuration; then
        exit 1
    fi
    
    # Check transcript data (non-blocking)
    check_transcript_data
    
    # Start backend based on mode
    if [ "$BACKGROUND_MODE" = "true" ]; then
        start_backend_background
    else
        start_backend
    fi
}

# Parse command line arguments
BACKGROUND_MODE="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            BACKEND_PORT="$2"
            shift 2
            ;;
        --host)
            BACKEND_HOST="$2"
            shift 2
            ;;
        --background)
            BACKGROUND_MODE="true"
            shift
            ;;
        --stop)
            load_environment
            stop_backend
            exit 0
            ;;
        --status)
            show_status
            exit 0
            ;;
        --logs)
            show_logs
            exit 0
            ;;
        --check-only)
            load_environment
            check_configuration && print_success "Backend is ready to start"
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