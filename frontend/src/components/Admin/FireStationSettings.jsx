import { useState, useEffect } from 'react'
import axios from 'axios'

function FireStationSettings() {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  
  const [formData, setFormData] = useState({
    name: '',
    street: '',
    city: '',
    postal_code: ''
  })
  const [hasLogo, setHasLogo] = useState(false)
  const [logoPreview, setLogoPreview] = useState(null)

  const token = localStorage.getItem('token')
  const authHeader = { headers: { Authorization: `Bearer ${token}` } }

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      const response = await axios.get('/api/settings/firestation')
      setFormData({
        name: response.data.name || '',
        street: response.data.street || '',
        city: response.data.city || '',
        postal_code: response.data.postal_code || ''
      })
      setHasLogo(response.data.has_logo)
      if (response.data.has_logo) {
        setLogoPreview(`/api/settings/firestation/logo?t=${Date.now()}`)
      }
    } catch (err) {
      setError('Fehler beim Laden der Einstellungen')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    setSuccess(null)

    try {
      await axios.put('/api/settings/firestation', formData, authHeader)
      setSuccess('Einstellungen erfolgreich gespeichert!')
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Speichern')
    } finally {
      setSaving(false)
    }
  }

  const handleLogoUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    // Validierung
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/svg+xml']
    if (!allowedTypes.includes(file.type)) {
      setError('Nur PNG, JPG und SVG Dateien sind erlaubt')
      return
    }

    if (file.size > 2 * 1024 * 1024) {
      setError('Datei ist zu groß. Maximale Größe: 2 MB')
      return
    }

    setUploading(true)
    setError(null)

    const formDataUpload = new FormData()
    formDataUpload.append('file', file)

    try {
      await axios.post('/api/settings/firestation/logo', formDataUpload, {
        ...authHeader,
        headers: {
          ...authHeader.headers,
          'Content-Type': 'multipart/form-data'
        }
      })
      setHasLogo(true)
      setLogoPreview(`/api/settings/firestation/logo?t=${Date.now()}`)
      setSuccess('Logo erfolgreich hochgeladen!')
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Hochladen des Logos')
    } finally {
      setUploading(false)
    }
  }

  const handleDeleteLogo = async () => {
    if (!confirm('Logo wirklich löschen?')) return

    try {
      await axios.delete('/api/settings/firestation/logo', authHeader)
      setHasLogo(false)
      setLogoPreview(null)
      setSuccess('Logo gelöscht')
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Fehler beim Löschen des Logos')
    }
  }

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-feuerwehr-red border-t-transparent mx-auto"></div>
        <p className="mt-4 text-gray-600">Lade Einstellungen...</p>
      </div>
    )
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Feuerwehr-Einstellungen</h2>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-4">
          {error}
          <button onClick={() => setError(null)} className="float-right font-bold">×</button>
        </div>
      )}

      {success && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg mb-4">
          {success}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Einstellungsformular */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Stammdaten</h3>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Name der Feuerwehr *
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                className="input-touch"
                placeholder="z.B. Freiwillige Feuerwehr Musterstadt"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Straße
              </label>
              <input
                type="text"
                name="street"
                value={formData.street}
                onChange={handleChange}
                className="input-touch"
                placeholder="z.B. Hauptstraße 1"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  PLZ *
                </label>
                <input
                  type="text"
                  name="postal_code"
                  value={formData.postal_code}
                  onChange={handleChange}
                  required
                  className="input-touch"
                  placeholder="12345"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Stadt *
                </label>
                <input
                  type="text"
                  name="city"
                  value={formData.city}
                  onChange={handleChange}
                  required
                  className="input-touch"
                  placeholder="Musterstadt"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={saving}
              className="btn-primary w-full"
            >
              {saving ? 'Speichere...' : 'Einstellungen speichern'}
            </button>
          </form>
        </div>

        {/* Logo-Upload */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Logo</h3>
          
          <div className="space-y-4">
            {/* Logo-Vorschau */}
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center">
              {logoPreview ? (
                <div>
                  <img
                    src={logoPreview}
                    alt="Feuerwehr-Logo"
                    className="max-h-40 mx-auto mb-4 object-contain"
                    onError={() => {
                      setLogoPreview(null)
                      setHasLogo(false)
                    }}
                  />
                  <button
                    onClick={handleDeleteLogo}
                    className="btn-danger text-sm"
                  >
                    Logo löschen
                  </button>
                </div>
              ) : (
                <div className="py-8 text-gray-500">
                  <div className="text-4xl mb-2">🖼️</div>
                  <p>Kein Logo hochgeladen</p>
                </div>
              )}
            </div>

            {/* Upload-Button */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Logo hochladen
              </label>
              <input
                type="file"
                accept=".png,.jpg,.jpeg,.svg"
                onChange={handleLogoUpload}
                disabled={uploading}
                className="block w-full text-sm text-gray-500
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-lg file:border-0
                  file:text-sm file:font-semibold
                  file:bg-feuerwehr-red file:text-white
                  hover:file:bg-red-700
                  cursor-pointer"
              />
              <p className="text-xs text-gray-500 mt-1">
                Erlaubte Formate: PNG, JPG, SVG. Max. 2 MB.
              </p>
              {uploading && (
                <p className="text-sm text-blue-600 mt-2">Logo wird hochgeladen...</p>
              )}
            </div>
          </div>
        </div>

        {/* PDF-Vorschau */}
        <div className="card lg:col-span-2">
          <h3 className="text-lg font-semibold mb-4">Vorschau (PDF-Header)</h3>
          <div className="border rounded-lg p-6 bg-white">
            <div className="text-center">
              {logoPreview && (
                <img
                  src={logoPreview}
                  alt="Logo"
                  className="h-16 mx-auto mb-2 object-contain"
                  onError={() => setLogoPreview(null)}
                />
              )}
              <h2 className="text-xl font-bold text-red-800">{formData.name || 'Feuerwehr-Name'}</h2>
              {(formData.street || formData.postal_code || formData.city) && (
                <p className="text-gray-600 text-sm">
                  {formData.street && `${formData.street}, `}
                  {formData.postal_code} {formData.city}
                </p>
              )}
              <p className="text-gray-500 mt-1">Anwesenheitsliste</p>
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            So wird der Header in den PDF-Exporten angezeigt.
          </p>
        </div>
      </div>
    </div>
  )
}

export default FireStationSettings
