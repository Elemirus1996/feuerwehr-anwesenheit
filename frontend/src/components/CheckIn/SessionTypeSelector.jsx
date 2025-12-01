import { useState } from 'react'
import axios from 'axios'

const EVENT_TYPES = [
  { value: 'einsatz', label: 'Einsatz', icon: '🚒', color: 'bg-red-600 hover:bg-red-700' },
  { value: 'uebungsdienst', label: 'Übungsdienst', icon: '📋', color: 'bg-blue-600 hover:bg-blue-700' },
  { value: 'arbeitsdienst_a', label: 'Arbeitsdienst Tour A', icon: '🔧', color: 'bg-green-600 hover:bg-green-700' },
  { value: 'arbeitsdienst_b', label: 'Arbeitsdienst Tour B', icon: '🔧', color: 'bg-green-600 hover:bg-green-700' },
  { value: 'arbeitsdienst_c', label: 'Arbeitsdienst Tour C', icon: '🔧', color: 'bg-green-600 hover:bg-green-700' },
]

function SessionTypeSelector({ onSessionCreated }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSelectType = async (eventType) => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await axios.post('/api/sessions/', { event_type: eventType })
      onSessionCreated(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Erstellen der Session')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-feuerwehr-red mb-2">
            🚒 Feuerwehr Anwesenheit
          </h1>
          <p className="text-gray-600 text-lg">
            Bitte wählen Sie den Veranstaltungstyp
          </p>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-6 text-center">
            {error}
          </div>
        )}

        <div className="space-y-4">
          {EVENT_TYPES.map((type) => (
            <button
              key={type.value}
              onClick={() => handleSelectType(type.value)}
              disabled={loading}
              className={`w-full ${type.color} text-white text-xl font-semibold 
                         py-6 px-8 rounded-xl shadow-lg transition-all duration-200 
                         active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed
                         flex items-center justify-center gap-4`}
            >
              <span className="text-3xl">{type.icon}</span>
              <span>{type.label}</span>
            </button>
          ))}
        </div>

        {loading && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-8 shadow-2xl">
              <div className="animate-spin rounded-full h-12 w-12 border-4 border-feuerwehr-red border-t-transparent mx-auto"></div>
              <p className="mt-4 text-gray-600">Session wird erstellt...</p>
            </div>
          </div>
        )}

        <div className="mt-8 text-center text-gray-500 text-sm">
          <p>Übungs- und Arbeitsdienste enden automatisch nach 3 Stunden.</p>
          <p>Einsätze müssen manuell durch UBM oder höher beendet werden.</p>
        </div>
      </div>
    </div>
  )
}

export default SessionTypeSelector
