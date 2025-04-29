"""Utility modules for testing.

This package provides common utilities for testing:
- factories: Model factories for test data generation
- mocks: Mock service factories for testing
- api_testing: API testing utilities
- env_management: Environment variable management
- db_verification: Database verification helpers
"""

# Re-export common utilities for convenience
from tests.utils.factories import (
    ArticleFactory, EntityFactory, AnalysisResultFactory,
    CanonicalEntityFactory, EntityMentionContextFactory,
    EntityProfileFactory, EntityRelationshipFactory,
    create_article_batch, create_entity_batch,
    create_canonical_entity_batch, create_related_entities
)

from tests.utils.mocks import (
    MockService, MockRssFeedService, MockEntityService,
    MockArticleService, MockAnalysisService,
    create_mock_rss_service, create_mock_entity_service,
    create_mock_article_service, create_mock_analysis_service,
    create_sequence_behavior, create_conditional_behavior,
    create_error_then_success, ServicePatcher
)

from tests.utils.api_testing import (
    create_test_token, ApiTestHelper,
    assert_fields_match
)

from tests.utils.env_management import (
    EnvironmentManager
)

from tests.utils.db_verification import (
    DatabaseVerifier, ModelTester
)
