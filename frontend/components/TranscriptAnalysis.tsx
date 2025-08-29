'use client'

interface TranscriptAnalysisProps {
  summary: any
}

export function TranscriptAnalysis({ summary }: TranscriptAnalysisProps) {
  if (!summary) {
    return (
      <div className="text-center py-8 text-gray-500">
        <div className="text-4xl mb-2">📋</div>
        <p>No transcript analysis available</p>
      </div>
    )
  }

  const {
    executive_summary,
    call_outcome,
    call_quality,
    areas_of_improvement,
    metadata
  } = summary

  const getQualityColor = (rating: string) => {
    switch (rating?.toLowerCase()) {
      case 'excellent':
        return 'text-green-600 bg-green-100'
      case 'good':
        return 'text-blue-600 bg-blue-100'
      case 'fair':
        return 'text-yellow-600 bg-yellow-100'
      case 'poor':
        return 'text-red-600 bg-red-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const getSatisfactionColor = (satisfaction: string) => {
    switch (satisfaction?.toLowerCase()) {
      case 'high':
        return 'text-green-600'
      case 'medium':
        return 'text-yellow-600'
      case 'low':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  return (
    <div className="space-y-6">
      {/* Call Outcome - Blue Banner */}
      <div className="bg-blue-600 text-white rounded-lg p-4">
        <div className="flex items-center space-x-3 mb-2">
          <div className="text-xl">🎯</div>
          <h3 className="text-lg font-semibold">Call Outcome</h3>
        </div>
        <p className="text-base leading-relaxed">{call_outcome}</p>
      </div>

      {/* Executive Summary */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-2">Executive Summary</h4>
        <p className="text-gray-700 text-sm leading-relaxed">{executive_summary}</p>
      </div>

      {/* Call Quality Assessment - Compact Grid */}
      <div>
        <h4 className="font-medium text-gray-900 mb-3">Call Quality Assessment</h4>
        <div className="grid grid-cols-3 gap-3">
          {/* Resolution Achieved */}
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-lg mb-1">
              {call_quality?.resolution_achieved ? '✅' : '❌'}
            </div>
            <div className="text-xs font-medium text-gray-900">Resolution</div>
            <div className="text-xs text-gray-600">
              {call_quality?.resolution_achieved ? 'Achieved' : 'Not Met'}
            </div>
          </div>

          {/* Customer Satisfaction */}
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-lg mb-1">
              {call_quality?.customer_satisfaction === 'high' ? '😊' : 
               call_quality?.customer_satisfaction === 'medium' ? '😐' : '😞'}
            </div>
            <div className="text-xs font-medium text-gray-900">Satisfaction</div>
            <div className={`text-xs font-medium ${
              getSatisfactionColor(call_quality?.customer_satisfaction)
            }`}>
              {call_quality?.customer_satisfaction || 'Unknown'}
            </div>
          </div>

          {/* Overall Rating */}
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-lg mb-1">
              {call_quality?.overall_rating === 'excellent' ? '⭐' : 
               call_quality?.overall_rating === 'good' ? '👍' : 
               call_quality?.overall_rating === 'fair' ? '⚠️' : '👎'}
            </div>
            <div className="text-xs font-medium text-gray-900">Overall</div>
            <div className={`text-xs font-medium px-2 py-1 rounded-full inline-block ${
              getQualityColor(call_quality?.overall_rating)
            }`}>
              {call_quality?.overall_rating || 'Unknown'}
            </div>
          </div>
        </div>
      </div>

      {/* Areas of Improvement - Red Section */}
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center space-x-2 mb-3">
          <div className="text-lg">🔴</div>
          <h4 className="font-medium text-red-900">Areas of Improvement</h4>
        </div>
        
        {areas_of_improvement && areas_of_improvement.length > 0 ? (
          <ul className="space-y-2">
            {areas_of_improvement.map((area: string, index: number) => (
              <li key={index} className="flex items-start space-x-2">
                <div className="h-1.5 w-1.5 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                <span className="text-red-800 text-sm leading-relaxed">{area}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-red-700 italic text-sm">No specific areas of improvement identified.</p>
        )}
      </div>

      {/* Metadata Footer */}
      {metadata && (
        <div className="text-xs text-gray-500 pt-3 border-t border-gray-200">
          <p>Generated using {metadata.model_used}</p>
          {metadata.summary_timestamp && (
            <p>Summary created: {new Date(metadata.summary_timestamp).toLocaleString()}</p>
          )}
        </div>
      )}
    </div>
  )
}
