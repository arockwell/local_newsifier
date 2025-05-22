import pytest
from unittest.mock import MagicMock, patch

from tests.fixtures.event_loop import event_loop_fixture


def test_get_entity_tracking_flow(event_loop_fixture):
    """Ensure provider creates EntityTrackingFlow instance with mocks."""
    from local_newsifier.di import providers
    with patch("local_newsifier.di.providers.get_entity_service", return_value=MagicMock()), \
         patch("local_newsifier.di.providers.get_entity_tracker_tool", return_value=MagicMock()), \
         patch("local_newsifier.di.providers.get_entity_extractor_tool", return_value=MagicMock()), \
         patch("local_newsifier.di.providers.get_context_analyzer_tool", return_value=MagicMock()), \
         patch("local_newsifier.di.providers.get_entity_resolver_tool", return_value=MagicMock()), \
         patch("local_newsifier.di.providers.get_session", return_value=MagicMock()):
        flow = providers.get_entity_tracking_flow()
        from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow
        assert isinstance(flow, EntityTrackingFlow)

