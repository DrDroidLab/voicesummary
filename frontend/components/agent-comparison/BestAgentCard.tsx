"use client";

import { AgentRanking } from "@/types/agent-comparison";
import { Trophy, Zap, Brain, Target, Clock, PhoneOff, TrendingUp } from "lucide-react";

interface BestAgentCardProps {
  agent: AgentRanking;
  simulationsPerAgent: number;
}

export default function BestAgentCard({ agent, simulationsPerAgent }: BestAgentCardProps) {
  const formatPercentage = (value: number | null) => {
    if (value === null) return "N/A";
    return `${(value * 100).toFixed(1)}%`;
  };

  const formatLatency = (value: number | null) => {
    if (value === null) return "N/A";
    return `${value.toFixed(2)}s`;
  };

  const formatScore = (value: number | null) => {
    if (value === null) return "N/A";
    return value.toFixed(1);
  };

  const getProgressBarColor = (value: number | null, max: number = 10) => {
    if (value === null) return "bg-gray-300";
    const percentage = (value / max) * 100;
    if (percentage >= 70) return "bg-green-500";
    if (percentage >= 50) return "bg-yellow-500";
    return "bg-red-500";
  };

  const getProgressWidth = (value: number | null, max: number = 10) => {
    if (value === null) return "0%";
    return `${Math.min((value / max) * 100, 100)}%`;
  };

  return (
    <div className="bg-gradient-to-br from-yellow-50 to-amber-50 rounded-lg border-2 border-yellow-400 shadow-lg overflow-hidden">
      <div className="bg-gradient-to-r from-yellow-400 to-amber-500 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center shadow-md">
              <Trophy className="w-10 h-10 text-yellow-500" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-2xl font-bold text-white">{agent.agent_name}</h3>
                <span className="px-3 py-1 bg-white/90 text-yellow-700 text-sm font-bold rounded-full">
                  WINNER
                </span>
              </div>
              <p className="text-sm text-yellow-100 mt-1">{agent.agent_id}</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold text-white">
              {formatScore(agent.composite_score.mean)}
            </div>
            <div className="text-sm text-yellow-100">Composite Score</div>
          </div>
        </div>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <Brain className="w-4 h-4 text-primary-600" />
              <span>Accuracy Score</span>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold text-gray-900">
                  {formatPercentage(agent.accuracy.mean)}
                </span>
                <span className="text-sm text-gray-500">±{formatPercentage(agent.accuracy.std)}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all ${getProgressBarColor(agent.accuracy.mean ? agent.accuracy.mean * 10 : null)}`}
                  style={{ width: getProgressWidth(agent.accuracy.mean ? agent.accuracy.mean * 10 : null) }}
                />
              </div>
              <div className="flex justify-between text-xs text-gray-500">
                <span>Min: {formatPercentage(agent.accuracy.min)}</span>
                <span>Max: {formatPercentage(agent.accuracy.max)}</span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <Target className="w-4 h-4 text-primary-600" />
              <span>Outcome Orientation</span>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold text-gray-900">
                  {formatScore(agent.outcome_orientation.mean)}/10
                </span>
                <span className="text-sm text-gray-500">±{formatScore(agent.outcome_orientation.std)}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all ${getProgressBarColor(agent.outcome_orientation.mean)}`}
                  style={{ width: getProgressWidth(agent.outcome_orientation.mean) }}
                />
              </div>
              <div className="flex justify-between text-xs text-gray-500">
                <span>Min: {formatScore(agent.outcome_orientation.min)}/10</span>
                <span>Max: {formatScore(agent.outcome_orientation.max)}/10</span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <Zap className="w-4 h-4 text-primary-600" />
              <span>Human-like Rating</span>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold text-gray-900">
                  {formatScore(agent.humanlike.mean)}/10
                </span>
                <span className="text-sm text-gray-500">±{formatScore(agent.humanlike.std)}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all ${getProgressBarColor(agent.humanlike.mean)}`}
                  style={{ width: getProgressWidth(agent.humanlike.mean) }}
                />
              </div>
              <div className="flex justify-between text-xs text-gray-500">
                <span>Min: {formatScore(agent.humanlike.min)}/10</span>
                <span>Max: {formatScore(agent.humanlike.max)}/10</span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <Clock className="w-4 h-4 text-primary-600" />
              <span>Response Latency</span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <div className="text-center">
                <div className="text-xs text-gray-500 mb-1">Median</div>
                <div className="text-sm font-semibold text-gray-900">
                  {formatLatency(agent.latency.median_mean)}
                </div>
                <div className="text-xs text-gray-400">±{formatLatency(agent.latency.median_std)}</div>
              </div>
              <div className="text-center">
                <div className="text-xs text-gray-500 mb-1">P75</div>
                <div className="text-sm font-semibold text-gray-900">
                  {formatLatency(agent.latency.p75_mean)}
                </div>
                <div className="text-xs text-gray-400">±{formatLatency(agent.latency.p75_std)}</div>
              </div>
              <div className="text-center">
                <div className="text-xs text-gray-500 mb-1">P99</div>
                <div className="text-sm font-semibold text-gray-900">
                  {formatLatency(agent.latency.p99_mean)}
                </div>
                <div className="text-xs text-gray-400">±{formatLatency(agent.latency.p99_std)}</div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-200">
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-xs text-gray-500 mb-1">
              <PhoneOff className="w-3 h-3" />
              <span>Hangup Rate</span>
            </div>
            <div className="text-xl font-bold text-gray-900">
              {formatPercentage(agent.hangup_success_rate)}
            </div>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-xs text-gray-500 mb-1">
              <TrendingUp className="w-3 h-3" />
              <span>Avg Turns</span>
            </div>
            <div className="text-xl font-bold text-gray-900">
              {formatScore(agent.avg_turns.mean)}
            </div>
            <div className="text-xs text-gray-400">±{formatScore(agent.avg_turns.std)}</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-500 mb-1">Success Rate</div>
            <div className="text-xl font-bold text-green-600">
              {agent.successful_simulations}/{agent.total_simulations}
            </div>
            <div className="text-xs text-gray-400">
              {((agent.successful_simulations / agent.total_simulations) * 100).toFixed(0)}%
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
