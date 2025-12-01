import { useState, useEffect } from 'react'
import { NavLink } from 'react-router-dom'
import axios from 'axios'

function BackupSettings() {
  const [settings, setSettings] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [pathValidation, setPathValidation] = useState({ valid: null, message: '' })
  const [validating, setValidating] = useState(false)
  const [creatingBackup, setCreatingBackup] = useState(false)

  const [formData, setFormData] = useState({
    backup_enabled: true,
    backup_path: './backups/',
    backup_schedule_time: '03:00',
    backup_retention_days: 30
  })

  const token = localStorage.getItem('token')
  const authHeader = { headers: { Authorization: `Bearer ${token}` } }

  const loadSettings = async () => {
    try {
      const response = await axios.get('/api/backup/settings', authHeader)
      setSettings(response.data)
      setFormData({
        backup_enabled: response.data.backup_enabled,
        backup_path: response.data.backup_path,
        backup_schedule_time: response.data.backup_schedule_time,
        backup_retention_days: response.data.backup_retention_days
      })
    } catch (err) {
      setError('Fehler beim Laden der Backup-Einstellungen')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSettings()
  }, [])

  const handleValidatePath = async () => {
    setValidating(true)
    setPathValidation({ valid: null, message: '' })
    
    try {
      const response = await axios.post('/api/backup/validate-path', {
        path: formData.backup_path
      }, authHeader)
      
      setPathValidation({
        valid: response.data.valid,
        message: response.data.message || (response.data.valid ? 'Pfad ist gültig' : 'Pfad ist ungültig')
      })
    } catch (err) {
      setPathValidation({
        valid: false,
        message: err.response?.data?.detail || 'Fehler bei der Pfad-Validierung'
      })
    } finally {
      setValidating(false)
    }
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    setSuccess(null)

    try {
      const response = await axios.put('/api/backup/settings', formData, authHeader)
      setSettings(response.data)
      setSuccess('Einstellungen erfolgreich gespeichert')
      setPathValidation({ valid: null, message: '' })
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Speichern')
    } finally {
      setSaving(false)
    }
  }

  const handleCreateBackup = async () => {
    setCreatingBackup(true)
    setError(null)
    setSuccess(null)

    try {
      const response = await axios.post('/api/backup/create', {}, authHeader)
      setSuccess(response.data.message)
      loadSettings() // Aktualisiere Last-Backup-Info
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Erstellen des Backups')
    } finally {
      setCreatingBackup(false)
    }
  }

  const formatBytes = (bytes) => {
    if (!bytes) return '-'
    const mb = bytes / (1024 * 1024)
    return `${mb.toFixed(2)} MB`
  }

  const formatDateTime = (isoString) => {
    if (!isoString) return '-'
    const date = new Date(isoString)
    return date.toLocaleString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading) {
    return <div className="text-center py-8">Lade Backup-Einstellungen...</div>
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Backup-Einstellungen</h2>
        <NavLink
          to="/admin/backup/list"
          className="btn-secondary"
        >
          📁 Alle Backups anzeigen
        </NavLink>
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

      {/* Status-Karte */}
      <div className="card mb-6">
        <h3 className="text-lg font-semibold mb-4">Backup-Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="text-sm text-gray-500">Letztes Backup</div>
            <div className="text-lg font-semibold">
              {formatDateTime(settings?.last_backup_time)}
            </div>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="text-sm text-gray-500">Größe des letzten Backups</div>
            <div className="text-lg font-semibold">
              {formatBytes(settings?.last_backup_size)}
            </div>
          </div>
        </div>
        <div className="mt-4">
          <button
            onClick={handleCreateBackup}
            disabled={creatingBackup}
            className="btn-primary"
          >
            {creatingBackup ? '⏳ Erstelle Backup...' : '💾 Jetzt Backup erstellen'}
          </button>
        </div>
      </div>

      {/* Einstellungs-Formular */}
      <form onSubmit={handleSave} className="card">
        <h3 className="text-lg font-semibold mb-4">Konfiguration</h3>

        {/* Backup aktivieren */}
        <div className="mb-6">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={formData.backup_enabled}
              onChange={(e) => setFormData({ ...formData, backup_enabled: e.target.checked })}
              className="w-5 h-5 rounded border-gray-300"
            />
            <div>
              <span className="font-medium text-gray-700">Automatisches Backup aktivieren</span>
              <p className="text-sm text-gray-500">Backup läuft täglich zur ausgewählten Zeit</p>
            </div>
          </label>
        </div>

        {/* Backup-Pfad */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Backup-Speicherort
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={formData.backup_path}
              onChange={(e) => {
                setFormData({ ...formData, backup_path: e.target.value })
                setPathValidation({ valid: null, message: '' })
              }}
              placeholder="./backups/ oder C:\Feuerwehr-Backups"
              className="input-touch flex-1"
            />
            <button
              type="button"
              onClick={handleValidatePath}
              disabled={validating}
              className="btn-secondary whitespace-nowrap"
            >
              {validating ? '⏳' : '🔍'} Pfad testen
            </button>
          </div>
          
          {/* Validierungs-Ergebnis */}
          {pathValidation.valid !== null && (
            <div className={`mt-2 text-sm ${pathValidation.valid ? 'text-green-600' : 'text-red-600'}`}>
              {pathValidation.valid ? '✅' : '❌'} {pathValidation.message}
            </div>
          )}
          
          {/* Hilfetext */}
          <div className="mt-2 text-sm text-gray-500">
            <p>Absolute oder relative Pfade möglich. Netzwerk-Pfade werden unterstützt.</p>
            <details className="mt-1">
              <summary className="cursor-pointer text-blue-600 hover:underline">Beispiele anzeigen</summary>
              <ul className="mt-2 space-y-1 pl-4">
                <li><code className="bg-gray-100 px-1 rounded">./backups</code> - Relativ zum Anwendungsverzeichnis</li>
                <li><code className="bg-gray-100 px-1 rounded">../data/backups</code> - Relativ übergeordnetes Verzeichnis</li>
                <li><code className="bg-gray-100 px-1 rounded">C:\Backups\Feuerwehr</code> - Windows absoluter Pfad</li>
                <li><code className="bg-gray-100 px-1 rounded">/home/pi/backups</code> - Linux/Raspberry Pi</li>
                <li><code className="bg-gray-100 px-1 rounded">/mnt/nas/feuerwehr</code> - Gemountetes Netzlaufwerk</li>
                <li><code className="bg-gray-100 px-1 rounded">\\192.168.1.100\backups</code> - Windows Netzwerk-Pfad</li>
              </ul>
            </details>
          </div>
        </div>

        {/* Backup-Zeit */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Backup-Zeit (täglich)
          </label>
          <input
            type="time"
            value={formData.backup_schedule_time}
            onChange={(e) => setFormData({ ...formData, backup_schedule_time: e.target.value })}
            className="input-touch w-auto"
          />
          <p className="text-sm text-gray-500 mt-1">
            Automatisches Backup läuft täglich zu dieser Uhrzeit
          </p>
        </div>

        {/* Aufbewahrungszeit */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Backups aufbewahren für (Tage)
          </label>
          <div className="flex items-center gap-4">
            <input
              type="range"
              min="7"
              max="90"
              value={formData.backup_retention_days}
              onChange={(e) => setFormData({ ...formData, backup_retention_days: parseInt(e.target.value) })}
              className="flex-1"
            />
            <input
              type="number"
              min="7"
              max="90"
              value={formData.backup_retention_days}
              onChange={(e) => setFormData({ ...formData, backup_retention_days: parseInt(e.target.value) || 30 })}
              className="input-touch w-20 text-center"
            />
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Ältere Backups werden automatisch gelöscht (7-90 Tage)
          </p>
        </div>

        {/* Speichern-Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="btn-primary"
          >
            {saving ? '⏳ Speichere...' : '💾 Einstellungen speichern'}
          </button>
        </div>
      </form>
    </div>
  )
}

export default BackupSettings
