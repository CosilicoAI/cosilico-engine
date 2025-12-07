import type { ExperimentData } from "../types";

interface ExperimentSummaryProps {
  experiment: ExperimentData;
}

export function ExperimentSummary({ experiment }: ExperimentSummaryProps) {
  const { summary } = experiment;
  const successRate = (summary.successful / summary.total_provisions) * 100;

  // Group by phase
  const byPhase: Record<number, { success: number; total: number }> = {};
  Object.values(experiment.provisions).forEach((p) => {
    if (!byPhase[p.phase]) {
      byPhase[p.phase] = { success: 0, total: 0 };
    }
    byPhase[p.phase].total++;
    if (p.success) byPhase[p.phase].success++;
  });

  return (
    <div className="experiment-summary">
      <div className="summary-header">
        <h2>Experiment: {experiment.timestamp}</h2>
        <span className="model">{experiment.model}</span>
      </div>

      <div className="summary-stats">
        <div className="stat">
          <div className="stat-value">{summary.successful}/{summary.total_provisions}</div>
          <div className="stat-label">Provisions Passed</div>
        </div>
        <div className="stat">
          <div className="stat-value">{successRate.toFixed(0)}%</div>
          <div className="stat-label">Success Rate</div>
        </div>
        <div className="stat">
          <div className="stat-value">${summary.total_cost_usd.toFixed(2)}</div>
          <div className="stat-label">Total Cost</div>
        </div>
        <div className="stat">
          <div className="stat-value">{summary.mean_iterations.toFixed(1)}</div>
          <div className="stat-label">Mean Iterations</div>
        </div>
      </div>

      <div className="phase-breakdown">
        <h4>By Phase</h4>
        <div className="phases">
          {Object.entries(byPhase)
            .sort(([a], [b]) => Number(a) - Number(b))
            .map(([phase, stats]) => (
              <div key={phase} className="phase-stat">
                <span className="phase-name">Phase {phase}</span>
                <span className="phase-value">
                  {stats.success}/{stats.total} (
                  {((stats.success / stats.total) * 100).toFixed(0)}%)
                </span>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
