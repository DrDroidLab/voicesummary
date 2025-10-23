/**
 * TypeScript types for Agent Comparison feature
 */

export interface AgentBadge {
  agent_id: string;
  agent_name: string;
  status: "valid" | "invalid" | "loading";
  supported?: boolean;
}

export interface ScenarioConfig {
  agent_overview: string;
  user_persona: string;
  situation: string;
  primary_language: string;
  expected_outcome: string;
}

export interface TranscriptTurn {
  role: "USER" | "AGENT";
  content: string;
  timestamp_ms: number;
  latency_ms?: number;
}

export interface TurnLatency {
  turn: number;
  latency_ms: number;
}

export interface TurnAccuracy {
  turn: number;
  accuracy: number;
  context_understanding: number;
  response_quality: number;
  reasoning: string;
  issues: string[];
}

export interface LeastAccurateTurn {
  turn: number;
  accuracy: number;
  issue: string;
  problems: string[];
}

export interface AgentComparisonRun {
  run_id: string;
  comparison_id: string;
  agent_id: string;
  agent_name: string | null;
  call_id: string | null;
  status: "pending" | "running" | "completed" | "failed";
  agent_config: Record<string, any> | null;
  simulated_transcript: TranscriptTurn[] | null;
  total_turns: number | null;
  turn_latencies: TurnLatency[] | null;
  turn_accuracy: TurnAccuracy[] | null;
  latency_median: number | null;
  latency_p75: number | null;
  latency_p99: number | null;
  overall_accuracy: number | null;
  humanlike_rating: number | null;
  outcome_orientation: number | null;
  least_accurate_turns: LeastAccurateTurn[] | null;
  created_at: number;
  completed_at: number | null;
}

export interface AgentRanking {
  rank: number;
  agent_id: string;
  agent_name: string;
  total_simulations: number;
  successful_simulations: number;
  failed_simulations: number;
  latency: {
    median_mean: number | null;
    median_std: number | null;
    p75_mean: number | null;
    p75_std: number | null;
    p99_mean: number | null;
    p99_std: number | null;
  };
  accuracy: {
    mean: number | null;
    std: number | null;
    min: number | null;
    max: number | null;
  };
  humanlike: {
    mean: number | null;
    std: number | null;
    min: number | null;
    max: number | null;
  };
  outcome_orientation: {
    mean: number | null;
    std: number | null;
    min: number | null;
    max: number | null;
  };
  composite_score: {
    mean: number | null;
    std: number | null;
  };
  avg_turns: {
    mean: number | null;
    std: number | null;
  };
  hangup_success_rate: number;
}

export interface CriticalIssue {
  severity: "critical" | "high" | "medium";
  title: string;
  description: string;
  metric_value: string;
  threshold: string;
  recommended_fix: string;
}

export interface ComparisonResults {
  total_agents: number;
  simulations_per_agent: number;
  rankings: AgentRanking[];
  critical_issues?: CriticalIssue[];
}

export interface AgentComparison {
  comparison_id: string;
  name: string;
  scenario_config: Record<string, any>;
  agent_ids: string[];
  status: "pending" | "running" | "completed" | "failed";
  error_message?: string | null;
  results: ComparisonResults | null;
  created_at: number;
  updated_at: number;
  completed_at: number | null;
}

export interface AgentComparisonCreate {
  name: string;
  agent_overview: string;
  user_persona: string;
  situation: string;
  primary_language: string;
  expected_outcome: string;
  agent_ids: string[];
}

export interface AgentConfigResponse {
  agent_id: string;
  agent_name: string;
  supported: boolean;
  llm_family: string;
  llm_model: string;
  system_prompt?: string;
  hangup_prompt?: string;
  welcome_message?: string;
}

export interface AgentLookupResponse {
  agent_id: string;
  agent_name: string;
  status: string;
}

export interface ExecuteComparisonResponse {
  comparison_id: string;
  run_ids: string[];
  total_agents: number;
}

export interface VariableDefinition {
  name: string;
  description?: string;
}

export interface ManualAgentCreate {
  agent_name: string;
  welcome_message: string;
  system_prompt: string;
  hangup_prompt: string;
  llm_model?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface AgentWithVariables {
  agent_id: string;
  agent_name: string;
  config: Record<string, any>;
  required_variables: string[];
}

export interface AdvancedSettings {
  max_concurrent_simulations?: number;
  conversation_timeout_seconds?: number;
  max_conversation_turns?: number;
}

export interface AgentComparisonCreateEnhanced {
  name: string;
  agent_overview: string;
  user_persona: string;
  situation: string;
  primary_language: string;
  expected_outcome: string;
  bolna_agent_ids?: string[];
  manual_agents?: ManualAgentCreate[];
  variable_values: Record<string, string>;
  num_simulations?: number;
  max_concurrent_simulations?: number;
  conversation_timeout_seconds?: number;
  max_conversation_turns?: number;
}
