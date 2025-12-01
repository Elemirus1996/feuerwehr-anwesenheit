/**
 * RoleManagement - Feature 9: Security
 * Admin component for managing roles and permissions
 */

import { useState, useEffect } from 'react'
import axios from 'axios'

function RoleManagement() {
  const [roles, setRoles] = useState([])
  const [allPermissions, setAllPermissions] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [selectedRole, setSelectedRole] = useState(null)
  const [editingPermissions, setEditingPermissions] = useState([])

  const token = localStorage.getItem('token')
  const authHeader = { headers: { Authorization: `Bearer ${token}` } }

  const roleLabels = {
    admin: 'Administrator',
    wehrfuehrer: 'Wehrführer',
    gruppenfuehrer: 'Gruppenführer',
    mitglied: 'Mitglied'
  }

  const roleDescriptions = {
    admin: 'Volle Kontrolle über alle Bereiche der Anwendung',
    wehrfuehrer: 'Alle Funktionen außer System-Einstellungen',
    gruppenfuehrer: 'Personal einsehen/bearbeiten, Sessions beenden, Berichte',
    mitglied: 'Nur eigene Daten sehen, Check-in/out'
  }

  const roleColors = {
    admin: 'bg-red-100 text-red-800 border-red-200',
    wehrfuehrer: 'bg-purple-100 text-purple-800 border-purple-200',
    gruppenfuehrer: 'bg-blue-100 text-blue-800 border-blue-200',
    mitglied: 'bg-gray-100 text-gray-800 border-gray-200'
  }

  const loadRoles = async () => {
    try {
      const response = await axios.get('/api/roles/', authHeader)
      setRoles(response.data)
    } catch (err) {
      setError('Fehler beim Laden der Rollen')
    }
  }

  const loadPermissions = async () => {
    try {
      const response = await axios.get('/api/roles/permissions', authHeader)
      setAllPermissions(response.data)
    } catch (err) {
      console.log('Fehler beim Laden der Berechtigungen:', err)
    }
  }

  useEffect(() => {
    Promise.all([loadRoles(), loadPermissions()])
      .finally(() => setLoading(false))
  }, [])

  const handleSelectRole = (role) => {
    setSelectedRole(role)
    setEditingPermissions([...role.permissions])
  }

  const handleTogglePermission = (permission) => {
    if (editingPermissions.includes(permission)) {
      setEditingPermissions(editingPermissions.filter(p => p !== permission))
    } else {
      setEditingPermissions([...editingPermissions, permission])
    }
  }

  const handleSavePermissions = async () => {
    if (!selectedRole) return

    setError(null)
    setSuccess(null)

    try {
      await axios.put(`/api/roles/${selectedRole.id}/permissions`, {
        permissions: editingPermissions
      }, authHeader)
      setSuccess('Berechtigungen gespeichert')
      loadRoles()
      setSelectedRole(null)
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Speichern')
    }
  }

  const getCategoryLabel = (category) => {
    const labels = {
      personnel: '👥 Personal',
      sessions: '📋 Sessions',
      reports: '📊 Berichte',
      settings: '⚙️ Einstellungen',
      announcements: '📢 Ankündigungen',
      groups: '🏷️ Gruppen',
      trainings: '📚 Schulungen',
      audit: '📋 Audit-Log',
      backup: '💾 Backups',
      roles: '🔑 Rollen'
    }
    return labels[category] || category
  }

  if (loading) {
    return <div className="text-center py-8">Lade Rollen...</div>
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">🔑 Rollen & Berechtigungen</h2>
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Roles List */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Standard-Rollen</h3>
          <div className="space-y-3">
            {roles.map((role) => (
              <div
                key={role.id}
                onClick={() => handleSelectRole(role)}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  selectedRole?.id === role.id
                    ? 'border-feuerwehr-red bg-red-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium border ${roleColors[role.name]}`}>
                      {roleLabels[role.name] || role.name}
                    </span>
                    <span className="text-sm text-gray-500">
                      {role.user_count} Benutzer
                    </span>
                  </div>
                </div>
                <p className="text-sm text-gray-600">
                  {roleDescriptions[role.name]}
                </p>
                <div className="mt-2 text-xs text-gray-500">
                  {role.permissions.length} Berechtigung{role.permissions.length !== 1 ? 'en' : ''}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Permissions Editor */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">
            {selectedRole
              ? `Berechtigungen: ${roleLabels[selectedRole.name] || selectedRole.name}`
              : 'Berechtigungen bearbeiten'}
          </h3>

          {!selectedRole ? (
            <div className="text-center py-8 text-gray-500">
              Wählen Sie eine Rolle aus, um die Berechtigungen zu bearbeiten
            </div>
          ) : (
            <div className="space-y-4">
              {Object.entries(allPermissions).map(([category, permissions]) => (
                <div key={category} className="border rounded-lg p-3">
                  <h4 className="font-medium text-sm mb-2 text-gray-700">
                    {getCategoryLabel(category)}
                  </h4>
                  <div className="space-y-2">
                    {permissions.map((perm) => (
                      <label
                        key={perm.key}
                        className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-1 rounded"
                      >
                        <input
                          type="checkbox"
                          checked={editingPermissions.includes(perm.key)}
                          onChange={() => handleTogglePermission(perm.key)}
                          className="w-4 h-4 rounded border-gray-300 text-feuerwehr-red focus:ring-feuerwehr-red"
                          disabled={selectedRole.name === 'admin'}
                        />
                        <span className="text-sm">{perm.label}</span>
                        <span className="text-xs text-gray-400 ml-auto">{perm.key}</span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}

              {selectedRole.name === 'admin' && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-sm text-yellow-700">
                  ⚠️ Die Admin-Rolle hat automatisch alle Berechtigungen und kann nicht eingeschränkt werden.
                </div>
              )}

              <div className="flex gap-3 pt-4 border-t">
                <button
                  onClick={() => {
                    setSelectedRole(null)
                    setEditingPermissions([])
                  }}
                  className="btn-secondary flex-1"
                >
                  Abbrechen
                </button>
                <button
                  onClick={handleSavePermissions}
                  disabled={selectedRole.name === 'admin'}
                  className="btn-primary flex-1 disabled:opacity-50"
                >
                  Speichern
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Info Box */}
      <div className="card mt-6 bg-blue-50 border-blue-200">
        <h4 className="font-semibold text-blue-800 mb-2">ℹ️ Hinweis zu Rollen</h4>
        <p className="text-sm text-blue-700">
          Die Rollen werden automatisch beim Start der Anwendung erstellt. 
          Sie können die Berechtigungen jeder Rolle anpassen, aber keine neuen Rollen erstellen.
          Um einem Benutzer oder Mitglied eine Rolle zuzuweisen, nutzen Sie die Personalverwaltung.
        </p>
      </div>
    </div>
  )
}

export default RoleManagement
