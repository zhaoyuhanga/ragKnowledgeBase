import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Input,
  Button,
  List,
  Typography,
  Spin,
  Avatar,
  Tag,
  Row,
  Col,
  message,
  Tabs,
  Table,
  Rate,
  Modal,
  Descriptions,
  Divider
} from 'antd';
import {
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  LikeOutlined,
  DislikeOutlined,
  HistoryOutlined,
  BarChartOutlined,
  FileTextOutlined,
  LoadingOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import {
  askQuestion,
  askQuestionStream,
  submitFeedback,
  getQALogs,
  getQALogDetail,
  getQASessions,
  getFeedbackStatistics
} from '../services/qa';
import type { QALogItem, QAFeedbackStatistics, QASession, QAResponseData, QALogDetailData } from '../types/api';
import { BASE_URL as API_BASE_URL } from '../services/api';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

interface ChatMessage {
  id: number;
  type: 'user' | 'assistant';
  content: string;
  references?: QAResponseData['references'];
  loading?: boolean;
  qaId?: number;
  feedback?: number;
  qualityScore?: number;
}

const QA: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const [activeTab, setActiveTab] = useState('chat');
  const [qaLogs, setQaLogs] = useState<QALogItem[]>([]);
  const [sessions, setSessions] = useState<QASession[]>([]);
  const [feedbackStats, setFeedbackStats] = useState<QAFeedbackStatistics | null>(null);
  const [logsLoading, setLogsLoading] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // 日志详情弹窗
  const [logDetailVisible, setLogDetailVisible] = useState(false);
  const [logDetail, setLogDetail] = useState<QALogDetailData | null>(null);
  const [logDetailLoading, setLogDetailLoading] = useState(false);

  useEffect(() => {
    loadQALogs();
    loadSessions();
    loadFeedbackStats();
  }, []);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const loadQALogs = async () => {
    setLogsLoading(true);
    try {
      const res = await getQALogs({ page_no: 1, page_size: 20 });
      if (res.code === 0 && res.data) {
        setQaLogs(res.data.items);
      }
    } catch (error) {
      console.error('Failed to load QA logs:', error);
    } finally {
      setLogsLoading(false);
    }
  };

  const loadSessions = async () => {
    try {
      const res = await getQASessions({ page_no: 1, page_size: 10 });
      if (res.code === 0 && res.data) {
        setSessions(res.data.items);
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const loadFeedbackStats = async () => {
    try {
      const res = await getFeedbackStatistics();
      if (res.code === 0 && res.data) {
        setFeedbackStats(res.data);
      }
    } catch (error) {
      console.error('Failed to load feedback stats:', error);
    }
  };

  // 查看日志详情
  const handleViewLogDetail = async (qaId: number) => {
    setLogDetailVisible(true);
    setLogDetailLoading(true);
    setLogDetail(null);

    try {
      const res = await getQALogDetail(qaId);
      if (res.code === 0 && res.data) {
        setLogDetail(res.data);
      } else {
        message.error(res.message || '获取详情失败');
      }
    } catch (error) {
      console.error('Failed to load log detail:', error);
      message.error('获取详情失败');
    } finally {
      setLogDetailLoading(false);
    }
  };

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    setLoading(true);

    const userMessage: ChatMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue.trim(),
    };

    const assistantMessage: ChatMessage = {
      id: Date.now() + 1,
      type: 'assistant',
      content: '',
      loading: true,
    };

    setMessages(prev => [...prev, userMessage, assistantMessage]);
    setInputValue('');

    try {
      // 使用流式接口
      await handleStreamQuestion(userMessage.content, assistantMessage.id);
    } catch (error) {
      console.error('QA request failed:', error);
      setMessages(prev =>
        prev.map(msg =>
          msg.id === assistantMessage.id
            ? { ...msg, content: '抱歉，网络请求失败，请检查网络连接。', loading: false }
            : msg
        )
      );
      message.error('网络请求失败');
      setLoading(false);
    }
  };

  // 流式问答处理
  const handleStreamQuestion = async (question: string, messageId: number) => {
    return new Promise<void>((resolve, reject) => {
      const fullContent: string[] = [];
      let qaId: number | undefined;
      let references: QAResponseData['references'] = [];

      // 创建AbortController用于取消请求
      abortControllerRef.current = new AbortController();

      fetch(`${API_BASE_URL}/qa/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question,
          session_id: sessionId,
          use_rerank: true,
          top_k: 20,
          rerank_top_k: 10,
        }),
        signal: abortControllerRef.current.signal,
      }).then(async (response) => {
        if (!response.ok) {
          throw new Error('请求失败');
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('无法读取响应流');
        }

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('event: ')) {
              continue;
            }
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));

                if (data.session_id) {
                  // 开始事件
                  console.log('Stream started:', data.session_id);
                } else if (data.qa_id && data.retrieval_time_ms !== undefined) {
                  // 元数据事件
                  qaId = data.qa_id;
                  // 获取引用信息
                  try {
                    const detailRes = await getQALogDetail(qaId);
                    if (detailRes.code === 0 && detailRes.data) {
                      references = detailRes.data.references || [];
                    }
                  } catch (e) {
                    console.error('Failed to get references:', e);
                  }
                } else if (data.content) {
                  // 内容事件
                  fullContent.push(data.content);
                  setMessages(prev =>
                    prev.map(msg =>
                      msg.id === messageId
                        ? { ...msg, content: fullContent.join(''), loading: false }
                        : msg
                    )
                  );
                } else if (data.error) {
                  // 错误事件
                  throw new Error(data.error);
                }
              } catch (e) {
                // 忽略解析错误
              }
            }
          }
        }

        // 流结束
        setMessages(prev =>
          prev.map(msg =>
            msg.id === messageId
              ? {
                  ...msg,
                  content: fullContent.join('') || '抱歉，未能获取到答案。',
                  qaId,
                  references,
                  loading: false,
                }
              : msg
          )
        );

        // 刷新日志列表
        loadQALogs();
        resolve();
      }).catch((error) => {
        if (error.name === 'AbortError') {
          console.log('Request was cancelled');
        } else {
          console.error('Stream error:', error);
          setMessages(prev =>
            prev.map(msg =>
              msg.id === messageId
                ? { ...msg, content: `抱歉，发生错误: ${error.message}`, loading: false }
                : msg
            )
          );
        }
      });
    }).finally(() => {
      setLoading(false);
      abortControllerRef.current = null;
    });
  };

  const handleFeedback = async (qaId: number, feedback: number) => {
    try {
      const res = await submitFeedback({
        qa_id: qaId,
        feedback,
        quality_score: feedback === 1 ? 5 : 1,
      });
      if (res.code === 0) {
        message.success('反馈成功');
        setMessages(prev =>
          prev.map(msg =>
            msg.qaId === qaId ? { ...msg, feedback } : msg
          )
        );
        loadFeedbackStats();
      } else {
        message.error(res.message || '反馈失败');
      }
    } catch (error) {
      console.error('Feedback failed:', error);
      message.error('反馈失败');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const renderReference = (references: QAResponseData['references'], qaId?: number) => {
    if (!references || references.length === 0) {
      // 如果没有引用但有qaId，提供查看详情的选项
      if (qaId) {
        return (
          <div style={{ marginTop: 8 }}>
            <Button
              type="link"
              size="small"
              icon={<FileTextOutlined />}
              onClick={() => handleViewLogDetail(qaId)}
            >
              查看引用文档
            </Button>
          </div>
        );
      }
      return null;
    }

    const displayRefs = references.slice(0, 5); // 最多显示5个引用

    return (
      <div className="qa-references" style={{ marginTop: 8, padding: '8px 12px', background: '#f8f8f8', borderRadius: 8 }}>
        <Row align="middle" style={{ marginBottom: 8 }}>
          <FileTextOutlined style={{ marginRight: 6 }} />
          <Text type="secondary" style={{ fontSize: 12 }}>
            参考文档 ({references.length})
          </Text>
          {qaId && (
            <Button
              type="link"
              size="small"
              style={{ marginLeft: 'auto', padding: 0, height: 'auto' }}
              onClick={() => handleViewLogDetail(qaId)}
            >
              查看详情
            </Button>
          )}
        </Row>
        {displayRefs.map((ref: any, index: number) => (
          <div
            key={index}
            className="qa-reference-item"
            style={{
              marginBottom: 8,
              padding: '6px 8px',
              background: '#fff',
              borderRadius: 4,
              border: '1px solid #e8e8e8'
            }}
          >
            <Row align="middle" style={{ marginBottom: 4 }}>
              <Tag color="blue" style={{ marginRight: 6 }}>{index + 1}</Tag>
              <Text strong style={{ fontSize: 12 }}>{ref.title_path || '未知文档'}</Text>
              {ref.page_start && (
                <Text type="secondary" style={{ fontSize: 11, marginLeft: 8 }}>
                  第{ref.page_start}页
                </Text>
              )}
            </Row>
            <Paragraph
              ellipsis={{ rows: 2, expandable: true, symbol: '展开' }}
              style={{ margin: 0, fontSize: 12 }}
            >
              {ref.content_preview || ref.content || '暂无内容'}
            </Paragraph>
            {ref.score !== undefined && (
              <Text type="secondary" style={{ fontSize: 10 }}>
                相关度: {(ref.score * 100).toFixed(1)}%
              </Text>
            )}
          </div>
        ))}
        {references.length > 5 && (
          <Text type="secondary" style={{ fontSize: 11 }}>
            还有 {references.length - 5} 个引用...
          </Text>
        )}
      </div>
    );
  };

  const logsColumns: ColumnsType<QALogItem> = [
    {
      title: '问题',
      dataIndex: 'question',
      key: 'question',
      width: 250,
      ellipsis: true,
      render: (text: string) => <Text ellipsis={{ tooltip: text }}>{text}</Text>,
    },
    {
      title: '答案预览',
      dataIndex: 'answer',
      key: 'answer',
      ellipsis: true,
      render: (text: string) => <Text ellipsis={{ tooltip: text }}>{text || '-'}</Text>,
    },
    {
      title: '反馈',
      dataIndex: 'feedback',
      key: 'feedback',
      width: 100,
      render: (feedback: number) => (
        feedback === 1 ? <Tag color="success">满意</Tag> :
        feedback === 0 ? <Tag color="error">不满意</Tag> : '-'
      ),
    },
    {
      title: '评分',
      dataIndex: 'quality_score',
      key: 'quality_score',
      width: 120,
      render: (score: number) => score ? <Rate disabled defaultValue={score} style={{ fontSize: 12 }} /> : '-',
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Button
          type="link"
          size="small"
          onClick={() => handleViewLogDetail(record.id)}
        >
          查看详情
        </Button>
      ),
    },
  ];

  const tabItems = [
    {
      key: 'chat',
      label: (
        <span>
          <RobotOutlined />
          智能问答
        </span>
      ),
      children: (
        <div style={{ display: 'flex', height: 'calc(100vh - 280px)', gap: 24 }}>
          {/* 聊天区域 */}
          <Card
            style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
            styles={{ body: { flex: 1, display: 'flex', flexDirection: 'column', padding: 0 } }}
          >
            {/* 消息列表 */}
            <div
              ref={chatContainerRef}
              style={{
                flex: 1,
                overflow: 'auto',
                padding: '16px 24px',
              }}
            >
              {messages.length === 0 && (
                <div style={{ textAlign: 'center', padding: '40px 0', color: '#8c8c8c' }}>
                  <RobotOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                  <div>请输入您的问题开始对话</div>
                  <div style={{ marginTop: 8, fontSize: 12 }}>
                    支持流式输出，答案将逐字显示
                  </div>
                </div>
              )}
              {messages.map(msg => (
                <div
                  key={msg.id}
                  className={`qa-message ${msg.type}`}
                  style={{
                    marginBottom: 16,
                    display: 'flex',
                    flexDirection: msg.type === 'user' ? 'row-reverse' : 'row',
                    alignItems: 'flex-start',
                    gap: 12,
                  }}
                >
                  <Avatar
                    icon={msg.type === 'user' ? <UserOutlined /> : <RobotOutlined />}
                    style={{
                      backgroundColor: msg.type === 'user' ? '#1677ff' : '#52c41a',
                    }}
                  />
                  <div style={{ maxWidth: '70%' }}>
                    <div
                      style={{
                        padding: '8px 16px',
                        borderRadius: 8,
                        background: msg.type === 'user' ? '#1677ff' : '#f5f5f5',
                        color: msg.type === 'user' ? '#fff' : '#262626',
                      }}
                    >
                      {msg.loading ? (
                        <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <LoadingOutlined />
                          <span>正在思考...</span>
                        </span>
                      ) : (
                        <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
                          {msg.content}
                        </div>
                      )}
                    </div>
                    {!msg.loading && msg.references && renderReference(msg.references, msg.qaId)}
                    {!msg.loading && !msg.references && msg.qaId && (
                      <Button
                        type="link"
                        size="small"
                        style={{ padding: 0, marginTop: 4 }}
                        onClick={() => handleViewLogDetail(msg.qaId!)}
                      >
                        查看引用文档
                      </Button>
                    )}
                    {!msg.loading && msg.qaId && (
                      <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
                        {msg.feedback === undefined ? (
                          <>
                            <Button
                              size="small"
                              icon={<LikeOutlined />}
                              onClick={() => handleFeedback(msg.qaId!, 1)}
                            >
                              满意
                            </Button>
                            <Button
                              size="small"
                              danger
                              icon={<DislikeOutlined />}
                              onClick={() => handleFeedback(msg.qaId!, 0)}
                            >
                              不满意
                            </Button>
                          </>
                        ) : (
                          <Tag color={msg.feedback === 1 ? 'success' : 'error'}>
                            {msg.feedback === 1 ? '已满意' : '已不满意'}
                          </Tag>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* 输入区域 */}
            <div
              style={{
                borderTop: '1px solid #f0f0f0',
                padding: '12px 24px',
                display: 'flex',
                gap: 12,
                alignItems: 'flex-end',
              }}
            >
              <TextArea
                value={inputValue}
                onChange={e => setInputValue(e.target.value)}
                onPressEnter={handleKeyPress}
                placeholder="请输入您的问题，按Enter发送..."
                autoSize={{ minRows: 1, maxRows: 4 }}
                style={{ flex: 1 }}
              />
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleSend}
                loading={loading}
              >
                发送
              </Button>
            </div>
          </Card>

          {/* 侧边栏 */}
          <div style={{ width: 280 }}>
            <Card
              title="会话历史"
              extra={<Button type="link" size="small" icon={<HistoryOutlined />} onClick={loadSessions}>
                刷新
              </Button>}
              style={{ marginBottom: 16 }}
              styles={{ body: { padding: 0 } }}
            >
              <List
                size="small"
                dataSource={sessions}
                renderItem={item => (
                  <List.Item style={{ padding: '8px 12px', cursor: 'pointer' }}>
                    <Text ellipsis={{ tooltip: item.session_id }}>
                      {item.last_question || '新会话'}
                    </Text>
                  </List.Item>
                )}
                locale={{ emptyText: '暂无会话记录' }}
              />
            </Card>

            <Card
              title="反馈统计"
              extra={<Button type="link" size="small" icon={<BarChartOutlined />} onClick={loadFeedbackStats}>
                刷新
              </Button>}
            >
              {feedbackStats && (
                <div>
                  <Row gutter={[8, 8]}>
                    <Col span={12}>
                      <Text type="secondary">总反馈数</Text>
                      <div style={{ fontSize: 20, fontWeight: 600 }}>
                        {feedbackStats.total_count}
                      </div>
                    </Col>
                    <Col span={12}>
                      <Text type="secondary">满意率</Text>
                      <div style={{ fontSize: 20, fontWeight: 600, color: '#52c41a' }}>
                        {feedbackStats.positive_rate.toFixed(1)}%
                      </div>
                    </Col>
                  </Row>
                </div>
              )}
            </Card>
          </div>
        </div>
      ),
    },
    {
      key: 'logs',
      label: (
        <span>
          <HistoryOutlined />
          问答日志
        </span>
      ),
      children: (
        <Card bordered={false}>
          <Table
            columns={logsColumns}
            dataSource={qaLogs}
            rowKey="id"
            loading={logsLoading}
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 条`,
            }}
          />
        </Card>
      ),
    },
  ];

  return (
    <div className="fade-in">
      <div className="page-header">
        <Title level={2}>问答管理</Title>
        <Text type="secondary">基于RAG的智能问答系统</Text>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
      />

      {/* 日志详情弹窗 */}
      <Modal
        title="问答详情"
        open={logDetailVisible}
        onCancel={() => setLogDetailVisible(false)}
        footer={null}
        width={800}
        styles={{ body: { maxHeight: '60vh', overflow: 'auto' } }}
      >
        {logDetailLoading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin tip="加载中..." />
          </div>
        ) : logDetail ? (
          <>
            <Descriptions bordered column={2} size="small">
              <Descriptions.Item label="问题" span={2}>
                {logDetail.question}
              </Descriptions.Item>
              <Descriptions.Item label="会话ID">
                {logDetail.session_id}
              </Descriptions.Item>
              <Descriptions.Item label="反馈">
                {logDetail.feedback === 'helpful' ? <Tag color="success">满意</Tag> :
                 logDetail.feedback === 'not_helpful' ? <Tag color="error">不满意</Tag> : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="评分">
                {logDetail.quality_score ? <Rate disabled defaultValue={logDetail.quality_score} style={{ fontSize: 12 }} /> : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="检索耗时">
                {logDetail.retrieval_time_ms}ms
              </Descriptions.Item>
              <Descriptions.Item label="生成耗时">
                {logDetail.generation_time_ms}ms
              </Descriptions.Item>
              <Descriptions.Item label="总耗时">
                {logDetail.total_time_ms}ms
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {dayjs(logDetail.created_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
            </Descriptions>

            <Divider>答案</Divider>
            <div style={{ background: '#f5f5f5', padding: 16, borderRadius: 8, whiteSpace: 'pre-wrap' }}>
              {logDetail.answer || '暂无答案'}
            </div>

            {logDetail.references && logDetail.references.length > 0 && (
              <>
                <Divider>参考文档 ({logDetail.references.length})</Divider>
                {logDetail.references.map((ref: any, index: number) => (
                  <Card key={index} size="small" style={{ marginBottom: 12 }}>
                    <Row align="middle" style={{ marginBottom: 8 }}>
                      <Tag color="blue" style={{ marginRight: 8 }}>{index + 1}</Tag>
                      <Text strong>{ref.title_path || '未知文档'}</Text>
                      {ref.page_start && (
                        <Text type="secondary" style={{ marginLeft: 8 }}>第{ref.page_start}页</Text>
                      )}
                    </Row>
                    <Paragraph style={{ margin: 0, fontSize: 13 }}>
                      {ref.content_preview || ref.content || '暂无内容'}
                    </Paragraph>
                    {ref.score !== undefined && (
                      <Text type="secondary" style={{ fontSize: 11, marginTop: 4, display: 'block' }}>
                        相关度: {(ref.score * 100).toFixed(1)}%
                      </Text>
                    )}
                  </Card>
                ))}
              </>
            )}

            {logDetail.feedback_reason && (
              <>
                <Divider>反馈原因</Divider>
                <div style={{ color: '#faad14' }}>
                  {logDetail.feedback_reason}
                </div>
              </>
            )}
          </>
        ) : (
          <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
            暂无详情数据
          </div>
        )}
      </Modal>
    </div>
  );
};

export default QA;
