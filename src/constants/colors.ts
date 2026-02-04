export const semanticColors = {
  primary: '#3b82f6',
  primaryHover: '#2563eb',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  muted: '#64748b',
  main: '#1e293b',
  surface: '#334155',
  elevated: '#475569',
  deep: '#0f172a',
  input: '#1e293b',
  subtle: '#334155',
} as const;

export const statusColors = {
  completed: 'text-semantic-success border-semantic-success',
  active: 'text-primary border-primary',
  pending: 'text-text-muted border-text-muted',
  failed: 'text-semantic-danger border-semantic-danger',
} as const;

export const healthColors = {
  healthy: 'text-semantic-success',
  warning: 'text-semantic-warning',
  error: 'text-semantic-danger',
} as const;

export const riskLevelColors = {
  low: 'bg-semantic-success/10 text-semantic-success',
  medium: 'bg-semantic-warning/10 text-semantic-warning',
  high: 'bg-semantic-danger/10 text-semantic-danger',
  critical: 'bg-semantic-danger text-white',
} as const;

export const nodeTypeColors = {
  symptom: { bg: 'bg-semantic-warning/10', border: 'border-semantic-warning' },
  solution: { bg: 'bg-semantic-success/10', border: 'border-semantic-success' },
  evidence: { bg: 'bg-primary/10', border: 'border-primary' },
  hypothesis: { bg: 'bg-semantic-danger/10', border: 'border-semantic-danger' },
} as const;
