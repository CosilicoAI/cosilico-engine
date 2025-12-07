import type { ProvisionResult } from "../types";

interface ProvisionCardProps {
  id: string;
  provision: ProvisionResult;
  isSelected: boolean;
  onClick: () => void;
}

export function ProvisionCard({
  id,
  provision,
  isSelected,
  onClick,
}: ProvisionCardProps) {
  return (
    <div
      className={`provision-card ${isSelected ? "selected" : ""} ${
        provision.success ? "success" : "failed"
      }`}
      onClick={onClick}
    >
      <div className="provision-header">
        <span className="provision-id">{id}</span>
        <span className={`status ${provision.success ? "success" : "failed"}`}>
          {provision.success ? "✓" : "✗"}
        </span>
      </div>
      <div className="provision-citation">{provision.citation}</div>
      <div className="provision-stats">
        <span className="accuracy">
          {(provision.final_accuracy * 100).toFixed(0)}%
        </span>
        <span className="iterations">{provision.iterations} iter</span>
        <span className="cost">${provision.cost.total_cost_usd.toFixed(3)}</span>
      </div>
      <div className="provision-meta">
        <span className="complexity">Complexity: {provision.complexity}</span>
        <span className="phase">Phase {provision.phase}</span>
      </div>
    </div>
  );
}
