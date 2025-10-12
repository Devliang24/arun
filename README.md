APIRunner (MVP)

Minimal HTTP API test runner with a YAML DSL, HttpRunner-style ${...} templating, JMESPath extraction, baseline assertions, and JSON/JUnit/HTML reports.

Quickstart
- Create `.env` from `.env.example` and set BASE_URL and credentials.
- Put YAML tests in `testcases/` (HttpRunner 命名规范：`test_*.yaml`)。
- Run: `arun run testcases --env-file .env --report reports/run.json --junit reports/junit.xml --html reports/report.html`.
- Validate YAML (no execution): `arun check testcases`。

CLI
- `arun run <path>`: Run a file or directory of YAML tests
  - Options: `-k <expr>` tag filter, `--vars k=v` (repeatable), `--failfast`, `--report <file>`, `--junit <file>`, `--html <file>`, `--log-level info|debug`, `--env-file <path>`, `--log-file <file>`, `--httpx-logs/--no-httpx-logs`, `--reveal-secrets/--mask-secrets`
    `--log-file <file>` 指定日志文件路径（默认 `logs/run-<timestamp>.log`）；`--httpx-logs/--no-httpx-logs` 控制是否显示 httpx 内建请求日志（默认关闭）。
  - File naming (默认仅收集以下命名)：
    - 位于目录 `testcases/` 或 `testsuites/` 下的 `.yml|.yaml` 文件；或
    - 文件名以 `test_`（用例）或 `suite_`（套件）开头。
  - 环境变量（与 HttpRunner 风格一致）：
    - `--env <name>`（预留）：会从 `envs/<name>.yaml | environments/<name>.yaml | env/<name>.yaml` 读取环境配置（支持 `variables/base_url/headers`）。也支持单文件 `env.yaml` 按名称分节。
    - `--env-file <path>`：可读取 `KEY=VALUE` 的 `.env` 或 YAML 文件；与 `--env` 结果合并。
    - 自动合并系统环境变量（`ENV_*`、`BASE_URL`）。
    - 合并顺序：命名环境 < `--env-file` < OS 环境 < `--vars`（最高）。

DSL (YAML)
- config: `name?`, `base_url?`, `variables?`(dict), `headers?`(dict), `timeout?`(float), `verify?`(bool), `tags?`(list)
- parameters?:
  - enumerate: list of dicts: `[{a:1,b:2},{a:3,b:4}]`
  - matrix: dict of lists: `{a:[1,3], b:[2,4]}`
- steps[]:
  - `name`
  - `variables?` (dict)
  - request: `method`, `url`, `params?`, `headers?`, `json?`, `data?`, `files?`, `auth?` (basic|bearer), `timeout?`, `verify?`, `allow_redirects?`
  - `extract?` (dict var -> `$` 表达式，仅支持 `$` 语法)
- `validate?` (list of comparator entries，如 `- eq: ["status_code", 200]`；`check` 支持 `$` 语法)
  - `setup_hooks?` (list[string]，在发送请求前调用 hooks 函数)
  - `teardown_hooks?` (list[string]，在收到响应后调用 hooks 函数)
  - `skip?` (bool|string)
  - `retry?` (int), `retry_backoff?` (float seconds)

Comparators
- `eq, ne, contains, not_contains, regex, lt, le, gt, ge, len_eq, in, not_in`

Checks 与 Extract 语法
- Extract 仅支持 `$` 开头（HttpRunner 风格）：
  - `$.data.access_token`, `$[0].id`
  - 特殊：`$headers.Content-Type`、`$status_code` 也可用于提取请求头/状态码
- Check（断言）规范（单一格式）：
  - 写法：`- <comparator>: ["<check>", <expect>]`
    - 例如：`- eq: ["status_code", 200]`
  - 状态码与请求头不需要 `$`：`status_code`、`headers.Content-Type`
  - 响应体字段使用 `$`：`$.data.id`、`$[0].name`
- 不再支持 `body.foo.bar` 写法，请统一使用 `$` 语法（如 `$.foo.bar`）

Hooks（函数钩子）
- 放置在 `arun_hooks.py` 的可调用函数会被自动加载。
- 在步骤级支持：`setup_hooks`（请求前）、`teardown_hooks`（响应后）。
- 签名约定（按需实现其中任意参数，未用可省略）：
  - setup: `def my_setup(request: dict, variables: dict, env: dict) -> dict | None`
    - 可原地修改 `request`（如加签、补 headers）；返回的 dict 会合并进运行变量（供后续步骤使用）。
  - teardown: `def my_teardown(response: dict, variables: dict, env: dict) -> dict | None`
    - 可检查响应（抛异常使步骤失败）；返回的 dict 会合并进运行变量。
- YAML 示例：
  ```yaml
  steps:
    - name: signed request
      setup_hooks: [setup_hook_sign_request]
      request:
        method: GET
        url: /secure
      teardown_hooks: [teardown_hook_assert_status_ok]
  ```
- API Key 注入示例：
  ```yaml
  steps:
    - name: with api key
      setup_hooks: [setup_hook_api_key]
      request:
        method: GET
        url: /debug/info
  ```

- 表达式 Hooks 示例：
  ```yaml
  steps:
    - name: expr style
      setup_hooks: ["${setup_hook_sign_request($request)}"]
      request:
        method: GET
        url: /debug/info
      teardown_hooks: ["${teardown_hook_assert_status_ok($response)}"]
  ```

- HMAC 加签示例：
  ```yaml
  steps:
    - name: hmac signed
      setup_hooks: [setup_hook_hmac_sign]
      request:
        method: GET
        url: /debug/info
      validate:
        - [status_code, eq, 200]
  ```
  需要在环境中提供 `APP_SECRET`（例如 `.env` 中设置 APP_SECRET=xxxx）。
 - Case/Suite 级 hooks：在 `cases[].setup_hooks/teardown_hooks` 与 suite 顶层的 `setup_hooks/teardown_hooks` 中声明，执行顺序：Suite.setup → Case.setup → Steps → Case.teardown → Suite.teardown。
 - 函数命名约定：
   - setup 函数需以 `setup_hook_` 开头，例如 `setup_hook_sign_request`
   - teardown 函数需以 `teardown_hook_` 开头，例如 `teardown_hook_assert_status_ok`
- 进阶：也支持表达式写法 `${setup_hook_sign_request($request)}` / `${teardown_hook_assert_status_ok($response)}`，但推荐使用“函数名字符串列表”形式。

Hooks 参考表（示例已内置于 `arun_hooks.py`）
- setup_hook_sign_request(request, variables, env) -> dict
  - 简单加签（X-Timestamp/X-Signature），返回 `{'last_signature': sig}`
- setup_hook_api_key(request, variables, env) -> None
  - 注入 `X-API-Key`，优先从 `env['API_KEY']`，否则 `variables['API_KEY']`
- setup_hook_hmac_sign(request, variables, env) -> dict
  - HMAC-SHA256 对 `METHOD|URL|TS` 签名，写入 `X-HMAC/X-Timestamp`，需要 `APP_SECRET`
- teardown_hook_assert_status_ok(response, variables, env) -> None
  - 若 `status_code` 非 200 抛异常
- teardown_hook_capture_request_id(response, variables, env) -> dict
  - 若响应体包含 `request_id`，写入变量 `{'request_id': ...}`

Project Layout
- `apirunner/` core package
- `testcases/` YAML testcases (HttpRunner 风格 `test_*.yaml`)
- `testsuites/` YAML testsuites（可选，`suite_*.yaml`）
- `reports/` output folder (created at runtime)
- `spec/openapi/ecommerce_api.json` API doc (reference only)
- `spec/postman/HC-UDI.postman.json` Postman collection (reference only)

变量与函数（语法约定）
- 系统/环境变量仅允许通过 `ENV` 读取：`${ENV(KEY)}`，例如 `base_url: "${ENV(BASE_URL)}"`、`${ENV(USER_USERNAME)}`。
- 调用辅助函数：仅支持 `${...}` 语法，例如：`${sum_two_int(1, 2)}`。
- 步骤内引用变量推荐使用 `$var` 简写，复杂表达式仍使用 `${...}`，禁用 `{{ ... }}`。

arun_hooks.py（辅助函数）
- 将 `arun_hooks.py` 放在用例同级或任意上级目录（就近优先），框架会自动加载其中的可调用对象并在模板中可用。
- 示例：
  ```py
  # arun_hooks.py
  import time, hashlib
  def ts():
      return int(time.time())
  def md5(s: str) -> str:
      return hashlib.md5(s.encode()).hexdigest()
  def sign(app_key: str, ts: int) -> str:
      return md5(f"{app_key}{ts}")
  def sum_two_int(a:int,b:int)->int:
      return a+b
  ```
  在 YAML 中：
  ```yaml
  config:
    base_url: "${ENV(BASE_URL)}"
  steps:
    - name: demo
      request:
        method: GET
        url: /ping?x=${sum_two_int(1,2)}
  ```
高级：通过环境变量 ARUN_HOOKS_FILE 指定自定义文件名（支持逗号分隔多个候选名），例如 `ARUN_HOOKS_FILE=custom_hooks.py`。
- 敏感信息显示
  - 默认明文显示敏感字段（`Authorization/password/*token*` 等），便于联调排查
  - 如需隐藏/脱敏输出，使用 `--mask-secrets`
