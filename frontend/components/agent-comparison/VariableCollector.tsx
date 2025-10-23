"use client";

import React, { useState, useEffect } from "react";
import type { AgentWithVariables } from "@/types/agent-comparison";

interface VariableCollectorProps {
  agents: AgentWithVariables[];
  onVariablesCollected: (variables: Record<string, string>) => void;
  onBack: () => void;
}

export function VariableCollector({ agents, onVariablesCollected, onBack }: VariableCollectorProps) {
  const [variableValues, setVariableValues] = useState<Record<string, string>>({});
  const [allVariables, setAllVariables] = useState<string[]>([]);

  useEffect(() => {
    const uniqueVars = new Set<string>();
    agents.forEach(agent => {
      agent.required_variables.forEach(v => uniqueVars.add(v));
    });
    setAllVariables(Array.from(uniqueVars).sort());

    const initialValues: Record<string, string> = {};
    uniqueVars.forEach(v => {
      initialValues[v] = "";
    });
    setVariableValues(initialValues);
  }, [agents]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onVariablesCollected(variableValues);
  };

  const isFormValid = () => {
    return allVariables.every(v => variableValues[v]?.trim().length > 0);
  };

  const getAgentsUsingVariable = (variable: string) => {
    return agents.filter(agent => agent.required_variables.includes(variable));
  };

  return (
    <div className="border rounded-lg p-6 bg-white">
      <h3 className="text-lg font-semibold mb-4">Fill Required Variables</h3>

      {allVariables.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <p>No variables detected in agent configurations.</p>
          <p className="text-sm mt-2">You can proceed to the next step.</p>
          <button
            onClick={() => onVariablesCollected({})}
            className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
          >
            Continue
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <p className="text-sm text-gray-600 mb-4">
            The following variables were detected in your agent configurations. Please provide values for each:
          </p>

          {allVariables.map(variable => {
            const usingAgents = getAgentsUsingVariable(variable);
            return (
              <div key={variable} className="border-l-4 border-blue-500 pl-4">
                <label className="block text-sm font-medium mb-1">
                  {variable}
                </label>
                <p className="text-xs text-gray-500 mb-2">
                  Used by: {usingAgents.map(a => a.agent_name).join(", ")}
                </p>
                <input
                  type="text"
                  value={variableValues[variable] || ""}
                  onChange={(e) =>
                    setVariableValues({ ...variableValues, [variable]: e.target.value })
                  }
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder={`Enter value for ${variable}`}
                  required
                />
              </div>
            );
          })}

          <div className="flex gap-2 justify-end pt-4">
            <button
              type="button"
              onClick={onBack}
              className="px-4 py-2 border rounded-md hover:bg-gray-50"
            >
              Back
            </button>
            <button
              type="submit"
              disabled={!isFormValid()}
              className={`px-4 py-2 rounded-md ${
                isFormValid()
                  ? "bg-blue-600 text-white hover:bg-blue-700"
                  : "bg-gray-300 text-gray-500 cursor-not-allowed"
              }`}
            >
              Continue with Variables
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
