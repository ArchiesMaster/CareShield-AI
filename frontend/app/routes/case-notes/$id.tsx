import { useEffect, useState } from 'react'
import { useParams } from 'react-router'
import { getCaseNote } from '~/lib/api'
import type { CaseNote } from '~/types/case-note'

const formatDateTime = (timestamp?: string | null) => {
  if (!timestamp) return 'N/A'
  const date = new Date(timestamp)
  return isNaN(date.getTime()) ? timestamp : date.toLocaleString()
}

const formatDateOnly = (value?: string | null) => {
  if (!value) return 'N/A'
  const date = new Date(value)
  return isNaN(date.getTime()) ? value : date.toLocaleDateString()
}

const formatTimeOnly = (value?: string | null) => {
  if (!value) return 'N/A'

  // Backend may return "14:30:00"
  const parts = value.split(':')
  if (parts.length >= 2) {
    return `${parts[0]}:${parts[1]}`
  }

  return value
}

const CaseNoteDetailPage = () => {
  const { id } = useParams()
  const [caseNote, setCaseNote] = useState<CaseNote | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return

    const fetchCaseNote = async () => {
      try {
        const data = await getCaseNote(Number(id))
        setCaseNote(data)
      } catch (err) {
        console.error(err)
        setError('Failed to load case note.')
      }
    }

    fetchCaseNote()
  }, [id])

  if (error) {
    return (
      <div className='flex flex-col h-[calc(100vh-56px)] bg-gray-100'>
        <div className='max-w-2xl mx-auto mt-8 w-full px-2 sm:px-4 md:px-8'>
          <div className='bg-white p-4 sm:p-6 rounded-lg shadow border border-red-200 text-red-600'>{error}</div>
        </div>
      </div>
    )
  }

  if (!caseNote) {
    return (
      <div className='flex flex-col h-[calc(100vh-56px)] bg-gray-100'>
        <div className='max-w-2xl mx-auto mt-8 w-full text-gray-500 px-2 sm:px-4 md:px-8'>Loading case note...</div>
      </div>
    )
  }

  const conversationLog = caseNote.metadata_json?.conversation_log

  return (
    <div className='flex flex-col h-[calc(100vh-56px)] bg-gray-100'>
      <div className='max-w-2xl mx-auto mt-4 sm:mt-8 w-full space-y-6 px-2 sm:px-4 md:px-8'>
        {/* Header */}
        <div>
          <h1 className='text-2xl sm:text-3xl font-bold text-(--primary-color)'>Case Note #{caseNote.id}</h1>
          <p className='text-xs sm:text-sm text-gray-500'>Reported: {formatDateTime(caseNote.reported_timestamp)}</p>
        </div>

        {/* Summary */}
        <section className='bg-white p-3 sm:p-5 rounded-lg shadow transition-all duration-200 border border-transparent'>
          <h2 className='text-lg sm:text-xl font-semibold text-purple-700 mb-2'>Summary</h2>
          <p className='text-gray-800'>{caseNote.summary}</p>
        </section>

        {/* Report Details */}
        <section className='bg-white p-3 sm:p-5 rounded-lg shadow transition-all duration-200 border border-transparent'>
          <h2 className='text-xl font-semibold text-purple-700 mb-4'>Report Details</h2>
          <div className='grid grid-cols-1 md:grid-cols-2 gap-4 text-xs sm:text-sm text-gray-800'>
            <div>
              <span className='font-semibold text-gray-600'>Report Type:</span>{' '}
              {caseNote.metadata_json?.report_type || 'N/A'}
            </div>
            <div>
              <span className='font-semibold text-gray-600'>Incident Occurred:</span>{' '}
              {caseNote.incident_occurred ? 'Yes' : 'No'}
            </div>

            <div>
              <span className='font-semibold text-gray-600'>Category:</span> {caseNote.metadata_json?.category || 'N/A'}
            </div>

            <div>
              <span className='font-semibold text-gray-600'>Incident Date:</span>{' '}
              {formatDateOnly(caseNote.incident_date)}
            </div>

            <div>
              <span className='font-semibold text-gray-600'>Incident Time:</span>{' '}
              {formatTimeOnly(caseNote.incident_time)}
            </div>
            <div>
              <span className='font-semibold text-gray-600'>Location:</span> {caseNote.location || 'N/A'}
            </div>
            <div>
              <span className='font-semibold text-gray-600'>Injury Status:</span> {caseNote.injury_status || 'N/A'}
            </div>
            <div>
              <span className='font-semibold text-gray-600'>Languages:</span>{' '}
              {caseNote.metadata_json?.languages?.join(', ') || 'N/A'}
            </div>
            <div>
              <span className='font-semibold text-gray-600'>Severity:</span> {caseNote.metadata_json?.severity || 'N/A'}
            </div>
            <div>
              <span className='font-semibold text-gray-600'>Escalation Required:</span>{' '}
              {caseNote.metadata_json?.escalation_required || 'N/A'}
            </div>
          </div>
        </section>

        {/* Original Text */}
        <section className='bg-white p-3 sm:p-5 rounded-lg shadow transition-all duration-200 border border-transparent'>
          <h2 className='text-lg sm:text-xl font-semibold text-purple-700 mb-2'>Original Text</h2>
          <p className='whitespace-pre-wrap text-gray-800'>{caseNote.original_text}</p>
        </section>

        {/* English Translation */}
        {caseNote.english_translation && (
          <section className='bg-white p-3 sm:p-5 rounded-lg shadow transition-all duration-200 border border-transparent'>
            <h2 className='text-lg sm:text-xl font-semibold text-purple-700 mb-2'>English Translation</h2>
            <p className='whitespace-pre-wrap text-gray-800'>{caseNote.english_translation}</p>
          </section>
        )}

        {/* Conversation Log */}
        {conversationLog && conversationLog.length > 0 && (
          <section className='bg-white p-3 sm:p-5 rounded-lg shadow transition-all duration-200 border border-transparent'>
            <h2 className='text-lg sm:text-xl font-semibold text-purple-700 mb-4'>Conversation Log</h2>
            <div className='space-y-3'>
              {conversationLog.map((entry, index) => (
                <div key={index} className='border rounded-lg p-4 bg-gray-50 transition-all duration-200'>
                  <div className='text-xs text-gray-500 mb-1'>
                    {entry.role.toUpperCase()} • {formatDateTime(entry.timestamp)}
                  </div>

                  {/* Original Message */}
                  <div className='text-gray-800 whitespace-pre-wrap'>{entry.message}</div>

                  {/* Metadata Line (Audio / Translation Info) */}
                  {(entry.input_type === 'audio' || entry.was_translated) && (
                    <div className='text-xs text-gray-400 italic mt-1'>
                      {entry.input_type === 'audio' && (
                        <>
                          Transcribed from audio
                          {entry.original_language && ` (Detected: ${entry.original_language.toUpperCase()})`}
                        </>
                      )}

                      {entry.input_type === 'audio' && entry.was_translated && ' • '}

                      {entry.was_translated &&
                        entry.original_language &&
                        `Translated from ${entry.original_language.toUpperCase()}`}
                    </div>
                  )}

                  {/* Translated Message */}
                  {entry.translated_message && (
                    <div className='text-gray-600 italic mt-2 whitespace-pre-wrap border-l-4 border-purple-300 pl-3'>
                      {entry.translated_message}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  )
}

export default CaseNoteDetailPage
