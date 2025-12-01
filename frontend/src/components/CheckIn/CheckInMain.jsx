import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import SessionTypeSelector from './SessionTypeSelector'
import StammrollenInput from './StammrollenInput'
import CurrentAttendees from './CurrentAttendees'

function CheckInMain() {
  const [activeSession, setActiveSession] = useState(null)
  const [attendees, setAttendees] = useState([])
  const [showInput, setShowInput] = useState(false)
  const [showEndSession, setShowEndSession] = useState(false)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [feedback, setFeedback] = useState(null)

  // Aktive Session und Anwesende laden
  const loadData = useCallback(async () => {
    try {
      const response = await axios.get('/api/sessions/active')
      if (response.data.active) {
        setActiveSession(response.data.session)
        // Anwesende laden
        const attendeesRes = await axios.get(`/api/attendance/current/${response.data.session.id}`)
        setAttendees(attendeesRes.data)
      } else {
        setActiveSession(null)
        setAttendees([])
      }
    } catch (err) {
      console.error('Fehler beim Laden der Daten:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
    // Alle 30 Sekunden aktualisieren
    const interval = setInterval(loadData, 30000)
    return () => clearInterval(interval)
  }, [loadData])

  const showFeedback = (type, message) => {
    setFeedback({ type, message })
    setTimeout(() => setFeedback(null), 3000)
  }

  const handleSessionCreated = (session) => {
    setActiveSession(session)
    showFeedback('success', `${session.event_type_display} gestartet!`)
  }

  const handleCheckInOut = async (stammrollennummer) => {
    setActionLoading(true)
    try {
      const response = await axios.post('/api/attendance/toggle', {
        session_id: activeSession.id,
        stammrollennummer
      })
      
      showFeedback('success', response.data.message)
      setShowInput(false)
      loadData()
    } catch (err) {
      showFeedback('error', err.response?.data?.detail || 'Fehler bei der Aktion')
    } finally {
      setActionLoading(false)
    }
  }

  const handleEndSession = async (stammrollennummer) => {
    setActionLoading(true)
    try {
      await axios.post(`/api/sessions/${activeSession.id}/end`, {
        stammrollennummer: stammrollennummer || null
      })
      
      showFeedback('success', 'Session erfolgreich beendet!')
      setShowEndSession(false)
      setActiveSession(null)
      setAttendees([])
    } catch (err) {
      showFeedback('error', err.response?.data?.detail || 'Fehler beim Beenden der Session')
    } finally {
      setActionLoading(false)
    }
  }

  // Loading State
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-feuerwehr-red border-t-transparent mx-auto"></div>
          <p className="mt-4 text-gray-600 text-lg">Lade Daten...</p>
        </div>
      </div>
    )
  }

  // Keine aktive Session - Session Type Selector anzeigen
  if (!activeSession) {
    return <SessionTypeSelector onSessionCreated={handleSessionCreated} />
  }

  // Stammrollennummer Eingabe für Check-in/Check-out
  if (showInput) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <StammrollenInput
            onSubmit={handleCheckInOut}
            onCancel={() => setShowInput(false)}
            loading={actionLoading}
          />
        </div>
      </div>
    )
  }

  // Stammrollennummer Eingabe für Session beenden (nur bei Einsatz)
  if (showEndSession && activeSession.event_type === 'einsatz') {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-4">
            <h2 className="text-xl font-bold text-red-600">Einsatz beenden</h2>
            <p className="text-gray-600">Stammrollennummer des Berechtigten eingeben</p>
            <p className="text-sm text-gray-500">(mindestens UBM erforderlich)</p>
          </div>
          <StammrollenInput
            onSubmit={handleEndSession}
            onCancel={() => setShowEndSession(false)}
            loading={actionLoading}
          />
        </div>
      </div>
    )
  }

  // Hauptansicht mit aktiver Session
  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* Feedback Banner */}
      {feedback && (
        <div className={`fixed top-0 left-0 right-0 z-50 p-4 text-center text-white text-lg font-semibold
                        ${feedback.type === 'success' ? 'bg-green-500 animate-success' : 'bg-red-500 animate-error'}`}>
          {feedback.message}
        </div>
      )}

      {/* Header */}
      <header className="bg-feuerwehr-red text-white py-4 px-6 shadow-lg">
        <div className="flex justify-between items-center max-w-4xl mx-auto">
          <div>
            <h1 className="text-2xl font-bold">🚒 Feuerwehr Anwesenheit</h1>
            <p className="text-red-100">{activeSession.event_type_display}</p>
          </div>
          <div className="text-right">
            <div className="text-sm text-red-100">Gestartet</div>
            <div className="font-mono">
              {new Date(activeSession.start_time).toLocaleTimeString('de-DE', {
                hour: '2-digit',
                minute: '2-digit'
              })}
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 p-4 max-w-4xl mx-auto w-full">
        <div className="grid gap-4 lg:grid-cols-2">
          {/* Aktionen */}
          <div className="card">
            <h2 className="text-xl font-bold text-gray-800 mb-4">Aktionen</h2>
            
            <button
              onClick={() => setShowInput(true)}
              className="btn-success w-full mb-4 py-8 text-xl"
            >
              📝 Ein-/Auschecken
            </button>

            <button
              onClick={() => {
                if (activeSession.event_type === 'einsatz') {
                  setShowEndSession(true)
                } else {
                  handleEndSession(null)
                }
              }}
              className="btn-danger w-full py-6"
            >
              🛑 {activeSession.event_type === 'einsatz' ? 'Einsatz beenden' : 'Session beenden'}
            </button>

            {activeSession.event_type !== 'einsatz' && (
              <p className="text-xs text-gray-500 mt-2 text-center">
                Alle anwesenden Personen werden automatisch ausgecheckt
              </p>
            )}
          </div>

          {/* Anwesende */}
          <CurrentAttendees 
            attendees={attendees} 
            sessionInfo={activeSession}
          />
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-200 py-2 text-center text-sm text-gray-500">
        <a href="/admin" className="hover:text-feuerwehr-red">
          Admin-Bereich
        </a>
      </footer>
    </div>
  )
}

export default CheckInMain
