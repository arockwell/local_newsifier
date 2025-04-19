#!/bin/bash
# Script to run tests for the refactored architecture

# Set up terminal colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running tests for the refactored architecture...${NC}"

# Run the integration test for the overall architecture
echo -e "\n${YELLOW}Running architecture integration test...${NC}"
python -m pytest tests/test_refactored_architecture.py -v

# Run the entity service tests
echo -e "\n${YELLOW}Running entity service tests...${NC}"
python -m pytest tests/services/test_entity_service.py -v

# Run the sentiment service tests
echo -e "\n${YELLOW}Running sentiment service tests...${NC}"
python -m pytest tests/services/test_sentiment_service.py -v

# Run the sentiment analyzer v2 tests
echo -e "\n${YELLOW}Running sentiment analyzer v2 tests...${NC}"
python -m pytest tests/tools/test_sentiment_analyzer_v2.py -v

# All tests have been run
echo -e "\n${GREEN}All refactored architecture tests completed.${NC}"
echo -e "\n${YELLOW}To run the demos, use:${NC}"
echo "python scripts/demo_refactored_architecture.py"
echo "python scripts/demo_sentiment_analysis_v2.py"
echo -e "\n${YELLOW}To see migration patterns, use:${NC}"
echo "python scripts/migrate_to_new_architecture.py"
