import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { getCaseNotes } from '~/lib/api'

type CaseNote = {
  id: number
  summary: string
  reported_timestamp: string
}

const CaseNotesPage = () => {
  const [caseNotes, setCaseNotes] = useState<CaseNote[]>([])

  useEffect(() => {
    const loadCaseNotes = async () => {
      try {
        const data = await getCaseNotes()
        setCaseNotes(data)
      } catch (error) {
        console.error('Error fetching case notes:', error)
      }
    }

    loadCaseNotes()
  }, [])

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp)
    return isNaN(date.getTime()) ? 'Unknown date' : date.toLocaleString()
  }

  return (
    <div className='flex flex-col h-[calc(100vh-56px)] bg-gray-100'>
      <div className='max-w-2xl mx-auto mt-4 sm:mt-8 w-full px-2 sm:px-4'>
        <h2 className='text-xl sm:text-2xl text-(--primary-color) font-bold mb-4 text-center sm:text-left'>
          Case Notes
        </h2>

        {caseNotes.length === 0 ? (
          <div className='text-gray-500 text-center py-12 text-base sm:text-lg'>
            No case notes found.
            <br />
            Generate a case note from the <b>Chat</b> page!
          </div>
        ) : (
          <ul className='space-y-3 sm:space-y-4 w-full max-w-md mx-auto'>
            {caseNotes.map((note) => (
              <li key={note.id}>
                <Link
                  to={`/case-notes/${note.id}`}
                  className='w-full min-w-0 max-w-full block p-3 sm:p-4 bg-white rounded-lg shadow transition-all duration-200
                    hover:bg-purple-50 hover:shadow-lg hover:-translate-y-1 border border-transparent hover:border-purple-400  '
                >
                  <div className='font-semibold text-purple-700 text-base sm:text-lg'>Case Note #{note.id}</div>
                  <div className='text-xs sm:text-sm text-gray-500'>{formatDate(note.reported_timestamp)}</div>
                  <div className='text-sm sm:text-base text-gray-700 mt-1 truncate'>{note.summary}</div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

export default CaseNotesPage
