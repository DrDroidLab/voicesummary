'use client'

import { useState } from 'react'

interface AgentAnalysisProps {
  analysis: any
  callId: string
  onReanalyze?: (agentType: string, context?: string) => void
}

export function AgentAnalysis({ analysis, callId, onReanalyze }: AgentAnalysisProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [showReanalyzeForm, setShowReanalyzeForm] = useState(false)
  const [newAgentType, setNewAgentType] = useState(analysis?.metadata?.agent_type || '')
  const [newContext, setNewContext] = useState('')

  if (!analysis || analysis.error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center space-x-3">
          <div className="h-6 w-6 text-red-400 text-2xl">❌</div>
          <div>
            <h3 className="text-lg font-medium text-red-800">Agent Analysis Failed</h3>
            <p className="text-sm text-red-700 mt-1">
              {analysis?.error || 'Unable to analyze agent performance'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  const {
    goal_achievement,
    script_adherence,
    communication_quality,
    overall_assessment,
    transcript_analysis,
    metadata
  } = analysis

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-100'
    if (score >= 60) return 'text-yellow-600 bg-yellow-100'
    return 'text-red-600 bg-red-100'
  }

  const getScoreIcon = (score: number) => {
    if (score >= 80) return <div className="h-5 w-5 text-green-500 text-xl">✅</div>
    if (score >= 60) return <div className="h-5 w-5 text-yellow-500 text-xl">⚠️</div>
    return <div className="h-5 w-5 text-red-500 text-xl">❌</div>
  }

  const handleReanalyze = async () => {
    if (onReanalyze && newAgentType) {
      await onReanalyze(newAgentType, newContext || undefined)
      setShowReanalyzeForm(false)
      setNewAgentType('')
      setNewContext('')
    }
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <div className="h-6 w-6 text-blue-600 text-2xl">ℹ️</div>
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Agent Performance Analysis</h2>
            <p className="text-sm text-gray-500">
              {metadata?.agent_name} • Analyzed on {new Date(metadata?.analysis_timestamp).toLocaleString()}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${getScoreColor(overall_assessment?.overall_score || 0)}`}>
            Overall Score: {overall_assessment?.overall_score || 0}/100
          </div>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            {isExpanded ? 'Show Less' : 'Show More'}
          </button>
        </div>
      </div>

      {/* Goal Achievement */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-medium text-gray-900">Goal Achievement</h3>
          <div className="flex items-center space-x-2">
            {getScoreIcon(goal_achievement?.score || 0)}
            <span className={`px-2 py-1 rounded text-sm font-medium ${getScoreColor(goal_achievement?.score || 0)}`}>
              {goal_achievement?.score || 0}/100
            </span>
          </div>
        </div>
        
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            {goal_achievement?.achieved ? (
              <div className="h-5 w-5 text-green-500 text-xl">✅</div>
            ) : (
              <div className="h-5 w-5 text-red-500 text-xl">❌</div>
            )}
            <span className={`font-medium ${goal_achievement?.achieved ? 'text-green-700' : 'text-red-700'}`}>
              {goal_achievement?.achieved ? 'Goals Achieved' : 'Goals Not Fully Achieved'}
            </span>
          </div>
          <p className="text-gray-700 text-sm mb-3">{goal_achievement?.reasoning}</p>
          
          {isExpanded && (
            <div className="space-y-2">
              {goal_achievement?.specific_goals_met?.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-green-700 mb-1">Goals Met:</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {goal_achievement.specific_goals_met.map((goal: string, index: number) => (
                      <li key={index} className="flex items-center space-x-2">
                        <div className="h-4 w-4 text-green-500 text-sm">✅</div>
                        <span>{goal}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {goal_achievement?.goals_not_met?.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-red-700 mb-1">Goals Not Met:</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {goal_achievement.goals_not_met.map((goal: string, index: number) => (
                      <li key={index} className="flex items-center space-x-2">
                        <div className="h-4 w-4 text-red-500 text-sm">❌</div>
                        <span>{goal}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Script Adherence */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-medium text-gray-900">Script Adherence</h3>
          <div className="flex items-center space-x-2">
            {getScoreIcon(script_adherence?.score || 0)}
            <span className={`px-2 py-1 rounded text-sm font-medium ${getScoreColor(script_adherence?.score || 0)}`}>
              {script_adherence?.score || 0}/100
            </span>
          </div>
        </div>
        
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            {script_adherence?.followed_script ? (
              <div className="h-5 w-5 text-green-500 text-xl">✅</div>
            ) : (
              <div className="h-5 w-5 text-yellow-500 text-xl">⚠️</div>
            )}
            <span className={`font-medium ${script_adherence?.followed_script ? 'text-green-700' : 'text-yellow-700'}`}>
              {script_adherence?.followed_script ? 'Script Followed' : 'Script Deviations Detected'}
            </span>
          </div>
          <p className="text-gray-700 text-sm mb-3">{script_adherence?.reasoning}</p>
          
          {isExpanded && script_adherence?.deviations?.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-yellow-700 mb-1">Script Deviations:</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                {script_adherence.deviations.map((deviation: string, index: number) => (
                  <li key={index} className="flex items-center space-x-2">
                    <div className="h-4 w-4 text-yellow-500 text-sm">⚠️</div>
                    <span>{deviation}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Communication Quality */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-medium text-gray-900">Communication Quality</h3>
          <div className="flex items-center space-x-2">
            {getScoreIcon(communication_quality?.score || 0)}
            <span className={`px-2 py-1 rounded text-sm font-medium ${getScoreColor(communication_quality?.score || 0)}`}>
              {communication_quality?.score || 0}/100
            </span>
          </div>
        </div>
        
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-gray-700 text-sm mb-3">{communication_quality?.tone_analysis}</p>
          
          {isExpanded && (
            <div className="space-y-3">
              {communication_quality?.strengths?.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-green-700 mb-1">Strengths:</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {communication_quality.strengths.map((strength: string, index: number) => (
                      <li key={index} className="flex items-center space-x-2">
                        <div className="h-4 w-4 text-green-500 text-sm">✅</div>
                        <span>{strength}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {communication_quality?.areas_for_improvement?.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-yellow-700 mb-1">Areas for Improvement:</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {communication_quality.areas_for_improvement.map((area: string, index: number) => (
                      <li key={index} className="flex items-center space-x-2">
                        <div className="h-4 w-4 text-yellow-500 text-sm">⚠️</div>
                        <span>{area}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Overall Assessment */}
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-3">Overall Assessment</h3>
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-gray-700 text-sm mb-3">{overall_assessment?.summary}</p>
          
          {isExpanded && (
            <div className="space-y-3">
              {overall_assessment?.key_achievements?.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-green-700 mb-1">Key Achievements:</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {overall_assessment.key_achievements.map((achievement: string, index: number) => (
                      <li key={index} className="flex items-center space-x-2">
                        <div className="h-4 w-4 text-green-500 text-sm">✅</div>
                        <span>{achievement}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {overall_assessment?.critical_issues?.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-red-700 mb-1">Critical Issues:</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {overall_assessment.critical_issues.map((issue: string, index: number) => (
                      <li key={index} className="flex items-center space-x-2">
                        <div className="h-4 w-4 text-red-500 text-sm">❌</div>
                        <span>{issue}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {overall_assessment?.recommendations?.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-blue-700 mb-1">Recommendations:</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {overall_assessment.recommendations.map((rec: string, index: number) => (
                      <li key={index} className="flex items-center space-x-2">
                        <div className="h-4 w-4 text-blue-500 text-sm">ℹ️</div>
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Re-analyze Section */}
      <div className="border-t border-gray-200 pt-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-medium text-gray-900">Re-analyze with Different Agent Type</h3>
          <button
            onClick={() => setShowReanalyzeForm(!showReanalyzeForm)}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            {showReanalyzeForm ? 'Cancel' : 'Change Agent Type'}
          </button>
        </div>
        
        {showReanalyzeForm && (
          <div className="bg-gray-50 rounded-lg p-4 space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Agent Type
              </label>
              <select
                value={newAgentType}
                onChange={(e) => setNewAgentType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select agent type...</option>
                <option value="customer_support">Customer Support</option>
                <option value="sales_agent">Sales Agent</option>
                <option value="appointment_scheduler">Appointment Scheduler</option>
                <option value="technical_support">Technical Support</option>
                <option value="general_inquiry">General Inquiry</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Additional Context (Optional)
              </label>
              <textarea
                value={newContext}
                onChange={(e) => setNewContext(e.target.value)}
                placeholder="Provide additional context about the call..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
              />
            </div>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowReanalyzeForm(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleReanalyze}
                disabled={!newAgentType}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Re-analyze
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
