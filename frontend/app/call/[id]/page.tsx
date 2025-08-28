'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { AudioPlayer } from '@/components/AudioPlayer'
import { TranscriptViewer } from '@/components/TranscriptViewer'
import { TimelineBars } from '@/components/TimelineBars'
import { EnhancedTimeline } from '@/components/EnhancedTimeline'
import { Call } from '@/types/call'
import { ArrowLeftIcon, ClockIcon, UsersIcon } from 'lucide-react'

export default function CallDetailPage() {
  const params = useParams()
  const router = useRouter()
  const callId = params.id as string
  
  const [call, setCall] = useState<Call | null>(null)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [transcript, setTranscript] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (callId) {
      fetchCallData()
    }
  }, [callId])

  const fetchCallData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      // Get call details, audio URL and transcript
      const [callResponse, audioResponse, transcriptResponse] = await Promise.all([
        fetch(`/api/calls/${callId}`, { 
          headers: { 'Cache-Control': 'no-cache' },
          cache: 'no-store'
        }),
        fetch(`/api/calls/${callId}/audio`, { 
          headers: { 'Cache-Control': 'no-cache' },
          cache: 'no-store'
        }),
        fetch(`/api/calls/${callId}/transcript`, { 
          headers: { 'Cache-Control': 'no-cache' },
          cache: 'no-store'
        })
      ])
      
      console.log('All responses received:', {
        call: { ok: callResponse.ok, status: callResponse.status },
        audio: { ok: audioResponse.ok, status: audioResponse.status, statusText: audioResponse.statusText },
        transcript: { ok: transcriptResponse.ok, status: transcriptResponse.status }
      })
      
      // Debug: Check the actual audio response in detail
      console.log('Audio response details:', {
        url: audioResponse.url,
        status: audioResponse.status,
        statusText: audioResponse.statusText,
        ok: audioResponse.ok,
        type: audioResponse.type,
        headers: Object.fromEntries(audioResponse.headers.entries())
      })
      
      if (callResponse.ok && transcriptResponse.ok) {
        const callData = await callResponse.json()
        const transcriptData = await transcriptResponse.json()
        
        setCall(callData)
        setTranscript(transcriptData.transcript)
        
        // Handle audio response separately since it might fail
        if (audioResponse.ok) {
          console.log('Audio response is OK, processing...')
          await processAudioResponse(audioResponse, callId)
        } else {
          console.log('Audio response failed:', {
            status: audioResponse.status,
            statusText: audioResponse.statusText,
            ok: audioResponse.ok
          })
          const audioError = await audioResponse.json()
          console.warn('Audio not available:', audioError)
          setAudioUrl(null) // No audio available
        }
      } else {
        throw new Error('Failed to fetch call data')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const processAudioResponse = async (audioResponse: Response, callId: string) => {
    try {
      // Get the content type from the audio response headers
      const contentType = audioResponse.headers.get('content-type') || 'audio/mpeg'
      const contentDisposition = audioResponse.headers.get('content-disposition') || ''
      console.log('Audio content type from backend:', contentType)
      console.log('Audio content disposition from backend:', contentDisposition)
      console.log('All audio response headers:', Object.fromEntries(audioResponse.headers.entries()))
      console.log('Audio response status:', audioResponse.status)
      console.log('Audio response ok:', audioResponse.ok)
      
      // Check if the response is actually audio data
      if (!contentType.startsWith('audio/')) {
        console.warn('Response content type is not audio:', contentType)
      }
      
      // Check for common error response patterns in headers
      if (contentDisposition && contentDisposition.includes('error')) {
        console.error('Response indicates error in content-disposition:', contentDisposition)
      }
      
      // Check if the response is actually binary data
      const contentLength = audioResponse.headers.get('content-length')
      if (contentLength) {
        console.log('Expected content length:', contentLength, 'bytes')
      }
      
      // Check if the response is actually binary data by examining the response type
      const responseType = audioResponse.type
      console.log('Response type:', responseType)
      
      // If the response type is 'default', it might be an error response
      if (responseType === 'default') {
        console.warn('Response type is "default" - this might indicate an error response')
      }
      
      // Extract file extension from content-disposition header
      let detectedExtension = 'mp3' // default
      if (contentDisposition.includes('filename=')) {
        const filenameMatch = contentDisposition.match(/filename=([^;]+)/)
        if (filenameMatch && filenameMatch[1]) {
          const filename = filenameMatch[1].replace(/"/g, '')
          if (filename.includes('.')) {
            detectedExtension = filename.split('.').pop() || 'mp3'
            console.log('Detected file extension from content-disposition:', detectedExtension)
          }
        }
      }
      
      // Create blob with proper content type
      const audioBlob = await audioResponse.blob()
      console.log('Audio blob created:', {
        size: audioBlob.size,
        type: audioBlob.type
      })
      
      // Check if the response is actually audio data
      if (audioBlob.size === 0) {
        console.error('Audio response is empty!')
        throw new Error('Audio response is empty')
      }
      
      // Check if the response type is audio
      if (!audioBlob.type.startsWith('audio/') && audioBlob.type !== '') {
        console.warn('Response type is not audio:', audioBlob.type)
      }
      
      // Check if the response is actually audio data by examining the first few bytes
      const arrayBuffer = await audioBlob.arrayBuffer()
      const uint8Array = new Uint8Array(arrayBuffer)
      const firstBytes = Array.from(uint8Array.slice(0, 16)).map(b => b.toString(16).padStart(2, '0')).join(' ')
      console.log('First 16 bytes of audio data:', firstBytes)
      console.log('Audio data size:', arrayBuffer.byteLength, 'bytes')
      
      // Validate that the audio data is not corrupted
      if (arrayBuffer.byteLength < 100) {
        console.error('Audio data is too small, likely corrupted:', arrayBuffer.byteLength, 'bytes')
        throw new Error('Audio data is too small, likely corrupted')
      }
      
      // Check for common audio file signatures and update extension if needed
      let finalExtension = detectedExtension
      if (uint8Array[0] === 0xFF && (uint8Array[1] === 0xFB || uint8Array[1] === 0xF3)) {
        console.log('Detected MP3 file signature')
        finalExtension = 'mp3'
      } else if (uint8Array[0] === 0x52 && uint8Array[1] === 0x49 && uint8Array[2] === 0x46 && uint8Array[3] === 0x46) {
        console.log('Detected WAV file signature')
        finalExtension = 'wav'
      } else if (uint8Array[4] === 0x66 && uint8Array[5] === 0x74 && uint8Array[6] === 0x79 && uint8Array[7] === 0x70) {
        console.log('Detected MP4/M4A file signature')
        finalExtension = 'm4a'
      } else {
        console.warn('Unknown file signature, using detected extension:', finalExtension)
      }
      
      // Update content type based on final extension
      const finalContentType = `audio/${finalExtension === 'mp3' ? 'mpeg' : finalExtension}`
      console.log('Final content type:', finalContentType)
      
      // IMPORTANT: Don't create a new blob from the existing blob - this can corrupt the data
      // Instead, use the original blob and just set the type
      const typedAudioBlob = new Blob([arrayBuffer], { type: finalContentType })
      console.log('Typed audio blob created:', {
        size: typedAudioBlob.size,
        type: typedAudioBlob.type
      })
      
      // Validate the blob
      if (typedAudioBlob.size === 0) {
        console.error('Audio blob is empty!')
        throw new Error('Audio blob is empty')
      }
      
      if (typedAudioBlob.size !== arrayBuffer.byteLength) {
        console.error('Blob size mismatch! Expected:', arrayBuffer.byteLength, 'Got:', typedAudioBlob.size)
        throw new Error('Blob size mismatch')
      }
      
      if (!typedAudioBlob.type.startsWith('audio/')) {
        console.warn('Audio blob type is not audio:', typedAudioBlob.type)
      }
      
      // Test if the blob can be read back correctly
      const testArrayBuffer = await typedAudioBlob.arrayBuffer()
      if (testArrayBuffer.byteLength !== arrayBuffer.byteLength) {
        console.error('Blob readback size mismatch! Expected:', arrayBuffer.byteLength, 'Got:', testArrayBuffer.byteLength)
        throw new Error('Blob readback size mismatch')
      }
      
      console.log('Blob validation passed - size and readback are correct')
      
      const blobUrl = URL.createObjectURL(typedAudioBlob)
      console.log('Blob URL created:', blobUrl)
      
      // Test if the blob URL can be accessed
      try {
        const testResponse = await fetch(blobUrl)
        if (!testResponse.ok) {
          console.error('Blob URL test failed:', testResponse.status)
          throw new Error('Blob URL test failed')
        }
        console.log('Blob URL test passed')
      } catch (error) {
        console.error('Blob URL test error:', error)
        throw new Error(`Blob URL test error: ${error}`)
      }
      
      // Alternative approach: try to create a blob directly from the response
      // This might work better if the first approach fails
      let alternativeBlobUrl = null
      try {
        console.log('Trying alternative blob creation approach...')
        const alternativeBlob = new Blob([arrayBuffer], { type: finalContentType })
        alternativeBlobUrl = URL.createObjectURL(alternativeBlob)
        console.log('Alternative blob created:', {
          size: alternativeBlob.size,
          type: alternativeBlob.type,
          url: alternativeBlobUrl
        })
      } catch (error) {
        console.error('Alternative blob creation failed:', error)
      }
      
      setAudioUrl(blobUrl)
    } catch (error) {
      console.error('Error processing audio response:', error)
      setAudioUrl(null) // Ensure audioUrl is null on error
    }
  }

  const formatTimestamp = (timestamp: number) => {
    try {
      // Convert epoch timestamp (seconds) to milliseconds and create Date object
      const date = new Date(timestamp * 1000)
      
      // Check if date is valid
      if (isNaN(date.getTime())) {
        console.warn('Invalid epoch timestamp:', timestamp)
        return 'Invalid date'
      }
      
      // Format in local timezone
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZoneName: 'long'
      })
    } catch (error) {
      console.error('Error formatting epoch timestamp:', error, timestamp)
      return 'Invalid date'
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <div className="text-gray-600 text-lg">Loading call details...</div>
        </div>
      </div>
    )
  }

  if (error || !call) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="text-red-500 text-6xl mb-4">❌</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Error Loading Call</h1>
          <p className="text-gray-600 mb-6">{error || 'Call not found'}</p>
          <button 
            onClick={() => router.push('/')}
            className="btn-primary"
          >
            Back to Calls
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/')}
                className="flex items-center text-gray-600 hover:text-gray-900 transition-colors duration-200"
              >
                <ArrowLeftIcon className="w-5 h-5 mr-2" />
                Back to Calls
              </button>
              <div className="h-6 w-px bg-gray-300"></div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Call Details</h1>
                <p className="text-sm text-gray-500">{call.call_id}</p>
              </div>
            </div>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <div className="flex items-center">
                <ClockIcon className="w-4 h-4 mr-1" />
                {formatTimestamp(call.timestamp)}
              </div>
              {call.transcript && typeof call.transcript === 'object' && call.transcript.participants && (
                <div className="flex items-center">
                  <UsersIcon className="w-4 h-4 mr-1" />
                  {call.transcript.participants.length} participants
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Call Health Summary */}
      {call.processed_data && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <h3 className="text-lg font-medium text-gray-900">Call Health Summary</h3>
                {call.processed_data.summary?.conversation_health_score && (
                  <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                    call.processed_data.summary.conversation_health_score >= 80 
                      ? 'bg-green-100 text-green-800' 
                      : call.processed_data.summary.conversation_health_score >= 60 
                      ? 'bg-yellow-100 text-yellow-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    Score: {call.processed_data.summary.conversation_health_score}/100
                  </div>
                )}
              </div>
              <div className="flex items-center space-x-6 text-sm text-gray-600">
                {call.processed_data.summary?.pause_count !== undefined && (
                  <div className="flex items-center space-x-2">
                    <span className="font-medium">Pauses:</span>
                    <span className="text-gray-900">{call.processed_data.summary.pause_count}</span>
                  </div>
                )}
                {call.processed_data.summary?.interruption_count !== undefined && (
                  <div className="flex items-center space-x-2">
                    <span className="font-medium">Interruptions:</span>
                    <span className="text-gray-900">{call.processed_data.summary.interruption_count}</span>
                  </div>
                )}
                {call.processed_data.summary?.termination_issues !== undefined && (
                  <div className="flex items-center space-x-2">
                    <span className="font-medium">Termination Issues:</span>
                    <span className="text-gray-900">{call.processed_data.summary.termination_issues}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Pause Information Banners */}
      {call.processed_data?.pauses && call.processed_data.pauses.length > 0 && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          {/* Pause Summary Header */}
          {call.processed_data.pauses.length > 1 && (
            <div className="bg-red-50 border-l-4 border-red-400 rounded-r-lg p-4 mb-4">
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-medium text-red-800">
                    Multiple Pauses Detected
                  </h3>
                  <p className="text-sm text-red-700 mt-1">
                    {call.processed_data.pauses.length} pause{call.processed_data.pauses.length !== 1 ? 's' : ''} found during audio analysis
                  </p>
                </div>
              </div>
            </div>
          )}
          
          <div className="space-y-3">
            {call.processed_data.pauses.map((pause: any, index: number) => {
              // Determine banner color based on pause count and severity
              const isSinglePause = call.processed_data.pauses.length === 1;
              const isLowSeverity = pause.severity === 'low';
              const shouldShowYellow = isSinglePause && isLowSeverity;
              const shouldShowRed = !shouldShowYellow; // Multiple pauses or high severity
              
              const bannerClasses = shouldShowYellow 
                ? 'bg-yellow-50 border-l-4 border-yellow-400' 
                : 'bg-red-50 border-l-4 border-red-400';
              
              const iconClasses = shouldShowYellow 
                ? 'h-5 w-5 text-yellow-400' 
                : 'h-5 w-5 text-red-400';
              
              const textClasses = shouldShowYellow 
                ? 'text-yellow-800' 
                : 'text-red-800';
              
              const descriptionClasses = shouldShowYellow 
                ? 'text-yellow-700' 
                : 'text-red-700';
              
              return (
                <div key={index} className={`${bannerClasses} rounded-r-lg p-4`}>
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      <svg className={iconClasses} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <h3 className={`text-sm font-medium ${textClasses}`}>
                        Pause #{index + 1}
                      </h3>
                      <p className={`mt-1 text-sm ${descriptionClasses}`}>
                        {pause.duration.toFixed(1)}s pause at {pause.start_time.toFixed(1)}s 
                        {pause.type && ` (${pause.type})`}
                        {pause.severity && ` - ${pause.severity} severity`}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
          
        </div>
      )}

      {/* Termination Issues Banners */}
      {call.processed_data?.termination?.issues && call.processed_data.termination.issues.length > 0 && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          
          <div className="space-y-3">
            {call.processed_data.termination.issues.map((issue: string, index: number) => (
              <div className="bg-red-50 border-l-4 border-red-400 rounded-r-lg p-4 mb-4">
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-red-800">
                      {issue}
                    </h3>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
        </div>
      )}

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column: Audio Player + Speaking Activity */}
          <div className="space-y-6">
            {/* Audio Player */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <span className="text-2xl mr-3">🎵</span>
                Audio Player
              </h2>
              {audioUrl ? (
                <AudioPlayer 
                  audioUrl={audioUrl} 
                  callId={call.call_id}
                  timestamp={call.timestamp}
                />
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <div className="text-4xl mb-2">🔇</div>
                  <div className="text-lg font-medium mb-2">Audio not available</div>
                  <div className="text-sm text-gray-400">
                    This call's audio file could not be processed or is unavailable.
                  </div>
                </div>
              )}
            </div>

            {/* Speaking Activity */}
            {call.processed_data ? (
              <EnhancedTimeline 
                transcript={transcript} 
                processedData={call.processed_data}
              />
            ) : (
              <TimelineBars transcript={transcript} />
            )}
          </div>

          {/* Right Column: Transcript */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <span className="text-2xl mr-3">📋</span>
              Transcript
            </h2>
            {transcript ? (
              <TranscriptViewer transcript={transcript} />
            ) : (
              <div className="text-center py-12 text-gray-500">
                <div className="text-4xl mb-2">📝</div>
                Transcript not available
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
