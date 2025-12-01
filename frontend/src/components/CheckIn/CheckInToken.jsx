import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import axios from 'axios'
import StammrollenInput from './StammrollenInput'

function CheckInToken() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [session, setSession] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [feedback, setFeedback] = useState(null)

  const token = searchParams.get('token')

  useEffect(() => {
    if (token) {
      validateToken()
    } else {
      setError('Kein Token angegeben')
      setLoading(false)
    }
  }, [token])

  const validateToken = async () => {
    try {
      const response = await axios.get(`/api/sessions/checkin/token/${token}`)
      if (response.data.valid) {
        setSession(response.data.session)
      } else {
        setError('Token ist ungültig')
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Token ungültig oder abgelaufen')
    } finally {
      setLoading(false)
    }
  }

  const showFeedback = (type, message) => {
    setFeedback({ type, message })
    setTimeout(() => setFeedback(null), 3000)
  }

  const handleCheckIn = async (stammrollennummer) => {
    setActionLoading(true)
    try {
      const response = await axios.post('/api/attendance/toggle', {
        session_id: session.id,
        stammrollennummer
      })
      
      showFeedback('success', response.data.message)
      
      // Nach 2 Sekunden zur Hauptseite navigieren
      setTimeout(() => {
        navigate('/')
      }, 2000)
    } catch (err) {
      showFeedback('error', err.response?.data?.detail || 'Fehler bei der Aktion')
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-feuerwehr-red border-t-transparent mx-auto"></div>
          <p className="mt-4 text-gray-600 text-lg">Prüfe QR-Code...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
        <div className="card max-w-md w-full text-center">
          <div className="text-6xl mb-4">❌</div>
          <h2 className="text-xl font-bold text-red-600 mb-2">Ungültiger QR-Code</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => navigate('/')}
            className="btn-primary w-full"
          >
            Zur Startseite
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* Feedback Banner */}
      {feedback && (
        <div className={`fixed top-0 left-0 right-0 z-50 p-4 text-center text-white text-lg font-semibold
                        ${feedback.type === 'success' ? 'bg-green-500' : 'bg-red-500'}`}>
          {feedback.message}
        </div>
      )}

      {/* Header */}
      <header className="bg-feuerwehr-red text-white py-4 px-6 shadow-lg">
        <div className="max-w-md mx-auto text-center">
          <h1 className="text-2xl font-bold">🚒 Feuerwehr Check-in</h1>
          <p className="text-red-100">{session?.event_type_display}</p>
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 p-4 flex items-center justify-center">
        <div className="w-full max-w-md">
          <div className="card">
            <div className="text-center mb-6">
              <div className="text-5xl mb-4">✅</div>
              <h2 className="text-xl font-bold text-gray-800">QR-Code erkannt!</h2>
              <p className="text-gray-600">Bitte Stammrollennummer eingeben</p>
            </div>
            
            <StammrollenInput
              onSubmit={handleCheckIn}
              onCancel={() => navigate('/')}
              loading={actionLoading}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-200 py-2 text-center text-sm text-gray-500">
        Session: {session?.event_type_display} - Gestartet um {session?.start_time && new Date(session.start_time).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}
      </footer>
    </div>
  )
}

export default CheckInToken
