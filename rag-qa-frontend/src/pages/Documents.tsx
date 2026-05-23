import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Input,
  Upload,
  Tag,
  message,
  Row,
  Col,
  Typography,
  DatePicker,
  Select,
  Popconfirm,
  Descriptions,
  Tabs,
  Spin,
  Modal,
  Alert
} from 'antd';
import type { UploadProps, TablePaginationConfig } from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  EyeOutlined,
  ReloadOutlined,
  UploadOutlined,
  ArrowLeftOutlined,
  WarningOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import dayjs from 'dayjs';
import {
  getDocuments,
  uploadDocument,
  batchUploadDocuments,
  deleteDocument,
  getDocumentDetail,
  getDocumentVersions,
  initializeSystem
} from '../services/documents';
import { triggerParse } from '../services/parse';
import type { DocumentItem, DocumentListParams, DocumentDetail, DocumentVersion } from '../types/api';
import { DocumentStatusMap } from '../types/api';

const { Title } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

const Documents: React.FC = () => {
  const navigate = useNavigate();
  const params = useParams();
  const location = useLocation();

  // 检查是否是详情页模式
  const isDetailMode = location.pathname.includes('/documents/') && params.id;

  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [initializing, setInitializing] = useState(false);
  const [initResult, setInitResult] = useState<any>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [detailLoading, setDetailLoading] = useState(false);
  const [documentDetail, setDocumentDetail] = useState<DocumentDetail | null>(null);
  const [versions, setVersions] = useState<DocumentVersion[]>([]);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  });
  const [searchParams, setSearchParams] = useState<DocumentListParams>({
    page_no: 1,
    page_size: 20,
  });

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getDocuments(searchParams);
      if (res.code === 0 && res.data) {
        setDocuments(res.data.items);
        setPagination(prev => ({
          ...prev,
          total: res.data!.total,
          current: res.data!.page_no,
          pageSize: res.data!.page_size,
        }));
      }
    } catch (error) {
      console.error('Failed to load documents:', error);
      message.error('加载文档列表失败');
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  const loadDocumentDetail = useCallback(async (documentId: number) => {
    setDetailLoading(true);
    try {
      const [detailRes, versionsRes] = await Promise.all([
        getDocumentDetail(documentId),
        getDocumentVersions(documentId)
      ]);

      if (detailRes.code === 0 && detailRes.data) {
        setDocumentDetail(detailRes.data);
      } else {
        message.error(detailRes.message || '加载文档详情失败');
      }

      if (versionsRes.code === 0 && versionsRes.data) {
        setVersions(versionsRes.data.items);
      }
    } catch (error) {
      console.error('Failed to load document detail:', error);
      message.error('加载文档详情失败');
    } finally {
      setDetailLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isDetailMode && params.id) {
      loadDocumentDetail(parseInt(params.id));
    } else {
      loadDocuments();
    }
  }, [isDetailMode, params.id, loadDocuments, loadDocumentDetail]);

  const handleBackToList = () => {
    navigate('/documents');
  };

  const handleTableChange = (paginationConfig: TablePaginationConfig) => {
    setSearchParams(prev => ({
      ...prev,
      page_no: paginationConfig.current || 1,
      page_size: paginationConfig.pageSize || 20,
    }));
  };

  const handleSearch = (value: string) => {
    setSearchParams(prev => ({
      ...prev,
      keyword: value || undefined,
      page_no: 1,
    }));
  };

  const handleStatusFilter = (status: number | undefined) => {
    setSearchParams(prev => ({
      ...prev,
      status,
      page_no: 1,
    }));
  };

  const handleDateRangeChange = (dates: any) => {
    if (dates) {
      setSearchParams(prev => ({
        ...prev,
        start_date: dates[0]?.format('YYYY-MM-DD'),
        end_date: dates[1]?.format('YYYY-MM-DD'),
        page_no: 1,
      }));
    } else {
      setSearchParams(prev => ({
        ...prev,
        start_date: undefined,
        end_date: undefined,
        page_no: 1,
      }));
    }
  };

  const handleUpload = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    setUploading(true);
    try {
      const res = await uploadDocument(formData);
      if (res.code === 0) {
        message.success('文档上传成功');
        loadDocuments();
      } else {
        message.error(res.message || '上传失败');
      }
    } catch (error) {
      console.error('Upload failed:', error);
      message.error('上传失败');
    } finally {
      setUploading(false);
    }
    return false; // 阻止默认上传
  };

  const handleBatchUpload: UploadProps['beforeUpload'] = async (_file, fileList) => {
    if (fileList.length === 0) return false;
    
    const formData = new FormData();
    fileList.forEach(f => formData.append('files', f as File));
    
    setUploading(true);
    try {
      const res = await batchUploadDocuments(formData);
      if (res.code === 0 && res.data) {
        const { success, failed, duplicates } = res.data;
        message.success(`批量上传完成: 成功 ${success}, 失败 ${failed}, 重复 ${duplicates}`);
        loadDocuments();
      } else {
        message.error(res.message || '批量上传失败');
      }
    } catch (error) {
      console.error('Batch upload failed:', error);
      message.error('批量上传失败');
    } finally {
      setUploading(false);
    }
    return false;
  };

  const handleDelete = async (documentId: number) => {
    try {
      const res = await deleteDocument(documentId);
      if (res.code === 0) {
        message.success('删除成功');
        loadDocuments();
      } else {
        message.error(res.message || '删除失败');
      }
    } catch (error) {
      console.error('Delete failed:', error);
      message.error('删除失败');
    }
  };

  const handleParse = async (documentId: number) => {
    try {
      const res = await triggerParse(documentId);
      if (res.code === 0) {
        message.success('解析任务已创建');
        setTimeout(() => loadDocuments(), 1000);
      } else {
        message.error(res.message || '创建解析任务失败');
      }
    } catch (error) {
      console.error('Parse failed:', error);
      message.error('创建解析任务失败');
    }
  };

  const handleInitialize = async () => {
    setInitializing(true);
    try {
      const res = await initializeSystem();
      if (res.code === 0) {
        setInitResult(res.data);
        message.success('系统初始化完成');
        loadDocuments();
      } else {
        message.error(res.message || '初始化失败');
      }
    } catch (error) {
      console.error('Initialize failed:', error);
      message.error('初始化失败');
    } finally {
      setInitializing(false);
    }
  };

  const showInitConfirm = () => {
    Modal.confirm({
      title: '确认初始化系统?',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <Alert
            message="警告: 此操作不可逆!"
            description="初始化将清空以下所有数据:
            • 所有文档和版本
            • 所有Chunks和向量数据
            • 所有问答日志和反馈
            • 所有优化规则
            • Milvus向量数据库
            • 上传文件目录"
            type="error"
            showIcon
            style={{ marginBottom: 16 }}
          />
          <p>确定要继续吗?</p>
        </div>
      ),
      okText: '确认初始化',
      okType: 'danger',
      cancelText: '取消',
      onOk: handleInitialize,
    });
  };

  const getDocTypeIcon = (docType: string) => {
    const colors: Record<string, string> = {
      pdf: '#ff4d4f',
      word: '#1677ff',
      doc: '#1677ff',
      docx: '#1677ff',
      xls: '#52c41a',
      xlsx: '#52c41a',
      ppt: '#fa8c16',
      pptx: '#fa8c16',
      txt: '#595959',
    };
    const color = colors[docType.toLowerCase()] || '#8c8c8c';
    return (
      <div className={`doc-type-icon ${docType.toLowerCase()}`} style={{ color }}>
        {docType.toUpperCase().slice(0, 3)}
      </div>
    );
  };

  const columns: ColumnsType<DocumentItem> = [
    {
      title: '文档名称',
      dataIndex: 'name',
      key: 'name',
      width: 300,
      render: (name: string, record) => (
        <Space>
          {getDocTypeIcon(record.doc_type)}
          <a onClick={() => navigate(`/documents/${record.id}`)}>{name}</a>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: number) => (
        <Tag color={
          status === 2 ? 'success' :
          status === 0 ? 'default' :
          status === 1 ? 'processing' :
          status === 3 ? 'error' : 'default'
        }>
          {DocumentStatusMap[status] || '未知'}
        </Tag>
      ),
    },
    {
      title: '文档类型',
      dataIndex: 'doc_type',
      key: 'doc_type',
      width: 100,
    },
    {
      title: '版本数',
      dataIndex: 'total_versions',
      key: 'total_versions',
      width: 80,
      render: (versions: number) => `v${versions}`,
    },
    {
      title: '页数',
      dataIndex: 'total_pages',
      key: 'total_pages',
      width: 80,
    },
    {
      title: 'Chunks',
      dataIndex: 'total_chunks',
      key: 'total_chunks',
      width: 80,
    },
    {
      title: '创建者',
      dataIndex: 'creator_name',
      key: 'creator_name',
      width: 100,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/documents/${record.id}`)}
          >
            查看
          </Button>
          {record.status === 0 && (
            <Button
              type="link"
              size="small"
              icon={<ReloadOutlined />}
              onClick={() => handleParse(record.id)}
            >
              解析
            </Button>
          )}
          <Popconfirm
            title="确认删除此文档?"
            onConfirm={() => handleDelete(record.id)}
            okText="确认"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 列表视图
  const renderListView = () => (
    <>
      <Card bordered={false}>
        {/* 工具栏 */}
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col flex="none">
            <Space>
              <Upload
                beforeUpload={handleUpload}
                showUploadList={false}
                accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt"
              >
                <Button type="primary" icon={<UploadOutlined />} loading={uploading}>
                  上传文档
                </Button>
              </Upload>
              <Upload
                beforeUpload={handleBatchUpload}
                showUploadList={false}
                multiple
                accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt"
              >
                <Button icon={<PlusOutlined />} loading={uploading}>
                  批量上传
                </Button>
              </Upload>
            </Space>
          </Col>
          <Col flex="auto">
            <Space wrap>
              <Input.Search
                placeholder="搜索文档名称"
                allowClear
                onSearch={handleSearch}
                style={{ width: 200 }}
              />
              <Select
                placeholder="文档状态"
                allowClear
                onChange={handleStatusFilter}
                style={{ width: 120 }}
              >
                <Option value={0}>待解析</Option>
                <Option value={1}>解析中</Option>
                <Option value={2}>已解析</Option>
                <Option value={3}>解析失败</Option>
                <Option value={9}>已删除</Option>
              </Select>
              <RangePicker onChange={handleDateRangeChange} />
              <Button icon={<ReloadOutlined />} onClick={loadDocuments}>
                刷新
              </Button>
              <Button
                danger
                type="primary"
                icon={<WarningOutlined />}
                onClick={showInitConfirm}
                loading={initializing}
              >
                初始化系统
              </Button>
            </Space>
          </Col>
        </Row>

        {/* 文档列表 */}
        <Table
          columns={columns}
          dataSource={documents}
          rowKey="id"
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 1200 }}
        />
      </Card>
    </>
  );

  // 详情页视图
  const renderDetailView = () => {
    if (detailLoading) {
      return (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" tip="加载中..." />
        </div>
      );
    }

    if (!documentDetail) {
      return (
        <Card bordered={false}>
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <p>文档不存在或加载失败</p>
            <Button type="primary" onClick={handleBackToList}>
              返回列表
            </Button>
          </div>
        </Card>
      );
    }

    const versionColumns: ColumnsType<DocumentVersion> = [
      {
        title: '版本',
        dataIndex: 'version',
        key: 'version',
        width: 80,
        render: (v) => `v${v}`,
      },
      {
        title: '文件名',
        dataIndex: 'file_name',
        key: 'file_name',
        width: 200,
      },
      {
        title: '文件大小',
        dataIndex: 'file_size',
        key: 'file_size',
        width: 120,
        render: (size: number) => {
          if (size < 1024) return `${size} B`;
          if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
          return `${(size / (1024 * 1024)).toFixed(1)} MB`;
        },
      },
      {
        title: '页数',
        dataIndex: 'total_pages',
        key: 'total_pages',
        width: 80,
      },
      {
        title: '解析进度',
        dataIndex: 'parse_progress',
        key: 'parse_progress',
        width: 150,
        render: (progress: number) => `${progress || 0}%`,
      },
      {
        title: '上传者',
        dataIndex: 'uploader_name',
        key: 'uploader_name',
        width: 100,
      },
      {
        title: '上传时间',
        dataIndex: 'uploaded_at',
        key: 'uploaded_at',
        width: 180,
        render: (time: string) => time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-',
      },
      {
        title: '解析时间',
        dataIndex: 'parsed_at',
        key: 'parsed_at',
        width: 180,
        render: (time: string) => time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-',
      },
    ];

    return (
      <div className="fade-in">
        <div className="page-header" style={{ marginBottom: 16 }}>
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={handleBackToList}>
              返回列表
            </Button>
            <Title level={2} style={{ margin: 0 }}>{documentDetail.name}</Title>
          </Space>
        </div>

        <Card bordered={false}>
          <Descriptions bordered column={2} title="文档信息">
            <Descriptions.Item label="文档ID">{documentDetail.id}</Descriptions.Item>
            <Descriptions.Item label="文档类型">{documentDetail.doc_type}</Descriptions.Item>
            <Descriptions.Item label="业务ID">{documentDetail.business_id || '-'}</Descriptions.Item>
            <Descriptions.Item label="业务名称">{documentDetail.business_name || '-'}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={
                documentDetail.status === 2 ? 'success' :
                documentDetail.status === 0 ? 'default' :
                documentDetail.status === 1 ? 'processing' :
                documentDetail.status === 3 ? 'error' : 'default'
              }>
                {documentDetail.status_name || '未知'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="当前版本">v{documentDetail.total_versions}</Descriptions.Item>
            <Descriptions.Item label="总页数">{documentDetail.total_pages || 0}</Descriptions.Item>
            <Descriptions.Item label="总Chunks">{documentDetail.total_chunks || 0}</Descriptions.Item>
            <Descriptions.Item label="创建者">{documentDetail.creator_name || '-'}</Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {documentDetail.created_at ? dayjs(documentDetail.created_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
            </Descriptions.Item>
          </Descriptions>
        </Card>

        <Card bordered={false} style={{ marginTop: 16 }}>
          <Tabs
            defaultActiveKey="versions"
            items={[
              {
                key: 'versions',
                label: '版本历史',
                children: (
                  <Table
                    columns={versionColumns}
                    dataSource={versions}
                    rowKey="id"
                    pagination={false}
                  />
                ),
              },
            ]}
          />
        </Card>
      </div>
    );
  };

  // 初始化结果弹窗
  const renderInitResultModal = () => (
    <Modal
      title="初始化结果"
      open={!!initResult}
      onCancel={() => setInitResult(null)}
      footer={
        <Button type="primary" onClick={() => setInitResult(null)}>
          关闭
        </Button>
      }
      width={600}
    >
      {initResult && (
        <div>
          <Alert
            message="系统初始化成功"
            description="以下数据已被清空:"
            type="success"
            showIcon
            style={{ marginBottom: 16 }}
          />
          <Descriptions bordered column={2} size="small">
            <Descriptions.Item label="文档">{initResult.documents_deleted} 条</Descriptions.Item>
            <Descriptions.Item label="版本">{initResult.versions_deleted} 条</Descriptions.Item>
            <Descriptions.Item label="Chunks">{initResult.chunks_deleted} 条</Descriptions.Item>
            <Descriptions.Item label="关键词索引">{initResult.keyword_indexes_deleted} 条</Descriptions.Item>
            <Descriptions.Item label="导入任务">{initResult.tasks_deleted} 条</Descriptions.Item>
            <Descriptions.Item label="问答日志">{initResult.qa_logs_deleted} 条</Descriptions.Item>
            <Descriptions.Item label="反馈分析">{initResult.feedback_analysis_deleted} 条</Descriptions.Item>
            <Descriptions.Item label="优化规则">{initResult.optimization_rules_deleted} 条</Descriptions.Item>
            <Descriptions.Item label="Milvus向量">{String(initResult.milvus_entities_deleted)}</Descriptions.Item>
            <Descriptions.Item label="物理文件">{initResult.files_deleted} 个</Descriptions.Item>
          </Descriptions>
          {initResult.errors && initResult.errors.length > 0 && (
            <Alert
              message="部分操作存在错误"
              description={initResult.errors.join('\n')}
              type="warning"
              showIcon
              style={{ marginTop: 16 }}
            />
          )}
        </div>
      )}
    </Modal>
  );

  // 根据模式返回不同视图
  return (
    <>
      {isDetailMode ? renderDetailView() : renderListView()}
      {renderInitResultModal()}
    </>
  );
};

export default Documents;
