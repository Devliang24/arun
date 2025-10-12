# APIRunner

<div align="center">

**A lightweight, powerful HTTP API testing framework with YAML-based DSL**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[Features](#features) • [Quick Start](#quick-start) • [Documentation](#documentation) • [Examples](#examples)

</div>

---

## Overview

APIRunner is a modern, minimal HTTP API test runner designed for simplicity and power. Write your API tests in clean YAML syntax, leverage powerful templating and extraction capabilities, and generate comprehensive test reports—all without writing a single line of code.

APIRunner offers a streamlined, Pythonic approach to API testing with first-class support for:
- **YAML-First**: Declarative test cases in human-readable YAML
- **Dual Templating**: Both `${...}` expression and Jinja2 (`{{ ... }}`) syntax
- **Smart Extraction**: JMESPath-powered JSON response extraction
- **Flexible Hooks**: Custom Python functions for setup, teardown, and request signing
- **Rich Reporting**: JSON, JUnit XML, and interactive HTML reports
- **SQL Validation**: Built-in database assertion support
- **CI/CD Ready**: Designed for seamless integration with your pipeline

## Features

### Core Capabilities

- **Declarative YAML DSL**: Write tests in clean, maintainable YAML syntax
- **Powerful Templating Engine**:
  - `${...}` expressions: `${variable}`, `${function()}`
  - Jinja2 templates: `{{ variable }}`, `{{ function() }}`
  - Environment variable injection: `${ENV(VAR_NAME)}`
- **Advanced Response Handling**:
  - JMESPath-based extraction: `$.data.user.id`
  - Rich assertion library: `eq`, `contains`, `regex`, `lt`, `gt`, etc.
  - Automatic token/auth injection
- **Test Organization**:
  - Tag-based filtering with logical expressions
  - Parameterized testing (enumerate, matrix, zipped)
  - Suite-level and case-level configuration inheritance
- **Custom Hooks System**:
  - Setup/teardown hooks at suite, case, and step levels
  - Request signing and authentication hooks
  - Custom validation and data transformation
- **Database Integration**:
  - SQL response validation
  - Query results stored as variables
  - Multiple database connection support
- **Professional Reporting**:
  - Detailed JSON reports with full request/response logs
  - JUnit XML for CI/CD integration
  - Interactive HTML reports with filtering and search
- **Security Features**:
  - Automatic sensitive data masking
  - Configurable secret revelation for debugging
- **Developer Experience**:
  - Fast execution with connection pooling
  - Retry logic with exponential backoff
  - Rich console output with color coding
  - Curl command generation for debugging

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/apirunner.git
cd apirunner

# Install in development mode
pip install -e .

# Verify installation
arun --help
```

### Your First Test

1. **Create environment file** (`.env`):
```env
BASE_URL=https://api.example.com
USER_USERNAME=test_user
USER_PASSWORD=test_pass
```

2. **Write a test case** (`testcases/test_health.yaml`):
```yaml
config:
  name: Health Check
  base_url: ${ENV(BASE_URL)}
  tags: [smoke, health]

steps:
  - name: Check API health
    request:
      method: GET
      url: /health
    validate:
      - eq: [status_code, 200]
      - eq: [$.status, "healthy"]
      - contains: [$.data, "version"]
```

3. **Run the test**:
```bash
arun run testcases/test_health.yaml --env-file .env --html reports/report.html
```

4. **View results**:
```
Total: 1 Passed: 1 Failed: 0 Skipped: 0 Duration: 145.3ms
HTML report written to reports/report.html
```

## Installation

### Requirements

- Python 3.10 or higher
- pip (Python package installer)

### Dependencies

APIRunner has minimal dependencies:
- `httpx` (>=0.27) - Modern HTTP client
- `pydantic` (>=2.6) - Data validation
- `jinja2` (>=3.1) - Template engine
- `jmespath` (>=1.0) - JSON extraction
- `PyYAML` (>=6.0) - YAML parsing
- `rich` (>=13.7) - Beautiful terminal output
- `typer` (>=0.12) - CLI framework

### Installation Methods

**Development Installation:**
```bash
git clone https://github.com/your-org/apirunner.git
cd apirunner
pip install -e .
```

**From Source:**
```bash
pip install git+https://github.com/your-org/apirunner.git
```

## Usage

### Basic Commands

**Run tests:**
```bash
# Run all tests in a directory
arun run testcases --env-file .env

# Run with tag filtering
arun run testcases -k "smoke and not slow" --env-file .env

# Run with variable overrides
arun run testcases --vars base_url=http://localhost:8000 --vars debug=true

# Generate all report types
arun run testcases \
  --env-file .env \
  --report reports/run.json \
  --junit reports/junit.xml \
  --html reports/report.html \
  --log-level debug

**Notifications (optional):**
```bash
# Send Feishu notification on failure only
ARUN_NOTIFY_ONLY=failed FEISHU_WEBHOOK=https://open.feishu.cn/xxx \
python -m apirunner.cli run testcases --env-file .env --notify feishu

# Send email notification always (attach HTML report)
SMTP_HOST=smtp.example.com SMTP_PORT=465 SMTP_USER=noreply@example.com \
SMTP_PASS=app-pass MAIL_FROM=noreply@example.com MAIL_TO=qa@example.com \
python -m apirunner.cli run testcases --env-file .env --notify email --notify-only always --notify-attach-html
```
```

**Validate YAML syntax:**
```bash
# Check YAML files without running tests
arun check testcases
```

**Auto-fix YAML style:**
```bash
# Migrate hooks to new config-based format
arun fix testcases
```

**Merge reports:**
```bash
# Combine multiple JSON reports
arun report reports/run1.json reports/run2.json -o reports/merged.json
```

### Command-Line Options

| Option | Description |
|--------|-------------|
| `path` | File or directory to run (required) |
| `-k EXPR` | Tag filter expression (e.g., `"smoke and not slow"`) |
| `--vars k=v` | Variable overrides (repeatable) |
| `--failfast` | Stop on first failure |
| `--report FILE` | Write JSON report |
| `--junit FILE` | Write JUnit XML report |
| `--html FILE` | Write HTML report |
| `--log-level LEVEL` | Logging level (INFO, DEBUG) |
| `--env-file FILE` | Environment file path (default: `.env`) |
| `--log-file FILE` | Log file path (default: `logs/run-<timestamp>.log`) |
| `--httpx-logs` | Show httpx internal logs |
| `--mask-secrets` | Hide sensitive data in logs/reports |

## Documentation

### DSL Syntax Reference

#### Test Case Structure

```yaml
config:
  name: Test Case Name                    # Required
  base_url: https://api.example.com       # Optional (can use ${ENV(BASE_URL)})
  variables:                              # Optional case-level variables
    user_id: 12345
    api_key: secret
  headers:                                # Optional default headers
    X-API-Version: "v1"
  timeout: 30.0                           # Optional request timeout (seconds)
  verify: true                            # Optional SSL verification
  tags: [smoke, regression]               # Optional tags for filtering
  setup_hooks:                            # Optional case setup hooks
    - ${setup_function()}
  teardown_hooks:                         # Optional case teardown hooks
    - ${teardown_function()}

parameters:                               # Optional parameterization
  env: [dev, staging]                     # Matrix: generates 2 test instances
  region: [us, eu]                        # Matrix: 2 x 2 = 4 instances total

steps:
  - name: Step Name                       # Required
    variables:                            # Optional step-level variables
      custom_id: abc123

    request:                              # Required
      method: POST                        # Required: GET, POST, PUT, DELETE, etc.
      url: /api/users                     # Required: absolute or relative to base_url
      params:                             # Optional query parameters
        page: 1
        limit: 10
      headers:                            # Optional headers (merged with config)
        Content-Type: application/json
      json:                               # Optional JSON body
        username: ${ENV(USER_USERNAME)}
        email: user@example.com
      data:                               # Optional form data
        key: value
      files:                              # Optional file uploads
        file: /path/to/file.pdf
      auth:                               # Optional authentication
        type: bearer                      # bearer or basic
        token: ${ENV(API_TOKEN)}
      timeout: 10.0                       # Optional request-specific timeout
      verify: true                        # Optional SSL verification
      allow_redirects: true               # Optional redirect handling

    extract:                              # Optional response extraction
      user_id: $.data.user.id            # JMESPath expression ($ required)
      token: $.data.access_token         # Stored for use in subsequent steps

    validate:                             # Optional assertions
      - eq: [status_code, 200]           # Status code check
      - eq: [$.success, true]            # Response body check
      - contains: [$.message, "success"] # Substring check
      - regex: [$.email, ".*@.*\\.com"]  # Regex pattern
      - lt: [$elapsed_ms, 2000]          # Response time check

    sql_validate:                         # Optional SQL validation
      - query: "SELECT status FROM users WHERE id='$user_id'"
        expect:
          - eq: [status, "active"]
        store:                            # Store query results as variables
          db_status: status

    setup_hooks:                          # Optional step setup hooks
      - ${sign_request($request)}

    teardown_hooks:                       # Optional step teardown hooks
      - ${validate_response($response)}

    skip: false                           # Optional: skip this step
    retry: 3                              # Optional: retry count on failure
    retry_backoff: 0.5                    # Optional: initial backoff (seconds)
```

#### Suite Structure

```yaml
config:
  name: Test Suite Name
  base_url: ${ENV(BASE_URL)}
  variables:
    suite_var: value
  tags: [integration]
  setup_hooks:                            # Suite-level setup (runs once)
    - ${suite_setup()}
  teardown_hooks:                         # Suite-level teardown (runs once)
    - ${suite_teardown()}

cases:
  - config:
      name: Case 1
      tags: [smoke]
    steps:
      - name: Step 1
        request:
          method: GET
          url: /api/endpoint
        validate:
          - eq: [status_code, 200]

  - config:
      name: Case 2
      tags: [regression]
    steps:
      - name: Step 1
        request:
          method: POST
          url: /api/endpoint
        validate:
          - eq: [status_code, 201]
```

### Templating System

APIRunner supports dual templating syntax:

#### Dollar Style (Recommended)

```yaml
# Variable reference
url: /users/$user_id                    # Simple variable

# Function call
headers:
  X-Timestamp: ${ts()}                  # Current timestamp
  X-Signature: ${sign($app_key, ts())} # Custom function

# Environment variable
base_url: ${ENV(BASE_URL)}              # Read from environment

# Complex expression
json:
  user_id: ${int($user_id) + 1}        # Arithmetic
```

#### Jinja2 Style (Alternative)

```yaml
# Variable reference
url: /users/{{ user_id }}

# Function call
headers:
  X-Timestamp: {{ ts() }}
  X-Signature: {{ sign(app_key, ts()) }}

# Filters and logic
message: {{ username | upper }}
```

**Variable Precedence** (highest to lowest):
1. CLI overrides: `--vars key=value`
2. Step-level: `steps[].variables`
3. Config-level: `config.variables`
4. Parameters: `parameters`
5. Extracts: `steps[].extract`
6. Environment: `${ENV(KEY)}`

### Assertions (Validators)

| Comparator | Description | Example |
|------------|-------------|---------|
| `eq` | Equal | `- eq: [status_code, 200]` |
| `ne` | Not equal | `- ne: [$.error, null]` |
| `lt` | Less than | `- lt: [$elapsed_ms, 1000]` |
| `le` | Less than or equal | `- le: [$.price, 100]` |
| `gt` | Greater than | `- gt: [$.count, 0]` |
| `ge` | Greater than or equal | `- ge: [$.age, 18]` |
| `contains` | Contains substring/element | `- contains: [$.message, "success"]` |
| `not_contains` | Does not contain | `- not_contains: [$.errors, "fatal"]` |
| `regex` | Regex match | `- regex: [$.email, ".*@example\\.com"]` |
| `len_eq` | Length equals | `- len_eq: [$.items, 10]` |
| `in` | Element in collection | `- in: ["admin", $.roles]` |
| `not_in` | Element not in collection | `- not_in: ["banned", $.statuses]` |

**Check Targets:**
- `status_code` - HTTP status code
- `headers.Header-Name` - Response header (case-insensitive)
- `$.path.to.field` - JSON body field (JMESPath)
- `$[0].id` - Array element
- `$elapsed_ms` - Response time in milliseconds

### Extraction (JMESPath)

Extract data from responses to use in subsequent steps:

```yaml
extract:
  # Extract single field
  user_id: $.data.user.id

  # Extract from array
  first_item: $[0].name

  # Extract nested field
  access_token: $.data.auth.access_token

  # Extract header
  rate_limit: $headers.X-RateLimit-Remaining

  # Extract status code
  status: $status_code
```

Extracted variables are automatically available in all subsequent steps.

### Parameterization

Run the same test with multiple input combinations:

#### Enumerate (List of Dicts)

```yaml
parameters:
  - {username: alice, role: admin}
  - {username: bob, role: user}
  - {username: charlie, role: guest}

# Generates 3 test instances
```

#### Matrix (Cartesian Product)

```yaml
parameters:
  env: [dev, staging, prod]
  region: [us, eu, asia]

# Generates 3 × 3 = 9 test instances
```

#### Zipped (Parallel Arrays)

```yaml
parameters:
  - username-password:
      - [alice, pass123]
      - [bob, secret456]
      - [charlie, pwd789]

# Generates 3 test instances with paired values
```

### Hooks System

Hooks are Python functions that run at specific points in the test lifecycle.

#### Hook Types

1. **Suite Hooks** (in `config.setup_hooks` / `config.teardown_hooks`)
2. **Case Hooks** (in `config.setup_hooks` / `config.teardown_hooks`)
3. **Step Hooks** (in `steps[].setup_hooks` / `steps[].teardown_hooks`)

#### Creating Custom Hooks

Create `arun_hooks.py` in your project root:

```python
import time
import hashlib
import hmac

def ts() -> int:
    """Return current Unix timestamp"""
    return int(time.time())

def md5(s: str) -> str:
    """Calculate MD5 hash"""
    return hashlib.md5(s.encode()).hexdigest()

def setup_hook_sign_request(request: dict, variables: dict, env: dict) -> dict:
    """
    Setup hook: sign the request with HMAC-SHA256

    Args:
        request: Request dict (mutable, modify in-place)
        variables: Current variables dict
        env: Environment variables dict

    Returns:
        Dict of new variables to inject (or None)
    """
    secret = env.get('APP_SECRET', '').encode()
    method = request.get('method', 'GET')
    url = request.get('url', '')
    timestamp = str(ts())

    # Calculate signature
    raw = f"{method}|{url}|{timestamp}".encode()
    sig = hmac.new(secret, raw, hashlib.sha256).hexdigest()

    # Modify request headers
    headers = request.setdefault('headers', {})
    headers['X-Timestamp'] = timestamp
    headers['X-Signature'] = sig

    # Return new variables
    return {'last_signature': sig, 'last_timestamp': timestamp}

def teardown_hook_assert_status_ok(response: dict, variables: dict, env: dict) -> None:
    """
    Teardown hook: verify response status is 200

    Args:
        response: Response dict with status_code, headers, body, etc.
        variables: Current variables dict
        env: Environment variables dict

    Returns:
        None (or dict of new variables)

    Raises:
        AssertionError: If status code is not 200
    """
    if response.get('status_code') != 200:
        raise AssertionError(f"Expected 200, got {response.get('status_code')}")
```

#### Using Hooks in YAML

```yaml
config:
  name: Signed Request Test
  base_url: ${ENV(BASE_URL)}
  setup_hooks:
    - ${setup_hook_sign_request($request)}

steps:
  - name: Make signed request
    setup_hooks:
      - ${setup_hook_sign_request($request)}
    request:
      method: GET
      url: /api/secure
    teardown_hooks:
      - ${teardown_hook_assert_status_ok($response)}
    validate:
      - eq: [status_code, 200]
```

**Hook Context Variables:**
- `$request` / `$step_request` - Request dict
- `$response` / `$step_response` - Response dict
- `$step_name` - Current step name
- `$step_variables` - Step-level variables
- `$session_variables` - All session variables
- `$session_env` - Environment variables

### SQL Validation

Validate API responses against database state:

#### Setup

Install a database driver:
```bash
pip install pymysql  # For MySQL/MariaDB
```

Configure connection in `.env`:
```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=test_user
MYSQL_PASSWORD=test_pass
MYSQL_DB=test_db

# Or use DSN
MYSQL_DSN=mysql://user:pass@localhost:3306/test_db
```

#### Usage

```yaml
steps:
  - name: Create order
    request:
      method: POST
      url: /api/orders
      json:
        sku: "PRODUCT-123"
        quantity: 2
    extract:
      order_id: $.data.order_id

    sql_validate:
      # Query 1: Verify order status
      - query: "SELECT status, total FROM orders WHERE id='$order_id'"
        expect:
          - eq: [status, "pending"]
          - gt: [total, 0]
        store:                         # Store results as variables
          db_status: status
          db_total: total

      # Query 2: Verify order items
      - query: "SELECT COUNT(*) AS cnt FROM order_items WHERE order_id='$order_id'"
        expect:
          - ge: [cnt, 1]
        allow_empty: false             # Fail if query returns no rows

      # Query 3: Override DSN for different database
      - query: "SELECT audit_log FROM audit_db.logs WHERE order_id='$order_id'"
        dsn: mysql://user:pass@audit-host:3306/audit_db
        expect:
          - contains: [audit_log, "order_created"]
```

**SQL Validation Options:**
- `query` - SQL query (required, supports variable interpolation)
- `expect` - Assertions on query results (optional)
- `store` - Store column values as variables (optional)
- `allow_empty` / `optional` - Allow empty result set (default: false)
- `dsn` - Override database connection (optional)

### Tag Filtering

Filter test execution using logical tag expressions:

```bash
# Run tests with 'smoke' tag
arun run testcases -k "smoke"

# Run tests with both 'smoke' AND 'regression' tags
arun run testcases -k "smoke and regression"

# Run tests with either 'smoke' OR 'p0' tags
arun run testcases -k "smoke or p0"

# Run all tests EXCEPT 'slow' ones
arun run testcases -k "not slow"

# Complex expression
arun run testcases -k "(smoke or regression) and not slow and not flaky"
```

**Tag Expression Syntax:**
- `and` - Logical AND (higher precedence)
- `or` - Logical OR
- `not` - Logical NOT
- `( )` - Grouping (left-to-right evaluation)
- Case-insensitive matching

### Auto-Injection Features

#### Bearer Token Auto-Injection

When a variable named `token` is extracted, APIRunner automatically injects `Authorization: Bearer {token}` header in subsequent requests (unless explicitly overridden):

```yaml
steps:
  - name: Login
    request:
      method: POST
      url: /api/auth/login
      json:
        username: ${ENV(USER_USERNAME)}
        password: ${ENV(USER_PASSWORD)}
    extract:
      token: $.data.access_token        # Extract token
    validate:
      - eq: [status_code, 200]

  - name: Get user profile
    request:
      method: GET
      url: /api/users/me
      # No need to manually set Authorization header!
      # APIRunner automatically adds: Authorization: Bearer {token}
    validate:
      - eq: [status_code, 200]
```

### Retry and Backoff

Configure automatic retry for flaky endpoints:

```yaml
steps:
  - name: Flaky endpoint
    request:
      method: GET
      url: /api/sometimes-fails
    retry: 3                            # Retry up to 3 times
    retry_backoff: 0.5                  # Initial backoff: 0.5s
                                        # Exponential: 0.5s, 1.0s, 2.0s (max)
    validate:
      - eq: [status_code, 200]
```

## Architecture

### Project Structure

```
apirunner/
├── apirunner/              # Core package
│   ├── cli.py             # CLI entry point
│   ├── engine/            # HTTP client
│   │   └── http.py
│   ├── loader/            # YAML parsing & discovery
│   │   ├── collector.py   # Test file discovery
│   │   ├── yaml_loader.py # YAML parsing
│   │   ├── hooks.py       # Hook loading
│   │   └── env.py         # Environment loading
│   ├── runner/            # Test execution
│   │   ├── runner.py      # Main runner
│   │   ├── assertions.py  # Assertion logic
│   │   └── extractors.py  # JMESPath extraction
│   ├── templating/        # Template engine
│   │   ├── engine.py      # Dual-syntax rendering
│   │   ├── context.py     # Variable scoping
│   │   └── builtins.py    # Built-in functions
│   ├── models/            # Pydantic models
│   │   ├── case.py        # Case & Suite models
│   │   ├── step.py        # Step model
│   │   ├── config.py      # Config model
│   │   └── report.py      # Report models
│   ├── reporter/          # Report generation
│   │   ├── json_reporter.py
│   │   ├── junit_reporter.py
│   │   ├── html_reporter.py
│   │   └── merge.py
│   ├── db/                # Database support
│   │   └── sql_validate.py
│   └── utils/             # Utilities
│       ├── logging.py     # Rich logging
│       ├── mask.py        # Secret masking
│       └── curl.py        # Curl generation
├── testcases/             # Test case files
├── testsuites/            # Test suite files
├── examples/              # Example tests
├── arun_hooks.py          # Custom hook functions
├── .env                   # Environment variables
└── reports/               # Generated reports
```

### Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CLI (cli.py)                                             │
│    ├─ Parse arguments                                       │
│    ├─ Load environment (.env, --env-file, --vars)          │
│    └─ Discover test files (collector.py)                   │
└────────────────────┬────────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Loader (loader/)                                         │
│    ├─ Parse YAML (yaml_loader.py)                          │
│    ├─ Validate models (models/)                            │
│    ├─ Expand parameters (enumerate/matrix/zipped)          │
│    ├─ Load custom hooks (hooks.py → arun_hooks.py)         │
│    └─ Apply tag filters                                    │
└────────────────────┬────────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Runner (runner/runner.py)                               │
│    ├─ Initialize VarContext (variable scoping)             │
│    ├─ Execute suite/case setup hooks                       │
│    │                                                        │
│    └─ For each step:                                       │
│        ├─ Push step variables to context                   │
│        ├─ Render templates (templating/engine.py)          │
│        ├─ Execute setup hooks                              │
│        ├─ Send HTTP request (engine/http.py)               │
│        ├─ Extract variables (extractors.py)                │
│        ├─ Run assertions (assertions.py)                   │
│        ├─ Execute SQL validations (db/sql_validate.py)     │
│        ├─ Execute teardown hooks                           │
│        └─ Pop step context                                 │
│                                                             │
│    ├─ Execute suite/case teardown hooks                    │
│    └─ Build case result                                    │
└────────────────────┬────────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Reporters (reporter/)                                    │
│    ├─ Aggregate results                                    │
│    ├─ Generate JSON report (json_reporter.py)              │
│    ├─ Generate JUnit XML (junit_reporter.py)               │
│    ├─ Generate HTML report (html_reporter.py)              │
│    └─ Write logs (utils/logging.py)                        │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Dual Templating**: Support both `${...}` and Jinja2 (`{{ ... }}`) for flexibility and migration paths
2. **Immutable Scoping**: Variable contexts use a stack-based approach for clean isolation between steps
3. **Type Preservation**: Single-token templates (`${var}`) preserve native types (int, bool, etc.) instead of stringifying
4. **Hook Signatures**: Flexible hook signatures allow functions to declare only needed parameters
5. **Fail-Fast Option**: `--failfast` stops execution on first failure for rapid feedback
6. **Secret Masking**: Automatic masking of sensitive fields (configurable with `--reveal-secrets`)

## Examples

### Example 1: Login Flow with Token Auto-Injection

```yaml
config:
  name: Login and Access Protected Resource
  base_url: ${ENV(BASE_URL)}
  variables:
    username: ${ENV(USER_USERNAME)}
    password: ${ENV(USER_PASSWORD)}

steps:
  - name: User login
    request:
      method: POST
      url: /api/v1/auth/login
      json:
        username: $username
        password: $password
    extract:
      token: $.data.access_token
      user_id: $.data.user.id
    validate:
      - eq: [status_code, 200]
      - eq: [$.success, true]
      - eq: [$.message, "登录成功"]

  - name: Get user profile
    request:
      method: GET
      url: /api/v1/users/me
      # Authorization: Bearer {token} automatically injected
    validate:
      - eq: [status_code, 200]
      - eq: [$.data.user.id, var:user_id]
```

### Example 2: Parameterized Testing

```yaml
config:
  name: Multi-Environment Health Check
  tags: [smoke, health]

parameters:
  env: [dev, staging, prod]
  region: [us, eu]

steps:
  - name: Check health endpoint
    variables:
      base_url: https://${env}-${region}.example.com
    request:
      method: GET
      url: ${base_url}/health
    validate:
      - eq: [status_code, 200]
      - eq: [$.status, "healthy"]
      - contains: [$.data.region, $region]
```

### Example 3: Request Signing with Hooks

**arun_hooks.py:**
```python
import time
import hmac
import hashlib

def setup_hook_hmac_sign(request: dict, variables: dict, env: dict) -> dict:
    secret = env.get('APP_SECRET', '').encode()
    method = request.get('method', 'GET')
    url = request.get('url', '')
    timestamp = str(int(time.time()))

    message = f"{method}|{url}|{timestamp}".encode()
    signature = hmac.new(secret, message, hashlib.sha256).hexdigest()

    headers = request.setdefault('headers', {})
    headers['X-Timestamp'] = timestamp
    headers['X-Signature'] = signature

    return {'last_signature': signature}
```

**test_signed_request.yaml:**
```yaml
config:
  name: Signed API Request
  base_url: ${ENV(BASE_URL)}

steps:
  - name: Make signed request
    setup_hooks:
      - ${setup_hook_hmac_sign($request)}
    request:
      method: GET
      url: /api/secure/data
    validate:
      - eq: [status_code, 200]
      - eq: [$.authenticated, true]
```

### Example 4: SQL Validation

```yaml
config:
  name: Order Creation with Database Verification
  base_url: ${ENV(BASE_URL)}

steps:
  - name: Create order
    request:
      method: POST
      url: /api/orders
      json:
        product_id: "PROD-001"
        quantity: 5
        shipping_address: "123 Main St, City, 12345"
    extract:
      order_id: $.data.order_id
      total_price: $.data.total_price
    validate:
      - eq: [status_code, 201]
      - eq: [$.success, true]

    sql_validate:
      - query: |
          SELECT status, total_amount, created_at
          FROM orders
          WHERE id = '$order_id'
        expect:
          - eq: [status, "pending"]
          - eq: [total_amount, var:total_price]
        store:
          db_status: status
          db_created_at: created_at

      - query: |
          SELECT COUNT(*) AS item_count
          FROM order_items
          WHERE order_id = '$order_id'
        expect:
          - ge: [item_count, 1]
```

### Example 5: Test Suite with Inheritance

```yaml
config:
  name: User Management Test Suite
  base_url: ${ENV(BASE_URL)}
  variables:
    api_version: v1
  headers:
    X-API-Version: $api_version
  tags: [integration, users]
  setup_hooks:
    - ${setup_hook_suite_init()}
  teardown_hooks:
    - ${teardown_hook_suite_cleanup()}

cases:
  - config:
      name: User Registration
      tags: [registration]
    steps:
      - name: Register new user
        request:
          method: POST
          url: /api/$api_version/users/register
          json:
            username: test_user_${short_uid(8)}
            email: test_${short_uid()}@example.com
            password: SecurePass123!
        extract:
          user_id: $.data.user.id
        validate:
          - eq: [status_code, 201]
          - eq: [$.success, true]

  - config:
      name: User Login
      tags: [auth]
    steps:
      - name: Login with credentials
        request:
          method: POST
          url: /api/$api_version/auth/login
          json:
            username: ${ENV(USER_USERNAME)}
            password: ${ENV(USER_PASSWORD)}
        extract:
          token: $.data.access_token
        validate:
          - eq: [status_code, 200]
          - eq: [$.success, true]
```

### More Examples

Check the `examples/` directory for additional examples:
- `test_params_matrix.yaml` - Matrix parameterization
- `test_params_enumerate.yaml` - Enumeration parameterization
- `test_assertions_showcase.yaml` - All assertion types
- `test_perf_timing.yaml` - Performance assertions
- `test_skip_and_retry.yaml` - Skip and retry logic
- `test_negative_auth.yaml` - Negative test cases
- `suite_hooks.yaml` - Suite-level hooks
- And many more...

Run all examples:
```bash
arun run examples --env-file .env --html reports/examples.html
```

## Environment Configuration

### Environment File Format

**.env (KEY=VALUE format):**
```env
# API Configuration
BASE_URL=https://api.example.com
API_VERSION=v1

# Authentication
USER_USERNAME=test_user
USER_PASSWORD=test_password
API_KEY=your-api-key-here
APP_SECRET=your-hmac-secret

# Database (for SQL validation)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=db_user
MYSQL_PASSWORD=db_password
MYSQL_DB=test_database

# Or use DSN
MYSQL_DSN=mysql://user:pass@localhost:3306/test_db

# Feature Flags
ENABLE_RETRY=true
MAX_RETRY_COUNT=3
```

**Environment variables in YAML:**
```yaml
config:
  base_url: ${ENV(BASE_URL)}      # Read from environment
  variables:
    api_key: ${ENV(API_KEY)}      # Inject into variables
    version: ${ENV(API_VERSION, v1)}  # With default value
```

### Variable Precedence

When the same variable is defined in multiple places:

1. **CLI overrides** (`--vars key=value`) - Highest priority
2. **Step variables** (`steps[].variables`)
3. **Config variables** (`config.variables`)
4. **Parameters** (`parameters`)
5. **Extracted variables** (`steps[].extract`)
6. **Environment** (`${ENV(KEY)}`) - Lowest priority

## Reporting

### JSON Report

Structured JSON output with full request/response details:

```bash
arun run testcases --report reports/run.json
```

**Example output:**
```json
{
  "summary": {
    "total": 10,
    "passed": 8,
    "failed": 2,
    "skipped": 0,
    "duration_ms": 2456.7
  },
  "cases": [
    {
      "name": "Health Check",
      "status": "passed",
      "duration_ms": 145.3,
      "parameters": {},
      "steps": [
        {
          "name": "Check API health",
          "status": "passed",
          "request": {
            "method": "GET",
            "url": "https://api.example.com/health",
            "headers": {...}
          },
          "response": {
            "status_code": 200,
            "headers": {...},
            "body": {...}
          },
          "asserts": [
            {
              "check": "status_code",
              "comparator": "eq",
              "expect": 200,
              "actual": 200,
              "passed": true
            }
          ],
          "duration_ms": 145.3
        }
      ]
    }
  ]
}
```

### JUnit XML Report

CI/CD-compatible XML output:

```bash
arun run testcases --junit reports/junit.xml
```

Integrates with:
- Jenkins
- GitLab CI
- GitHub Actions
- CircleCI
- Azure DevOps

### HTML Report

Interactive HTML report with search and filtering:

```bash
arun run testcases --html reports/report.html
```

Features:
- Summary dashboard with pass/fail statistics
- Expandable test case details
- Request/response inspection
- Assertion results with diff view
- Search and filter capabilities
- Responsive design

### Report Merging

Combine multiple test runs:

```bash
# Run tests in parallel jobs
arun run testcases/smoke --report reports/smoke.json
arun run testcases/regression --report reports/regression.json

# Merge reports
arun report reports/smoke.json reports/regression.json -o reports/merged.json
```

## Advanced Topics

### Test File Discovery

APIRunner discovers test files using these rules:

1. **Directory-based**: Files in `testcases/` or `testsuites/` directories
2. **Name-based**: Files matching `test_*.yaml` (cases) or `suite_*.yaml` (suites)

**Custom hooks file discovery:**
- Search upward from test file for `arun_hooks.py`
- Configurable via `ARUN_HOOKS_FILE` environment variable

```bash
# Use custom hooks file
ARUN_HOOKS_FILE=custom_hooks.py arun run testcases
```

### Sensitive Data Handling

**Automatic masking** (default):
```bash
arun run testcases --env-file .env  # Secrets masked in logs/reports
```

**Reveal secrets for debugging:**
```bash
arun run testcases --env-file .env --reveal-secrets
```

Masked fields:
- `Authorization` header
- `password` fields
- `*token*` fields (access_token, refresh_token, etc.)
- `*secret*` fields
- `*key*` fields (api_key, etc.)

### Performance Testing

Assert on response times:

```yaml
steps:
  - name: Performance-critical endpoint
    request:
      method: GET
      url: /api/data
    validate:
      - eq: [status_code, 200]
      - lt: [$elapsed_ms, 500]    # Must respond in < 500ms
```

### Debugging

**Enable debug logging:**
```bash
arun run testcases --log-level debug --log-file debug.log
```

**Show httpx internal logs:**
```bash
arun run testcases --httpx-logs
```

**Generate curl commands:**
Debug logs automatically include curl equivalents for all requests:
```
[DEBUG] cURL: curl -X POST 'https://api.example.com/login' -H 'Content-Type: application/json' -d '{"username":"test","password":"***"}'
```

## CI/CD Integration

### GitHub Actions

```yaml
name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -e .

      - name: Run API tests
        env:
          BASE_URL: ${{ secrets.API_BASE_URL }}
          USER_USERNAME: ${{ secrets.TEST_USERNAME }}
          USER_PASSWORD: ${{ secrets.TEST_PASSWORD }}
        run: |
          arun run testcases \
            --junit reports/junit.xml \
            --html reports/report.html \
            --mask-secrets

      - name: Publish test results
        uses: EnricoMi/publish-unit-test-result-action@v2
        if: always()
        with:
          files: reports/junit.xml

      - name: Upload HTML report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-report
          path: reports/report.html
```

### GitLab CI

```yaml
stages:
  - test

api-tests:
  stage: test
  image: python:3.10
  before_script:
    - pip install -e .
  script:
    - |
      arun run testcases \
        --env-file .env \
        --junit reports/junit.xml \
        --html reports/report.html \
        --mask-secrets
  artifacts:
    when: always
    reports:
      junit: reports/junit.xml
    paths:
      - reports/
  variables:
    BASE_URL: $API_BASE_URL
    USER_USERNAME: $TEST_USERNAME
    USER_PASSWORD: $TEST_PASSWORD
```

### Jenkins

```groovy
pipeline {
    agent any

    environment {
        BASE_URL = credentials('api-base-url')
        USER_USERNAME = credentials('test-username')
        USER_PASSWORD = credentials('test-password')
    }

    stages {
        stage('Setup') {
            steps {
                sh 'pip install -e .'
            }
        }

        stage('Test') {
            steps {
                sh '''
                    arun run testcases \
                        --junit reports/junit.xml \
                        --html reports/report.html \
                        --mask-secrets
                '''
            }
        }
    }

    post {
        always {
            junit 'reports/junit.xml'
            publishHTML([
                reportDir: 'reports',
                reportFiles: 'report.html',
                reportName: 'API Test Report'
            ])
        }
    }
}
```

## Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/your-org/apirunner.git
cd apirunner

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e .

# Verify installation
arun --help
```

### Running Tests

```bash
# Run all tests
arun run testcases --env-file .env

# Run specific tags
arun run testcases -k "smoke" --env-file .env

# Run with full reporting
arun run testcases \
  --env-file .env \
  --report reports/run.json \
  --junit reports/junit.xml \
  --html reports/report.html \
  --log-level debug
```

### Code Style

This project uses:
- `black` for code formatting
- `ruff` for linting
- `mypy` for type checking

### Git Hooks

Auto-fix YAML formatting on commit:

```bash
# Make pre-commit hook executable
chmod +x scripts/pre-commit-fix-hooks.sh

# Install hook
ln -sf ../../scripts/pre-commit-fix-hooks.sh .git/hooks/pre-commit
```

This automatically runs `arun fix` to migrate hooks to the new config-based format.

## Notes

APIRunner focuses on a minimal core with practical features for everyday API testing without extra bloat.

## Troubleshooting

### Common Issues

**Issue: `ModuleNotFoundError: No module named 'apirunner'`**
```bash
# Solution: Install in editable mode
pip install -e .
```

**Issue: `No YAML test files found`**
```bash
# Solution: Ensure files follow naming convention
# - Located in testcases/ or testsuites/ directories, OR
# - Named test_*.yaml or suite_*.yaml
```

**Issue: `Invalid check 'body.field': use '$' syntax`**
```bash
# Old syntax (deprecated):
validate:
  - eq: [body.user.id, 123]

# New syntax (required):
validate:
  - eq: [$.user.id, 123]
```

**Issue: Hooks not loading**
```bash
# Ensure arun_hooks.py is in project root or parent directory
# Or specify explicitly:
ARUN_HOOKS_FILE=path/to/hooks.py arun run testcases
```

**Issue: SQL validation fails with connection error**
```bash
# Install database driver
pip install pymysql  # For MySQL

# Verify environment variables
echo $MYSQL_HOST $MYSQL_USER $MYSQL_DB

# Or use DSN
export MYSQL_DSN=mysql://user:pass@host:3306/db
```

## Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Make your changes**
4. **Run tests**: `arun run testcases --env-file .env`
5. **Commit**: `git commit -m "feat: add amazing feature"`
6. **Push**: `git push origin feature/your-feature`
7. **Open a Pull Request**

### Contribution Guidelines

- Follow existing code style (black, ruff)
- Add tests for new features
- Update documentation
- Write clear commit messages
- Keep changes focused and atomic

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [httpx](https://www.python-httpx.org/), [pydantic](https://pydantic-docs.helpmanual.io/), [rich](https://rich.readthedocs.io/)
- Thanks to all contributors

## Support

- **Documentation**: See [CLAUDE.md](CLAUDE.md) for detailed technical documentation
- **Examples**: Check the `examples/` directory for sample tests
- **Issues**: Report bugs and request features on [GitHub Issues](https://github.com/your-org/apirunner/issues)

---

<div align="center">

**Built with ❤️ by the APIRunner Team**

[⬆ Back to Top](#apirunner)

</div>
