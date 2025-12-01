/**
 * PermissionContext - Feature 9: Security
 * Provides permission checking throughout the app
 */

import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import axios from 'axios'

const PermissionContext = createContext(null)

export const PermissionProvider = ({ children }) => {
  const [permissions, setPermissions] = useState([])
  const [role, setRole] = useState(null)
  const [loading, setLoading] = useState(true)

  // Load permissions from API
  const loadPermissions = useCallback(async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      setPermissions([])
      setRole(null)
      setLoading(false)
      return
    }

    try {
      const response = await axios.get('/api/roles/my-permissions', {
        headers: { Authorization: `Bearer ${token}` }
      })
      setPermissions(response.data.permissions || [])
      setRole(response.data.role)
    } catch (err) {
      console.log('Could not load permissions:', err)
      // If token is invalid, don't set any permissions
      setPermissions([])
      setRole(null)
    }

    setLoading(false)
  }, [])

  // Check if user has a specific permission
  const hasPermission = useCallback((permission) => {
    // Admin role has all permissions
    if (role === 'admin') return true
    return permissions.includes(permission)
  }, [permissions, role])

  // Check if user has any of the given permissions
  const hasAnyPermission = useCallback((permissionList) => {
    if (role === 'admin') return true
    return permissionList.some(p => permissions.includes(p))
  }, [permissions, role])

  // Check if user has all of the given permissions
  const hasAllPermissions = useCallback((permissionList) => {
    if (role === 'admin') return true
    return permissionList.every(p => permissions.includes(p))
  }, [permissions, role])

  // Initial load
  useEffect(() => {
    loadPermissions()
  }, [loadPermissions])

  // Reload when token changes
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === 'token') {
        loadPermissions()
      }
    }

    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [loadPermissions])

  const value = {
    permissions,
    role,
    loading,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    loadPermissions
  }

  return (
    <PermissionContext.Provider value={value}>
      {children}
    </PermissionContext.Provider>
  )
}

export const usePermissions = () => {
  const context = useContext(PermissionContext)
  if (!context) {
    throw new Error('usePermissions must be used within a PermissionProvider')
  }
  return context
}

export default PermissionContext
