APIRunner (MVP)

Minimal HTTP API test runner with a YAML DSL, HttpRunner-style ${...} templating, JMESPath extraction, baseline assertions, and JSON/JUnit/HTML reports.

Quickstart
- Create `.env` from `.env.example` and set BASE_URL and credentials.
- Put YAML tests in `testcases/` (HttpRunner 命名规范：`test_*.yaml`)。
- Run: `arun run testcases --env-file .env --report reports/run.json --junit reports/junit.xml --html reports/report.html`.

CLI
- `arun run <path>`: Run a file or directory of YAML tests
  - Options: `-k <expr>` tag filter, `--vars k=v` (repeatable), `--failfast`, `--report <file>`, `--junit <file>`, `--html <file>`, `--log-level info|debug`, `--env-file <path>`
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
  - `extract?` (dict var -> jmespath on response body)
  - `validate?` (list of `[check, comparator, expect]`)
  - `skip?` (bool|string)
  - `retry?` (int), `retry_backoff?` (float seconds)

Comparators
- `eq, ne, contains, not_contains, regex, lt, le, gt, ge, len_eq, in, not_in`

Project Layout
- `apirunner/` core package
- `testcases/` YAML testcases (HttpRunner 风格 `test_*.yaml`)
- `testsuites/` YAML testsuites（可选，`suite_*.yaml`）
- `reports/` output folder (created at runtime)
- `spec/openapi/ecommerce_api.json` API doc (reference only)
- `spec/postman/HC-UDI.postman.json` Postman collection (reference only)

变量与函数（语法约定）
- 系统/环境变量仅允许通过 `ENV` 读取：`${ENV(KEY)}`，例如 `base_url: "${ENV(BASE_URL)}"`、`${ENV(USER_USERNAME)}`。
- 调用辅助函数：`${sum_two_int(1, 2)}` 或 `{{ sum_two_int(1, 2) }}`。
- 同时兼容 HttpRunner 风格的 `${func()}` 与 `$var` 到 Jinja2 的转换。

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
