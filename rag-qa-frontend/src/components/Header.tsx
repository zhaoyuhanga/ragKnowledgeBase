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
      <Space size="middle">
        <Button
          type="text"
          icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={onToggleCollapse}
          style={{ fontSize: 16, width: 40, height: 40 }}
        />
        <span style={{ fontSize: 16, fontWeight: 500 }}>RAG知识库管理系统</span>
        {getHealthTag()}
      </Space>

      <Space size="middle">
        <Button type="text" icon={<BellOutlined />} style={{ fontSize: 16 }} />
        <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
          <Space style={{ cursor: 'pointer' }}>
            <Avatar style={{ backgroundColor: '#1677ff' }} icon={<UserOutlined />} />
            <span>管理员</span>
          </Space>
        </Dropdown>
      </Space>
    </Header>
  );
};

export default AppHeader;
