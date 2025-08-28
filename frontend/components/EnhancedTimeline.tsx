'use client'

import { UsersIcon, Volume2Icon, PauseIcon } from 'lucide-react'

interface TimelineEvent {
  type: 'speech' | 'pause'
  start: number
  end: number
  duration: number
  pause_type?: string
}

interface EnhancedTranscript {
  turns: Array<{
    role: string
    content: string
    start_time?: number
    end_time?: number
    duration?: number
    timeline_position?: number
    original_timestamp?: string
    speech_segment_index?: number
    timing_method?: string
  }>
  timeline_events: TimelineEvent[]
  audio_analysis: {
    speech_segments: Array<{
      start: number
      end: number
      duration: number
    }>
    pauses: Array<{
      start_time: number
      end_time: number
      duration: number
      type: string
    }>
    total_duration: number
    speech_percentage: number
  }
  metadata?: {
    enhancement_method?: string
    original_turns_count?: number
    enhanced_turns_count?: number
    timeline_events_count?: number
  }
}

interface EnhancedTimelineProps {
  transcript: EnhancedTranscript | null
  processedData?: any
}

export function EnhancedTimeline({ transcript, processedData }: EnhancedTimelineProps) {
  if (!transcript || !transcript.turns || !Array.isArray(transcript.turns)) {
    return null
  }

  // Calculate timeline data
  const calculateTimeline = () => {
    const turns = transcript.turns.filter((turn: any) => 
      turn.role === 'USER' || turn.role === 'AGENT'
    )
    
    if (turns.length === 0) return null

    // Use audio analysis duration if available, otherwise estimate from transcript
    const totalDuration = transcript.audio_analysis?.total_duration || 
      (turns.length * 2) // Fallback: 2 seconds per turn

    // Get timeline events from enhanced transcript
    const timelineEvents = transcript.timeline_events || []
    
    // Separate events by type
    const userSegments: Array<{start: number, end: number, content: string}> = []
    const agentSegments: Array<{start: number, end: number, content: string}> = []
    const pauseSegments: Array<{start: number, end: number, type: string, duration: number}> = []

    // Process turns with their timestamps
    turns.forEach((turn: any) => {
      if (turn.start_time !== undefined && turn.end_time !== undefined) {
        const segment = {
          start: turn.start_time,
          end: turn.end_time,
          content: turn.content
        }
        
        if (turn.role === 'USER') {
          userSegments.push(segment)
        } else if (turn.role === 'AGENT') {
          agentSegments.push(segment)
        }
      }
    })

    // Process pause events from timeline_events (more accurate)
    timelineEvents.forEach((event: any) => {
      if (event.type === 'pause') {
        pauseSegments.push({
          start: event.start,
          end: event.end,
          type: event.pause_type || 'unknown',
          duration: event.duration
        })
      }
    })

    // Calculate percentages based on actual durations
    const userDuration = userSegments.reduce((total, segment) => total + (segment.end - segment.start), 0)
    const agentDuration = agentSegments.reduce((total, segment) => total + (segment.end - segment.start), 0)
    const pauseDuration = pauseSegments.reduce((total, segment) => total + segment.duration, 0)
    
    const totalSpeakingDuration = userDuration + agentDuration
    
    const userPercentage = totalDuration > 0 ? Math.round((userDuration / totalDuration) * 100) : 0
    const agentPercentage = totalDuration > 0 ? Math.round((agentDuration / totalDuration) * 100) : 0
    const pausePercentage = totalDuration > 0 ? Math.round((pauseDuration / totalDuration) * 100) : 0

    return {
      totalDuration,
      userSegments,
      agentSegments,
      pauseSegments,
      userPercentage,
      agentPercentage,
      pausePercentage,
      userDuration,
      agentDuration,
      pauseDuration
    }
  }

  const timeline = calculateTimeline()
  if (!timeline) return null

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.round(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const formatTimePosition = (seconds: number) => {
    return formatDuration(seconds)
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <UsersIcon className="w-5 h-5 text-gray-600" />
          <span className="text-lg font-semibold text-gray-900">
            Timeline
          </span>
          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
        <div className="text-sm text-gray-500">
          Total duration: {formatDuration(timeline.totalDuration)}
        </div>
      </div>

      <div className="space-y-6">
        {/* USER Timeline */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-20 text-sm font-medium text-gray-700">USER</div>
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <Volume2Icon className="w-4 h-4" />
                <span className="font-medium">{timeline.userPercentage}%</span>
                <span className="text-gray-400">({formatDuration(timeline.userDuration)})</span>
              </div>
            </div>
          </div>
          <div className="flex-1 relative">
            <div className="h-6 bg-gray-100 rounded-full overflow-hidden relative">
              {timeline.userSegments.map((segment, index) => (
                <div
                  key={index}
                  className="absolute h-full bg-blue-600 rounded-full"
                  style={{
                    left: `${(segment.start / timeline.totalDuration) * 100}%`,
                    width: `${((segment.end - segment.start) / timeline.totalDuration) * 100}%`
                  }}
                  title={`${formatTimePosition(segment.start)} - ${formatTimePosition(segment.end)}: ${segment.content.substring(0, 50)}...`}
                />
              ))}
            </div>
          </div>
        </div>

        {/* AGENT Timeline */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-20 text-sm font-medium text-gray-700">AGENT</div>
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <Volume2Icon className="w-4 h-4" />
                <span className="font-medium">{timeline.agentPercentage}%</span>
                <span className="text-gray-400">({formatDuration(timeline.agentDuration)})</span>
              </div>
            </div>
          </div>
          <div className="flex-1 relative">
            <div className="h-6 bg-gray-100 rounded-full overflow-hidden relative">
              {timeline.agentSegments.map((segment, index) => (
                <div
                  key={index}
                  className="absolute h-full bg-green-600 rounded-full"
                  style={{
                    left: `${(segment.start / timeline.totalDuration) * 100}%`,
                    width: `${((segment.end - segment.start) / timeline.totalDuration) * 100}%`
                  }}
                  title={`${formatTimePosition(segment.start)} - ${formatTimePosition(segment.end)}: ${segment.content.substring(0, 50)}...`}
                />
              ))}
            </div>
          </div>
        </div>

        {/* PAUSES Timeline */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-20 text-sm font-medium text-gray-700">PAUSES</div>
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <PauseIcon className="w-4 h-4" />
                <span className="font-medium">{timeline.pausePercentage}%</span>
                <span className="text-gray-400">({formatDuration(timeline.pauseDuration)})</span>
              </div>
            </div>
          </div>
          <div className="flex-1 relative">
            <div className="h-6 bg-gray-100 rounded-full overflow-hidden relative">
              {timeline.pauseSegments.map((segment, index) => (
                <div
                  key={index}
                  className="absolute h-full bg-yellow-500 rounded-full"
                  style={{
                    left: `${(segment.start / timeline.totalDuration) * 100}%`,
                    width: `${(segment.duration / timeline.totalDuration) * 100}%`
                  }}
                  title={`${formatTimePosition(segment.start)} - ${formatTimePosition(segment.start + segment.duration)}: ${segment.type} pause (${formatDuration(segment.duration)})`}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Timeline Scale */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex justify-between text-xs text-gray-500">
            <span>0:00</span>
            <span>{formatDuration(timeline.totalDuration / 4)}</span>
            <span>{formatDuration(timeline.totalDuration / 2)}</span>
            <span>{formatDuration(timeline.totalDuration * 3 / 4)}</span>
            <span>{formatDuration(timeline.totalDuration)}</span>
          </div>
        </div>


      </div>
    </div>
  )
}
