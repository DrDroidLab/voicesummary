"use client";

import React, { useState } from "react";
import type { ManualAgentCreate } from "@/types/agent-comparison";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface ManualAgentBuilderProps {
  onAgentCreated: (agent: ManualAgentCreate) => void;
  onCancel: () => void;
}

export function ManualAgentBuilder({ onAgentCreated, onCancel }: ManualAgentBuilderProps) {
  const [formData, setFormData] = useState<ManualAgentCreate>({
    agent_name: "",
    welcome_message: "",
    system_prompt: "",
    hangup_prompt: "",
    llm_model: "gpt-4o",
    temperature: 0.7,
    max_tokens: 1000,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAgentCreated(formData);
  };

  return (
    <div className="border rounded-lg p-6 bg-white">
      <h3 className="text-lg font-semibold mb-4">Create Manual Agent</h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">
            Agent Name
          </label>
          <input
            type="text"
            value={formData.agent_name}
            onChange={(e) => setFormData({ ...formData, agent_name: e.target.value })}
            className="w-full px-3 py-2 border rounded-md"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            Welcome Message
          </label>
          <textarea
            value={formData.welcome_message}
            onChange={(e) => setFormData({ ...formData, welcome_message: e.target.value })}
            className="w-full px-3 py-2 border rounded-md"
            rows={3}
            placeholder="Hello! How can I help you today?"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            System Prompt
          </label>
          <textarea
            value={formData.system_prompt}
            onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
            className="w-full px-3 py-2 border rounded-md"
            rows={6}
            placeholder="You are a helpful assistant..."
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            Hangup Prompt
          </label>
          <textarea
            value={formData.hangup_prompt}
            onChange={(e) => setFormData({ ...formData, hangup_prompt: e.target.value })}
            className="w-full px-3 py-2 border rounded-md"
            rows={3}
            placeholder="Thank you for calling. Goodbye!"
            required
          />
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              LLM Model
            </label>
            <Select value={formData.llm_model || "gpt-4o"} onValueChange={(newValue) => setFormData({ ...formData, llm_model: newValue })}>
              <SelectTrigger>
                <SelectValue placeholder="Select model" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                <SelectItem value="gpt-4-turbo">GPT-4 Turbo</SelectItem>
                <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Temperature
            </label>
            <input
              type="number"
              value={formData.temperature}
              onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 border rounded-md"
              min="0"
              max="2"
              step="0.1"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Max Tokens
            </label>
            <input
              type="number"
              value={formData.max_tokens}
              onChange={(e) => setFormData({ ...formData, max_tokens: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border rounded-md"
              min="100"
              max="4000"
              step="100"
            />
          </div>
        </div>

        <div className="flex gap-2 justify-end">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 border rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
          >
            Create Agent
          </button>
        </div>
      </form>
    </div>
  );
}
