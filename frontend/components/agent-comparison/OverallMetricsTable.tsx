"use client";

import { AgentRanking } from "@/types/agent-comparison";
import { Trophy, TrendingUp, TrendingDown, Minus } from "lucide-react";

interface OverallMetricsTableProps {
  rankings: AgentRanking[];
}

export default function OverallMetricsTable({ rankings }: OverallMetricsTableProps) {
  const getMetricColor = (value: number | null, type: "accuracy" | "latency" | "rate") => {
    if (value === null) return "text-gray-400";

    if (type === "accuracy" || type === "rate") {
      if (value >= 0.7) return "text-green-600 font-semibold";
      if (value >= 0.5) return "text-yellow-600";
      return "text-red-600 font-semibold";
    } else {
      if (value < 2.0) return "text-green-600 font-semibold";
      if (value < 3.0) return "text-yellow-600";
      return "text-red-600 font-semibold";
    }
  };

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

  const getMedalIcon = (rank: number) => {
    if (rank === 1) return <Trophy className="w-5 h-5 text-yellow-500" />;
    if (rank === 2) return <Trophy className="w-5 h-5 text-gray-400" />;
    if (rank === 3) return <Trophy className="w-5 h-5 text-orange-600" />;
    return null;
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Rank
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Agent Name
              </th>
              <th scope="col" className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Accuracy
              </th>
              <th scope="col" className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Humanlike
              </th>
              <th scope="col" className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Outcome
              </th>
              <th scope="col" className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Latency Median
              </th>
              <th scope="col" className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Latency P99
              </th>
              <th scope="col" className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Hangup Rate
              </th>
              <th scope="col" className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Score
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {rankings.map((agent) => (
              <tr
                key={agent.agent_id}
                className={`${agent.rank === 1 ? "bg-yellow-50/50" : "hover:bg-gray-50"} transition-colors`}
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    {getMedalIcon(agent.rank)}
                    <span className="text-lg font-bold text-gray-700">#{agent.rank}</span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm font-medium text-gray-900">{agent.agent_name}</div>
                  <div className="text-xs text-gray-500">{agent.agent_id}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <div className={`text-sm ${getMetricColor(agent.accuracy.mean, "accuracy")}`}>
                    {formatPercentage(agent.accuracy.mean)}
                  </div>
                  <div className="text-xs text-gray-400">
                    ±{formatPercentage(agent.accuracy.std)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <div className="text-sm font-medium text-gray-900">
                    {formatScore(agent.humanlike.mean)}/10
                  </div>
                  <div className="text-xs text-gray-400">
                    ±{formatScore(agent.humanlike.std)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <div className="text-sm font-medium text-gray-900">
                    {formatScore(agent.outcome_orientation.mean)}/10
                  </div>
                  <div className="text-xs text-gray-400">
                    ±{formatScore(agent.outcome_orientation.std)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <div className={`text-sm ${getMetricColor(agent.latency.median_mean, "latency")}`}>
                    {formatLatency(agent.latency.median_mean)}
                  </div>
                  <div className="text-xs text-gray-400">
                    ±{formatLatency(agent.latency.median_std)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <div className={`text-sm ${getMetricColor(agent.latency.p99_mean, "latency")}`}>
                    {formatLatency(agent.latency.p99_mean)}
                  </div>
                  <div className="text-xs text-gray-400">
                    ±{formatLatency(agent.latency.p99_std)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <div className={`text-sm ${getMetricColor(agent.hangup_success_rate, "rate")}`}>
                    {formatPercentage(agent.hangup_success_rate)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <div className="text-sm font-bold text-primary-600">
                    {formatScore(agent.composite_score.mean)}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="px-6 py-3 bg-gray-50 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          Showing {rankings.length} agent{rankings.length !== 1 ? "s" : ""} ranked by composite score
          (weighted average of accuracy, humanlike, outcome, and hangup rate)
        </p>
      </div>
    </div>
  );
}
