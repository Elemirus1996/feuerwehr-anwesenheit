/**
 * ThemeContext - Feature 12: Personalization
 * Provides theme, font-size, and high-contrast settings throughout the app
 */

import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import axios from 'axios'

const ThemeContext = createContext(null)

export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState('auto')
  const [fontSize, setFontSize] = useState('normal')
  const [highContrast, setHighContrast] = useState(false)
  const [language, setLanguage] = useState('de')
  const [loading, setLoading] = useState(true)
  const [kioskMode, setKioskMode] = useState(false)

  // Load preferences from API or localStorage
  const loadPreferences = useCallback(async () => {
    // First try to load from localStorage (for non-authenticated users)
    const savedTheme = localStorage.getItem('theme')
    const savedFontSize = localStorage.getItem('fontSize')
    const savedHighContrast = localStorage.getItem('highContrast')
    const savedLanguage = localStorage.getItem('language')
    const savedKioskMode = localStorage.getItem('kioskMode')

    if (savedTheme) setTheme(savedTheme)
    if (savedFontSize) setFontSize(savedFontSize)
    if (savedHighContrast) setHighContrast(savedHighContrast === 'true')
    if (savedLanguage) setLanguage(savedLanguage)
    if (savedKioskMode) setKioskMode(savedKioskMode === 'true')

    // If authenticated, try to load from API
    const token = localStorage.getItem('token')
    if (token) {
      try {
        const response = await axios.get('/api/preferences', {
          headers: { Authorization: `Bearer ${token}` }
        })
        const prefs = response.data
        setTheme(prefs.theme)
        setFontSize(prefs.font_size)
        setHighContrast(prefs.high_contrast)
        setLanguage(prefs.language)
      } catch (err) {
        // If API fails, use localStorage values (already set above)
        console.log('Could not load preferences from API, using localStorage')
      }
    }

    setLoading(false)
  }, [])

  // Save preferences to API and localStorage
  const savePreferences = useCallback(async (newPrefs) => {
    // Always save to localStorage
    if (newPrefs.theme !== undefined) {
      localStorage.setItem('theme', newPrefs.theme)
      setTheme(newPrefs.theme)
    }
    if (newPrefs.fontSize !== undefined) {
      localStorage.setItem('fontSize', newPrefs.fontSize)
      setFontSize(newPrefs.fontSize)
    }
    if (newPrefs.highContrast !== undefined) {
      localStorage.setItem('highContrast', newPrefs.highContrast.toString())
      setHighContrast(newPrefs.highContrast)
    }
    if (newPrefs.language !== undefined) {
      localStorage.setItem('language', newPrefs.language)
      setLanguage(newPrefs.language)
    }
    if (newPrefs.kioskMode !== undefined) {
      localStorage.setItem('kioskMode', newPrefs.kioskMode.toString())
      setKioskMode(newPrefs.kioskMode)
    }

    // Try to save to API if authenticated
    const token = localStorage.getItem('token')
    if (token) {
      try {
        // Only include defined values in API payload
        const apiPayload = {}
        if (newPrefs.theme !== undefined) apiPayload.theme = newPrefs.theme
        if (newPrefs.fontSize !== undefined) apiPayload.font_size = newPrefs.fontSize
        if (newPrefs.highContrast !== undefined) apiPayload.high_contrast = newPrefs.highContrast
        if (newPrefs.language !== undefined) apiPayload.language = newPrefs.language
        
        if (Object.keys(apiPayload).length > 0) {
          await axios.put('/api/preferences', apiPayload, {
            headers: { Authorization: `Bearer ${token}` }
          })
        }
      } catch (err) {
        console.log('Could not save preferences to API')
      }
    }
  }, [])

  // Apply theme to document
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  // Apply font size to document
  useEffect(() => {
    document.documentElement.setAttribute('data-font-size', fontSize)
  }, [fontSize])

  // Apply high contrast to document
  useEffect(() => {
    document.documentElement.setAttribute('data-high-contrast', highContrast.toString())
  }, [highContrast])

  // Apply kiosk mode to document
  useEffect(() => {
    document.documentElement.setAttribute('data-kiosk-mode', kioskMode.toString())
  }, [kioskMode])

  // Initial load
  useEffect(() => {
    loadPreferences()
  }, [loadPreferences])

  const value = {
    theme,
    fontSize,
    highContrast,
    language,
    kioskMode,
    loading,
    setTheme: (t) => savePreferences({ theme: t }),
    setFontSize: (f) => savePreferences({ fontSize: f }),
    setHighContrast: (h) => savePreferences({ highContrast: h }),
    setLanguage: (l) => savePreferences({ language: l }),
    setKioskMode: (k) => savePreferences({ kioskMode: k }),
    savePreferences,
    loadPreferences
  }

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

export default ThemeContext
