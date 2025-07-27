#!/bin/bash

# Quick test script for FlowProcessor
# Run this script to quickly test your changes before committing

set -e  # Exit on any error

echo "🧪 Running FlowProcessor quick test suite..."

# Change to the project directory
cd "$(dirname "$0")/.."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Virtual environment not detected. Tests may fail."
    echo "   Activate your virtual environment: source venv/bin/activate"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    if [[ $status -eq 0 ]]; then
        echo -e "${GREEN}✅${NC} $message"
    else
        echo -e "${RED}❌${NC} $message"
        return 1
    fi
}

# Run tests in parallel for speed
echo "📋 Running tests..."
pytest tests/ -v --tb=short --maxfail=5 &
TEST_PID=$!

# Wait for tests to complete
wait $TEST_PID
TEST_RESULT=$?

if [[ $TEST_RESULT -eq 0 ]]; then
    print_status 0 "All tests passed"
else
    print_status 1 "Some tests failed"
    exit 1
fi

# Run coverage check
echo "📊 Checking coverage..."
COVERAGE_OUTPUT=$(pytest --cov=flowproc --cov-report=term-missing --tb=no 2>/dev/null | tail -n 1)
if echo "$COVERAGE_OUTPUT" | grep -q "TOTAL"; then
    print_status 0 "Coverage check completed"
else
    print_status 1 "Coverage check failed"
    exit 1
fi

# Run linting
echo "🔍 Running linting checks..."
if command -v flake8 &> /dev/null; then
    if flake8 flowproc/ --max-line-length=88 --extend-ignore=E203,W503; then
        print_status 0 "Linting passed"
    else
        print_status 1 "Linting failed"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  flake8 not found, skipping linting${NC}"
fi

# Run type checking
echo "🔍 Running type checks..."
if command -v mypy &> /dev/null; then
    if mypy flowproc/ --ignore-missing-imports; then
        print_status 0 "Type checking passed"
    else
        print_status 1 "Type checking failed"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  mypy not found, skipping type checking${NC}"
fi

echo ""
echo -e "${GREEN}🎉 All checks passed! Your code is ready to commit.${NC}"
echo ""
echo "💡 Next steps:"
echo "   git add ."
echo "   git commit -m 'Your commit message'"
echo ""
echo "   The pre-commit hooks will run automatically and ensure everything is still working." 