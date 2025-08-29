'use client'

interface AudioAnalysisProps {
  processedData: any
}

export function AudioAnalysis({ processedData }: AudioAnalysisProps) {
  if (!processedData) {
    return (
      <div className="text-center py-8 text-gray-500">
        <div className="text-4xl mb-2">🎵</div>
        <p>No audio analysis available</p>
      </div>
    )
  }

  const {
    audio_info,
    pauses,
    interruptions,
    termination,
    summary
  } = processedData

  return (
    <div className="space-y-6">
      {/* Audio Information */}
      {audio_info && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-medium text-blue-900 mb-3">Audio Information</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-blue-700 font-medium">Duration:</span>
              <span className="ml-2 text-blue-800">{audio_info.duration?.toFixed(2)}s</span>
            </div>
            <div>
              <span className="text-blue-700 font-medium">Speech Time:</span>
              <span className="ml-2 text-blue-800">{audio_info.speech_time?.toFixed(2)}s</span>
            </div>
            <div>
              <span className="text-blue-700 font-medium">Speech %:</span>
              <span className="ml-2 text-blue-800">{audio_info.speech_percentage?.toFixed(1)}%</span>
            </div>
            <div>
              <span className="text-blue-700 font-medium">File:</span>
              <span className="ml-2 text-blue-800 text-xs truncate">{audio_info.file}</span>
            </div>
          </div>
        </div>
      )}

      {/* Pauses Analysis */}
      {pauses && pauses.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h4 className="font-medium text-yellow-900 mb-3">Pause Analysis</h4>
          <div className="space-y-2">
            {pauses.map((pause: any, index: number) => (
              <div key={index} className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                  <span className="text-yellow-800">
                    {pause.start_time?.toFixed(2)}s - {pause.end_time?.toFixed(2)}s
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-yellow-700 font-medium">{pause.duration?.toFixed(2)}s</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    pause.type === 'long_pause' ? 'bg-red-100 text-red-800' :
                    pause.type === 'medium_pause' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {pause.type?.replace('_', ' ')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Interruptions */}
      {interruptions && interruptions.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h4 className="font-medium text-red-900 mb-3">Interruptions</h4>
          <div className="space-y-2">
            {interruptions.map((interruption: any, index: number) => (
              <div key={index} className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                  <span className="text-red-800">
                    {interruption.start_time?.toFixed(2)}s - {interruption.end_time?.toFixed(2)}s
                  </span>
                </div>
                <span className="text-red-700 font-medium">{interruption.duration?.toFixed(2)}s</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Termination Analysis */}
      {termination && (
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <h4 className="font-medium text-purple-900 mb-3">Call Termination</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex items-center space-x-2">
              <span className={`w-3 h-3 rounded-full ${
                termination.session_started_properly ? 'bg-green-500' : 'bg-red-500'
              }`}></span>
              <span className="text-purple-700 font-medium">Started Properly:</span>
              <span className="text-purple-800">{termination.session_started_properly ? 'Yes' : 'No'}</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`w-3 h-3 rounded-full ${
                termination.session_ended_properly ? 'bg-green-500' : 'bg-red-500'
              }`}></span>
              <span className="text-purple-700 font-medium">Ended Properly:</span>
              <span className="text-purple-800">{termination.session_ended_properly ? 'Yes' : 'No'}</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`w-3 h-3 rounded-full ${
                !termination.abrupt_ending ? 'bg-green-500' : 'bg-red-500'
              }`}></span>
              <span className="text-purple-700 font-medium">Abrupt Ending:</span>
              <span className="text-purple-800">{termination.abrupt_ending ? 'Yes' : 'No'}</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`w-3 h-3 rounded-full ${
                !termination.duplicate_endings ? 'bg-green-500' : 'bg-red-500'
              }`}></span>
              <span className="text-purple-700 font-medium">Duplicate Endings:</span>
              <span className="text-purple-800">{termination.duplicate_endings ? 'Yes' : 'No'}</span>
            </div>
          </div>
          
          {/* Termination Issues */}
          {termination.issues && termination.issues.length > 0 && (
            <div className="mt-3 pt-3 border-t border-purple-200">
              <h5 className="text-sm font-medium text-purple-800 mb-2">Issues Found:</h5>
              <ul className="space-y-1">
                {termination.issues.map((issue: string, index: number) => (
                  <li key={index} className="flex items-start space-x-2 text-sm">
                    <div className="w-1.5 h-1.5 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                    <span className="text-red-700">{issue}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

    </div>
  )
}
