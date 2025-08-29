'use client'

import { AudioPlayer } from './AudioPlayer'
import { TimelineBars } from './TimelineBars'
import { EnhancedTimeline } from './EnhancedTimeline'

interface MediaSectionProps {
  audioUrl: string | null
  processedData: any
  transcript: any
  callId: string
  timestamp: number
}

export function MediaSection({ audioUrl, processedData, transcript, callId, timestamp }: MediaSectionProps) {
  return (
    <div className="space-y-6">
      {/* Audio Player */}
      {audioUrl && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-3">Audio Player</h4>
          <AudioPlayer audioUrl={audioUrl} callId={callId} timestamp={timestamp} />
        </div>
      )}


      {/* Enhanced Timeline */}
      {transcript && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-3">Conversation Timeline</h4>
          <EnhancedTimeline 
            transcript={transcript}
            processedData={processedData}
          />
        </div>
      )}

      {/* No Media Available */}
      {!audioUrl && !processedData?.speech_segments && !processedData?.conversation_timeline && (
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-2">🎵</div>
          <p>No media content available</p>
        </div>
      )}
    </div>
  )
}
