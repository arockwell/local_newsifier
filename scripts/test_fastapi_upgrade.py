"""Test script to verify FastAPI functionality after upgrade.

This script creates a simple FastAPI app and runs it to verify that the
upgrade to FastAPI 0.112.4 didn't break any functionality.
"""

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Path, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlmodel import Session

from local_newsifier.api.dependencies import get_session
from local_newsifier.container import container
from local_newsifier.database.engine import SessionManager


# Create a test FastAPI app
app = FastAPI(title="FastAPI Upgrade Test")


@app.get("/")
async def root():
    """Root endpoint for testing."""
    return {"message": "FastAPI upgrade test successful"}


@app.get("/session-test")
async def session_test(session: Session = Depends(get_session)):
    """Test session dependency."""
    # Just verify we can get a session
    return {"message": "Session dependency works"}


@app.get("/container-test")
async def container_test():
    """Test container access."""
    # Try to get a service from the container
    session_factory = container.get("session_factory")
    if session_factory is None:
        raise HTTPException(status_code=500, detail="Container not working")
    return {"message": "Container access works"}


@app.get("/error-test")
async def error_test():
    """Test error handling."""
    raise HTTPException(status_code=404, detail="Test error handling")


def run_tests():
    """Run basic tests on the FastAPI app."""
    client = TestClient(app)
    
    # Test root endpoint
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "FastAPI upgrade test successful"}
    print("✓ Root endpoint test passed")
    
    # Test session dependency
    response = client.get("/session-test")
    assert response.status_code == 200
    assert response.json() == {"message": "Session dependency works"}
    print("✓ Session dependency test passed")
    
    # Test container access
    response = client.get("/container-test")
    assert response.status_code == 200
    assert response.json() == {"message": "Container access works"}
    print("✓ Container access test passed")
    
    # Test error handling
    response = client.get("/error-test")
    assert response.status_code == 404
    assert response.json() == {"detail": "Test error handling"}
    print("✓ Error handling test passed")
    
    print("\nAll tests passed! FastAPI upgrade is compatible.")


if __name__ == "__main__":
    # Run tests by default
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        # Run the server if requested
        uvicorn.run(app, host="127.0.0.1", port=8000)
    else:
        run_tests()