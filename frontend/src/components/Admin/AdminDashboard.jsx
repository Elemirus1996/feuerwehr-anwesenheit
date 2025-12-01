import { useState, useEffect } from 'react'
import { Routes, Route, NavLink, useNavigate } from 'react-router-dom'
import axios from 'axios'
import PersonnelManagement from './PersonnelManagement'
import SessionList from './SessionList'
import AnnouncementManagement from './AnnouncementManagement'
import GroupManagement from './GroupManagement'
import TrainingManagement from './TrainingManagement'
import AuditLog from './AuditLog'
import BackupManagement from './BackupManagement'
import RoleManagement from './RoleManagement'
import PersonalizationSettings from '../Settings/PersonalizationSettings'

function AdminDashboard({ onLogout }) {
  const [stats, setStats] = useState(null)
  const [user, setUser] = useState(null)
  const [showMobileMenu, setShowMobileMenu] = useState(false)
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
    `px-4 py-2 rounded-lg transition-colors whitespace-nowrap ${
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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">📋 Verwaltung</h3>
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
          <h3 className="text-lg font-semibold mb-4">👥 Team-Features</h3>
          <div className="space-y-3">
            <NavLink
              to="/admin/announcements"
              className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="font-semibold">📢 Schwarzes Brett</div>
              <div className="text-sm text-gray-500">Ankündigungen verwalten</div>
            </NavLink>
            <NavLink
              to="/admin/groups"
              className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="font-semibold">🏷️ Gruppen</div>
              <div className="text-sm text-gray-500">Gruppenbildung</div>
            </NavLink>
            <NavLink
              to="/admin/trainings"
              className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="font-semibold">📚 Ausbildungen</div>
              <div className="text-sm text-gray-500">Schulungs-Tracking</div>
            </NavLink>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold mb-4">🔒 Administration</h3>
          <div className="space-y-3">
            <NavLink
              to="/admin/roles"
              className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="font-semibold">🔑 Rollen & Rechte</div>
              <div className="text-sm text-gray-500">Berechtigungen verwalten</div>
            </NavLink>
            <NavLink
              to="/admin/audit"
              className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="font-semibold">📋 Audit-Log</div>
              <div className="text-sm text-gray-500">Änderungsverfolgung</div>
            </NavLink>
            <NavLink
              to="/admin/backup"
              className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="font-semibold">💾 Backups</div>
              <div className="text-sm text-gray-500">Datensicherung</div>
            </NavLink>
            <NavLink
              to="/admin/settings"
              className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="font-semibold">⚙️ Einstellungen</div>
              <div className="text-sm text-gray-500">Personalisierung</div>
            </NavLink>
          </div>
        </div>
      </div>

      <div className="card mt-6">
        <h3 className="text-lg font-semibold mb-4">System-Info</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-500 block">Angemeldet als:</span>
            <span className="font-medium">{user?.username || '-'}</span>
          </div>
          <div>
            <span className="text-gray-500 block">Mitarbeiter gesamt:</span>
            <span className="font-medium">{stats?.total_personnel || 0}</span>
          </div>
          <div>
            <span className="text-gray-500 block">Version:</span>
            <span className="font-medium">1.1.0</span>
          </div>
          <div>
            <span className="text-gray-500 block">Features:</span>
            <span className="font-medium">F12, F15, F9</span>
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-bold text-feuerwehr-red">🚒 Feuerwehr Admin</h1>
              <nav className="hidden lg:flex gap-2 ml-8">
                <NavLink to="/admin" end className={navLinkClass}>
                  Dashboard
                </NavLink>
                <NavLink to="/admin/personnel" className={navLinkClass}>
                  Personal
                </NavLink>
                <NavLink to="/admin/sessions" className={navLinkClass}>
                  Sessions
                </NavLink>
                <NavLink to="/admin/announcements" className={navLinkClass}>
                  📢 Brett
                </NavLink>
                <NavLink to="/admin/groups" className={navLinkClass}>
                  Gruppen
                </NavLink>
                <NavLink to="/admin/trainings" className={navLinkClass}>
                  Schulungen
                </NavLink>
              </nav>
            </div>
            <div className="flex items-center gap-4">
              <NavLink to="/admin/settings" className="text-gray-500 hover:text-gray-700">
                ⚙️
              </NavLink>
              <span className="text-sm text-gray-500 hidden md:inline">{user?.username}</span>
              <button
                onClick={handleLogout}
                className="btn-secondary text-sm py-2"
              >
                Abmelden
              </button>
              <button
                onClick={() => setShowMobileMenu(!showMobileMenu)}
                className="lg:hidden text-gray-600"
              >
                ☰
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Navigation */}
      {showMobileMenu && (
        <nav className="lg:hidden bg-white border-b px-4 py-2 flex flex-wrap gap-2">
          <NavLink to="/admin" end className={navLinkClass} onClick={() => setShowMobileMenu(false)}>
            Dashboard
          </NavLink>
          <NavLink to="/admin/personnel" className={navLinkClass} onClick={() => setShowMobileMenu(false)}>
            Personal
          </NavLink>
          <NavLink to="/admin/sessions" className={navLinkClass} onClick={() => setShowMobileMenu(false)}>
            Sessions
          </NavLink>
          <NavLink to="/admin/announcements" className={navLinkClass} onClick={() => setShowMobileMenu(false)}>
            📢 Brett
          </NavLink>
          <NavLink to="/admin/groups" className={navLinkClass} onClick={() => setShowMobileMenu(false)}>
            Gruppen
          </NavLink>
          <NavLink to="/admin/trainings" className={navLinkClass} onClick={() => setShowMobileMenu(false)}>
            Schulungen
          </NavLink>
          <NavLink to="/admin/roles" className={navLinkClass} onClick={() => setShowMobileMenu(false)}>
            Rollen
          </NavLink>
          <NavLink to="/admin/audit" className={navLinkClass} onClick={() => setShowMobileMenu(false)}>
            Audit
          </NavLink>
          <NavLink to="/admin/backup" className={navLinkClass} onClick={() => setShowMobileMenu(false)}>
            Backup
          </NavLink>
          <NavLink to="/admin/settings" className={navLinkClass} onClick={() => setShowMobileMenu(false)}>
            Settings
          </NavLink>
        </nav>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<DashboardOverview />} />
          <Route path="/personnel" element={<PersonnelManagement />} />
          <Route path="/sessions" element={<SessionList />} />
          <Route path="/announcements" element={<AnnouncementManagement />} />
          <Route path="/groups" element={<GroupManagement />} />
          <Route path="/trainings" element={<TrainingManagement />} />
          <Route path="/roles" element={<RoleManagement />} />
          <Route path="/audit" element={<AuditLog />} />
          <Route path="/backup" element={<BackupManagement />} />
          <Route path="/settings" element={<PersonalizationSettings />} />
        </Routes>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t py-4 text-center text-sm text-gray-500">
        Feuerwehr Anwesenheits-App v1.1.0 | 
        <a href="/" className="text-feuerwehr-red hover:underline ml-1">
          Zur Anwesenheitserfassung
        </a>
      </footer>
    </div>
  )
}

export default AdminDashboard
