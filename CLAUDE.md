# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

APIRunner is a minimal HTTP API test runner with a YAML-based DSL. It supports `${...}`-style expressions, JMESPath extraction, and multiple report formats.

**Key Features:**
- YAML test cases with declarative syntax
- Dollar-style templating: `${...}` expressions (`$var`, `${func()}`)
- Custom hooks via `arun_hooks.py` for helper functions
- Tag-based test filtering
- Parameterized testing (enumerate/matrix)
- JSON/HTML reporting

## Development Commands

### Installation
```bash
# Install in development mode
pip install -e .

# The CLI command 'arun' will be available after installation
```

### Running Tests

```bash
# Basic usage: run all tests in testcases/
arun run testcases --env-file .env

# With filtering by tag
arun run testcases -k "smoke" --env-file .env

# With full reporting
arun run testcases \
  --env-file .env \
  --report reports/run.json \
  --html reports/report.html \
  --log-level debug

# With variable overrides
arun run testcases --vars base_url=http://localhost:9000 --vars user=admin

# Fail fast on first error
arun run testcases --failfast --env-file .env

# Merge multiple JSON reports
arun report reports/run1.json reports/run2.json -o reports/merged.json
```

### Test File Naming
Test files should follow these conventions:
- Located in `testcases/` or `testsuites/` directories, OR
- Named with prefix `test_*.yaml` (cases) or `suite_*.yaml` (suites)

## Architecture

### Request Flow

```
CLI (cli.py)
  ↓
Loader (loader/)
  - collector.py: discover test files
  - yaml_loader.py: parse YAML into Case/Suite models
  - hooks.py: load custom functions from arun_hooks.py
  ↓
Runner (runner/runner.py)
  - VarContext: manage variable scoping
  - TemplateEngine: render templates with variables + functions
  - HTTPClient: execute HTTP requests (engine/http.py)
  - extractors.py: JMESPath extraction from responses
  - assertions.py: validate responses with comparators
  ↓
Reporters (reporter/)
  - json_reporter.py: structured JSON output
  - html_reporter.py: interactive HTML report
  - html_reporter.py: interactive HTML report
```

### Templating System

**Templating** (`apirunner/templating/engine.py`): Only Dollar expressions `${...}` are supported.

**Variable Scoping** (priority order, highest to lowest):
1. CLI overrides: `--vars key=value`
2. Step-level: `steps[].variables`
3. Config-level: `config.variables`
4. Parameters: `parameters` (enumerate/matrix expansion)
5. Extracts: `steps[].extract` (from previous step responses)

Implementation: `apirunner/templating/context.py` (VarContext with push/pop stack)

### Hooks Mechanism

**Custom Functions** (`apirunner/loader/hooks.py`):
- Searches upward from test file for `arun_hooks.py` (or `hooks.py`)
- Configurable via `ARUN_HOOKS_FILE` env var (comma-separated list)
- Auto-loads all callable objects (non-underscore prefixed)
- Functions available in templates via Dollar syntax: `${my_function(arg)}`

Example `arun_hooks.py`:
```python
import time, hashlib

def ts() -> int:
    return int(time.time())

def md5(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()

def sign(app_key: str, ts: int) -> str:
    return md5(f"{app_key}{ts}")
```

### Models & Validation

**Pydantic Models** (`apirunner/models/`):
- `Case`: config + parameters + steps[]
- `Suite`: config + cases[] (inherits config to children)
- `Step`: request + validate + extract + skip + retry
- `Config`: base_url, variables, headers, timeout, verify, tags

**Suite Inheritance** (`apirunner/loader/yaml_loader.py:45-54`):
When loading a suite file, each case inherits:
- `base_url` (if not set in case)
- `variables` (merged: suite vars + case vars)
- `headers` (merged: suite headers + case headers)
- `tags` (union of suite and case tags)

### Parameterization

**Two modes** (`apirunner/loader/yaml_loader.py:expand_parameters`):

1. **Enumerate** (list of dicts):
```yaml
parameters:
  - {user: alice, role: admin}
  - {user: bob, role: user}
```

2. **Matrix** (cartesian product):
```yaml
parameters:
  env: [dev, staging]
  region: [us, eu]
# Generates: [{env: dev, region: us}, {env: dev, region: eu}, {env: staging, region: us}, {env: staging, region: eu}]
```

### Tag Filtering

**Expression Syntax** (`apirunner/loader/collector.py:match_tags`):
- Operators: `and`, `or`, `not`
- Case-insensitive matching
- Left-to-right evaluation (`and` binds tighter than `or`)

Examples:
- `-k "smoke"`: only smoke tests
- `-k "smoke and regression"`: both tags required
- `-k "smoke or p0"`: either tag matches
- `-k "not slow"`: exclude slow tests

### Retry & Backoff

**Failure Retry** (`apirunner/runner/runner.py:72-86`):
- `retry`: max retry attempts (default 0)
- `retry_backoff`: initial backoff in seconds (default 0.1)
- Exponential backoff: `backoff * (2 ** attempt)`, capped at 2.0s

### Assertions & Extraction

**Comparators** (`apirunner/runner/assertions.py`):
- `eq, ne, lt, le, gt, ge`: numeric/string comparison
- `contains, not_contains`: substring/element membership
- `regex`: pattern matching
- `len_eq`: length validation
- `in, not_in`: reverse membership

**Check Targets** (`apirunner/runner/runner.py:_resolve_check`):
- `status_code`: HTTP status
- `headers.X`: specific header
- `body.field.subfield`: JMESPath on JSON body
- `field`: shorthand for `body.field`

**Extraction** (`apirunner/runner/extractors.py`):
- Uses JMESPath library for JSON querying
- Extracted variables added to VarContext for subsequent steps

## Key Files

### Core Logic
- `apirunner/cli.py`: CLI entry point, orchestrates discovery → loading → execution → reporting
- `apirunner/runner/runner.py`: Main test execution engine (run_case method)
- `apirunner/loader/yaml_loader.py`: YAML parsing, suite inheritance, parameter expansion
- `apirunner/templating/engine.py`: Template rendering with dual syntax support

### HTTP Layer
- `apirunner/engine/http.py`: HTTPClient wrapper around httpx
- Supports basic/bearer auth, file uploads, custom headers, redirects

### Utilities
- `apirunner/utils/logging.py`: Rich console logging + file output
- `apirunner/utils/mask.py`: Sanitize sensitive data in reports
- `apirunner/utils/curl.py`: Generate curl commands for debugging

### Environment Configuration
- `.env.example`: Template for environment variables
- Variables auto-mapped to lowercase for templating (e.g., `BASE_URL` → `base_url`)

## Common Patterns

### Adding New Comparators
Edit `apirunner/runner/assertions.py`, add to `compare()` function.

### Adding New Built-in Functions
Edit `apirunner/templating/builtins.py`, export in `BUILTINS` dict.

### Extending Models
Modify Pydantic models in `apirunner/models/`, ensure backward compatibility with existing YAML files.

### Custom Reporters
Implement in `apirunner/reporter/`, follow pattern from `json_reporter.py` (accepts `RunReport` model).
