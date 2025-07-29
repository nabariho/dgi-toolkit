#!/bin/bash

# DGI Toolkit - Automated Test Runner
# Ensures proper test environment isolation and provides different test modes

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_DATA_DIR="$PROJECT_ROOT/tests/test_data"
COVERAGE_DIR="$PROJECT_ROOT/htmlcov"

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

# Function to check if we're in the right directory
check_environment() {
    if [[ ! -f "$PROJECT_ROOT/pyproject.toml" ]]; then
        print_error "pyproject.toml not found. Please run this script from the dgi-toolkit directory."
        exit 1
    fi

    if [[ ! -d "$PROJECT_ROOT/tests" ]]; then
        print_error "tests directory not found. Please ensure you're in the correct project directory."
        exit 1
    fi

    print_success "Environment check passed"
}

# Function to ensure test data directory exists
setup_test_data() {
    print_status "Setting up test data directory..."

    if [[ ! -d "$TEST_DATA_DIR" ]]; then
        mkdir -p "$TEST_DATA_DIR"
        print_success "Created test data directory: $TEST_DATA_DIR"
    fi

    # Create test data file if it doesn't exist
    TEST_CSV_FILE="$TEST_DATA_DIR/test_fundamentals.csv"
    if [[ ! -f "$TEST_CSV_FILE" ]]; then
        cat > "$TEST_CSV_FILE" << 'EOF'
symbol,name,sector,industry,dividend_yield,payout,dividend_cagr,fcf_yield
TEST1,Test Company 1,Technology,Software,0.025,30.0,0.08,5.0
TEST2,Test Company 2,Healthcare,Pharmaceuticals,0.035,45.0,0.12,4.5
TEST3,Test Company 3,Consumer,Retail,0.020,25.0,0.06,3.8
TEST4,Test Company 4,Finance,Banking,0.040,60.0,0.15,6.2
TEST5,Test Company 5,Energy,Oil & Gas,0.050,70.0,0.10,7.1
EOF
        print_success "Created test data file: $TEST_CSV_FILE"
    fi
}

# Function to run tests with isolation
run_tests() {
    local test_type="$1"
    local coverage="$2"
    local verbose="$3"

    print_status "Running tests with isolation..."

    # Set test environment variables
    export DGI_ENVIRONMENT="test"
    export DGI_DATA_PATH="$TEST_DATA_DIR/test_fundamentals.csv"

    # Clear sensitive environment variables for tests
    unset OPENAI_API_KEY
    unset ANTHROPIC_API_KEY

    print_status "Test environment: $DGI_ENVIRONMENT"
    print_status "Test data path: $DGI_DATA_PATH"
    print_status "API keys cleared for security"

    # Build pytest command
    local pytest_cmd="poetry run pytest"

    # Add test type filter
    case "$test_type" in
        "unit")
            pytest_cmd="$pytest_cmd -m unit"
            print_status "Running unit tests only"
            ;;
        "integration")
            pytest_cmd="$pytest_cmd -m integration"
            print_status "Running integration tests only"
            ;;
        "api")
            pytest_cmd="$pytest_cmd -m api"
            print_status "Running API tests only"
            ;;
        "fast")
            pytest_cmd="$pytest_cmd -m 'not slow'"
            print_status "Running fast tests (excluding slow ones)"
            ;;
        "all")
            print_status "Running all tests"
            ;;
        *)
            print_error "Unknown test type: $test_type"
            print_status "Available types: unit, integration, api, fast, all"
            exit 1
            ;;
    esac

    # Add coverage options
    if [[ "$coverage" == "true" ]]; then
        pytest_cmd="$pytest_cmd --cov=dgi --cov=api --cov-report=term-missing --cov-report=html"
        print_status "Coverage reporting enabled"
    fi

    # Add verbose output
    if [[ "$verbose" == "true" ]]; then
        pytest_cmd="$pytest_cmd -v"
    fi

    # Run the tests
    print_status "Executing: $pytest_cmd"
    echo "=========================================="

    if eval "$pytest_cmd"; then
        print_success "All tests passed!"

        if [[ "$coverage" == "true" && -d "$COVERAGE_DIR" ]]; then
            print_success "Coverage report generated: $COVERAGE_DIR/index.html"
        fi
    else
        print_error "Tests failed!"
        exit 1
    fi
}

# Function to run test server
run_test_server() {
    print_status "Starting test server with isolated environment..."

    # Set test environment
    export DGI_ENVIRONMENT="test"
    export DGI_DATA_PATH="$TEST_DATA_DIR/test_fundamentals.csv"

    # Clear sensitive environment variables
    unset OPENAI_API_KEY
    unset ANTHROPIC_API_KEY

    print_status "Test server environment:"
    print_status "  - DGI_ENVIRONMENT: $DGI_ENVIRONMENT"
    print_status "  - DGI_DATA_PATH: $DGI_DATA_PATH"
    print_status "  - API keys: cleared"
    print_status ""
    print_status "Starting server on http://localhost:8000"
    print_status "API Documentation: http://localhost:8000/docs"
    print_status "Health Check: http://localhost:8000/healthz"
    print_status "Press Ctrl+C to stop"

    poetry run python run_test_server.py
}

# Function to show help
show_help() {
    echo "DGI Toolkit - Automated Test Runner"
    echo ""
    echo "Usage: $0 [OPTIONS] [TEST_TYPE]"
    echo ""
    echo "TEST_TYPE (optional):"
    echo "  unit        Run unit tests only"
    echo "  integration Run integration tests only"
    echo "  api         Run API tests only"
    echo "  fast        Run fast tests (exclude slow ones)"
    echo "  all         Run all tests (default)"
    echo ""
    echo "OPTIONS:"
    echo "  -c, --coverage    Enable coverage reporting"
    echo "  -v, --verbose     Verbose output"
    echo "  -s, --server      Start test server instead of running tests"
    echo "  -h, --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all tests"
    echo "  $0 api                # Run API tests only"
    echo "  $0 -c unit            # Run unit tests with coverage"
    echo "  $0 -v -c integration  # Run integration tests with verbose output and coverage"
    echo "  $0 -s                 # Start test server"
    echo ""
    echo "Environment Isolation:"
    echo "  - Test environment variables are automatically set"
    echo "  - Production API keys are cleared for security"
    echo "  - Test data is isolated from production data"
    echo "  - All tests use TEST* symbols (no real company data)"
}

# Main script logic
main() {
    local test_type="all"
    local coverage="false"
    local verbose="false"
    local server_mode="false"

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -c|--coverage)
                coverage="true"
                shift
                ;;
            -v|--verbose)
                verbose="true"
                shift
                ;;
            -s|--server)
                server_mode="true"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            unit|integration|api|fast|all)
                test_type="$1"
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Check environment
    check_environment

    # Setup test data
    setup_test_data

    # Run tests or start server
    if [[ "$server_mode" == "true" ]]; then
        run_test_server
    else
        run_tests "$test_type" "$coverage" "$verbose"
    fi
}

# Run main function with all arguments
main "$@"
