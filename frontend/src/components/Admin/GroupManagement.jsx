/**
 * GroupManagement - Feature 15: Team-Features
 * Admin component for managing groups (Gruppenbildung)
 */

import { useState, useEffect } from 'react'
import axios from 'axios'

function GroupManagement() {
  const [groups, setGroups] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [editingGroup, setEditingGroup] = useState(null)
  const [selectedGroup, setSelectedGroup] = useState(null)
  const [groupMembers, setGroupMembers] = useState([])
  const [allPersonnel, setAllPersonnel] = useState([])
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    color: '#666666'
  })

  const token = localStorage.getItem('token')
  const authHeader = { headers: { Authorization: `Bearer ${token}` } }

  const presetColors = [
    '#3B82F6', '#22C55E', '#A855F7', '#F59E0B',
    '#EF4444', '#EC4899', '#06B6D4', '#84CC16'
  ]

  const loadGroups = async () => {
    try {
      const response = await axios.get('/api/groups?include_inactive=true', authHeader)
      setGroups(response.data)
    } catch (err) {
      setError('Fehler beim Laden der Gruppen')
    } finally {
      setLoading(false)
    }
  }

  const loadGroupMembers = async (groupId) => {
    try {
      const response = await axios.get(`/api/groups/${groupId}/members?include_inactive=true`, authHeader)
      setGroupMembers(response.data)
    } catch (err) {
      console.log('Fehler beim Laden der Mitglieder:', err)
    }
  }

  const loadAllPersonnel = async () => {
    try {
      const response = await axios.get('/api/personnel/', authHeader)
      setAllPersonnel(response.data)
    } catch (err) {
      console.log('Fehler beim Laden des Personals:', err)
    }
  }

  useEffect(() => {
    loadGroups()
    loadAllPersonnel()
  }, [])

  useEffect(() => {
    if (selectedGroup) {
      loadGroupMembers(selectedGroup.id)
    }
  }, [selectedGroup])

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      color: '#666666'
    })
    setEditingGroup(null)
    setShowForm(false)
  }

  const handleEdit = (group) => {
    setEditingGroup(group)
    setFormData({
      name: group.name,
      description: group.description || '',
      color: group.color
    })
    setShowForm(true)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    try {
      if (editingGroup) {
        await axios.put(`/api/groups/${editingGroup.id}`, formData, authHeader)
      } else {
        await axios.post('/api/groups/', formData, authHeader)
      }
      loadGroups()
      resetForm()
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Speichern')
    }
  }

  const handleDelete = async (group) => {
    if (!confirm(`Gruppe "${group.name}" wirklich löschen? Mitglieder werden nicht gelöscht, sondern nur aus der Gruppe entfernt.`)) {
      return
    }

    try {
      await axios.delete(`/api/groups/${group.id}`, authHeader)
      loadGroups()
      if (selectedGroup?.id === group.id) {
        setSelectedGroup(null)
        setGroupMembers([])
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Löschen')
    }
  }

  const handleAddMember = async (personnelId) => {
    if (!selectedGroup) return

    try {
      await axios.post(`/api/groups/${selectedGroup.id}/members/${personnelId}`, {}, authHeader)
      loadGroupMembers(selectedGroup.id)
      loadGroups()
      loadAllPersonnel()
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Hinzufügen')
    }
  }

  const handleRemoveMember = async (personnelId) => {
    if (!selectedGroup) return

    try {
      await axios.delete(`/api/groups/${selectedGroup.id}/members/${personnelId}`, authHeader)
      loadGroupMembers(selectedGroup.id)
      loadGroups()
      loadAllPersonnel()
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Entfernen')
    }
  }

  const availablePersonnel = allPersonnel.filter(
    p => p.group_id !== selectedGroup?.id
  )

  if (loading) {
    return <div className="text-center py-8">Lade Gruppen...</div>
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">👥 Gruppenmanagement</h2>
        <button
          onClick={() => setShowForm(true)}
          className="btn-primary"
        >
          + Neue Gruppe
        </button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* Form */}
      {showForm && (
        <div className="card mb-6">
          <h3 className="text-lg font-semibold mb-4">
            {editingGroup ? 'Gruppe bearbeiten' : 'Neue Gruppe'}
          </h3>
          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input-touch"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Beschreibung
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="input-touch"
                  rows={2}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Farbe
                </label>
                <div className="flex items-center gap-4">
                  <input
                    type="color"
                    value={formData.color}
                    onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                    className="w-12 h-12 rounded cursor-pointer"
                  />
                  <div className="flex gap-2">
                    {presetColors.map(color => (
                      <button
                        key={color}
                        type="button"
                        onClick={() => setFormData({ ...formData, color })}
                        className={`w-8 h-8 rounded-full border-2 transition-transform hover:scale-110 ${
                          formData.color === color ? 'border-gray-800 scale-110' : 'border-transparent'
                        }`}
                        style={{ backgroundColor: color }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button type="button" onClick={resetForm} className="btn-secondary flex-1">
                Abbrechen
              </button>
              <button type="submit" className="btn-primary flex-1">
                Speichern
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Groups List */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Gruppen</h3>
          <div className="space-y-3">
            {groups.map((group) => (
              <div
                key={group.id}
                onClick={() => setSelectedGroup(group)}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  selectedGroup?.id === group.id
                    ? 'border-feuerwehr-red bg-red-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-4 h-4 rounded-full"
                      style={{ backgroundColor: group.color }}
                    />
                    <div>
                      <div className="font-semibold">{group.name}</div>
                      <div className="text-sm text-gray-500">
                        {group.member_count} Mitglied{group.member_count !== 1 ? 'er' : ''}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleEdit(group)
                      }}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      ✏️
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDelete(group)
                      }}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
                {group.description && (
                  <p className="text-sm text-gray-500 mt-2">{group.description}</p>
                )}
              </div>
            ))}

            {groups.length === 0 && (
              <div className="text-center py-4 text-gray-500">
                Keine Gruppen vorhanden
              </div>
            )}
          </div>
        </div>

        {/* Members Management */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">
            {selectedGroup ? (
              <span className="flex items-center gap-2">
                <div
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: selectedGroup.color }}
                />
                Mitglieder: {selectedGroup.name}
              </span>
            ) : (
              'Mitglieder verwalten'
            )}
          </h3>

          {!selectedGroup ? (
            <div className="text-center py-8 text-gray-500">
              Wählen Sie eine Gruppe aus, um Mitglieder zu verwalten
            </div>
          ) : (
            <div className="space-y-4">
              {/* Current Members */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">
                  Aktuelle Mitglieder ({groupMembers.length})
                </h4>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {groupMembers.map((member) => (
                    <div
                      key={member.id}
                      className="flex items-center justify-between p-2 bg-gray-50 rounded"
                    >
                      <div>
                        <span className="bg-feuerwehr-red text-white px-2 py-0.5 rounded text-xs mr-2">
                          {member.dienstgrad}
                        </span>
                        {member.vorname} {member.nachname}
                      </div>
                      <button
                        onClick={() => handleRemoveMember(member.id)}
                        className="text-red-600 hover:text-red-800 text-sm"
                      >
                        Entfernen
                      </button>
                    </div>
                  ))}
                  {groupMembers.length === 0 && (
                    <div className="text-gray-500 text-sm">Keine Mitglieder</div>
                  )}
                </div>
              </div>

              {/* Add Members */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">
                  Mitglied hinzufügen
                </h4>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {availablePersonnel.map((person) => (
                    <div
                      key={person.id}
                      className="flex items-center justify-between p-2 border border-gray-200 rounded hover:bg-gray-50"
                    >
                      <div>
                        <span className="bg-gray-200 text-gray-700 px-2 py-0.5 rounded text-xs mr-2">
                          {person.dienstgrad}
                        </span>
                        {person.vorname} {person.nachname}
                        {person.group_name && (
                          <span className="text-xs text-gray-400 ml-2">
                            (in: {person.group_name})
                          </span>
                        )}
                      </div>
                      <button
                        onClick={() => handleAddMember(person.id)}
                        className="text-green-600 hover:text-green-800 text-sm"
                      >
                        + Hinzufügen
                      </button>
                    </div>
                  ))}
                  {availablePersonnel.length === 0 && (
                    <div className="text-gray-500 text-sm">
                      Alle Mitarbeiter sind bereits in dieser Gruppe
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default GroupManagement
