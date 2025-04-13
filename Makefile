.PHONY: build deploy clean

# AWS region to deploy to
REGION ?= us-east-1
# Stack name for the deployment
STACK_NAME ?= local-newsifier

# Build the Lambda function package
build:
	@echo "Building Lambda function package..."
	@mkdir -p .aws-sam/build
	@cp -r src/local_newsifier/functions/fetch_articles/* .aws-sam/build/
	@cp -r src/local_newsifier/shared .aws-sam/build/
	@cp -r src/local_newsifier/models .aws-sam/build/
	@cp -r src/local_newsifier/flows .aws-sam/build/
	@cp -r src/local_newsifier/tools .aws-sam/build/
	@pip install -r src/local_newsifier/functions/fetch_articles/requirements.txt -t .aws-sam/build/

# Deploy the application
deploy: build
	@echo "Deploying application..."
	@sam deploy \
		--template-file template.yaml \
		--stack-name $(STACK_NAME) \
		--capabilities CAPABILITY_IAM \
		--region $(REGION)

# Clean up build artifacts
clean:
	@echo "Cleaning up build artifacts..."
	@rm -rf .aws-sam

# Local testing
test-local:
	@echo "Testing Lambda function locally..."
	@sam local invoke FetchArticlesFunction --event events/event.json

# Help target
help:
	@echo "Available targets:"
	@echo "  build    - Build the Lambda function package"
	@echo "  deploy   - Deploy the application to AWS"
	@echo "  clean    - Clean up build artifacts"
	@echo "  test-local - Test the Lambda function locally"
	@echo ""
	@echo "Variables:"
	@echo "  REGION    - AWS region to deploy to (default: us-east-1)"
	@echo "  STACK_NAME - CloudFormation stack name (default: local-newsifier)" 