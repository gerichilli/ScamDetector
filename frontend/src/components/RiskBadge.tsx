import type { RiskLevel } from "../api/types";

const labels: Record<RiskLevel, string> = {
  low: "Rủi ro thấp",
  medium: "Rủi ro vừa",
  high: "Rủi ro cao",
  critical: "Rất nguy hiểm",
};

export function RiskBadge({ level }: { level: RiskLevel }) {
  return <span className={`risk risk-${level}`}>{labels[level]}</span>;
}
