"use client";

import { useState, useEffect } from "react";
import { ArrowLeft, Download, Zap, RefreshCw, ChevronRight, Clock, CheckCircle, XCircle } from "lucide-react";
import Link from "next/link";
import AgentInput from "@/components/agent-comparison/AgentInput";
import ScenarioBuilder from "@/components/agent-comparison/ScenarioBuilder";
import ComparisonProgress from "@/components/agent-comparison/ComparisonProgress";
import ComparisonResults from "@/components/agent-comparison/ComparisonResults";
import { ManualAgentBuilder } from "@/components/agent-comparison/ManualAgentBuilder";
import { VariableCollector } from "@/components/agent-comparison/VariableCollector";
import {
  AgentBadge,
  AgentComparison,
  ExecuteComparisonResponse,
  ScenarioConfig,
  ManualAgentCreate,
  AgentWithVariables,
  AgentComparisonCreateEnhanced,
  ComparisonResults as ComparisonResultsType,
} from "@/types/agent-comparison";

type WorkflowStep = "history" | "agent-selection" | "variable-collection" | "scenario-definition" | "execution" | "results";

export default function AgentComparisonPage() {
  const [currentStep, setCurrentStep] = useState<WorkflowStep>("history");
  const [agentSource, setAgentSource] = useState<"bolna" | "manual" | null>(null);

  const [pastComparisons, setPastComparisons] = useState<AgentComparison[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  const [comparisonName, setComparisonName] = useState("");
  const [bolnaAgents, setBolnaAgents] = useState<AgentBadge[]>([]);
  const [manualAgents, setManualAgents] = useState<ManualAgentCreate[]>([]);
  const [showManualBuilder, setShowManualBuilder] = useState(false);

  const [agentsWithVariables, setAgentsWithVariables] = useState<AgentWithVariables[]>([]);
  const [variableValues, setVariableValues] = useState<Record<string, string>>({});

  const [scenarioConfig, setScenarioConfig] = useState<ScenarioConfig>({
    agent_overview: "",
    user_persona: "",
    situation: "",
    primary_language: "",
    expected_outcome: "",
  });
  const [isScenarioValid, setIsScenarioValid] = useState(false);
  const [numSimulations, setNumSimulations] = useState(5);
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);
  const [advancedSettings, setAdvancedSettings] = useState<{
    max_concurrent_simulations?: number;
    conversation_timeout_seconds?: number;
    max_conversation_turns?: number;
  }>({});

  const [isExecuting, setIsExecuting] = useState(false);
  const [currentComparison, setCurrentComparison] = useState<AgentComparison | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchComparisons = async () => {
    setIsLoadingHistory(true);
    try {
      const response = await fetch("/api/comparisons?limit=20");
      if (response.ok) {
        const data = await response.json();
        setPastComparisons(data);
      }
    } catch (err) {
      console.error("Failed to fetch comparisons:", err);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  useEffect(() => {
    if (currentStep === "history") {
      fetchComparisons();
    }
  }, [currentStep]);

  const handleManualAgentCreated = (agent: ManualAgentCreate) => {
    setManualAgents([...manualAgents, agent]);
    setShowManualBuilder(false);
  };

  const handleProceedToVariables = async () => {
    setError(null);

    try {
      const response = await fetch("/api/comparisons/detect-variables", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          bolna_agent_ids: agentSource === "bolna" ? bolnaAgents.map(a => a.agent_id) : undefined,
          manual_agents: agentSource === "manual" ? manualAgents : undefined,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to detect variables");
      }

      const data: AgentWithVariables[] = await response.json();
      setAgentsWithVariables(data);
      setCurrentStep("variable-collection");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to detect variables");
    }
  };

  const handleVariablesCollected = (variables: Record<string, string>) => {
    setVariableValues(variables);
    setCurrentStep("scenario-definition");
  };

  const canProceedFromAgentSelection =
    comparisonName.trim() &&
    ((agentSource === "bolna" && bolnaAgents.length >= 2 && bolnaAgents.every(a => a.status === "valid")) ||
     (agentSource === "manual" && manualAgents.length >= 2));

  const canExecute = isScenarioValid && !isExecuting;

  const handleExecute = async () => {
    if (!canExecute) return;

    setError(null);
    setIsExecuting(true);
    setCurrentStep("execution");

    try {
      const createPayload: AgentComparisonCreateEnhanced = {
        name: comparisonName,
        agent_overview: scenarioConfig.agent_overview,
        user_persona: scenarioConfig.user_persona,
        situation: scenarioConfig.situation,
        primary_language: scenarioConfig.primary_language,
        expected_outcome: scenarioConfig.expected_outcome,
        bolna_agent_ids: agentSource === "bolna" ? bolnaAgents.map(a => a.agent_id) : undefined,
        manual_agents: agentSource === "manual" ? manualAgents : undefined,
        variable_values: variableValues,
        num_simulations: numSimulations,
        max_concurrent_simulations: advancedSettings.max_concurrent_simulations,
        conversation_timeout_seconds: advancedSettings.conversation_timeout_seconds,
        max_conversation_turns: advancedSettings.max_conversation_turns,
      };

      const createResponse = await fetch("/api/comparisons/enhanced", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(createPayload),
      });

      if (!createResponse.ok) {
        const errorData = await createResponse.json();
        throw new Error(errorData.detail || "Failed to create comparison");
      }

      const comparison: AgentComparison = await createResponse.json();
      setCurrentComparison(comparison);

      const executeResponse = await fetch(
        `/api/comparisons/${comparison.comparison_id}/execute`,
        {
          method: "POST",
        }
      );

      if (!executeResponse.ok) {
        throw new Error("Failed to execute comparison");
      }

      await executeResponse.json();

      pollForResults(comparison.comparison_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to execute comparison");
      setIsExecuting(false);
      setCurrentStep("scenario-definition");
    }
  };

  const pollForResults = async (comparisonId: string) => {
    const maxAttempts = 120;
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await fetch(`/api/comparisons/${comparisonId}/status`);
        if (!response.ok) {
          throw new Error("Failed to fetch status");
        }

        const statusData = await response.json();

        if (statusData.status === "completed") {
          const resultsResponse = await fetch(`/api/comparisons/${comparisonId}/results`);
          if (!resultsResponse.ok) {
            throw new Error("Failed to fetch results");
          }

          const resultsData: ComparisonResultsType = await resultsResponse.json();

          // Construct full AgentComparison object with results
          const fullComparison: AgentComparison = {
            comparison_id: comparisonId,
            name: comparisonName,
            scenario_config: scenarioConfig,
            agent_ids: agentSource === "bolna" ? bolnaAgents.map(a => a.agent_id) : manualAgents.map((_, i) => `manual-${i}`),
            status: "completed",
            results: resultsData,
            created_at: Date.now() / 1000,
            updated_at: Date.now() / 1000,
            completed_at: Date.now() / 1000,
          };

          setCurrentComparison(fullComparison);
          setIsExecuting(false);
          setCurrentStep("results");
        } else if (statusData.status === "failed") {
          setError("Comparison failed");
          setIsExecuting(false);
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 2000);
        } else {
          setError("Comparison timed out");
          setIsExecuting(false);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch status");
        setIsExecuting(false);
      }
    };

    poll();
  };

  const handleViewResults = async (comparisonId: string) => {
    try {
      const response = await fetch(`/api/comparisons/${comparisonId}/results`);
      if (!response.ok) {
        throw new Error("Failed to fetch results");
      }

      const resultsData: ComparisonResultsType = await response.json();
      const comparison = pastComparisons.find(c => c.comparison_id === comparisonId);

      if (comparison) {
        setCurrentComparison({
          ...comparison,
          results: resultsData,
        });
        setCurrentStep("results");
      }
    } catch (err) {
      console.error("Failed to load results:", err);
      alert("Failed to load comparison results. Please try again.");
    }
  };

  const handleRerunComparison = async (comparisonId: string) => {
    try {
      setError(null);

      const response = await fetch(`/api/comparisons/${comparisonId}/rerun`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Failed to re-run comparison");
      }

      const data: ExecuteComparisonResponse = await response.json();

      const comparisonResponse = await fetch(`/api/comparisons/${data.comparison_id}`);
      if (comparisonResponse.ok) {
        const newComparison: AgentComparison = await comparisonResponse.json();

        const agentConfigs = newComparison.scenario_config?.agent_configs || [];

        // Set agent states FIRST before showing execution UI
        if (agentConfigs.length > 0 && agentConfigs[0].agent_id) {
          setAgentSource("bolna");
          setBolnaAgents(agentConfigs.map((config: any) => ({
            agent_id: config.agent_id,
            agent_name: config.agent_name,
            status: "valid" as const,
          })));
          setManualAgents([]);
        } else {
          setAgentSource("manual");
          setManualAgents(agentConfigs.map((config: any) => ({
            agent_name: config.agent_name,
            agent_prompt: config.agent_prompt,
            llm_model: config.llm_model,
            llm_family: config.llm_family,
            temperature: config.temperature,
            max_tokens: config.max_tokens,
            top_p: config.top_p,
          })));
          setBolnaAgents([]);
        }

        // Now set execution states - agents are already populated
        setCurrentComparison(newComparison);
        setIsExecuting(true);
        setCurrentStep("execution");
        pollForResults(data.comparison_id);
      } else {
        throw new Error("Failed to fetch new comparison details");
      }
    } catch (err) {
      console.error("Failed to re-run comparison:", err);
      setError(err instanceof Error ? err.message : "Failed to re-run comparison");
      setIsExecuting(false);
    }
  };

  const handleReset = () => {
    setCurrentStep("agent-selection");
    setAgentSource(null);
    setCurrentComparison(null);
    setComparisonName("");
    setBolnaAgents([]);
    setManualAgents([]);
    setAgentsWithVariables([]);
    setVariableValues({});
    setScenarioConfig({
      agent_overview: "",
      user_persona: "",
      situation: "",
      primary_language: "",
      expected_outcome: "",
    });
    setIsScenarioValid(false);
    setNumSimulations(5);
    setError(null);
  };

  const handleDownloadTranscripts = async () => {
    if (!currentComparison) return;

    try {
      const response = await fetch(`/api/comparisons/${currentComparison.comparison_id}/transcripts/download`);
      if (!response.ok) {
        throw new Error("Failed to download transcripts");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `comparison_${currentComparison.comparison_id}_transcripts.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error("Failed to download transcripts:", err);
      alert("Failed to download transcripts. Please try again.");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-8">
            {currentStep === "history" ? (
              <Link
                href="/"
                className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 mb-4 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                <span className="text-sm font-medium">Back to Calls</span>
              </Link>
            ) : currentStep === "results" ? (
              <button
                onClick={() => setCurrentStep("history")}
                className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 mb-4 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                <span className="text-sm font-medium">Back to Comparison History</span>
              </button>
            ) : (
              <Link
                href="/"
                className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 mb-4 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                <span className="text-sm font-medium">Back to Calls</span>
              </Link>
            )}
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center shadow-lg">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Agent Comparison
                </h1>
                <p className="text-lg text-gray-600">
                  Compare multiple voice agents with scenario-based testing
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  This tool simulates conversations using your agent configurations without making actual calls. Tune your agent context to build the perfect agent.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentStep === "history" ? (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Comparison History</h2>
                <p className="text-sm text-gray-600 mt-1">View and manage your past agent comparisons</p>
              </div>
              <button
                onClick={() => setCurrentStep("agent-selection")}
                className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors"
              >
                New Comparison
              </button>
            </div>

            {isLoadingHistory ? (
              <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-12 text-center">
                <p className="text-gray-500">Loading comparisons...</p>
              </div>
            ) : pastComparisons.length === 0 ? (
              <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-12 text-center">
                <p className="text-gray-500 mb-4">No comparisons yet</p>
                <button
                  onClick={() => setCurrentStep("agent-selection")}
                  className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors"
                >
                  Create Your First Comparison
                </button>
              </div>
            ) : (
              <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-x-auto">
                <table className="w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-[35%]">
                        Name
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-[15%]">
                        Status
                      </th>
                      <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-[10%]">
                        Agents
                      </th>
                      <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-[15%]">
                        Created
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider w-[25%]">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {pastComparisons.map((comparison) => (
                      <tr key={comparison.comparison_id} className="hover:bg-gray-50">
                        <td className="px-4 py-4 max-w-xs">
                          <div className="text-sm font-medium text-gray-900 truncate" title={comparison.name}>{comparison.name}</div>
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap">
                          <div className="flex items-center gap-2">
                            {comparison.status === "completed" && (
                              <>
                                <CheckCircle className="w-4 h-4 text-green-500" />
                                <span className="text-sm text-green-700">Completed</span>
                              </>
                            )}
                            {comparison.status === "running" && (
                              <>
                                <Clock className="w-4 h-4 text-blue-500 animate-spin" />
                                <span className="text-sm text-blue-700">Running</span>
                              </>
                            )}
                            {comparison.status === "failed" && (
                              <div className="flex items-center gap-2 group relative">
                                <XCircle className="w-4 h-4 text-red-500" />
                                <span className="text-sm text-red-700">Failed</span>
                                {comparison.error_message && (
                                  <div className="absolute left-0 top-full mt-2 hidden group-hover:block z-10 w-96 bg-red-50 border border-red-200 rounded-lg shadow-lg p-3">
                                    <p className="text-xs text-red-800 font-mono whitespace-pre-wrap break-words">
                                      {comparison.error_message}
                                    </p>
                                  </div>
                                )}
                              </div>
                            )}
                            {comparison.status === "pending" && (
                              <>
                                <Clock className="w-4 h-4 text-gray-500" />
                                <span className="text-sm text-gray-700">Pending</span>
                              </>
                            )}
                          </div>
                        </td>
                        <td className="px-3 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">{comparison.agent_ids.length} agents</div>
                        </td>
                        <td className="px-3 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-500">
                            {new Date(comparison.created_at * 1000).toLocaleDateString()}
                          </div>
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex items-center justify-end gap-2">
                            {comparison.status === "completed" && (
                              <>
                                <button
                                  onClick={() => handleViewResults(comparison.comparison_id)}
                                  className="inline-flex items-center gap-1 text-primary-600 hover:text-primary-700"
                                >
                                  View Results
                                  <ChevronRight className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => handleRerunComparison(comparison.comparison_id)}
                                  className="inline-flex items-center gap-1 text-gray-600 hover:text-gray-700"
                                  title="Re-run this comparison"
                                >
                                  <RefreshCw className="w-4 h-4" />
                                  Re-run
                                </button>
                              </>
                            )}
                            {comparison.status === "failed" && (
                              <button
                                onClick={() => handleRerunComparison(comparison.comparison_id)}
                                className="inline-flex items-center gap-1 text-gray-600 hover:text-gray-700"
                                title="Re-run this failed comparison"
                              >
                                <RefreshCw className="w-4 h-4" />
                                Re-run
                              </button>
                            )}
                            {comparison.status === "pending" && (
                              <button
                                onClick={async () => {
                                  try {
                                    const executeResponse = await fetch(
                                      `/api/comparisons/${comparison.comparison_id}/execute`,
                                      { method: "POST" }
                                    );
                                    if (!executeResponse.ok) {
                                      throw new Error("Failed to execute comparison");
                                    }
                                    // Refresh history to show updated status
                                    fetchComparisons();
                                  } catch (err) {
                                    setError(err instanceof Error ? err.message : "Failed to execute");
                                  }
                                }}
                                className="inline-flex items-center gap-1 text-primary-600 hover:text-primary-700"
                                title="Execute this pending comparison"
                              >
                                <ChevronRight className="w-4 h-4" />
                                Run Now
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ) : currentStep === "results" && currentComparison?.results ? (
          <div className="space-y-6">
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">
                    {currentComparison.name}
                  </h2>
                  <p className="text-sm text-gray-500 mt-1">
                    Completed{" "}
                    {currentComparison.completed_at
                      ? new Date(currentComparison.completed_at * 1000).toLocaleString()
                      : ""}
                  </p>
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={handleDownloadTranscripts}
                    className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-lg transition-colors"
                  >
                    <Download className="w-4 h-4" />
                    Download Transcripts
                  </button>
                  <button
                    onClick={() => handleRerunComparison(currentComparison.comparison_id)}
                    className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-lg transition-colors"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Re-run Comparison
                  </button>
                  <button
                    onClick={handleReset}
                    className="px-4 py-2 text-sm font-medium text-primary-600 hover:text-primary-700 border border-primary-300 hover:border-primary-400 rounded-lg transition-colors"
                  >
                    New Comparison
                  </button>
                </div>
              </div>
            </div>
            <ComparisonResults results={currentComparison.results} />
          </div>
        ) : (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
            <div className="space-y-8">
              {currentStep === "agent-selection" && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Comparison Name
                    </label>
                    <input
                      type="text"
                      value={comparisonName}
                      onChange={(e) => setComparisonName(e.target.value)}
                      placeholder="e.g., Appointment Scheduling Test"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-4">
                      Agent Source
                    </label>
                    <div className="grid grid-cols-2 gap-4 mb-6">
                      <button
                        onClick={() => setAgentSource("bolna")}
                        className={`p-4 border-2 rounded-lg text-left transition-colors ${
                          agentSource === "bolna"
                            ? "border-primary-500 bg-primary-50"
                            : "border-gray-200 hover:border-gray-300"
                        }`}
                      >
                        <h3 className="font-medium">Import from Bolna</h3>
                        <p className="text-sm text-gray-600 mt-1">
                          Use existing Bolna agent IDs
                        </p>
                      </button>
                      <button
                        onClick={() => setAgentSource("manual")}
                        className={`p-4 border-2 rounded-lg text-left transition-colors ${
                          agentSource === "manual"
                            ? "border-primary-500 bg-primary-50"
                            : "border-gray-200 hover:border-gray-300"
                        }`}
                      >
                        <h3 className="font-medium">Create Manually</h3>
                        <p className="text-sm text-gray-600 mt-1">
                          Define agents from scratch
                        </p>
                      </button>
                    </div>
                  </div>

                  {agentSource === "bolna" && (
                    <AgentInput agents={bolnaAgents} onChange={setBolnaAgents} />
                  )}

                  {agentSource === "manual" && (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <h3 className="text-sm font-medium text-gray-700">
                          Manual Agents ({manualAgents.length})
                        </h3>
                        <button
                          onClick={() => setShowManualBuilder(true)}
                          className="px-4 py-2 bg-primary-600 text-white text-sm rounded-md hover:bg-primary-700"
                        >
                          Add Agent
                        </button>
                      </div>

                      {manualAgents.map((agent, index) => (
                        <div key={index} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <h4 className="font-medium">{agent.agent_name}</h4>
                              <p className="text-sm text-gray-500">Model: {agent.llm_model}</p>
                            </div>
                            <button
                              onClick={() => setManualAgents(manualAgents.filter((_, i) => i !== index))}
                              className="text-red-600 hover:text-red-700 text-sm"
                            >
                              Remove
                            </button>
                          </div>
                        </div>
                      ))}

                      {showManualBuilder && (
                        <ManualAgentBuilder
                          onAgentCreated={handleManualAgentCreated}
                          onCancel={() => setShowManualBuilder(false)}
                        />
                      )}
                    </div>
                  )}

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Number of Simulations per Agent
                    </label>
                    <input
                      type="number"
                      value={numSimulations}
                      onChange={(e) => setNumSimulations(parseInt(e.target.value) || 5)}
                      min="1"
                      max="20"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>

                  {error && (
                    <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-sm text-red-800">{error}</p>
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                    <button
                      onClick={() => setCurrentStep("history")}
                      className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-700 border border-gray-300 hover:border-gray-400 rounded-lg transition-colors"
                    >
                      Back to History
                    </button>
                    <button
                      onClick={handleProceedToVariables}
                      disabled={!canProceedFromAgentSelection}
                      className={`px-6 py-3 rounded-lg font-medium transition-all ${
                        canProceedFromAgentSelection
                          ? "bg-primary-600 hover:bg-primary-700 text-white shadow-lg hover:shadow-xl"
                          : "bg-gray-300 text-gray-500 cursor-not-allowed"
                      }`}
                    >
                      Continue to Variables
                    </button>
                  </div>
                </>
              )}

              {currentStep === "variable-collection" && (
                <VariableCollector
                  agents={agentsWithVariables}
                  onVariablesCollected={handleVariablesCollected}
                  onBack={() => setCurrentStep("agent-selection")}
                />
              )}

              {currentStep === "scenario-definition" && (
                <>
                  <ScenarioBuilder
                    value={scenarioConfig}
                    onChange={setScenarioConfig}
                    onValidationChange={setIsScenarioValid}
                  />

                  <div className="mt-6 border border-gray-200 rounded-lg overflow-hidden">
                    <button
                      onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
                      className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 text-left font-medium text-gray-700 flex items-center justify-between transition-colors"
                    >
                      <span>Advanced Settings (Optional)</span>
                      <svg
                        className={`w-5 h-5 transition-transform ${showAdvancedSettings ? 'rotate-180' : ''}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>

                    {showAdvancedSettings && (
                      <div className="p-4 space-y-4 bg-white">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Max Concurrent Simulations
                            <span className="ml-2 text-xs text-gray-500">(default: 3)</span>
                          </label>
                          <input
                            type="number"
                            value={advancedSettings.max_concurrent_simulations ?? ''}
                            onChange={(e) => setAdvancedSettings({
                              ...advancedSettings,
                              max_concurrent_simulations: e.target.value ? parseInt(e.target.value) : undefined
                            })}
                            min="1"
                            max="10"
                            placeholder="3"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          />
                          <p className="mt-1 text-xs text-gray-500">
                            How many simulations to run in parallel (1-10)
                          </p>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Conversation Timeout (seconds)
                            <span className="ml-2 text-xs text-gray-500">(default: 300)</span>
                          </label>
                          <input
                            type="number"
                            value={advancedSettings.conversation_timeout_seconds ?? ''}
                            onChange={(e) => setAdvancedSettings({
                              ...advancedSettings,
                              conversation_timeout_seconds: e.target.value ? parseInt(e.target.value) : undefined
                            })}
                            min="60"
                            max="600"
                            placeholder="300"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          />
                          <p className="mt-1 text-xs text-gray-500">
                            Maximum time allowed per conversation (60-600 seconds)
                          </p>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Max Conversation Turns
                            <span className="ml-2 text-xs text-gray-500">(default: 10)</span>
                          </label>
                          <input
                            type="number"
                            value={advancedSettings.max_conversation_turns ?? ''}
                            onChange={(e) => setAdvancedSettings({
                              ...advancedSettings,
                              max_conversation_turns: e.target.value ? parseInt(e.target.value) : undefined
                            })}
                            min="5"
                            max="20"
                            placeholder="10"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          />
                          <p className="mt-1 text-xs text-gray-500">
                            Maximum turns (user + agent pairs) per conversation (5-20)
                          </p>
                        </div>
                      </div>
                    )}
                  </div>

                  {error && (
                    <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-sm text-red-800">{error}</p>
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                    <button
                      onClick={() => setCurrentStep("variable-collection")}
                      className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-700 border border-gray-300 hover:border-gray-400 rounded-lg transition-colors"
                    >
                      Back
                    </button>
                    <button
                      onClick={handleExecute}
                      disabled={!canExecute}
                      className={`px-6 py-3 rounded-lg font-medium transition-all flex items-center gap-2 ${
                        canExecute
                          ? "bg-primary-600 hover:bg-primary-700 text-white shadow-lg hover:shadow-xl"
                          : "bg-gray-300 text-gray-500 cursor-not-allowed"
                      }`}
                    >
                      <Zap className="w-5 h-5" />
                      Execute & Compare
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>

      {isExecuting && currentStep === "execution" && (
        <ComparisonProgress
          agents={agentSource === "bolna" ? bolnaAgents : manualAgents.map((a, i) => ({
            agent_id: `manual-${i}`,
            agent_name: a.agent_name,
            status: "valid" as const,
          }))}
          comparisonId={currentComparison?.comparison_id || ""}
          onClose={() => setCurrentStep("history")}
        />
      )}
    </div>
  );
}
