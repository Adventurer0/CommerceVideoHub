# CommerceVideoHub｜多平台带货视频矩阵项目规划

> 版本：v0.1（方案 / 非已实现程序）  
> 基准日期：2026-11-06  
> 环境：Windows 11、本机离线保存素材与账号会话、本地 Web 管理界面  
> 开发方式：本地 AI 阅读三个仓库，在新的独立工作目录分阶段实现、测试、验收。

## 0. 核心结论

**不要把三个项目整体复制进一个工程。** 用 MPAU 的平台上传器作为主参考与可适配基础，用 `commerce-multi-platform-publisher` 的队列、商品映射、恢复、回查思路，用 MultiPublish 的 Windows 用户体验、账号管理与发布结果交互设计。全部通过统一 `PlatformAdapter` 契约连接。

必须把 **视频已发布** 与 **指定商品已正确关联** 拆成两个可验证结果。若平台不能可靠核验挂载，就只能显示“待人工核验”，不能将任务标为“带货发布成功”。对于平台安全验证、登录失效或不确定是否发布成功，停止自动重试，人工核查后再继续。

### 已核对的源码范围（非真实店铺验收）

| 仓库 | 已查看的关键源码 | 适合复用 | 不直接照搬的部分 |
|---|---|---|---|
| MPAU：`cjccd/multi-platform-auto-upload` | `mpau_cli.py`，`uploader/{douyin,ks,tencent,pdd,tmall,jd}_uploader/main.py`，`uploader/base_video.py`，`utils/base_social_media.py` | 六个平台上传器的路径、输入字段、Patchright/Playwright 登录/上传策略、CLI 参数 | 各平台参数不统一；CLI 不是可靠任务服务；快手没有原生商品挂载；不能假定发布/挂载回查齐全 |
| commerce：`whichmen/commerce-multi-platform-publisher` | `publisher/adapters.py`、`publish_runner.py`、`publish_plan.py`、`publish_verify.py`、`pdd_queue.py`、`browser_manager.py`、`utils/product_metadata.py`、`uploader/ks_uploader/{main,add_product}.py`、测试及授权声明 | 排期、幂等、掉线恢复、验证、账号隔离、拼多多延迟任务、SKU sidecar 概念 | 上游衍生代码许可证边界未解决；快手商品绑定通过关键词匹配首个结果，不是精确 ID 绑定；JSON 文件充当队列不适于多任务一致性；Linux/systemd 方案不适合直接搬到 Win11 |
| MultiPublish：`whut09/MultiPublish` | `src/main/{index,browser-manager,store,persistent-store}.ts`、`src/shared/types.ts`、`src/renderer/src/App.tsx`、`src/preload/index.ts` | Windows 上多账号 UI、视频封面与发布记录交互、原子持久化思路、限流并发/任务超时、后台回查 UX | `browser-manager.ts` 约 5,645 行，浏览器与平台规则严重集中；原生 Electron Session 不能无损移植为 Python Playwright Profile；商品字段缺失；应用内 JSON 存储不适合作为本项目唯一数据库 |

**特别注意许可：** MPAU、MultiPublish 仓库公开标注 MIT；`commerce-multi-platform-publisher` 在 `THIRD_PARTY_NOTICES.md` 明确承认继承自 `dreammis/social-auto-upload` 的部分源码授权不明，而其 `LICENSE-ADDITIONS` 只覆盖新增部分。未核实授权之前，仅借鉴设计和流程思路，不将继承代码直接复制进发布工程，也不附带不明来源的 `biliup.exe`。

## 1. 范围与交付顺序

### P0：必须实现

1. Win11 上启动本地服务，默认只绑定 `127.0.0.1`，浏览器打开本地 Web 管理页面。
2. 本地视频仓库：批量导入 MP4、预览、缩略图、封面、删除/归档；鼠标悬停预览/放大；FFmpeg 读取元数据。
3. 平台账号管理：抖音、快手、视频号；人工扫码登录，独立会话，登录状态检测与失效提示。
4. 商品仓库：内部 SKU + 平台/店铺商品 ID 一对一映射。同一 SKU 可以映射到不同店铺的不同商品 ID。支持手动填写、导入表格及预览（先不做官方 ERP 商品同步）。
5. 视频元数据统一填写：通用标题/简介/标签/封面；平台特有字段显示补充表单，发布前完成校验。
6. 抖音、快手、视频号三平台：上传、商品选择、发布、双层回查、日志、失败人工接管；必须真实账号小批量验收。
7. 队列持久化、按店铺串行、全局限并发、断电重启恢复、防重复发布、未知结果人工核验。

### P1：扩展

1. 淘宝光合、多多视频、京东京麦三个连接器；京东优先参照 MPAU 的 `jd` 实现。
2. 统一定时发布；平台不支持的定时功能用本地队列调度，但设备/登录会话需要处于可用状态。
3. 批量标题优化、重复素材识别、商品匹配校验、发布前综合检查分（内部评分，不代表官方 90 分）。
4. 失败告警、日志导出、备份恢复、可选 Windows 开机自启、单机打包。

### 不进入首版

统一库存、订单 ERP、自动抓取/登录破解、验证码自动绕过、逆向私有接口、无人确认的大规模账号矩阵、不经授权的跨平台导流商品链接。上述需求可以预留独立模块，但不能阻碍首版发布闭环。

## 2. 推荐技术架构

```text
Windows 11 + 本地浏览器
        │
        ▼
React + TypeScript + Ant Design（借鉴 MultiPublish UI，适配浏览器）
        │  HTTP / WebSocket，局域网默认关闭
        ▼
FastAPI + Pydantic + SQLAlchemy + Alembic
        ├─ MediaService：视频/封面/缩略图/元信息
        ├─ ProductService：内部 SKU 与平台商品绑定
        ├─ AccountService：每个店铺独立身份与登录状态
        ├─ PublishPlanner：预检、任务拆分、排期
        ├─ JobWorker：SQLite 持久化队列、锁、幂等、超时、状态恢复
        ├─ VerificationService：视频回查 + 商品回查（独立结论）
        └─ AdapterRegistry
           ├─ DouyinAdapter
           ├─ KuaishouAdapter
           ├─ WeixinChannelsAdapter
           ├─ TaobaoGuangheAdapter
           ├─ JdJingmaiAdapter
           └─ PddVideoAdapter
                │
                ▼
  Python Playwright/Patchright + 各账号独立 Browser Profile
  （登录与验证码由用户在平台官方页面手动完成）
```

**关键架构决策：** 不直接混用 Electron `session.fromPartition()`、Chrome CDP 和 Patchright 的 Cookie/Profile。首版统一以 Python 的浏览器自动化为主体；MultiPublish 主要用于 UI 和状态/交互参考。若未来选 Electron 包装网页，作为外壳即可，不让它同时成为第二套发布引擎。

推荐技术：Python 3.11、FastAPI、SQLAlchemy 2、SQLite WAL、Alembic、Playwright/Patchright、React、TypeScript、Vite、Ant Design、FFmpeg、Pytest。先采用进程内持久化工作队列；只有确实需要多机扩展再评估 Redis/Celery。Windows 任务计划程序可替代 systemd。

## 3. 工程目录（建议）

```text
D:\CommerceVideoHub\
├─ refs\
│  ├─ mpau\                       # 只读第三方参考
│  ├─ commerce-publisher\         # 只读第三方参考；注意上游许可
│  └─ multipublish\               # 只读第三方参考
├─ app\
│  ├─ backend\
│  │  ├─ api\
│  │  ├─ domain\                    # 领域类型、任务状态机、契约
│  │  ├─ models\                    # SQLAlchemy 数据模型
│  │  ├─ services\                  # 产品映射、媒体管理、校验
│  │  ├─ adapters\                  # 每个平台独立目录
│  │  │  ├─ douyin\
│  │  │  ├─ kuaishou\
│  │  │  ├─ weixin\
│  │  │  ├─ taobao\
│  │  │  ├─ jd\
│  │  │  └─ pdd\
│  │  ├─ workers\
│  │  ├─ migrations\
│  │  └─ tests\
│  ├─ frontend\
│  └─ scripts\
├─ runtime\                      # 本机私有数据，严格 Git 忽略
│  ├─ profiles\
│  ├─ media\
│  ├─ thumbnails\
│  ├─ logs\
│  └─ app.db
├─ docs\
│  ├─ SOURCE_AUDIT.md
│  ├─ LICENSE_AUDIT.md
│  ├─ PLATFORM_CAPABILITIES.md
│  ├─ TEST_REPORT.md
│  └─ DECISIONS.md
├─ AGENTS.md
└─ PROJECT_PLAN.md
```

## 4. 平台与商品关联契约

### 4.1 统一任务模型

```json
{
  "internal_sku": "SKU-001",
  "media_id": "video-001",
  "common": {
    "title": "示例产品演示",
    "description": "真实商品演示",
    "tags": ["产品展示"],
    "cover_path": "runtime/media/cover.jpg"
  },
  "targets": [
    {"platform": "douyin", "account_id": "dy-shop-a", "product_id": "该店实际商品ID"},
    {"platform": "kuaishou", "account_id": "ks-shop-a", "product_id": "该店实际商品ID"},
    {"platform": "weixin", "account_id": "wx-shop-a", "product_id": "该店实际商品ID"}
  ]
}
```

上方为**目标数据协议示意**，不是三个源码现在已统一支持的参数。内部 SKU 不应与平台商品 ID 混同。商品绑定必须以 `platform + account_id + product_id` 为键；对非纯数字商品号的校验，按对应平台规则处理。

### 4.2 统一适配器接口

```python
class PlatformAdapter(Protocol):
    platform: str

    async def check_login(self, account) -> LoginResult: ...
    async def validate_content(self, job) -> ValidationResult: ...
    async def resolve_product(self, job) -> ProductResolution: ...
    async def upload_media(self, job, context) -> UploadEvidence: ...
    async def attach_product(self, job, context) -> ProductAttachmentEvidence: ...
    async def submit(self, job, context) -> SubmissionEvidence: ...
    async def verify_post(self, job, context) -> PostVerification: ...
    async def verify_product(self, job, context) -> ProductVerification: ...
```

接口仅为示例，开发时在 `domain/contracts.py` 定义真实 Pydantic/dataclass 类型，所有平台共享。若目标平台无法提供可靠的发布后商品校验，需要明确在能力矩阵中标为 `manual_required`，不能虚构已验证。

### 4.3 状态机与禁止误报

`pending → preflight → login_check → uploading → attaching_product → submitting → verifying → success`。任何一步可能转为 `manual_required / failed_retryable / failed_permanent / unknown / cancelled`。

- 成功必须同时具备：**平台作品管理页可回查到目标作品** + **商品关联有可靠的对应 ID/商品标识证据**。两个证据单独保存。
- 上传完、点击发布按钮、页面跳转、命令返回码 0，全部不足以单独判定“带货成功”。
- 商品列表存在同名候选、第一条搜索结果无法确认目标 ID，必须阻塞并要求人工选择；严禁静默挂载。
- 提交后发生网络断开/超时：先检查平台后台是否已经存在作品，再决定是否重试；不允许直接重新发布以免重复。
- `unknown` 任务不可自动重试。相同 `content_id + account_id + publish_version` 实施唯一约束。
- 任务失败时保留截图、控件信息、关键事件和脱敏日志，不能自动删除视频文件。

## 5. 数据库最小表

| 表 | 关键字段 | 约束 |
|---|---|---|
| `media_assets` | id, path, sha256, duration, resolution, cover_path, created_at | 文件必须存在；SHA256 识别重复素材 |
| `products` | id, internal_sku, name, category, attributes | `internal_sku` 唯一 |
| `shop_accounts` | id, platform, name, profile_key, login_status, last_checked_at | 账号唯一且拥有独立 Profile |
| `product_mappings` | id, product_id, shop_account_id, external_product_id, external_name, url, verified_at | `(shop_account_id, product_id)` 唯一 |
| `publish_drafts` | id, media_id, title, description, tags, cover_path, version | 可保留版本与平台覆盖字段 |
| `publish_jobs` | id, draft_id, account_id, mapping_id, schedule_at, status, attempt_count, idempotency_key | 唯一幂等键；同账号串行 |
| `publish_evidence` | job_id, post_url, post_id, post_verified, product_verified, product_id_seen, screenshot_path | 两项核验结果明确分离 |
| `job_events` | job_id, timestamp, stage, outcome, message, error_code | 只存脱敏信息，便于故障回溯 |

## 6. 六平台验收矩阵

| 平台 | 原项目基础 | 关键短板 | 最低验收 |
|---|---|---|---|
| 抖音 | MPAU 视频+商品链接；commerce 商品流程；MultiPublish 视频发布回查 | 商品链接的账号权限、商品精确映射需要真机确认 | 同店铺真实商品 ID 可选中；作品与商品分别确认 |
| 快手 | MPAU 视频上传；commerce 关键词挂商品；MultiPublish Windows 发布 | 必须重写为精确商品关联；当前按名称/视频文件名匹配会误挂 | **一款商品对应唯一目标 ID；歧义即阻断** |
| 视频号 | MPAU `tencent` 商品字段；commerce 商品流程 | 商品橱窗/微信小店权限；已选商品是否持久化 | 可在官方后台核验视频与对应商品 |
| 淘宝光合 | MPAU `tmall`；commerce `tb_uploader` | 淘宝/天猫账号与商品类型各异 | 视频发布 + 指定商品准确挂载 + 回查 |
| 京东京麦 | MPAU `jd` 包含按数字 ID 站内搜索 | `whichmen` 仓库无京东主链路 | 商品 ID 匹配、视频提交与回查三步过关 |
| 多多视频 | MPAU `pdd`；commerce 延迟队列 | 定时发布依赖商品先关联；页面/审核不确定性 | 正确挂载 ID，未知结果不重复发布 |

**测试判定**：先 Mock/离线用例通过，再用有权限的真实店铺与真实商品，每个平台人工确认至少一条视频+商品关联闭环；同时记录平台页面版本、账号类型和测试日期。没有真实账号测试的状态一律写“未验收”。

## 7. 实施工作包（顺序与依赖）

下方是摘要；完整可过滤任务表见同名 `.xlsx`。

| 顺序 | 包 | 必须交付 | 验收门槛 |
|---|---|---|---|
| G0 | 源码与授权审计 | SOURCES、SHA、依赖、许可证、风险记录 | 三仓库各有说明；不确定授权的代码未复制 |
| G1 | 最小骨架 | Python API、React UI、SQLite、启动脚本、健康检测 | Win11 一键启动，Web 只绑定 localhost |
| G2 | 媒体与商品中心 | 本地视频管理、预览、SKU 商品映射、各店铺商品 ID | 一次选择商品可生成多平台精确目标 |
| G3 | 发布引擎 | 统一 Adapter、状态机、队列、账号隔离、前置校验 | Mock 测试、重启恢复、幂等与同账号串行通过 |
| G4 | 三平台 P0 | 抖音、快手、视频号上传+商品+核验 | 三平台逐条真实测试，失败不报成功 |
| G5 | 三平台 P1 | 淘宝、京东、拼多多 | 六平台均能实测闭环或诚实标注阻碍 |
| G6 | 稳定与发布 | 失败截图、日志、授权清单、Windows 启动器 | 用户机器回归测试、备份恢复与安全检查 |

## 8. AI 开发禁止事项

1. 禁止以“README 声称支持”为依据标记功能完成；必须阅读代码、运行测试并由真实账号验收。
2. 禁止将三套浏览器的 Cookie/Profile 直接互导；禁止上传真实 Cookie/账号信息到 AI 云服务或公开仓库。
3. 禁止直接拷贝授权不明的 `commerce` 上游衍生连接器和二进制文件；先做许可证调查，明确允许范围后再作代码级复用。
4. 禁止在商品匹配不确定时选择第一个结果；禁止把“只发布视频”伪装为“挂商品成功”。
5. 禁止自动绕过验证码、短信验证、登录风控、平台权限控制；遇到此类情况停机提示人工操作。
6. 禁止将首版范围扩张到订单 ERP、库存同步、多机分布式和抓取竞品，除非发布闭环已通过验收。
7. 禁止一次性重构整个项目然后声称成功；每完成一个小模块必须执行类型检查、单元测试与端到端验收。

## 9. 本地 AI 的运行与交付规则

每轮开发只执行当前工作包，先提交：`变更文件清单 → 代码方案 → 测试脚本 → 测试输出 → 未完成清单 → 下一任务`。不能只贴生成代码而不验证。记录故障根因和平台实际行为。产品挂载的模糊匹配必须明确显示人工处理。首版默认只给可登录账号的本机用户使用。

必要交付：`start.ps1`、`README.md`、依赖锁文件、数据库迁移、`tests/`、`docs/PLATFORM_CAPABILITIES.md`、`docs/TEST_REPORT.md`、`docs/LICENSE_AUDIT.md`、`docs/DECISIONS.md`、`runtime/` 的 Git 忽略规则。

## 10. 可复制的下载目录命令（PowerShell）

```powershell
New-Item -ItemType Directory -Force D:\CommerceVideoHub\refs | Out-Null
Set-Location D:\CommerceVideoHub\refs
git clone https://github.com/cjccd/multi-platform-auto-upload.git mpau
git clone https://github.com/whichmen/commerce-multi-platform-publisher.git commerce-publisher
git clone https://github.com/whut09/MultiPublish.git multipublish

# 记录下载时的准确版本，以免后续上游更新产生差异
foreach ($repo in @('mpau','commerce-publisher','multipublish')) {
  Write-Host "$repo  $(git -C $repo rev-parse HEAD)"
}
```

把这三个 `refs` 目录设为只读参考；让本地 AI 在 `D:\CommerceVideoHub\app` 新建代码。每次升级都先审计 diff，不直接覆盖现有工程。

## 11. 源码参照链接

- MPAU：https://github.com/cjccd/multi-platform-auto-upload
- MPAU CLI：https://github.com/cjccd/multi-platform-auto-upload/blob/main/mpau_cli.py
- MPAU 京东：https://github.com/cjccd/multi-platform-auto-upload/blob/main/uploader/jd_uploader/main.py
- commerce：https://github.com/whichmen/commerce-multi-platform-publisher
- commerce 快手商品关联：https://github.com/whichmen/commerce-multi-platform-publisher/blob/main/uploader/ks_uploader/add_product.py
- commerce 幂等排期：https://github.com/whichmen/commerce-multi-platform-publisher/blob/main/publisher/publish_plan.py
- commerce 授权说明：https://github.com/whichmen/commerce-multi-platform-publisher/blob/main/THIRD_PARTY_NOTICES.md
- MultiPublish：https://github.com/whut09/MultiPublish
- MultiPublish 主进程：https://github.com/whut09/MultiPublish/blob/main/src/main/index.ts
- MultiPublish 浏览器管理：https://github.com/whut09/MultiPublish/blob/main/src/main/browser-manager.ts
- MultiPublish React UI：https://github.com/whut09/MultiPublish/blob/main/src/renderer/src/App.tsx
