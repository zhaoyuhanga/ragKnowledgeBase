import React from 'react';
import { Table } from 'antd';
import type { TableProps } from 'antd';

/**
 * 统一表格封装
 *
 * 默认值：
 * - 中文空态（"暂无数据"）
 * - 中等尺寸
 * - 横向滚动 x: max-content（避免表格挤压）
 * - 分页：显示总数与每页条数选择（调用方可覆盖）
 */
const AppTable = <T extends object>(props: TableProps<T>): React.ReactElement => {
  const { locale, scroll, pagination, size = 'middle', ...rest } = props;

  const mergedPagination =
    pagination === false || pagination === undefined
      ? pagination
      : {
          showSizeChanger: true,
          showQuickJumper: false,
          showTotal: (total: number) => `共 ${total} 条`,
          ...(typeof pagination === 'object' ? pagination : {}),
        };

  return (
    <Table<T>
      {...rest}
      size={size}
      locale={{
        emptyText: '暂无数据',
        ...(locale || {}),
      }}
      scroll={{ x: 'max-content', ...(scroll || {}) }}
      pagination={mergedPagination as TableProps<T>['pagination']}
    />
  );
};

export default AppTable;
