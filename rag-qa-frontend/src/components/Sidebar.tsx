import React from 'react';
import { Layout, Menu } from 'antd';
import {
  FileTextOutlined,
  ToolOutlined,
  MessageOutlined,
  SearchOutlined,
  SettingOutlined,
  DashboardOutlined,
  DatabaseOutlined
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';

const { Sider } = Layout;

interface SidebarProps {
  collapsed?: boolean;
  onCollapse?: (collapsed: boolean) => void;
}

const menuItems = [
  {
    key: '/dashboard',
    icon: <DashboardOutlined />,
    label: '仪表盘',
  },
  {
    key: '/documents',
    icon: <FileTextOutlined />,
    label: '文档管理',
  },
  {
    key: '/cleaning',
    icon: <ToolOutlined />,
    label: '清洗规则',
  },
  {
    key: '/qa',
    icon: <MessageOutlined />,
    label: '问答管理',
  },
  {
    key: '/retrieval',
    icon: <SearchOutlined />,
    label: '检索测试',
  },
  {
    key: '/queue',
    icon: <DatabaseOutlined />,
    label: '队列管理',
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: '系统设置',
  },
];

const Sidebar: React.FC<SidebarProps> = ({ collapsed, onCollapse }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  return (
    <Sider
      width={220}
      style={{
        background: 'linear-gradient(180deg, #001529 0%, #0b2b4d 100%)',
        borderRight: 'none',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 56,
        bottom: 0,
        overflow: 'auto',
        zIndex: 99,
      }}
      collapsible
      collapsed={collapsed}
      onCollapse={onCollapse}
      trigger={null}
    >
      <div className="app-brand">
        <div className="app-brand-logo">R</div>
        {!collapsed && (
          <span className="app-brand-title">RAG知识库系统</span>
        )}
      </div>
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={handleMenuClick}
        style={{ borderRight: 0, marginTop: 8, background: 'transparent' }}
      />
    </Sider>
  );
};

export default Sidebar;
