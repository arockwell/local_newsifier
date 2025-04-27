import pytest
import sys

# Run specific failing tests
pytest_args = [
    "-xvs",
    "tests/services/test_rss_feed_service.py::test_process_feed_with_global_task_func",
    "tests/services/test_rss_feed_service.py::test_process_feed_no_service_no_task",
    "tests/services/test_rss_feed_service.py::test_process_feed_temp_service_fails",
    "tests/services/test_rss_feed_service.py::test_register_process_article_task",
    "tests/database/test_engine.py::test_get_engine_retry_and_fail",
    "tests/database/test_engine.py::test_get_session_success"
]

sys.exit(pytest.main(pytest_args))
