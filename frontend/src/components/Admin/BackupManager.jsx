import { useState, useEffect } from 'react'
import axios from 'axios'

function BackupManager() {
  const [backups, setBackups] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [actionLoading, setActionLoading] = useState(null)
  const [restoreConfirm, setRestoreConfirm] = useState(null)
  const [deleteConfirm, setDeleteConfirm] = useState(null)
  const [totalCount, setTotalCount] = useState(0)
  const [totalSizeMb, setTotalSizeMb] = useState(0)

  const token = localStorage.getItem('token')
  const authHeader = { headers: { Authorization: `Bearer ${token}` } }

  const loadBackups = async () => {
    try {
      const response = await axios.get('/api/backup/list', authHeader)
      setBackups(response.data.backups)
      setTotalCount(response.data.total_count)
      setTotalSizeMb(response.data.total_size_mb)
    } catch (err) {
      setError('Fehler beim Laden der Backups')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadBackups()
  }, [])

  const formatDateTime = (isoString) => {
    const date = new Date(isoString)
    return date.toLocaleString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const handleDownload = async (filename) => {
    setActionLoading(filename)
    try {
      const response = await axios.get(`/api/backup/download/${filename}`, {
        ...authHeader,
        responseType: 'blob'
      })
      
      // Erstelle Download-Link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setError('Fehler beim Herunterladen des Backups')
    } finally {
      setActionLoading(null)
    }
  }

  const handleRestore = async (filename) => {
    setActionLoading(filename)
    setError(null)
    setSuccess(null)
    
    try {
      const response = await axios.post(`/api/backup/restore/${filename}`, {}, authHeader)
      setSuccess(response.data.message)
      setRestoreConfirm(null)
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler bei der Wiederherstellung')
    } finally {
      setActionLoading(null)
    }
  }

  const handleDelete = async (filename) => {
    setActionLoading(filename)
    setError(null)
    setSuccess(null)
    
    try {
      await axios.delete(`/api/backup/${filename}`, authHeader)
      setSuccess(`Backup ${filename} erfolgreich gelöscht`)
      setDeleteConfirm(null)
      loadBackups()
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Löschen')
    } finally {
      setActionLoading(null)
    }
  }

  const handleCleanup = async () => {
    setActionLoading('cleanup')
    setError(null)
    setSuccess(null)
    
    try {
      const response = await axios.post('/api/backup/cleanup', {}, authHeader)
      setSuccess(response.data.message)
      loadBackups()
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Aufräumen')
    } finally {
      setActionLoading(null)
    }
  }

  if (loading) {
    return <div className="text-center py-8">Lade Backups...</div>
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Backup-Verwaltung</h2>
        <button
          onClick={handleCleanup}
          disabled={actionLoading === 'cleanup'}
          className="btn-secondary"
        >
          {actionLoading === 'cleanup' ? '⏳ Räume auf...' : '🧹 Alte Backups aufräumen'}
        </button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg mb-4">
          {success}
        </div>
      )}

      {/* Statistik */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="card bg-blue-50">
          <div className="text-blue-600 text-sm font-medium">Anzahl Backups</div>
          <div className="text-3xl font-bold text-blue-800">{totalCount}</div>
        </div>
        <div className="card bg-green-50">
          <div className="text-green-600 text-sm font-medium">Gesamtgröße</div>
          <div className="text-3xl font-bold text-green-800">{totalSizeMb} MB</div>
        </div>
      </div>

      {/* Restore-Bestätigung Modal */}
      {restoreConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md mx-4">
            <h3 className="text-lg font-bold text-red-600 mb-4">⚠️ Backup wiederherstellen</h3>
            <p className="text-gray-600 mb-2">
              <strong>ACHTUNG:</strong> Alle aktuellen Daten werden überschrieben!
            </p>
            <p className="text-gray-600 mb-4">
              Ein automatisches Sicherungs-Backup wird vor der Wiederherstellung erstellt.
            </p>
            <p className="text-gray-800 mb-6">
              Möchten Sie das Backup <strong>{restoreConfirm}</strong> wirklich wiederherstellen?
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setRestoreConfirm(null)}
                className="btn-secondary flex-1"
              >
                Abbrechen
              </button>
              <button
                onClick={() => handleRestore(restoreConfirm)}
                disabled={actionLoading === restoreConfirm}
                className="btn-primary flex-1 bg-red-600 hover:bg-red-700"
              >
                {actionLoading === restoreConfirm ? '⏳ Stelle wieder her...' : '✓ Wiederherstellen'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete-Bestätigung Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md mx-4">
            <h3 className="text-lg font-bold text-red-600 mb-4">🗑️ Backup löschen</h3>
            <p className="text-gray-600 mb-6">
              Möchten Sie das Backup <strong>{deleteConfirm}</strong> wirklich löschen?
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="btn-secondary flex-1"
              >
                Abbrechen
              </button>
              <button
                onClick={() => handleDelete(deleteConfirm)}
                disabled={actionLoading === deleteConfirm}
                className="btn-primary flex-1 bg-red-600 hover:bg-red-700"
              >
                {actionLoading === deleteConfirm ? '⏳ Lösche...' : '✓ Löschen'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Backup-Liste */}
      <div className="card overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-4 font-semibold text-gray-600">Dateiname</th>
              <th className="text-left py-3 px-4 font-semibold text-gray-600">Erstellt</th>
              <th className="text-left py-3 px-4 font-semibold text-gray-600">Größe</th>
              <th className="text-right py-3 px-4 font-semibold text-gray-600">Aktionen</th>
            </tr>
          </thead>
          <tbody>
            {backups.map((backup) => (
              <tr key={backup.filename} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-3 px-4">
                  <span className="font-mono text-sm">{backup.filename}</span>
                </td>
                <td className="py-3 px-4">
                  {formatDateTime(backup.created)}
                </td>
                <td className="py-3 px-4">
                  {backup.size_mb} MB
                </td>
                <td className="py-3 px-4 text-right">
                  <div className="flex gap-2 justify-end">
                    <button
                      onClick={() => handleDownload(backup.filename)}
                      disabled={actionLoading === backup.filename}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                      title="Herunterladen"
                    >
                      {actionLoading === backup.filename ? '⏳' : '⬇️'} Download
                    </button>
                    <button
                      onClick={() => setRestoreConfirm(backup.filename)}
                      disabled={actionLoading === backup.filename}
                      className="text-green-600 hover:text-green-800 text-sm"
                      title="Wiederherstellen"
                    >
                      🔄 Restore
                    </button>
                    <button
                      onClick={() => setDeleteConfirm(backup.filename)}
                      disabled={actionLoading === backup.filename}
                      className="text-red-600 hover:text-red-800 text-sm"
                      title="Löschen"
                    >
                      🗑️ Löschen
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {backups.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            Keine Backups vorhanden
          </div>
        )}
      </div>
    </div>
  )
}

export default BackupManager
