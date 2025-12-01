import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import CheckInMain from './components/CheckIn/CheckInMain'
import CheckInToken from './components/CheckIn/CheckInToken'
import AdminDashboard from './components/Admin/AdminDashboard'
import Login from './components/Admin/Login'
import { useState, useEffect } from 'react'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    // Prüfe ob Token vorhanden ist
    const token = localStorage.getItem('token')
    setIsAuthenticated(!!token)
  }, [])

  const handleLogin = (token) => {
    localStorage.setItem('token', token)
    setIsAuthenticated(true)
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    setIsAuthenticated(false)
  }

  return (
    <Router>
      <Routes>
        {/* Check-in Interface (Kiosk-Modus) */}
        <Route path="/" element={<CheckInMain />} />
        
        {/* QR-Code Check-in */}
        <Route path="/checkin" element={<CheckInToken />} />
        
        {/* Admin Login */}
        <Route 
          path="/admin/login" 
          element={
            isAuthenticated 
              ? <Navigate to="/admin" replace /> 
              : <Login onLogin={handleLogin} />
          } 
        />
        
        {/* Admin Dashboard */}
        <Route 
          path="/admin/*" 
          element={
            isAuthenticated 
              ? <AdminDashboard onLogout={handleLogout} /> 
              : <Navigate to="/admin/login" replace />
          } 
        />
        
        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  )
}

export default App
