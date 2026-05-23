import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Typography,
  Row,
  Col,
  Statistic,
  Spin,
  message,
  Alert
} from 'antd';
import {
  DatabaseOutlined,
  ReloadOutlined,
  SyncOutlined,
  DeleteOutlined,
  InboxOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import {
  getQueues,
  getQueueStats,
  getDLXMessages,
  clearDLXMessages,
  deleteDLXMessage
} from '../services/queue';
import type { QueueInfo, QueueStatistics, DLXMessage } from '../types/api';

const { Title, Text } = Typography;

const QueueManagement: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [queues, setQueues] = useState<QueueInfo[]>([]);
  const [queueStats, setQueueStats] = useState<Record<string, QueueStatistics>>({});
  const [dlxMessages, setDlxMessages] = useState<DLXMessage[]>([]);
  const [dlxLoading, setDlxLoading] = useState(false);
  const [clearing, setClearing] = useState(false);

  const loadQueues = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getQueues();
      if (res.code === 0 && res.data) {
        setQueues(res.data.queues);
        
        // 加载每个队列的统计
        const statsPromises = res.data.queues.map(async (queue) => {
          try {
            const statsRes = await getQueueStats(queue.name);
            if (statsRes.code === 0) {
              return { [queue.name]: statsRes.data };
            }
          } catch (e) {
            console.error(`Failed to load stats for ${queue.name}:`, e);
          }
          return { [queue.name]: null };
        });
        
        const statsResults = await Promise.all(statsPromises);
        const statsMap: Record<string, QueueStatistics> = {};
        statsResults.forEach(result => {
          Object.entries(result).forEach(([key, value]) => {
            if (value) {
              statsMap[key] = value;
            }
          });
        });
        setQueueStats(statsMap);
      }
    } catch (error) {
      console.error('Failed to load queues:', error);
      message.error('加载队列列表失败');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadDLXMessages = useCallback(async () => {
    setDlxLoading(true);
    try {
      const res = await getDLXMessages(20, 0);
      if (res.code === 0 && res.data) {
        setDlxMessages(res.data.messages);
      }
    } catch (error) {
      console.error('Failed to load DLX messages:', error);
      message.error('加载死信队列失败');
    } finally {
      setDlxLoading(false);
    }
  }, []);

  useEffect(() => {
    loadQueues();
    loadDLXMessages();
  }, [loadQueues, loadDLXMessages]);

  const handleClearDLX = async () => {
    setClearing(true);
    try {
      const res = await clearDLXMessages();
      if (res.code === 0) {
        message.success('死信队列已清空');
        loadDLXMessages();
      } else {
        message.error(res.message || '清空失败');
      }
    } catch (error) {
      console.error('Failed to clear DLX:', error);
      message.error('清空失败');
    } finally {
      setClearing(false);
    }
  };

  const handleDeleteDLXMessage = async (messageId: string) => {
    try {
      const res = await deleteDLXMessage(messageId);
      if (res.code === 0) {
        message.success('删除成功');
        loadDLXMessages();
      } else {
        message.error(res.message || '删除失败');
      }
    } catch (error) {
      console.error('Failed to delete DLX message:', error);
      message.error('删除失败');
    }
  };

  const queueColumns: ColumnsType<QueueInfo & { stats?: QueueStatistics }> = [
    {
      title: '队列名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (name: string) => <Tag color="blue">{name}</Tag>,
    },
    {
      title: '显示名称',
      dataIndex: 'display_name',
      key: 'display_name',
      width: 200,
    },
    {
      title: '消息数量',
      key: 'message_count',
      width: 120,
      render: (_, record) => {
        const stats = queueStats[record.name];
        return stats ? (
          <Tag color={stats.message_count > 0 ? 'warning' : 'success'}>
            {stats.message_count}
          </Tag>
        ) : '-';
      },
    },
    {
      title: '消费者数量',
      key: 'consumer_count',
      width: 120,
      render: (_, record) => {
        const stats = queueStats[record.name];
        return stats ? stats.consumer_count : '-';
      },
    },
    {
      title: '状态',
      key: 'status',
      width: 100,
      render: (_, record) => {
        const stats = queueStats[record.name];
        if (!stats) return <Tag>检查中</Tag>;
        return stats.consumer_count > 0 ? (
          <Tag color="success">运行中</Tag>
        ) : (
          <Tag color="default">空闲</Tag>
        );
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: () => (
        <Button type="link" size="small" icon={<SyncOutlined />}>
          刷新
        </Button>
      ),
    },
  ];

  const dlxColumns: ColumnsType<DLXMessage> = [
    {
      title: '消息ID',
      dataIndex: 'message_id',
      key: 'message_id',
      width: 200,
      ellipsis: true,
    },
    {
      title: '内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Button
          type="link"
          size="small"
          danger
          icon={<DeleteOutlined />}
          onClick={() => handleDeleteDLXMessage(record.message_id)}
        >
          删除
        </Button>
      ),
    },
  ];

  const getTotalMessages = () => {
    return Object.values(queueStats).reduce((sum, stats) => sum + stats.message_count, 0);
  };

  const getTotalConsumers = () => {
    return Object.values(queueStats).reduce((sum, stats) => sum + stats.consumer_count, 0);
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <Title level={2}>队列管理</Title>
        <Text type="secondary">管理系统消息队列，监控队列状态和处理死信消息</Text>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card bordered={false}>
            <Statistic
              title="队列总数"
              value={queues.length}
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card bordered={false}>
            <Statistic
              title="总消息数"
              value={getTotalMessages()}
              valueStyle={{ color: getTotalMessages() > 0 ? '#faad14' : '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card bordered={false}>
            <Statistic
              title="总消费者"
              value={getTotalConsumers()}
            />
          </Card>
        </Col>
      </Row>

      {/* 队列列表 */}
      <Card
        title="队列列表"
        extra={
          <Button icon={<ReloadOutlined />} onClick={loadQueues} loading={loading}>
            刷新
          </Button>
        }
        style={{ marginBottom: 24 }}
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin />
          </div>
        ) : (
          <Table
            columns={queueColumns}
            dataSource={queues.map(q => ({ ...q, stats: queueStats[q.name] }))}
            rowKey="name"
            pagination={false}
          />
        )}
      </Card>

      {/* 死信队列 */}
      <Card
        title={
          <Space>
            <InboxOutlined />
            <span>死信队列 (DLX)</span>
            {dlxMessages.length > 0 && (
              <Tag color="error">{dlxMessages.length} 条</Tag>
            )}
          </Space>
        }
        extra={
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadDLXMessages}
              loading={dlxLoading}
            >
              刷新
            </Button>
            {dlxMessages.length > 0 && (
              <Button
                danger
                icon={<DeleteOutlined />}
                onClick={handleClearDLX}
                loading={clearing}
              >
                清空
              </Button>
            )}
          </Space>
        }
      >
        {dlxMessages.length === 0 ? (
          <Alert
            message="死信队列为空"
            description="目前没有失败的消息"
            type="success"
            showIcon
          />
        ) : (
          <Table
            columns={dlxColumns}
            dataSource={dlxMessages}
            rowKey="message_id"
            pagination={false}
            loading={dlxLoading}
          />
        )}
      </Card>
    </div>
  );
};

export default QueueManagement;
