// Types for experiment data

export interface Failure {
  type: string;
  message: string;
  expected: number | string;
  actual: number | string;
  inputs?: Record<string, unknown>;
}

export interface TrajectoryStep {
  iteration: number;
  code: string;
  accuracy: number;
  passed: number;
  total: number;
  mean_absolute_error: number;
  failures: Failure[];
  is_best: boolean;
}

export interface ConversationEntry {
  turn: number;
  role: "assistant" | "tool_call";
  text?: string;
  input_tokens?: number;
  output_tokens?: number;
  tool_name?: string;
  tool_input?: Record<string, unknown>;
  tool_result?: string;
}

export interface Cost {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  input_cost_usd: number;
  output_cost_usd: number;
  total_cost_usd: number;
  model: string;
}

export interface ProvisionResult {
  citation: string;
  complexity: number;
  phase: number;
  n_test_cases: number;
  success: boolean;
  final_accuracy: number;
  iterations: number;
  submitted: boolean;
  cost: Cost;
  final_code: string;
  trajectory?: TrajectoryStep[];
  conversation?: ConversationEntry[];
}

export interface ExperimentSummary {
  total_provisions: number;
  successful: number;
  total_cost_usd: number;
  mean_iterations: number;
}

export interface ExperimentData {
  timestamp: string;
  model: string;
  max_iterations: number;
  target_accuracy: number;
  provisions: Record<string, ProvisionResult>;
  summary: ExperimentSummary;
}
