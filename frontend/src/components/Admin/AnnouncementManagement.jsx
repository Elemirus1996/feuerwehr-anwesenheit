/**
 * AnnouncementManagement - Feature 15: Team-Features
 * Admin component for managing announcements (Schwarzes Brett)
 */

import { useState, useEffect } from 'react'
import axios from 'axios'

function AnnouncementManagement() {
  const [announcements, setAnnouncements] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [editingAnn, setEditingAnn] = useState(null)
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    priority: 'normal',
    valid_from: '',
    valid_until: '',
    target_groups: ['all']
  })

  const token = localStorage.getItem('token')
  const authHeader = { headers: { Authorization: `Bearer ${token}` } }

  const targetGroupOptions = [
    { value: 'all', label: 'Alle' },
    { value: 'jugend', label: 'Jugend' },
    { value: 'aktive', label: 'Aktive' },
    { value: 'ehrenabteilung', label: 'Ehrenabteilung' },
    { value: 'altersabteilung', label: 'Altersabteilung' }
  ]

  const priorityOptions = [
    { value: 'low', label: 'Niedrig', color: 'bg-gray-100 text-gray-800' },
    { value: 'normal', label: 'Normal', color: 'bg-blue-100 text-blue-800' },
    { value: 'high', label: 'Hoch', color: 'bg-yellow-100 text-yellow-800' },
    { value: 'urgent', label: 'Dringend', color: 'bg-red-100 text-red-800' }
  ]

  const loadAnnouncements = async () => {
    try {
      const response = await axios.get('/api/announcements/all?include_inactive=true', authHeader)
      setAnnouncements(response.data)
    } catch (err) {
      setError('Fehler beim Laden der Ankündigungen')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAnnouncements()
  }, [])

  const resetForm = () => {
    setFormData({
      title: '',
      content: '',
      priority: 'normal',
      valid_from: '',
      valid_until: '',
      target_groups: ['all']
    })
    setEditingAnn(null)
    setShowForm(false)
  }

  const handleEdit = (ann) => {
    setEditingAnn(ann)
    setFormData({
      title: ann.title,
      content: ann.content,
      priority: ann.priority,
      valid_from: ann.valid_from ? ann.valid_from.split('T')[0] : '',
      valid_until: ann.valid_until ? ann.valid_until.split('T')[0] : '',
      target_groups: ann.target_groups || ['all']
    })
    setShowForm(true)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    try {
      const payload = {
        ...formData,
        valid_from: formData.valid_from || new Date().toISOString(),
        valid_until: formData.valid_until || null
      }

      if (editingAnn) {
        await axios.put(`/api/announcements/${editingAnn.id}`, payload, authHeader)
      } else {
        await axios.post('/api/announcements/', payload, authHeader)
      }
      loadAnnouncements()
      resetForm()
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Speichern')
    }
  }

  const handleDelete = async (ann) => {
    if (!confirm(`Ankündigung "${ann.title}" wirklich löschen?`)) {
      return
    }

    try {
      await axios.delete(`/api/announcements/${ann.id}`, authHeader)
      loadAnnouncements()
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Löschen')
    }
  }

  const handleToggleActive = async (ann) => {
    try {
      await axios.put(`/api/announcements/${ann.id}`, {
        is_active: !ann.is_active
      }, authHeader)
      loadAnnouncements()
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Aktualisieren')
    }
  }

  const handleTargetGroupChange = (value) => {
    if (value === 'all') {
      setFormData({ ...formData, target_groups: ['all'] })
    } else {
      let newGroups = formData.target_groups.filter(g => g !== 'all')
      if (newGroups.includes(value)) {
        newGroups = newGroups.filter(g => g !== value)
      } else {
        newGroups.push(value)
      }
      if (newGroups.length === 0) {
        newGroups = ['all']
      }
      setFormData({ ...formData, target_groups: newGroups })
    }
  }

  const getPriorityBadge = (priority) => {
    const opt = priorityOptions.find(p => p.value === priority)
    return opt ? (
      <span className={`px-2 py-1 rounded text-sm ${opt.color}`}>
        {opt.label}
      </span>
    ) : null
  }

  if (loading) {
    return <div className="text-center py-8">Lade Ankündigungen...</div>
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">📢 Schwarzes Brett</h2>
        <button
          onClick={() => setShowForm(true)}
          className="btn-primary"
        >
          + Neue Ankündigung
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
            {editingAnn ? 'Ankündigung bearbeiten' : 'Neue Ankündigung'}
          </h3>
          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Titel
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="input-touch"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Inhalt
                </label>
                <textarea
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  className="input-touch min-h-[120px]"
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Priorität
                  </label>
                  <select
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                    className="input-touch"
                  >
                    {priorityOptions.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Gültig ab
                  </label>
                  <input
                    type="date"
                    value={formData.valid_from}
                    onChange={(e) => setFormData({ ...formData, valid_from: e.target.value })}
                    className="input-touch"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Gültig bis (optional)
                  </label>
                  <input
                    type="date"
                    value={formData.valid_until}
                    onChange={(e) => setFormData({ ...formData, valid_until: e.target.value })}
                    className="input-touch"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Zielgruppen
                </label>
                <div className="flex flex-wrap gap-2">
                  {targetGroupOptions.map(opt => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => handleTargetGroupChange(opt.value)}
                      className={`px-3 py-1 rounded-full border transition-colors ${
                        formData.target_groups.includes(opt.value)
                          ? 'bg-feuerwehr-red text-white border-feuerwehr-red'
                          : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
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

      {/* List */}
      <div className="space-y-4">
        {announcements.map((ann) => (
          <div
            key={ann.id}
            className={`card border-l-4 ${
              ann.is_active ? 'border-l-feuerwehr-red' : 'border-l-gray-300 opacity-60'
            }`}
          >
            <div className="flex justify-between items-start mb-2">
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-lg">{ann.title}</h3>
                {getPriorityBadge(ann.priority)}
                {!ann.is_active && (
                  <span className="px-2 py-1 rounded text-sm bg-gray-100 text-gray-600">
                    Inaktiv
                  </span>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleToggleActive(ann)}
                  className={`text-sm px-3 py-1 rounded ${
                    ann.is_active
                      ? 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      : 'bg-green-100 text-green-700 hover:bg-green-200'
                  }`}
                >
                  {ann.is_active ? 'Deaktivieren' : 'Aktivieren'}
                </button>
                <button
                  onClick={() => handleEdit(ann)}
                  className="text-blue-600 hover:text-blue-800"
                >
                  Bearbeiten
                </button>
                <button
                  onClick={() => handleDelete(ann)}
                  className="text-red-600 hover:text-red-800"
                >
                  Löschen
                </button>
              </div>
            </div>

            <p className="text-gray-600 mb-3 whitespace-pre-wrap">{ann.content}</p>

            <div className="flex flex-wrap gap-4 text-sm text-gray-500">
              <span>
                📅 Gültig ab: {new Date(ann.valid_from).toLocaleDateString('de-DE')}
              </span>
              {ann.valid_until && (
                <span>
                  ⏰ Bis: {new Date(ann.valid_until).toLocaleDateString('de-DE')}
                </span>
              )}
              <span>
                👤 Von: {ann.author_name || 'Unbekannt'}
              </span>
              <span>
                🎯 Gruppen: {ann.target_groups.join(', ')}
              </span>
            </div>
          </div>
        ))}

        {announcements.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            Keine Ankündigungen vorhanden
          </div>
        )}
      </div>
    </div>
  )
}

export default AnnouncementManagement
