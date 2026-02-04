export const statusLabels = {
  resolved: '已解决',
  investigating: '分析中',
  pending: '待处理',
} as const;

export const statusBadges = {
  validated: { color: 'bg-semantic-success/10 text-semantic-success', label: '已验证' },
  investigating: { color: 'bg-primary/10 text-primary', label: '调查中' },
  rejected: { color: 'bg-semantic-danger/10 text-semantic-danger', label: '已排除' },
  recommended: { color: 'bg-semantic-success/10 text-semantic-success', label: '推荐' },
} as const;
