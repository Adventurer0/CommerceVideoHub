# G0 授权边界

审计对象为 SOURCE_MANIFEST.json 锁定的本地字节，日期 2026-11-06。本文件记录仓库声明和本轮使用边界，不宣称第三方权属已全面厘清。

| 来源 | 实际文件 | 许可声明 | 本轮处理 |
|---|---|---|---|
| MPAU | refs/mpau/LICENSE | MIT，Copyright (c) 2026 cjccd | 阅读参考；未移植代码、资源或二进制。未来复用前逐文件核对来源，保留完整许可证及版权声明。 |
| MultiPublish | refs/multipublish/LICENSE | MIT，Copyright (c) 2026 whut09 | 阅读 UI/持久化思路；未复用代码、图像或 Electron 引擎。 |
| commerce 独立新增 | THIRD_PARTY_NOTICES.md + LICENSE-ADDITIONS | scoped MIT，Copyright (c) 2026 Wei Zhang；publisher、browser_manager、legacy、scripts、tests 等列举范围 | 本轮也不复制，仅独立编写契约、迁移和状态策略。 |
| commerce 上游衍生 | THIRD_PARTY_NOTICES.md | baseline b517db00ed7552125a058a34f85f9a6dd7842cc1；声明 upstream 缺完整 LICENSE，fork 关系不解决授权 | uploader、utils、myUtils、db、examples、cli_main.py、sau_backend.py/目录、sau_frontend 全部禁止移入新工程。 |
| biliup.exe | THIRD_PARTY_NOTICES.md 的二进制条目 | 有 SHA/blob 来源记录，但声明未重建/独立安全审计，且仍在未解决授权范围 | 不执行、不打包；审计原测试只读取哈希。 |

**结论：许可风险仍未解除，采用独立实现可以继续 G1。** 未取得新的可验证许可，不将 commerce 上游文件、片段及不明二进制纳入 app。所有 refs 从 Git/构建产物排除，审计脚本只引用本地路径。SOURCE_MANIFEST 保存哈希而非源码。未来引入 MIT 实质代码时应同时加入完整 LICENSE 与著作权归属清单。

G1 的常规第三方依赖由 uv.lock、package-lock.json 锁定；它们仍保有各自许可，分发前在 G6 输出完整依赖许可证清单。本轮不是可对外分发安装包。
