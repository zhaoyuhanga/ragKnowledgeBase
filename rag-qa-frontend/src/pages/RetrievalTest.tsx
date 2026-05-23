import React, { useState, useCallback } from 'react';
import {
  Card,
  Input,
  Button,
  Space,
  Typography,
  Spin,
  Row,
  Col,
  Select,
  Switch,
  Slider,
  Table,
  Tag,
  Divider,
  message,
  Collapse,
  Statistic,
  Progress
} from 'antd';
import {
  SearchOutlined,
  ReloadOutlined,
  ThunderboltOutlined,
  SettingOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import {
  hybridSearch,
  rewriteQuery,
  getRetrievalStatistics
} from '../services/retrieval';
import type { HybridSearchResponse, RetrievalStatistics } from '../types/api';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;
const { Panel } = Collapse;

const RetrievalTest: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<HybridSearchResponse | null>(null);
  const [rewriteResults, setRewriteResults] = useState<{
    normalized_query: string;
    multi_queries: string[];
    sub_queries: string[];
  } | null>(null);
  const [stats, setStats] = useState<RetrievalStatistics | null>(null);

  // 检索参数
  const [topK, setTopK] = useState(10);
  const [enableRewrite, setEnableRewrite] = useState(false);
  const [fusionMethod, setFusionMethod] = useState<'rrf' | 'weighted' | 'rank'>('rrf');
  const [vectorTopK, setVectorTopK] = useState(100);
  const [keywordTopK, setKeywordTopK] = useState(100);
  const [rewriteConfig, setRewriteConfig] = useState({
    enable_multi_query: true,
    enable_subquery: false,
    enable_hyde: false,
    enable_background: false,
    max_queries: 5,
  });

  const loadStats = useCallback(async () => {
    try {
      const res = await getRetrievalStatistics();
      if (res.code === 0 && res.data) {
        setStats(res.data);
      }
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  }, []);

  const handleSearch = async () => {
    if (!query.trim()) {
      message.warning('请输入查询内容');
      return;
    }

    setLoading(true);
    setResults(null);
    setRewriteResults(null);

    try {
      // 查询改写
      if (enableRewrite) {
        const rewriteRes = await rewriteQuery({
          query,
          ...rewriteConfig,
        });
        if (rewriteRes.code === 0 && rewriteRes.data) {
          setRewriteResults(rewriteRes.data);
        }
      }

      // 混合检索
      const searchRes = await hybridSearch({
        query,
        top_k: topK,
        fusion_method: fusionMethod,
        enable_rewrite: enableRewrite,
        vector_top_k: vectorTopK,
        keyword_top_k: keywordTopK,
      });

      if (searchRes.code === 0 && searchRes.data) {
        setResults(searchRes.data);
        message.success(`检索完成，返回 ${searchRes.data.total} 条结果`);
      } else {
        message.error(searchRes.message || '检索失败');
      }
    } catch (error) {
      console.error('Search failed:', error);
      message.error('检索请求失败');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setQuery('');
    setResults(null);
    setRewriteResults(null);
  };

  const columns: ColumnsType<HybridSearchResponse['results'][0]> = [
    {
      title: '排名',
      key: 'rank',
      width: 60,
      render: (_, __, index) => index + 1,
    },
    {
      title: '文档路径',
      key: 'title_path',
      width: 200,
      render: (_, record) => (
        <Tag color="blue">{record.chunk.title_path || '无标题'}</Tag>
      ),
    },
    {
      title: '内容',
      key: 'content',
      render: (_, record) => (
        <Paragraph ellipsis={{ rows: 3, tooltip: true }}>
          {record.chunk.content}
        </Paragraph>
      ),
    },
    {
      title: '综合得分',
      key: 'fusion_score',
      width: 100,
      sorter: (a, b) => a.fusion_score - b.fusion_score,
      render: (score: number) => (
        <Progress
          percent={Math.round((score || 0) * 100)}
          size="small"
          format={(p) => ((p || 0) / 100).toFixed(2)}
        />
      ),
    },
    {
      title: '向量得分',
      dataIndex: ['vector_score'],
      key: 'vector_score',
      width: 100,
      render: (score: number) => score?.toFixed(4) || '-',
    },
    {
      title: '关键词得分',
      dataIndex: ['keyword_score'],
      key: 'keyword_score',
      width: 100,
      render: (score: number) => score?.toFixed(4) || '-',
    },
  ];

  return (
    <div className="fade-in">
      <div className="page-header">
        <Title level={2}>检索测试</Title>
        <Text type="secondary">测试混合检索、查询改写等功能</Text>
      </div>

      <Row gutter={[16, 16]}>
        {/* 左侧配置区域 */}
        <Col xs={24} lg={16}>
          <Card
            title={
              <Space>
                <SearchOutlined />
                <span>检索测试</span>
              </Space>
            }
            extra={
              <Button icon={<ReloadOutlined />} onClick={handleReset}>
                重置
              </Button>
            }
          >
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <TextArea
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="请输入查询内容..."
                autoSize={{ minRows: 3, maxRows: 6 }}
              />

              <Collapse defaultActiveKey={['settings']}>
                <Panel header={<Space><SettingOutlined />检索参数</Space>} key="settings">
                  <Row gutter={[16, 16]}>
                    <Col span={12}>
                      <Text type="secondary">返回数量 (top_k)</Text>
                      <Slider
                        min={1}
                        max={50}
                        value={topK}
                        onChange={setTopK}
                        marks={{ 1: '1', 10: '10', 20: '20', 50: '50' }}
                      />
                    </Col>
                    <Col span={12}>
                      <Text type="secondary">融合方法</Text>
                      <Select
                        value={fusionMethod}
                        onChange={setFusionMethod}
                        style={{ width: '100%' }}
                      >
                        <Option value="rrf">RRF (倒数排名融合)</Option>
                        <Option value="weighted">加权融合</Option>
                        <Option value="rank">排名融合</Option>
                      </Select>
                    </Col>
                    <Col span={12}>
                      <Text type="secondary">向量检索数量 (vector_top_k)</Text>
                      <Slider
                        min={10}
                        max={200}
                        value={vectorTopK}
                        onChange={setVectorTopK}
                        marks={{ 10: '10', 50: '50', 100: '100', 200: '200' }}
                      />
                    </Col>
                    <Col span={12}>
                      <Text type="secondary">关键词检索数量 (keyword_top_k)</Text>
                      <Slider
                        min={10}
                        max={200}
                        value={keywordTopK}
                        onChange={setKeywordTopK}
                        marks={{ 10: '10', 50: '50', 100: '100', 200: '200' }}
                      />
                    </Col>
                  </Row>
                </Panel>
                <Panel header={<Space><ThunderboltOutlined />查询改写</Space>} key="rewrite">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Switch
                        checked={enableRewrite}
                        onChange={setEnableRewrite}
                      />
                      <Text style={{ marginLeft: 8 }}>启用查询改写</Text>
                    </div>
                    {enableRewrite && (
                      <Row gutter={[16, 16]}>
                        <Col span={12}>
                          <Switch
                            checked={rewriteConfig.enable_multi_query}
                            onChange={v => setRewriteConfig(prev => ({ ...prev, enable_multi_query: v }))}
                          />
                          <Text style={{ marginLeft: 8 }}>多查询生成</Text>
                        </Col>
                        <Col span={12}>
                          <Switch
                            checked={rewriteConfig.enable_subquery}
                            onChange={v => setRewriteConfig(prev => ({ ...prev, enable_subquery: v }))}
                          />
                          <Text style={{ marginLeft: 8 }}>子查询分解</Text>
                        </Col>
                        <Col span={12}>
                          <Text type="secondary">最大查询数量</Text>
                          <Slider
                            min={1}
                            max={10}
                            value={rewriteConfig.max_queries}
                            onChange={v => setRewriteConfig(prev => ({ ...prev, max_queries: v }))}
                          />
                        </Col>
                      </Row>
                    )}
                  </Space>
                </Panel>
              </Collapse>

              <Button
                type="primary"
                icon={<SearchOutlined />}
                onClick={handleSearch}
                loading={loading}
                block
                size="large"
              >
                开始检索
              </Button>
            </Space>
          </Card>

          {/* 改写结果 */}
          {rewriteResults && (
            <Card
              title="查询改写结果"
              style={{ marginTop: 16 }}
              styles={{ body: { padding: '12px 24px' } }}
            >
              <div style={{ marginBottom: 16 }}>
                <Text type="secondary">规范化查询: </Text>
                <Text strong>{rewriteResults.normalized_query}</Text>
              </div>
              {rewriteResults.multi_queries.length > 0 && (
                <div style={{ marginBottom: 16 }}>
                  <Text type="secondary">多查询: </Text>
                  <div style={{ marginTop: 8 }}>
                    {rewriteResults.multi_queries.map((q, i) => (
                      <Tag key={i} style={{ marginBottom: 4 }}>{q}</Tag>
                    ))}
                  </div>
                </div>
              )}
              {rewriteResults.sub_queries.length > 0 && (
                <div>
                  <Text type="secondary">子查询: </Text>
                  <div style={{ marginTop: 8 }}>
                    {rewriteResults.sub_queries.map((q, i) => (
                      <Tag key={i} color="green" style={{ marginBottom: 4 }}>{q}</Tag>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          )}

          {/* 检索结果 */}
          {results && (
            <Card
              title={`检索结果 (${results.total} 条)`}
              style={{ marginTop: 16 }}
              extra={<Text type="secondary">耗时: {results.retrieval_time_ms}ms</Text>}
            >
              <Table
                columns={columns}
                dataSource={results.results}
                rowKey={(_, index) => (index ?? 0).toString()}
                pagination={false}
                size="small"
              />
            </Card>
          )}

          {loading && (
            <Card style={{ marginTop: 16, textAlign: 'center' }}>
              <Spin tip="正在检索..." />
            </Card>
          )}
        </Col>

        {/* 右侧统计区域 */}
        <Col xs={24} lg={8}>
          <Card title="检索统计">
            <Statistic
              title="向量总数"
              value={stats?.total_vectors || 0}
              style={{ marginBottom: 16 }}
            />
            <Statistic
              title="关键词总数"
              value={stats?.total_keywords || 0}
              style={{ marginBottom: 16 }}
            />
            <Divider style={{ margin: '16px 0' }} />
            <Statistic
              title="向量检索耗时"
              value={stats?.avg_vector_search_time_ms || 0}
              suffix="ms"
              style={{ marginBottom: 16 }}
            />
            <Statistic
              title="关键词检索耗时"
              value={stats?.avg_keyword_search_time_ms || 0}
              suffix="ms"
              style={{ marginBottom: 16 }}
            />
            <Statistic
              title="融合耗时"
              value={stats?.avg_fusion_time_ms || 0}
              suffix="ms"
            />
            <Button
              type="link"
              icon={<ReloadOutlined />}
              onClick={loadStats}
              style={{ padding: 0, marginTop: 8 }}
            >
              刷新统计
            </Button>
          </Card>

          <Card title="融合方法说明" style={{ marginTop: 16 }}>
            <div style={{ fontSize: 12 }}>
              <Paragraph>
                <Text strong>RRF (倒数排名融合)</Text>
                <br />
                最常用的融合方法，通过计算各检索结果的倒数排名来融合得分。
              </Paragraph>
              <Paragraph>
                <Text strong>加权融合</Text>
                <br />
                根据预设的权重对向量检索和关键词检索得分进行加权求和。
              </Paragraph>
              <Paragraph>
                <Text strong>排名融合</Text>
                <br />
                仅考虑结果在不同检索方法中的排名，不考虑具体得分。
              </Paragraph>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default RetrievalTest;
