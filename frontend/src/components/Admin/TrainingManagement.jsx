/**
 * TrainingManagement - Feature 15: Team-Features
 * Admin component for managing trainings (Ausbildungs-Tracking)
 */

import { useState, useEffect } from 'react'
import axios from 'axios'

function TrainingManagement() {
  const [trainings, setTrainings] = useState([])
  const [expiringTrainings, setExpiringTrainings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [editingTraining, setEditingTraining] = useState(null)
  const [activeTab, setActiveTab] = useState('trainings')
  const [formData, setFormData] = useState({
    name: '',
    category: 'lehrgang',
    duration_hours: '',
    validity_months: ''
  })

  const token = localStorage.getItem('token')
  const authHeader = { headers: { Authorization: `Bearer ${token}` } }

  const categoryOptions = [
    { value: 'lehrgang', label: 'Lehrgang' },
    { value: 'fortbildung', label: 'Fortbildung' },
    { value: 'zertifikat', label: 'Zertifikat' }
  ]

  const loadTrainings = async () => {
    try {
      const response = await axios.get('/api/trainings/', authHeader)
      setTrainings(response.data)
    } catch (err) {
      setError('Fehler beim Laden der Schulungen')
    } finally {
      setLoading(false)
    }
  }

  const loadExpiringTrainings = async () => {
    try {
      const response = await axios.get('/api/trainings/expiring?days=90', authHeader)
      setExpiringTrainings(response.data)
    } catch (err) {
      console.log('Fehler beim Laden der ablaufenden Schulungen:', err)
    }
  }

  useEffect(() => {
    loadTrainings()
    loadExpiringTrainings()
  }, [])

  const resetForm = () => {
    setFormData({
      name: '',
      category: 'lehrgang',
      duration_hours: '',
      validity_months: ''
    })
    setEditingTraining(null)
    setShowForm(false)
  }

  const handleEdit = (training) => {
    setEditingTraining(training)
    setFormData({
      name: training.name,
      category: training.category,
      duration_hours: training.duration_hours || '',
      validity_months: training.validity_months || ''
    })
    setShowForm(true)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    const payload = {
      name: formData.name,
      category: formData.category,
      duration_hours: formData.duration_hours ? parseInt(formData.duration_hours) : null,
      validity_months: formData.validity_months ? parseInt(formData.validity_months) : null
    }

    try {
      if (editingTraining) {
        await axios.put(`/api/trainings/${editingTraining.id}`, payload, authHeader)
      } else {
        await axios.post('/api/trainings/', payload, authHeader)
      }
      loadTrainings()
      resetForm()
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Speichern')
    }
  }

  const handleDelete = async (training) => {
    if (!confirm(`Schulung "${training.name}" wirklich löschen? Alle zugewiesenen Einträge werden ebenfalls gelöscht.`)) {
      return
    }

    try {
      await axios.delete(`/api/trainings/${training.id}`, authHeader)
      loadTrainings()
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Löschen')
    }
  }

  const getCategoryBadge = (category) => {
    const colors = {
      lehrgang: 'bg-blue-100 text-blue-800',
      fortbildung: 'bg-purple-100 text-purple-800',
      zertifikat: 'bg-green-100 text-green-800'
    }
    const labels = {
      lehrgang: 'Lehrgang',
      fortbildung: 'Fortbildung',
      zertifikat: 'Zertifikat'
    }
    return (
      <span className={`px-2 py-1 rounded text-sm ${colors[category] || 'bg-gray-100 text-gray-800'}`}>
        {labels[category] || category}
      </span>
    )
  }

  const getExpiryStyle = (daysUntil) => {
    if (daysUntil <= 14) return 'bg-red-100 border-l-4 border-l-red-500'
    if (daysUntil <= 30) return 'bg-yellow-100 border-l-4 border-l-yellow-500'
    return 'bg-orange-50 border-l-4 border-l-orange-300'
  }

  if (loading) {
    return <div className="text-center py-8">Lade Schulungen...</div>
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">📚 Ausbildungs-Tracking</h2>
        <button
          onClick={() => setShowForm(true)}
          className="btn-primary"
        >
          + Neue Schulung
        </button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('trainings')}
          className={`px-4 py-2 rounded-lg transition-colors ${
            activeTab === 'trainings'
              ? 'bg-feuerwehr-red text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Schulungen ({trainings.length})
        </button>
        <button
          onClick={() => setActiveTab('expiring')}
          className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'expiring'
              ? 'bg-feuerwehr-red text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Ablaufende Zertifikate
          {expiringTrainings.length > 0 && (
            <span className={`px-2 py-0.5 rounded-full text-xs ${
              activeTab === 'expiring' ? 'bg-white text-feuerwehr-red' : 'bg-red-500 text-white'
            }`}>
              {expiringTrainings.length}
            </span>
          )}
        </button>
      </div>

      {/* Form */}
      {showForm && (
        <div className="card mb-6">
          <h3 className="text-lg font-semibold mb-4">
            {editingTraining ? 'Schulung bearbeiten' : 'Neue Schulung'}
          </h3>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name der Schulung
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input-touch"
                  placeholder="z.B. Atemschutz G26, Maschinisten-Lehrgang"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Kategorie
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="input-touch"
                >
                  {categoryOptions.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Dauer (Stunden)
                </label>
                <input
                  type="number"
                  value={formData.duration_hours}
                  onChange={(e) => setFormData({ ...formData, duration_hours: e.target.value })}
                  className="input-touch"
                  placeholder="Optional"
                  min="1"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Gültigkeitsdauer (Monate)
                </label>
                <input
                  type="number"
                  value={formData.validity_months}
                  onChange={(e) => setFormData({ ...formData, validity_months: e.target.value })}
                  className="input-touch"
                  placeholder="Leer lassen für unbegrenzte Gültigkeit"
                  min="1"
                />
                <p className="text-sm text-gray-500 mt-1">
                  z.B. 12 für jährliche Wiederholung, 24 für alle 2 Jahre
                </p>
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

      {/* Trainings List */}
      {activeTab === 'trainings' && (
        <div className="card overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-semibold text-gray-600">Name</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-600">Kategorie</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-600">Dauer</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-600">Gültigkeit</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-600">Zugewiesen</th>
                <th className="text-right py-3 px-4 font-semibold text-gray-600">Aktionen</th>
              </tr>
            </thead>
            <tbody>
              {trainings.map((training) => (
                <tr key={training.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4 font-medium">{training.name}</td>
                  <td className="py-3 px-4">{getCategoryBadge(training.category)}</td>
                  <td className="py-3 px-4">
                    {training.duration_hours ? `${training.duration_hours} Std.` : '-'}
                  </td>
                  <td className="py-3 px-4">
                    {training.validity_months ? `${training.validity_months} Monate` : 'Unbegrenzt'}
                  </td>
                  <td className="py-3 px-4">
                    <span className="bg-gray-100 text-gray-700 px-2 py-1 rounded">
                      {training.personnel_count} Person{training.personnel_count !== 1 ? 'en' : ''}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => handleEdit(training)}
                      className="text-blue-600 hover:text-blue-800 mr-3"
                    >
                      Bearbeiten
                    </button>
                    <button
                      onClick={() => handleDelete(training)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Löschen
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {trainings.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              Keine Schulungen vorhanden
            </div>
          )}
        </div>
      )}

      {/* Expiring Trainings */}
      {activeTab === 'expiring' && (
        <div className="space-y-3">
          {expiringTrainings.length === 0 ? (
            <div className="card text-center py-8 text-gray-500">
              ✅ Keine Zertifikate laufen in den nächsten 90 Tagen ab
            </div>
          ) : (
            expiringTrainings.map((item) => (
              <div
                key={item.id}
                className={`card ${getExpiryStyle(item.days_until_expiry)}`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-semibold text-lg">{item.personnel_name}</div>
                    <div className="text-gray-600">
                      <span className="font-mono text-sm">#{item.stammrollennummer}</span>
                      {' • '}
                      {item.training_name}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`font-bold ${
                      item.days_until_expiry <= 14 ? 'text-red-600' : 
                      item.days_until_expiry <= 30 ? 'text-yellow-600' : 'text-orange-600'
                    }`}>
                      {item.days_until_expiry === 0 
                        ? 'Läuft heute ab!'
                        : item.days_until_expiry === 1
                          ? 'Läuft morgen ab!'
                          : `Noch ${item.days_until_expiry} Tage`}
                    </div>
                    <div className="text-sm text-gray-500">
                      Ablauf: {new Date(item.expires_date).toLocaleDateString('de-DE')}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}

export default TrainingManagement
