'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { AgentAnalysis } from '@/components/AgentAnalysis'
import { TranscriptAnalysis } from '@/components/TranscriptAnalysis'
import { AudioAnalysis } from '@/components/AudioAnalysis'
import { MediaSection } from '@/components/MediaSection'
import { TranscriptViewer } from '@/components/TranscriptViewer'
import { TabbedLayout } from '@/components/TabbedLayout'
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
  const [reanalyzing, setReanalyzing] = useState(false)

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
        
        // Debug: Log the call data to see what's being returned
        console.log('Call data received:', callData)
        console.log('Call processed_data:', callData.processed_data)
        console.log('Transcript summary:', callData.processed_data?.transcript_summary)
        
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

  const handleReanalyze = async (agentType: string, context?: string) => {
    if (!callId) return
    
    setReanalyzing(true)
    try {
      const response = await fetch(`/api/calls/${callId}/analyze-agent`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          call_id: callId,
          agent_type: agentType,
          call_context: context
        })
      })
      
      if (response.ok) {
        const result = await response.json()
        // Refresh call data to get updated analysis
        await fetchCallData()
      } else {
        const error = await response.json()
        console.error('Reanalysis failed:', error)
        // You could show a toast notification here
      }
    } catch (error) {
      console.error('Error during reanalysis:', error)
    } finally {
      setReanalyzing(false)
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

      {/* Tabbed Layout for Call Analysis */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <TabbedLayout
          tabs={[
            {
              id: 'transcript-analysis',
              label: 'Transcript Analysis',
              icon: '📋',
              content: (
                <div className="space-y-6">
                  {/* Transcript Summary */}
                  {call.processed_data?.processed_data?.transcript_summary?.call_outcome ? (
                    <TranscriptAnalysis 
                      summary={call.processed_data?.processed_data?.transcript_summary} 
                    />
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <div className="text-4xl mb-2">📋</div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">No Transcript Summary Available</h3>
                      <p className="text-gray-600">
                        This call does not have a transcript summary. Summaries are generated automatically during call processing.
                      </p>
                    </div>
                  )}

                  {/* Agent Performance Analysis */}
                  {call.processed_data?.agent_analysis && (
                    <div className="pt-6 border-t border-gray-200">
                      <AgentAnalysis 
                        analysis={call.processed_data.agent_analysis}
                        callId={call.call_id}
                        onReanalyze={handleReanalyze}
                      />
                    </div>
                  )}
                </div>
              )
            },
            {
              id: 'audio-analysis',
              label: 'Audio Analysis',
              icon: '🎵',
              content: (
                <div className="space-y-6">
                  {/* Audio Analysis */}
                  {call.processed_data && (
                    <AudioAnalysis processedData={call.processed_data} />
                  )}

                  {/* Media Section */}
                  <div className="pt-6 border-t border-gray-200">
                    <MediaSection 
                      audioUrl={audioUrl}
                      processedData={call.processed_data}
                      transcript={transcript}
                      callId={call.call_id}
                      timestamp={call.timestamp}
                    />
                  </div>
                </div>
              )
            },
            {
              id: 'transcript',
              label: 'Raw Transcript',
              icon: '📝',
              content: (
                <div>
                  {transcript ? (
                    <TranscriptViewer transcript={transcript} />
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <div className="text-4xl mb-2">📝</div>
                      <p>No transcript available</p>
                    </div>
                  )}
                </div>
              )
            }
          ]}
          defaultTab="transcript-analysis"
        />
      </div>
    </div>
  )
}
