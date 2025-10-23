# Apala API - Python SDK

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Type Hints](https://img.shields.io/badge/type--hints-yes-brightgreen)](https://docs.python.org/3/library/typing.html)


## 🚀 Quick Start

### Installation

```bash
# Install the package
pip install apala-api

# Or install from source with development tools
git clone <repository-url>
cd apala_api
pip install -e ".[dev]"
```

### Basic Usage

```python
from apala_client import ApalaClient, Message, MessageFeedback

# Initialize client
client = ApalaClient(
    api_key="your-api-key", 
    base_url="https://your-server.com"
)

# Authenticate (automatic JWT token management)
client.authenticate()

# Create customer message history
messages = [
    Message(content="Hi, I need help with my loan application.", channel="EMAIL"),
    Message(content="What are the current interest rates?", channel="SMS"),
    Message(content="When will I hear back about approval?", channel="EMAIL")
]

# Create your candidate response
candidate = Message(
    content="Thank you for your inquiry! Our current rates start at 3.5% APR for qualified borrowers. We'll review your application and respond within 2 business days.",
    channel="EMAIL"
)

# Process messages through the AI system
response = client.message_process(
    message_history=messages,
    candidate_message=candidate,
    customer_id="550e8400-e29b-41d4-a716-446655440000",
    zip_code="90210",
    company_guid="550e8400-e29b-41d4-a716-446655440001"
)

print(f"Processed message ID: {response['candidate_message']['message_id']}")

# Submit feedback after customer interaction
feedback = MessageFeedback(
    original_message_id=response["candidate_message"]["message_id"],
    sent_message_content=response["candidate_message"]["content"],
    customer_responded=True,
    quality_score=85,
    time_to_respond_ms=1800000  # 30 minutes
)

feedback_result = client.submit_single_feedback(feedback)
print(f"Feedback submitted: {feedback_result['feedback_id']}")
```

## 🎯 Core Features

### ✅ **Type-Safe API**
- Full **TypedDict** responses with IDE autocomplete
- **mypy** integration catches errors at development time
- **No runtime surprises** - all response fields are typed

### ✅ **Complete Functionality**
- **Message Processing**: Analyze customer conversations and candidate responses
- **Message Optimization**: Enhance messages for maximum engagement
- **Feedback Tracking**: Monitor message performance and customer responses
- **Authentication**: Automatic JWT token management with refresh

### ✅ **Production Ready**
- **Multi-Python Support**: Python 3.9, 3.10, 3.11, 3.12
- **Comprehensive Testing**: Unit tests, integration tests, type checking
- **Error Handling**: Uses standard `requests` exceptions (no custom exceptions)
- **Validation**: Client-side validation of UUIDs, zip codes, channels

### ✅ **Developer Experience**
- **Interactive Demo**: Marimo notebook with complete workflow
- **Documentation**: Full Sphinx docs with examples
- **Code Quality**: Ruff formatting, mypy type checking, tox multi-version testing

## 📖 Documentation

### Authentication

The SDK uses a secure two-tier authentication system:

1. **API Key**: Your long-lived company credentials
2. **JWT Tokens**: Short-lived session tokens for API calls (auto-managed)

```python
# Authentication is automatic - just provide your API key
client = ApalaClient(api_key="your-api-key")
auth_response = client.authenticate()

# JWT tokens are automatically refreshed when needed
# No manual token management required!
```

### Message Processing Workflow

```python
# 1. Create message objects with validation
customer_messages = [
    Message(
        content="I'm interested in a home loan",
        channel="EMAIL",
        reply_or_not=False
    ),
    Message(
        content="What documents do I need?", 
        channel="SMS",
        reply_or_not=False
    )
]

# 2. Define your candidate response
candidate_response = Message(
    content="Great! For a home loan, you'll need: income verification, credit report, and bank statements. We offer competitive rates starting at 3.2% APR.",
    channel="EMAIL"
)

# 3. Process through AI system
result = client.message_process(
    message_history=customer_messages,
    candidate_message=candidate_response,
    customer_id="customer-uuid-here",
    zip_code="12345",
    company_guid="company-uuid-here"
)

# 4. Get typed response with IDE completion
message_id = result["candidate_message"]["message_id"]  # Type: str
company = result["company"]  # Type: str
customer = result["customer_id"]  # Type: str
```

### Message Optimization

Enhance your messages for better customer engagement:

```python
# Optimize your message for maximum engagement
optimization = client.optimize_message(
    message_history=customer_messages,
    candidate_message=candidate_response,
    customer_id="customer-uuid",
    zip_code="12345", 
    company_guid="company-uuid"
)

print(f"Original: {optimization['original_message']}")
print(f"Optimized: {optimization['optimized_message']}")
print(f"Recommended channel: {optimization['recommended_channel']}")
```

### Feedback Tracking

Monitor message performance and learn from customer interactions:

```python
# Track how customers respond to your messages
feedback = MessageFeedback(
    original_message_id="message-id-from-processing",
    sent_message_content="The actual message you sent",
    customer_responded=True,
    quality_score=88,  # 0-100 quality rating
    time_to_respond_ms=1200000  # 20 minutes in milliseconds
)

result = client.submit_single_feedback(feedback)
print(f"Feedback recorded with ID: {result['feedback_id']}")

# Or submit multiple feedback items at once
feedback_list = [(message1, feedback1), (message2, feedback2)]
results = client.message_feedback(feedback_list)
```

## 🔧 Configuration

### Environment Variables

Set these for production deployment:

```bash
# Required
export APALA_API_KEY="your-production-api-key"
export APALA_BASE_URL="https://your-phoenix-server.com"
export APALA_COMPANY_GUID="your-company-uuid"

# Optional
export APALA_CUSTOMER_ID="default-customer-uuid"  # For testing
```

### Client Configuration

```python
# Basic configuration
client = ApalaClient(
    api_key="your-key",
    base_url="https://api.yourcompany.com"
)

# Advanced usage with custom session
import requests
session = requests.Session()
session.timeout = 30  # Custom timeout
client = ApalaClient(api_key="your-key")
client._session = session
```

## 🧪 Testing & Development

### Setup

```bash
# Clone and install in development mode with uv
git clone <repository-url>
cd apala_api
uv sync --group dev
```

### Running Tests

```bash
# Run unit tests
uv run pytest tests/test_models.py tests/test_client.py -v

# Run with coverage
uv run pytest --cov=apala_client --cov-report=html

# Run integration tests (requires running server)
# In Fish shell:
env RUN_INTEGRATION_TESTS=1 APALA_API_KEY=test-key APALA_COMPANY_GUID=test-company-uuid uv run pytest tests/test_integration.py

# In Bash/Zsh:
export RUN_INTEGRATION_TESTS=1 APALA_API_KEY=test-key APALA_COMPANY_GUID=test-company-uuid
uv run pytest tests/test_integration.py
```

### Code Quality

```bash
# Static type checking
uv run mypy .

# Linting
uv run ruff check .

# Code formatting
uv run ruff format .
```

### Documentation

```bash
# Build HTML documentation
uv run sphinx-build -b html docs docs/_build/html

# Build with live reload (auto-refreshes on changes)
uv run sphinx-autobuild docs docs/_build/html --port 8001

# Clean build directory
uv run python -c "import shutil; shutil.rmtree('docs/_build', ignore_errors=True)"

# Check for broken links
uv run sphinx-build -b linkcheck docs docs/_build/linkcheck
```

### Multi-Python Testing

```bash
# Test across Python versions
uv run tox

# Test specific version
uv run tox -e py311
```

## 📊 Interactive Demo

Try the complete workflow in an interactive notebook:

```bash
# Install notebook dependencies
pip install -e ".[notebook]"

# Run the interactive demo
cd notebooks
marimo run apala_demo.py
```

The demo covers:
- 🔐 Authentication setup
- 📤 Message processing workflow  
- 🎯 Message optimization
- 📊 Feedback submission
- ⚡ Error handling examples

## 🛡️ Error Handling

The SDK uses standard Python exceptions - no custom error types to learn:

```python
import requests
from apala_client import ApalaClient

client = ApalaClient(api_key="your-key")

try:
    # All SDK methods may raise requests exceptions
    response = client.message_process(...)
    
except requests.HTTPError as e:
    # HTTP errors (4xx, 5xx responses)
    print(f"HTTP {e.response.status_code}: {e}")
    
except requests.ConnectionError as e:
    # Network connectivity issues
    print(f"Connection failed: {e}")
    
except requests.Timeout as e:
    # Request timeout
    print(f"Request timed out: {e}")
    
except requests.RequestException as e:
    # Any other requests-related error
    print(f"Request error: {e}")
    
except ValueError as e:
    # Data validation errors (invalid UUIDs, etc.)
    print(f"Invalid data: {e}")
```

## 🔍 API Reference

### ApalaClient

Main client class for all API interactions.

#### Constructor
```python
ApalaClient(api_key: str, base_url: str = "http://localhost:4000")
```

#### Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `authenticate()` | `AuthResponse` | Exchange API key for JWT tokens |
| `refresh_access_token()` | `RefreshResponse` | Refresh access token |
| `message_process(...)` | `MessageProcessingResponse` | Process customer messages |
| `optimize_message(...)` | `MessageOptimizationResponse` | Optimize message content |
| `submit_single_feedback(...)` | `FeedbackResponse` | Submit single feedback |
| `message_feedback(...)` | `List[FeedbackResponse]` | Submit multiple feedback items |
| `close()` | `None` | Close HTTP session |

### Data Models

#### Message
Customer or candidate message with validation.

```python
@dataclass
class Message:
    content: str  # Message text
    channel: str  # "SMS", "EMAIL", "OTHER"
    message_id: Optional[str] = None  # Auto-generated if None
    send_timestamp: Optional[str] = None  # Auto-generated if None  
    reply_or_not: bool = False  # Whether this is a reply
```

#### MessageFeedback
Performance feedback for processed messages.

```python
@dataclass
class MessageFeedback:
    original_message_id: str  # ID from message processing
    sent_message_content: str  # Actual message sent to customer
    customer_responded: bool  # Did customer respond?
    quality_score: int  # Quality rating 0-100
    time_to_respond_ms: Optional[int] = None  # Response time in milliseconds
```

### Response Types

All API responses are fully typed with TypedDict:

#### AuthResponse
```python
class AuthResponse(TypedDict):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    company_id: str
    company_name: str
```

#### MessageProcessingResponse
```python
class MessageProcessingResponse(TypedDict):
    company: str
    customer_id: str
    candidate_message: CandidateMessageResponse

class CandidateMessageResponse(TypedDict):
    content: str
    channel: str
    message_id: str
```

*See full API documentation for complete type definitions.*

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Add tests** for new functionality
4. **Run the test suite** (`pytest` and `mypy apala_client`)
5. **Commit** your changes (`git commit -m 'Add amazing feature'`)
6. **Push** to your branch (`git push origin feature/amazing-feature`)
7. **Create** a Pull Request

### Development Setup

```bash
git clone <your-fork>
cd apala_api
pip install -e ".[dev]"

# Run all checks before submitting
pytest                    # Unit tests
mypy apala_client        # Type checking  
ruff check apala_client  # Linting
ruff format apala_client # Formatting
tox                      # Multi-Python testing
```

## 📄 License

Copyright (c) 2025 Apala Cap. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution, or use of this software, via any medium, is strictly prohibited.

## 🔗 Links

- **Documentation**: [Full API Documentation](docs/)
- **Source Code**: [GitHub Repository](#)
- **Issue Tracker**: [GitHub Issues](#)
- **PyPI Package**: [apala-api](#)

## 💬 Support

- **GitHub Issues**: For bugs and feature requests
- **Documentation**: Complete API reference and guides
- **Type Safety**: Full mypy support for development-time error catching

---

*Apala API - Proprietary Software by Apala Cap*
