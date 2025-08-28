'use client'

import { useState } from 'react'

interface TranscriptViewerProps {
  transcript: any
}

export function TranscriptViewer({ transcript }: TranscriptViewerProps) {
  if (!transcript || !transcript.turns || !Array.isArray(transcript.turns)) {
    return (
      <div className="text-center py-8 text-gray-500">
        <div className="text-4xl mb-2">📝</div>
        <div className="text-lg font-semibold mb-2">No transcript available</div>
        <p className="text-gray-400">Transcript data could not be loaded</p>
      </div>
    )
  }

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp)
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    } catch {
      return timestamp
    }
  }

  const getRoleDisplayName = (role: string) => {
    switch (role) {
      case 'USER':
        return 'USER'
      case 'AGENT_SPEECH':
        return 'AGENT'
      case 'AGENT':
        return 'AGENT'
      default:
        return role
    }
  }

  // Find first and last AGENT entries for call start/end
  const agentEntries = transcript.turns.filter((turn: any) => turn.role === 'AGENT')
  const firstAgentEntry = agentEntries[0]
  const lastAgentEntry = agentEntries[agentEntries.length - 1]

  return (
    <div className="space-y-3">      
      {/* Call Start Info */}
      {firstAgentEntry && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4">
          <div className="flex items-center space-x-2 text-green-800">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-sm font-medium">Call Started</span>
            {/* <span className="text-gray-500">•</span>
            <span className="text-sm text-gray-600">{formatTimestamp(firstAgentEntry.original_timestamp)}</span> */}
          </div>
        </div>
      )}

      {/* Transcript List */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {transcript.turns && transcript.turns.length > 0 && (
          <div className="mt-2 text-xs text-gray-500">
            {transcript.turns.filter((turn: any) => turn.role === 'USER' || turn.role === 'AGENT').map((turn: any, index: number) => (
              <div key={index} className="ml-2">
                <div key={index} className="text-sm leading-relaxed">
                  <span>
                    {turn.start_time !== undefined ? `${turn.start_time.toFixed(2)}s - ${turn.end_time?.toFixed(2)}s` : 'No timestamp'}
                  </span>
                  <span className="text-blue-600 font-medium ml-2">
                    {getRoleDisplayName(turn.role)}:
                  </span>
                  <span className="text-gray-800 ml-2">
                    {turn.content}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Call End Info */}
      {lastAgentEntry && lastAgentEntry !== firstAgentEntry && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mt-4">
          <div className="flex items-center space-x-2 text-red-800">
            <div className="w-2 h-2 bg-red-500 rounded-full"></div>
            <span className="text-sm font-medium">Call Ended</span>
            {/* <span className="text-gray-500">•</span>
            <span className="text-sm text-gray-600">{formatTimestamp(lastAgentEntry.original_timestamp)}</span> */}
          </div>
        </div>
      )}
    </div>
  )
}
