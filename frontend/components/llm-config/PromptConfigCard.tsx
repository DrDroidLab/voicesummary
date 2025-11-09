"use client";

import React from "react";
import { X, Settings2, Trash2 } from "lucide-react";
import { PromptConfig, LLMModel, LLMProvider, LLMModelOption } from "@/types/llm-config";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  SelectGroup,
  SelectLabel,
} from "@/components/ui/select";

interface PromptConfigCardProps {
  config: PromptConfig;
  onUpdate: (config: PromptConfig) => void;
  onDelete: (id: string) => void;
  availableModels: LLMModelOption[];
}

const TASK_TYPES = [
  { value: "extraction", label: "Data Extraction" },
  { value: "classification", label: "Classification" },
  { value: "labeling", label: "Labeling" },
  { value: "summarization", label: "Summarization" },
  { value: "sentiment", label: "Sentiment Analysis" },
  { value: "custom", label: "Custom" },
] as const;

export function PromptConfigCard({
  config,
  onUpdate,
  onDelete,
  availableModels,
}: PromptConfigCardProps) {
  const handleFieldChange = (field: keyof PromptConfig, value: any) => {
    onUpdate({
      ...config,
      [field]: value,
    });
  };

  const handleModelChange = (model: LLMModel) => {
    const selectedModel = availableModels.find((m) => m.value === model);
    if (selectedModel) {
      onUpdate({
        ...config,
        model,
        provider: selectedModel.provider,
      });
    }
  };

  const modelsByProvider = availableModels.reduce((acc, model) => {
    if (!acc[model.provider]) {
      acc[model.provider] = [];
    }
    acc[model.provider].push(model);
    return acc;
  }, {} as Record<LLMProvider, LLMModelOption[]>);

  return (
    <div className="border border-gray-200 rounded-lg p-6 bg-white hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
            <Settings2 className="w-5 h-5 text-primary-600" />
          </div>
          <div>
            <input
              type="text"
              value={config.name}
              onChange={(e) => handleFieldChange("name", e.target.value)}
              placeholder="Prompt Name"
              className="text-lg font-semibold text-gray-900 bg-transparent border-none focus:outline-none focus:ring-0 p-0"
            />
            <div className="flex items-center gap-2 mt-1">
              <select
                value={config.taskType}
                onChange={(e) => handleFieldChange("taskType", e.target.value)}
                className="text-xs text-gray-500 bg-transparent border-none focus:outline-none focus:ring-0 p-0 cursor-pointer"
              >
                {TASK_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={config.enabled}
              onChange={(e) => handleFieldChange("enabled", e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
          </label>
          <button
            onClick={() => onDelete(config.id)}
            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            title="Delete prompt"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <input
            type="text"
            value={config.description || ""}
            onChange={(e) => handleFieldChange("description", e.target.value)}
            placeholder="Brief description of what this prompt does..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Prompt Text
          </label>
          <textarea
            value={config.prompt}
            onChange={(e) => handleFieldChange("prompt", e.target.value)}
            placeholder="Enter your prompt here. Use {transcript} or other variables as needed..."
            rows={6}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm font-mono"
          />
          <p className="mt-1 text-xs text-gray-500">
            Use variables like {"{transcript}"} that will be replaced at runtime
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Language Model
            </label>
            <Select value={config.model} onValueChange={handleModelChange}>
              <SelectTrigger>
                <SelectValue placeholder="Select model" />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(modelsByProvider).map(([provider, models]) => (
                  <SelectGroup key={provider}>
                    <SelectLabel className="capitalize">{provider}</SelectLabel>
                    {models.map((model) => (
                      <SelectItem key={model.value} value={model.value}>
                        {model.label}
                      </SelectItem>
                    ))}
                  </SelectGroup>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Provider
            </label>
            <div className="px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-sm capitalize">
              {config.provider}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Temperature
              <span className="ml-2 text-xs text-gray-500">
                (0-2, default: 0.7)
              </span>
            </label>
            <input
              type="number"
              value={config.temperature ?? 0.7}
              onChange={(e) =>
                handleFieldChange("temperature", parseFloat(e.target.value))
              }
              min="0"
              max="2"
              step="0.1"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Max Tokens
              <span className="ml-2 text-xs text-gray-500">(optional)</span>
            </label>
            <input
              type="number"
              value={config.maxTokens ?? ""}
              onChange={(e) =>
                handleFieldChange(
                  "maxTokens",
                  e.target.value ? parseInt(e.target.value) : undefined
                )
              }
              min="100"
              max="8000"
              step="100"
              placeholder="1000"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

