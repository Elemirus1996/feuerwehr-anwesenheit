/**
 * BackupManagement - Feature 9: Security
 * Admin component for managing database backups
 */

import { useState, useEffect } from 'react'
import axios from 'axios'

function BackupManagement() {
  const [backups, setBackups] = useState([])
  const [status, setStatus] = useState(null)
  const [settings, setSettings] = useState(null)
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [restoring, setRestoring] = useState(null)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [showSettings, setShowSettings] = useState(false)

  const token = localStorage.getItem('token')
  const authHeader = { headers: { Authorization: `Bearer ${token}` } }

  const loadBackups = async () => {
    try {
      const response = await axios.get('/api/backup/list', authHeader)
      setBackups(response.data)
    } catch (err) {
      setError('Fehler beim Laden der Backups')
    }
  }

  const loadStatus = async () => {
    try {
      const response = await axios.get('/api/backup/status', authHeader)
      setStatus(response.data)
    } catch (err) {
      console.log('Fehler beim Laden des Status:', err)
    }
  }

  const loadSettings = async () => {
    try {
      const response = await axios.get('/api/backup/settings', authHeader)
      setSettings(response.data)
    } catch (err) {
      console.log('Fehler beim Laden der Einstellungen:', err)
    }
  }

  useEffect(() => {
    Promise.all([loadBackups(), loadStatus(), loadSettings()])
      .finally(() => setLoading(false))
  }, [])

  const handleCreateBackup = async () => {
    setCreating(true)
    setError(null)
    setSuccess(null)

    try {
      const response = await axios.post('/api/backup/create', {}, authHeader)
      setSuccess(`Backup erstellt: ${response.data.filename}`)
      loadBackups()
      loadStatus()
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Erstellen des Backups')
    } finally {
      setCreating(false)
    }
  }

  const handleDownload = async (filename) => {
    try {
      const response = await axios.get(`/api/backup/download/${filename}`, {
        ...authHeader,
        responseType: 'blob'
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err) {
      setError('Fehler beim Download')
    }
  }

  const handleRestore = async (filename) => {
    if (!confirm(`ACHTUNG: Beim Wiederherstellen gehen ALLE aktuellen Daten verloren!\n\nEs wird automatisch ein Sicherungs-Backup erstellt.\n\nBackup "${filename}" wirklich wiederherstellen?`)) {
      return
    }

    setRestoring(filename)
    setError(null)
    setSuccess(null)

    try {
      const response = await axios.post(`/api/backup/restore/${filename}`, {}, authHeader)
      setSuccess(`Backup wiederhergestellt! Sicherungs-Backup: ${response.data.pre_restore_backup}`)
      loadBackups()
      loadStatus()
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Wiederherstellen')
    } finally {
      setRestoring(null)
    }
  }

  const handleDelete = async (filename) => {
    if (!confirm(`Backup "${filename}" wirklich löschen?`)) {
      return
    }

    try {
      await axios.delete(`/api/backup/${filename}`, authHeader)
      setSuccess('Backup gelöscht')
      loadBackups()
      loadStatus()
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Löschen')
    }
  }

  const handleSaveSettings = async () => {
    try {
      await axios.put('/api/backup/settings', settings, authHeader)
      setSuccess('Einstellungen gespeichert')
      setShowSettings(false)
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Speichern')
    }
  }

  const handleCleanup = async () => {
    try {
      const response = await axios.post('/api/backup/cleanup', {}, authHeader)
      if (response.data.deleted_count > 0) {
        setSuccess(`${response.data.deleted_count} alte Backup(s) gelöscht`)
      } else {
        setSuccess('Keine alten Backups zum Löschen gefunden')
      }
      loadBackups()
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Aufräumen')
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const formatDate = (isoString) => {
    return new Date(isoString).toLocaleString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading) {
    return <div className="text-center py-8">Lade Backup-Informationen...</div>
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">💾 Backup-Verwaltung</h2>
        <div className="flex gap-2">
          <button onClick={() => setShowSettings(true)} className="btn-secondary">
            ⚙️ Einstellungen
          </button>
          <button
            onClick={handleCreateBackup}
            disabled={creating}
            className="btn-primary"
          >
            {creating ? '⏳ Erstelle...' : '📦 Backup jetzt erstellen'}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-4">
          {error}
          <button onClick={() => setError(null)} className="float-right">✕</button>
        </div>
      )}

      {success && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg mb-4">
          {success}
          <button onClick={() => setSuccess(null)} className="float-right">✕</button>
        </div>
      )}

      {/* Status Card */}
      {status && (
        <div className={`card mb-6 ${status.warning ? 'border-2 border-yellow-400' : ''}`}>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold mb-2">
                {status.warning ? '⚠️ Backup-Status' : '✅ Backup-Status'}
              </h3>
              <div className="text-sm text-gray-600 space-y-1">
                <div>Backups gesamt: <span className="font-semibold">{status.total_backups}</span></div>
                {status.last_backup ? (
                  <>
                    <div>Letztes Backup: <span className="font-semibold">{formatDate(status.last_backup.created_at)}</span></div>
                    <div>Alter: <span className={`font-semibold ${status.last_backup_age_hours > 24 ? 'text-yellow-600' : 'text-green-600'}`}>
                      {status.last_backup_age_hours} Stunden
                    </span></div>
                  </>
                ) : (
                  <div className="text-yellow-600 font-semibold">Noch kein Backup vorhanden!</div>
                )}
              </div>
            </div>
            {status.warning && (
              <div className="text-yellow-600 text-center">
                <div className="text-4xl mb-1">⚠️</div>
                <div className="text-sm">Backup empfohlen</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Backup List */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Verfügbare Backups</h3>
          <button onClick={handleCleanup} className="text-sm text-gray-600 hover:text-gray-800">
            🧹 Alte Backups aufräumen
          </button>
        </div>

        <div className="space-y-3">
          {backups.map((backup, index) => (
            <div
              key={backup.filename}
              className={`p-4 rounded-lg border ${
                index === 0 ? 'border-green-300 bg-green-50' : 'border-gray-200'
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium flex items-center gap-2">
                    {backup.filename}
                    {index === 0 && (
                      <span className="text-xs bg-green-200 text-green-800 px-2 py-0.5 rounded">
                        Neuestes
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-500">
                    {formatDate(backup.created_at)} • {formatFileSize(backup.size)}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleDownload(backup.filename)}
                    className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                  >
                    ⬇️ Download
                  </button>
                  <button
                    onClick={() => handleRestore(backup.filename)}
                    disabled={restoring === backup.filename}
                    className="px-3 py-1 text-sm bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200 disabled:opacity-50"
                  >
                    {restoring === backup.filename ? '⏳...' : '🔄 Wiederherstellen'}
                  </button>
                  <button
                    onClick={() => handleDelete(backup.filename)}
                    className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </div>
          ))}

          {backups.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              Keine Backups vorhanden. Erstellen Sie Ihr erstes Backup!
            </div>
          )}
        </div>
      </div>

      {/* Settings Modal */}
      {showSettings && settings && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold">⚙️ Backup-Einstellungen</h3>
                <button
                  onClick={() => setShowSettings(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="font-medium">Automatische Backups</label>
                    <p className="text-sm text-gray-500">Tägliches Backup um 03:00 Uhr</p>
                  </div>
                  <button
                    onClick={() => setSettings({ ...settings, enabled: !settings.enabled })}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      settings.enabled ? 'bg-green-500' : 'bg-gray-200'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                        settings.enabled ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Aufbewahrungsdauer (Tage)
                  </label>
                  <input
                    type="number"
                    value={settings.retention_days}
                    onChange={(e) => setSettings({ ...settings, retention_days: parseInt(e.target.value) })}
                    className="input-touch"
                    min="1"
                    max="365"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Backups älter als {settings.retention_days} Tage werden automatisch gelöscht
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Mindestanzahl behalten
                  </label>
                  <input
                    type="number"
                    value={settings.keep_minimum}
                    onChange={(e) => setSettings({ ...settings, keep_minimum: parseInt(e.target.value) })}
                    className="input-touch"
                    min="1"
                    max="100"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Mindestens {settings.keep_minimum} Backup(s) werden immer behalten
                  </p>
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowSettings(false)}
                  className="btn-secondary flex-1"
                >
                  Abbrechen
                </button>
                <button
                  onClick={handleSaveSettings}
                  className="btn-primary flex-1"
                >
                  Speichern
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default BackupManagement
