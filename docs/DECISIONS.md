# G1 技术决策（2026-11-06）

1. **范围**：G0 审计和 G1 骨架；账户扫码、CRUD、worker、发布、商品查找均不实现。预先交付 G3 要用的类型和纯状态策略，不把 G3 标为完成。遵循规划表 G0-01 至 G1-04；Windows 11 仍待目标机器验收，当前机器实际 Windows 10 Pro 10.0.19045。
2. **独立工程**：D:\CommerceVideoHub；原始规划复制为根配置，第三方仅 junction 引用并忽略；所有 app 业务实现独立编写。审计工具不属于运行时发布引擎。
3. **单引擎**：Python3.11/FastAPI、SQLAlchemy2 Core 类型化表定义、Alembic、SQLite WAL。后续只用 Python Playwright（可评估 Patchright）；不导入/互转 Electron session、Chrome CDP 与旧 Cookie。当前没有浏览器账户存储操作。
4. **前端**：React/TypeScript/Vite/Ant Design。六个菜单使用 hash 路由，刷新能保留页面。正式启动由 FastAPI 同源托管构建产物，只有 127.0.0.1:8765 一个监听；开发 Vite 限定 127.0.0.1:5173，preview 限定 127.0.0.1:4173。没有宽泛 CORS；Host 限制防止任意域名访问；G1 没有写业务 API。
5. **迁移**：静态版本 0001，独立于当前模型；显式 upgrade 而非 API 隐式 create_all。health 实际读迁移版本、WAL 和外键开关，不把 HTTP 运行当数据库可用。版本不符返回503。upgrade 幂等、downgrade/re-upgrade 在一次性测试库验收。
6. **身份**：所有远端 ID 按不透明字符串保存，包括前导零；AccountId/MediaId/ExternalProductId/JobId 分离类型。一个 shop_accounts 对应一个平台店铺，唯一(platform,shop_id)。同 SKU 每店一个映射；任务 mapping_id+account_id 复合外键防跨店绑定。若未来需同店多操作员，增加独立 shop 实体迁移，不能复用账户主键冒充商品。
7. **草稿和幂等**：publish_drafts.id 作为 content_id，版本需将来由服务冻结；jobs 唯一(draft_id,account_id,publish_version) 和 idempotency_key 双约束。target_snapshot 为提交时快照，防未来映射修改影响回查；G1 尚不实施快照写入业务和并发串行锁。
8. **证据**：publish_evidence 按 kind=post/product 分行保存独立状态及观察时间，容许一次任务多次回查。success 的纯函数要求同任务、同平台/账户/店铺、同 post_id 和准确 product_id 的两份验证证据。DB 的检查约束只保底，实际证据采集和持久化事务在 G3/G4 实现。禁止把单次 bool、退出码或 UI 跳转当最终成功。
9. **错误和未知**：见 STATE_MACHINE.md；提交后失败不能进入自动重发；unknown 只能回查或人工处理。G1 无后台队列，也无重试按钮，不能产生真实发布。
10. **私有数据**：start.ps1 初始化 runtime DACL，仅当前用户和 SYSTEM 完全控制，子目录继承。runtime/profiles、media、logs 等全部 Git 忽略，不通过静态服务暴露；只托管 frontend/dist。stdout/stderr 禁访问日志，后续账号相关日志必须独立脱敏。G1 未处理任何真实凭证，ACL 不等于未来完整安全验收。
11. **可复现依赖**：uv.lock + npm package-lock；首次依赖准备允许联网，已准备后运行与测试无需平台网络。uv sync --frozen；Node>=22.12，当前实测24.19.0。环境无 PATH 中 npm，当前工具脚本兼容本机 Codex Node + 工程 .tools npm；普通机器推荐安装 Node LTS（含 npm）和 uv。浏览器 E2E 使用本机 Chrome 的临时新上下文，与用户登录态无关。
12. **验收**：单测/类型/构建、真实本地 HTTP 和浏览器菜单验收，以及 mock API 断连；均不能替代真实平台视频与商品验证。不能更改第三方源码消除其 Windows 失败。
