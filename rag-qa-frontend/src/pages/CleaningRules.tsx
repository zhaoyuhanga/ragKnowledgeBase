import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  Switch,
  message,
  Row,
  Col,
  Typography,
  Popconfirm
} from 'antd';
import type { TablePaginationConfig } from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import {
  getCleaningRules,
  createCleaningRule,
  updateCleaningRule,
  deleteCleaningRule
} from '../services/cleaning';
import type { CleaningRule, CreateCleaningRuleRequest } from '../types/api';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const CleaningRules: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [rules, setRules] = useState<CleaningRule[]>([]);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  });
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRule, setEditingRule] = useState<CleaningRule | null>(null);
  const [form] = Form.useForm();

  const loadRules = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getCleaningRules({
        page: pagination.current,
        page_size: pagination.pageSize,
      });
      if (res.code === 0 && res.data) {
        setRules(res.data.items);
        setPagination(prev => ({
          ...prev,
          total: res.data!.total,
        }));
      }
    } catch (error) {
      console.error('Failed to load rules:', error);
      message.error('加载清洗规则失败');
    } finally {
      setLoading(false);
    }
  }, [pagination.current, pagination.pageSize]);

  useEffect(() => {
    loadRules();
  }, [loadRules]);

  const handleTableChange = (paginationConfig: TablePaginationConfig) => {
    setPagination(prev => ({
      ...prev,
      current: paginationConfig.current || 1,
      pageSize: paginationConfig.pageSize || 20,
    }));
  };

  const handleAdd = () => {
    setEditingRule(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (rule: CleaningRule) => {
    setEditingRule(rule);
    form.setFieldsValue({
      rule_name: rule.rule_name,
      rule_type: rule.rule_type,
      scope_type: rule.scope_type,
      priority: rule.priority,
      enabled: rule.enabled,
      description: rule.description,
      patterns: (rule.rule_config as { patterns?: string[] })?.patterns?.join('\n') || '',
      regex_pattern: (rule.rule_config as { regex_pattern?: string })?.regex_pattern || '',
      replacement: (rule.rule_config as { replacement?: string })?.replacement || '',
    });
    setModalVisible(true);
  };

  const handleDelete = async (ruleId: number) => {
    try {
      const res = await deleteCleaningRule(ruleId);
      if (res.code === 0) {
        message.success('删除成功');
        loadRules();
      } else {
        message.error(res.message || '删除失败');
      }
    } catch (error) {
      console.error('Delete failed:', error);
      message.error('删除失败');
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      let ruleConfig: Record<string, unknown> = {};
      if (values.rule_type === 'regex_delete' || values.rule_type === 'regex_replace') {
        ruleConfig.patterns = values.patterns?.split('\n').filter((p: string) => p.trim());
        if (values.regex_pattern) {
          ruleConfig.regex_pattern = values.regex_pattern;
        }
        if (values.replacement !== undefined) {
          ruleConfig.replacement = values.replacement;
        }
      }

      const data: CreateCleaningRuleRequest = {
        rule_name: values.rule_name,
        rule_type: values.rule_type,
        rule_config: ruleConfig,
        scope_type: values.scope_type,
        priority: values.priority,
        enabled: values.enabled,
        description: values.description,
      };

      let res;
      if (editingRule) {
        res = await updateCleaningRule(editingRule.id, data);
      } else {
        res = await createCleaningRule(data);
      }

      if (res.code === 0) {
        message.success(editingRule ? '更新成功' : '创建成功');
        setModalVisible(false);
        loadRules();
      } else {
        message.error(res.message || '操作失败');
      }
    } catch (error) {
      console.error('Submit failed:', error);
    }
  };

  const getRuleTypeTag = (type: string) => {
    const typeMap: Record<string, { color: string; label: string }> = {
      'regex_delete': { color: 'red', label: '正则删除' },
      'regex_replace': { color: 'blue', label: '正则替换' },
      'pattern_delete': { color: 'orange', label: '模式删除' },
      'pattern_replace': { color: 'cyan', label: '模式替换' },
      'desensitize': { color: 'purple', label: '脱敏' },
    };
    const config = typeMap[type] || { color: 'default', label: type };
    return <Tag color={config.color}>{config.label}</Tag>;
  };

  const columns: ColumnsType<CleaningRule> = [
    {
      title: '规则名称',
      dataIndex: 'rule_name',
      key: 'rule_name',
      width: 200,
    },
    {
      title: '规则类型',
      dataIndex: 'rule_type',
      key: 'rule_type',
      width: 120,
      render: (type: string) => getRuleTypeTag(type),
    },
    {
      title: '适用范围',
      dataIndex: 'scope_type',
      key: 'scope_type',
      width: 100,
      render: (scope: string) => scope === 'global' ? '全局' : scope || '-',
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      sorter: (a, b) => a.priority - b.priority,
    },
    {
      title: '启用状态',
      dataIndex: 'enabled',
      key: 'enabled',
      width: 100,
      render: (enabled: boolean) => (
        <Tag color={enabled ? 'success' : 'default'}>
          {enabled ? '已启用' : '已禁用'}
        </Tag>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确认删除此规则?"
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

  return (
    <div className="fade-in">
      <div className="page-header">
        <Title level={2}>清洗规则</Title>
        <Text type="secondary">配置文档清洗规则，包括正则删除、模式替换、脱敏处理等</Text>
      </div>

      <Card bordered={false}>
        <Row justify="space-between" style={{ marginBottom: 16 }}>
          <Col />
          <Col>
            <Space>
              <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
                创建规则
              </Button>
              <Button icon={<ReloadOutlined />} onClick={loadRules}>
                刷新
              </Button>
            </Space>
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={rules}
          rowKey="id"
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
          onChange={handleTableChange}
        />
      </Card>

      <Modal
        title={editingRule ? '编辑清洗规则' : '创建清洗规则'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
        okText="确认"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            rule_type: 'regex_delete',
            scope_type: 'global',
            priority: 10,
            enabled: true,
          }}
        >
          <Form.Item
            name="rule_name"
            label="规则名称"
            rules={[{ required: true, message: '请输入规则名称' }]}
          >
            <Input placeholder="请输入规则名称" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="rule_type"
                label="规则类型"
                rules={[{ required: true, message: '请选择规则类型' }]}
              >
                <Select>
                  <Option value="regex_delete">正则删除</Option>
                  <Option value="regex_replace">正则替换</Option>
                  <Option value="pattern_delete">模式删除</Option>
                  <Option value="pattern_replace">模式替换</Option>
                  <Option value="desensitize">脱敏处理</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="scope_type" label="适用范围">
                <Select>
                  <Option value="global">全局</Option>
                  <Option value="document">单个文档</Option>
                  <Option value="business">业务级</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            noStyle
            shouldUpdate={(prev, curr) => prev.rule_type !== curr.rule_type}
          >
            {({ getFieldValue }) => {
              const ruleType = getFieldValue('rule_type');
              if (ruleType === 'regex_delete' || ruleType === 'regex_replace') {
                return (
                  <>
                    <Form.Item
                      name="patterns"
                      label="匹配模式 (每行一个)"
                      extra="支持正则表达式，每行一个模式"
                    >
                      <TextArea rows={4} placeholder="^第\s*\d+\s*页$" />
                    </Form.Item>
                    {ruleType === 'regex_replace' && (
                      <Form.Item name="replacement" label="替换内容">
                        <Input placeholder="替换为..." />
                      </Form.Item>
                    )}
                  </>
                );
              }
              return null;
            }}
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="priority" label="优先级">
                <InputNumber min={1} max={100} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="enabled" label="启用状态" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="description" label="描述">
            <TextArea rows={2} placeholder="规则描述..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default CleaningRules;
