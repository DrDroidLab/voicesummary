"use client";

import { CriticalIssue } from "@/types/agent-comparison";
import { AlertTriangle, AlertCircle, Info } from "lucide-react";

interface CriticalIssuesProps {
  issues: CriticalIssue[];
  agentName: string;
}

export default function CriticalIssues({ issues, agentName }: CriticalIssuesProps) {
  if (!issues || issues.length === 0) {
    return null;
  }

  const getSeverityConfig = (severity: "critical" | "high" | "medium") => {
    switch (severity) {
      case "critical":
        return {
          bgColor: "bg-red-50",
          borderColor: "border-red-300",
          iconColor: "text-red-600",
          titleColor: "text-red-900",
          descColor: "text-red-800",
          metricColor: "text-red-700",
          badgeBg: "bg-red-100",
          badgeText: "text-red-800",
          Icon: AlertTriangle
        };
      case "high":
        return {
          bgColor: "bg-orange-50",
          borderColor: "border-orange-300",
          iconColor: "text-orange-600",
          titleColor: "text-orange-900",
          descColor: "text-orange-800",
          metricColor: "text-orange-700",
          badgeBg: "bg-orange-100",
          badgeText: "text-orange-800",
          Icon: AlertCircle
        };
      case "medium":
        return {
          bgColor: "bg-yellow-50",
          borderColor: "border-yellow-300",
          iconColor: "text-yellow-600",
          titleColor: "text-yellow-900",
          descColor: "text-yellow-800",
          metricColor: "text-yellow-700",
          badgeBg: "bg-yellow-100",
          badgeText: "text-yellow-800",
          Icon: Info
        };
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <AlertTriangle className="w-6 h-6 text-red-600" />
        <h2 className="text-2xl font-bold text-gray-900">
          Critical Issues to Fix in {agentName}
        </h2>
      </div>

      <p className="text-sm text-gray-600">
        The following {issues.length} issue{issues.length !== 1 ? "s" : ""} require immediate attention to improve agent performance:
      </p>

      <div className="space-y-4">
        {issues.map((issue, index) => {
          const config = getSeverityConfig(issue.severity);
          const IconComponent = config.Icon;

          return (
            <div
              key={index}
              className={`${config.bgColor} border ${config.borderColor} rounded-lg p-5 shadow-sm`}
            >
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 mt-0.5">
                  <IconComponent className={`w-6 h-6 ${config.iconColor}`} />
                </div>

                <div className="flex-1 min-w-0 space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <h3 className={`text-lg font-semibold ${config.titleColor}`}>
                      {index + 1}. {issue.title}
                    </h3>
                    <span className={`px-3 py-1 ${config.badgeBg} ${config.badgeText} text-xs font-bold rounded-full uppercase whitespace-nowrap`}>
                      {issue.severity}
                    </span>
                  </div>

                  <p className={`text-sm ${config.descColor} leading-relaxed`}>
                    {issue.description}
                  </p>

                  <div className="grid grid-cols-2 gap-4 py-3 px-4 bg-white/60 rounded-md border border-gray-200">
                    <div>
                      <div className="text-xs font-medium text-gray-600 mb-1">Current Value</div>
                      <div className={`text-base font-bold ${config.metricColor}`}>
                        {issue.metric_value}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs font-medium text-gray-600 mb-1">Threshold</div>
                      <div className="text-base font-semibold text-gray-700">
                        {issue.threshold}
                      </div>
                    </div>
                  </div>

                  <div className="bg-white/60 rounded-md p-4 border border-gray-200">
                    <div className="text-xs font-medium text-gray-600 mb-2">Recommended Fix:</div>
                    <p className="text-sm text-gray-800 leading-relaxed">
                      {issue.recommended_fix}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
