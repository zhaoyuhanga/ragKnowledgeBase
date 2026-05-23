import React from 'react';
import { Card, Row, Col } from 'antd';
import {
  FileTextOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';

interface StatisticCardProps {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  color: string;
  suffix?: string;
  loading?: boolean;
}

const StatisticCard: React.FC<StatisticCardProps> = ({
  title,
  value,
  icon,
  color,
  suffix,
  loading = false
}) => {
  return (
    <Card
      bordered={false}
      style={{
        borderRadius: 8,
        boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03)',
      }}
      styles={{ body: { padding: '20px 24px' } }}
      loading={loading}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <div style={{ color: '#8c8c8c', fontSize: 14, marginBottom: 8 }}>{title}</div>
          <div style={{ fontSize: 28, fontWeight: 600 }}>
            {value}
            {suffix && <span style={{ fontSize: 14, marginLeft: 4, color: '#8c8c8c' }}>{suffix}</span>}
          </div>
        </div>
        <div
          style={{
            width: 56,
            height: 56,
            borderRadius: 8,
            background: `${color}15`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 28,
            color: color,
          }}
        >
          {icon}
        </div>
      </div>
    </Card>
  );
};

interface DashboardStatsProps {
  stats?: {
    totalDocuments: number;
    parsedDocuments: number;
    pendingDocuments: number;
    failedDocuments: number;
    totalChunks: number;
    avgQuality: number;
  };
  loading?: boolean;
}

const DashboardStats: React.FC<DashboardStatsProps> = ({ stats, loading = false }) => {
  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} sm={12} lg={6}>
        <StatisticCard
          title="文档总数"
          value={stats?.totalDocuments ?? 0}
          icon={<FileTextOutlined />}
          color="#1677ff"
          loading={loading}
        />
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <StatisticCard
          title="已解析"
          value={stats?.parsedDocuments ?? 0}
          icon={<CheckCircleOutlined />}
          color="#52c41a"
          loading={loading}
        />
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <StatisticCard
          title="待解析"
          value={stats?.pendingDocuments ?? 0}
          icon={<ClockCircleOutlined />}
          color="#faad14"
          loading={loading}
        />
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <StatisticCard
          title="解析失败"
          value={stats?.failedDocuments ?? 0}
          icon={<ExclamationCircleOutlined />}
          color="#ff4d4f"
          loading={loading}
        />
      </Col>
    </Row>
  );
};

export { StatisticCard, DashboardStats };
