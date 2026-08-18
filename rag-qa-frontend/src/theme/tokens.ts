/**
 * 前端设计令牌（单一事实来源）
 *
 * 布局常量与语义色统一在此定义，组件与页面不再散落硬编码数值。
 * 使用时：import { LAYOUT } from '../theme/tokens';
 */

// 布局常量
export const LAYOUT = {
  headerHeight: 56,
  siderWidth: 220,
  siderCollapsedWidth: 80,
  contentPadding: 24,
} as const;

// 圆角
export const RADIUS = {
  sm: 6,
  md: 8,
  lg: 12,
  pill: 999,
} as const;

// 阴影
export const SHADOW = {
  card: '0 1px 2px 0 rgba(0, 0, 0, 0.03)',
  hover: '0 6px 16px 0 rgba(0, 0, 0, 0.08)',
} as const;

// 语义色（浅色主题）
export const COLORS = {
  brand: '#1677ff',
  brandGradient: 'linear-gradient(135deg, #1677ff, #69b1ff)',
  sidebarBg: 'linear-gradient(180deg, #001529 0%, #0b2b4d 100%)',
  contentBg: 'linear-gradient(180deg, #f0f2f5 0%, #eef1f6 100%)',
  textPrimary: '#262626',
  textSecondary: '#595959',
  textTertiary: '#8c8c8c',
} as const;
