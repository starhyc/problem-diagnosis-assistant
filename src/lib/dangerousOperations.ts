export interface DangerousOperation {
  id: string;
  name: string;
  description: string;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  requiresConfirmation: boolean;
  canBeInterrupted: boolean;
  whitelistPatterns?: string[];
}

export interface WhitelistRule {
  id: string;
  pattern: string;
  operationType: string;
  description: string;
  enabled: boolean;
  createdAt: string;
}

export const dangerousOperations: DangerousOperation[] = [
  {
    id: 'delete_file',
    name: '删除文件',
    description: '删除系统文件或配置文件',
    riskLevel: 'high',
    requiresConfirmation: true,
    canBeInterrupted: true,
    whitelistPatterns: [
      '/tmp/*',
      '/var/log/*.log',
      '*.tmp',
    ],
  },
  {
    id: 'modify_config',
    name: '修改配置文件',
    description: '修改系统或应用配置',
    riskLevel: 'medium',
    requiresConfirmation: true,
    canBeInterrupted: true,
    whitelistPatterns: [
      '/etc/app/*',
      'application*.yml',
      'application*.yaml',
      'application*.properties',
    ],
  },
  {
    id: 'restart_service',
    name: '重启服务',
    description: '重启系统服务或应用服务',
    riskLevel: 'medium',
    requiresConfirmation: true,
    canBeInterrupted: false,
    whitelistPatterns: [
      'nginx',
      'apache2',
      'mysql',
      'postgresql',
      'redis',
    ],
  },
  {
    id: 'execute_command',
    name: '执行命令',
    description: '执行系统命令',
    riskLevel: 'critical',
    requiresConfirmation: true,
    canBeInterrupted: true,
    whitelistPatterns: [
      'ls',
      'cat',
      'grep',
      'tail',
      'head',
      'wc',
      'ps',
      'netstat',
      'ss',
    ],
  },
  {
    id: 'modify_database',
    name: '修改数据库',
    description: '执行数据库修改操作（INSERT/UPDATE/DELETE）',
    riskLevel: 'critical',
    requiresConfirmation: true,
    canBeInterrupted: true,
    whitelistPatterns: [],
  },
  {
    id: 'scale_resources',
    name: '调整资源',
    description: '调整计算、存储或网络资源',
    riskLevel: 'medium',
    requiresConfirmation: true,
    canBeInterrupted: true,
    whitelistPatterns: [],
  },
  {
    id: 'network_change',
    name: '网络变更',
    description: '修改网络配置或路由',
    riskLevel: 'high',
    requiresConfirmation: true,
    canBeInterrupted: true,
    whitelistPatterns: [],
  },
  {
    id: 'deploy_code',
    name: '部署代码',
    description: '部署新版本代码',
    riskLevel: 'high',
    requiresConfirmation: true,
    canBeInterrupted: true,
    whitelistPatterns: [],
  },
];

export const defaultWhitelistRules: WhitelistRule[] = [
  {
    id: 'wl-1',
    pattern: '/tmp/*',
    operationType: 'delete_file',
    description: '允许删除临时目录下的文件',
    enabled: true,
    createdAt: new Date().toISOString(),
  },
  {
    id: 'wl-2',
    pattern: '/var/log/*.log',
    operationType: 'delete_file',
    description: '允许删除日志文件',
    enabled: true,
    createdAt: new Date().toISOString(),
  },
  {
    id: 'wl-3',
    pattern: 'ls,cat,grep,tail,head,wc,ps,netstat,ss',
    operationType: 'execute_command',
    description: '允许执行只读命令',
    enabled: true,
    createdAt: new Date().toISOString(),
  },
  {
    id: 'wl-4',
    pattern: 'application*.yml,application*.yaml,application*.properties',
    operationType: 'modify_config',
    description: '允许修改应用配置文件',
    enabled: false,
    createdAt: new Date().toISOString(),
  },
];

export function checkWhitelist(
  operationId: string,
  target: string,
  whitelistRules: WhitelistRule[] = defaultWhitelistRules
): { allowed: boolean; reason?: string } {
  const operation = dangerousOperations.find((op) => op.id === operationId);
  
  if (!operation) {
    return { allowed: false, reason: '未知操作类型' };
  }

  if (!operation.requiresConfirmation) {
    return { allowed: true };
  }

  const applicableRules = whitelistRules.filter(
    (rule) => rule.operationType === operationId && rule.enabled
  );

  for (const rule of applicableRules) {
    const patterns = rule.pattern.split(',');
    for (const pattern of patterns) {
      const trimmedPattern = pattern.trim();
      if (matchesPattern(target, trimmedPattern)) {
        return { allowed: true };
      }
    }
  }

  return {
    allowed: false,
    reason: `操作需要确认，且不在白名单中。风险等级：${operation.riskLevel}`,
  };
}

function matchesPattern(target: string, pattern: string): boolean {
  const regexPattern = pattern
    .replace(/\./g, '\\.')
    .replace(/\*/g, '.*')
    .replace(/\?/g, '.');
  
  const regex = new RegExp(`^${regexPattern}$`, 'i');
  return regex.test(target);
}

export function getRiskLevelColor(level: string): string {
  switch (level) {
    case 'low':
      return 'text-semantic-success border-semantic-success bg-semantic-success/10';
    case 'medium':
      return 'text-semantic-warning border-semantic-warning bg-semantic-warning/10';
    case 'high':
      return 'text-semantic-danger border-semantic-danger bg-semantic-danger/10';
    case 'critical':
      return 'text-semantic-danger border-semantic-danger bg-semantic-danger/20 animate-pulse';
    default:
      return 'text-text-muted border-text-muted bg-bg-elevated/10';
  }
}

export function getRiskLevelLabel(level: string): string {
  switch (level) {
    case 'low':
      return '低风险';
    case 'medium':
      return '中风险';
    case 'high':
      return '高风险';
    case 'critical':
      return '严重风险';
    default:
      return '未知';
  }
}
