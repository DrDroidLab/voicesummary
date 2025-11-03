"use client";

import { useState, useCallback } from "react";
import { X, Loader2, CheckCircle, XCircle } from "lucide-react";
import { AgentBadge } from "@/types/agent-comparison";

interface AgentInputProps {
  agents: AgentBadge[];
  onChange: (agents: AgentBadge[]) => void;
}

export default function AgentInput({ agents, onChange }: AgentInputProps) {
  const [inputValue, setInputValue] = useState("");
  const [isValidating, setIsValidating] = useState(false);

  const validateAgentId = useCallback(async (agentId: string): Promise<AgentBadge> => {
    try {
      const response = await fetch(`/api/agents/${agentId}`);
      if (!response.ok) {
        return {
          agent_id: agentId,
          agent_name: "Unknown",
          status: "invalid",
        };
      }
      const data = await response.json();
      return {
        agent_id: agentId,
        agent_name: data.agent_name,
        status: "valid",
      };
    } catch (error) {
      return {
        agent_id: agentId,
        agent_name: "Error",
        status: "invalid",
      };
    }
  }, []);

  const handleInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setInputValue(value);

    if (value.endsWith(",") || value.endsWith(" ")) {
      const agentId = value.slice(0, -1).trim();
      if (agentId && !agents.find((a) => a.agent_id === agentId)) {
        setIsValidating(true);
        const loadingAgent: AgentBadge = {
          agent_id: agentId,
          agent_name: "Loading...",
          status: "loading",
        };
        onChange([...agents, loadingAgent]);
        setInputValue("");

        const validatedAgent = await validateAgentId(agentId);
        onChange([...agents.filter((a) => a.agent_id !== agentId), validatedAgent]);
        setIsValidating(false);
      } else {
        setInputValue("");
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      const agentId = inputValue.trim();
      if (agentId && !agents.find((a) => a.agent_id === agentId)) {
        setIsValidating(true);
        const loadingAgent: AgentBadge = {
          agent_id: agentId,
          agent_name: "Loading...",
          status: "loading",
        };
        onChange([...agents, loadingAgent]);
        setInputValue("");

        validateAgentId(agentId).then((validatedAgent) => {
          onChange([...agents.filter((a) => a.agent_id !== agentId), validatedAgent]);
          setIsValidating(false);
        });
      }
    } else if (e.key === "Backspace" && !inputValue && agents.length > 0) {
      e.preventDefault();
      onChange(agents.slice(0, -1));
    }
  };

  const removeAgent = (agentId: string) => {
    onChange(agents.filter((a) => a.agent_id !== agentId));
  };

  const getStatusIcon = (status: AgentBadge["status"]) => {
    switch (status) {
      case "loading":
        return <Loader2 className="w-3 h-3 animate-spin" />;
      case "valid":
        return <CheckCircle className="w-3 h-3 text-green-600" />;
      case "invalid":
        return <XCircle className="w-3 h-3 text-red-600" />;
    }
  };

  const getBadgeColor = (status: AgentBadge["status"]) => {
    switch (status) {
      case "loading":
        return "bg-gray-100 border-gray-300 text-gray-700";
      case "valid":
        return "bg-green-50 border-green-300 text-green-800";
      case "invalid":
        return "bg-red-50 border-red-300 text-red-800";
    }
  };

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">
        Agent IDs
        <span className="text-gray-500 font-normal ml-2">
          (comma-separated)
        </span>
      </label>
      <div className="min-h-[42px] p-2 border border-gray-300 rounded-lg focus-within:ring-2 focus-within:ring-primary-500 focus-within:border-primary-500 bg-white">
        <div className="flex flex-wrap gap-2">
          {agents.map((agent) => (
            <div
              key={agent.agent_id}
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border ${getBadgeColor(
                agent.status
              )} text-sm`}
            >
              {getStatusIcon(agent.status)}
              <span className="font-medium">{agent.agent_name}</span>
              <button
                type="button"
                onClick={() => removeAgent(agent.agent_id)}
                className="hover:bg-black/10 rounded-full p-0.5 transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
          <input
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder={agents.length === 0 ? "Enter agent IDs separated by commas..." : ""}
            className="flex-1 min-w-[200px] outline-none bg-transparent text-sm"
            disabled={isValidating}
          />
        </div>
      </div>
      <p className="text-xs text-gray-500">
        Enter Bolna agent IDs separated by commas or press Enter
      </p>
    </div>
  );
}
