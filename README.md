# APIRunner

<div align="center">

**轻量级、强大的 HTTP API 测试框架，基于 YAML DSL**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[功能特性](#功能特性) • [快速开始](#快速开始) • [使用文档](#使用文档) • [示例](#示例)

</div>

---

## 项目概述

APIRunner 是一个现代化的、极简的 HTTP API 测试运行器，专为简洁性和强大功能而设计。使用清晰的 YAML 语法编写 API 测试，利用强大的模板和提取能力，生成全面的测试报告——无需编写一行代码。

APIRunner 提供简化的、Python 风格的 API 测试方法，一流支持：
- **YAML 优先**：声明式测试用例，人类可读的 YAML 格式
- **模板**：仅支持 `${...}` Dollar 风格表达式
- **智能提取**：基于 JMESPath 的 JSON 响应提取
- **灵活 Hooks**：自定义 Python 函数，用于 setup、teardown 和请求签名
- **丰富报告**：JSON 和交互式 HTML 报告
- **SQL 验证**：内置数据库断言支持
- **CI/CD 就绪**：专为无缝集成流水线而设计

## 功能特性

### 核心能力

- **声明式 YAML DSL**：使用清晰、可维护的 YAML 语法编写测试
- **强大的模板引擎**：
  - `${...}` 表达式：`${variable}`、`${function()}`
  - 环境变量注入：`${ENV(VAR_NAME)}`
- **高级响应处理**：
  - 基于 JMESPath 的提取：`$.data.user.id`
  - 丰富的断言库：`eq`、`contains`、`regex`、`lt`、`gt` 等
  - 自动 token/认证注入
- **测试组织**：
  - 基于标签的过滤，支持逻辑表达式
  - 参数化测试（枚举、矩阵、压缩）
  - 套件级和用例级配置继承
- **自定义 Hooks 系统**：
  - 套件、用例和步骤级别的 setup/teardown hooks
  - 请求签名和认证 hooks
  - 自定义验证和数据转换
- **数据库集成**：
  - SQL 响应验证
  - 查询结果存储为变量
  - 支持多数据库连接
- **专业报告**：
  - 详细的 JSON 报告，包含完整请求/响应日志
  
  - 交互式 HTML 报告，支持过滤和搜索
- **安全特性**：
  - 自动敏感数据脱敏
  - 可配置的密钥显示（用于调试）
- **开发者体验**：
  - 快速执行，连接池
  - 重试逻辑，指数退避
  - 丰富的控制台输出，带颜色编码
  - Curl 命令生成，用于调试

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/your-org/apirunner.git
cd apirunner

# 开发模式安装
pip install -e .

# 验证安装
arun --help
```

### 第一个测试

1. **创建环境文件** (`.env`)：
```env
BASE_URL=https://api.example.com
USER_USERNAME=test_user
USER_PASSWORD=test_pass
```

2. **编写测试用例** (`testcases/test_health.yaml`)：
```yaml
config:
  name: 健康检查
  base_url: ${ENV(BASE_URL)}
  tags: [smoke, health]

steps:
  - name: 检查 API 健康状态
    request:
      method: GET
      url: /health
    validate:
      - eq: [status_code, 200]
      - eq: [$.status, "healthy"]
      - contains: [$.data, "version"]
```

3. **运行测试**：
```bash
arun run testcases/test_health.yaml --env-file .env --html reports/report.html
```

4. **查看结果**：
```
Total: 1 Passed: 1 Failed: 0 Skipped: 0 Duration: 145.3ms
HTML report written to reports/report.html
```

## 安装

### 环境要求

- Python 3.10 或更高版本
- pip（Python 包管理器）

### 依赖项

APIRunner 依赖项极少：
- `httpx` (>=0.27) - 现代 HTTP 客户端
- `pydantic` (>=2.6) - 数据验证
- `jmespath` (>=1.0) - JSON 提取
- `PyYAML` (>=6.0) - YAML 解析
- `rich` (>=13.7) - 美观的终端输出
- `typer` (>=0.12) - CLI 框架

### 安装方法

**开发模式安装：**
```bash
git clone https://github.com/your-org/apirunner.git
cd apirunner
pip install -e .
```

**从源码安装：**
```bash
pip install git+https://github.com/your-org/apirunner.git
```

## 使用说明

### 基本命令

**运行测试：**
```bash
# 运行目录中的所有测试
arun run testcases --env-file .env

# 使用标签过滤
arun run testcases -k "smoke and not slow" --env-file .env

# 使用变量覆盖
arun run testcases --vars base_url=http://localhost:8000 --vars debug=true

# 生成所有类型的报告
arun run testcases \
  --env-file .env \
  --report reports/run.json \
  --html reports/report.html \
  --log-level debug
```

**通知功能（可选）：**
```bash
# 仅在失败时发送飞书通知
ARUN_NOTIFY_ONLY=failed FEISHU_WEBHOOK=https://open.feishu.cn/xxx \
python -m apirunner.cli run testcases --env-file .env --notify feishu

# 始终发送邮件通知（附带 HTML 报告）
SMTP_HOST=smtp.example.com SMTP_PORT=465 SMTP_USER=noreply@example.com \
SMTP_PASS=app-pass MAIL_FROM=noreply@example.com MAIL_TO=qa@example.com \
python -m apirunner.cli run testcases --env-file .env --notify email --notify-only always --notify-attach-html
```

环境变量说明：
- `ARUN_NOTIFY`：默认通知渠道（如果未提供 `--notify`），例如 `feishu,email`
- `ARUN_NOTIFY_ONLY`：通知策略，`failed`（默认）或 `always`
- `NOTIFY_TOPN`：包含的失败用例数量（默认 5）

飞书选项：
- `FEISHU_WEBHOOK`（必需）
- `FEISHU_SECRET`（可选）
- `FEISHU_MENTION`（可选，逗号分隔）
- `FEISHU_STYLE`：`text`（默认）或 `card`
- `REPORT_URL`：HTML 报告的公开 URL（用于卡片按钮）

邮件选项：
- `SMTP_HOST`、`SMTP_PORT`、`SMTP_USER`、`SMTP_PASS`
- `MAIL_FROM`、`MAIL_TO`
- `NOTIFY_ATTACH_HTML`：附加 HTML 报告（true/false）
- `NOTIFY_HTML_BODY`：发送 HTML 正文（true/false）
<!-- 自定义通知模板（Jinja2）已移除，仅保留内置摘要通知 -->

**验证 YAML 语法：**
```bash
# 检查 YAML 文件但不运行测试
arun check testcases
```

YAML 风格规范：
- `steps` 中相邻步骤之间保留一行空行，提升可读性
- 如未满足，可使用 `arun fix` 自动修复

**自动修复 YAML 风格：**
```bash
# 将 hooks 迁移到新的基于 config 的格式
arun fix testcases

# 同时会自动修复 steps 之间的空行（如缺失）

# 仅修复空行（不迁移 hooks）
arun fix testcases --only-spacing

# 仅迁移 hooks（不修复空行）
arun fix testcases --only-hooks
```

**合并报告：**
```bash
# 合并多个 JSON 报告
arun report reports/run1.json reports/run2.json -o reports/merged.json
```

### 命令行选项

| 选项 | 描述 |
|------|------|
| `path` | 要运行的文件或目录（必需） |
| `-k EXPR` | 标签过滤表达式（例如 `"smoke and not slow"`） |
| `--vars k=v` | 变量覆盖（可重复） |
| `--failfast` | 首次失败时停止 |
| `--report FILE` | 写入 JSON 报告 |
| `--html FILE` | 写入 HTML 报告 |
| `--log-level LEVEL` | 日志级别（INFO、DEBUG） |
| `--env-file FILE` | 环境文件路径（默认：`.env`） |
| `--log-file FILE` | 日志文件路径（默认：`logs/run-<timestamp>.log`） |
| `--httpx-logs` | 显示 httpx 内部日志 |
| `--mask-secrets` | 在日志/报告中隐藏敏感数据 |

## 使用文档

### DSL 语法参考

#### 测试用例结构

```yaml
config:
  name: 测试用例名称                        # 必需
  base_url: https://api.example.com       # 可选（可使用 ${ENV(BASE_URL)}）
  variables:                              # 可选：用例级变量
    user_id: 12345
    api_key: secret
  headers:                                # 可选：默认请求头
    X-API-Version: "v1"
  timeout: 30.0                           # 可选：请求超时时间（秒）
  verify: true                            # 可选：SSL 验证
  tags: [smoke, regression]               # 可选：用于过滤的标签
  setup_hooks:                            # 可选：用例 setup hooks
    - ${setup_function()}
  teardown_hooks:                         # 可选：用例 teardown hooks
    - ${teardown_function()}

parameters:                               # 可选：参数化
  env: [dev, staging]                     # 矩阵：生成 2 个测试实例
  region: [us, eu]                        # 矩阵：2 x 2 = 4 个实例总计

steps:
  - name: 步骤名称                         # 必需
    variables:                            # 可选：步骤级变量
      custom_id: abc123

    request:                              # 必需
      method: POST                        # 必需：GET、POST、PUT、DELETE 等
      url: /api/users                     # 必需：绝对路径或相对于 base_url
      params:                             # 可选：查询参数
        page: 1
        limit: 10
      headers:                            # 可选：请求头（与 config 合并）
        Content-Type: application/json
      body:                               # 可选：请求体（通常为 JSON）
        username: ${ENV(USER_USERNAME)}
        email: user@example.com
      data:                               # 可选：表单数据
        key: value
      files:                              # 可选：文件上传
        file: /path/to/file.pdf
      auth:                               # 可选：认证
        type: bearer                      # bearer 或 basic
        token: ${ENV(API_TOKEN)}
      timeout: 10.0                       # 可选：请求特定的超时时间
      verify: true                        # 可选：SSL 验证
      allow_redirects: true               # 可选：重定向处理

    extract:                              # 可选：响应提取
      user_id: $.data.user.id            # JMESPath 表达式（必须以 $ 开头）
      token: $.data.access_token         # 存储供后续步骤使用

    validate:                             # 可选：断言
      - eq: [status_code, 200]           # 状态码检查
      - eq: [$.success, true]            # 响应体检查
      - contains: [$.message, "success"] # 子字符串检查
      - regex: [$.email, ".*@.*\\.com"]  # 正则表达式模式
      - lt: [$elapsed_ms, 2000]          # 响应时间检查

    sql_validate:                         # 可选：SQL 验证
      - query: "SELECT status FROM users WHERE id='$user_id'"
        expect:
          - eq: [status, "active"]
        store:                            # 将查询结果存储为变量
          db_status: status

    setup_hooks:                          # 可选：步骤 setup hooks
      - ${sign_request($request)}

    teardown_hooks:                       # 可选：步骤 teardown hooks
      - ${validate_response($response)}

    skip: false                           # 可选：跳过此步骤
    retry: 3                              # 可选：失败时重试次数
    retry_backoff: 0.5                    # 可选：初始退避时间（秒）
```

#### 测试套件结构

```yaml
config:
  name: 测试套件名称
  base_url: ${ENV(BASE_URL)}
  variables:
    suite_var: value
  tags: [integration]
  setup_hooks:                            # 套件级 setup（运行一次）
    - ${suite_setup()}
  teardown_hooks:                         # 套件级 teardown（运行一次）
    - ${suite_teardown()}

cases:
  - config:
      name: 用例 1
      tags: [smoke]
    steps:
      - name: 步骤 1
        request:
          method: GET
          url: /api/endpoint
        validate:
          - eq: [status_code, 200]

  - config:
      name: 用例 2
      tags: [regression]
    steps:
      - name: 步骤 1
        request:
          method: POST
          url: /api/endpoint
        validate:
          - eq: [status_code, 201]
```

### 模板系统

APIRunner 仅支持 Dollar 风格：

#### Dollar 风格

```yaml
# 变量引用
url: /users/$user_id                    # 简单变量

# 函数调用
headers:
  X-Timestamp: ${ts()}                  # 当前时间戳
  X-Signature: ${sign($app_key, ts())} # 自定义函数

# 环境变量
base_url: ${ENV(BASE_URL)}              # 从环境读取

# 复杂表达式
body:
  user_id: ${int($user_id) + 1}        # 算术运算
```


**变量优先级**（从高到低）：
1. CLI 覆盖：`--vars key=value`
2. 步骤级：`steps[].variables`
3. 配置级：`config.variables`
4. 参数：`parameters`
5. 提取：`steps[].extract`
6. 环境：`${ENV(KEY)}`

### 断言（验证器）

| 比较器 | 描述 | 示例 |
|--------|------|------|
| `eq` | 等于 | `- eq: [status_code, 200]` |
| `ne` | 不等于 | `- ne: [$.error, null]` |
| `lt` | 小于 | `- lt: [$elapsed_ms, 1000]` |
| `le` | 小于或等于 | `- le: [$.price, 100]` |
| `gt` | 大于 | `- gt: [$.count, 0]` |
| `ge` | 大于或等于 | `- ge: [$.age, 18]` |
| `contains` | 包含子字符串/元素 | `- contains: [$.message, "success"]` |
| `not_contains` | 不包含 | `- not_contains: [$.errors, "fatal"]` |
| `regex` | 正则匹配 | `- regex: [$.email, ".*@example\\.com"]` |
| `len_eq` | 长度等于 | `- len_eq: [$.items, 10]` |
| `in` | 元素在集合中 | `- in: ["admin", $.roles]` |
| `not_in` | 元素不在集合中 | `- not_in: ["banned", $.statuses]` |

**检查目标：**
- `status_code` - HTTP 状态码
- `headers.Header-Name` - 响应头（不区分大小写）
- `$.path.to.field` - JSON 响应体字段（JMESPath）
- `$[0].id` - 数组元素
- `$elapsed_ms` - 响应时间（毫秒）

### 提取（JMESPath）

从响应中提取数据供后续步骤使用：

```yaml
extract:
  # 提取单个字段
  user_id: $.data.user.id

  # 从数组提取
  first_item: $[0].name

  # 提取嵌套字段
  access_token: $.data.auth.access_token

  # 提取响应头
  rate_limit: $headers.X-RateLimit-Remaining

  # 提取状态码
  status: $status_code
```

提取的变量自动在所有后续步骤中可用。

### 参数化

使用多个输入组合运行相同的测试：

#### 枚举（字典列表）

```yaml
parameters:
  - {username: alice, role: admin}
  - {username: bob, role: user}
  - {username: charlie, role: guest}

# 生成 3 个测试实例
```

#### 矩阵（笛卡尔积）

```yaml
parameters:
  env: [dev, staging, prod]
  region: [us, eu, asia]

# 生成 3 × 3 = 9 个测试实例
```

#### 压缩（并行数组）

```yaml
parameters:
  - username-password:
      - [alice, pass123]
      - [bob, secret456]
      - [charlie, pwd789]

# 生成 3 个测试实例，值成对出现
```

### Hooks 系统

Hooks 是在测试生命周期特定点运行的 Python 函数。

#### Hook 类型

1. **套件 Hooks**（在 `config.setup_hooks` / `config.teardown_hooks` 中）
2. **用例 Hooks**（在 `config.setup_hooks` / `config.teardown_hooks` 中）
3. **步骤 Hooks**（在 `steps[].setup_hooks` / `steps[].teardown_hooks` 中）

#### 创建自定义 Hooks

在项目根目录创建 `arun_hooks.py`：

```python
import time
import hashlib
import hmac

def ts() -> int:
    """返回当前 Unix 时间戳"""
    return int(time.time())

def md5(s: str) -> str:
    """计算 MD5 哈希"""
    return hashlib.md5(s.encode()).hexdigest()

def setup_hook_sign_request(request: dict, variables: dict, env: dict) -> dict:
    """
    Setup hook：使用 HMAC-SHA256 签名请求

    Args:
        request: 请求字典（可变，可原地修改）
        variables: 当前变量字典
        env: 环境变量字典

    Returns:
        要注入的新变量字典（或 None）
    """
    secret = env.get('APP_SECRET', '').encode()
    method = request.get('method', 'GET')
    url = request.get('url', '')
    timestamp = str(ts())

    # 计算签名
    raw = f"{method}|{url}|{timestamp}".encode()
    sig = hmac.new(secret, raw, hashlib.sha256).hexdigest()

    # 修改请求头
    headers = request.setdefault('headers', {})
    headers['X-Timestamp'] = timestamp
    headers['X-Signature'] = sig

    # 返回新变量
    return {'last_signature': sig, 'last_timestamp': timestamp}

def teardown_hook_assert_status_ok(response: dict, variables: dict, env: dict) -> None:
    """
    Teardown hook：验证响应状态为 200

    Args:
        response: 响应字典，包含 status_code、headers、body 等
        variables: 当前变量字典
        env: 环境变量字典

    Returns:
        None（或新变量字典）

    Raises:
        AssertionError: 如果状态码不是 200
    """
    if response.get('status_code') != 200:
        raise AssertionError(f"Expected 200, got {response.get('status_code')}")
```

#### 在 YAML 中使用 Hooks

```yaml
config:
  name: 签名请求测试
  base_url: ${ENV(BASE_URL)}
  setup_hooks:
    - ${setup_hook_sign_request($request)}

steps:
  - name: 发起签名请求
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

**Hook 上下文变量：**
- `$request` / `$step_request` - 请求字典
- `$response` / `$step_response` - 响应字典
- `$step_name` - 当前步骤名称
- `$step_variables` - 步骤级变量
- `$session_variables` - 所有会话变量
- `$session_env` - 环境变量

### SQL 验证

根据数据库状态验证 API 响应：

#### 设置

安装数据库驱动：
```bash
pip install pymysql  # 用于 MySQL/MariaDB
```

在 `.env` 中配置连接：
```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=test_user
MYSQL_PASSWORD=test_pass
MYSQL_DB=test_db

# 或使用 DSN
MYSQL_DSN=mysql://user:pass@localhost:3306/test_db
```

#### 使用

```yaml
steps:
  - name: 创建订单
    request:
      method: POST
      url: /api/orders
      body:
        sku: "PRODUCT-123"
        quantity: 2
    extract:
      order_id: $.data.order_id

    sql_validate:
      # 查询 1：验证订单状态
      - query: "SELECT status, total FROM orders WHERE id='$order_id'"
        expect:
          - eq: [status, "pending"]
          - gt: [total, 0]
        store:                         # 将结果存储为变量
          db_status: status
          db_total: total

      # 查询 2：验证订单项
      - query: "SELECT COUNT(*) AS cnt FROM order_items WHERE order_id='$order_id'"
        expect:
          - ge: [cnt, 1]
        allow_empty: false             # 如果查询返回无行则失败

      # 查询 3：覆盖 DSN 用于不同数据库
      - query: "SELECT audit_log FROM audit_db.logs WHERE order_id='$order_id'"
        dsn: mysql://user:pass@audit-host:3306/audit_db
        expect:
          - contains: [audit_log, "order_created"]
```

**SQL 验证选项：**
- `query` - SQL 查询（必需，支持变量插值）
- `expect` - 对查询结果的断言（可选）
- `store` - 将列值存储为变量（可选）
- `allow_empty` / `optional` - 允许空结果集（默认：false）
- `dsn` - 覆盖数据库连接（可选）

### 标签过滤

使用逻辑标签表达式过滤测试执行：

```bash
# 运行带有 'smoke' 标签的测试
arun run testcases -k "smoke"

# 运行同时带有 'smoke' 和 'regression' 标签的测试
arun run testcases -k "smoke and regression"

# 运行带有 'smoke' 或 'p0' 标签的测试
arun run testcases -k "smoke or p0"

# 运行除 'slow' 之外的所有测试
arun run testcases -k "not slow"

# 复杂表达式
arun run testcases -k "(smoke or regression) and not slow and not flaky"
```

**标签表达式语法：**
- `and` - 逻辑与（优先级更高）
- `or` - 逻辑或
- `not` - 逻辑非
- `( )` - 分组（从左到右求值）
- 不区分大小写匹配

### 自动注入功能

#### Bearer Token 自动注入

当提取名为 `token` 的变量时，APIRunner 会在后续请求中自动注入 `Authorization: Bearer {token}` 头（除非显式覆盖）：

```yaml
steps:
  - name: 登录
    request:
      method: POST
      url: /api/auth/login
      body:
        username: ${ENV(USER_USERNAME)}
        password: ${ENV(USER_PASSWORD)}
    extract:
      token: $.data.access_token        # 提取 token
    validate:
      - eq: [status_code, 200]

  - name: 获取用户资料
    request:
      method: GET
      url: /api/users/me
      # 无需手动设置 Authorization 头！
      # APIRunner 自动添加：Authorization: Bearer {token}
    validate:
      - eq: [status_code, 200]
```

### 重试和退避

为不稳定的端点配置自动重试：

```yaml
steps:
  - name: 不稳定的端点
    request:
      method: GET
      url: /api/sometimes-fails
    retry: 3                            # 最多重试 3 次
    retry_backoff: 0.5                  # 初始退避：0.5 秒
                                        # 指数退避：0.5s、1.0s、2.0s（最大值）
    validate:
      - eq: [status_code, 200]
```

## 架构

### 项目结构

```
apirunner/
├── apirunner/              # 核心包
│   ├── cli.py             # CLI 入口点
│   ├── engine/            # HTTP 客户端
│   │   └── http.py
│   ├── loader/            # YAML 解析和发现
│   │   ├── collector.py   # 测试文件发现
│   │   ├── yaml_loader.py # YAML 解析
│   │   ├── hooks.py       # Hook 加载
│   │   └── env.py         # 环境加载
│   ├── runner/            # 测试执行
│   │   ├── runner.py      # 主运行器
│   │   ├── assertions.py  # 断言逻辑
│   │   └── extractors.py  # JMESPath 提取
│   ├── templating/        # 模板引擎
│   │   ├── engine.py      # 双语法渲染
│   │   ├── context.py     # 变量作用域
│   │   └── builtins.py    # 内置函数
│   ├── models/            # Pydantic 模型
│   │   ├── case.py        # Case 和 Suite 模型
│   │   ├── step.py        # Step 模型
│   │   ├── config.py      # Config 模型
│   │   └── report.py      # Report 模型
│   ├── reporter/          # 报告生成
│   │   ├── json_reporter.py
│   │   ├── (已移除) junit_reporter.py
│   │   ├── html_reporter.py
│   │   └── merge.py
│   ├── db/                # 数据库支持
│   │   └── sql_validate.py
│   └── utils/             # 工具
│       ├── logging.py     # Rich 日志
│       ├── mask.py        # 秘密脱敏
│       └── curl.py        # Curl 生成
├── testcases/             # 测试用例文件
├── testsuites/            # 测试套件文件
├── examples/              # 示例测试
├── arun_hooks.py          # 自定义 hook 函数
├── .env                   # 环境变量
└── reports/               # 生成的报告
```

### 执行流程

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CLI (cli.py)                                             │
│    ├─ 解析参数                                              │
│    ├─ 加载环境（.env、--env-file、--vars）                 │
│    └─ 发现测试文件（collector.py）                         │
└────────────────────┬────────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Loader (loader/)                                         │
│    ├─ 解析 YAML（yaml_loader.py）                          │
│    ├─ 验证模型（models/）                                  │
│    ├─ 展开参数（枚举/矩阵/压缩）                           │
│    ├─ 加载自定义 hooks（hooks.py → arun_hooks.py）         │
│    └─ 应用标签过滤                                         │
└────────────────────┬────────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Runner (runner/runner.py)                               │
│    ├─ 初始化 VarContext（变量作用域）                      │
│    ├─ 执行套件/用例 setup hooks                            │
│    │                                                        │
│    └─ 对每个步骤：                                         │
│        ├─ 将步骤变量推入上下文                             │
│        ├─ 渲染模板（templating/engine.py）                 │
│        ├─ 执行 setup hooks                                 │
│        ├─ 发送 HTTP 请求（engine/http.py）                 │
│        ├─ 提取变量（extractors.py）                        │
│        ├─ 运行断言（assertions.py）                        │
│        ├─ 执行 SQL 验证（db/sql_validate.py）              │
│        ├─ 执行 teardown hooks                              │
│        └─ 弹出步骤上下文                                   │
│                                                             │
│    ├─ 执行套件/用例 teardown hooks                         │
│    └─ 构建用例结果                                         │
└────────────────────┬────────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Reporters (reporter/)                                    │
│    ├─ 聚合结果                                             │
│    ├─ 生成 JSON 报告（json_reporter.py）                   │
│    ├─ （已移除）生成 JUnit XML                             │
│    ├─ 生成 HTML 报告（html_reporter.py）                   │
│    └─ 写入日志（utils/logging.py）                         │
└─────────────────────────────────────────────────────────────┘
```

### 关键设计决策

1. **Dollar 模板**：仅支持 `${...}` 表达式，语法简单明确
2. **不可变作用域**：变量上下文使用基于堆栈的方法，在步骤之间实现干净隔离
3. **类型保留**：单 token 模板 (`${var}`) 保留原生类型（int、bool 等），而不是字符串化
4. **Hook 签名**：灵活的 hook 签名允许函数仅声明所需的参数
5. **快速失败选项**：`--failfast` 在首次失败时停止执行，以获得快速反馈
6. **秘密脱敏**：自动脱敏敏感字段（可使用 `--reveal-secrets` 配置）

## 示例

### 示例 1：登录流程与 Token 自动注入

```yaml
config:
  name: 登录并访问受保护资源
  base_url: ${ENV(BASE_URL)}
  variables:
    username: ${ENV(USER_USERNAME)}
    password: ${ENV(USER_PASSWORD)}

steps:
  - name: 用户登录
    request:
      method: POST
      url: /api/v1/auth/login
      body:
        username: $username
        password: $password
    extract:
      token: $.data.access_token
      user_id: $.data.user.id
    validate:
      - eq: [status_code, 200]
      - eq: [$.success, true]
      - eq: [$.message, "登录成功"]

  - name: 获取用户资料
    request:
      method: GET
      url: /api/v1/users/me
      # Authorization: Bearer {token} 自动注入
    validate:
      - eq: [status_code, 200]
      - eq: [$.data.user.id, var:user_id]
```

### 示例 2：参数化测试

```yaml
config:
  name: 多环境健康检查
  tags: [smoke, health]

parameters:
  env: [dev, staging, prod]
  region: [us, eu]

steps:
  - name: 检查健康端点
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

### 示例 3：使用 Hooks 进行请求签名

**arun_hooks.py：**
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

**test_signed_request.yaml：**
```yaml
config:
  name: 签名 API 请求
  base_url: ${ENV(BASE_URL)}

steps:
  - name: 发起签名请求
    setup_hooks:
      - ${setup_hook_hmac_sign($request)}
    request:
      method: GET
      url: /api/secure/data
    validate:
      - eq: [status_code, 200]
      - eq: [$.authenticated, true]
```

### 示例 4：SQL 验证

```yaml
config:
  name: 订单创建与数据库验证
  base_url: ${ENV(BASE_URL)}

steps:
  - name: 创建订单
    request:
      method: POST
      url: /api/orders
      body:
        product_id: "PROD-001"
        quantity: 5
        shipping_address: "上海市黄浦区XX路123号"
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

### 示例 5：带继承的测试套件

```yaml
config:
  name: 用户管理测试套件
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
      name: 用户注册
      tags: [registration]
    steps:
      - name: 注册新用户
        request:
          method: POST
          url: /api/$api_version/users/register
          body:
            username: test_user_${short_uid(8)}
            email: test_${short_uid()}@example.com
            password: SecurePass123!
        extract:
          user_id: $.data.user.id
        validate:
          - eq: [status_code, 201]
          - eq: [$.success, true]

  - config:
      name: 用户登录
      tags: [auth]
    steps:
      - name: 使用凭据登录
        request:
          method: POST
          url: /api/$api_version/auth/login
          body:
            username: ${ENV(USER_USERNAME)}
            password: ${ENV(USER_PASSWORD)}
        extract:
          token: $.data.access_token
        validate:
          - eq: [status_code, 200]
          - eq: [$.success, true]
```

### 更多示例

查看 `examples/` 目录获取更多示例：
- `test_params_matrix.yaml` - 矩阵参数化
- `test_params_enumerate.yaml` - 枚举参数化
- `test_assertions_showcase.yaml` - 所有断言类型
- `test_perf_timing.yaml` - 性能断言
- `test_skip_and_retry.yaml` - 跳过和重试逻辑
- `test_negative_auth.yaml` - 负面测试用例
- `suite_hooks.yaml` - 套件级 hooks
- 以及更多...

运行所有示例：
```bash
arun run examples --env-file .env --html reports/examples.html
```

## 环境配置

### 环境文件格式

**.env（KEY=VALUE 格式）：**
```env
# API 配置
BASE_URL=https://api.example.com
API_VERSION=v1

# 认证
USER_USERNAME=test_user
USER_PASSWORD=test_password
API_KEY=your-api-key-here
APP_SECRET=your-hmac-secret

# 数据库（用于 SQL 验证）
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=db_user
MYSQL_PASSWORD=db_password
MYSQL_DB=test_database

# 或使用 DSN
MYSQL_DSN=mysql://user:pass@localhost:3306/test_db

# 功能标志
ENABLE_RETRY=true
MAX_RETRY_COUNT=3
```

**YAML 中的环境变量：**
```yaml
config:
  base_url: ${ENV(BASE_URL)}      # 从环境读取
  variables:
    api_key: ${ENV(API_KEY)}      # 注入到变量中
    version: ${ENV(API_VERSION, v1)}  # 带默认值
```

### 变量优先级

当同一变量在多个地方定义时：

1. **CLI 覆盖** (`--vars key=value`) - 最高优先级
2. **步骤变量** (`steps[].variables`)
3. **配置变量** (`config.variables`)
4. **参数** (`parameters`)
5. **提取的变量** (`steps[].extract`)
6. **环境** (`${ENV(KEY)}`) - 最低优先级

## 报告

### JSON 报告

结构化 JSON 输出，包含完整的请求/响应详情：

```bash
arun run testcases --report reports/run.json
```

**示例输出：**
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
      "name": "健康检查",
      "status": "passed",
      "duration_ms": 145.3,
      "parameters": {},
      "steps": [
        {
          "name": "检查 API 健康状态",
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

<!-- JUnit XML 报告功能已移除 -->

### HTML 报告

带搜索和过滤的交互式 HTML 报告：

```bash
arun run testcases --html reports/report.html
```

功能：
- 带通过/失败统计的摘要仪表板
- 可展开的测试用例详情
- 请求/响应检查
- 带差异视图的断言结果
- 搜索和过滤功能
- 响应式设计

### 报告合并

合并多个测试运行：

```bash
# 并行任务运行测试
arun run testcases/smoke --report reports/smoke.json
arun run testcases/regression --report reports/regression.json

# 合并报告
arun report reports/smoke.json reports/regression.json -o reports/merged.json
```

## 高级主题

### 测试文件发现

APIRunner 使用以下规则发现测试文件：

1. **基于目录**：位于 `testcases/` 或 `testsuites/` 目录中的文件
2. **基于名称**：匹配 `test_*.yaml`（用例）或 `suite_*.yaml`（套件）的文件

**自定义 hooks 文件发现：**
- 从测试文件向上搜索 `arun_hooks.py`
- 可通过 `ARUN_HOOKS_FILE` 环境变量配置

```bash
# 使用自定义 hooks 文件
ARUN_HOOKS_FILE=custom_hooks.py arun run testcases
```

### 敏感数据处理

**自动脱敏**（默认）：
```bash
arun run testcases --env-file .env  # 日志/报告中脱敏密钥
```

**为调试显示密钥：**
```bash
arun run testcases --env-file .env --reveal-secrets
```

脱敏字段：
- `Authorization` 头
- `password` 字段
- `*token*` 字段（access_token、refresh_token 等）
- `*secret*` 字段
- `*key*` 字段（api_key 等）

### 性能测试

对响应时间进行断言：

```yaml
steps:
  - name: 性能关键端点
    request:
      method: GET
      url: /api/data
    validate:
      - eq: [status_code, 200]
      - lt: [$elapsed_ms, 500]    # 必须在 500ms 内响应
```

### 调试

**启用调试日志：**
```bash
arun run testcases --log-level debug --log-file debug.log
```

**显示 httpx 内部日志：**
```bash
arun run testcases --httpx-logs
```

**生成 curl 命令：**
调试日志自动包含所有请求的 curl 等效命令：
```
[DEBUG] cURL: curl -X POST 'https://api.example.com/login' -H 'Content-Type: application/json' -d '{"username":"test","password":"***"}'
```

## CI/CD 集成

### GitHub Actions

```yaml
name: API 测试

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: 设置 Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: 安装依赖
        run: |
          pip install -e .

      - name: 运行 API 测试
        env:
          BASE_URL: ${{ secrets.API_BASE_URL }}
          USER_USERNAME: ${{ secrets.TEST_USERNAME }}
          USER_PASSWORD: ${{ secrets.TEST_PASSWORD }}
        run: |
          arun run testcases \
            --junit reports/junit.xml \
            --html reports/report.html \
            --mask-secrets

      - name: 发布测试结果
        uses: EnricoMi/publish-unit-test-result-action@v2
        if: always()
        with:
          files: reports/junit.xml

      - name: 上传 HTML 报告
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
        stage('设置') {
            steps {
                sh 'pip install -e .'
            }
        }

        stage('测试') {
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
                reportName: 'API 测试报告'
            ])
        }
    }
}
```

## 开发

### 设置开发环境

```bash
# 克隆仓库
git clone https://github.com/your-org/apirunner.git
cd apirunner

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows：venv\Scripts\activate

# 以可编辑模式安装，包括开发依赖
pip install -e .

# 验证安装
arun --help
```

### 运行测试

```bash
# 运行所有测试
arun run testcases --env-file .env

# 运行特定标签
arun run testcases -k "smoke" --env-file .env

# 运行并生成完整报告
arun run testcases \
  --env-file .env \
  --report reports/run.json \
  --junit reports/junit.xml \
  --html reports/report.html \
  --log-level debug
```

### 代码风格

本项目使用：
- `black` 用于代码格式化
- `ruff` 用于代码检查
- `mypy` 用于类型检查

### Git Hooks

在提交时自动修复 YAML 格式：

```bash
# 使 pre-commit hook 可执行
chmod +x scripts/pre-commit-fix-hooks.sh

# 安装 hook
ln -sf ../../scripts/pre-commit-fix-hooks.sh .git/hooks/pre-commit
```

这会自动运行 `arun fix` 将 hooks 迁移到新的基于 config 的格式。

## 说明

APIRunner 专注于最小化核心和实用功能，用于日常 API 测试，没有额外的臃肿。

## 故障排查

### 常见问题

**问题：`ModuleNotFoundError: No module named 'apirunner'`**
```bash
# 解决方案：以可编辑模式安装
pip install -e .
```

**问题：`No YAML test files found`**
```bash
# 解决方案：确保文件遵循命名约定
# - 位于 testcases/ 或 testsuites/ 目录中，或
# - 命名为 test_*.yaml 或 suite_*.yaml
```

**问题：`Invalid check 'body.field': use '$' syntax`**
```bash
# 旧语法（已弃用）：
validate:
  - eq: [body.user.id, 123]

# 新语法（必需）：
validate:
  - eq: [$.user.id, 123]
```

**问题：Hooks 未加载**
```bash
# 确保 arun_hooks.py 在项目根目录或父目录中
# 或显式指定：
ARUN_HOOKS_FILE=path/to/hooks.py arun run testcases
```

**问题：SQL 验证失败，连接错误**
```bash
# 安装数据库驱动
pip install pymysql  # 用于 MySQL

# 验证环境变量
echo $MYSQL_HOST $MYSQL_USER $MYSQL_DB

# 或使用 DSN
export MYSQL_DSN=mysql://user:pass@host:3306/db
```

## 贡献

我们欢迎贡献！以下是入门方法：

1. **Fork 仓库**
2. **创建功能分支**：`git checkout -b feature/your-feature`
3. **进行更改**
4. **运行测试**：`arun run testcases --env-file .env`
5. **提交**：`git commit -m "feat: add amazing feature"`
6. **推送**：`git push origin feature/your-feature`
7. **打开 Pull Request**

### 贡献指南

- 遵循现有代码风格（black、ruff）
- 为新功能添加测试
- 更新文档
- 编写清晰的提交消息
- 保持更改集中和原子化

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 致谢

- 使用 [httpx](https://www.python-httpx.org/)、[pydantic](https://pydantic-docs.helpmanual.io/)、[rich](https://rich.readthedocs.io/) 构建
- 感谢所有贡献者

## 支持

- **文档**：详细技术文档见 [CLAUDE.md](CLAUDE.md)
- **示例**：查看 `examples/` 目录获取示例测试
- **问题**：在 [GitHub Issues](https://github.com/your-org/apirunner/issues) 上报告 bug 和请求功能

---

<div align="center">

**由 APIRunner 团队用 ❤️ 构建**

[⬆ 回到顶部](#apirunner)

</div>
