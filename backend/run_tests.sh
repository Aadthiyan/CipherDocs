#!/bin/bash
# Test Runner Script for Cipherdocs Backend
# Convenience script to run tests with various configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_header() {
    echo -e "${BLUE}===================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check if we're in backend directory
if [ ! -f "pytest.ini" ]; then
    print_error "pytest.ini not found. Please run this script from the backend directory."
    exit 1
fi

# Show usage
show_help() {
    echo "Usage: ./run_tests.sh [option]"
    echo ""
    echo "Options:"
    echo "  all              Run all tests with coverage (default)"
    echo "  unit             Run unit tests only"
    echo "  auth             Run authentication tests"
    echo "  encryption       Run encryption tests"
    echo "  chunking         Run chunking tests"
    echo "  embedding        Run embedding tests"
    echo "  database         Run database tests"
    echo "  coverage         Run with detailed coverage report"
    echo "  fast             Run fast tests only (skip slow tests)"
    echo "  verbose          Run with verbose output"
    echo "  report           Generate HTML coverage report only"
    echo "  help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run_tests.sh all          # Run all tests"
    echo "  ./run_tests.sh auth -v      # Run auth tests verbosely"
    echo "  ./run_tests.sh coverage     # Run with coverage report"
}

# Run all tests with coverage
run_all_tests() {
    print_header "Running All Tests with Coverage"
    python -m pytest \
        --cov=app \
        --cov-report=html:htmlcov \
        --cov-report=term-missing \
        -v
    print_success "All tests completed"
}

# Run unit tests only
run_unit_tests() {
    print_header "Running Unit Tests"
    python -m pytest tests/test_*_comprehensive.py -v
    print_success "Unit tests completed"
}

# Run auth tests
run_auth_tests() {
    print_header "Running Authentication Tests"
    python -m pytest tests/test_auth_jwt_comprehensive.py -v
    print_success "Auth tests completed"
}

# Run encryption tests
run_encryption_tests() {
    print_header "Running Encryption Tests"
    python -m pytest tests/test_encryption_comprehensive.py -v
    print_success "Encryption tests completed"
}

# Run chunking tests
run_chunking_tests() {
    print_header "Running Chunking Tests"
    python -m pytest tests/test_chunking_comprehensive.py -v
    print_success "Chunking tests completed"
}

# Run embedding tests
run_embedding_tests() {
    print_header "Running Embedding Tests"
    python -m pytest tests/test_embedding_comprehensive.py -v
    print_success "Embedding tests completed"
}

# Run database tests
run_database_tests() {
    print_header "Running Database Tests"
    python -m pytest tests/test_database_ops.py -v
    print_success "Database tests completed"
}

# Run with detailed coverage
run_coverage_report() {
    print_header "Running Tests with Detailed Coverage"
    python -m pytest \
        --cov=app \
        --cov-report=html:htmlcov \
        --cov-report=term-missing \
        --cov-report=xml \
        --cov-branch \
        -v
    print_success "Coverage report generated in htmlcov/index.html"
}

# Run fast tests only
run_fast_tests() {
    print_header "Running Fast Tests (excluding slow tests)"
    python -m pytest -m "not slow" -v
    print_success "Fast tests completed"
}

# Run verbose
run_verbose() {
    print_header "Running All Tests (Verbose)"
    python -m pytest -vv
    print_success "Tests completed"
}

# Generate coverage report only
generate_report() {
    print_header "Generating HTML Coverage Report"
    if [ -d "htmlcov" ]; then
        print_warning "Existing htmlcov directory found, overwriting..."
    fi
    python -m pytest \
        --cov=app \
        --cov-report=html:htmlcov \
        --cov-report=term-missing \
        -q
    print_success "Coverage report generated in htmlcov/index.html"
    
    # Try to open in browser
    if command -v xdg-open &> /dev/null; then
        xdg-open htmlcov/index.html
    elif command -v open &> /dev/null; then
        open htmlcov/index.html
    elif command -v start &> /dev/null; then
        start htmlcov/index.html
    else
        print_warning "Could not auto-open browser. Open htmlcov/index.html manually."
    fi
}

# Show test statistics
show_stats() {
    print_header "Test Suite Statistics"
    
    # Count test files
    test_files=$(find tests -name "test_*.py" -type f | wc -l)
    echo "Test files: $test_files"
    
    # Count test functions (approximate)
    test_count=$(grep -r "def test_" tests/ | wc -l)
    echo "Test functions: $test_count"
    
    # Count test classes
    class_count=$(grep -r "class Test" tests/ | wc -l)
    echo "Test classes: $class_count"
    
    # Count assertions (approximate)
    assertion_count=$(grep -r "assert " tests/ | wc -l)
    echo "Assertions: $assertion_count"
    
    # Count lines of test code
    lines=$(find tests -name "test_*.py" -exec wc -l {} + | tail -1 | awk '{print $1}')
    echo "Total test code lines: $lines"
    
    print_header ""
}

# Main script logic
case "${1:-all}" in
    all)
        run_all_tests
        ;;
    unit)
        run_unit_tests
        ;;
    auth)
        run_auth_tests
        ;;
    encryption)
        run_encryption_tests
        ;;
    chunking)
        run_chunking_tests
        ;;
    embedding)
        run_embedding_tests
        ;;
    database)
        run_database_tests
        ;;
    coverage)
        run_coverage_report
        ;;
    fast)
        run_fast_tests
        ;;
    verbose)
        run_verbose
        ;;
    report)
        generate_report
        ;;
    stats)
        show_stats
        ;;
    help)
        show_help
        ;;
    *)
        print_error "Unknown option: $1"
        echo ""
        show_help
        exit 1
        ;;
esac

echo ""
print_success "Test execution completed at $(date '+%Y-%m-%d %H:%M:%S')"
