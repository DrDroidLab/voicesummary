'use client'

import { UsersIcon, Volume2Icon } from 'lucide-react'

interface TimelineBarsProps {
  transcript: any
}

export function TimelineBars({ transcript }: TimelineBarsProps) {
  if (!transcript || !transcript.turns || !Array.isArray(transcript.turns)) {
    return null
  }

  // Calculate timeline data
  const calculateTimeline = () => {
    const turns = transcript.turns.filter((turn: any) => 
      turn.role === 'USER' || turn.role === 'AGENT'
    )
    
    if (turns.length === 0) return null

    const firstTimestamp = new Date(turns[0].timestamp).getTime()
    const lastTimestamp = new Date(turns[turns.length - 1].timestamp).getTime()
    const totalDuration = lastTimestamp - firstTimestamp

    // Group turns by role and calculate speaking segments with proper duration
    const userSegments: Array<{start: number, end: number}> = []
    const agentSegments: Array<{start: number, end: number}> = []

    turns.forEach((turn: any, index: number) => {
      const currentTimestamp = new Date(turn.timestamp).getTime()
      const nextTimestamp = index < turns.length - 1 
        ? new Date(turns[index + 1].timestamp).getTime() 
        : lastTimestamp
      
      const startPosition = ((currentTimestamp - firstTimestamp) / totalDuration) * 100
      const endPosition = ((nextTimestamp - firstTimestamp) / totalDuration) * 100
      
      if (turn.role === 'USER') {
        userSegments.push({
          start: startPosition,
          end: endPosition
        })
      } else if (turn.role === 'AGENT_SPEECH') {
        agentSegments.push({
          start: startPosition,
          end: endPosition
        })
      }
    })

    // Calculate percentages based on actual speaking duration
    const userDuration = userSegments.reduce((total, segment) => total + (segment.end - segment.start), 0)
    const agentDuration = agentSegments.reduce((total, segment) => total + (segment.end - segment.start), 0)
    const totalSpeakingDuration = userDuration + agentDuration
    
    const userPercentage = totalSpeakingDuration > 0 ? Math.round((userDuration / totalSpeakingDuration) * 100) : 0
    const agentPercentage = totalSpeakingDuration > 0 ? Math.round((agentDuration / totalSpeakingDuration) * 100) : 0

    return {
      totalDuration,
      userSegments,
      agentSegments,
      userPercentage,
      agentPercentage,
      userDuration,
      agentDuration
    }
  }

  const timeline = calculateTimeline()
  if (!timeline) return null

  const formatDuration = (ms: number) => {
    const seconds = Math.round(ms / 1000)
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <UsersIcon className="w-5 h-5 text-gray-600" />
          <span className="text-lg font-semibold text-gray-900">
            Speaking Activity
          </span>
          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
        <div className="text-sm text-gray-500">
          Total duration: {formatDuration(timeline.totalDuration)}
        </div>
      </div>

      <div className="space-y-4">
        {/* USER Timeline */}
        <div className="flex items-center space-x-4">
          <div className="w-24 text-sm font-medium text-gray-700">USER</div>
          <div className="flex-1 relative">
            <div className="h-4 bg-gray-100 rounded-full overflow-hidden">
              {timeline.userSegments.map((segment, index) => (
                <div
                  key={index}
                  className="absolute h-full bg-blue-600 rounded-full"
                  style={{
                    left: `${segment.start}%`,
                    width: `${segment.end - segment.start}%`
                  }}
                />
              ))}
            </div>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <Volume2Icon className="w-4 h-4" />
            <span className="font-medium">{timeline.userPercentage}%</span>
          </div>
        </div>

        {/* AGENT_SPEECH Timeline */}
        <div className="flex items-center space-x-4">
          <div className="w-24 text-sm font-medium text-gray-700">AGENT</div>
          <div className="flex-1 relative">
            <div className="h-4 bg-gray-100 rounded-full overflow-hidden">
              {timeline.agentSegments.map((segment, index) => (
                <div
                  key={index}
                  className="absolute h-full bg-green-600 rounded-full"
                  style={{
                    left: `${segment.start}%`,
                    width: `${segment.end - segment.start}%`
                  }}
                />
              ))}
            </div>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <Volume2Icon className="w-4 h-4" />
            <span className="font-medium">{timeline.agentPercentage}%</span>
          </div>
        </div>
      </div>
    </div>
  )
}
