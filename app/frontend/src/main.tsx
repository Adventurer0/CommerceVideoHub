import { StrictMode, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Alert, ConfigProvider, Empty, Layout, Menu, Tag, Typography } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import 'antd/dist/reset.css';
import './styles.css';

const pages = [
  { key: 'media', label: '视频仓库', description: '本地视频导入、预览与封面管理将在下一阶段开放。' },
  { key: 'products', label: '商品仓库', description: '按内部 SKU 与指定店铺的准确商品 ID 建立映射。' },
  { key: 'accounts', label: '店铺账号', description: '账号登录尚未开放。后续由你在官方页面扫码登录。' },
  { key: 'publish', label: '发布中心', description: '发布功能尚未开放。商品无法唯一匹配时将阻断发布。' },
  { key: 'history', label: '发布记录', description: '暂无发布记录。视频发布与商品关联将分别显示验证状态。' },
  { key: 'settings', label: '设置', description: '当前仅运行本地工程骨架，平台能力均未验收。' },
];

function readPage() {
  const key = window.location.hash.replace('#/', '');
  return pages.some(page => page.key === key) ? key : 'media';
}

function App() {
  const [active, setActive] = useState(readPage);
  const [health, setHealth] = useState<'loading' | 'ok' | 'error'>('loading');
  useEffect(() => {
    const onHash = () => setActive(readPage());
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 5000);
    fetch('/api/health', { signal: controller.signal })
      .then(async response => {
        if (!response.ok) throw new Error('unavailable');
        const body: unknown = await response.json();
        if (!body || typeof body !== 'object' || !('status' in body) || body.status !== 'ok') {
          throw new Error('invalid health response');
        }
        setHealth('ok');
      })
      .catch(() => setHealth('error'))
      .finally(() => window.clearTimeout(timer));
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, []);
  const page = pages.find(item => item.key === active)!;
  return <ConfigProvider locale={zhCN} theme={{ token: { colorPrimary: '#245bcc', borderRadius: 8 } }}>
    <Layout className="shell">
      <Layout.Sider width={220} theme="light" breakpoint="lg" collapsedWidth={0}>
        <div className="brand">CommerceVideoHub<span>本地视频工作台</span></div>
        <nav aria-label="主导航"><Menu selectedKeys={[active]} items={pages.map(({key, label}) => ({key, label}))}
          onClick={({ key }) => { window.location.hash = `/${key}`; setActive(key); }} /></nav>
      </Layout.Sider>
      <Layout>
        <Layout.Header className="header">
          <span>本机工作空间</span>
          <Tag color={health === 'ok' ? 'green' : health === 'error' ? 'red' : 'default'}>
            {health === 'ok' ? '本地服务正常' : health === 'error' ? '本地服务不可用' : '正在检查服务'}
          </Tag>
        </Layout.Header>
        <Layout.Content className="content">
          <Alert type="info" showIcon title="工程骨架 · 发布尚未开放"
            description="优先接入抖音、快手、视频号。所有平台均未完成真实账号和商品挂载验收。" />
          {health === 'error' && <Alert className="connection-alert" type="error" showIcon title="无法连接本地服务"
            description="请检查启动窗口中的错误，服务恢复后刷新页面。" />}
          <section className="workspace" aria-labelledby="page-title">
            <Typography.Title id="page-title" level={1}>{page.label}</Typography.Title>
            <Typography.Paragraph type="secondary">{page.description}</Typography.Paragraph>
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="功能待开发" />
          </section>
          <footer>本地存储 · 指定店铺商品 ID · 视频与商品分别验证</footer>
        </Layout.Content>
      </Layout>
    </Layout>
  </ConfigProvider>;
}

createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>);
