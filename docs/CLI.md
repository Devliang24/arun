# 🛠 命令行工具（CLI）

本页汇总 `arun` 常用子命令与选项。

## arun run

运行测试用例（Case）：

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

示例：

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

## arun check

验证 YAML 语法和风格：

```bash
arun check testcases
arun check testcases/test_login.yaml
```

检查项：
- YAML 语法错误
- 提取语法（必须使用 `$` 前缀）
- 断言目标（`status_code`、`headers.*`、`$.*`）
- Hooks 函数命名规范
- 步骤间空行（可读性）

## arun fix

自动修复 YAML 风格问题：

```bash
arun fix testcases
arun fix testcases testsuites examples
arun fix testcases --only-spacing
arun fix testcases --only-hooks
```

修复内容：
- 将 suite/case 级 hooks 移到 `config.setup_hooks/teardown_hooks`
- 确保 `steps` 中相邻步骤之间有一个空行

<a id="format-conversion"></a>
## arun convert - 智能格式转换

将 cURL、Postman、HAR、OpenAPI 转为 ARun YAML 的统一入口。无需记忆多个子命令，`arun convert` 自动识别文件格式（`.curl`/`.har`/`.json`）；对 `.json` 自动区分 OpenAPI（检测 `openapi` 字段）与 Postman。

```bash
# 合并多个 cURL 为单个测试用例（Case）
arun convert requests.curl --outfile testcases/imported.yaml

# 拆分每条 curl
arun convert requests.curl --split-output

# 直接从标准输入读取
curl https://api.example.com/users | arun convert -

# 导入 Postman Collection
arun convert collection.json --outfile testcases/postman_suite.yaml

# 导入 HAR（可拆分）
arun convert recording.har --split-output

# OpenAPI 3.x → 测试用例（Case）（按 tag 过滤，拆分输出）
arun convert openapi spec/openapi/api.json --tags users,orders --split-output

# 追加到现有 YAML
arun convert new_requests.curl --into testcases/test_api.yaml

# 自定义用例信息
arun convert requests.curl \
  --case-name "API 测试套件" \
  --base-url https://api.example.com \
  --outfile testcases/test_suite.yaml
```

选项说明：
- `--outfile`：写入指定文件（默认 stdout）
- `--split-output`：为每个请求生成独立 YAML（与 `--into` 互斥）
- `--into`：追加到已有 YAML 文件
- `--case-name`：指定用例名称（默认 "Imported Case"）
- `--base-url`：覆盖或设定 `base_url`

特性与提示：
- 自动解析方法、URL、headers、query、body，并添加基础断言
- 支持从 stdin 读取（使用 `-`）；拆分模式下默认生成 `imported_step_<n>.yaml`
- 支持 curl 片段、Postman Collection、浏览器/抓包 HAR 记录、OpenAPI 3.x 规范文档
- OpenAPI 转换支持 `--tags` 过滤、`--split-output` 拆分输出、`--redact` 脱敏、`--placeholders` 变量占位

## arun export - 导出为 cURL

将 YAML 用例导出为 cURL，便于调试与分享。

```bash
arun export curl testcases/test_api.yaml
arun export curl testcases/test_api.yaml --outfile requests.curl
arun export curl testcases/test_api.yaml --one-line
arun export curl testcases/test_api.yaml --steps "1,3-5"
arun export curl testcases/test_api.yaml --with-comments
arun export curl testcases/test_api.yaml --redact Authorization,Cookie
arun export curl testcases --outfile all_requests.curl
arun export curl testsuites/testsuite_smoke.yaml --case-name "健康检查"
```

选项说明：
- `--outfile FILE`：输出到文件（默认 stdout）
- `--multiline` / `--one-line`：多行或单行格式
- `--steps "1,3-5"`：导出指定测试步骤（Step）（支持范围）
- `--with-comments`：添加 `# Case/Step` 注释
- `--redact HEADERS`：脱敏指定头部，如 `Authorization,Cookie`
- `--case-name NAME`：仅导出匹配的测试用例（Case）
- `--shell sh|ps`：行延续符风格（sh: `\`，ps: `` ` ``）

导出特性：
- 自动渲染变量与环境变量（读取 `.env`）
- 使用 `--data-raw` 确保 JSON 载荷不被修改
- JSON 自动格式化（indent=2）
- 自动添加 `Content-Type: application/json`（当 body 为 JSON 时）
- 智能 HTTP 方法处理（POST 有 body 时省略 `-X POST`）
- 支持复杂请求（params、files、auth、redirects）
