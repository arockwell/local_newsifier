# Mock Container Cleanup Report

This report lists files that still have references to the legacy 'mock_container' fixture.
These files need to be updated to use the injectable pattern.

## File: tests/services/test_isolated_rss_feed.py

- Status: **SKIPPED** (has pytest.mark.skip)
- References to mock_container: 24

### Test methods using mock_container:

```python
    # Create a mock container
    mock_container = MagicMock()
    
--
        return None
    mock_container.get.side_effect = mock_get
    
    # Add the container to the service
    service.container = mock_container
    
--
    # Create a mock container
    mock_container = MagicMock()
    
    # Create a mock process_article_task that should NOT be used
    mock_container_task = MagicMock()
    mock_container_task.delay = MagicMock()
    
--
        if service_name == "process_article_task":
            return mock_container_task
        return None
    mock_container.get.side_effect = mock_get
    
    # Add the container to the service
    service.container = mock_container
    
--
        # Verify that the container task was NOT used
        assert mock_container_task.delay.call_count == 0

--
    # Create a mock container
    mock_container = MagicMock()
    
    # Create a mock article_service from the container
    mock_container_article_service = MagicMock()
    mock_container_article_service.create_article_from_rss_entry.side_effect = [201, 202]
    
--
        if service_name == "article_service":
            return mock_container_article_service
        return None
    mock_container.get.side_effect = mock_get
    
    # Add the container to the service
    service.container = mock_container
    with patch('local_newsifier.services.rss_feed_service.parse_rss_feed', return_value=mock_feed_data):
--
        # Verify that container article service was used
        assert mock_container_article_service.create_article_from_rss_entry.call_count == 2

--
    # Create a mock container
    mock_container = MagicMock()
    
    # Configure container to return None for article_service
    mock_container.get.return_value = None
    
    # Add the container to the service
    service.container = mock_container
    
--
    mock_rss_feed_service = MagicMock()
    mock_container = MagicMock()
    
    # Configure container to return our mock service
    mock_container.get.return_value = mock_rss_feed_service
    
    # Test the function
    with patch('local_newsifier.container.container', mock_container):
        register_article_service(mock_article_service)
--
        # Verify the article service was registered
        mock_container.get.assert_called_with("rss_feed_service")
        assert mock_rss_feed_service.article_service == mock_article_service
```

