#!/bin/bash

# SkillForge Test Runner
# Runs unit, integration, and optionally E2E tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Running SkillForge Test Suite...${NC}"
echo ""

# Parse arguments
RUN_E2E=false
RUN_COVERAGE=true
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            RUN_E2E=true
            shift
            ;;
        --no-coverage)
            RUN_COVERAGE=false
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--full] [--no-coverage] [--verbose]"
            exit 1
            ;;
    esac
done

# Initialize result variables
unit_result=0
integration_result=0
e2e_result=0

# Build pytest command
PYTEST_CMD="pytest"
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -vv"
else
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [ "$RUN_COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=skillforge --cov-report=html --cov-report=term-missing"
fi

# 1. Unit Tests
echo -e "${YELLOW}1️⃣  Running unit tests...${NC}"
$PYTEST_CMD tests/unit/ -m "not slow" || unit_result=$?

if [ $unit_result -eq 0 ]; then
    echo -e "${GREEN}✅ Unit tests passed${NC}"
else
    echo -e "${RED}❌ Unit tests failed${NC}"
fi

echo ""

# 2. Integration Tests
echo -e "${YELLOW}2️⃣  Running integration tests...${NC}"
pytest -v tests/integration/ -m "integration" || integration_result=$?

if [ $integration_result -eq 0 ]; then
    echo -e "${GREEN}✅ Integration tests passed${NC}"
else
    echo -e "${RED}❌ Integration tests failed${NC}"
fi

echo ""

# 3. E2E Tests (optional)
if [ "$RUN_E2E" = true ]; then
    echo -e "${YELLOW}3️⃣  Running E2E tests (this may take a while)...${NC}"
    pytest -v tests/e2e/ -m "e2e and slow" || e2e_result=$?

    if [ $e2e_result -eq 0 ]; then
        echo -e "${GREEN}✅ E2E tests passed${NC}"
    else
        echo -e "${RED}❌ E2E tests failed${NC}"
    fi
else
    echo -e "${BLUE}⏭️   Skipping E2E tests (use --full to run them)${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Summary
echo -e "${BLUE}📊 Test Summary:${NC}"
echo ""

if [ $unit_result -eq 0 ]; then
    echo -e "  Unit Tests:       ${GREEN}✅ PASS${NC}"
else
    echo -e "  Unit Tests:       ${RED}❌ FAIL${NC}"
fi

if [ $integration_result -eq 0 ]; then
    echo -e "  Integration:      ${GREEN}✅ PASS${NC}"
else
    echo -e "  Integration:      ${RED}❌ FAIL${NC}"
fi

if [ "$RUN_E2E" = true ]; then
    if [ $e2e_result -eq 0 ]; then
        echo -e "  E2E Tests:        ${GREEN}✅ PASS${NC}"
    else
        echo -e "  E2E Tests:        ${RED}❌ FAIL${NC}"
    fi
else
    echo -e "  E2E Tests:        ${YELLOW}⏭️  SKIPPED${NC}"
fi

echo ""

# Coverage report location
if [ "$RUN_COVERAGE" = true ] && [ $unit_result -eq 0 ]; then
    echo -e "${BLUE}📈 Coverage report generated:${NC}"
    echo "   Open: htmlcov/index.html"
    echo ""
fi

# Exit code
if [ $unit_result -eq 0 ] && [ $integration_result -eq 0 ] && [ $e2e_result -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 0
else
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ Some tests failed${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 1
fi
