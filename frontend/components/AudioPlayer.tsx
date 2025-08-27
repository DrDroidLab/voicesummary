'use client'

import { useState, useRef, useEffect } from 'react'
import { PlayIcon, PauseIcon, Volume2Icon, VolumeXIcon } from 'lucide-react'

interface AudioPlayerProps {
  audioUrl: string
  callId: string
  timestamp: number  // Epoch timestamp in seconds
}

export function AudioPlayer({ audioUrl, callId, timestamp }: AudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [volume, setVolume] = useState(1)
  const [isMuted, setIsMuted] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [networkState, setNetworkState] = useState<number>(0)
  const [audioFormat, setAudioFormat] = useState<string>('Unknown')
  
  const audioRef = useRef<HTMLAudioElement>(null)
  const progressRef = useRef<HTMLDivElement>(null)

  // Debug audio URL changes
  useEffect(() => {
    console.log('AudioPlayer: audioUrl changed to:', audioUrl)
    console.log('AudioPlayer: callId:', callId)
    
    if (audioUrl) {
      setIsLoading(true)
      setError(null)
      
      // Test the audio URL
      testAudioUrl(audioUrl)
    }
  }, [audioUrl, callId])

  // Monitor audio element creation
  useEffect(() => {
    const audio = audioRef.current
    if (audio) {
      console.log('Audio element created:', {
        src: audio.src,
        readyState: audio.readyState,
        networkState: audio.networkState
      })
      
      // Add error event listener
      const handleAudioError = (e: Event) => {
        console.error('Audio element error event:', e)
        const target = e.target as HTMLAudioElement
        if (target.error) {
          console.error('Audio error details:', {
            code: target.error.code,
            message: target.error.message
          })
          
          // Set specific error messages based on error code
          switch (target.error.code) {
            case MediaError.MEDIA_ERR_ABORTED:
              setError('Audio loading was aborted')
              break
            case MediaError.MEDIA_ERR_NETWORK:
              setError('Audio network error')
              break
            case MediaError.MEDIA_ERR_DECODE:
              setError('Audio decode error - unsupported format')
              break
            case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
              setError('Audio source not supported - check format')
              break
            default:
              setError(`Audio error: ${target.error.message}`)
          }
        }
      }
      
      audio.addEventListener('error', handleAudioError)
      
      return () => {
        audio.removeEventListener('error', handleAudioError)
      }
    }
  }, [])

  // Monitor audio element src changes
  useEffect(() => {
    const audio = audioRef.current
    if (audio && audioUrl) {
      console.log('Audio element src set to:', audioUrl)
      audio.src = audioUrl
      console.log('Audio element after src set:', {
        src: audio.src,
        currentSrc: audio.currentSrc,
        readyState: audio.readyState,
        networkState: audio.networkState
      })
    }
  }, [audioUrl])

  const testAudioUrl = async (url: string) => {
    try {
      console.log('Testing audio URL:', url)
      
      // Handle blob URLs differently - they don't support HEAD requests
      if (url.startsWith('blob:')) {
        console.log('Audio URL is a blob, extracting format from blob')
        
        // For blob URLs, we need to get the format from the audio element itself
        // or from the blob type if available
        const audio = audioRef.current
        if (audio) {
          // Wait for the audio to load metadata to get format info
          audio.addEventListener('loadedmetadata', () => {
            console.log('Audio metadata loaded for blob:', {
              duration: audio.duration,
              readyState: audio.readyState
            })
            
            // Try to extract format from the blob type
            const format = extractFormatFromBlobType(url)
            setAudioFormat(format)
          }, { once: true })
        }
        
        // Try to detect format from the blob type if available
        // This will be set when we create the blob with proper content type
        setAudioFormat('Detecting...')
        return
      }
      
      // For regular URLs, test with HEAD request
      const response = await fetch(url, { method: 'HEAD' })
      console.log('Audio URL test response:', {
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries())
      })
      
      if (!response.ok) {
        console.error('Audio URL test failed:', response.status, response.statusText)
        setError(`Audio URL test failed: ${response.status} ${response.statusText}`)
      } else {
        // Check content type
        const contentType = response.headers.get('content-type')
        console.log('Audio content type:', contentType)
        
        // Detect format from URL
        const format = detectAudioFormat(url, contentType)
        console.log('Detected audio format:', format)
        setAudioFormat(format)
      }
    } catch (error) {
      console.error('Audio URL test error:', error)
      setError(`Audio URL test error: ${error}`)
    }
  }

  const detectAudioFormat = (url: string, contentType?: string | null): string => {
    // Try to detect from content type first
    if (contentType) {
      if (contentType.includes('audio/mpeg') || contentType.includes('audio/mp3')) return 'MP3'
      if (contentType.includes('audio/wav')) return 'WAV'
      if (contentType.includes('audio/mp4') || contentType.includes('audio/m4a')) return 'M4A'
      if (contentType.includes('audio/aac')) return 'AAC'
      if (contentType.includes('audio/ogg')) return 'OGG'
      if (contentType.includes('audio/flac')) return 'FLAC'
    }
    
    // Try to detect from URL
    if (url.includes('.mp3')) return 'MP3'
    if (url.includes('.wav')) return 'WAV'
    if (url.includes('.m4a')) return 'M4A'
    if (url.includes('.aac')) return 'AAC'
    if (url.includes('.ogg')) return 'OGG'
    if (url.includes('.flac')) return 'FLAC'
    
    return 'Unknown'
  }

  const detectAudioFormatFromBlob = (blobUrl: string): string => {
    // For blob URLs, we need to get the format from the audio element
    // This will be called when the audio metadata is loaded
    const audio = audioRef.current
    if (audio && audio.src === blobUrl) {
      // Try to get format from the audio element's currentSrc or other properties
      // Since we're now setting the proper content type when creating the blob,
      // the browser should be able to determine the format
      return 'Detected from blob'
    }
    return 'Unknown'
  }

  const extractFormatFromBlobType = (blobUrl: string): string => {
    // Try to extract format from the blob type by examining the audio element
    const audio = audioRef.current
    if (audio && audio.src === blobUrl) {
      // Check if we can get format from the audio element's properties
      if (audio.readyState >= 1) { // HAVE_METADATA
        // Try to infer format from duration and other properties
        if (audio.duration > 0) {
          return `Audio (${Math.round(audio.duration)}s)`
        }
      }
    }
    return 'Audio (Format detecting...)'
  }

  const checkAudioElementState = () => {
    const audio = audioRef.current
    if (audio) {
      console.log('Audio element state:', {
        src: audio.src,
        currentSrc: audio.currentSrc,
        readyState: audio.readyState,
        networkState: audio.networkState,
        error: audio.error,
        duration: audio.duration,
        paused: audio.paused,
        ended: audio.ended
      })
    }
  }

  const testAudioPlayback = async () => {
    const audio = audioRef.current
    if (!audio) return
    
    try {
      console.log('Testing audio playback...')
      console.log('Audio element before play:', {
        src: audio.src,
        readyState: audio.readyState,
        networkState: audio.networkState,
        error: audio.error
      })
      
      // Try to play the audio
      await audio.play()
      console.log('Audio playback started successfully')
      
      // Pause immediately
      audio.pause()
      console.log('Audio playback test completed')
      
    } catch (error) {
      console.error('Audio playback test failed:', error)
      setError(`Playback test failed: ${error}`)
    }
  }

  const validateAudioElement = () => {
    const audio = audioRef.current
    if (!audio) return
    
    console.log('Audio element validation:')
    console.log('- src:', audio.src)
    console.log('- currentSrc:', audio.currentSrc)
    console.log('- readyState:', audio.readyState)
    console.log('- networkState:', audio.networkState)
    console.log('- error:', audio.error)
    console.log('- duration:', audio.duration)
    console.log('- paused:', audio.paused)
    console.log('- ended:', audio.ended)
    
    // Check if the audio element has a valid source
    if (!audio.src) {
      console.error('Audio element has no source')
      setError('Audio element has no source')
      return
    }
    
    // Check if the audio element is in an error state
    if (audio.error) {
      console.error('Audio element error:', audio.error)
      setError(`Audio error: ${audio.error.message}`)
      return
    }
    
    // Check if the audio element can load
    if (audio.readyState === 0) {
      console.log('Audio element is in HAVE_NOTHING state - waiting for data')
    } else if (audio.readyState >= 1) {
      console.log('Audio element has metadata loaded')
    }
  }

  const checkAudioLoadability = () => {
    const audio = audioRef.current
    if (!audio) return
    
    console.log('Checking audio loadability...')
    
    // Try to load the audio
    if (audio.readyState === 0) {
      console.log('Audio element readyState is 0 - attempting to load')
      
      // Create a new audio element to test loading
      const testAudio = new Audio()
      testAudio.src = audio.src
      
      testAudio.addEventListener('loadstart', () => {
        console.log('Test audio load started')
      })
      
      testAudio.addEventListener('loadedmetadata', () => {
        console.log('Test audio metadata loaded successfully')
        setError(null)
      })
      
      testAudio.addEventListener('error', (e) => {
        console.error('Test audio failed to load:', e)
        const target = e.target as HTMLAudioElement
        if (target.error) {
          setError(`Test audio error: ${target.error.message}`)
        }
      })
      
      // Try to load
      testAudio.load()
    } else {
      console.log('Audio element already has data loaded')
    }
  }

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const handleLoadedMetadata = () => {
      console.log('Audio metadata loaded:', {
        duration: audio.duration,
        currentSrc: audio.currentSrc,
        readyState: audio.readyState
      })
      setDuration(audio.duration)
      setIsLoading(false)
      
      // Try to detect format from the audio element
      if (audioUrl.startsWith('blob:')) {
        // For blob URLs, try to get format from the audio element
        const format = extractFormatFromBlobType(audioUrl)
        setAudioFormat(format)
        
        // Also try to infer from duration
        if (audio.duration > 0) {
          const durationFormat = `Audio (${Math.round(audio.duration)}s)`
          if (format === 'Audio (Format detecting...)' || format.includes('Format detecting')) {
            setAudioFormat(durationFormat)
          }
        }
      }
    }

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime)
    }

    const handleEnded = () => {
      setIsPlaying(false)
      setCurrentTime(0)
    }

    const handleError = (e: Event) => {
      console.error('Audio error:', e)
      console.error('Audio error details:', {
        error: audio.error,
        currentSrc: audio.currentSrc,
        networkState: audio.networkState,
        readyState: audio.readyState
      })
      
      // Check the full audio element state
      checkAudioElementState()
      
      setIsLoading(false)
      setError('Failed to load audio file')
    }

    const handleLoadStart = () => {
      console.log('Audio load started:', audio.currentSrc)
      setIsLoading(true)
      setError(null)
    }

    const handleCanPlay = () => {
      console.log('Audio can play:', audio.currentSrc)
      setIsLoading(false)
    }

    const handleNetworkStateChange = () => {
      console.log('Network state changed:', audio.networkState)
      setNetworkState(audio.networkState)
    }

    audio.addEventListener('loadedmetadata', handleLoadedMetadata)
    audio.addEventListener('timeupdate', handleTimeUpdate)
    audio.addEventListener('ended', handleEnded)
    audio.addEventListener('error', handleError)
    audio.addEventListener('loadstart', handleLoadStart)
    audio.addEventListener('canplay', handleCanPlay)
    audio.addEventListener('networkstatechange', handleNetworkStateChange)

    return () => {
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata)
      audio.removeEventListener('timeupdate', handleTimeUpdate)
      audio.removeEventListener('ended', handleEnded)
      audio.removeEventListener('error', handleError)
      audio.removeEventListener('loadstart', handleLoadStart)
      audio.removeEventListener('canplay', handleCanPlay)
      audio.removeEventListener('networkstatechange', handleNetworkStateChange)
    }
  }, [])

  const togglePlayPause = () => {
    const audio = audioRef.current
    if (!audio) return

    if (isPlaying) {
      audio.pause()
      setIsPlaying(false)
    } else {
      audio.play()
      setIsPlaying(true)
    }
  }

  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const audio = audioRef.current
    const progressBar = progressRef.current
    if (!audio || !progressBar) return

    const rect = progressBar.getBoundingClientRect()
    const clickX = e.clientX - rect.left
    const progressBarWidth = rect.width
    const clickPercent = clickX / progressBarWidth
    const newTime = clickPercent * duration

    audio.currentTime = newTime
    setCurrentTime(newTime)
  }

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVolume = parseFloat(e.target.value)
    setVolume(newVolume)
    
    const audio = audioRef.current
    if (audio) {
      audio.volume = newVolume
    }
  }

  const toggleMute = () => {
    const audio = audioRef.current
    if (!audio) return

    if (isMuted) {
      audio.volume = volume
      setIsMuted(false)
    } else {
      audio.volume = 0
      setIsMuted(true)
    }
  }

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60)
    const seconds = Math.floor(time % 60)
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }

  const formatTimestamp = (timestamp: string) => {
    try {
      // Convert epoch timestamp (seconds) to milliseconds and create Date object
      const epochTimestamp = parseInt(timestamp)
      const date = new Date(epochTimestamp * 1000)
      
      // Check if date is valid
      if (isNaN(date.getTime())) {
        console.warn('Invalid epoch timestamp:', timestamp)
        return 'Invalid date'
      }
      
      // Format in local timezone
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZoneName: 'short'
      })
    } catch (error) {
      console.error('Error formatting epoch timestamp:', error, timestamp)
      return 'Invalid date'
    }
  }

  return (
    <div className="space-y-4">
      {/* Call Info */}
      <div className="flex items-center justify-between text-sm text-gray-600">
        <div>
          <span className="font-medium">Call ID:</span> {callId}
        </div>
        <div>
          <span className="font-medium">Recorded:</span> {formatTimestamp(timestamp.toString())}
        </div>
      </div>

      {/* Audio Element */}
      <audio 
        ref={audioRef} 
        src={audioUrl} 
        preload="metadata" 
        crossOrigin="anonymous"
        onError={(e) => console.error('Audio element error:', e)}
        onLoadStart={() => console.log('Audio element load start')}
        onCanPlay={() => console.log('Audio element can play')}
        onLoadedMetadata={() => console.log('Audio element metadata loaded')}
      />

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <span className="ml-2 text-gray-600">Loading audio...</span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="flex items-center justify-center py-8">
          <div className="text-red-600 text-center">
            <div className="text-lg font-medium mb-2">Audio Loading Error</div>
            <div className="text-sm text-gray-600 mb-4">{error}</div>
            <div className="text-xs text-gray-500">
              This might be due to an unsupported audio format or missing file extension.
            </div>
          </div>
        </div>
      )}

      {/* Network Status */}
      <div className="text-center text-sm text-gray-600">
        <div className="inline-flex items-center px-3 py-1 rounded-full bg-gray-100">
          <div className={`w-2 h-2 rounded-full mr-2 ${
            networkState === 0 ? 'bg-gray-400' : 
            networkState === 1 ? 'bg-yellow-400' : 
            networkState === 2 ? 'bg-blue-400' : 
            networkState === 3 ? 'bg-green-400' : 'bg-red-400'
          }`}></div>
          {networkState === 0 ? 'No Source' :
           networkState === 1 ? 'Loading' :
           networkState === 2 ? 'Buffering' :
           networkState === 3 ? 'Ready' : 'Error'}
        </div>
      </div>

      {/* Audio Controls */}
      <div className="flex items-center space-x-4">
        {/* Play/Pause Button */}
        <button
          onClick={togglePlayPause}
          disabled={isLoading}
          className="w-12 h-12 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 rounded-full flex items-center justify-center text-white transition-colors duration-200"
        >
          {isPlaying ? (
            <PauseIcon className="w-6 h-6" />
          ) : (
            <PlayIcon className="w-6 h-6" />
          )}
        </button>

        {/* Progress Bar */}
        <div className="flex-1">
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <span>{formatTime(currentTime)}</span>
            <div
              ref={progressRef}
              onClick={handleProgressClick}
              className="flex-1 h-2 bg-gray-200 rounded-full cursor-pointer relative"
            >
              <div
                className="h-full bg-primary-600 rounded-full transition-all duration-100"
                style={{ width: `${duration > 0 ? (currentTime / duration) * 100 : 0}%` }}
              />
              <div
                className="absolute top-0 w-4 h-4 bg-primary-600 rounded-full -mt-1 -ml-2 cursor-pointer transition-all duration-100 hover:scale-110"
                style={{ left: `${duration > 0 ? (currentTime / duration) * 100 : 0}%` }}
              />
            </div>
            <span>{formatTime(duration)}</span>
          </div>
        </div>

        {/* Volume Control */}
        <div className="flex items-center space-x-2">
          <button
            onClick={toggleMute}
            className="text-gray-600 hover:text-gray-800 transition-colors duration-200"
          >
            {isMuted ? (
              <VolumeXIcon className="w-5 h-5" />
            ) : (
              <Volume2Icon className="w-5 h-5" />
            )}
          </button>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={isMuted ? 0 : volume}
            onChange={handleVolumeChange}
            className="w-20 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
          />
        </div>
      </div>

      {/* Audio Format Info */}
      <div className="text-center text-sm text-gray-600">
        <div className="inline-flex items-center px-3 py-1 rounded-full bg-blue-100 text-blue-800">
          <span className="font-medium">Format:</span> {audioFormat}
        </div>
        <div className="mt-2 space-x-2">
          <button
            onClick={checkAudioElementState}
            className="px-2 py-1 text-xs bg-gray-200 hover:bg-gray-300 rounded text-gray-700"
          >
            Debug State
          </button>
          <button
            onClick={validateAudioElement}
            className="px-2 py-1 text-xs bg-yellow-200 hover:bg-yellow-300 rounded text-yellow-700"
          >
            Validate
          </button>
          <button
            onClick={checkAudioLoadability}
            className="px-2 py-1 text-xs bg-blue-200 hover:bg-blue-300 rounded text-blue-700"
          >
            Test Load
          </button>
          <button
            onClick={testAudioPlayback}
            className="px-2 py-1 text-xs bg-green-200 hover:bg-green-300 rounded text-green-700"
          >
            Test Playback
          </button>
        </div>
      </div>

      {/* Audio Status */}
      <div className="text-center">
        <div className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
          {isPlaying ? (
            <>
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
              Playing
            </>
          ) : (
            <>
              <div className="w-2 h-2 bg-gray-400 rounded-full mr-2"></div>
              Paused
            </>
          )}
        </div>
      </div>

      <style jsx>{`
        .slider::-webkit-slider-thumb {
          appearance: none;
          height: 16px;
          width: 16px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
        }
        
        .slider::-moz-range-thumb {
          height: 16px;
          width: 16px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
          border: none;
        }
      `}</style>
    </div>
  )
}