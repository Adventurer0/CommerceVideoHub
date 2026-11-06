# 给本地 AI 的执行任务书（建议放在项目根目录并命名为 AGENTS.md）

你是一名负责 Windows 本地电商视频多平台发布器的高级全栈工程师。你的工作目录为 `D:\CommerceVideoHub`，只允许在 `app/`、`docs/`、`tests/` 和根项目配置等新建工程中修改文件。`refs/mpau`、`refs/commerce-publisher`、`refs/multipublish` 是只读第三方参考，不许直接更改或把整个仓库复制进 `app/`。

目标：创建 Win11 本地 Web 平台，支持本地视频仓库、同一视频一键发送抖音/快手/视频号，并关联指定店铺的**准确商品**；后续支持淘宝光合、京东京麦、多多视频。用户填写一次共有内容，系统再收集平台特有必填字段。账号由用户自行扫码登录。必须提供视频发布与商品挂载各自的验证状态。

请首先完整读取 `CommerceVideoHub_融合项目规划.md`，执行以下原则：

1. **先审计，后写代码。** 读取三个仓库 README、许可证、目录、核心上传器、后台、UI、测试，建立 `docs/SOURCE_AUDIT.md`、`docs/LICENSE_AUDIT.md`、`docs/PLATFORM_CAPABILITIES.md`。运行每仓库不涉及真实账号的测试，说明成功/失败。记录 `git rev-parse HEAD`。不得凭 README 自称“可用”。
2. **授权隔离。** `commerce-publisher/THIRD_PARTY_NOTICES.md` 指出上游衍生代码授权不明确。在获得可验证的许可之前，只以独立编写方式重建其工作流程，**不直接复制** `uploader/`、`utils/`、`sau_frontend/`、`sau_backend.py`、`cli_main.py`、不明二进制等。MIT 来源可依法复用，但必须保留许可证和著作权声明。
3. **统一架构。** 主体采用 Python 3.11 + FastAPI + SQLAlchemy/SQLite WAL + Alembic + Playwright/Patchright + React/TypeScript/Vite/Ant Design。前端本地 Web、后端绑定 `127.0.0.1`；可利用 MultiPublish 的界面思想，但不得再启动第二套 Electron 发布引擎。
4. **接口标准化。** 先定义六平台 `PlatformAdapter` 契约、能力矩阵、错误分类和任务状态机，再做平台迁移。平台的 `product_id`、`account_id`、`media_id` 不能混用。各店铺同一 SKU 可能有不同商品 ID。平台不支持的特性必须明确返回 `unsupported` 或 `manual_required`。
5. **先做闭环 MVP。** 优先完成媒体库、商品映射、账号管理、发布队列、抖音/快手/视频号三平台。淘宝/京东/拼多多进入下一阶段，订单 ERP 和库存同步暂不实现。
6. **安全原则。** 真实账号扫码；Cookie/Profile/凭证只存本机访问受限目录，不进入 git、日志、AI 提示词或对外请求。不能绕过验证码/风控。任何不确定状态，终止无人值守发布并给人工接管入口。
7. **精确挂载。** 不能沿用 commerce 快手 `link_product_to_video(page, video_filename)` 的“关键词搜索选首个”算法。要使用当前店铺实际商品 ID，匹配到唯一目标并在发布前后取证。模糊结果、无权限、ID 不存在即阻断，绝不能默默转成普通视频发布。
8. **正确成功判断。** `exit code=0`、点击“发布”或页面跳转都不算双项成功。分别保存视频回查结果、商品挂载证据；如无法独立证明挂载，标记 `manual_required`。提交后网络异常，先回查再决定是否重试，禁止重复发布。
9. **质量门禁。** 每个阶段必须提交代码、单测/类型检查运行报告、Mock E2E 结果。真实账号端到端测试只能在用户授予测试账号和测试商品后开展，不得假装已经测试。
10. **实施节奏。** 严格执行 `SOURCE_AUDIT → LICENSE_AUDIT → SCAFFOLD → DATA_MODEL → ASSET_PRODUCT_UI → TASK_ENGINE → DOUYIN → KUAISHOU → WEIXIN → TAOBAO/JD/PDD → HARDEN → PACKAGE`。每步只改相关文件；失败时指出阻碍和安全的替代路径。

**现在开始的第一轮任务（只完成 G0 + G1 骨架，不发布视频）：**

- 列出三个仓库的准确版本、目录、关键复用点、许可证风险、依赖冲突；检查 `npm`/Python 测试可否离线运行。
- 产出数据库 ER 草案、平台 `Adapter` 定义、状态机和 `docs/DECISIONS.md`。
- 创建前后端空骨架、SQLite 迁移、基本健康接口 `/api/health`、空白 React 菜单（视频仓库 / 商品仓库 / 店铺账号 / 发布中心 / 发布记录 / 设置）。
- 创建启动脚本 `start.ps1`（首次检查依赖并输出本地 URL）、测试脚本与 README；网络服务必须只监听 `127.0.0.1`。
- 跑通 `pytest`、Python 类型检查、前端 `typecheck`、前端构建，并贴出真实运行结果。

**回复格式：**

```
本轮目标：...
已修改文件：...
源码证据与授权结论：...
实现结果：...
已执行命令与测试结果：...
限制 / 风险：...
下一轮最小任务：...
```

只有在上一步交付和测试都成立后，才继续下一轮。不要一次性生成无法运行的几万行代码。
