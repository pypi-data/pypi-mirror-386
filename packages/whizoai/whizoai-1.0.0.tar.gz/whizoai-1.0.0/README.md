# WhizoAI SDK for Python

Official Python SDK for the WhizoAI web scraping and data extraction API.

[![PyPI version](https://badge.fury.io/py/whizoai.svg)](https://pypi.org/project/whizoai/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Simple & Intuitive** - Pythonic API design
- **Type Hints** - Full type annotations for better IDE support
- **Pydantic Models** - Validated response models
- **Automatic Retries** - Built-in exponential backoff for failed requests
- **Error Handling** - Structured exception hierarchy
- **Async Support** - Optional async/await support (coming soon)
- **Comprehensive** - All WhizoAI endpoints supported

## Installation

```bash
pip install whizoai
```

Or with Poetry:
```bash
poetry add whizoai
```

Or with pip and requirements.txt:
```
whizoai>=1.0.0
```

## Quick Start

```python
from whizoai import WhizoAI

# Initialize the client
client = WhizoAI(api_key="whizo_your_api_key_here")

# Scrape a webpage
result = client.scrape(
    url="https://example.com",
    format="markdown",
    only_main_content=True,
)

print(result["data"]["content"])
print(f"Credits used: {result['creditsUsed']}")
```

## Authentication

Get your API key from the [WhizoAI Dashboard](https://whizo.ai/app/api-keys).

### Environment Variable (Recommended)

```bash
export WHIZOAI_API_KEY="whizo_your_api_key_here"
```

```python
import os
from whizoai import WhizoAI

client = WhizoAI(api_key=os.getenv("WHIZOAI_API_KEY"))
```

### Direct Initialization

```python
from whizoai import WhizoAI

client = WhizoAI(api_key="whizo_your_api_key_here")
```

## API Reference

### Scraping

#### Single Page Scraping

```python
result = client.scrape(
    url="https://example.com",
    format="markdown",  # 'markdown', 'html', 'text', 'json'
    only_main_content=True,
    include_screenshot=False,
    include_pdf=False,
    wait_for=0,  # milliseconds to wait before scraping
    headers={
        "User-Agent": "Custom User Agent",
    },
)

print(result["data"]["content"])
print(result["data"]["metadata"]["title"])
print(f"Credits used: {result['creditsUsed']}")
```

#### Multi-Page Crawling

```python
result = client.crawl(
    url="https://example.com",
    max_pages=10,
    max_depth=2,
    allowed_domains=["example.com"],
    exclude_paths=["/admin", "/private"],
    format="markdown",
    only_main_content=True,
)

print(f"Crawled {len(result['data']['pages'])} pages")
for page in result["data"]["pages"]:
    print(f"{page['url']}: {page['content'][:100]}...")
```

### AI-Powered Extraction

Extract structured data from webpages using AI:

```python
result = client.extract(
    url="https://github.com/anthropics",
    schema={
        "companyName": "string",
        "description": "string",
        "mainProducts": ["string"],
        "teamSize": "number",
    },
    model="gpt-3.5-turbo",  # or 'gpt-4'
    prompt="Extract information about this company",
)

extracted = result["data"]["extractedData"]
print(extracted)
# {
#     "companyName": "Anthropic",
#     "description": "AI safety company...",
#     "mainProducts": ["Claude", "Constitutional AI"],
#     "teamSize": 150
# }
```

### Web Search

Search the web with optional content scraping:

```python
result = client.search(
    query="best web scraping tools 2025",
    max_results=10,
    scrape_results=True,  # Scrape each search result
    search_engine="google",  # 'google', 'bing', 'duckduckgo'
    country="us",
    language="en",
)

print(f"Found {len(result['data']['results'])} results")
for item in result["data"]["results"]:
    print(f"{item['title']}: {item['url']}")
    if "content" in item:
        print(f"Content: {item['content'][:200]}...")
```

### URL Mapping

Discover all URLs on a website:

```python
result = client.map(
    url="https://example.com",
    max_depth=3,
    max_pages=100,
    include_subdomains=False,
)

print(f"Found {result['totalUrls']} URLs")
for url_info in result["data"]["urls"]:
    print(f"{url_info['url']} (depth: {url_info['depth']})")
```

### Batch Operations

Process multiple URLs in parallel:

```python
result = client.batch(
    urls=[
        "https://example.com",
        "https://example.com/about",
        "https://example.com/contact",
    ],
    scrape_type="scrape",
    options={
        "format": "markdown",
        "only_main_content": True,
    },
)

print(f"Total credits used: {result['totalCreditsUsed']}")
for i, item in enumerate(result["data"]["results"], 1):
    print(f"Result {i}: {item['status']}")
    if "data" in item:
        print(item["data"]["content"][:100])
```

### Job Management

#### List Jobs

```python
jobs = client.list_jobs(
    limit=20,
    offset=0,
    status="completed",  # 'pending', 'running', 'completed', 'failed'
    scrape_type="scrape",  # Filter by type
)

print(f"Found {jobs['data']['total']} jobs")
for job in jobs["data"]["jobs"]:
    print(f"{job['id']}: {job['url']} - {job['status']}")
```

#### Get Job Details

```python
job = client.get_job(job_id="job-id-here")

print(f"Status: {job['data']['status']}")
print(f"Progress: {job['data']['progress']}%")
print(f"Credits used: {job['data']['creditsUsed']}")
```

#### Cancel Job

```python
client.cancel_job(job_id="job-id-here")
print("Job cancelled successfully")
```

#### Delete Job

```python
client.delete_job(job_id="job-id-here")
print("Job deleted successfully")
```

### User & Credits

#### Check Credit Balance

```python
credits = client.get_credit_balance()

print(f"Plan: {credits['data']['plan']}")
print(f"Monthly credits: {credits['data']['monthlyCredits']}")
print(f"Used this month: {credits['data']['creditsUsedThisMonth']}")
print(f"Remaining: {credits['data']['creditsRemaining']}")
print(f"Lifetime credits: {credits['data']['lifetimeCredits']}")
```

#### Get User Profile

```python
profile = client.get_user_profile()

print(f"Email: {profile['data']['email']}")
print(f"Name: {profile['data']['fullName']}")
print(f"Plan: {profile['data']['plan']}")
```

#### Update User Profile

```python
client.update_user_profile(
    full_name="John Doe",
    email="john@example.com",
)
```

#### Get Usage Analytics

```python
usage = client.get_usage_analytics(
    start_date="2025-01-01",
    end_date="2025-01-31",
    group_by="day",  # 'hour', 'day', 'week', 'month'
)

print(f"Total requests: {usage['data']['totalRequests']}")
print(f"Total credits: {usage['data']['totalCredits']}")
for item in usage["data"]["breakdown"]:
    print(f"{item['date']}: {item['requests']} requests, {item['credits']} credits")
```

### API Key Management

#### List API Keys

```python
keys = client.list_api_keys()

for key in keys["data"]:
    status = "Active" if key["isActive"] else "Inactive"
    print(f"{key['name']}: {key['maskedKey']} ({status})")
    print(f"  Last used: {key['lastUsedAt']}")
    print(f"  Usage: {key['usageCount']} requests")
```

#### Create API Key

```python
new_key = client.create_api_key(
    name="Production API Key",
    scopes=["scrape", "crawl", "extract"],
    rate_limit_per_hour=100,
    expires_at="2025-12-31T23:59:59Z",  # Optional
)

print(f"New API key: {new_key['data']['apiKey']}")
print("⚠️ Save this key - you won't see it again!")
```

#### Update API Key

```python
client.update_api_key(
    key_id="key-id-here",
    name="Updated Key Name",
    is_active=False,  # Disable the key
)
```

#### Delete API Key

```python
client.delete_api_key(key_id="key-id-here")
print("API key deleted successfully")
```

### Webhooks

#### List Webhooks

```python
webhooks = client.list_webhooks()

for webhook in webhooks["data"]:
    print(f"{webhook['url']} - {', '.join(webhook['events'])}")
```

#### Create Webhook

```python
webhook = client.create_webhook(
    url="https://your-app.com/webhooks/whizoai",
    events=["job.completed", "job.failed"],
    secret="your-webhook-secret",  # For signature verification
)

print(f"Webhook created: {webhook['data']['id']}")
```

#### Delete Webhook

```python
client.delete_webhook(webhook_id="webhook-id-here")
```

## Error Handling

The SDK provides structured exception types for better error handling:

```python
from whizoai import (
    WhizoAI,
    WhizoAIError,
    AuthenticationError,
    ValidationError,
    InsufficientCreditsError,
    RateLimitError,
    NetworkError,
)

client = WhizoAI(api_key="your-api-key")

try:
    result = client.scrape(url="https://example.com")
except AuthenticationError as e:
    print(f"Invalid API key: {e.message}")
except ValidationError as e:
    print(f"Invalid input: {e.details}")
except InsufficientCreditsError as e:
    print(f"Out of credits: {e.message}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e.message}")
except NetworkError as e:
    print(f"Network error: {e.message}")
except WhizoAIError as e:
    print(f"WhizoAI error: {e.message} (code: {e.code})")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Advanced Configuration

### Custom API URL

For self-hosted or testing environments:

```python
client = WhizoAI(
    api_key="your-api-key",
    api_url="http://localhost:8080",  # Default: https://api.whizo.ai
)
```

### Custom Timeout

```python
client = WhizoAI(
    api_key="your-api-key",
    timeout=60,  # 60 seconds (default: 30)
)
```

### Retry Configuration

```python
client = WhizoAI(
    api_key="your-api-key",
    max_retries=5,  # Default: 3
    retry_delay=2.0,  # Initial delay in seconds (default: 1.0)
)
```

### Custom User Agent

```python
client = WhizoAI(
    api_key="your-api-key",
    user_agent="MyApp/1.0.0",
)
```

## Type Hints

The SDK provides full type hints for better IDE support:

```python
from typing import Dict, Any, List
from whizoai import WhizoAI

client: WhizoAI = WhizoAI(api_key="your-api-key")

# All methods return Dict[str, Any]
result: Dict[str, Any] = client.scrape(url="https://example.com")

# Access nested data with type safety
content: str = result["data"]["content"]
credits_used: int = result["creditsUsed"]
```

## Examples

### Basic Web Scraping

```python
from whizoai import WhizoAI
import os

client = WhizoAI(api_key=os.getenv("WHIZOAI_API_KEY"))

# Scrape a blog post as markdown
result = client.scrape(
    url="https://blog.example.com/post-123",
    format="markdown",
    only_main_content=True,
)

# Save to file
with open("scraped_content.md", "w", encoding="utf-8") as f:
    f.write(result["data"]["content"])

print(f"Saved content. Credits used: {result['creditsUsed']}")
```

### Extract Product Information

```python
from whizoai import WhizoAI
import json

client = WhizoAI(api_key=os.getenv("WHIZOAI_API_KEY"))

# Extract product details using AI
result = client.extract(
    url="https://store.example.com/product/xyz",
    schema={
        "productName": "string",
        "price": "number",
        "currency": "string",
        "inStock": "boolean",
        "description": "string",
        "features": ["string"],
    },
    model="gpt-4",
)

product = result["data"]["extractedData"]
print(json.dumps(product, indent=2))
```

### Crawl Documentation Site

```python
from whizoai import WhizoAI
import os

client = WhizoAI(api_key=os.getenv("WHIZOAI_API_KEY"))

# Crawl documentation pages
result = client.crawl(
    url="https://docs.example.com",
    max_pages=50,
    max_depth=3,
    allowed_domains=["docs.example.com"],
    format="markdown",
)

# Save each page
for i, page in enumerate(result["data"]["pages"], 1):
    filename = f"docs/page_{i}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {page['metadata']['title']}\n\n")
        f.write(f"URL: {page['url']}\n\n")
        f.write(page["content"])

print(f"Saved {len(result['data']['pages'])} pages")
```

### Monitor Job Progress

```python
from whizoai import WhizoAI
import time

client = WhizoAI(api_key=os.getenv("WHIZOAI_API_KEY"))

# Start a large crawl job
result = client.crawl(
    url="https://example.com",
    max_pages=100,
)

job_id = result["jobId"]
print(f"Job started: {job_id}")

# Poll for completion
while True:
    job = client.get_job(job_id=job_id)
    status = job["data"]["status"]
    progress = job["data"]["progress"]

    print(f"Status: {status}, Progress: {progress}%")

    if status in ["completed", "failed"]:
        break

    time.sleep(5)

if status == "completed":
    print(f"Job completed! Credits used: {job['data']['creditsUsed']}")
else:
    print(f"Job failed: {job['data'].get('error')}")
```

### Batch URL Processing

```python
from whizoai import WhizoAI
import csv

client = WhizoAI(api_key=os.getenv("WHIZOAI_API_KEY"))

# Read URLs from CSV
urls = []
with open("urls.csv", "r") as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    urls = [row[0] for row in reader]

# Process in batches
result = client.batch(
    urls=urls,
    scrape_type="scrape",
    options={
        "format": "text",
        "only_main_content": True,
    },
)

# Save results
with open("results.json", "w") as f:
    json.dump(result, f, indent=2)

print(f"Processed {len(urls)} URLs")
print(f"Total credits used: {result['totalCreditsUsed']}")
```

## Credit Costs

| Operation | Base Cost | Additional |
|-----------|-----------|------------|
| Basic scraping | 1 credit | - |
| Screenshot | +1 credit | Per page |
| PDF generation | +1 credit | Per page |
| AI extraction (GPT-3.5) | 3 credits | Per page |
| AI extraction (GPT-4) | 6 credits | Per page |
| Web search | 1 credit | Per search |
| Stealth mode | +4 credits | Per page |

## Rate Limits

Rate limits vary by subscription plan:

| Plan | Requests/Hour | Requests/Day |
|------|--------------|--------------|
| Free | 10 | 100 |
| Starter | 50 | 500 |
| Pro | 200 | 2,000 |
| Enterprise | 1,000 | 10,000 |

## Requirements

- Python 3.8 or higher
- `requests` >= 2.31.0
- `pydantic` >= 2.0.0
- `typing-extensions` >= 4.0.0 (for Python < 3.10)

## Support

- **Documentation**: [https://docs.whizo.ai](https://docs.whizo.ai)
- **Dashboard**: [https://whizo.ai/app](https://whizo.ai/app)
- **Email**: support@whizo.ai
- **GitHub Issues**: [https://github.com/whizoai/whizoai-sdks/issues](https://github.com/whizoai/whizoai-sdks/issues)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes in each version.

---

**Made with ❤️ by the WhizoAI Team**
