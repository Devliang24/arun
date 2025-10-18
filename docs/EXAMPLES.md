# 💻 实战示例

以下示例演示从登录流程、E2E 购物流程、参数化、请求签名 Hooks 到格式转换/导出等常见用法，以及测试套件（Testsuite，引用型）的组织方式。

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

> 说明：此示例使用了项目自带的 `uid()` 和 `short_uid()` 辅助函数（定义在根目录 `arun_hooks.py`），用于生成唯一的测试数据。

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

arun_hooks.py：

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

test_signed_api.yaml：

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

### 示例 5：格式转换与导出工作流

演示从浏览器/Postman 到 ARun YAML 的完整转换流程。

注意：`arun convert` 要求“文件在前，选项在后”，且不支持无选项转换（至少提供 `--outfile`/`--split-output`/`--redact`/`--placeholders` 等其一）。

#### 场景 1：从浏览器 HAR 快速生成测试

```bash
# 1. 在浏览器中操作（F12 开发者工具）
#    - 打开 Network 面板
#    - 执行业务操作（登录、下单等）
#    - 右键 → Save all as HAR with content

# 2. 导入为测试用例（Case，每个请求一个文件）
arun convert recording.har --split-output \
  --case-name "浏览器录制" \
  --base-url https://api.example.com

# 输出：
# [CONVERT] Wrote YAML for '浏览器录制 - Step 1' to recording_step1.yaml
# [CONVERT] Wrote YAML for '浏览器录制 - Step 2' to recording_step2.yaml
# ...

# 3. 运行测试验证
arun run recording_step1.yaml --env-file .env

# 4. 导出为 cURL 命令调试
arun export curl recording_step1.yaml --with-comments
```

#### 场景 2：Postman Collection 迁移

```bash
# 1. 从 Postman 导出 Collection（JSON 格式）

# 2. 转换为 YAML（合并为一个测试套件）
arun convert api_collection.json \
  --outfile testcases/test_api_suite.yaml \
  --case-name "API 完整测试"

# 3. 编辑 YAML 添加断言和提取逻辑
# （此时可以利用 ARun 的变量提取、参数化等高级特性）

# 4. 运行测试
arun run testcases/test_api_suite.yaml --env-file .env --html reports/report.html
```

#### 场景 3：cURL 命令转测试用例（Case）

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
arun convert api_requests.curl \
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
# 团队成员 A：创建测试用例（Case）
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

# 导出为 cURL 命令分享给团队成员 B
arun export curl testcases/test_new_feature.yaml \
  --outfile share.curl \
  --with-comments

# 团队成员 B：收到 cURL 命令后
# 方式 1：直接在终端执行验证
bash share.curl

# 方式 2：导入为自己的测试用例（Case）
arun convert share.curl --outfile my_tests/imported.yaml
```

工作流优势：
- 🚀 快速上手：从现有工具（浏览器、Postman）无缝迁移
- 🔄 双向转换：YAML ↔ curl 灵活互转
- 🧪 渐进增强：先导入基础用例，再添加断言、提取、参数化
- 👥 团队协作：通过 cURL 命令快速分享请求示例

---

## 🧩 测试套件（Testsuite，引用用例）

除内联的 Suite（在一个文件的 `cases:` 中直接编写多个用例）外，还支持“引用型 Testsuite”：在 `testsuites/` 目录下的 Testsuite 文件通过 `testcases:` 引用 `testcases/` 下的单用例文件，并可在条目级覆盖名称、注入变量或提供参数化。

示例（`testsuites/testsuite_smoke.yaml`）：

```yaml
config:
  name: 冒烟测试套件
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
  name: 回归测试套件
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
- Testsuite 文件与内联 Suite 文件可共存。推荐优先使用 Testsuite（引用型），Suite（内联型）作为兼容形式继续支持。
- 条目级 `variables` 覆盖用例 `config.variables`（优先级：Suite.config.variables < Case.config.variables < Item.variables < CLI/Step）。
- 条目级 `parameters` 会覆盖用例自带的参数化配置。
