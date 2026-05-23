import React, { useState } from 'react';
import { Layout } from 'antd';
import Sidebar from './Sidebar';
import AppHeader from './Header';
import { Outlet } from 'react-router-dom';

const { Content } = Layout;

const AppLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [healthStatus] = useState<'healthy' | 'unhealthy' | 'loading'>('loading');

  const handleToggleCollapse = () => {
    setCollapsed(!collapsed);
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <AppHeader
        collapsed={collapsed}
        onToggleCollapse={handleToggleCollapse}
        healthStatus={healthStatus}
      />
      <Layout>
        <Sidebar collapsed={collapsed} onCollapse={setCollapsed} />
        <Content
          style={{
            marginLeft: collapsed ? 80 : 220,
            marginTop: 56,
            padding: 24,
            minHeight: 'calc(100vh - 56px)',
            background: '#f5f5f5',
            transition: 'margin-left 0.2s',
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default AppLayout;
