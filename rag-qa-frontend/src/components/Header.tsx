import React from 'react';
import { Layout, Button, Space, Dropdown, Avatar, Tag } from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BellOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined
} from '@ant-design/icons';
import type { MenuProps } from 'antd';

const { Header } = Layout;

interface AppHeaderProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
  healthStatus?: 'healthy' | 'unhealthy' | 'loading';
}

const userMenuItems: MenuProps['items'] = [
  {
    key: 'profile',
    icon: <UserOutlined />,
    label: '个人中心',
  },
  {
    key: 'settings',
    icon: <SettingOutlined />,
    label: '系统设置',
  },
  {
    type: 'divider',
  },
  {
    key: 'logout',
    icon: <LogoutOutlined />,
    label: '退出登录',
    danger: true,
  },
];

const AppHeader: React.FC<AppHeaderProps> = ({
  collapsed,
  onToggleCollapse,
  healthStatus = 'loading'
}) => {
  const getHealthTag = () => {
    switch (healthStatus) {
      case 'healthy':
        return <Tag color="success">系统正常</Tag>;
      case 'unhealthy':
        return <Tag color="error">系统异常</Tag>;
      default:
        return <Tag color="default">检查中...</Tag>;
    }
  };

  return (
    <Header
      style={{
        background: '#fff',
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid #f0f0f0',
        height: 56,
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 100,
      }}
    >
      <Space size="middle" style={{ alignItems: 'center' }}>
        <Button
          type="text"
          icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={onToggleCollapse}
          style={{ fontSize: 16, width: 40, height: 40 }}
        />
        <span style={{ fontSize: 16, fontWeight: 600, color: '#262626' }}>RAG知识库管理系统</span>
        <span className="health-tag">{getHealthTag()}</span>
      </Space>

      <Space size="middle" style={{ alignItems: 'center' }}>
        <Button type="text" icon={<BellOutlined />} style={{ fontSize: 16 }} />
        <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
          <Space style={{ cursor: 'pointer', padding: '4px 8px', borderRadius: 8 }} className="header-user">
            <Avatar
              size={32}
              style={{
                background: 'linear-gradient(135deg, #1677ff, #69b1ff)',
                boxShadow: '0 2px 6px rgba(22, 119, 255, 0.35)',
              }}
              icon={<UserOutlined />}
            />
            <span style={{ color: '#262626', fontWeight: 500 }}>管理员</span>
          </Space>
        </Dropdown>
      </Space>
    </Header>
  );
};

export default AppHeader;
