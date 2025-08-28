'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Call } from '@/types/call'
import { ChevronLeftIcon, ChevronRightIcon, ClockIcon, PlayIcon, ExternalLinkIcon, SearchIcon } from 'lucide-react'

export function CallList() {
  const router = useRouter()
  const [calls, setCalls] = useState<Call[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [totalCalls, setTotalCalls] = useState(0)
  const [searchTerm, setSearchTerm] = useState('')
  const [pageSize, setPageSize] = useState(10)

  useEffect(() => {
    fetchCalls()
  }, [page, pageSize])

  useEffect(() => {
    fetchTotalCount()
  }, [])

  const fetchTotalCount = async () => {
    try {
      const response = await fetch('/api/calls/count')
      if (response.ok) {
        const data = await response.json()
        setTotalCalls(data.total)
      }
    } catch (err) {
      console.error('Failed to fetch total count:', err)
    }
  }

  const fetchCalls = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`/api/calls/?skip=${(page - 1) * pageSize}&limit=${pageSize}`)
      
      if (!response.ok) {
        throw new Error('Failed to fetch calls')
      }
      
      const data = await response.json()
      
      // Debug: Log the raw data to see timestamp format
      console.log('Raw data from backend:', data)
      if (data.length > 0) {
        console.log('First call timestamp:', data[0].timestamp, 'Type:', typeof data[0].timestamp)
      }
      
      // No need to sort here since backend now orders by timestamp
      setCalls(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
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

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1) {
      setPage(newPage)
    }
  }

  const handleCallClick = (call: Call) => {
    router.push(`/call/${call.call_id}`)
  }

  const filteredCalls = calls.filter(call => 
    call.call_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    call.timestamp.toString().toLowerCase().includes(searchTerm.toLowerCase())
  )

  const totalPages = Math.ceil(totalCalls / pageSize)

  if (loading && calls.length === 0) {
    return (
      <div className="space-y-6">
        {/* Search Bar Skeleton */}
        <div className="h-10 bg-gray-200 rounded-lg animate-pulse"></div>
        
        {/* Calls List Skeleton */}
        <div className="space-y-3">
          {[...Array(5)].map((_, index) => (
            <div key={index} className="flex items-center justify-between p-5 bg-white rounded-xl border border-gray-200">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-gray-200 rounded-full animate-pulse"></div>
                <div className="space-y-2">
                  <div className="h-5 bg-gray-200 rounded w-32 animate-pulse"></div>
                  <div className="h-4 bg-gray-200 rounded w-24 animate-pulse"></div>
                </div>
              </div>
              <div className="text-right space-y-2">
                <div className="h-4 bg-gray-200 rounded w-20 animate-pulse"></div>
                <div className="h-3 bg-gray-200 rounded w-16 animate-pulse"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-500 text-6xl mb-4">❌</div>
        <div className="text-red-500 text-xl font-semibold mb-2">Error loading calls</div>
        <div className="text-gray-600 mb-6 max-w-md mx-auto">{error}</div>
        <button 
          onClick={() => fetchCalls()}
          className="btn-primary"
        >
          Try Again
        </button>
      </div>
    )
  }

  if (calls.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="text-gray-400 text-6xl mb-4">📞</div>
        <div className="text-gray-500 text-xl font-semibold mb-2">No calls found</div>
        <p className="text-gray-400 max-w-md mx-auto">
          It looks like you haven't recorded any calls yet. Start by uploading an audio file to see it here.
        </p>
      </div>
    )
  }

  // Calculate overall statistics for processed calls
  const processedCalls = calls.filter(call => call.processed_data)
  const totalProcessedCalls = processedCalls.length
  
  const averageHealthScore = totalProcessedCalls > 0 
    ? Math.round(processedCalls.reduce((sum, call) => 
        sum + (call.processed_data?.call_health_score || 0), 0) / totalProcessedCalls)
    : 0
  
  const totalPauses = processedCalls.reduce((sum, call) => 
    sum + (call.processed_data?.pauses?.length || 0), 0)
  
  const totalIssues = processedCalls.reduce((sum, call) => 
    sum + (call.processed_data?.termination?.issues?.length || 0), 0)

  return (
    <div className="space-y-6">

      {/* Search Bar */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <SearchIcon className="h-5 w-5 text-gray-400" />
        </div>
        <input
          type="text"
          placeholder="Search calls by ID or timestamp..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
        />
      </div>

      {/* Calls List */}
      <div className="space-y-3">
        {filteredCalls.map((call) => (
          <div
            key={call.call_id}
            onClick={() => handleCallClick(call)}
            className="group flex items-center justify-between p-5 bg-white hover:bg-gray-50 rounded-xl cursor-pointer transition-all duration-200 border border-gray-200 hover:border-primary-300 hover:shadow-lg"
          >
            <div className="flex items-center space-x-4">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-gradient-to-br from-primary-100 to-primary-200 group-hover:from-primary-200 group-hover:to-primary-300 rounded-full flex items-center justify-center transition-all duration-200 shadow-sm">
                  <PlayIcon className="w-6 h-6 text-primary-600" />
                </div>
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <div className="font-semibold text-gray-900 group-hover:text-primary-700 transition-colors duration-200 text-lg">
                    {call.call_id}
                  </div>
                  {/* Processing Status Badge */}
                  {call.processed_data ? (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      <span className="w-2 h-2 bg-green-400 rounded-full mr-1"></span>
                      Processed
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                      <span className="w-2 h-2 bg-gray-400 rounded-full mr-1"></span>
                      Raw
                    </span>
                  )}
                </div>
                <div className="flex items-center text-sm text-gray-500 mt-1">
                  <ClockIcon className="w-4 h-4 mr-2" />
                  {formatTimestamp(call.timestamp)}
                </div>
              </div>
            </div>
            <div className="text-right">
              {/* Processed Data Metrics */}
              {call.processed_data && (
                <div className="mb-2 space-y-1">
                  {/* Call Health Score */}
                  {call.processed_data.call_health_score !== undefined && (
                    <div className="flex items-center justify-end space-x-2">
                      <span className="text-xs text-gray-500">Health:</span>
                      <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
                        call.processed_data.call_health_score >= 80 ? 'bg-green-100 text-green-800' :
                        call.processed_data.call_health_score >= 60 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {call.processed_data.call_health_score}%
                      </span>
                    </div>
                  )}
                  
                  {/* Pause Count */}
                  {call.processed_data.pauses && call.processed_data.pauses.length > 0 && (
                    <div className="flex items-center justify-end space-x-2">
                      <span className="text-xs text-gray-500">Pauses:</span>
                      <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
                        call.processed_data.pauses.length === 1 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {call.processed_data.pauses.length}
                      </span>
                    </div>
                  )}
                  
                  {/* Termination Issues */}
                  {call.processed_data.termination && call.processed_data.termination.issues && call.processed_data.termination.issues.length > 0 && (
                    <div className="flex items-center justify-end space-x-2">
                      <span className="text-xs text-gray-500">Issues:</span>
                      <span className="text-xs font-semibold px-2 py-1 rounded-full bg-red-100 text-red-800">
                        {call.processed_data.termination.issues.length}
                      </span>
                    </div>
                  )}
                </div>
              )}
              
              {/* Participants Count */}
              <div className="text-sm text-gray-600 font-medium mb-1">
                {call.transcript && typeof call.transcript === 'object' && call.transcript.participants
                  ? `${call.transcript.participants.length} participants`
                  : 'No participants'
                }
              </div>
              
              {/* View Details Link */}
              <div className="flex items-center text-xs text-gray-400 group-hover:text-primary-500 transition-colors duration-200">
                <span className="mr-2">View details</span>
                <ExternalLinkIcon className="w-4 h-4" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between pt-6 border-t border-gray-200">
        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-700">
            Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, totalCalls)} of {totalCalls} calls
          </div>
          
          {/* Page Size Selector */}
          <div className="flex items-center space-x-2">
            <label className="text-sm text-gray-600">Show:</label>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value))
                setPage(1) // Reset to first page when changing page size
              }}
              className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-primary-500"
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
          </div>
        </div>
        
        {totalPages > 1 && (
          <div className="flex items-center space-x-2">
            <button
              onClick={() => handlePageChange(1)}
              disabled={page <= 1}
              className="flex items-center px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              First
            </button>
            <button
              onClick={() => handlePageChange(page - 1)}
              disabled={page <= 1}
              className="flex items-center px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              <ChevronLeftIcon className="w-4 h-4 mr-1" />
              Previous
            </button>
            
            {/* Page Numbers */}
            <div className="flex items-center space-x-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (page <= 3) {
                  pageNum = i + 1;
                } else if (page >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = page - 2 + i;
                }
                
                return (
                  <button
                    key={pageNum}
                    onClick={() => handlePageChange(pageNum)}
                    className={`px-3 py-2 text-sm font-medium rounded-lg transition-all duration-200 ${
                      page === pageNum
                        ? 'bg-primary-500 text-white border border-primary-500'
                        : 'text-gray-500 bg-white border border-gray-300 hover:bg-gray-50 hover:text-gray-700'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>
            
            <button
              onClick={() => handlePageChange(page + 1)}
              disabled={page >= totalPages}
              className="flex items-center px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              Next
              <ChevronRightIcon className="w-4 h-4 ml-1" />
            </button>
            <button
              onClick={() => handlePageChange(totalPages)}
              disabled={page >= totalPages}
              className="flex items-center px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              Last
            </button>
          </div>
        )}
      </div>

      {/* No results for search */}
      {searchTerm && filteredCalls.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 text-4xl mb-3">🔍</div>
          <div className="text-gray-500 text-lg mb-2">No calls found</div>
          <p className="text-gray-400">Try adjusting your search terms</p>
        </div>
      )}
    </div>
  )
}
