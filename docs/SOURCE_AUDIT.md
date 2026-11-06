# G0 源码审计（2026-11-06）

## 来源与准确版本

根指令、PROJECT_PLAN.md 已完整读取；规划中另名 `CommerceVideoHub_融合项目规划.md` 未提供，以 PROJECT_PLAN.md 为实际规划。另只读检查了项目规划表.xlsx 的 G0/G1 条目，未修改原表。工程位于 D:\CommerceVideoHub。refs 是指向用户原解压目录的 junction，只读使用，未复制第三方仓库到 app。

| refs 名称 | 原始目录（用户工作区下） | 包版本 | ZIP 注释中的提交号 |
|---|---|---|---|
| mpau | multi-platform-auto-upload-main | 0.1.0 | 4c8b6465c2473aac3cfe064c8c6dfbadd87b2238 |
| commerce-publisher | commerce-multi-platform-publisher-main | 0.1.0 | e9c38a4d9518f4e47590524e35145ce7a416aa3f |
| multipublish | MultiPublish-main | 0.1.50 | 9333852cd1db76ed3698ee3684e78dff9644d02f |

对三目录实际执行 `git -C <source> rev-parse HEAD` 均 exit 128：not a git repository。不能声称 Git 历史已验证。归档注释仅是来源提示；完整文件哈希证明本轮审计的准确字节版本，非远端签名认证。83 / 157 / 31 个文件分别与 ZIP 全量匹配。见 [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json)，含原始路径、完整清单、每文件/目录/归档 SHA-256。复查：`python app/scripts/audit_sources.py`；不一致即失败。

| 归档 | SHA-256 |
|---|---|
| MPAU | eb3394de4f3882b4c3a61478738923f039538457f5dcd0b92fc1adcc8d98a78c |
| commerce | 56067760efcad8beda3a681fb8a6f749404681216179732606e48b1bc64c4a03 |
| MultiPublish | 1b2be06c20a1a29485c014a3151078095741b6f926ff23ee6cca80c34382af80 |

## 目录、源码证据与重建边界

| 项目/模块 | 实际源码依据 | 结论 |
|---|---|---|
| MPAU CLI | mpau_cli.py:10–66 导入上传器；请求 dataclass 和 dispatch；tests/test_mpau_cli.py | 多平台参数/dispatch 可作接口参考；CLI 退出不能证明商品绑定。9 测试仅解析和 mock dispatch。 |
| MPAU 公共层 | uploader/base_video.py；utils/base_social_media.py；utils/config.py、log.py | 文件/日期校验，初始化脚本，账户路径；log 导入会创建日志，审计测试重定向到临时目录。当前树未提供独立完整 Web 前后端，pyproject 的 Flask web extra 不是现成 Web 产品。 |
| MPAU 抖音 | uploader/douyin_uploader/main.py:553、815、879 | 商品链接流程返回 bool，upload 调用未强制检查失败结果；需要独立重建阻断策略。 |
| MPAU 快手 | uploader/ks_uploader/main.py 的 KSVideo/上传与定时逻辑 | 有视频流程，未找到商品精确挂载链路；不能补成默认普通视频发布。 |
| MPAU 视频号 | uploader/tencent_uploader/main.py:1090–1182 | goods_id 搜索；空结果会中止，但 1157 起选第一行，未证实该行属于唯一目标 ID；日志“挂载成功”不是发布后证据。 |
| MPAU 淘宝/京东 | uploader/tmall_uploader/main.py:394–480；jd_uploader/main.py:275–378 | ID 搜索后仍选首个商品卡；“包含价格/弹窗关闭”不等于精确绑定，京东不能直接视为已满足要求。 |
| MPAU 多多 | uploader/pdd_uploader/main.py:207–217、300–363、697–718 | 定时依赖商品；ID 搜索及弹窗关闭判定；发布后跳转不等于双项核验。 |
| commerce 契约/执行 | publisher/adapters.py:75–120；publish_runner.py:40–82 | CLI receipt 以 returncode=0 标 success；主 runner 又做标题/排期回查；这两种层次都不是独立商品证据。 |
| commerce 队列/恢复 | publisher/publish_plan.py:44–60、362–389；pdd_queue.py:95–125 | JSON 原子替换、fcntl 锁、stale running 恢复可作设计参考；提交未知状态直接回 pending 存在重复风险，不能直接迁移。 |
| commerce 回查 | publisher/publish_verify.py:263、298、538、642 | 标题/时间与页面/API 响应回查；不满足本工程按店铺 ID 的双项证据契约。 |
| commerce 商品 | utils/product_metadata.py:29–57；uploader/ks_uploader/add_product.py:6、45、51、78 | sidecar 把 sku/product_id 归一；快手关键词首条且验证失败仍继续。禁止复用为准确商品绑定。 |
| commerce 浏览器 | browser_manager.py:4、136–144、248 起 | Linux fcntl/CDP/profile/桌面环境；不能原样在 Windows 运行。 |
| commerce Web/UI | sau_backend.py:17–20、483；sau_frontend/package.json、src/router/index.js | Flask + 宽 CORS + 0.0.0.0:5409；Vue3/Element Plus/Pinia，不适合合并入 React/FastAPI；仅看业务分区。 |
| MultiPublish 引擎 | src/main/browser-manager.ts:133、689、2430、5033；src/main/index.ts | Electron partition/CDP、发布前后标题回查；本次文件 5,465 行（与规划估算不同）。平台逻辑高度集中，不启动第二套引擎。 |
| MultiPublish 回查 | src/main/publish-verification.ts | 抖音/视频号完整标题，其余含标题前缀候选；同标题仍可能混淆，商品字段缺失。 |
| MultiPublish 持久化 | src/main/persistent-store.ts、store.ts | 临时文件+flush+备份，串行更新；删除旧文件到 rename 有窗口，不代替数据库事务。 |
| MultiPublish UI | src/shared/types.ts、src/preload/index.ts、src/renderer/src/App.tsx | 账号页、发布记录、失败人工入口可参考；IPC 改为本地 HTTP，不迁移 Electron session。 |

## 依赖与离线条件

- MPAU Python >=3.10,<3.13，Patchright=1.58.2，Playwright>=1.44、OpenCV 等；旧 requirements.txt 是 UTF-16 大包集合，锁 Playwright=1.52，和 pyproject/uv.lock 并非同一依赖入口。新工程不合并该文件。
- commerce Python>=3.11，Playwright>=1.52,<2、pytest>=8.4,<9 等；fcntl 是 Windows 标准库缺失，不可伪造锁实现让测试变绿；systemd、/usr/bin 路径另需重建。
- MultiPublish Electron39/React19/AntD6/Vite7/TS5.9；test 使用 Node 类型剥离，README Node20+ 不足以保证 test 命令可运行。本轮 Node24.19.0 跑测试，无需 Electron/FFmpeg 下载。完整 npm ci 离线失败 ENOTCACHED（zustand），在 tests/audit-install 中仅复制 package 两文件检测，未写 refs。
- commerce Web 是 Vue3/Vite6；MultiPublish 是 React19/electron-vite4；不合并路由、状态或依赖树。
- 首次 Python 离线装依赖失败：pytest 缓存缺失。之后联网准备隔离 .audit-venv，测试阶段拒绝非回环 socket 和真实子进程，禁 pycache、禁 refs 写入。未安装/启动平台浏览器，未读真实会话。
- Playwright/Patchright 的 Python 包与浏览器二进制独立；G1 仅声明 Playwright 可选依赖，不需要下载浏览器或操作账号。

完整测试结果和限制见 [TEST_REPORT.md](TEST_REPORT.md)。原仓库失败不通过修改第三方代码消除；新工程使用独立实现并单独验收。
