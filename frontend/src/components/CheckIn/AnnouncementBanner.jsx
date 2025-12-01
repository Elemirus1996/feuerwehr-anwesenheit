/**
 * AnnouncementBanner - Feature 15: Team-Features
 * Displays announcements on the Kiosk interface
 */

import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'

function AnnouncementBanner() {
  const [announcements, setAnnouncements] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [loading, setLoading] = useState(true)

  const loadAnnouncements = useCallback(async () => {
    try {
      const response = await axios.get('/api/announcements')
      setAnnouncements(response.data)
    } catch (err) {
      console.log('Could not load announcements:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAnnouncements()
    // Refresh every 5 minutes
    const interval = setInterval(loadAnnouncements, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [loadAnnouncements])

  // Auto-rotate announcements every 10 seconds
  useEffect(() => {
    if (announcements.length <= 1) return

    const rotateInterval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % announcements.length)
    }, 10000)

    return () => clearInterval(rotateInterval)
  }, [announcements.length])

  if (loading || announcements.length === 0) {
    return null
  }

  const currentAnnouncement = announcements[currentIndex]

  const getPriorityStyles = (priority) => {
    switch (priority) {
      case 'urgent':
        return 'bg-red-600 text-white border-red-700'
      case 'high':
        return 'bg-yellow-500 text-white border-yellow-600'
      case 'normal':
        return 'bg-blue-500 text-white border-blue-600'
      case 'low':
      default:
        return 'bg-gray-500 text-white border-gray-600'
    }
  }

  const getPriorityIcon = (priority) => {
    switch (priority) {
      case 'urgent':
        return '🚨'
      case 'high':
        return '⚠️'
      case 'normal':
        return '📢'
      case 'low':
      default:
        return 'ℹ️'
    }
  }

  return (
    <div className={`announcement-banner border-b-4 ${getPriorityStyles(currentAnnouncement.priority)}`}>
      <div className="max-w-4xl mx-auto px-4 py-3">
        <div className="flex items-start gap-3">
          <span className="text-2xl flex-shrink-0">
            {getPriorityIcon(currentAnnouncement.priority)}
          </span>
          <div className="flex-1 min-w-0">
            <h3 className="font-bold text-lg">{currentAnnouncement.title}</h3>
            <p className="text-sm opacity-90 line-clamp-2">{currentAnnouncement.content}</p>
          </div>
          {announcements.length > 1 && (
            <div className="flex items-center gap-2 flex-shrink-0">
              <span className="text-sm opacity-75">
                {currentIndex + 1} / {announcements.length}
              </span>
              <div className="flex gap-1">
                <button
                  onClick={() => setCurrentIndex((prev) => (prev - 1 + announcements.length) % announcements.length)}
                  className="p-1 hover:bg-white/20 rounded"
                >
                  ◀
                </button>
                <button
                  onClick={() => setCurrentIndex((prev) => (prev + 1) % announcements.length)}
                  className="p-1 hover:bg-white/20 rounded"
                >
                  ▶
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default AnnouncementBanner
