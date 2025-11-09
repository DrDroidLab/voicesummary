"use client";

import React, { useState, useEffect } from "react";
import { ArrowLeft, Plus, Save, Loader2, CheckCircle, XCircle } from "lucide-react";
import Link from "next/link";
import { PromptConfigCard } from "@/components/llm-config/PromptConfigCard";
import {
  PromptConfig,
  LLMModel,
  LLMProvider,
  LLMModelOption,
} from "@/types/llm-config";

const AVAILABLE_MODELS: LLMModelOption[] = [
  // OpenAI
  {
    value: "gpt-4o",
    label: "GPT-4o",
    provider: "openai",
    description: "Most capable OpenAI model",
  },
  {
    value: "gpt-4-turbo",
    label: "GPT-4 Turbo",
    provider: "openai",
    description: "Faster GPT-4 variant",
  },
  {
    value: "gpt-4",
    label: "GPT-4",
    provider: "openai",
    description: "Standard GPT-4",
  },
  {
    value: "gpt-3.5-turbo",
    label: "GPT-3.5 Turbo",
    provider: "openai",
    description: "Fast and cost-effective",
  },
  // Anthropic
  {
    value: "claude-3-5-sonnet-20241022",
    label: "Claude 3.5 Sonnet",
    provider: "anthropic",
    description: "Latest Claude model",
  },
  {
    value: "claude-3-opus-20240229",
    label: "Claude 3 Opus",
    provider: "anthropic",
    description: "Most capable Claude model",
  },
  {
    value: "claude-3-sonnet-20240229",
    label: "Claude 3 Sonnet",
    provider: "anthropic",
    description: "Balanced performance",
  },
  {
    value: "claude-3-haiku-20240307",
    label: "Claude 3 Haiku",
    provider: "anthropic",
    description: "Fast and efficient",
  },
  // Grok
  {
    value: "grok-beta",
    label: "Grok Beta",
    provider: "grok",
    description: "xAI Grok beta",
  },
  {
    value: "grok-2",
    label: "Grok-2",
    provider: "grok",
    description: "Latest Grok model",
  },
];

const DEFAULT_PROMPTS: Omit<PromptConfig, "id">[] = [
  {
    name: "Call Summarization",
    description: "Summarize call transcripts into concise summaries",
    prompt: "Summarize the following call transcript in 2-3 sentences:\n\n{transcript}",
    model: "gpt-4o",
    provider: "openai",
    taskType: "summarization",
    enabled: true,
    temperature: 0.7,
    maxTokens: 500,
  },
  {
    name: "Sentiment Analysis",
    description: "Analyze the sentiment of call conversations",
    prompt: "Analyze the sentiment of this call transcript. Classify as positive, neutral, or negative:\n\n{transcript}",
    model: "gpt-3.5-turbo",
    provider: "openai",
    taskType: "sentiment",
    enabled: true,
    temperature: 0.3,
    maxTokens: 100,
  },
  {
    name: "Customer Information Extraction",
    description: "Extract customer information from call transcripts",
    prompt: "Extract customer information from this transcript: {transcript}\n\nReturn only a JSON object with: customer_name, customer_email, customer_phone, customer_id, account_number. Set to null if not found.",
    model: "gpt-4o",
    provider: "openai",
    taskType: "extraction",
    enabled: true,
    temperature: 0.2,
    maxTokens: 500,
  },
];

export default function LLMConfigPage() {
  const [prompts, setPrompts] = useState<PromptConfig[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<"success" | "error" | null>(null);
  const [saveMessage, setSaveMessage] = useState("");

  useEffect(() => {
    loadConfiguration();
  }, []);

  const loadConfiguration = async () => {
    setIsLoading(true);
    try {
      // TODO: Replace with actual API call
      // const response = await fetch("/api/llm-config");
      // if (response.ok) {
      //   const data = await response.json();
      //   setPrompts(data.prompts || []);
      // } else {
      //   // Load default prompts if no config exists
      //   setPrompts(createDefaultPrompts());
      // }

      // For now, use default prompts
      const savedConfig = localStorage.getItem("llm-config");
      if (savedConfig) {
        const config = JSON.parse(savedConfig);
        setPrompts(config.prompts || createDefaultPrompts());
      } else {
        setPrompts(createDefaultPrompts());
      }
    } catch (error) {
      console.error("Failed to load configuration:", error);
      setPrompts(createDefaultPrompts());
    } finally {
      setIsLoading(false);
    }
  };

  const createDefaultPrompts = (): PromptConfig[] => {
    return DEFAULT_PROMPTS.map((prompt, index) => ({
      ...prompt,
      id: `prompt-${Date.now()}-${index}`,
    }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    setSaveStatus(null);
    setSaveMessage("");

    try {
      // TODO: Replace with actual API call
      // const response = await fetch("/api/llm-config", {
      //   method: "POST",
      //   headers: {
      //     "Content-Type": "application/json",
      //   },
      //   body: JSON.stringify({ prompts }),
      // });

      // if (!response.ok) {
      //   throw new Error("Failed to save configuration");
      // }

      // For now, save to localStorage
      localStorage.setItem(
        "llm-config",
        JSON.stringify({ prompts, savedAt: new Date().toISOString() })
      );

      setSaveStatus("success");
      setSaveMessage("Configuration saved successfully!");
      setTimeout(() => {
        setSaveStatus(null);
        setSaveMessage("");
      }, 3000);
    } catch (error) {
      console.error("Failed to save configuration:", error);
      setSaveStatus("error");
      setSaveMessage(
        error instanceof Error
          ? error.message
          : "Failed to save configuration"
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleAddPrompt = () => {
    const newPrompt: PromptConfig = {
      id: `prompt-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      name: "New Prompt",
      description: "",
      prompt: "Enter your prompt here...",
      model: "gpt-4o",
      provider: "openai",
      taskType: "custom",
      enabled: true,
      temperature: 0.7,
      maxTokens: 1000,
    };
    setPrompts([...prompts, newPrompt]);
  };

  const handleUpdatePrompt = (updatedPrompt: PromptConfig) => {
    setPrompts(
      prompts.map((p) => (p.id === updatedPrompt.id ? updatedPrompt : p))
    );
  };

  const handleDeletePrompt = (id: string) => {
    if (confirm("Are you sure you want to delete this prompt configuration?")) {
      setPrompts(prompts.filter((p) => p.id !== id));
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-12 text-center">
            <Loader2 className="w-8 h-8 text-primary-600 animate-spin mx-auto mb-4" />
            <p className="text-gray-500">Loading configuration...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-8">
            <Link
              href="/"
              className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 mb-4 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="text-sm font-medium">Back to Calls</span>
            </Link>
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center shadow-lg">
                <svg
                  className="w-6 h-6 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                  />
                </svg>
              </div>
              <div className="flex-1">
                <h1 className="text-3xl font-bold text-gray-900">
                  LLM Configuration Settings
                </h1>
                <p className="text-lg text-gray-600 mt-1">
                  Configure prompts and assign language models for processing tasks
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                Prompt Configurations
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Manage your AI prompts and model assignments. Each prompt can be
                mapped to a specific language model.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleAddPrompt}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-primary-600 hover:text-primary-700 border border-primary-300 hover:border-primary-400 rounded-lg transition-colors"
              >
                <Plus className="w-4 h-4" />
                Add Prompt
              </button>
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="inline-flex items-center gap-2 px-6 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSaving ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    Save Configuration
                  </>
                )}
              </button>
            </div>
          </div>

          {saveStatus && (
            <div
              className={`mb-6 p-4 rounded-lg flex items-center gap-2 ${
                saveStatus === "success"
                  ? "bg-green-50 border border-green-200"
                  : "bg-red-50 border border-red-200"
              }`}
            >
              {saveStatus === "success" ? (
                <CheckCircle className="w-5 h-5 text-green-600" />
              ) : (
                <XCircle className="w-5 h-5 text-red-600" />
              )}
              <p
                className={`text-sm ${
                  saveStatus === "success" ? "text-green-800" : "text-red-800"
                }`}
              >
                {saveMessage}
              </p>
            </div>
          )}

          {prompts.length === 0 ? (
            <div className="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg">
              <p className="text-gray-500 mb-4">No prompt configurations yet</p>
              <button
                onClick={handleAddPrompt}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-primary-600 hover:text-primary-700 border border-primary-300 hover:border-primary-400 rounded-lg transition-colors"
              >
                <Plus className="w-4 h-4" />
                Add Your First Prompt
              </button>
            </div>
          ) : (
            <div className="space-y-6">
              {prompts.map((prompt) => (
                <PromptConfigCard
                  key={prompt.id}
                  config={prompt}
                  onUpdate={handleUpdatePrompt}
                  onDelete={handleDeletePrompt}
                  availableModels={AVAILABLE_MODELS}
                />
              ))}
            </div>
          )}

          <div className="mt-8 pt-6 border-t border-gray-200">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-blue-900 mb-2">
                💡 Tips
              </h3>
              <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
                <li>Use variables like {"{transcript}"} in your prompts that will be replaced at runtime</li>
                <li>Enable/disable prompts to control which ones are used in processing</li>
                <li>Different models have different strengths - choose based on your task requirements</li>
                <li>Lower temperature (0-0.3) for consistent outputs, higher (0.7-1.0) for creative responses</li>
                <li>Save your configuration to persist changes (currently saved to browser localStorage)</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

