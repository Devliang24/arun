# APIRunner

<div align="center">

**零代码 HTTP API 测试框架 · 基于 YAML DSL · 5 分钟上手**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-orange)]()

[快速开始](#-快速开始-5-分钟) • [核心特性](#-核心特性) • [文档](#-核心概念) • [示例](#-实战示例)

</div>

---

## 📖 项目简介

APIRunner 是一个**极简、强大、生产就绪**的 HTTP API 测试框架。使用清晰的 YAML 语法编写测试用例，无需编写代码，5 分钟即可完成第一个测试。

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

### 💡 为什么选择 APIRunner？

| 特性 | APIRunner | 其他工具 |
|------|-----------|----------|
| **零代码** | ✅ 纯 YAML，无需编程 | ❌ 需要 Python/JavaScript 代码 |
| **学习曲线** | ✅ 5 分钟上手 | ⚠️ 需要学习测试框架 |
| **模板系统** | ✅ 简洁的 `${expr}` 语法 | ⚠️ 复杂的模板引擎 |
| **数据库验证** | ✅ 内置 SQL 断言 | ❌ 需要额外开发 |
| **CI/CD 就绪** | ✅ 开箱即用 | ⚠️ 需要配置 |
| **报告系统** | ✅ HTML + JSON + 通知 | ⚠️ 需要集成第三方 |

### 🎯 适用场景

✅ **接口测试**：REST API、微服务接口验证
✅ **E2E 测试**：完整业务流程测试
✅ **冒烟测试**：快速验证服务可用性
✅ **回归测试**：CI/CD 流水线集成
✅ **性能监控**：响应时间断言

---

## ⚡ 核心特性

### 🔥 开箱即用

- **零配置启动**：`pip install -e . && arun run testcases`
- **YAML DSL**：声明式测试用例，人类可读
- **智能变量管理**：6 层作用域，自动 token 注入
- **JMESPath 提取**：强大的 JSON 数据提取能力

### 🚀 高级功能

- **Hooks 系统**：Suite/Case/Step 三级生命周期钩子，支持请求签名、数据准备
- **SQL 验证**：内置 MySQL 支持，查询结果断言和变量存储
- **参数化测试**：矩阵、枚举、压缩三种模式，轻松生成测试组合
- **重试机制**：指数退避，容错不稳定接口

### 📊 企业级特性

- **专业报告**：交互式 HTML 报告（可复制 JSON/cURL）+ 结构化 JSON 报告 + Allure 集成
- **通知集成**：飞书卡片/文本、钉钉文本/Markdown、邮件 HTML/附件，失败聚合通知
- **安全保护**：敏感数据自动脱敏（headers/body/环境变量）
- **调试友好**：Rich 彩色输出、cURL 命令生成（格式化 JSON + 自动 Content-Type）、详细日志、错误步骤详情

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

APIRunner 使用简洁的 **Dollar 表达式**进行变量插值：

```yaml
# 1. 简单变量引用
url: /users/$user_id                 # 等同于 /users/123

# 2. 表达式（花括号）
headers:
  X-Timestamp: ${ts()}               # 调用自定义函数（需在 arun_hooks.py 中定义）
  X-Signature: ${md5($api_key)}      # 函数嵌套

# 3. 环境变量
base_url: ${ENV(BASE_URL)}           # 读取环境变量
api_key: ${ENV(API_KEY, default)}    # 带默认值

# 4. 算术运算
body:
  user_id: ${int($user_id) + 1}      # 支持基本运算
```

### 变量作用域优先级

变量查找顺序（**从高到低**）：

```
1. CLI 覆盖      --vars key=value (最高优先级)
2. 步骤变量      steps[].variables (当前步骤内有效)
3. 配置变量      config.variables (用例级全局)
4. 参数变量      parameters (参数化测试时注入)
5. 提取变量      steps[].extract (从上一步响应提取，存入会话变量)
```

> **注意**：`${ENV(KEY)}` 用于读取操作系统环境变量，不属于变量作用域的一部分，而是模板引擎的内置函数。

示例：

```yaml
config:
  variables:
    user_id: 100        # 优先级 3：配置变量

parameters:
  user_id: [1, 2]       # 优先级 4：参数变量会被配置变量覆盖

steps:
  - name: 登录
    extract:
      user_id: $.data.id  # 优先级 5：提取变量存入会话，供后续步骤使用

  - name: 获取用户
    variables:
      user_id: 999      # 优先级 2：步骤变量（当前步骤内最高）
    request:
      url: /users/$user_id  # 使用 999
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
python -m apirunner.cli run testsuites/testsuite_smoke.yaml \
  --env-file .env \
  --html reports/report.html

# 打开：reports/report.html
```

**特性**：
- 📈 摘要仪表板：总数、通过、失败、跳过、耗时（随筛选动态更新）
- 🔍 详细断言：每个断言的期望值、实际值、结果（支持"仅失败断言"）
- 📦 请求/响应/提取变量/cURL：完整 JSON 和命令（支持一键复制，带视觉反馈）
  - ✅ 复制成功：绿色高亮提示"已复制"
  - ⚠️ 复制失败：橙色提示"已选中，按 Ctrl/Cmd+C"自动选中文本
  - 🎯 精准复制：基于原始数据，确保 JSON 格式准确无误
- 🎛️ 交互增强：
  - 状态筛选：通过/失败/跳过
  - 仅失败断言、仅失败断言步骤、展开/折叠全部、仅失败用例
- 🧩 JSON 可读性：请求/响应/提取变量采用轻量 JSON 语法高亮（零依赖）
- 🎨 GitHub 主题：默认浅色 GitHub 风格，简洁专业

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
- **套件分组**：默认按用例来源文件名归类（若可用），否则归为 "APIRunner"
- **趋势分析**：多次运行后可查看历史趋势（需保留 `allure-report/history` 目录）
- **CI/CD 集成**：可配合 Jenkins/GitLab CI 的 Allure 插件自动生成并展示报告

### 合并报告

合并多个测试运行的报告：

```bash
# 并行运行
arun run testcases/smoke --report reports/smoke.json
arun run testcases/regression --report reports/regression.json

# 合并结果
arun report reports/smoke.json reports/regression.json -o reports/merged.json
```

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
--html FILE                   # 输出 HTML 报告
--allure-results DIR          # 输出 Allure 结果目录（供 allure generate 使用）
--log-level DEBUG             # 日志级别（INFO/DEBUG）
--log-file FILE               # 日志文件路径
--httpx-logs                  # 显示 httpx 内部日志
--mask-secrets                # 脱敏敏感数据（默认 --reveal-secrets）
--notify feishu,email,dingtalk# 通知渠道
--notify-only failed          # 通知策略（failed/always）
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
# 修复所有问题
arun fix testcases

# 仅修复步骤间空行
arun fix testcases --only-spacing

# 仅迁移 hooks 到 config
arun fix testcases --only-hooks
```

**修复内容**：
- 将 suite/case 级 hooks 移到 `config.setup_hooks/teardown_hooks`
- 确保 `steps` 中相邻步骤之间有一个空行

### arun report

合并多个 JSON 报告：

```bash
arun report <input1.json> <input2.json> ... -o <output.json>

# 示例
arun report reports/run1.json reports/run2.json -o reports/merged.json
```

---

## 💻 实战示例

### 示例 1：登录流程 + Token 自动注入

```yaml
config:
  name: 登录并访问受保护资源
  base_url: ${ENV(BASE_URL)}

steps:
  - name: 用户登录
    request:
      method: POST
      url: /api/v1/auth/login
      body:
        username: ${ENV(USER_USERNAME)}
        password: ${ENV(USER_PASSWORD)}
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

steps:
  - name: 注册新用户
    request:
      method: POST
      url: /api/v1/auth/register
      body:
        username: user_${short_uid(8)}
        email: ${uid()}@example.com
        password: "Test@123"
    extract:
      username: $.data.username

  - name: 登录
    request:
      method: POST
      url: /api/v1/auth/login
      body:
        username: $username
        password: "Test@123"
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
        shipping_address: "123 Test St"
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
            --mask-secrets

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
        --mask-secrets
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

#### 1. 找不到测试文件

```
No YAML test files found.
```

**原因**：文件不符合命名规范。

**解决方案**：
- 文件放在 `testcases/` 或 `testsuites/` 目录，或
- 文件命名为 `test_*.yaml` 或 `suite_*.yaml`

#### 2. 模块导入错误

```
ModuleNotFoundError: No module named 'apirunner'
```

**解决方案**：

```bash
pip install -e .
```

#### 3. 变量未定义

```
KeyError: 'user_id'
```

**原因**：变量在当前作用域不存在。

**解决方案**：
- 检查变量名拼写
- 确认变量在 `config.variables`、`steps[].variables` 或 `extract` 中定义
- 检查提取路径是否正确

#### 4. SQL 验证失败

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

#### 5. Hooks 未加载

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
| `ENV(key, default)` | 读取环境变量 | `${ENV(BASE_URL)}` |
| `now()` | 当前 UTC 时间 | `${now()}` |
| `uuid()` | 生成 UUID | `${uuid()}` |
| `random_int(min, max)` | 随机整数 | `${random_int(1, 100)}` |
| `base64_encode(s)` | Base64 编码 | `${base64_encode('text')}` |
| `hmac_sha256(key, msg)` | HMAC-SHA256 | `${hmac_sha256($secret, $data)}` |

> **注意**：以上函数由框架内置提供，无需额外配置。

### 项目自带辅助函数

本项目根目录包含 `arun_hooks.py` 示例文件，提供了常用的辅助函数和 Hooks，可直接使用或按需修改：

**模板辅助函数**（在 `${}` 中调用）：

| 函数 | 说明 | 示例 |
|------|------|------|
| `ts()` | Unix 时间戳（秒） | `${ts()}` → `1678901234` |
| `md5(s)` | MD5 哈希 | `${md5('hello')}` → `5d41402a...` |
| `uid()` | 32 字符十六进制 UUID | `${uid()}` → `a1b2c3d4...` |
| `short_uid(n)` | 短 UUID（默认 8 字符） | `${short_uid(8)}` → `a1b2c3d4` |
| `sign(key, ts)` | 签名示例（md5） | `${sign($api_key, $ts)}` |
| `uuid4()` | 标准 UUID | `${uuid4()}` → `550e8400-e29b-...` |

**生命周期 Hooks**（在 `setup_hooks/teardown_hooks` 中使用）：

| Hook 函数 | 用途 | 示例 |
|-----------|------|------|
| `setup_hook_sign_request` | 添加简单 MD5 签名头 | `${setup_hook_sign_request($request)}` |
| `setup_hook_hmac_sign` | 添加 HMAC-SHA256 签名头 | `${setup_hook_hmac_sign($request)}` |
| `setup_hook_api_key` | 注入 API Key 头 | `${setup_hook_api_key($request)}` |
| `teardown_hook_assert_status_ok` | 断言状态码为 200 | `${teardown_hook_assert_status_ok($response)}` |
| `teardown_hook_capture_request_id` | 提取 request_id 到变量 | `${teardown_hook_capture_request_id($response)}` |

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
# black apirunner/
# ruff check apirunner/
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

APIRunner 基于优秀的开源项目构建：

- [httpx](https://www.python-httpx.org/) - 现代 HTTP 客户端
- [pydantic](https://docs.pydantic.dev/) - 数据验证
- [jmespath](https://jmespath.org/) - JSON 查询
- [rich](https://rich.readthedocs.io/) - 终端美化
- [typer](https://typer.tiangolo.com/) - CLI 框架

感谢所有贡献者！

---

<div align="center">

**由 APIRunner 团队用 ❤️ 构建**

[⬆ 回到顶部](#apirunner)

</div>
