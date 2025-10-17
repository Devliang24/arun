# 格式转换实战：导入期脱敏与生成 Testsuite

本节演示如何将已有资产（cURL/HAR/Postman/OpenAPI）快速转换为 ARun 可运行用例，并在“转换阶段”完成敏感信息脱敏、变量占位与 testsuite 生成，形成可持续维护的资产库。

## 快速命令清单

- cURL → 用例（带脱敏与占位）
  - `arun convert sample.curl --outfile testcases/from_curl.yaml --redact Authorization,Cookie --placeholders`
- HAR → 用例（过滤静态资源，仅保留 2xx，按正则排除）
  - `arun convert recording.har --exclude-static --only-2xx --exclude-pattern '(\.png$|/auth/)' --outfile testcases/from_har.yaml`
- Postman → 用例（导入环境变量、拆分多文件、生成 testsuite、脱敏/占位）
  - `arun convert collection.json --postman-env postman_env.json --split-output --suite-out testsuites/testsuite_postman.yaml --redact Authorization --placeholders`
- OpenAPI → 用例（按 tag 过滤、输出多文件、脱敏/占位）
  - `arun convert openapi spec/openapi.yaml --tags users,orders --split-output --outfile testcases/from_openapi.yaml --redact Authorization --placeholders`

> 提示：`.json` 文件如果包含 `openapi` 字段，`arun convert` 会自动走 OpenAPI 流程；否则默认按 Postman Collection 解析。

---

## 导入期脱敏与变量占位（--redact / --placeholders）

- `--redact Header1,Header2`：将指定头部的值在生成的 YAML 中替换为 `***`，避免敏感信息落盘。
- `--placeholders`：将敏感头或鉴权信息提取为 `config.variables`，并把请求中的实际值替换为 `$var`（如 `Authorization: Bearer $token`）。
  - 优先处理 `Authorization: Bearer <token>` → 写入 `variables.token`。
  - 其他敏感头（如 `X-API-Key`）→ 写入 `variables.x_api_key`。
  - Basic 鉴权的 `username/password` 会被占位为 `$username/$password`。

两种方式可叠加使用；只开启 `--placeholders` 时未显式指定的敏感头会使用默认清单（Authorization/Cookie/API-Key）。

---

## Postman 高保真导入

- `--postman-env postman_env.json`：导入 Postman 环境变量；`{{var}}` 会自动转换为 `$var` 并写入 `config.variables`。
  - 如果没有环境文件，可省略该参数；CLI 会照常转换（此时仅使用 Collection 自带的变量定义）。
- 鉴权映射：
  - Bearer → `auth: { type: bearer, token: $token }`
  - Basic → `auth: { type: basic, username: $username, password: $password }`
  - API Key（in: header）→ 直接写入 `headers`（支持占位）
- 目录到 testsuite：`--split-output` + `--suite-out testsuites/testsuite_postman.yaml` 会生成引用式 testsuite，保留每条请求为独立 case 文件，suite 中统一引用。

示例：

```bash
arun convert collection.json \
  --postman-env postman_env.json \
  --split-output \
  --suite-out testsuites/testsuite_postman.yaml \
  --redact Authorization,Cookie \
  --placeholders
```

无环境文件的等价示例：

```bash
arun convert collection.json \
  --split-output \
  --suite-out testsuites/testsuite_postman.yaml \
  --redact Authorization,Cookie \
  --placeholders
```

---

## HAR 录制治理

- `--exclude-static`：过滤 image/css/js/font 等静态资源（默认开启，可用 `--keep-static` 保留）。
- `--only-2xx`：仅保留 2xx 响应，去掉跳转/错误请求。
- `--exclude-pattern REGEX`：按 URL 或 `mimeType` 进行正则排除。

示例：

```bash
arun convert recording.har \
  --exclude-static \
  --only-2xx \
  --exclude-pattern '(\\.png$|/cdn/|/auth/)' \
  --outfile testcases/from_har.yaml
```

---

## cURL 解析增强

- `-G/--get` + `--data/--data-urlencode`：自动合并到查询参数 `params`。
- `-F/--form`：支持 multipart；`file=@path` → `files`，其他键值 → `data`。
- `-b/--cookie`：合并为 `Cookie` 请求头。

示例：

```bash
arun convert curl.txt --outfile testcases/from_curl.yaml --redact Authorization --placeholders
```

---

## OpenAPI 转换

- 自动从 `servers` 推断 `base_url`；
- 支持 `--tags users,orders` 筛选 operation；
- 当 `requestBody` 的 `application/json` 包含 `example/示例` 时，会生成示例 `body`；
- 支持 `--split-output` 将每个 operation 生成为独立 case 文件。

示例：

```bash
arun convert openapi spec/openapi/ecommerce_api.json \
  --tags users,orders \
  --split-output \
  --outfile testcases/from_openapi.yaml \
  --redact Authorization \
  --placeholders
```

---

## 转换输出与合并策略

- `--outfile file.yaml`：将所有请求写入一个 Case。
- `--split-output`：每条请求写入独立 YAML（命名按原始顺序递增）。
- `--into existing.yaml`：将生成的步骤追加到现有用例（Case 或 Suite），便于持续扩充单一 case。

> 注意：`--split-output` 与 `--into` 不可同时使用。
