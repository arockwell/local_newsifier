#!/usr/bin/env python3
"""Manual test for the simplified webhook endpoint."""

import json
import time

import requests


def test_webhook():
    """Test the simplified webhook endpoint."""
    url = "http://localhost:8000/webhooks/apify"

    # Test 1: Valid webhook
    print("\n=== Test 1: Valid webhook ===")
    payload = {
        "resource": {
            "id": f"test-run-{int(time.time())}",
            "actId": "test-actor",
            "status": "SUCCEEDED",
            "defaultDatasetId": "test-dataset",
        }
    }

    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    # Test 2: Duplicate webhook
    print("\n=== Test 2: Duplicate webhook (same payload) ===")
    response2 = requests.post(url, json=payload)
    print(f"Status: {response2.status_code}")
    print(f"Response: {json.dumps(response2.json(), indent=2)}")

    # Test 3: Missing run_id
    print("\n=== Test 3: Missing run_id ===")
    bad_payload = {"resource": {"actId": "test-actor", "status": "SUCCEEDED"}}

    response3 = requests.post(url, json=bad_payload)
    print(f"Status: {response3.status_code}")
    if response3.status_code == 400:
        print(f"Response: {json.dumps(response3.json(), indent=2)}")

    # Test 4: Failed run (no article creation)
    print("\n=== Test 4: Failed run ===")
    failed_payload = {
        "resource": {
            "id": f"test-run-failed-{int(time.time())}",
            "actId": "test-actor",
            "status": "FAILED",
        }
    }

    response4 = requests.post(url, json=failed_payload)
    print(f"Status: {response4.status_code}")
    print(f"Response: {json.dumps(response4.json(), indent=2)}")


if __name__ == "__main__":
    print("Testing simplified webhook endpoint...")
    print("Make sure the API is running at http://localhost:8000")
    input("Press Enter to continue...")
    test_webhook()
