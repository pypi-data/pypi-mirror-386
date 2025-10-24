#!/usr/bin/env python3
"""Simple test script for pantsonfire functionality"""

import os
import tempfile
from pathlib import Path

# Sample blog content with outdated information
SAMPLE_BLOG = """
# How to Use the Python Requests Library

In this tutorial, we'll learn how to use the popular Python requests library for making HTTP calls.

## Making a GET Request

To make a GET request, you can use the following code:

```python
import requests

response = requests.get('https://api.example.com/v1/users')
print(response.json())
```

Note: The current version of requests is 2.25.0, and it uses the old urllib3 backend.

## Authentication

For basic authentication, use:

```python
requests.get('https://api.example.com/v1/data', auth=('user', 'pass'))
```

The library supports HTTP Basic Auth out of the box.
"""

# Sample official documentation (truth source)
SAMPLE_DOCS = """
# Python Requests Library Documentation

Version: 2.31.0

## Installation

```bash
pip install requests
```

## Quick Start

### Making Requests

```python
import requests

# GET request
response = requests.get('https://api.example.com/v2/users')
data = response.json()
```

### Authentication

Requests supports multiple authentication methods:

- Basic Auth: `requests.get(url, auth=('user', 'pass'))`
- Bearer Token: `requests.get(url, headers={'Authorization': 'Bearer token'})`
- API Keys: `requests.get(url, headers={'X-API-Key': 'key'})`

## Important Changes

### Version 2.30.0 (2023)
- Updated urllib3 dependency
- Improved SSL handling

### Version 2.25.0 (2021)
- Deprecated Python 3.5 support
- Added new authentication helpers

### API Changes
- The `/v1/` endpoints are deprecated. Use `/v2/` endpoints instead.
- New authentication methods added in v2.28.0
"""

def create_sample_files():
    """Create sample files for testing"""
    # Create temp directory
    temp_dir = Path(tempfile.mkdtemp())

    # Write sample blog
    blog_file = temp_dir / "sample_blog.md"
    blog_file.write_text(SAMPLE_BLOG)

    # Write sample docs
    docs_file = temp_dir / "official_docs.md"
    docs_file.write_text(SAMPLE_DOCS)

    return temp_dir, blog_file, docs_file

def test_basic_functionality():
    """Test basic pantsonfire functionality"""
    print("Testing pantsonfire basic functionality...")

    # Create sample files
    temp_dir, blog_file, docs_file = create_sample_files()
    print(f"Created sample files in: {temp_dir}")

    try:
        # Import and create app
        import sys
        sys.path.insert(0, '/Users/seanmcdonald/Documents/GitHub/pantsonfire')

        # Test basic imports
        print("Testing imports...")
        try:
            from pantsonfire.extractors import get_extractor
            print("✓ Extractor imports working")
        except ImportError as e:
            print(f"✗ Extractor import failed: {e}")
            return

        # Test extractor directly
        print("Testing content extraction...")
        extractor = get_extractor("internal")

        print(f"Testing extraction from: {blog_file}")
        blog_content = extractor.extract(blog_file)
        print(f"Blog content length: {len(blog_content) if blog_content else 0}")

        print(f"Testing extraction from: {docs_file}")
        docs_content = extractor.extract(docs_file)
        print(f"Docs content length: {len(docs_content) if docs_content else 0}")

        if blog_content and docs_content:
            print("✓ Content extraction working")
        else:
            print("✗ Content extraction failed")

        # Test LLM client (if available)
        try:
            from pantsonfire import create_app
            app = create_app(mode="internal")
            print("✓ App creation working")

            if os.getenv("OPENROUTER_API_KEY"):
                print("Testing LLM client...")
                try:
                    # Simple test
                    test_response = app.llm.client.chat.completions.create(
                        model="anthropic/claude-3-haiku",
                        messages=[{"role": "user", "content": "Say 'test' if you can read this"}],
                        max_tokens=10
                    )
                    print("✓ LLM client working")
                except Exception as e:
                    print(f"✗ LLM client failed: {e}")
            else:
                print("⚠ No OPENROUTER_API_KEY set, skipping LLM test")

        except ImportError as e:
            print(f"⚠ Full app import failed (expected without API key): {e}")
        except Exception as e:
            print(f"⚠ App creation failed: {e}")

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        print(f"Cleaned up temp directory: {temp_dir}")

if __name__ == "__main__":
    test_basic_functionality()
