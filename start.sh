#!/bin/bash

# Financial Transcripts RAG Application - Startup Script
# This script starts both FastAPI backend and Streamlit frontend

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=8000
FRONTEND_PORT=8501
BACKEND_PID_FILE=".backend.pid"
FRONTEND_PID_FILE=".frontend.pid"
LOG_DIR="logs"

# Create logs directory
mkdir -p "$LOG_DIR"

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

print_backend() {
    echo -e "${PURPLE}[BACKEND]${NC} $1"
}

print_frontend() {
    echo -e "${BLUE}[FRONTEND]${NC} $1"
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

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            print_success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within $max_attempts seconds"
    return 1
}

# Function to start backend
start_backend() {
    print_status "Starting FastAPI backend..."
    
    if ! check_port $BACKEND_PORT; then
        print_error "Port $BACKEND_PORT is already in use"
        exit 1
    fi
    
    # Check if backend environment exists
    if [ ! -d "backend/venv" ]; then
        print_error "Backend virtual environment not found. Run ./install.sh first."
        exit 1
    fi
    
    cd backend
    
    # Start backend in background
    source venv/bin/activate
    nohup uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > "../$LOG_DIR/backend.log" 2>&1 &
    local backend_pid=$!
    echo $backend_pid > "../$BACKEND_PID_FILE"
    
    deactivate
    cd ..
    
    print_backend "Started with PID $backend_pid"
    
    # Wait for backend to be ready
    if ! wait_for_service "http://localhost:$BACKEND_PORT/health" "Backend API"; then
        stop_services
        exit 1
    fi
    
    print_backend "API available at: http://localhost:$BACKEND_PORT"
    print_backend "API docs available at: http://localhost:$BACKEND_PORT/docs"
}

# Function to start frontend
start_frontend() {
    print_status "Starting Streamlit frontend..."
    
    if ! check_port $FRONTEND_PORT; then
        print_error "Port $FRONTEND_PORT is already in use"
        exit 1
    fi
    
    # Check if frontend environment exists
    if [ ! -d "frontend/venv" ]; then
        print_error "Frontend virtual environment not found. Run ./install.sh first."
        exit 1
    fi
    
    cd frontend
    source venv/bin/activate
    
    print_frontend "Starting Streamlit application..."
    
    # Start Streamlit (this will run in foreground)
    export BACKEND_URL="http://localhost:$BACKEND_PORT"
    streamlit run app.py --server.port $FRONTEND_PORT --server.headless true --browser.gatherUsageStats false
}

# Function to stop services
stop_services() {
    print_status "Stopping services..."
    
    # Stop backend
    if [ -f "$BACKEND_PID_FILE" ]; then
        local backend_pid=$(cat "$BACKEND_PID_FILE")
        if kill -0 $backend_pid 2>/dev/null; then
            print_backend "Stopping backend (PID: $backend_pid)..."
            kill $backend_pid
            rm -f "$BACKEND_PID_FILE"
        fi
    fi
    
    # Stop any remaining processes
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    pkill -f "streamlit run" 2>/dev/null || true
    
    print_success "All services stopped"
}

# Function to show service status
show_status() {
    echo "=============================================="
    echo "           Service Status"
    echo "=============================================="
    
    # Check backend
    if [ -f "$BACKEND_PID_FILE" ]; then
        local backend_pid=$(cat "$BACKEND_PID_FILE")
        if kill -0 $backend_pid 2>/dev/null; then
            print_backend "Running (PID: $backend_pid) - http://localhost:$BACKEND_PORT"
        else
            print_backend "Not running (stale PID file)"
            rm -f "$BACKEND_PID_FILE"
        fi
    else
        print_backend "Not running"
    fi
    
    # Check frontend
    if pgrep -f "streamlit run" >/dev/null 2>&1; then
        print_frontend "Running - http://localhost:$FRONTEND_PORT"
    else
        print_frontend "Not running"
    fi
    
    echo ""
}

# Function to show logs
show_logs() {
    local service=${1:-all}
    
    case $service in
        backend)
            if [ -f "$LOG_DIR/backend.log" ]; then
                tail -f "$LOG_DIR/backend.log"
            else
                print_error "Backend log file not found"
            fi
            ;;
        all)
            if [ -f "$LOG_DIR/backend.log" ]; then
                print_status "Backend logs:"
                tail -20 "$LOG_DIR/backend.log"
                echo ""
            fi
            ;;
        *)
            print_error "Unknown service: $service"
            ;;
    esac
}

# Function to cleanup on script exit
cleanup() {
    echo ""
    print_status "Received interrupt signal. Cleaning up..."
    stop_services
    exit 0
}

# Function to check environment file
check_environment() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found"
        if [ -f "env.example" ]; then
            print_status "Creating .env from env.example..."
            cp env.example .env
            print_warning "Please edit .env file and add your GOOGLE_API_KEY"
            return 1
        else
            print_error "env.example file not found. Run ./install.sh first."
            exit 1
        fi
    fi
    
    # Check if GOOGLE_API_KEY is set
    if ! grep -q "GOOGLE_API_KEY=your_gemini_api_key_here" .env; then
        print_success "Environment file configured"
    else
        print_warning "Please edit .env file and add your actual GOOGLE_API_KEY"
        return 1
    fi
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --backend-only    Start only the FastAPI backend"
    echo "  --frontend-only   Start only the Streamlit frontend"
    echo "  --stop           Stop all running services"
    echo "  --status         Show status of all services"
    echo "  --logs [service] Show logs (backend, or all)"
    echo "  --verbose        Enable verbose output"
    echo "  --help           Show this help message"
    echo ""
    echo "Default: Start both backend and frontend services"
}

# Main execution
main() {
    # Set trap for cleanup on script interrupt
    trap cleanup SIGINT SIGTERM
    
    echo "=============================================="
    echo "    Financial Transcripts RAG - Startup     "
    echo "=============================================="
    echo ""
    
    # Check environment
    if ! check_environment; then
        print_error "Environment setup required. Please configure .env file."
        exit 1
    fi
    
    case "${1:-}" in
        --backend-only)
            if [ -f "backend/b_start.sh" ]; then
                print_status "Using component-specific backend startup..."
                cd backend
                ./b_start.sh
                cd ..
            else
                start_backend
                print_success "Backend started successfully!"
                print_status "Press Ctrl+C to stop"
                
                # Keep script running
                while true; do
                    sleep 1
                done
            fi
            ;;
        --frontend-only)
            if [ -f "frontend/f_start.sh" ]; then
                print_status "Using component-specific frontend startup..."
                cd frontend
                ./f_start.sh
                cd ..
            else
                start_frontend
            fi
            ;;
        --stop)
            stop_services
            ;;
        --status)
            show_status
            ;;
        --logs)
            show_logs "${2:-all}"
            ;;
        --verbose)
            set -x
            main
            ;;
        --help)
            show_help
            ;;
        "")
            # Default: start both services
            if [ -f "backend/b_start.sh" ] && [ -f "frontend/f_start.sh" ]; then
                print_status "Using component-specific scripts..."
                print_status "Starting backend in background..."
                cd backend
                ./b_start.sh --background
                cd ..
                
                print_status "Backend started! Starting frontend..."
                sleep 3
                
                # Start frontend (this will block)
                cd frontend
                ./f_start.sh
                cd ..
            else
                start_backend
                
                print_status "Backend started successfully! Starting frontend..."
                sleep 2
                
                # Start frontend (this will block)
                start_frontend
            fi
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 