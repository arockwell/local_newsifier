# CLI to FastAPI Migration Checklist

## Overview

This checklist provides a detailed, step-by-step guide for migrating the Local Newsifier CLI from direct dependency injection to FastAPI HTTP endpoints.

## Pre-Migration Tasks

### Planning & Setup
- [ ] Review current CLI functionality and create feature inventory
- [ ] Identify all dependency injection usage points
- [ ] Document current test coverage metrics
- [ ] Set up feature flags for gradual rollout
- [ ] Create rollback plan and procedures
- [ ] Schedule migration phases with team
- [ ] Set up monitoring for migration metrics

### Environment Preparation
- [ ] Create development branch for migration
- [ ] Set up test environment with new architecture
- [ ] Configure CI/CD for parallel testing
- [ ] Prepare staging environment
- [ ] Document environment variables needed

## Phase 1: API Router Implementation (Week 1)

### Create CLI Router
- [ ] Create `src/local_newsifier/api/routers/cli.py`
- [ ] Define all request/response models
- [ ] Implement article processing endpoint
- [ ] Implement batch processing endpoint
- [ ] Implement report generation endpoint
- [ ] Implement task status endpoint
- [ ] Implement scraper control endpoint
- [ ] Implement health check endpoint
- [ ] Add proper error handling
- [ ] Add input validation
- [ ] Add rate limiting
- [ ] Register router in main FastAPI app

### Testing Router
- [ ] Write unit tests for each endpoint
- [ ] Test error scenarios
- [ ] Test validation rules
- [ ] Test background task queuing
- [ ] Load test endpoints
- [ ] Document API with OpenAPI

## Phase 2: HTTP Client Development (Week 1)

### Build HTTP Client
- [ ] Create `src/local_newsifier/cli/client.py`
- [ ] Implement NewsifierClient base class
- [ ] Add connection management
- [ ] Implement error handling
- [ ] Add retry logic
- [ ] Create AsyncNewsifierClient
- [ ] Implement all API methods
- [ ] Add local mode support
- [ ] Add timeout configuration
- [ ] Add request logging
- [ ] Create client documentation

### Client Testing
- [ ] Unit test all client methods
- [ ] Test error handling
- [ ] Test timeout scenarios
- [ ] Test retry logic
- [ ] Test async operations
- [ ] Test local mode
- [ ] Integration tests with API

## Phase 3: CLI Commands Refactoring (Week 2)

### Update Commands
- [ ] Refactor main CLI entry point
- [ ] Update process command
- [ ] Update batch command
- [ ] Update report command
- [ ] Update scrape command
- [ ] Update health command
- [ ] Add rich console formatting
- [ ] Improve error messages
- [ ] Add progress indicators
- [ ] Update help documentation

### Command Testing
- [ ] Test each command with mock client
- [ ] Test error scenarios
- [ ] Test output formatting
- [ ] Test async operations
- [ ] Test with real API
- [ ] User acceptance testing

## Phase 4: Service Layer Migration (Week 2)

### Update Services
- [ ] Remove @injectable decorators
- [ ] Update constructors
- [ ] Add session parameters to methods
- [ ] Create async wrappers
- [ ] Update ArticleService
- [ ] Update EntityService
- [ ] Update AnalysisService
- [ ] Update OpinionService
- [ ] Update ApifyService
- [ ] Update ReportService
- [ ] Create FastAPI dependencies

### Service Testing
- [ ] Update service unit tests
- [ ] Remove DI mocks
- [ ] Test with explicit sessions
- [ ] Test async wrappers
- [ ] Integration tests
- [ ] Performance tests

## Phase 5: Test Suite Updates (Week 3)

### Test Infrastructure
- [ ] Remove event loop fixtures
- [ ] Remove conditional decorators
- [ ] Update test database setup
- [ ] Simplify test configuration
- [ ] Update CI configuration
- [ ] Remove flaky test workarounds

### Update Test Files
- [ ] Update API tests
- [ ] Update CLI tests
- [ ] Update service tests
- [ ] Update integration tests
- [ ] Update fixtures
- [ ] Update mocks
- [ ] Ensure 90%+ coverage

## Phase 6: Documentation (Week 3)

### User Documentation
- [ ] Update README
- [ ] Update CLI usage guide
- [ ] Create migration guide for users
- [ ] Update API documentation
- [ ] Create troubleshooting guide
- [ ] Update installation instructions

### Developer Documentation
- [ ] Update architecture diagrams
- [ ] Document new patterns
- [ ] Update contribution guide
- [ ] Document deployment process
- [ ] Create operational runbook
- [ ] Update code comments

## Phase 7: Deployment (Week 4)

### Staging Deployment
- [ ] Deploy API to staging
- [ ] Test all endpoints
- [ ] Run integration tests
- [ ] Performance testing
- [ ] Security testing
- [ ] User acceptance testing

### Production Deployment
- [ ] Create deployment plan
- [ ] Schedule maintenance window
- [ ] Deploy API changes
- [ ] Deploy CLI updates
- [ ] Monitor error rates
- [ ] Monitor performance
- [ ] Have rollback ready

### Post-Deployment
- [ ] Monitor metrics for 24 hours
- [ ] Address any issues
- [ ] Gather user feedback
- [ ] Document lessons learned
- [ ] Update runbooks
- [ ] Plan optimization phase

## Rollback Procedures

### If Issues Arise
- [ ] Implement dual-mode support
- [ ] Add --use-api flag to CLI
- [ ] Keep old code paths available
- [ ] Monitor both implementations
- [ ] Gradual user migration
- [ ] Clear communication

### Rollback Steps
1. Revert CLI to use direct injection
2. Keep API endpoints active
3. Fix issues in parallel branch
4. Re-test thoroughly
5. Plan second attempt

## Success Metrics

### Technical Metrics
- [ ] All tests passing (100%)
- [ ] Test coverage >90%
- [ ] No event loop errors
- [ ] API response time <100ms
- [ ] Zero downtime deployment
- [ ] Error rate <0.1%

### User Experience Metrics
- [ ] CLI response time improved
- [ ] No functionality lost
- [ ] Better error messages
- [ ] Positive user feedback
- [ ] Reduced support tickets

## Post-Migration Tasks

### Cleanup
- [ ] Remove old dependency injection code
- [ ] Remove workarounds and hacks
- [ ] Clean up unused imports
- [ ] Remove deprecated tests
- [ ] Archive old documentation

### Optimization
- [ ] Performance profiling
- [ ] Database query optimization
- [ ] Caching implementation
- [ ] Connection pooling tuning
- [ ] Load testing at scale

### Future Enhancements
- [ ] Add more CLI features
- [ ] Build web UI
- [ ] Add API authentication
- [ ] Implement webhooks
- [ ] Add plugin system

## Sign-off

### Stakeholder Approval
- [ ] Development team approval
- [ ] QA team approval
- [ ] Operations team approval
- [ ] Product owner approval
- [ ] Final go-live decision

### Completion Criteria
- [ ] All checklist items complete
- [ ] No critical bugs
- [ ] Performance targets met
- [ ] Documentation complete
- [ ] Team trained
- [ ] Users notified
