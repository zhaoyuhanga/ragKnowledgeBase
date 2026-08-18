import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { AppLayout } from './components';
import {
  Dashboard,
  Documents,
  CleaningRules,
  QA,
  RetrievalTest,
  QueueManagement,
  Settings
} from './pages';
import './styles/global.css';

const App: React.FC = () => {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#1677ff',
          colorInfo: '#1677ff',
          colorSuccess: '#52c41a',
          colorWarning: '#faad14',
          colorError: '#ff4d4f',
          colorBgLayout: '#f0f2f5',
          borderRadius: 8,
          fontSize: 14,
          fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif",
        },
        components: {
          Layout: {
            headerBg: '#ffffff',
            headerHeight: 56,
            siderBg: '#001529',
          },
          Menu: {
            darkItemBg: 'transparent',
            darkSubMenuItemBg: 'rgba(0, 0, 0, 0.2)',
            darkItemSelectedBg: '#1677ff',
            darkItemHoverBg: 'rgba(255, 255, 255, 0.08)',
            itemBorderRadius: 8,
            itemMarginInline: 8,
          },
          Card: {
            borderRadiusLG: 12,
          },
          Table: {
            headerBg: '#fafafa',
            headerColor: '#262626',
            headerSplitColor: 'transparent',
          },
          Button: {
            borderRadius: 6,
          },
          Modal: {
            borderRadiusLG: 12,
          },
        },
      }}
    >
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="documents" element={<Documents />} />
            <Route path="documents/:id" element={<Documents />} />
            <Route path="cleaning" element={<CleaningRules />} />
            <Route path="qa" element={<QA />} />
            <Route path="retrieval" element={<RetrievalTest />} />
            <Route path="queue" element={<QueueManagement />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;
