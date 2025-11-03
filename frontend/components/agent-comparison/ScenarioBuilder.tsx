"use client";

import React, { useState, useEffect } from "react";
import { ScenarioConfig } from "@/types/agent-comparison";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface ScenarioBuilderProps {
  value: ScenarioConfig;
  onChange: (scenario: ScenarioConfig) => void;
  onValidationChange: (isValid: boolean) => void;
}

const SUPPORTED_LANGUAGES = [
  "English",
  "Hindi",
  "Spanish",
  "French",
  "German",
  "Portuguese",
  "Italian",
  "Mandarin",
  "Japanese",
  "Korean",
  "Arabic",
  "Russian",
];

const MIN_LENGTH = 10;

export default function ScenarioBuilder({
  value,
  onChange,
  onValidationChange,
}: ScenarioBuilderProps) {
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    validateScenario();
  }, [value]);

  const validateScenario = () => {
    const newErrors: Record<string, string> = {};

    if (!value.agent_overview || value.agent_overview.trim().length < MIN_LENGTH) {
      newErrors.agent_overview = `Agent overview must be at least ${MIN_LENGTH} characters`;
    }

    if (!value.user_persona || value.user_persona.trim().length < MIN_LENGTH) {
      newErrors.user_persona = `User persona must be at least ${MIN_LENGTH} characters`;
    }

    if (!value.situation || value.situation.trim().length < MIN_LENGTH) {
      newErrors.situation = `Situation must be at least ${MIN_LENGTH} characters`;
    }

    if (!value.primary_language) {
      newErrors.primary_language = "Please select a language";
    }

    if (!value.expected_outcome || value.expected_outcome.trim().length < MIN_LENGTH) {
      newErrors.expected_outcome = `Expected outcome must be at least ${MIN_LENGTH} characters`;
    }

    setErrors(newErrors);
    const isValid = Object.keys(newErrors).length === 0 &&
      value.agent_overview?.trim() &&
      value.user_persona?.trim() &&
      value.situation?.trim() &&
      value.primary_language &&
      value.expected_outcome?.trim();

    onValidationChange(!!isValid);
  };

  const handleChange = (field: keyof ScenarioConfig, fieldValue: string) => {
    onChange({
      ...value,
      [field]: fieldValue,
    });
  };

  return (
    <div className="space-y-6">
      <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
        <h3 className="font-medium text-primary-900 mb-2">Scenario-Based Testing</h3>
        <p className="text-sm text-primary-700">
          Instead of pre-written scripts, define a scenario. The system will generate realistic
          user responses in real-time, responding dynamically to each agent.
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Agent Overview
          <span className="text-red-500">*</span>
        </label>
        <textarea
          value={value.agent_overview}
          onChange={(e) => handleChange("agent_overview", e.target.value)}
          placeholder="Describe what the agent does (e.g., 'A customer support agent that helps users with billing inquiries')"
          className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
            errors.agent_overview ? "border-red-500" : "border-gray-300"
          }`}
          rows={3}
        />
        {errors.agent_overview && (
          <p className="mt-1 text-sm text-red-600">{errors.agent_overview}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          User Persona
          <span className="text-red-500">*</span>
        </label>
        <textarea
          value={value.user_persona}
          onChange={(e) => handleChange("user_persona", e.target.value)}
          placeholder="Describe the user (e.g., 'A frustrated customer who received an unexpected charge')"
          className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
            errors.user_persona ? "border-red-500" : "border-gray-300"
          }`}
          rows={3}
        />
        {errors.user_persona && (
          <p className="mt-1 text-sm text-red-600">{errors.user_persona}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Situation
          <span className="text-red-500">*</span>
        </label>
        <textarea
          value={value.situation}
          onChange={(e) => handleChange("situation", e.target.value)}
          placeholder="Describe the specific situation (e.g., 'User wants to understand a $50 charge that appeared on their bill')"
          className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
            errors.situation ? "border-red-500" : "border-gray-300"
          }`}
          rows={3}
        />
        {errors.situation && (
          <p className="mt-1 text-sm text-red-600">{errors.situation}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Primary Language
          <span className="text-red-500">*</span>
        </label>
        <Select value={value.primary_language} onValueChange={(newValue) => handleChange("primary_language", newValue)}>
          <SelectTrigger className={errors.primary_language ? "border-red-500" : ""}>
            <SelectValue placeholder="Select a language" />
          </SelectTrigger>
          <SelectContent>
            {SUPPORTED_LANGUAGES.map((lang) => (
              <SelectItem key={lang} value={lang}>
                {lang}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.primary_language && (
          <p className="mt-1 text-sm text-red-600">{errors.primary_language}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Expected Outcome
          <span className="text-red-500">*</span>
        </label>
        <textarea
          value={value.expected_outcome}
          onChange={(e) => handleChange("expected_outcome", e.target.value)}
          placeholder="Describe what success looks like (e.g., 'User understands the charge and is satisfied with the explanation')"
          className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
            errors.expected_outcome ? "border-red-500" : "border-gray-300"
          }`}
          rows={3}
        />
        {errors.expected_outcome && (
          <p className="mt-1 text-sm text-red-600">{errors.expected_outcome}</p>
        )}
      </div>
    </div>
  );
}
