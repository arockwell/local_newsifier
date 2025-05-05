"""Debug script to test complex URL handling."""

import urllib.parse
from datetime import datetime, timezone

# Complex URL with query parameters
timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
complex_url = f"https://example.com/path/with/multiple/segments/{timestamp}?param=value&other=value"

print(f"Original URL: {complex_url}")

# 1. Test URL encoding for HTTP requests
encoded_url = urllib.parse.quote(complex_url)
print(f"URL encoded: {encoded_url}")

# 2. Test URL decoding as would happen in the API
decoded_url = urllib.parse.unquote(encoded_url)
print(f"URL decoded: {decoded_url}")

# 3. Compare
print(f"Original == decoded: {complex_url == decoded_url}")

# 4. Test conversion to pydantic HttpUrl
try:
    from pydantic import HttpUrl
    http_url = HttpUrl(complex_url)
    print(f"As HttpUrl: {http_url}")
    print(f"As str(HttpUrl): {str(http_url)}")
    print(f"Original == str(HttpUrl): {complex_url == str(http_url)}")
except Exception as e:
    print(f"Error converting to HttpUrl: {str(e)}")

# Test specific parts
import urllib.parse
url_parts = urllib.parse.urlparse(complex_url)
print(f"URL parts: {url_parts}")
print(f"Path: {url_parts.path}")
print(f"Query: {url_parts.query}")

# Test rebuilding URL
rebuilt_url = urllib.parse.urlunparse(url_parts)
print(f"Rebuilt URL: {rebuilt_url}")
print(f"Original == rebuilt: {complex_url == rebuilt_url}")

# URL in test request
test_url = f"/articles/by-url?url={complex_url}"
print(f"Test request URL: {test_url}")