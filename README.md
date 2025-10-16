# ARun

<div align="center">

**零代码 HTTP API 测试框架 · 基于 YAML DSL · 5 分钟上手**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-orange)]()

[快速开始](#-快速开始-5-分钟) • [核心特性](#-核心特性) • [文档](#-核心概念) • [示例](#-实战示例)

</div>

---

## 📖 项目简介

ARun 是一个**极简、强大、生产就绪**的 HTTP API 测试框架。使用清晰的 YAML 语法编写测试用例，无需编写代码，5 分钟即可完成第一个测试。

```yaml
# 就是这么简单！
config:
  name: 健康检查
  base_url: ${ENV(BASE_URL)}

steps:
  - name: 检查 API 状态
    request:
      method: GET
      url: /health
    validate:
      - eq: [status_code, 200]
      - eq: [$.data.status, "healthy"]
```

### 💡 为什么选择 ARun？

| 特性 | ARun | 其他工具 |
|------|-----------|----------|
| **零代码** | ✅ 纯 YAML，无需编程 | ❌ 需要 Python/JavaScript 代码 |
| **学习曲线** | ✅ 5 分钟上手 | ⚠️ 需要学习测试框架 |
| **模板系统** | ✅ 简洁的 `${expr}` 语法 | ⚠️ 复杂的模板引擎 |
| **格式转换** | ✅ curl/Postman/HAR 互转 | ❌ 需要手动编写或第三方工具 |
| **数据库验证** | ✅ 内置 SQL 断言 | ❌ 需要额外开发 |
| **CI/CD 就绪** | ✅ 开箱即用 | ⚠️ 需要配置 |
| **报告系统** | ✅ HTML + JSON + 通知 | ⚠️ 需要集成第三方 |

### 🎯 适用场景

- ✅ **接口测试**：REST API、微服务接口验证
- ✅ **E2E 测试**：完整业务流程测试
- ✅ **冒烟测试**：快速验证服务可用性
- ✅ **回归测试**：CI/CD 流水线集成
- ✅ **性能监控**：响应时间断言

---

## ⚡ 核心特性

### 🔥 开箱即用

- **零配置启动**：`pip install -e . && arun run testcases`
- **YAML DSL**：声明式测试用例，人类可读
- **智能变量管理**：6 层作用域，自动 token 注入
- **JMESPath 提取**：强大的 JSON 数据提取能力
- **格式转换**：curl/Postman/HAR ↔ YAML 互转，支持 `--split-output` 单步导出

### 🚀 高级功能

- **Hooks 系统**：Suite/Case/Step 三级生命周期钩子，支持请求签名、数据准备
- **SQL 验证**：内置 MySQL 支持，查询结果断言和变量存储
- **参数化测试**：矩阵、枚举、压缩三种模式，轻松生成测试组合
- **重试机制**：指数退避，容错不稳定接口

### 📊 企业级特性

- **专业报告**：
  - 交互式 HTML 报告（一键复制 JSON/cURL，ES5 兼容，支持旧浏览器和 file:// 协议）
  - 结构化 JSON 报告（CI/CD 集成）
  - Allure 集成（趋势分析、附件丰富）
- **通知集成**：飞书卡片/文本、钉钉文本/Markdown、邮件 HTML/附件，失败聚合通知
- **安全保护**：敏感数据自动脱敏（headers/body/环境变量），支持 `--mask-secrets` 选项
- **调试友好**：
  - Rich 彩色输出
  - cURL 命令生成（使用 `--data-raw`，JSON 自动格式化，自动 Content-Type）
  - 详细日志（支持 `--log-level debug` 和 `--httpx-logs`）
  - 错误步骤详情定位

---

## 🚀 快速开始 (5 分钟)

### 1. 安装

```bash
# 克隆项目
git clone https://github.com/Devliang24/arun.git
cd arun

# 安装（开发模式）
pip install -e .

# 验证安装
arun --help
```

### 2. 配置环境

创建 `.env` 文件：

```env
BASE_URL=https://api.example.com
USER_USERNAME=test_user
USER_PASSWORD=test_pass
# 可选：某些测试可能需要以下变量
# SHIPPING_ADDRESS=1 Test Road, Test City
# API_KEY=demo-api-key
# APP_SECRET=demo-app-secret
```

### 3. 编写第一个测试

创建 `testcases/test_hello.yaml`：

```yaml
config:
  name: 我的第一个测试
  base_url: ${ENV(BASE_URL)}
  tags: [smoke]

steps:
  - name: 健康检查
    request:
      method: GET
      url: /health
    validate:
      - eq: [status_code, 200]
      - eq: [$.success, true]
```

### 4. 运行测试

```bash
# 运行测试
arun run testcases/test_hello.yaml --env-file .env

# 生成 HTML 报告
arun run testcases --html reports/report.html --env-file .env

# 使用标签过滤
arun run testcases -k "smoke" --env-file .env
```

### 5. 查看结果

```
Filter expression: None
[RUN] Discovered files: 1 | Matched cases: 1 | Failfast=False
[CASE] Start: 我的第一个测试 | params={}
[CASE] Result: 我的第一个测试 | status=passed | duration=145.3ms
Total: 1 Passed: 1 Failed: 0 Skipped: 0 Duration: 145.3ms
HTML report written to reports/report.html
```

🎉 **恭喜！**你已经完成了第一个 API 测试。打开 `reports/report.html` 查看详细报告。

---

## 📚 核心概念

### 测试用例结构

一个测试用例 (Case) 包含配置和步骤：

```yaml
config:                              # 配置块
  name: 测试用例名称                  # 必需
  base_url: https://api.example.com  # 基础 URL
  variables:                         # 用例级变量
    api_key: my-key
  tags: [smoke, p0]                  # 标签（用于过滤）

steps:                               # 测试步骤列表
  - name: 步骤 1                      # 步骤名称
    request:                         # HTTP 请求定义
      method: GET                    # HTTP 方法
      url: /api/users                # 路径（相对于 base_url）
    validate:                        # 断言列表
      - eq: [status_code, 200]       # 状态码断言
```

### Dollar 模板语法

ARun 使用简洁的 **Dollar 表达式** `${...}` 进行变量插值和函数调用：

```yaml
# 1. 简单变量引用
url: /users/$user_id                 # 等同于 /users/123

# 2. 函数调用（花括号）
headers:
  X-Timestamp: ${ts()}               # 调用自定义函数（需在 arun_hooks.py 中定义）
  X-Signature: ${md5($api_key)}      # 函数嵌套、参数可以是变量

# 3. 环境变量读取
base_url: ${ENV(BASE_URL)}           # 读取环境变量（必需）
api_key: ${ENV(API_KEY, default)}    # 带默认值（可选参数）

# 4. 算术运算
body:
  user_id: ${int($user_id) + 1}      # 支持基本运算（类型转换 + 计算）
  total: ${float($price) * $quantity}
```

> **提示**：`$var` 是 `${var}` 的简写形式，两者完全等价。复杂表达式必须使用 `${...}` 格式。

### 变量作用域优先级

变量查找顺序（**从高到低**）：

```
1. CLI 覆盖      --vars key=value (最高优先级)
2. 步骤变量      steps[].variables (当前步骤内有效)
3. 配置变量      config.variables (用例级全局)
4. 参数变量      parameters (参数化测试时注入)
5. 提取变量      steps[].extract (从当前步骤响应提取，存入会话供后续步骤使用)
```

> **注意**：`${ENV(KEY)}` 用于读取操作系统环境变量，不属于变量作用域的一部分，而是模板引擎的内置函数。

示例：

```yaml
config:
  variables:
    user_id: 100        # 优先级 3：配置变量（用例级全局）

parameters:
  user_id: [1, 2]       # 优先级 4：参数变量会被配置变量覆盖

steps:
  - name: 登录
    request:
      url: /api/login
    extract:
      user_id: $.data.id  # 优先级 5：从响应提取，存入会话
                          # 提取后对本步骤及后续所有步骤可见

  - name: 创建订单
    request:
      url: /api/orders/$user_id  # 使用提取的 user_id（来自登录响应）

  - name: 查看订单详情
    variables:
      user_id: 999      # 优先级 2：步骤变量（仅当前步骤内最高）
    request:
      url: /api/users/$user_id  # 使用 999（步骤变量覆盖提取变量）
```

---

## 🔧 常用功能

### 断言和验证

支持丰富的断言器：

| 断言器 | 说明 | 示例 |
|--------|------|------|
| `eq` | 等于 | `- eq: [status_code, 200]` |
| `ne` | 不等于 | `- ne: [$.error, null]` |
| `lt` / `le` | 小于 / 小于等于 | `- lt: [$elapsed_ms, 1000]` |
| `gt` / `ge` | 大于 / 大于等于 | `- gt: [$.count, 0]` |
| `contains` | 包含子串/元素 | `- contains: [$.message, "success"]` |
| `not_contains` | 不包含 | `- not_contains: [$.errors, "fatal"]` |
| `regex` | 正则匹配 | `- regex: [$.email, ".*@example\\.com"]` |
| `len_eq` | 长度等于 | `- len_eq: [$.items, 10]` |
| `in` | 元素在集合中 | `- in: ["admin", $.roles]` |

**检查目标**：

```yaml
validate:
  - eq: [status_code, 200]            # 状态码
  - eq: [headers.Content-Type, "application/json"]  # 响应头
  - eq: [$.data.user.id, 123]         # 响应体（JMESPath）
  - lt: [$elapsed_ms, 500]            # 响应时间（毫秒）
```

### 数据提取 (JMESPath)

从响应中提取数据供后续步骤使用：

```yaml
steps:
  - name: 登录
    request:
      method: POST
      url: /api/auth/login
      body:
        username: admin
        password: pass123
    extract:
      token: $.data.access_token      # 提取 token
      user_id: $.data.user.id          # 提取用户 ID
      role: $.data.user.role           # 提取角色
    validate:
      - eq: [status_code, 200]

  - name: 获取用户信息
    request:
      method: GET
      url: /api/users/$user_id         # 使用提取的 user_id
      headers:
        Authorization: Bearer $token    # 使用提取的 token
    validate:
      - eq: [$.data.role, $role]       # 使用提取的 role
```

**常用 JMESPath 模式**：

```yaml
extract:
  # 基础路径
  user_id: $.data.user.id              # 嵌套对象
  first_name: $[0].name                # 数组第一个元素

  # 数组操作
  all_ids: $.data.items[*].id          # 所有 ID
  first_id: $.data.items[0].id         # 第一个 ID

  # 响应元数据
  content_type: $headers.Content-Type   # 响应头
  status: $status_code                  # 状态码
```

### Token 自动注入

提取名为 `token` 的变量后，后续请求自动添加 `Authorization: Bearer {token}` 头：

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

  - name: 访问受保护资源
    request:
      method: GET
      url: /api/users/me
      # 无需手动设置 Authorization 头，自动注入！
    validate:
      - eq: [status_code, 200]
```

> **注意**：如果步骤显式设置了 `Authorization` 头，则不会自动注入。

### 标签过滤

使用逻辑表达式过滤要运行的测试：

```bash
# 运行 smoke 测试
arun run testcases -k "smoke"

# 同时包含两个标签
arun run testcases -k "smoke and regression"

# 任一标签匹配
arun run testcases -k "smoke or p0"

# 排除慢速测试
arun run testcases -k "not slow"

# 复杂表达式
arun run testcases -k "(smoke or regression) and not slow and not flaky"
```

**标签定义**：

```yaml
config:
  name: 用户登录测试
  tags: [smoke, auth, p0]    # 定义多个标签
```

想快速查看项目中已有的标签，可使用 CLI：

```bash
arun tags              # 扫描默认的 testcases 目录
arun tags testsuites   # 指定其它目录
```

---

## 🎨 高级功能

### Hooks 系统

Hooks 允许在测试生命周期的不同阶段执行自定义 Python 函数。

> **提示**：项目根目录已提供 `arun_hooks.py` 示例文件，包含常用的模板辅助函数（如 `ts()`、`md5()`、`uid()`）和生命周期 Hooks（如 `setup_hook_sign_request`），可直接使用。

**函数分类**：
- **模板辅助函数**：在 `${}` 表达式中调用，用于数据生成、格式化等（如 `${ts()}`、`${md5($key)}`）
- **生命周期 Hooks**：在 `setup_hooks/teardown_hooks` 中使用，用于请求前处理、响应后验证（如 `${setup_hook_sign_request($request)}`）

#### Hook 类型

```yaml
# Suite 级别（在 suite 配置中）
config:
  setup_hooks:              # Suite 开始前执行
    - ${suite_setup()}
  teardown_hooks:           # Suite 结束后执行
    - ${suite_teardown()}

# Case 级别（在 case 配置中）
config:
  setup_hooks:              # Case 开始前执行
    - ${case_setup()}
  teardown_hooks:           # Case 结束后执行
    - ${case_cleanup()}

# Step 级别（在步骤中）
steps:
  - name: 发送请求
    setup_hooks:            # 步骤开始前执行
      - ${setup_hook_sign_request($request)}
    teardown_hooks:         # 步骤结束后执行
      - ${teardown_hook_validate($response)}
```

#### 自定义 Hooks

在项目根目录创建 `arun_hooks.py`：

```python
import time
import hmac
import hashlib

def ts() -> int:
    """返回当前 Unix 时间戳"""
    return int(time.time())

def setup_hook_sign_request(request: dict, variables: dict = None, env: dict = None) -> dict:
    """请求签名 Hook：添加时间戳和 HMAC 签名"""
    secret = env.get('APP_SECRET', '').encode()
    method = request.get('method', 'GET')
    url = request.get('url', '')
    timestamp = str(ts())

    # 计算 HMAC 签名
    message = f"{method}|{url}|{timestamp}".encode()
    signature = hmac.new(secret, message, hashlib.sha256).hexdigest()

    # 添加签名头
    headers = request.setdefault('headers', {})
    headers['X-Timestamp'] = timestamp
    headers['X-Signature'] = signature

    # 返回新变量（可选）
    return {'last_signature': signature}

def teardown_hook_validate(response: dict, variables: dict = None, env: dict = None):
    """响应验证 Hook：确保状态码为 200"""
    if response.get('status_code') != 200:
        raise AssertionError(f"Expected 200, got {response.get('status_code')}")
```

**Hook 上下文变量**：

- `$request` - 当前请求对象
- `$response` - 当前响应对象
- `$step_name` - 当前步骤名称
- `$session_variables` - 所有会话变量
- `$session_env` - 环境变量

#### 使用 Hooks

```yaml
config:
  name: 签名 API 测试
  base_url: ${ENV(BASE_URL)}
  setup_hooks:
    - ${setup_hook_sign_request($request)}

steps:
  - name: 获取用户信息
    request:
      method: GET
      url: /api/secure/users
    teardown_hooks:
      - ${teardown_hook_validate($response)}
    validate:
      - eq: [status_code, 200]
```

### 参数化测试

使用多组参数运行同一测试，支持三种模式：

#### 1. 矩阵模式（笛卡尔积）

```yaml
parameters:
  env: [dev, staging, prod]
  region: [us, eu]
  # 生成 3 × 2 = 6 个测试实例

steps:
  - name: 健康检查
    request:
      url: https://${env}-${region}.example.com/health
    validate:
      - eq: [status_code, 200]
```

#### 2. 枚举模式（列表）

```yaml
parameters:
  - {username: alice, role: admin}
  - {username: bob, role: user}
  - {username: charlie, role: guest}
  # 生成 3 个测试实例

steps:
  - name: 登录测试
    request:
      method: POST
      url: /api/login
      body:
        username: $username
    validate:
      - eq: [status_code, 200]
      - eq: [$.data.role, $role]
```

#### 3. 压缩模式（并行数组）

使用连字符分隔的变量名（如 `username-password`）将多个值打包成组，每组值对应一个测试实例。

```yaml
parameters:
  - username-password:        # 连字符分隔的变量名
      - [alice, pass123]      # 第 1 组：username=alice, password=pass123
      - [bob, secret456]      # 第 2 组：username=bob, password=secret456
      - [charlie, pwd789]     # 第 3 组：username=charlie, password=pwd789
  # 生成 3 个测试实例，每组参数成对使用

steps:
  - name: 登录
    request:
      method: POST
      url: /api/login
      body:
        username: $username   # 使用第 1 个变量
        password: $password   # 使用第 2 个变量
```

> **提示**：压缩模式适合多个参数需要成对出现的场景（如用户名和密码、坐标 x 和 y 等）。

### SQL 验证

对数据库状态进行断言，确保 API 操作正确写入数据库。

#### 环境配置

```env
# 方式 1：独立配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=test_user
MYSQL_PASSWORD=test_pass
MYSQL_DB=test_database

# 方式 2：DSN 连接串
MYSQL_DSN=mysql://user:pass@localhost:3306/test_db
```

#### 使用示例

```yaml
steps:
  - name: 创建订单
    request:
      method: POST
      url: /api/orders
      body:
        product_id: "PROD-001"
        quantity: 2
    extract:
      order_id: $.data.order_id
    validate:
      - eq: [status_code, 201]

    sql_validate:
      # 查询 1：验证订单状态
      - query: "SELECT status, total FROM orders WHERE id='$order_id'"
        expect:
          - eq: [status, "pending"]     # 断言 status 字段
          - gt: [total, 0]              # 断言 total 字段
        store:
          db_status: status             # 存储结果为变量
          db_total: total

      # 查询 2：验证订单项数量
      - query: "SELECT COUNT(*) AS cnt FROM order_items WHERE order_id='$order_id'"
        expect:
          - ge: [cnt, 1]                # 至少 1 条记录

      # 查询 3：使用不同数据库
      - query: "SELECT log FROM audit.logs WHERE order_id='$order_id'"
        dsn: mysql://user:pass@audit-host:3306/audit_db
        expect:
          - contains: [log, "order_created"]
```

**SQL 验证选项**：

- `query` - SQL 查询（必需，支持变量插值）
- `expect` - 断言列表（可选）
- `store` - 将字段存储为变量（可选）
- `allow_empty` - 允许空结果（可选，默认 false）
- `dsn` - 覆盖数据库连接（可选）

### 重试机制

为不稳定的接口配置自动重试：

```yaml
steps:
  - name: 调用不稳定接口
    request:
      method: GET
      url: /api/flaky-endpoint
    retry: 3                  # 最多重试 3 次
    retry_backoff: 0.5        # 初始退避 0.5 秒
                              # 重试间隔：0.5s → 1.0s → 2.0s（指数增长，上限 2.0s）
    validate:
      - eq: [status_code, 200]
```

---

## 📊 报告和通知

### HTML 报告

生成交互式 HTML 报告：

```bash
arun run testcases --html reports/report.html
```

截图预览（统一浅色风格）

```bash
# 生成并预览（示例使用引用型 testsuite）
python -m arun.cli run testsuites/testsuite_smoke.yaml \
  --env-file .env \
  --html reports/report.html

# 打开：reports/report.html
```

**特性**：
- 📈 **摘要仪表板**：总数、通过、失败、跳过、耗时（随筛选动态更新）
- 🔍 **详细断言**：每个断言的期望值、实际值、结果（支持"仅失败断言"筛选）
- 📦 **完整调试信息**：请求/响应/提取变量/cURL 命令（支持一键复制，带视觉反馈）
  - ✅ 复制成功：绿色高亮提示"已复制"
  - ⚠️ 复制失败（HTTPS 限制）：橙色提示"已选中，按 Ctrl/Cmd+C"自动选中文本
  - 🎯 精准复制：基于原始数据，确保 JSON 格式准确无误
  - 🔧 cURL 命令：使用 `--data-raw` 确保 payload 不被修改，JSON 自动格式化
- 🎛️ **交互增强**：
  - 状态筛选：通过/失败/跳过
  - 仅失败断言、仅失败断言步骤、展开/折叠全部、仅失败用例
- 🧩 **JSON 语法高亮**：请求/响应/提取变量采用轻量高亮（零依赖、ES5 兼容）
- 🎨 **GitHub 主题**：默认浅色 GitHub 风格，简洁专业
- 🌐 **兼容性**：ES5 兼容，支持旧浏览器和 `file://` 协议访问

### JSON 报告

生成结构化 JSON 报告：

```bash
arun run testcases --report reports/run.json
```

**格式**：

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
      "name": "用户登录",
      "status": "passed",
      "duration_ms": 145.3,
      "parameters": {},
      "steps": [...]
    }
  ]
}
```

### Allure 报告

生成 Allure 原始结果（可用 Allure CLI/插件渲染成可视化报告）：

```bash
# 生成 Allure 结果
arun run testcases --allure-results allure-results

# 使用 Allure CLI 生成与打开报告（本地需安装 allure 命令）
allure generate allure-results -o allure-report --clean
allure open allure-report
```

#### Allure CLI 安装

**macOS / Linux:**
```bash
# 使用 Homebrew (macOS/Linux)
brew install allure

# 或使用 Scoop (Windows)
scoop install allure

# 或手动下载
# 1. 从 https://github.com/allure-framework/allure2/releases 下载最新版本
# 2. 解压并添加 bin 目录到 PATH
```

**验证安装：**
```bash
allure --version
```

#### 特性说明

- **附件丰富**：为每个步骤生成请求/响应/cURL/断言/提取变量等附件（遵循 `--mask-secrets` 脱敏策略）
- **套件分组**：默认按用例来源文件名归类（若可用），否则归为 "ARun"
- **趋势分析**：多次运行后可查看历史趋势（需保留 `allure-report/history` 目录）
- **CI/CD 集成**：可配合 Jenkins/GitLab CI 的 Allure 插件自动生成并展示报告

### 通知集成

#### 飞书通知

```bash
# 环境变量配置
export FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
export FEISHU_SECRET=your-secret      # 可选，签名验证
export FEISHU_STYLE=card              # card 或 text（默认）
export ARUN_NOTIFY_ONLY=failed        # failed 或 always

# 运行并通知
arun run testcases --notify feishu --env-file .env
```

**飞书卡片示例**（`FEISHU_STYLE=card`）：
- 📊 测试摘要（总数、通过、失败）
- 🚨 失败用例列表（前 5 个）
- 🔗 报告链接（需配置 `REPORT_URL`）
- 👤 @提醒（需配置 `FEISHU_MENTION`）

#### 邮件通知

```bash
# 环境变量配置
export SMTP_HOST=smtp.example.com
export SMTP_PORT=465
export SMTP_USER=noreply@example.com
export SMTP_PASS=app-password
export MAIL_FROM=noreply@example.com
export MAIL_TO=qa@example.com,dev@example.com

# 运行并通知（附带 HTML 报告）
arun run testcases --notify email --notify-attach-html --env-file .env
```

**邮件内容**：
- 📧 **纯文本/HTML 正文**：测试摘要 + 失败用例
- 📎 **附件**：完整 HTML 报告（可选）

#### 钉钉通知

```bash
# 环境变量配置
export DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
# 可选：安全设置为“加签”时需配置 SECRET（自动追加 timestamp/sign）
export DINGTALK_SECRET=your-secret
# 可选：@ 指定手机号（逗号分隔）；或全员 @
export DINGTALK_AT_MOBILES=13800138000,13900139000
export DINGTALK_AT_ALL=false
# 可选：消息样式 text/markdown（默认 text）
export DINGTALK_STYLE=text

# 运行并通知（失败才发）
arun run testcases --notify dingtalk --notify-only failed --env-file .env

# 也可多渠道同时发
arun run testcases --notify feishu,dingtalk --notify-only always --env-file .env
```

说明：
- 文本内容为测试摘要与失败 TOPN（默认 5）；包含报告和日志路径（若存在）。
- 配置了 `DINGTALK_SECRET` 时，通知将按钉钉机器人加签规范使用 HMAC-SHA256 进行签名（毫秒级时间戳）。

---

## 🛠 命令行工具

### arun run

运行测试用例：

```bash
# 基本用法
arun run <path> [options]

# 常用选项
--env-file .env               # 环境文件路径（默认 .env）
-k "smoke and not slow"       # 标签过滤表达式
--vars key=value              # 变量覆盖（可重复）
--failfast                    # 首次失败时停止
--report FILE                 # 输出 JSON 报告
--html FILE                   # 输出 HTML 报告（默认 reports/report-<timestamp>.html）
--allure-results DIR          # 输出 Allure 结果目录（供 allure generate 使用）
--log-level DEBUG             # 日志级别（INFO/DEBUG，默认 INFO）
--log-file FILE               # 日志文件路径（默认 logs/run-<timestamp>.log）
--httpx-logs                  # 显示 httpx 内部日志
--reveal-secrets              # 显示敏感数据明文（默认）
--mask-secrets                # 脱敏敏感数据（CI/CD 推荐）
--notify feishu,email,dingtalk# 通知渠道
--notify-only failed          # 通知策略（failed/always，默认 failed）
--notify-attach-html          # 邮件附加 HTML 报告
```

**示例**：

```bash
# 运行整个目录
arun run testcases --env-file .env

# 使用标签过滤 + 生成报告
arun run testcases -k "smoke" --html reports/smoke.html

# 变量覆盖
arun run testcases --vars base_url=http://localhost:8000 --vars debug=true

# 失败时停止 + 详细日志
arun run testcases --failfast --log-level debug

# CI/CD 模式：失败时通知
arun run testcases --notify feishu --notify-only failed --mask-secrets
```

### arun check

验证 YAML 语法和风格：

```bash
# 检查测试文件
arun check testcases

# 检查单个文件
arun check testcases/test_login.yaml
```

**检查项**：
- YAML 语法错误
- 提取语法（必须使用 `$` 前缀）
- 断言目标（`status_code`、`headers.*`、`$.*`）
- Hooks 函数命名规范
- 步骤间空行（可读性）

### arun fix

自动修复 YAML 风格问题：

```bash
# 修复单个目录
arun fix testcases

# 修复多个目录（一次性处理）
arun fix testcases testsuites examples

# 仅修复步骤间空行
arun fix testcases --only-spacing

# 仅迁移 hooks 到 config
arun fix testcases --only-hooks
```

**修复内容**：
- 将 suite/case 级 hooks 移到 `config.setup_hooks/teardown_hooks`
- 确保 `steps` 中相邻步骤之间有一个空行

### arun import - 格式转换

将 curl/Postman/HAR 转换为 ARun YAML 用例，支持多种导出模式。

#### import curl

将 cURL 命令转换为 YAML 用例：

```bash
# 基本用法：多个 curl 合并成一个用例（默认行为）
arun import curl requests.curl --outfile testcases/imported.yaml

# 从标准输入导入
curl https://api.example.com/users | arun import curl -

# 单步导出：为每条 curl 生成独立 YAML 文件
arun import curl requests.curl --split-output
# 指定命名基准（将生成 foo_1.yaml、foo_2.yaml ...）
arun import curl requests.curl --outfile foo.yaml --split-output

# 追加到现有用例
arun import curl new_request.curl --into testcases/test_api.yaml

# 自定义用例信息
arun import curl requests.curl \
  --case-name "API 测试套件" \
  --base-url https://api.example.com \
  --outfile testcases/test_suite.yaml
```

**选项说明**：
- `--outfile` - 输出文件路径（默认输出到标准输出）
- `--split-output` - 为每条 curl 生成独立的 YAML 文件
- `--into` - 追加到现有 YAML 文件（与 `--split-output` 互斥）
- `--case-name` - 指定用例名称（默认 "Imported Case"）
- `--base-url` - 设置 base_url（会自动提取公共前缀）

#### import postman

从 Postman Collection JSON 导入：

```bash
# 基本导入：将所有请求合并为一个用例
arun import postman collection.json --outfile testcases/api_tests.yaml

# 单步导出：为每个请求生成独立文件
arun import postman collection.json --split-output

# 追加到现有用例
arun import postman new_collection.json --into testcases/test_api.yaml

# 自定义选项
arun import postman collection.json \
  --case-name "Postman 导入测试" \
  --base-url https://api.example.com \
  --split-output
```

**支持特性**：
- ✅ 请求方法、URL、headers、body
- ✅ 查询参数（params）
- ✅ 自动提取 base_url
- ✅ 默认添加状态码断言

#### import har

从浏览器 HAR 文件导入：

```bash
# 基本导入：合并所有请求
arun import har recording.har --outfile testcases/browser_tests.yaml

# 单步导出：为每个请求生成独立文件
arun import har recording.har --split-output

# 过滤并导入（结合其他工具）
# 例如：只导入特定域名的请求
cat recording.har | jq '.log.entries[] | select(.request.url | contains("api.example.com"))' | \
  arun import har - --outfile testcases/filtered.yaml

# 自定义选项
arun import har recording.har \
  --case-name "浏览器录制测试" \
  --base-url https://api.example.com \
  --split-output
```

**适用场景**：
- 🌐 浏览器开发者工具导出的 HAR 文件
- 🔍 抓包工具（Charles、Fiddler）导出的流量
- 🧪 将手工测试转换为自动化用例

**通用提示**：
- `--split-output` 不能与 `--into` 同时使用
- 从标准输入导入时（`-`），默认生成 `imported_step_<n>.yaml`
- 所有导入的用例自动添加 `eq: [status_code, 200]` 断言
- 支持自动提取和规范化 headers、params、body

### arun export - 导出为 cURL

将 YAML 用例导出为可执行的 cURL 命令，便于调试和分享。

#### export curl

```bash
# 基本导出：将用例转换为 curl 命令
arun export curl testcases/test_api.yaml

# 导出到文件（多行格式，便于阅读）
arun export curl testcases/test_api.yaml --outfile requests.curl

# 单行紧凑格式
arun export curl testcases/test_api.yaml --one-line

# 导出特定步骤（1-based 索引）
arun export curl testcases/test_api.yaml --steps "1,3-5"

# 添加步骤注释（说明用例名、步骤名、变量、表达式）
arun export curl testcases/test_api.yaml --with-comments

# 脱敏敏感头部
arun export curl testcases/test_api.yaml --redact Authorization,Cookie

# 导出整个目录
arun export curl testcases --outfile all_requests.curl

# 仅导出特定用例
arun export curl testsuites/testsuite_smoke.yaml --case-name "健康检查"
```

**选项说明**：
- `--outfile FILE` - 输出到文件（默认标准输出）
- `--multiline` / `--one-line` - 多行格式（默认）或单行紧凑格式
- `--steps "1,3-5"` - 导出指定步骤（支持范围语法）
- `--with-comments` - 添加 `# Case/Step` 注释
- `--redact HEADERS` - 脱敏指定头部（逗号分隔），如 `Authorization,Cookie`
- `--case-name NAME` - 仅导出匹配的用例
- `--shell sh|ps` - 行延续符风格（sh: `\`，ps: `` ` ``）

**导出特性**：
- ✅ 自动渲染变量和环境变量（从 `.env` 读取）
- ✅ 使用 `--data-raw` 确保 JSON payload 不被修改
- ✅ JSON 自动格式化（indent=2，便于阅读）
- ✅ 自动添加 `Content-Type: application/json`（当 body 为 JSON 时）
- ✅ 智能 HTTP 方法处理（POST 有 body 时省略 `-X POST`）
- ✅ 支持复杂请求（params、files、auth、redirects）

**导出示例**：

```bash
# 多行格式（默认）
curl 'https://api.example.com/users' \
  -H 'Authorization: Bearer ***' \
  -H 'Content-Type: application/json' \
  --data-raw '{
  "username": "test_user",
  "email": "test@example.com"
}'

# 单行格式（--one-line）
curl -X POST 'https://api.example.com/users' -H 'Authorization: Bearer ***' --data-raw '{"username":"test_user"}'

# 带注释格式（--with-comments）
# Case: 用户注册测试
# Step: 注册新用户
# Vars: username password
# Exprs: short_uid
curl 'https://api.example.com/register' \
  --data-raw '{"username":"user_abc123"}'
```

**适用场景**：
- 🐛 **调试**：快速在终端验证请求
- 📤 **分享**：与团队成员共享请求示例
- 📝 **文档**：生成 API 文档中的示例代码
- 🔄 **迁移**：将 YAML 用例转换为其他工具格式

## 💻 实战示例

### 示例 1：登录流程 + Token 自动注入

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
      token: $.data.access_token        # 提取 token
      user_id: $.data.user.id
    validate:
      - eq: [status_code, 200]
      - eq: [$.success, true]

  - name: 获取用户资料
    request:
      method: GET
      url: /api/v1/users/$user_id
      # Authorization 头自动注入：Bearer {token}
    validate:
      - eq: [status_code, 200]
      - eq: [$.data.id, $user_id]
```

### 示例 2：E2E 购物流程

> **说明**：此示例使用了项目自带的 `uid()` 和 `short_uid()` 辅助函数（定义在根目录 `arun_hooks.py`），用于生成唯一的测试数据。

```yaml
config:
  name: E2E 购物流程
  base_url: ${ENV(BASE_URL)}
  tags: [e2e, critical]
  variables:
    # 动态生成测试数据，避免冲突
    username: user_${short_uid(8)}
    email: ${uid()}@example.com
    password: Test@${short_uid(6)}
    shipping_address: ${short_uid(12)} Test Street

steps:
  - name: 注册新用户
    request:
      method: POST
      url: /api/v1/auth/register
      body:
        username: $username
        email: $email
        password: $password
        full_name: Test User
        shipping_address: $shipping_address
    extract:
      username: $.data.username

  - name: 登录
    request:
      method: POST
      url: /api/v1/auth/login
      body:
        username: $username
        password: $password
    extract:
      token: $.data.access_token

  - name: 浏览商品
    request:
      method: GET
      url: /api/v1/products/
    extract:
      product_id: $.data.items[0].id

  - name: 加入购物车
    request:
      method: POST
      url: /api/v1/cart/items
      body:
        product_id: $product_id
        quantity: 2
    validate:
      - eq: [status_code, 201]
      - eq: [$.data.items[0].quantity, 2]

  - name: 下单
    request:
      method: POST
      url: /api/v1/orders/
      body:
        shipping_address: $shipping_address
    extract:
      order_id: $.data.order_id
    validate:
      - eq: [status_code, 201]
      - gt: [$.data.order_id, 0]
```

### 示例 3：参数化矩阵测试

```yaml
config:
  name: 多环境健康检查
  tags: [smoke, health]

parameters:
  env: [dev, staging, prod]
  region: [us, eu, asia]
  # 生成 3 × 3 = 9 个测试实例

steps:
  - name: 检查服务健康
    variables:
      full_url: https://${env}-${region}.example.com
    request:
      method: GET
      url: ${full_url}/health
    validate:
      - eq: [status_code, 200]
      - eq: [$.status, "healthy"]
      - contains: [$.data.region, $region]
```

### 示例 4：请求签名 Hooks

**arun_hooks.py**：

```python
import time
import hmac
import hashlib

def setup_hook_hmac_sign(request: dict, variables: dict = None, env: dict = None) -> dict:
    """HMAC-SHA256 签名"""
    secret = env.get('APP_SECRET', '').encode()
    method = request.get('method', 'GET')
    url = request.get('url', '')
    timestamp = str(int(time.time()))

    message = f"{method}|{url}|{timestamp}".encode()
    signature = hmac.new(secret, message, hashlib.sha256).hexdigest()

    headers = request.setdefault('headers', {})
    headers['X-Timestamp'] = timestamp
    headers['X-HMAC'] = signature

    return {'last_signature': signature}
```

**test_signed_api.yaml**：

```yaml
config:
  name: 签名 API 测试
  base_url: ${ENV(BASE_URL)}
  setup_hooks:
    - ${setup_hook_hmac_sign($request)}

steps:
  - name: 访问签名接口
    request:
      method: GET
      url: /api/secure/data
      # X-Timestamp 和 X-HMAC 头自动添加
    validate:
      - eq: [status_code, 200]
```

### 示例 5：Import/Export 工作流

演示从浏览器/Postman 到 ARun YAML 的完整转换流程。

#### 场景 1：从浏览器 HAR 快速生成测试

```bash
# 1. 在浏览器中操作（F12 开发者工具）
#    - 打开 Network 面板
#    - 执行业务操作（登录、下单等）
#    - 右键 → Save all as HAR with content

# 2. 导入为测试用例（每个请求一个文件）
arun import har recording.har --split-output \
  --case-name "浏览器录制" \
  --base-url https://api.example.com

# 输出：
# [IMPORT] Wrote YAML for '浏览器录制 - Step 1' to recording_step1.yaml
# [IMPORT] Wrote YAML for '浏览器录制 - Step 2' to recording_step2.yaml
# ...

# 3. 运行测试验证
arun run recording_step1.yaml --env-file .env

# 4. 导出为 curl 命令调试
arun export curl recording_step1.yaml --with-comments
```

#### 场景 2：Postman Collection 迁移

```bash
# 1. 从 Postman 导出 Collection（JSON 格式）

# 2. 转换为 YAML（合并为一个测试套件）
arun import postman api_collection.json \
  --outfile testcases/test_api_suite.yaml \
  --case-name "API 完整测试"

# 3. 编辑 YAML 添加断言和提取逻辑
# （此时可以利用 ARun 的变量提取、参数化等高级特性）

# 4. 运行测试
arun run testcases/test_api_suite.yaml --env-file .env --html reports/report.html
```

#### 场景 3：curl 命令转测试用例

```bash
# 1. 复制浏览器 Network 面板中的 "Copy as cURL"
# 或从 API 文档复制 curl 示例

# 2. 保存到文件
cat > api_requests.curl <<'EOF'
curl 'https://api.example.com/auth/login' \
  -H 'Content-Type: application/json' \
  --data-raw '{"username":"admin","password":"secret"}'

curl 'https://api.example.com/users/me' \
  -H 'Authorization: Bearer TOKEN_HERE' \
  -H 'Accept: application/json'
EOF

# 3. 转换为 YAML
arun import curl api_requests.curl \
  --outfile testcases/test_auth_flow.yaml \
  --case-name "认证流程测试"

# 4. 编辑 YAML 添加 token 提取
# steps[0].extract: { token: $.data.access_token }
# steps[1].request.headers: { Authorization: "Bearer $token" }

# 5. 运行测试
arun run testcases/test_auth_flow.yaml --env-file .env
```

#### 场景 4：测试用例分享与调试

```bash
# 团队成员 A：创建测试用例
cat > testcases/test_new_feature.yaml <<'EOF'
config:
  name: 新功能测试
  base_url: ${ENV(BASE_URL)}
steps:
  - name: 创建资源
    request:
      method: POST
      url: /api/resources
      body: {name: "test", type: "demo"}
    extract:
      resource_id: $.data.id
    validate:
      - eq: [status_code, 201]
EOF

# 导出为 curl 命令分享给团队成员 B
arun export curl testcases/test_new_feature.yaml \
  --outfile share.curl \
  --with-comments

# 团队成员 B：收到 curl 命令后
# 方式 1：直接在终端执行验证
bash share.curl

# 方式 2：导入为自己的测试用例
arun import curl share.curl --outfile my_tests/imported.yaml
```

**工作流优势**：
- 🚀 **快速上手**：从现有工具（浏览器、Postman）无缝迁移
- 🔄 **双向转换**：YAML ↔ curl 灵活互转
- 🧪 **渐进增强**：先导入基础用例，再添加断言、提取、参数化
- 👥 **团队协作**：通过 curl 命令快速分享请求示例

---

## 🧩 Testsuite（引用用例）

除内联的 Suite（在一个文件的 `cases:` 中直接编写多个用例）外，还支持类似 HttpRunner 的“引用型 Testsuite”：在 `testsuites/` 目录下的 testsuite 文件通过 `testcases:` 引用 `testcases/` 下的单用例文件，并可在条目级覆盖名称、注入变量或提供参数化。

示例（`testsuites/testsuite_smoke.yaml`）：

```yaml
config:
  name: 冒烟套件
  base_url: ${ENV(BASE_URL)}
  tags: [smoke]

testcases:
  - name: 健康检查
    testcase: testcases/test_health.yaml
  - name: 目录基础
    testcase: testcases/test_catalog.yaml
```

示例（带条目级参数化）：

```yaml
config:
  name: 回归套件
  base_url: ${ENV(BASE_URL)}
  tags: [regression]

testcases:
  - name: 端到端下单（参数化）
    testcase: testcases/test_e2e_purchase.yaml
    parameters:
      quantity: [1, 2]
```

运行：

```bash
arun run testsuites --env-file .env
arun run testsuites -k "smoke" --env-file .env
```

说明：
- `testsuite` 文件与内联 `suite` 文件可共存。推荐优先使用 `testsuite`（引用型），`suite`（内联型）作为兼容形式继续支持。
- 条目级 `variables` 覆盖用例 `config.variables`（优先级：Suite.config.variables < Case.config.variables < Item.variables < CLI/Step）。
- 条目级 `parameters` 会覆盖用例自带的参数化配置。

---

## 🔗 CI/CD 集成

### GitHub Actions

```yaml
name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Dependencies
        run: pip install -e .

      - name: Run Tests
        env:
          BASE_URL: ${{ secrets.API_BASE_URL }}
          USER_USERNAME: ${{ secrets.TEST_USERNAME }}
          USER_PASSWORD: ${{ secrets.TEST_PASSWORD }}
        run: |
          arun run testcases \
            --html reports/report.html \
            --report reports/run.json \
            --mask-secrets \
            --notify-only failed

      - name: Upload Report
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
        --html reports/report.html \
        --report reports/run.json \
        --mask-secrets \
        --notify-only failed
  artifacts:
    when: always
    paths:
      - reports/
  variables:
    BASE_URL: $API_BASE_URL
    USER_USERNAME: $TEST_USERNAME
    USER_PASSWORD: $TEST_PASSWORD
```

### 最佳实践

1. **环境隔离**：使用不同的 `.env` 文件或环境变量区分开发/测试/生产环境
2. **敏感数据**：生产环境使用 `--mask-secrets` 防止泄露
3. **失败通知**：配置 `--notify` 和 `--notify-only failed` 及时发现问题
4. **报告归档**：保存 HTML 报告为 CI 制品，便于事后分析
5. **标签分类**：使用 `-k` 过滤，在不同阶段运行不同级别的测试（smoke → regression）

---

## 🐛 故障排查

### 常见问题

#### 1. BASE_URL 缺失警告

```
[ENV] Default .env not found and BASE_URL is missing. Relative URLs may fail.
```

**原因**：未提供 `.env` 文件且环境中没有 `BASE_URL` 变量。

**解决方案**：
```bash
# 方式 1：创建 .env 文件（推荐）
cat > .env <<EOF
BASE_URL=http://localhost:8000
USER_USERNAME=test_user
USER_PASSWORD=test_pass
EOF

# 方式 2：通过 CLI 传递
arun run testcases --vars base_url=http://localhost:8000

# 方式 3：导出环境变量
export BASE_URL=http://localhost:8000
```

#### 2. 找不到测试文件

```
No YAML test files found.
```

**原因**：文件不符合命名规范。

**解决方案**：
- 文件放在 `testcases/` 或 `testsuites/` 目录，或
- 文件命名为 `test_*.yaml` 或 `suite_*.yaml`

#### 3. 模块导入错误

```
ModuleNotFoundError: No module named 'arun'
```

**解决方案**：

```bash
pip install -e .
```

#### 4. 变量未定义

```
KeyError: 'user_id'
```

**原因**：变量在当前作用域不存在。

**解决方案**：
- 检查变量名拼写
- 确认变量在 `config.variables`、`steps[].variables` 或 `extract` 中定义
- 检查提取路径是否正确

#### 5. SQL 验证失败

```
MySQL assertion requires MYSQL_USER or dsn.user.
```

**解决方案**：

```env
# 添加到 .env
MYSQL_HOST=localhost
MYSQL_USER=test_user
MYSQL_PASSWORD=test_pass
MYSQL_DB=test_db
```

或安装数据库驱动：

```bash
pip install pymysql
```

#### 6. Hooks 未加载

**原因**：`arun_hooks.py` 文件位置不正确，或文件名拼写错误。

**解决方案**：

> **注意**：本项目根目录已提供 `arun_hooks.py` 示例文件，包含常用函数。

1. 确认 `arun_hooks.py` 在项目根目录
2. 检查文件名拼写（不是 `hooks.py`）
3. 或使用环境变量指定自定义路径：

```bash
export ARUN_HOOKS_FILE=/path/to/custom_hooks.py
arun run testcases
```

### 调试技巧

#### 1. 启用详细日志

```bash
arun run testcases --log-level debug --log-file debug.log
```

#### 2. 显示 httpx 请求日志

```bash
arun run testcases --httpx-logs
```

#### 3. 查看 cURL 命令

调试日志和 HTML 报告都包含每个请求的 cURL 等效命令（使用 `--data-raw` 确保 payload 不被修改，JSON 自动格式化提升可读性）：

```bash
# 调试日志示例
[DEBUG] cURL: curl -X POST 'https://api.example.com/login' \
  -H 'Content-Type: application/json' \
  --data-raw '{
  "username": "test",
  "password": "***"
}'

# HTML 报告中可一键复制 cURL 命令
# JSON 自动格式化（indent=2）+ 自动添加 Content-Type
```

#### 4. 验证 YAML 语法

```bash
arun check testcases
```

---

## 📚 完整参考

### DSL 完整语法

### 内置函数

| 函数 | 说明 | 示例 |
|------|------|------|
| `ENV(key, default?)` | 读取环境变量<br>可选默认值参数 | `${ENV(BASE_URL)}`<br>`${ENV(TIMEOUT, 30)}` |
| `now()` | 当前 UTC 时间（ISO 8601 格式） | `${now()}` → `2025-01-15T08:30:00` |
| `uuid()` | 生成标准 UUID v4 | `${uuid()}` → `550e8400-e29b-...` |
| `random_int(min, max)` | 生成范围内随机整数（含边界） | `${random_int(1, 100)}` → `42` |
| `base64_encode(s)` | Base64 编码字符串或字节 | `${base64_encode('hello')}` → `aGVsbG8=` |
| `hmac_sha256(key, msg)` | HMAC-SHA256 哈希（返回十六进制） | `${hmac_sha256($secret, $data)}` |

> **注意**：以上函数由框架内置提供（`arun/templating/builtins.py`），无需额外配置或导入。`ENV()` 是模板引擎内置的特殊函数，用于读取操作系统环境变量。

### 项目自带辅助函数

本项目根目录包含 `arun_hooks.py` 示例文件，提供了常用的辅助函数和 Hooks，可直接使用或按需修改：

**模板辅助函数**（在 `${}` 中调用）：

| 函数 | 说明 | 示例 |
|------|------|------|
| `ts()` | Unix 时间戳（秒） | `${ts()}` → `1678901234` |
| `md5(s)` | MD5 哈希（十六进制） | `${md5('hello')}` → `5d41402a...` |
| `uid()` | 32 字符十六进制 UUID | `${uid()}` → `a1b2c3d4e5f6...` |
| `short_uid(n=8)` | 短 UUID（默认 8 字符） | `${short_uid(12)}` → `a1b2c3d4e5f6` |
| `sign(key, ts)` | 签名示例（MD5 组合） | `${sign($api_key, $ts)}` |
| `uuid4()` | 标准 UUID v4 | `${uuid4()}` → `550e8400-e29b-...` |
| `echo(x)` | 回显输入值（调试用） | `${echo('test')}` → `test` |
| `sum_two_int(a, b)` | 两数相加 | `${sum_two_int(1, 2)}` → `3` |

**生命周期 Hooks**（在 `setup_hooks/teardown_hooks` 中使用）：

| Hook 函数 | 用途 | 参数 | 示例 |
|-----------|------|------|------|
| `setup_hook_sign_request` | 添加简单 MD5 签名头<br>（X-Timestamp + X-Signature） | `$request` | `${setup_hook_sign_request($request)}` |
| `setup_hook_hmac_sign` | 添加 HMAC-SHA256 签名头<br>（X-Timestamp + X-HMAC，需 APP_SECRET） | `$request` | `${setup_hook_hmac_sign($request)}` |
| `setup_hook_api_key` | 注入 API Key 头<br>（X-API-Key，从环境变量读取） | `$request` | `${setup_hook_api_key($request)}` |
| `teardown_hook_assert_status_ok` | 断言响应状态码为 200 | `$response` | `${teardown_hook_assert_status_ok($response)}` |
| `teardown_hook_capture_request_id` | 提取响应中的 request_id 到变量 | `$response` | `${teardown_hook_capture_request_id($response)}` |

**自定义函数**：编辑 `arun_hooks.py` 文件即可添加或修改函数，所有非下划线开头的函数自动加载到模板引擎中。

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `ARUN_ENV` | 环境名称 | - |
| `ARUN_HOOKS_FILE` | 自定义 hooks 文件路径 | `arun_hooks.py` |
| `ARUN_NOTIFY` | 默认通知渠道 | - |
| `ARUN_NOTIFY_ONLY` | 通知策略 | `failed` |
| `NOTIFY_TOPN` | 通知失败用例数量 | `5` |
| `FEISHU_WEBHOOK` | 飞书 Webhook URL | - |
| `FEISHU_SECRET` | 飞书签名密钥 | - |
| `FEISHU_STYLE` | 飞书消息风格 | `text` |
| `SMTP_HOST` | SMTP 服务器 | - |
| `SMTP_PORT` | SMTP 端口 | `465` |
| `MAIL_FROM` | 发件人 | - |
| `MAIL_TO` | 收件人（逗号分隔） | - |
| `MYSQL_DSN` | MySQL 连接串 | - |
| `MYSQL_HOST` | MySQL 主机 | `127.0.0.1` |
| `MYSQL_PORT` | MySQL 端口 | `3306` |
| `MYSQL_USER` | MySQL 用户 | - |
| `MYSQL_PASSWORD` | MySQL 密码 | - |
| `MYSQL_DB` | MySQL 数据库 | - |

---

## 🤝 贡献和支持

### 快速贡献

我们欢迎任何形式的贡献！

1. **Fork** 本仓库
2. 创建功能分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m "feat: add amazing feature"`
4. 推送到分支：`git push origin feature/amazing-feature`
5. 创建 **Pull Request**

### 贡献指南

- 遵循现有代码风格（black、ruff）
- 为新功能添加测试用例
- 更新相关文档
- 编写清晰的提交消息
- 保持更改集中和原子化

### 开发环境

```bash
# 克隆仓库
git clone https://github.com/Devliang24/arun.git
cd arun

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -e .

# 运行测试
arun run testcases --env-file .env

# 验证代码风格
# black arun/
# ruff check arun/
```

### 社区资源

- **示例集合**：[examples/](examples/)
- **问题追踪**：[GitHub Issues](https://github.com/Devliang24/arun/issues)
- **变更日志**：查看提交历史

---

## 📄 许可证

本项目采用 **MIT 许可证** - 详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

ARun 基于优秀的开源项目构建：

- [httpx](https://www.python-httpx.org/) - 现代 HTTP 客户端
- [pydantic](https://docs.pydantic.dev/) - 数据验证
- [jmespath](https://jmespath.org/) - JSON 查询
- [rich](https://rich.readthedocs.io/) - 终端美化
- [typer](https://typer.tiangolo.com/) - CLI 框架

感谢所有贡献者！

---

<div align="center">

**由 ARun 团队用 ❤️ 构建**

[⬆ 回到顶部](#arun)

</div>
