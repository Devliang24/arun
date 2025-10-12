示例（Examples）

本目录包含一组最小可运行的示例，演示 APIRunner 的常见用法与新规范（Suite/Case 级 hooks 需写在 config 内）。

准备工作
- 复制 `.env.example` 为 `.env`，设置 `BASE_URL`；如需登录示例，请设置 `USER_USERNAME/USER_PASSWORD`，或使用“注册+登录”示例。

示例列表
- 用例级 hooks（写在 config 内）：`test_case_hooks.yaml`
  - 演示在用例的 `config.setup_hooks/config.teardown_hooks` 中声明 hooks。
  - 运行：`arun run examples/test_case_hooks.yaml --env-file .env`

- 套件级 hooks（写在 suite 的 config 内）：`suite_hooks.yaml`
  - 演示在套件的 `config.setup_hooks/config.teardown_hooks` 中声明 hooks；套件内的用例在各自 `config` 中声明用例级 hooks。
  - 运行：`arun run examples/suite_hooks.yaml --env-file .env`

- 提取 token 并自动注入 Authorization：`test_login_whoami.yaml`
  - 第一步登录提取 `token`，第二步访问 `GET /api/v1/users/me`；未手动写 `Authorization` 头，运行器会自动注入 `Bearer $token`。
  - 需要 `.env` 中存在有效账号。
  - 运行：`arun run examples/test_login_whoami.yaml --env-file .env`

- 自注册 + 登录 + whoami：`test_register_and_login.yaml`
  - 无需预置账号，示例自动注册随机用户并登录，再访问 `GET /api/v1/users/me`。
  - 运行：`arun run examples/test_register_and_login.yaml --env-file .env`

批量运行
- 运行整个示例目录：`arun run examples --env-file .env`

注意
- 若运行登录相关示例失败，请先检查 `.env` 的用户名/密码是否有效，或直接使用“自注册 + 登录”示例。

