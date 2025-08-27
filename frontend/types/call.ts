export interface Call {
  call_id: string
  timestamp: number  // Epoch timestamp in seconds
  transcript: any
  audio_file_url: string
  processed_data?: any  // Audio analysis results and enhanced transcript
  created_at: number  // Epoch timestamp in seconds
  updated_at: number  // Epoch timestamp in seconds
}

export interface CallListResponse {
  calls: Call[]
  total: number
  page: number
  limit: number
}
