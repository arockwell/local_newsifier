#!/usr/bin/env python
"""
Simple script to test both methods of using flow classes:
1. Legacy container pattern with from_container()
2. Direct instantiation with dependencies
"""

import logging
from datetime import datetime, timedelta, timezone

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_flow_patterns():
    """Test both flow usage patterns for entity tracking flow."""
    logger.info("TESTING FLOW USAGE PATTERNS")
    
    # Method 1: Legacy container pattern with from_container()
    logger.info("\n--- Testing Legacy Container Pattern ---")
    from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow
    
    # Create the flow using the container
    container_flow = EntityTrackingFlow.from_container()
    logger.info(f"Created flow using legacy container pattern: {container_flow}")
    
    # Try using the flow
    try:
        dashboard = container_flow.get_entity_dashboard(days=30, entity_type="PERSON")
        if dashboard and 'entities' in dashboard:
            logger.info(f"Dashboard contains {len(dashboard['entities'])} entities")
        else:
            logger.info("No entities found in dashboard")
    except Exception as e:
        logger.error(f"Error testing legacy flow: {e}")
    
    # Method 2: Direct instantiation with dependencies
    logger.info("\n--- Testing Direct Instantiation ---")
    try:
        # Create minimal dependencies for demonstration
        from local_newsifier.services.entity_service import EntityService
        from local_newsifier.tools.entity_tracker_service import EntityTracker
        from local_newsifier.tools.extraction.entity_extractor import EntityExtractor
        from local_newsifier.tools.analysis.context_analyzer import ContextAnalyzer
        from local_newsifier.tools.resolution.entity_resolver import EntityResolver
        from local_newsifier.database.engine import get_session
        
        # Create a simple session factory
        session_factory = get_session
        session = next(session_factory())
        
        # Create required services
        entity_service = EntityService(
            entity_crud=None,
            canonical_entity_crud=None,
            entity_mention_context_crud=None,
            entity_profile_crud=None,
            article_crud=None,
            entity_extractor=None,
            context_analyzer=None,
            entity_resolver=None,
            session_factory=session_factory
        )
        
        # Create tools
        entity_tracker = EntityTracker()
        entity_extractor = EntityExtractor()
        context_analyzer = ContextAnalyzer()
        entity_resolver = EntityResolver()
        
        # Create the flow directly
        direct_flow = EntityTrackingFlow(
            entity_service=entity_service,
            entity_tracker=entity_tracker,
            entity_extractor=entity_extractor,
            context_analyzer=context_analyzer,
            entity_resolver=entity_resolver,
            session_factory=session_factory,
            session=session
        )
        
        logger.info(f"Created flow using direct instantiation: {direct_flow}")
        
        # Try using the flow
        try:
            dashboard = direct_flow.get_entity_dashboard(days=30, entity_type="PERSON")
            if dashboard and 'entities' in dashboard:
                logger.info(f"Dashboard contains {len(dashboard['entities'])} entities")
            else:
                logger.info("No entities found in dashboard")
        except Exception as e:
            logger.error(f"Error testing direct flow: {e}")
            
    except Exception as e:
        logger.error(f"Error creating direct flow: {e}")

if __name__ == "__main__":
    # Initialize tables if needed
    from local_newsifier.database.engine import create_db_and_tables
    create_db_and_tables()
    
    # Run the test
    test_flow_patterns()