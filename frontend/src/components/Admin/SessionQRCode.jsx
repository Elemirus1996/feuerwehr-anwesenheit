import { useState, useEffect } from 'react'

function SessionQRCode({ sessionId, size = 'medium' }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [qrUrl, setQrUrl] = useState(null)

  const sizeClasses = {
    small: 'w-24 h-24',
    medium: 'w-48 h-48',
    large: 'w-64 h-64'
  }

  useEffect(() => {
    if (sessionId) {
      loadQRCode()
    }
  }, [sessionId])

  const loadQRCode = () => {
    setLoading(true)
    setError(null)
    // Direkt die URL setzen, das Bild wird über <img> geladen
    setQrUrl(`/api/sessions/${sessionId}/qr?t=${Date.now()}`)
    setLoading(false)
  }

  const handleDownload = async () => {
    try {
      // Fetch image as blob for reliable cross-browser download
      const response = await fetch(qrUrl)
      const blob = await response.blob()
      const blobUrl = window.URL.createObjectURL(blob)
      
      const link = document.createElement('a')
      link.href = blobUrl
      link.download = `qr_session_${sessionId}.png`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      window.URL.revokeObjectURL(blobUrl)
    } catch (err) {
      console.error('Download failed:', err)
    }
  }

  const handlePrint = () => {
    const printWindow = window.open('', '_blank')
    printWindow.document.write(`
      <html>
        <head>
          <title>QR-Code Session ${sessionId}</title>
          <style>
            body {
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              min-height: 100vh;
              margin: 0;
              font-family: Arial, sans-serif;
            }
            img { max-width: 300px; }
            h2 { margin-bottom: 10px; }
            p { color: #666; }
          </style>
        </head>
        <body>
          <h2>🚒 Feuerwehr Check-in</h2>
          <img src="${qrUrl}" alt="QR-Code" />
          <p>Scanne diesen QR-Code zum Check-in</p>
          <p>Session #${sessionId}</p>
          <script>
            window.onload = function() {
              setTimeout(function() { window.print(); }, 500);
            }
          </script>
        </body>
      </html>
    `)
    printWindow.document.close()
  }

  if (!sessionId) {
    return null
  }

  if (loading) {
    return (
      <div className={`${sizeClasses[size]} flex items-center justify-center bg-gray-100 rounded-lg`}>
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-feuerwehr-red border-t-transparent"></div>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center">
      {qrUrl ? (
        <>
          <div className={`${sizeClasses[size]} border rounded-lg overflow-hidden bg-white p-2`}>
            <img
              src={qrUrl}
              alt="QR-Code zum Check-in"
              className="w-full h-full object-contain"
              onError={() => setError('QR-Code konnte nicht geladen werden')}
            />
          </div>
          {error && (
            <p className="text-red-500 text-sm mt-2">{error}</p>
          )}
          <p className="text-sm text-gray-500 mt-2 text-center">
            Scanne zum Check-in
          </p>
          <div className="flex gap-2 mt-2">
            <button
              onClick={handleDownload}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              📥 Herunterladen
            </button>
            <button
              onClick={handlePrint}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              🖨️ Drucken
            </button>
          </div>
        </>
      ) : (
        <div className={`${sizeClasses[size]} flex items-center justify-center bg-gray-100 rounded-lg`}>
          <p className="text-gray-500 text-sm">Kein QR-Code verfügbar</p>
        </div>
      )}
    </div>
  )
}

export default SessionQRCode
