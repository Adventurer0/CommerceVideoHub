# 六平台能力矩阵

这里区分“参考代码存在”与“CommerceVideoHub 已验证”。没有真实平台验收记录。

| 平台键 | 优先级 | 参考上传流程 | 参考商品输入与缺口 | 新工程 upload/attach/submit | 发布后核验 |
|---|---|---|---|---|---|
| douyin | P0 | MPAU DouYinVideo；MultiPublish | 商品链接/短标题，返回失败未强制阻断；需店铺 ID 唯一身份 | unsupported | manual_required，未验收 |
| kuaishou | P0 | MPAU KSVideo；MultiPublish | MPAU 无挂载；commerce 关键词首条不合格 | unsupported | manual_required，未验收 |
| weixin | P0 | MPAU TencentVideo | goods_id 搜索后第一行，橱窗权限/ID/已选持久化待验证 | unsupported | manual_required，未验收 |
| taobao | P1 | MPAU TmallVideo | ID 搜索后首卡，账号类型/商品身份待验 | unsupported | manual_required，未验收 |
| jd | P1 | MPAU JDVideo | ID 搜索后首卡；commerce 无主链路 | unsupported | manual_required，未验收 |
| pdd | P1 | MPAU PDDVideo；commerce 队列 | goods_id、定时依赖商品；提交后状态待验 | unsupported | manual_required，未验收 |

G1 六平台只注册禁用占位适配器；登录返回 manual_required（尚未实现扫码界面），内容校验/解析/上传/挂载/提交返回 unsupported，verify_post / verify_product 返回 manual_required。这些是新工程当前实现状态，不表示官方平台不支持功能。

统一字段为 platform + account_id + shop_id + external_product_id，内部 media_id/internal_product_id/internal_sku 独立。原 tencent→weixin、tmall→taobao 仅为审计名词映射，不能直接复用账户/Profile。

每个平台未来需在账号授权后记录：平台页面日期/版本、账号类型、指定店铺及商品 ID、发布前唯一匹配证据、发布后 post_id 与商品 ID 分项证据。歧义、权限不足、商品不存在必须阻断；无法独立回查必须 manual_required；未知提交不得自动重试。本轮未实施发布、调度或商品查找。
