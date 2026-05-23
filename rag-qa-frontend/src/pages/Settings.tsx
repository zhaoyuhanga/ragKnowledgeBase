import React, { useState, useEffect } from 'react';
import {
  Card,
  Tabs,
  Button,
  Space,
  Tag,
  Typography,
  Row,
  Col,
  Form,
  Switch,
  InputNumber,
  Select,
  Divider,
  Alert,
  Descriptions,
  Spin
} from 'antd';
import {
  SafetyCertificateOutlined,
  DatabaseOutlined,
  RocketOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined
} from '@ant-design/icons';
import { getAllHealthStatus } from '../services/health';
import { getEmbeddingStatistics } from '../services/embedding';
import { getKeywordStatistics } from '../services/keyword';
import type { ComponentHealth, EmbeddingStatistics, KeywordStatistics } from '../types/api';

const { Title, Text } = Typography;
const { Option } = Select;

const Settings: React.FC = () => {
  const [systemLoading, setSystemLoading] = useState(true);
  const [healthStatus, setHealthStatus] = useState<{
    health: { status: string; service: string; version: string; environment: string } | null;
    db: ComponentHealth | null;
    redis: ComponentHealth | null;
    milvus: ComponentHealth | null;
    rabbitmq: ComponentHealth | null;
  }>({
    health: null,
    db: null,
    redis: null,
    milvus: null,
    rabbitmq: null,
  });
  const [embeddingStats, setEmbeddingStats] = useState<EmbeddingStatistics | null>(null);
  const [keywordStats, setKeywordStats] = useState<KeywordStatistics | null>(null);

  useEffect(() => {
    loadHealthStatus();
  }, []);

  const loadHealthStatus = async () => {
    setSystemLoading(true);
    try {
      const status = await getAllHealthStatus();
      setHealthStatus({
        health: status.health.code === 0 ? status.health.data : null,
        db: status.db.code === 0 ? status.db.data : null,
        redis: status.redis.code === 0 ? status.redis.data : null,
        milvus: status.milvus.code === 0 ? status.milvus.data : null,
        rabbitmq: status.rabbitmq.code === 0 ? status.rabbitmq.data : null,
      });

      // 加载其他统计
      const [embRes, kwRes] = await Promise.all([
        getEmbeddingStatistics().catch(() => ({ code: -1, data: null })),
        getKeywordStatistics().catch(() => ({ code: -1, data: null })),
      ]);

      if (embRes.code === 0 && embRes.data) {
        setEmbeddingStats(embRes.data);
      }
      if (kwRes.code === 0 && kwRes.data) {
        setKeywordStats(kwRes.data);
      }
    } catch (error) {
      console.error('Failed to load health status:', error);
    } finally {
      setSystemLoading(false);
    }
  };

  const getStatusTag = (status: string | null | undefined) => {
    if (status === undefined || status === null) {
      return <Tag icon={<LoadingOutlined spin />}>检查中</Tag>;
    }
    if (status === 'connected' || status === 'healthy') {
      return <Tag color="success" icon={<CheckCircleOutlined />}>
        {status === 'connected' ? '已连接' : '健康'}
      </Tag>;
    }
    return <Tag color="error" icon={<CloseCircleOutlined />}>
      {status === 'disconnected' ? '未连接' : '异常'}
    </Tag>;
  };

  const renderHealthTab = () => (
    <div>
      {systemLoading ? (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <Spin size="large" tip="正在检查系统状态..." />
        </div>
      ) : (
        <>
          {/* 系统概览 */}
          {healthStatus.health && (
            <Card
              title="系统概览"
              style={{ marginBottom: 16 }}
              styles={{ body: { padding: '16px 24px' } }}
            >
              <Descriptions column={4}>
                <Descriptions.Item label="服务名称">
                  {healthStatus.health.service}
                </Descriptions.Item>
                <Descriptions.Item label="版本">
                  {healthStatus.health.version}
                </Descriptions.Item>
                <Descriptions.Item label="环境">
                  {healthStatus.health.environment}
                </Descriptions.Item>
                <Descriptions.Item label="状态">
                  {getStatusTag(healthStatus.health.status)}
                </Descriptions.Item>
              </Descriptions>
            </Card>
          )}

          {/* 组件状态 */}
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} lg={6}>
              <Card bordered={false}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Space>
                    <DatabaseOutlined style={{ fontSize: 24, color: '#1677ff' }} />
                    <Text strong>MySQL</Text>
                  </Space>
                  {getStatusTag(healthStatus.db?.status)}
                </Space>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card bordered={false}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Space>
                    <DatabaseOutlined style={{ fontSize: 24, color: '#ff4d4f' }} />
                    <Text strong>Redis</Text>
                  </Space>
                  {getStatusTag(healthStatus.redis?.status)}
                </Space>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card bordered={false}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Space>
                    <DatabaseOutlined style={{ fontSize: 24, color: '#52c41a' }} />
                    <Text strong>Milvus</Text>
                  </Space>
                  {getStatusTag(healthStatus.milvus?.status)}
                </Space>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card bordered={false}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Space>
                    <DatabaseOutlined style={{ fontSize: 24, color: '#faad14' }} />
                    <Text strong>RabbitMQ</Text>
                  </Space>
                  {getStatusTag(healthStatus.rabbitmq?.status)}
                </Space>
              </Card>
            </Col>
          </Row>

          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={loadHealthStatus}
            style={{ marginTop: 24 }}
          >
            刷新状态
          </Button>
        </>
      )}
    </div>
  );

  const renderDatabaseTab = () => (
    <div>
      <Card
        title="向量数据库统计"
        style={{ marginBottom: 16 }}
      >
        {embeddingStats ? (
          <Descriptions column={2}>
            <Descriptions.Item label="集合名称">
              {embeddingStats.collection_name}
            </Descriptions.Item>
            <Descriptions.Item label="向量维度">
              {embeddingStats.dimension}
            </Descriptions.Item>
            <Descriptions.Item label="总实体数">
              {embeddingStats.total_entities}
            </Descriptions.Item>
          </Descriptions>
        ) : (
          <Alert message="无法加载向量数据库统计" type="warning" showIcon />
        )}
      </Card>

      <Card title="关键词索引统计">
        {keywordStats ? (
          <Descriptions column={2}>
            <Descriptions.Item label="索引Chunk数">
              {keywordStats.total_indexed_chunks}
            </Descriptions.Item>
            <Descriptions.Item label="总词项数">
              {keywordStats.total_terms}
            </Descriptions.Item>
            <Descriptions.Item label="平均词项数/Chunk">
              {keywordStats.avg_terms_per_chunk.toFixed(2)}
            </Descriptions.Item>
          </Descriptions>
        ) : (
          <Alert message="无法加载关键词索引统计" type="warning" showIcon />
        )}
      </Card>
    </div>
  );

  const renderRetrievalTab = () => (
    <Card title="检索参数配置">
      <Form layout="vertical">
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="默认TopK">
              <InputNumber min={1} max={100} defaultValue={10} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="向量检索TopK">
              <InputNumber min={10} max={200} defaultValue={100} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="关键词检索TopK">
              <InputNumber min={10} max={200} defaultValue={100} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="默认融合方法">
              <Select defaultValue="rrf" style={{ width: '100%' }}>
                <Option value="rrf">RRF (倒数排名融合)</Option>
                <Option value="weighted">加权融合</Option>
                <Option value="rank">排名融合</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Divider />

        <Form.Item label="查询改写">
          <Space direction="vertical">
            <div>
              <Switch defaultChecked /> <Text style={{ marginLeft: 8 }}>启用查询改写</Text>
            </div>
            <div>
              <Switch defaultChecked /> <Text style={{ marginLeft: 8 }}>启用多查询生成</Text>
            </div>
            <div>
              <Switch /> <Text style={{ marginLeft: 8 }}>启用子查询分解</Text>
            </div>
          </Space>
        </Form.Item>

        <Form.Item>
          <Button type="primary">保存配置</Button>
        </Form.Item>
      </Form>
    </Card>
  );

  const renderQATab = () => (
    <Card title="问答参数配置">
      <Form layout="vertical">
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="默认TopK">
              <InputNumber min={1} max={50} defaultValue={20} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="重排后TopK">
              <InputNumber min={1} max={20} defaultValue={10} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="最大上下文Token数">
              <InputNumber min={1000} max={8000} step={500} defaultValue={4000} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="生成温度 (Temperature)">
              <InputNumber min={0} max={1} step={0.1} defaultValue={0.7} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item label="是否启用重排">
          <Switch defaultChecked />
        </Form.Item>

        <Form.Item>
          <Button type="primary">保存配置</Button>
        </Form.Item>
      </Form>
    </Card>
  );

  const tabItems = [
    {
      key: 'health',
      label: (
        <span>
          <SafetyCertificateOutlined />
          系统状态
        </span>
      ),
      children: renderHealthTab(),
    },
    {
      key: 'database',
      label: (
        <span>
          <DatabaseOutlined />
          数据库配置
        </span>
      ),
      children: renderDatabaseTab(),
    },
    {
      key: 'retrieval',
      label: (
        <span>
          <RocketOutlined />
          检索配置
        </span>
      ),
      children: renderRetrievalTab(),
    },
    {
      key: 'qa',
      label: (
        <span>
          <RocketOutlined />
          问答配置
        </span>
      ),
      children: renderQATab(),
    },
  ];

  return (
    <div className="fade-in">
      <div className="page-header">
        <Title level={2}>系统设置</Title>
        <Text type="secondary">系统配置、健康检查和参数管理</Text>
      </div>

      <Tabs items={tabItems} />
    </div>
  );
};

export default Settings;
