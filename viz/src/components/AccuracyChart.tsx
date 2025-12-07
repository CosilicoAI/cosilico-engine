import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";
import type { TrajectoryStep } from "../types";

interface AccuracyChartProps {
  trajectory: TrajectoryStep[];
  targetAccuracy: number;
}

export function AccuracyChart({
  trajectory,
  targetAccuracy,
}: AccuracyChartProps) {
  const data = trajectory.map((step) => ({
    iteration: step.iteration,
    accuracy: step.accuracy * 100,
    passed: step.passed,
    total: step.total,
  }));

  return (
    <div className="chart-container">
      <h3>Accuracy Over Iterations</h3>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis
            dataKey="iteration"
            stroke="#888"
            label={{ value: "Iteration", position: "bottom", fill: "#888" }}
          />
          <YAxis
            domain={[0, 100]}
            stroke="#888"
            label={{
              value: "Accuracy %",
              angle: -90,
              position: "insideLeft",
              fill: "#888",
            }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1a1a2e",
              border: "1px solid #444",
              borderRadius: "4px",
            }}
            formatter={(value: number, name: string) => [
              `${value.toFixed(1)}%`,
              name,
            ]}
          />
          <ReferenceLine
            y={targetAccuracy * 100}
            stroke="#4ade80"
            strokeDasharray="5 5"
            label={{
              value: `Target: ${(targetAccuracy * 100).toFixed(0)}%`,
              fill: "#4ade80",
              position: "right",
            }}
          />
          <Line
            type="monotone"
            dataKey="accuracy"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ fill: "#3b82f6", strokeWidth: 2, r: 5 }}
            activeDot={{ r: 8 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
