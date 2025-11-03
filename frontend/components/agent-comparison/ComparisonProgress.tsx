"use client";

import { useEffect, useState } from "react";
import { Loader2, Phone, Brain, BarChart3, CheckCircle2, X } from "lucide-react";
import { AgentBadge } from "@/types/agent-comparison";

interface ComparisonProgressProps {
  agents: AgentBadge[];
  comparisonId: string;
  onClose?: () => void;
}

interface StatusData {
  status: string;
  current_phase: string;
  total_runs: number;
  completed_runs: number;
  failed_runs: number;
  agents_in_progress: Array<{ agent_id: string; agent_name: string }>;
}

export default function ComparisonProgress({
  agents,
  comparisonId,
  onClose,
}: ComparisonProgressProps) {
  const [statusData, setStatusData] = useState<StatusData | null>(null);

  useEffect(() => {
    if (!comparisonId) return;

    const pollStatus = async () => {
      try {
        const response = await fetch(`/api/comparisons/${comparisonId}/status`);
        if (response.ok) {
          const data: StatusData = await response.json();
          setStatusData(data);
        }
      } catch (err) {
        console.error("Failed to fetch status:", err);
      }
    };

    pollStatus();
    const interval = setInterval(pollStatus, 2000);

    return () => clearInterval(interval);
  }, [comparisonId]);

  const phaseMap: Record<string, number> = {
    "fetching_configs": 0,
    "running_simulations": 1,
    "aggregating": 2,
    "analyzing": 3,
  };

  const currentPhaseIndex = statusData?.current_phase
    ? phaseMap[statusData.current_phase] ?? 0
    : 0;

  const phases = [
    {
      key: "fetching_configs",
      icon: Phone,
      title: "Fetching Agent Configs",
      description: "Loading agent configurations",
    },
    {
      key: "running_simulations",
      icon: Brain,
      title: "Running Simulations",
      description: statusData && statusData.completed_runs > 0
        ? `${statusData.completed_runs}/${statusData.total_runs} completed`
        : "Initializing simulations...",
    },
    {
      key: "aggregating",
      icon: BarChart3,
      title: "Aggregating Results",
      description: "Computing statistics across simulations",
    },
    {
      key: "analyzing",
      icon: CheckCircle2,
      title: "Analyzing Issues",
      description: "Identifying critical issues in best agent",
    },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-2xl w-full mx-4 relative">
        {onClose && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            title="Close and continue in background"
          >
            <X className="w-5 h-5" />
          </button>
        )}
        <div className="text-center space-y-6">
          <div className="relative">
            <div className="w-20 h-20 mx-auto bg-primary-100 rounded-full flex items-center justify-center">
              <Loader2 className="w-10 h-10 text-primary-600 animate-spin" />
            </div>
          </div>

          <div>
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">
              Comparison in Progress
            </h2>
            <p className="text-gray-600">
              Testing {agents.length} agent{agents.length !== 1 ? "s" : ""}...
            </p>
            {onClose && (
              <p className="text-sm text-gray-500 mt-2">
                You can close this and check back later from the history view
              </p>
            )}
          </div>

          <div className="space-y-4 pt-4">
            {phases.map((phase, index) => {
              const Icon = phase.icon;
              const isActive = index === currentPhaseIndex;
              const isPast = index < currentPhaseIndex;

              return (
                <div
                  key={index}
                  className={`flex items-start gap-4 p-4 rounded-lg transition-all ${
                    isActive
                      ? "bg-primary-50 border-2 border-primary-200"
                      : isPast
                      ? "bg-gray-50 border border-gray-200 opacity-60"
                      : "bg-white border border-gray-200 opacity-40"
                  }`}
                >
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                      isActive
                        ? "bg-primary-600 text-white"
                        : isPast
                        ? "bg-green-600 text-white"
                        : "bg-gray-200 text-gray-400"
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                  <div className="flex-1 text-left">
                    <h3
                      className={`font-medium ${
                        isActive ? "text-primary-900" : "text-gray-700"
                      }`}
                    >
                      {phase.title}
                    </h3>
                    <p
                      className={`text-sm ${
                        isActive ? "text-primary-700" : "text-gray-500"
                      }`}
                    >
                      {phase.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="pt-4">
            <div className="flex flex-wrap justify-center gap-2">
              {agents.map((agent) => (
                <div
                  key={agent.agent_id}
                  className="px-3 py-1.5 bg-gray-100 border border-gray-300 rounded-full text-sm text-gray-700"
                >
                  {agent.agent_name}
                </div>
              ))}
            </div>
          </div>

          <p className="text-xs text-gray-500 pt-2">
            This may take several minutes depending on the number of agents and script length
          </p>
        </div>
      </div>
    </div>
  );
}
