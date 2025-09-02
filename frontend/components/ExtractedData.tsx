'use client'

import { useState, useEffect } from 'react'
import { CheckCircleIcon, XCircleIcon, ClockIcon, AlertCircleIcon, RefreshCwIcon } from 'lucide-react'

interface ExtractedDataProps {
  callId: string
}

interface ExtractedData {
  call_id: string
  extraction_data?: Record<string, any>
  classification_data?: Record<string, any>
  labeling_data?: Record<string, any>
  processing_status: string
  processing_errors?: Record<string, string>
  created_at: number
  updated_at: number
}

export function ExtractedData({ callId }: ExtractedDataProps) {
  const [extractedData, setExtractedData] = useState<ExtractedData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [processing, setProcessing] = useState(false)

  useEffect(() => {
    fetchExtractedData()
  }, [callId])

  const fetchExtractedData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`/api/calls/${callId}/extracted-data`)
      if (response.ok) {
        const data = await response.json()
        setExtractedData(data)
      } else if (response.status === 404) {
        setExtractedData(null)
      } else {
        throw new Error('Failed to fetch extracted data')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const processDataPipeline = async () => {
    setProcessing(true)
    setError(null)
    
    try {
      const response = await fetch(`/api/calls/${callId}/process-data-pipeline`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          call_id: callId,
          force_reprocess: true
        })
      })
      
      if (response.ok) {
        const result = await response.json()
        if (result.status === 'success' && result.extracted_data) {
          setExtractedData(result.extracted_data)
        } else {
          throw new Error(result.message || 'Processing failed')
        }
      } else {
        throw new Error('Failed to process data pipeline')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setProcessing(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />
      case 'processing':
        return <ClockIcon className="w-5 h-5 text-yellow-500 animate-spin" />
      case 'failed':
        return <XCircleIcon className="w-5 h-5 text-red-500" />
      case 'pending':
        return <ClockIcon className="w-5 h-5 text-gray-500" />
      default:
        return <AlertCircleIcon className="w-5 h-5 text-gray-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50 border-green-200'
      case 'processing':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'failed':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'pending':
        return 'text-gray-600 bg-gray-50 border-gray-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString()
  }

  const renderExtractionData = (data: Record<string, any>) => {
    return Object.entries(data).map(([key, value]) => (
      <div key={key} className="bg-white rounded-lg border border-gray-200 p-4">
        <h4 className="font-medium text-gray-900 mb-3 capitalize">{key.replace(/_/g, ' ')}</h4>
        {value && typeof value === 'object' && !('error' in value) ? (
          <pre className="text-sm text-gray-700 bg-gray-50 p-3 rounded overflow-auto max-h-64">
            {JSON.stringify(value, null, 2)}
          </pre>
        ) : value && 'error' in value ? (
          <div className="text-red-600 text-sm">
            <AlertCircleIcon className="w-4 h-4 inline mr-1" />
            {value.error}
          </div>
        ) : (
          <div className="text-gray-500 text-sm">No data available</div>
        )}
      </div>
    ))
  }

  const renderClassificationData = (data: Record<string, any>) => {
    return Object.entries(data).map(([key, value]) => (
      <div key={key} className="bg-white rounded-lg border border-gray-200 p-4">
        <h4 className="font-medium text-gray-900 mb-3 capitalize">{key.replace(/_/g, ' ')}</h4>
        {value && typeof value === 'string' && !value.startsWith('error:') ? (
          <div className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
            {value}
          </div>
        ) : value && value.startsWith('error:') ? (
          <div className="text-red-600 text-sm">
            <AlertCircleIcon className="w-4 h-4 inline mr-1" />
            {value.replace('error: ', '')}
          </div>
        ) : (
          <div className="text-gray-500 text-sm">No classification available</div>
        )}
      </div>
    ))
  }

  const renderLabelingData = (data: Record<string, any>) => {
    return Object.entries(data).map(([key, value]) => (
      <div key={key} className="bg-white rounded-lg border border-gray-200 p-4">
        <h4 className="font-medium text-gray-900 mb-3 capitalize">{key.replace(/_/g, ' ')}</h4>
        {typeof value === 'boolean' ? (
          <div className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium">
            {value ? (
              <span className="bg-green-100 text-green-800">
                <CheckCircleIcon className="w-4 h-4 inline mr-1" />
                Yes
              </span>
            ) : (
              <span className="bg-gray-100 text-gray-800">
                <XCircleIcon className="w-4 h-4 inline mr-1" />
                No
              </span>
            )}
          </div>
        ) : value && 'error' in value ? (
          <div className="text-red-600 text-sm">
            <AlertCircleIcon className="w-4 h-4 inline mr-1" />
            {value.error}
          </div>
        ) : (
          <div className="text-gray-500 text-sm">No label data available</div>
        )}
      </div>
    ))
  }

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-2 text-gray-600">Loading extracted data...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <AlertCircleIcon className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Data</h3>
        <p className="text-gray-600 mb-4">{error}</p>
        <button
          onClick={fetchExtractedData}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
        >
          <RefreshCwIcon className="w-4 h-4 mr-2" />
          Retry
        </button>
      </div>
    )
  }

  if (!extractedData) {
    return (
      <div className="text-center py-8">
        <div className="text-4xl mb-4">🔍</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Extracted Data Available</h3>
        <p className="text-gray-600 mb-4">
          This call hasn't been processed through the data extraction pipeline yet.
        </p>
        <button
          onClick={processDataPipeline}
          disabled={processing}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
        >
          {processing ? (
            <>
              <RefreshCwIcon className="w-4 h-4 mr-2 animate-spin" />
              Processing...
            </>
          ) : (
            <>
              <RefreshCwIcon className="w-4 h-4 mr-2" />
              Process Data Pipeline
            </>
          )}
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Status Header */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Processing Status</h3>
          <div className="flex items-center space-x-2">
            {getStatusIcon(extractedData.processing_status)}
            <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(extractedData.processing_status)}`}>
              {extractedData.processing_status}
            </span>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
          <div>
            <span className="font-medium">Created:</span> {formatTimestamp(extractedData.created_at)}
          </div>
          <div>
            <span className="font-medium">Updated:</span> {formatTimestamp(extractedData.updated_at)}
          </div>
        </div>

        {extractedData.processing_errors && Object.keys(extractedData.processing_errors).length > 0 && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <h4 className="font-medium text-red-900 mb-2">Processing Errors</h4>
            <div className="space-y-2">
              {Object.entries(extractedData.processing_errors).map(([key, error]) => (
                <div key={key} className="text-sm text-red-700">
                  <span className="font-medium">{key}:</span> {error}
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="mt-4">
          <button
            onClick={processDataPipeline}
            disabled={processing}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
          >
            {processing ? (
              <>
                <RefreshCwIcon className="w-4 h-4 mr-2 animate-spin" />
                Reprocessing...
              </>
            ) : (
              <>
                <RefreshCwIcon className="w-4 h-4 mr-2" />
                Reprocess
              </>
            )}
          </button>
        </div>
      </div>

      {/* Extraction Data */}
      {extractedData.extraction_data && (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900">Extracted Data</h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {renderExtractionData(extractedData.extraction_data)}
          </div>
        </div>
      )}

      {/* Classification Data */}
      {extractedData.classification_data && (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900">Classifications</h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {renderClassificationData(extractedData.classification_data)}
          </div>
        </div>
      )}

      {/* Labeling Data */}
      {extractedData.labeling_data && (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900">Labels</h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {renderLabelingData(extractedData.labeling_data)}
          </div>
        </div>
      )}
    </div>
  )
}
