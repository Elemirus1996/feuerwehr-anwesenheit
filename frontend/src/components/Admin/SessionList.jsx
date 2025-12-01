import { useState, useEffect } from 'react'
import axios from 'axios'

function SessionList() {
  const [sessions, setSessions] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedSession, setSelectedSession] = useState(null)
  const [filters, setFilters] = useState({
    status: '',
    event_type: '',
    start_date: '',
    end_date: ''
  })
  const [exportLoading, setExportLoading] = useState(false)

  const token = localStorage.getItem('token')
  const authHeader = { headers: { Authorization: `Bearer ${token}` } }

  const loadSessions = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filters.status) params.append('status_filter', filters.status)
      if (filters.event_type) params.append('event_type', filters.event_type)
      if (filters.start_date) params.append('start_date', filters.start_date)
      if (filters.end_date) params.append('end_date', filters.end_date)
      
      const response = await axios.get(`/api/sessions/?${params.toString()}`, authHeader)
      setSessions(response.data.sessions)
      setTotal(response.data.total)
    } catch (err) {
      setError('Fehler beim Laden der Sessions')
    } finally {
      setLoading(false)
    }
  }

  const loadSessionDetail = async (sessionId) => {
    try {
      const response = await axios.get(`/api/sessions/${sessionId}`, authHeader)
      setSelectedSession(response.data)
    } catch (err) {
      setError('Fehler beim Laden der Session-Details')
    }
  }

  useEffect(() => {
    loadSessions()
  }, [filters])

  const formatDateTime = (isoString) => {
    if (!isoString) return '-'
    return new Date(isoString).toLocaleString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatDuration = (start, end) => {
    if (!start) return '-'
    const startDate = new Date(start)
    const endDate = end ? new Date(end) : new Date()
    const diff = Math.floor((endDate - startDate) / 60000) // Minuten
    const hours = Math.floor(diff / 60)
    const minutes = diff % 60
    return `${hours}h ${minutes}min`
  }

  const handleExportPDF = async (sessionId) => {
    setExportLoading(true)
    try {
      const response = await axios.get(`/api/export/session/${sessionId}/pdf`, {
        ...authHeader,
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `anwesenheit_session_${sessionId}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setError('Fehler beim Exportieren des PDFs')
    } finally {
      setExportLoading(false)
    }
  }

  const handleExportPeriod = async () => {
    if (!filters.start_date || !filters.end_date) {
      setError('Bitte Start- und Enddatum für den Export angeben')
      return
    }
    
    setExportLoading(true)
    try {
      const response = await axios.post('/api/export/period/pdf', {
        start_date: filters.start_date,
        end_date: filters.end_date,
        event_type: filters.event_type || null
      }, {
        ...authHeader,
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `anwesenheit_${filters.start_date}_${filters.end_date}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setError('Fehler beim Exportieren des Zeitraum-PDFs')
    } finally {
      setExportLoading(false)
    }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Anwesenheitslisten</h2>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-4">
          {error}
          <button onClick={() => setError(null)} className="float-right">×</button>
        </div>
      )}

      {/* Filter */}
      <div className="card mb-6">
        <h3 className="text-lg font-semibold mb-4">Filter</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="input-touch"
            >
              <option value="">Alle</option>
              <option value="active">Aktiv</option>
              <option value="completed">Abgeschlossen</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Event-Typ</label>
            <select
              value={filters.event_type}
              onChange={(e) => setFilters({ ...filters, event_type: e.target.value })}
              className="input-touch"
            >
              <option value="">Alle</option>
              <option value="einsatz">Einsatz</option>
              <option value="uebungsdienst">Übungsdienst</option>
              <option value="arbeitsdienst_a">Arbeitsdienst A</option>
              <option value="arbeitsdienst_b">Arbeitsdienst B</option>
              <option value="arbeitsdienst_c">Arbeitsdienst C</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Von</label>
            <input
              type="date"
              value={filters.start_date}
              onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
              className="input-touch"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Bis</label>
            <input
              type="date"
              value={filters.end_date}
              onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
              className="input-touch"
            />
          </div>
        </div>
        <div className="mt-4 flex gap-3">
          <button
            onClick={() => setFilters({ status: '', event_type: '', start_date: '', end_date: '' })}
            className="btn-secondary"
          >
            Filter zurücksetzen
          </button>
          <button
            onClick={handleExportPeriod}
            disabled={exportLoading || !filters.start_date || !filters.end_date}
            className="btn-primary"
          >
            {exportLoading ? 'Exportiere...' : 'Zeitraum als PDF exportieren'}
          </button>
        </div>
      </div>

      {/* Sessions-Liste */}
      <div className="card overflow-x-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Sessions ({total})</h3>
        </div>
        
        {loading ? (
          <div className="text-center py-8">Lade Sessions...</div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-semibold text-gray-600">Datum</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-600">Typ</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-600">Dauer</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-600">Teilnehmer</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-600">Status</th>
                <th className="text-right py-3 px-4 font-semibold text-gray-600">Aktionen</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((session) => (
                <tr key={session.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4">{formatDateTime(session.start_time)}</td>
                  <td className="py-3 px-4">{session.event_type_display}</td>
                  <td className="py-3 px-4">{formatDuration(session.start_time, session.end_time)}</td>
                  <td className="py-3 px-4">{session.attendee_count}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 rounded text-sm ${
                      session.status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {session.status === 'active' ? 'Aktiv' : 'Beendet'}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => loadSessionDetail(session.id)}
                      className="text-blue-600 hover:text-blue-800 mr-3"
                    >
                      Details
                    </button>
                    <button
                      onClick={() => handleExportPDF(session.id)}
                      className="text-green-600 hover:text-green-800"
                      disabled={exportLoading}
                    >
                      PDF
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {!loading && sessions.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            Keine Sessions gefunden
          </div>
        )}
      </div>

      {/* Session-Detail Modal */}
      {selectedSession && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-xl font-bold">{selectedSession.event_type_display}</h3>
                <button
                  onClick={() => setSelectedSession(null)}
                  className="text-gray-500 hover:text-gray-700 text-2xl"
                >
                  ×
                </button>
              </div>
              
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <span className="text-gray-500 text-sm">Start:</span>
                  <div className="font-semibold">{formatDateTime(selectedSession.start_time)}</div>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">Ende:</span>
                  <div className="font-semibold">{formatDateTime(selectedSession.end_time)}</div>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">Dauer:</span>
                  <div className="font-semibold">
                    {formatDuration(selectedSession.start_time, selectedSession.end_time)}
                  </div>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">Teilnehmer:</span>
                  <div className="font-semibold">{selectedSession.total_attendees}</div>
                </div>
              </div>

              <h4 className="font-semibold mb-3">Teilnehmerliste</h4>
              <div className="max-h-60 overflow-y-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2">Name</th>
                      <th className="text-left py-2">Dienstgrad</th>
                      <th className="text-left py-2">Check-in</th>
                      <th className="text-left py-2">Check-out</th>
                      <th className="text-left py-2">Dauer</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedSession.attendances?.map((att) => (
                      <tr key={att.id} className="border-b border-gray-100">
                        <td className="py-2">{att.vorname} {att.nachname}</td>
                        <td className="py-2">{att.dienstgrad}</td>
                        <td className="py-2">
                          {new Date(att.check_in_time).toLocaleTimeString('de-DE', {
                            hour: '2-digit', minute: '2-digit'
                          })}
                        </td>
                        <td className="py-2">
                          {att.check_out_time 
                            ? new Date(att.check_out_time).toLocaleTimeString('de-DE', {
                                hour: '2-digit', minute: '2-digit'
                              })
                            : '-'}
                        </td>
                        <td className="py-2">
                          {att.duration_minutes 
                            ? `${Math.floor(att.duration_minutes / 60)}h ${att.duration_minutes % 60}min`
                            : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-6 flex gap-3">
                <button
                  onClick={() => handleExportPDF(selectedSession.id)}
                  className="btn-primary flex-1"
                  disabled={exportLoading}
                >
                  Als PDF exportieren
                </button>
                <button
                  onClick={() => setSelectedSession(null)}
                  className="btn-secondary flex-1"
                >
                  Schließen
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SessionList
