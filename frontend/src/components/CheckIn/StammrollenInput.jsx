import { useState } from 'react'

function StammrollenInput({ onSubmit, onCancel, loading }) {
  const [stammrollennummer, setStammrollennummer] = useState('')
  const [error, setError] = useState(null)

  const handleNumberClick = (num) => {
    if (stammrollennummer.length < 10) {
      setStammrollennummer(prev => prev + num)
      setError(null)
    }
  }

  const handleBackspace = () => {
    setStammrollennummer(prev => prev.slice(0, -1))
    setError(null)
  }

  const handleClear = () => {
    setStammrollennummer('')
    setError(null)
  }

  const handleSubmit = () => {
    if (stammrollennummer.trim() === '') {
      setError('Bitte geben Sie eine Stammrollennummer ein')
      return
    }
    onSubmit(stammrollennummer)
  }

  return (
    <div className="card max-w-md mx-auto">
      <h2 className="text-xl font-bold text-center mb-4 text-gray-800">
        Stammrollennummer eingeben
      </h2>

      {/* Display */}
      <div className="relative mb-6">
        <input
          type="text"
          value={stammrollennummer}
          readOnly
          className="input-touch text-center text-2xl tracking-widest font-mono bg-gray-50"
          placeholder="---"
        />
        {stammrollennummer && (
          <button
            onClick={handleClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 
                       hover:text-gray-600 text-xl p-2"
          >
            ✕
          </button>
        )}
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-3 py-2 
                        rounded mb-4 text-center text-sm">
          {error}
        </div>
      )}

      {/* Numpad */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(num => (
          <button
            key={num}
            onClick={() => handleNumberClick(String(num))}
            disabled={loading}
            className="numpad-btn"
          >
            {num}
          </button>
        ))}
        <button
          onClick={handleBackspace}
          disabled={loading}
          className="numpad-btn text-feuerwehr-red"
        >
          ←
        </button>
        <button
          onClick={() => handleNumberClick('0')}
          disabled={loading}
          className="numpad-btn"
        >
          0
        </button>
        <button
          onClick={handleSubmit}
          disabled={loading || !stammrollennummer}
          className="numpad-btn bg-green-500 text-white hover:bg-green-600 
                     active:bg-green-700 disabled:opacity-50"
        >
          ✓
        </button>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button
          onClick={onCancel}
          disabled={loading}
          className="btn-secondary flex-1"
        >
          Abbrechen
        </button>
        <button
          onClick={handleSubmit}
          disabled={loading || !stammrollennummer}
          className="btn-primary flex-1"
        >
          {loading ? 'Prüfe...' : 'Bestätigen'}
        </button>
      </div>
    </div>
  )
}

export default StammrollenInput
