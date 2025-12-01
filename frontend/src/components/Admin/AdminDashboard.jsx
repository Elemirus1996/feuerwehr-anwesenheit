import { useState, useEffect } from 'react'
import { Routes, Route, NavLink, useNavigate } from 'react-router-dom'
import axios from 'axios'
import PersonnelManagement from './PersonnelManagement'
import SessionList from './SessionList'
import FireStationSettings from './FireStationSettings'

function AdminDashboard({ onLogout }) {
  const [stats, setStats] = useState(null)
  const [user, setUser] = useState(null)
  const navigate = useNavigate()

  const token = localStorage.getItem('token')
  const authHeader = { headers: { Authorization: `Bearer ${token}` } }

  useEffect(() => {
    loadStats()
    loadUser()
  }, [])

  const loadStats = async () => {
    try {
      const response = await axios.get('/api/admin/stats', authHeader)
      setStats(response.data)
    } catch (err) {
      console.error('Fehler beim Laden der Statistiken:', err)
    }
  }

  const loadUser = async () => {
    try {
      const response = await axios.get('/api/admin/me', authHeader)
      setUser(response.data)
    } catch (err) {
      console.error('Fehler beim Laden der Benutzerinfo:', err)
    }
  }

  const handleLogout = () => {
    onLogout()
    navigate('/admin/login')
  }

  const navLinkClass = ({ isActive }) =>
    `px-4 py-2 rounded-lg transition-colors ${
      isActive 
        ? 'bg-feuerwehr-red text-white' 
        : 'text-gray-600 hover:bg-gray-100'
    }`

  // Dashboard Übersicht
  const DashboardOverview = () => (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Dashboard</h2>
      
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="card bg-blue-50">
            <div className="text-blue-600 text-sm font-medium">Aktive Sessions</div>
            <div className="text-3xl font-bold text-blue-800">{stats.active_sessions}</div>
          </div>
          <div className="card bg-green-50">
            <div className="text-green-600 text-sm font-medium">Aktuell Anwesend</div>
            <div className="text-3xl font-bold text-green-800">{stats.current_attendees}</div>
          </div>
          <div className="card bg-yellow-50">
            <div className="text-yellow-600 text-sm font-medium">Aktive Mitarbeiter</div>
            <div className="text-3xl font-bold text-yellow-800">{stats.active_personnel}</div>
          </div>
          <div className="card bg-purple-50">
            <div className="text-purple-600 text-sm font-medium">Sessions (30 Tage)</div>
            <div className="text-3xl font-bold text-purple-800">{stats.recent_sessions_30d}</div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Schnellzugriff</h3>
          <div className="space-y-3">
            <NavLink
              to="/admin/personnel"
              className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="font-semibold">👥 Personalverwaltung</div>
              <div className="text-sm text-gray-500">Mitarbeiter verwalten</div>
            </NavLink>
            <NavLink
              to="/admin/sessions"
              className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="font-semibold">📋 Anwesenheitslisten</div>
              <div className="text-sm text-gray-500">Sessions und Berichte</div>
            </NavLink>
            <NavLink
              to="/admin/settings"
              className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="font-semibold">⚙️ Einstellungen</div>
              <div className="text-sm text-gray-500">Feuerwehr-Daten & Logo</div>
            </NavLink>
            <a
              href="/"
              className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="font-semibold">🖥️ Kiosk-Modus</div>
              <div className="text-sm text-gray-500">Zur Anwesenheitserfassung</div>
            </a>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold mb-4">System-Info</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Angemeldet als:</span>
              <span className="font-medium">{user?.username || '-'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Mitarbeiter gesamt:</span>
              <span className="font-medium">{stats?.total_personnel || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Version:</span>
              <span className="font-medium">1.0.0</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-bold text-feuerwehr-red">🚒 Feuerwehr Admin</h1>
              <nav className="hidden md:flex gap-2 ml-8">
                <NavLink to="/admin" end className={navLinkClass}>
                  Dashboard
                </NavLink>
                <NavLink to="/admin/personnel" className={navLinkClass}>
                  Personal
                </NavLink>
                <NavLink to="/admin/sessions" className={navLinkClass}>
                  Sessions
                </NavLink>
                <NavLink to="/admin/settings" className={navLinkClass}>
                  Einstellungen
                </NavLink>
              </nav>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-500">{user?.username}</span>
              <button
                onClick={handleLogout}
                className="btn-secondary text-sm py-2"
              >
                Abmelden
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Navigation */}
      <nav className="md:hidden bg-white border-b px-4 py-2 flex gap-2 overflow-x-auto">
        <NavLink to="/admin" end className={navLinkClass}>
          Dashboard
        </NavLink>
        <NavLink to="/admin/personnel" className={navLinkClass}>
          Personal
        </NavLink>
        <NavLink to="/admin/sessions" className={navLinkClass}>
          Sessions
        </NavLink>
        <NavLink to="/admin/settings" className={navLinkClass}>
          Einstellungen
        </NavLink>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<DashboardOverview />} />
          <Route path="/personnel" element={<PersonnelManagement />} />
          <Route path="/sessions" element={<SessionList />} />
          <Route path="/settings" element={<FireStationSettings />} />
        </Routes>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t py-4 text-center text-sm text-gray-500">
        Feuerwehr Anwesenheits-App v1.0.0 | 
        <a href="/" className="text-feuerwehr-red hover:underline ml-1">
          Zur Anwesenheitserfassung
        </a>
      </footer>
    </div>
  )
}

export default AdminDashboard
