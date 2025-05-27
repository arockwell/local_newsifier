# Injectable Dependencies Testing Examples

This directory contains example tests that demonstrate the simplified approach to testing components using fastapi-injectable dependencies.

## Overview

The examples showcase how to test different types of components:

1. **Services**: Business logic components that may interact with the database (`test_injectable_service_example.py`)
2. **Flows**: Higher-level components that orchestrate multiple services (`test_injectable_flow_example.py`)
3. **Tools**: Utility components that provide specific functionality (`test_injectable_tool_example.py`)

Each example demonstrates various testing patterns and techniques for testing injectable components.

## Key Testing Utilities

- `mock_injectable_dependencies`: A fixture for managing mock dependencies
- `common_injectable_mocks`: Pre-configured mocks for common dependencies
- `create_mock_service`: A helper function for creating services with mocks
- `injectable_test_app`: A fixture for testing FastAPI endpoints

## Testing Patterns Demonstrated

### 1. Direct Instantiation

Creating services directly with mock dependencies:

```python
service = ExampleEntityService(
    entity_crud=entity_crud_mock,
    canonical_entity_crud=canonical_entity_crud_mock,
    session=session_mock,
)
```

### 2. Using the MockManager

Registering and retrieving mocks through the `mock_injectable_dependencies` fixture:

```python
mock = mock_injectable_dependencies
mock.register("get_entity_crud", entity_crud_mock)
mock.register("get_session", session_mock)

service = ExampleEntityService(
    entity_crud=mock.get("get_entity_crud"),
    canonical_entity_crud=MagicMock(),
    session=mock.get("get_session"),
)
```

### 3. Using the Helper Function

Creating services with the `create_mock_service` helper:

```python
service = create_mock_service(
    ExampleEntityService,
    entity_crud=entity_crud_mock,
    canonical_entity_crud=MagicMock(),
    session=session_mock,
)
```

### 4. Using Common Mocks

Using pre-configured mocks from the `common_injectable_mocks` fixture:

```python
mock = common_injectable_mocks
mock.get("get_entity_crud").get.return_value = {"id": 1, "name": "Test Entity"}

service = ExampleEntityService(
    entity_crud=mock.get("get_entity_crud"),
    canonical_entity_crud=mock.get("get_canonical_entity_crud"),
    session=mock.get("get_session"),
)
```

## Running the Examples

To run the example tests:

```bash
# Run a specific example
pytest tests/examples/test_injectable_service_example.py -v

# Run all examples
pytest tests/examples/ -v
```

## Using These Examples in Your Tests

1. **Study the Patterns**: Review the examples to understand the different testing patterns
2. **Choose the Appropriate Pattern**: Select the pattern that best fits your component
3. **Use the Testing Utilities**: Leverage the testing utilities and patterns
4. **Follow the AAA Pattern**: Structure your tests with Arrange, Act, Assert

For detailed guidance on testing with injectable dependencies, refer to the comprehensive documentation in `docs/testing_injectable_dependencies.md`.
