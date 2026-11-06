# CommerceVideoHub

Windows 本地 Web 工程，当前只有 G0 源码/授权审计与 G1 骨架。没有登录、导入、商品管理或视频发布功能。抖音、快手、视频号优先，淘宝/京东/多多后续。

## 启动

需要 Python3.11（uv 可自动准备）、uv、Node.js>=22.12（含npm）。运行测试还需要本机 Google Chrome。首次安装依赖需联网，浏览器平台登录和真实发布不在本轮范围。

```powershell
cd D:\CommerceVideoHub
powershell -NoProfile -ExecutionPolicy Bypass -File .\start.ps1
```

脚本检查依赖、`uv sync --frozen`、初始化当前用户/SYSTEM 专有 runtime ACL、运行 Alembic、按 package-lock 安装依赖并构建前端，健康检查通过后输出并打开 http://127.0.0.1:8765。按 Ctrl+C 停止脚本及其服务。不会更改系统级执行策略。端口被占用时失败，不复用未知服务。

`-NoBrowser` 不打开窗口；`-PrepareOnly` 仅安装/迁移/构建。后端统一托管前端，无需第二个发布引擎。首次运行下载的是开发依赖，不会自动下载平台浏览器或访问平台。

本机工具兼容：若 PATH 无 node，environment.ps1 可使用现有 Codex runtime Node；若无 npm，使用本轮准备的 `.tools/package/bin/npm-cli.js` (11.6.2)。`.tools` 不进 Git，换机器请安装标准 Node+ npm。没有工具时脚本明确报错，不假装已启动。

## 验证

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\test.ps1
# 启动脚本本身：连续两次启动/退出、监听地址和 runtime ACL 检查
powershell -NoProfile -ExecutionPolicy Bypass -File .\tests\start_smoke.ps1
# 只执行单测/类型/构建；跳过浏览器必须明确记录未验收：
powershell -NoProfile -ExecutionPolicy Bypass -File .\test.ps1 -SkipBrowser
```

独立命令：`.venv\Scripts\python -m pytest -q`、`.venv\Scripts\python -m mypy`；前端目录 `npm run typecheck`、`npm run build`；根目录 `.venv\Scripts\python tests/e2e.py`。E2E 自建一次性 SQLite 和回环服务，Chrome 全新上下文，检查六菜单/刷新、健康接口、mock断连；不读取真实账户。

前端开发可用 `npm run dev`（127.0.0.1:5173），API代理到8765。健康接口 `/api/health` 检查数据库迁移/WAL/外键；`/api/platforms` 六平台均 unsupported/manual_required。

## 目录与边界

- `app/backend`：API、类型契约、纯状态策略、SQLAlchemy表定义和静态迁移。
- `app/frontend`：六个空白功能入口；不显示虚假完成数据。
- `tests`：新工程测试；`docs/test-logs`：真实运行结果。
- `refs`：仅指向用户原解压仓库的 junction。移动原目录将使引用失效，不影响应用启动；审计需恢复来源。不得修改/发布参考目录。
- `runtime`：本机私有目录（数据库/媒体/profile/log预留），严格Git忽略、不经HTTP暴露。不得手动放入代码库或上传真实凭证。

审计入口：[源码](docs/SOURCE_AUDIT.md)、[许可](docs/LICENSE_AUDIT.md)、[能力](docs/PLATFORM_CAPABILITIES.md)、[决策](docs/DECISIONS.md)、[ER](docs/DATA_MODEL.md)、[状态机](docs/STATE_MACHINE.md)、[测试](docs/TEST_REPORT.md)。

实际测试机器是 Windows10 Pro；Win11 验收未完成。真实三平台上传与商品精确关联均未验证；必须获得测试账户和商品后逐个平台验收。下一阶段先做 G2 最小媒体与商品映射，不启动真实发布。
