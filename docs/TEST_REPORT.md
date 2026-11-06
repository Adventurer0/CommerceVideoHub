# G0 / G1 真实测试报告

执行日期：2026-11-06（Asia/Shanghai）。本轮停止在 G1，不登录账号、不发布视频。

## 验收结论

- **G0 审计交付完成**：三个来源、归档提交提示、SHA、目录/源码/授权/依赖/离线测试均记录。上游测试失败作为审计发现保留，不能称三个参考项目都可用。
- **G1 实现和本机检查通过**：API、六菜单、迁移、类型契约、状态守卫和启动/退出均实测。**规划表要求的 Win11 验收仍未完成**：这台机器实际是 Windows10 Pro 10.0.19045。不能把整项 Win11 验收标为完成。
- **真实平台闭环：未执行、未验收**。六平台当前均禁用，尚无精确商品选择器、队列或账号扫码功能。

## 环境

Python 3.11.15（本轮通过 uv 准备）；uv 0.10.9；Node 24.19.0（本机 Codex runtime）；npm 11.6.2（工程 .tools）；Chrome 156.0.8078.80（临时测试上下文）。

新工程解析版本：FastAPI0.162.0、SQLAlchemy2.0.57、Alembic1.20.1、Uvicorn0.54.0、Pytest8.4.2、Mypy1.20.2、Playwright1.64.1、Vite7.3.7。完整可复现版本见 uv.lock、app/frontend/package-lock.json；参考项目隔离环境见 [audit-environment.txt](test-logs/audit-environment.txt)。

## G0 命令与结果

| 实际命令/检查 | exit | 结果与实际范围 |
|---|---|---|
| 三目录 `git -C <source> rev-parse HEAD` | 各128 | ZIP 解压无.git，不能取得 HEAD；改存 ZIP 注释提交提示和完整字节哈希 |
| `.venv/Scripts/python app/scripts/audit_sources.py` | 0 | 83 / 157 / 31 文件和归档逐字节匹配；审计后复跑无变更 |
| `uv pip install --offline --python .audit-venv/Scripts/python.exe pytest pytest-asyncio -r refs/mpau/pyproject.toml` | 1 | pytest 缓存缺失，初始环境无法离线安装；[日志](test-logs/refs-python-offline.txt) |
| `.audit-venv/Scripts/python app/scripts/audit_python.py mpau` | 0 | **9 passed**，1个原代码无效转义 DeprecationWarning；参数解析/Mock dispatch；[日志](test-logs/mpau-tests.txt) |
| `.audit-venv/Scripts/python app/scripts/audit_python.py commerce-publisher` | 2 | **4 collection errors**：browser_manager、pdd_reliability、publish_plan、publish_verify 导入 fcntl 失败；[日志](test-logs/commerce-tests.txt) |
| 同脚本 + `test_adapters.py test_account_label.py test_product_metadata.py test_xhs_account_config.py test_upstream_binary.py` | 1 | **27 passed, 1 failed**：`test_cli_adapter_builds_real_connector_command` 的 /usr/bin/python3 与 Windows反斜杠路径断言冲突；未修改上游；[日志](test-logs/commerce-subset.txt) |
| `node .tools/package/bin/npm-cli.js --prefix refs/multipublish test` | 0 | **10 passed**：持久化恢复、FFmpeg路径、标题候选、超时；未启动Electron/FFmpeg/平台；[日志](test-logs/multipublish-test.txt) |
| `node .tools/package/bin/npm-cli.js --prefix tests/audit-install/multipublish ci --offline --ignore-scripts --no-audit --no-fund` | 1 | **ENOTCACHED**，zustand 包未缓存；仅在测试目录复制包描述/锁进行检测，未往refs安装；[日志](test-logs/multipublish-offline-install.txt) |

commerce Web 未提供 npm test 脚本；MPAU 无独立 npm 项目。MultiPublish完整 typecheck/打包依赖未离线准备成功，未宣称完成。离线“执行测试”和离线“首次装依赖”分别记录。

Python 审计 runner 禁写 pycache/pytest cache，日志及运行目录转临时路径，阻断非回环socket和真实子进程。允许Windows asyncio内部回环 socketpair。未伪造 fcntl、未修补上游算法。二进制测试仅读取哈希，不运行exe。

## G1 命令与结果

最终完整命令：`powershell -NoProfile -ExecutionPolicy Bypass -File ./test.ps1`，exit **0**。[完整原始输出](test-logs/g1-final-checks.txt)。

| 子检查 | 结果 | 证据覆盖 |
|---|---|---|
| `python -m pytest -q` | **33 passed, 1 warning in 0.65s** | 新库迁移、重复upgrade、降级/再升级、WAL/FK、跨店铺复合外键、前导零ID、映射唯一性、重复发布双约束、分项证据约束、六个禁用adapter、证据身份匹配、unknown不可重发、API健康/503/Host拒绝/无发布API |
| `python -m mypy` | **Success: no issues found in 10 source files** | 后端严格类型检查，静态生成迁移在配置中排除 |
| `npm run typecheck` | **exit0** | TypeScript严格检查 |
| `npm run build` | **exit0** | Vite7.3.7，1534模块；主JS4.03KB、vendor240.19KB、antd315.31KB（未压缩传输体积） |
| `python tests/e2e.py` | **exit0** | 真实本机HTTP health；Chrome访问构建产物；六菜单逐项点击/刷新；无发布按钮；Mock503正确显示断连；0 pageerror；正常退出清理 |
| `powershell ... -File ./start.ps1 -PrepareOnly` | **exit0** | 首次依赖检查/安装、权限初始化、迁移和构建；[日志](test-logs/start-prepare.txt) |
| `powershell ... -File ./tests/start_smoke.ps1` | **exit0** | 实际start.ps1连续两次启动/退出；HTTP200；Get-NetTCPConnection证明仅127.0.0.1:8765；退出无残留监听；当前用户/SYSTEM专有ACL；[日志](test-logs/g1-startup.txt) |
| Alembic `command.check(Config('alembic.ini'))` | **exit0** | `No new upgrade operations detected.`；最终模型/迁移无漂移 |

浏览器截图已人工查看：[UI_SMOKE.png](UI_SMOKE.png)。Mock E2E 只指骨架/本地服务场景，没有伪造真实发布成功。

警告：Starlette当前版本提示 TestClient 的 httpx 集成将弃用（建议httpx2），单测目前通过；未通过屏蔽警告制造全绿。首次构建的AntD `use client` 提示针对服务组件指令，本项目是纯客户端SPA；最终构建仅过滤这一条已知无关警告，按vendor/antd拆包后无大包警告。

## 本轮发现并修复

1. 审计日志导入会写参考目录：通过运行时配置重定向临时目录，并以完整源哈希复核；关闭loguru句柄后清理。
2. 首次审计隔离阻断了Windows asyncio内部回环 socketpair：仅放行回环并仍禁真实子进程，原9测试通过；不是上传器修复。
3. 首次G1 E2E界面检查通过，但强制退出后SQLite shm清理 PermissionError导致进程exit1。改为本机stop flag驱动Uvicorn正常退出，等待连接dispose，复跑完整E2E exit0；保留事实，不把首次失败称通过。
4. 初始迁移的两个映射唯一约束自动命名重复：改为不同显式名称。在确认开发库八表全空后重建初始开发库，执行漂移检查通过；最终单测使用最终静态迁移。

## 下一步门禁

先在目标Win11机器执行 test.ps1 与 tests/start_smoke.ps1，记录系统版本和结果，补齐 G1-02/G1-04目标系统验收；本轮不推进 G2。之后最小G2任务为内部SKU/店铺商品映射与媒体导入的一小条可测路径。扫码及真实发布要另外取得测试账号/商品授权，逐平台先抖音、再快手、再视频号。
