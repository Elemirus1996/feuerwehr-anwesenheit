/**
 * PersonalizationSettings - Feature 12: Personalization
 * Component for managing theme, font size, high contrast, and language settings
 */

import { useState } from 'react'
import { useTheme } from '../../contexts/ThemeContext'

function PersonalizationSettings() {
  const {
    theme,
    fontSize,
    highContrast,
    language,
    kioskMode,
    setTheme,
    setFontSize,
    setHighContrast,
    setLanguage,
    setKioskMode
  } = useTheme()

  const [showSuccess, setShowSuccess] = useState(false)

  const handleChange = (setter) => (value) => {
    setter(value)
    setShowSuccess(true)
    setTimeout(() => setShowSuccess(false), 2000)
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Personalisierung</h2>

      {showSuccess && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg mb-4">
          Einstellungen gespeichert!
        </div>
      )}

      <div className="grid gap-6">
        {/* Theme Selection */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">🎨 Erscheinungsbild</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Farbschema
              </label>
              <div className="grid grid-cols-3 gap-3">
                <button
                  onClick={() => handleChange(setTheme)('light')}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    theme === 'light'
                      ? 'border-feuerwehr-red bg-red-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="text-2xl mb-1">☀️</div>
                  <div className="font-medium">Hell</div>
                </button>
                <button
                  onClick={() => handleChange(setTheme)('dark')}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    theme === 'dark'
                      ? 'border-feuerwehr-red bg-red-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="text-2xl mb-1">🌙</div>
                  <div className="font-medium">Dunkel</div>
                </button>
                <button
                  onClick={() => handleChange(setTheme)('auto')}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    theme === 'auto'
                      ? 'border-feuerwehr-red bg-red-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="text-2xl mb-1">🔄</div>
                  <div className="font-medium">Auto</div>
                </button>
              </div>
              <p className="text-sm text-gray-500 mt-2">
                "Auto" folgt den System-Einstellungen Ihres Geräts.
              </p>
            </div>

            {/* High Contrast */}
            <div className="flex items-center justify-between">
              <div>
                <label className="font-medium text-gray-700">Hoher Kontrast</label>
                <p className="text-sm text-gray-500">Verbesserte Lesbarkeit durch stärkere Kontraste</p>
              </div>
              <button
                onClick={() => handleChange(setHighContrast)(!highContrast)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  highContrast ? 'bg-feuerwehr-red' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                    highContrast ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* Font Size */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">📏 Schriftgröße</h3>
          
          <div className="grid grid-cols-3 gap-3">
            <button
              onClick={() => handleChange(setFontSize)('normal')}
              className={`p-4 rounded-lg border-2 transition-all ${
                fontSize === 'normal'
                  ? 'border-feuerwehr-red bg-red-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-base mb-1">Aa</div>
              <div className="font-medium text-sm">Normal</div>
            </button>
            <button
              onClick={() => handleChange(setFontSize)('large')}
              className={`p-4 rounded-lg border-2 transition-all ${
                fontSize === 'large'
                  ? 'border-feuerwehr-red bg-red-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-lg mb-1">Aa</div>
              <div className="font-medium text-sm">Groß</div>
            </button>
            <button
              onClick={() => handleChange(setFontSize)('extra_large')}
              className={`p-4 rounded-lg border-2 transition-all ${
                fontSize === 'extra_large'
                  ? 'border-feuerwehr-red bg-red-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-xl mb-1">Aa</div>
              <div className="font-medium text-sm">Sehr Groß</div>
            </button>
          </div>
        </div>

        {/* Language */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">🌐 Sprache</h3>
          
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => handleChange(setLanguage)('de')}
              className={`p-4 rounded-lg border-2 transition-all ${
                language === 'de'
                  ? 'border-feuerwehr-red bg-red-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-2xl mb-1">🇩🇪</div>
              <div className="font-medium">Deutsch</div>
            </button>
            <button
              onClick={() => handleChange(setLanguage)('en')}
              className={`p-4 rounded-lg border-2 transition-all ${
                language === 'en'
                  ? 'border-feuerwehr-red bg-red-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-2xl mb-1">🇬🇧</div>
              <div className="font-medium">English</div>
            </button>
          </div>
          <p className="text-sm text-gray-500 mt-2">
            Weitere Sprachen werden in zukünftigen Updates hinzugefügt.
          </p>
        </div>

        {/* Kiosk Mode */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">🖥️ Kiosk-Optimierungen</h3>
          
          <div className="flex items-center justify-between">
            <div>
              <label className="font-medium text-gray-700">Kiosk-Modus aktivieren</label>
              <p className="text-sm text-gray-500">
                Extra große Buttons (mind. 60x60px) für Touch-Bedienung
              </p>
            </div>
            <button
              onClick={() => handleChange(setKioskMode)(!kioskMode)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                kioskMode ? 'bg-feuerwehr-red' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                  kioskMode ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>

        {/* Preview */}
        <div className="card bg-gray-50">
          <h3 className="text-lg font-semibold mb-4">👁️ Vorschau</h3>
          <div className="p-4 rounded-lg bg-white border border-gray-200">
            <div className="text-lg font-bold mb-2">Beispiel-Überschrift</div>
            <p className="text-gray-600 mb-4">
              Dies ist ein Beispieltext, um die aktuellen Einstellungen zu demonstrieren.
              Die Schriftgröße und Kontraste werden hier dargestellt.
            </p>
            <div className="flex gap-2">
              <button className="btn-primary text-sm py-2 px-4">Primär</button>
              <button className="btn-secondary text-sm py-2 px-4">Sekundär</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PersonalizationSettings
