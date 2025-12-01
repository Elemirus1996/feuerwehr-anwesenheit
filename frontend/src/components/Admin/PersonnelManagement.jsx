import { useState, useEffect } from 'react'
import axios from 'axios'

const DIENSTGRADE = [
  'FM', 'OFM', 'HFM', 'LM', 'OLM', 'HLM', 'BM', 'OBM', 'HBM', 'UBM', 'BI', 'OBI', 'HBI', 'BR', 'OBR', 'BD'
]

function PersonnelManagement() {
  const [personnel, setPersonnel] = useState([])
  const [groups, setGroups] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [editingPerson, setEditingPerson] = useState(null)
  const [filterGroup, setFilterGroup] = useState('')
  const [formData, setFormData] = useState({
    stammrollennummer: '',
    vorname: '',
    nachname: '',
    dienstgrad: 'FM',
    aktiv: true,
    group_id: ''
  })

  const token = localStorage.getItem('token')
  const authHeader = { headers: { Authorization: `Bearer ${token}` } }

  const loadPersonnel = async () => {
    try {
      const params = filterGroup ? `?group_id=${filterGroup}` : ''
      const response = await axios.get(`/api/personnel/${params}`, authHeader)
      setPersonnel(response.data)
    } catch (err) {
      setError('Fehler beim Laden der Mitarbeiter')
    } finally {
      setLoading(false)
    }
  }

  const loadGroups = async () => {
    try {
      const response = await axios.get('/api/groups/', authHeader)
      setGroups(response.data)
    } catch (err) {
      console.log('Fehler beim Laden der Gruppen:', err)
    }
  }

  useEffect(() => {
    loadGroups()
  }, [])

  useEffect(() => {
    loadPersonnel()
  }, [filterGroup])

  const resetForm = () => {
    setFormData({
      stammrollennummer: '',
      vorname: '',
      nachname: '',
      dienstgrad: 'FM',
      aktiv: true,
      group_id: ''
    })
    setEditingPerson(null)
    setShowForm(false)
  }

  const handleEdit = (person) => {
    setEditingPerson(person)
    setFormData({
      stammrollennummer: person.stammrollennummer,
      vorname: person.vorname,
      nachname: person.nachname,
      dienstgrad: person.dienstgrad,
      aktiv: person.aktiv,
      group_id: person.group_id || ''
    })
    setShowForm(true)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    const submitData = {
      ...formData,
      group_id: formData.group_id ? parseInt(formData.group_id) : null
    }

    try {
      if (editingPerson) {
        await axios.put(`/api/personnel/${editingPerson.id}`, {
          vorname: submitData.vorname,
          nachname: submitData.nachname,
          dienstgrad: submitData.dienstgrad,
          aktiv: submitData.aktiv,
          group_id: submitData.group_id
        }, authHeader)
      } else {
        await axios.post('/api/personnel/', submitData, authHeader)
      }
      loadPersonnel()
      resetForm()
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Speichern')
    }
  }

  const handleDelete = async (person) => {
    if (!confirm(`Mitarbeiter ${person.vorname} ${person.nachname} wirklich löschen?`)) {
      return
    }

    try {
      await axios.delete(`/api/personnel/${person.id}`, authHeader)
      loadPersonnel()
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Löschen')
    }
  }

  if (loading) {
    return <div className="text-center py-8">Lade Mitarbeiter...</div>
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Personalverwaltung</h2>
        <button
          onClick={() => setShowForm(true)}
          className="btn-primary"
        >
          + Neuer Mitarbeiter
        </button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* Formular */}
      {showForm && (
        <div className="card mb-6">
          <h3 className="text-lg font-semibold mb-4">
            {editingPerson ? 'Mitarbeiter bearbeiten' : 'Neuer Mitarbeiter'}
          </h3>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Stammrollennummer
                </label>
                <input
                  type="text"
                  value={formData.stammrollennummer}
                  onChange={(e) => setFormData({ ...formData, stammrollennummer: e.target.value })}
                  className="input-touch"
                  required
                  disabled={!!editingPerson}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Dienstgrad
                </label>
                <select
                  value={formData.dienstgrad}
                  onChange={(e) => setFormData({ ...formData, dienstgrad: e.target.value })}
                  className="input-touch"
                >
                  {DIENSTGRADE.map(d => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Vorname
                </label>
                <input
                  type="text"
                  value={formData.vorname}
                  onChange={(e) => setFormData({ ...formData, vorname: e.target.value })}
                  className="input-touch"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nachname
                </label>
                <input
                  type="text"
                  value={formData.nachname}
                  onChange={(e) => setFormData({ ...formData, nachname: e.target.value })}
                  className="input-touch"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Gruppe
                </label>
                <select
                  value={formData.group_id}
                  onChange={(e) => setFormData({ ...formData, group_id: e.target.value })}
                  className="input-touch"
                >
                  <option value="">Keine Gruppe</option>
                  {groups.map(g => (
                    <option key={g.id} value={g.id}>{g.name}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="mt-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.aktiv}
                  onChange={(e) => setFormData({ ...formData, aktiv: e.target.checked })}
                  className="w-5 h-5 rounded border-gray-300"
                />
                <span className="text-sm font-medium text-gray-700">Aktiv</span>
              </label>
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

      {/* Filter */}
      <div className="card mb-4">
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">Filter nach Gruppe:</label>
          <select
            value={filterGroup}
            onChange={(e) => setFilterGroup(e.target.value)}
            className="input-touch py-2 max-w-xs"
          >
            <option value="">Alle Gruppen</option>
            {groups.map(g => (
              <option key={g.id} value={g.id}>{g.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Tabelle */}
      <div className="card overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-4 font-semibold text-gray-600">Stammr.</th>
              <th className="text-left py-3 px-4 font-semibold text-gray-600">Dienstgrad</th>
              <th className="text-left py-3 px-4 font-semibold text-gray-600">Name</th>
              <th className="text-left py-3 px-4 font-semibold text-gray-600">Gruppe</th>
              <th className="text-left py-3 px-4 font-semibold text-gray-600">Status</th>
              <th className="text-right py-3 px-4 font-semibold text-gray-600">Aktionen</th>
            </tr>
          </thead>
          <tbody>
            {personnel.map((person) => (
              <tr key={person.id} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-3 px-4 font-mono">{person.stammrollennummer}</td>
                <td className="py-3 px-4">
                  <span className="bg-feuerwehr-red text-white px-2 py-1 rounded text-sm">
                    {person.dienstgrad}
                  </span>
                </td>
                <td className="py-3 px-4">{person.vorname} {person.nachname}</td>
                <td className="py-3 px-4">
                  {person.group_name ? (
                    <span className="px-2 py-1 rounded text-sm bg-gray-100 text-gray-700">
                      {person.group_name}
                    </span>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="py-3 px-4">
                  <span className={`px-2 py-1 rounded text-sm ${
                    person.aktiv 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-gray-100 text-gray-600'
                  }`}>
                    {person.aktiv ? 'Aktiv' : 'Inaktiv'}
                  </span>
                </td>
                <td className="py-3 px-4 text-right">
                  <button
                    onClick={() => handleEdit(person)}
                    className="text-blue-600 hover:text-blue-800 mr-3"
                  >
                    Bearbeiten
                  </button>
                  <button
                    onClick={() => handleDelete(person)}
                    className="text-red-600 hover:text-red-800"
                  >
                    Löschen
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {personnel.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            Keine Mitarbeiter vorhanden
          </div>
        )}
      </div>
    </div>
  )
}

export default PersonnelManagement
