"use client";

import { Brain, Clock } from "lucide-react";
import { ComparisonResults as ComparisonResultsType } from "@/types/agent-comparison";
import OverallMetricsTable from "./OverallMetricsTable";
import BestAgentCard from "./BestAgentCard";
import CriticalIssues from "./CriticalIssues";

interface ComparisonResultsProps {
  results: ComparisonResultsType;
}

export default function ComparisonResults({ results }: ComparisonResultsProps) {
  const bestAgent = results.rankings[0];

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Overall Comparison - All Agents
        </h2>
        <p className="text-sm text-gray-600 mb-6">
          Comparing {results.total_agents} agent{results.total_agents !== 1 ? "s" : ""} with{" "}
          {results.simulations_per_agent} simulation{results.simulations_per_agent !== 1 ? "s" : ""} each
        </p>
        <OverallMetricsTable rankings={results.rankings} />
      </div>

      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Best Performing Agent
        </h2>
        <BestAgentCard agent={bestAgent} simulationsPerAgent={results.simulations_per_agent} />
      </div>

      {results.critical_issues && results.critical_issues.length > 0 && (
        <div>
          <CriticalIssues issues={results.critical_issues} agentName={bestAgent.agent_name} />
        </div>
      )}

      <div className="space-y-4">
        <div className="bg-gradient-to-r from-primary-50 to-primary-100 border border-primary-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center flex-shrink-0">
              <Brain className="w-4 h-4 text-white" />
            </div>
            <div>
              <h3 className="font-medium text-primary-900 mb-1">
                GPT-5 Validation
              </h3>
              <p className="text-sm text-primary-800">
                All responses were validated turn-by-turn using GPT-5 for accuracy,
                context understanding, and human-likeness. Scores range from 0-10.
              </p>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-amber-50 to-amber-100 border border-amber-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-amber-600 rounded-full flex items-center justify-center flex-shrink-0">
              <Clock className="w-4 h-4 text-white" />
            </div>
            <div>
              <h3 className="font-medium text-amber-900 mb-1">
                Latency Metrics
              </h3>
              <p className="text-sm text-amber-800">
                Latencies shown are for LLM generation only. Actual voice call latencies will be higher due to Speech-to-Text, Text-to-Speech, and telephony overhead. LLM generation typically accounts for 40-50% of total latency. Use these metrics for relative agent comparison.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
