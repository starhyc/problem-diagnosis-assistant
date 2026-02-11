export type ConfirmationRiskLevel = 'R0' | 'R1' | 'R2' | 'R3';

export type UiRiskLevel = 'low' | 'medium' | 'high';

const UI_RISK_LABELS: Record<UiRiskLevel, string> = {
  low: '低风险',
  medium: '中风险',
  high: '高风险',
};

export function mapRiskLevelToUiLevel(riskLevel: ConfirmationRiskLevel | undefined): UiRiskLevel {
  if (riskLevel === 'R2') return 'medium';
  if (riskLevel === 'R3') return 'high';
  return 'low';
}

export function formatRiskLevel(riskLevel: ConfirmationRiskLevel | undefined): string {
  const uiLevel = mapRiskLevelToUiLevel(riskLevel);
  const canonical = riskLevel ?? 'R0';
  return `${canonical} / ${UI_RISK_LABELS[uiLevel]}`;
}
