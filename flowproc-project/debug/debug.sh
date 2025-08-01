#!/bin/bash

# FlowProcessor Debug Tools
# Easy access to debugging and monitoring tools

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to check if virtual environment is activated
check_venv() {
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        print_error "Virtual environment not activated!"
        print_info "Please run: source venv/bin/activate"
        exit 1
    fi
    print_status "Virtual environment active: $VIRTUAL_ENV"
}

# Function to show usage
show_usage() {
    echo "FlowProcessor Debug Tools"
    echo "========================"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  quick     - Run quick diagnostic check"
    echo "  health    - Run comprehensive health check"
    echo "  monitor   - Run application with monitoring"
    echo "  logs      - Show recent log entries"
    echo "  status    - Show current system status"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 quick     # Quick environment check"
    echo "  $0 health    # Full system health check"
    echo "  $0 monitor   # Launch app with monitoring"
    echo "  $0 logs      # View recent logs"
}

# Function to run quick diagnostic
run_quick() {
    print_info "Running quick diagnostic..."
    python debug/quick_debug.py
}

# Function to run health check
run_health() {
    print_info "Running comprehensive health check..."
    python debug/debug_monitor.py health
}

# Function to run with monitoring
run_monitor() {
    print_info "Starting FlowProcessor with monitoring..."
    print_warning "Press Ctrl+C to stop monitoring"
    python debug/debug_monitor.py monitor
}

# Function to show logs
show_logs() {
    print_info "Recent log entries:"
    echo ""
    
    # Check for main log file
    if [[ -f "flowproc/data/logs/processing.log" ]]; then
        echo "=== Main Application Log ==="
        tail -20 flowproc/data/logs/processing.log
        echo ""
    else
        print_warning "Main log file not found"
    fi
    
    # Check for debug log file
    if [[ -f "debug.log" ]]; then
        echo "=== Debug Log ==="
        tail -10 debug.log
        echo ""
    else
        print_info "Debug log not found (run monitor first)"
    fi
}

# Function to show system status
show_status() {
    print_info "System Status:"
    echo ""
    
    # Check if any flowproc processes are running
    if pgrep -f flowproc > /dev/null; then
        print_status "FlowProcessor processes running:"
        ps aux | grep flowproc | grep -v grep
    else
        print_info "No FlowProcessor processes running"
    fi
    
    echo ""
    
    # Check log file sizes
    if [[ -f "flowproc/data/logs/processing.log" ]]; then
        size=$(du -h flowproc/data/logs/processing.log | cut -f1)
        print_info "Main log size: $size"
    fi
    
    if [[ -f "debug.log" ]]; then
        size=$(du -h debug.log | cut -f1)
        print_info "Debug log size: $size"
    fi
    
    echo ""
    
    # Check available disk space
    available=$(df -h . | tail -1 | awk '{print $4}')
    print_info "Available disk space: $available"
}

# Main script logic
main() {
    # Check if virtual environment is activated
    check_venv
    
    # Parse command
    case "${1:-help}" in
        "quick")
            run_quick
            ;;
        "health")
            run_health
            ;;
        "monitor")
            run_monitor
            ;;
        "logs")
            show_logs
            ;;
        "status")
            show_status
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 