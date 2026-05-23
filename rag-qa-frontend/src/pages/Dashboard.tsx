import React, { useEffect, useState } from 'react';
import { Card, Row, Col, List, Typography, Tag, Space } from 'antd';
import {
  FileTextOutlined,
  CheckCircleOutlined,
  RightOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { DashboardStats } from '../components/Stats';
import { getDocuments } from '../services/documents';
import { getQALogs } from '../services/qa';
import type { DocumentItem, QALogItem } from '../types/api';

const { Title, Text } = Typography;

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalDocuments: 0,
    parsedDocuments: 0,
    pendingDocuments: 0,
    failedDocuments: 0,
    totalChunks: 0,
    avgQuality: 0,
  });
  const [recentDocuments, setRecentDocuments] = useState<DocumentItem[]>([]);
  const [recentQA, setRecentQA] = useState<QALogItem[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // 加载文档列表
      const docsRes = await getDocuments({ page_no: 1, page_size: 5 });
      if (docsRes.code === 0 && docsRes.data) {
        setRecentDocuments(docsRes.data.items);
        
        // 统计
        const docs = docsRes.data.items;
        let parsed = 0, pending = 0, failed = 0, chunks = 0;
        docs.forEach(doc => {
          if (doc.status === 2) parsed++;
          else if (doc.status === 0 || doc.status === 1) pending++;
          else if (doc.status === 3) failed++;
          chunks += doc.total_chunks || 0;
        });
        
        setStats(prev => ({
          ...prev,
          totalDocuments: docsRes.data.total,
          parsedDocuments: parsed,
          pendingDocuments: pending,
          failedDocuments: failed,
          totalChunks: chunks,
        }));
      }

      // 加载最近问答
      const qaRes = await getQALogs({ page_no: 1, page_size: 5 });
      if (qaRes.code === 0 && qaRes.data) {
        setRecentQA(qaRes.data.items);
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getDocStatusTag = (status: number) => {
    const statusMap: Record<number, { color: string; text: string }> = {
      0: { color: 'default', text: '待解析' },
      1: { color: 'processing', text: '解析中' },
      2: { color: 'success', text: '已解析' },
      3: { color: 'error', text: '解析失败' },
      9: { color: 'default', text: '已删除' },
    };
    const config = statusMap[status] || { color: 'default', text: '未知' };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <Title level={2}>仪表盘</Title>
        <Text type="secondary">RAG知识库系统概览</Text>
      </div>

      {/* 统计卡片 */}
      <DashboardStats stats={stats} loading={loading} />

      {/* 最近文档和问答 */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <FileTextOutlined />
                <span>最近文档</span>
              </Space>
            }
            extra={
              <a onClick={() => navigate('/documents')}>
                查看更多 <RightOutlined />
              </a>
            }
            bordered={false}
            styles={{ body: { padding: 0 } }}
          >
            <List
              loading={loading}
              dataSource={recentDocuments}
              renderItem={(item) => (
                <List.Item style={{ padding: '12px 24px', cursor: 'pointer' }}>
                  <List.Item.Meta
                    avatar={
                      <div className={`doc-type-icon ${item.doc_type.toLowerCase()}`}>
                        {item.doc_type.toUpperCase().slice(0, 3)}
                      </div>
                    }
                    title={<a onClick={() => navigate(`/documents/${item.id}`)}>{item.name}</a>}
                    description={
                      <Space>
                        {getDocStatusTag(item.status)}
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {item.total_chunks} 个Chunk
                        </Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <CheckCircleOutlined />
                <span>最近问答</span>
              </Space>
            }
            extra={
              <a onClick={() => navigate('/qa')}>
                查看更多 <RightOutlined />
              </a>
            }
            bordered={false}
            styles={{ body: { padding: 0 } }}
          >
            <List
              loading={loading}
              dataSource={recentQA}
              renderItem={(item) => (
                <List.Item style={{ padding: '12px 24px' }}>
                  <List.Item.Meta
                    title={<Text ellipsis={{ tooltip: item.question }}>{item.question}</Text>}
                    description={
                      <Text type="secondary" style={{ fontSize: 12 }} ellipsis={{ tooltip: item.answer }}>
                        {item.answer}
                      </Text>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
