# Consolidate Entity Tracking Implementations

## Summary

This PR refactors and consolidates the entity tracking functionality by enhancing the EntityService and moving the implementation from direct database access in the original EntityTrackingFlow to a state-based approach through the service layer. This improves testability while maintaining backward compatibility with existing code.

## Changes

1. **Added new state models** - Created specialized state classes for different entity tracking operations:
   - `EntityBatchTrackingState` - For batch processing of articles
   - `EntityDashboardState` - For dashboard generation
   - `EntityRelationshipState` - For entity relationship analysis

2. **Enhanced EntityService** with new state-based methods:
   - `process_article_with_state()` - Process a single article using state
   - `process_articles_batch()` - Process multiple articles with status tracking
   - `generate_entity_dashboard()` - Generate entity dashboard with trends
   - `find_entity_relationships()` - Find relationships between entities

3. **Refactored EntityTrackingFlow** to:
   - Use the enhanced EntityService instead of direct database access
   - Adopt state-based pattern while maintaining backward compatibility
   - Maintain the same public API for demo scripts and other consumers

4. **Updated tests** for the refactored components:
   - Added comprehensive tests for each new state-based method
   - Ensured legacy methods still work as expected
   - Fixed context manager mocking for better test reliability

## Benefits

1. **Improved Separation of Concerns**
   - Business logic now in service layer, not in flows
   - Flow focuses on orchestration, service handles implementation

2. **Better Testability**
   - State-based approach makes testing more straightforward
   - Reduced direct database dependencies in flow code
   - Easier to mock components for isolated testing

3. **Maintained Compatibility**
   - Existing scripts and code continue to work with the refactored implementation
   - No need to update demo scripts or other consumers

4. **Future-Proofing**
   - State objects provide clear documentation of input/output
   - Easy to extend with additional functionality
   - Path forward for removing the deprecated functionality completely

## Test Results

All tests now pass, with proper coverage of the state-based flow methods.
