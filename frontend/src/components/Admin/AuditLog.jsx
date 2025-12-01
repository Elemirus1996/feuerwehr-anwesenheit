/**
 * AuditLog - Feature 9: Security
 * Admin component for viewing audit logs
 */

import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'

function AuditLog() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [totalLogs, setTotalLogs] = useState(0)
  const [page, setPage] = useState(1)
  const [selectedLog, setSelectedLog] = useState(null)
  const [filters, setFilters] = useState({
    action: '',
    entity_type: '',
    start_date: '',
    end_date: ''
  })

  const token = localStorage.getItem('token')
  const authHeader = { headers: { Authorization: `Bearer ${token}` } }

  const actionIcons = {
    create: '🔨',
    update: '✏️',
    delete: '🗑️',
    login: '🔐',
    logout: '🚪'
  }

  const actionColors = {
    create: 'text-green-600 bg-green-100',
    update: 'text-blue-600 bg-blue-100',
    delete: 'text-red-600 bg-red-100',
    login: 'text-purple-600 bg-purple-100',
    logout: 'text-gray-600 bg-gray-100'
  }

  const loadLogs = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ page, per_page: 20 })
      if (filters.action) params.append('action', filters.action)
      if (filters.entity_type) params.append('entity_type', filters.entity_type)
      if (filters.start_date) params.append('start_date', filters.start_date)
      if (filters.end_date) params.append('end_date', filters.end_date)

      const response = await axios.get(`/api/audit?${params}`, authHeader)
      setLogs(response.data.logs)
      setTotalLogs(response.data.total)
    } catch (err) {
      setError('Fehler beim Laden der Audit-Logs')
    } finally {
      setLoading(false)
    }
  }, [page, filters])

  useEffect(() => {
    loadLogs()
  }, [loadLogs])

  const handleExport = async () => {
    try {
      const params = new URLSearchParams()
      if (filters.start_date) params.append('start_date', filters.start_date)
      if (filters.end_date) params.append('end_date', filters.end_date)

      const response = await axios.get(`/api/audit/export?${params}`, {
        ...authHeader,
        responseType: 'blob'
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `audit_log_${new Date().toISOString().split('T')[0]}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err) {
      setError('Fehler beim Export')
    }
  }

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const totalPages = Math.ceil(totalLogs / 20)

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">📋 Audit-Log</h2>
        <button onClick={handleExport} className="btn-secondary">
          📥 CSV Export
        </button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="card mb-6">
        <h3 className="text-sm font-semibold text-gray-600 mb-3">Filter</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm text-gray-600 mb-1">Aktion</label>
            <select
              value={filters.action}
              onChange={(e) => {
                setFilters({ ...filters, action: e.target.value })
                setPage(1)
              }}
              className="input-touch text-sm py-2"
            >
              <option value="">Alle</option>
              <option value="create">Erstellen</option>
              <option value="update">Aktualisieren</option>
              <option value="delete">Löschen</option>
              <option value="login">Anmelden</option>
              <option value="logout">Abmelden</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">Entity-Typ</label>
            <select
              value={filters.entity_type}
              onChange={(e) => {
                setFilters({ ...filters, entity_type: e.target.value })
                setPage(1)
              }}
              className="input-touch text-sm py-2"
            >
              <option value="">Alle</option>
              <option value="personnel">Personal</option>
              <option value="session">Session</option>
              <option value="announcement">Ankündigung</option>
              <option value="group">Gruppe</option>
              <option value="training">Schulung</option>
              <option value="user">Benutzer</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">Von</label>
            <input
              type="date"
              value={filters.start_date}
              onChange={(e) => {
                setFilters({ ...filters, start_date: e.target.value })
                setPage(1)
              }}
              className="input-touch text-sm py-2"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">Bis</label>
            <input
              type="date"
              value={filters.end_date}
              onChange={(e) => {
                setFilters({ ...filters, end_date: e.target.value })
                setPage(1)
              }}
              className="input-touch text-sm py-2"
            />
          </div>
        </div>
      </div>

      {/* Logs Table */}
      <div className="card overflow-x-auto">
        {loading ? (
          <div className="text-center py-8">Lade Audit-Logs...</div>
        ) : (
          <>
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-semibold text-gray-600">Zeit</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-600">Benutzer</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-600">Aktion</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-600">Entity</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-600">Details</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr
                    key={log.id}
                    className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
                    onClick={() => setSelectedLog(log)}
                  >
                    <td className="py-3 px-4 text-sm text-gray-600">
                      {formatTimestamp(log.timestamp)}
                    </td>
                    <td className="py-3 px-4">
                      {log.user_name || `User #${log.user_id}` || 'System'}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-sm ${actionColors[log.action]}`}>
                        {actionIcons[log.action]} {log.action}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-gray-700">{log.entity_type}</span>
                      {log.entity_id && (
                        <span className="text-gray-400 ml-1">#{log.entity_id}</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-500">
                      {log.changes ? (
                        <span className="text-blue-600 hover:underline">
                          Änderungen anzeigen →
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {logs.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                Keine Audit-Logs gefunden
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex justify-between items-center mt-4 pt-4 border-t">
                <span className="text-sm text-gray-500">
                  {totalLogs} Einträge gesamt
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-3 py-1 rounded border disabled:opacity-50 hover:bg-gray-100"
                  >
                    ◀ Zurück
                  </button>
                  <span className="px-3 py-1">
                    Seite {page} von {totalPages}
                  </span>
                  <button
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="px-3 py-1 rounded border disabled:opacity-50 hover:bg-gray-100"
                  >
                    Weiter ▶
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Detail Modal */}
      {selectedLog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold">Audit-Log Details</h3>
                <button
                  onClick={() => setSelectedLog(null)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Zeitstempel:</span>
                    <div className="font-medium">{formatTimestamp(selectedLog.timestamp)}</div>
                  </div>
                  <div>
                    <span className="text-gray-500">Benutzer:</span>
                    <div className="font-medium">{selectedLog.user_name || `User #${selectedLog.user_id}` || 'System'}</div>
                  </div>
                  <div>
                    <span className="text-gray-500">Aktion:</span>
                    <div className={`inline-flex items-center gap-1 px-2 py-1 rounded text-sm ${actionColors[selectedLog.action]}`}>
                      {actionIcons[selectedLog.action]} {selectedLog.action}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-500">Entity:</span>
                    <div className="font-medium">
                      {selectedLog.entity_type}
                      {selectedLog.entity_id && ` #${selectedLog.entity_id}`}
                    </div>
                  </div>
                  {selectedLog.ip_address && (
                    <div>
                      <span className="text-gray-500">IP-Adresse:</span>
                      <div className="font-mono text-sm">{selectedLog.ip_address}</div>
                    </div>
                  )}
                </div>

                {selectedLog.changes && (
                  <div>
                    <span className="text-gray-500 text-sm">Änderungen:</span>
                    <div className="mt-2 bg-gray-50 rounded-lg p-4">
                      {selectedLog.changes.old && (
                        <div className="mb-3">
                          <div className="text-sm font-medium text-red-600 mb-1">Vorher:</div>
                          <pre className="text-xs bg-red-50 p-2 rounded overflow-x-auto">
                            {JSON.stringify(selectedLog.changes.old, null, 2)}
                          </pre>
                        </div>
                      )}
                      {selectedLog.changes.new && (
                        <div>
                          <div className="text-sm font-medium text-green-600 mb-1">Nachher:</div>
                          <pre className="text-xs bg-green-50 p-2 rounded overflow-x-auto">
                            {JSON.stringify(selectedLog.changes.new, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {selectedLog.user_agent && (
                  <div>
                    <span className="text-gray-500 text-sm">User-Agent:</span>
                    <div className="text-xs font-mono bg-gray-50 p-2 rounded mt-1 break-all">
                      {selectedLog.user_agent}
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setSelectedLog(null)}
                  className="btn-secondary"
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

export default AuditLog
