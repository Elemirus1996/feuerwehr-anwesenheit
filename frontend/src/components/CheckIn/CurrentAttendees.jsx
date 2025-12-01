function CurrentAttendees({ attendees, sessionInfo }) {
  const formatTime = (isoString) => {
    const date = new Date(isoString)
    return date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="card">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-gray-800">
          Aktuell anwesend
        </h2>
        <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full font-semibold">
          {attendees.length} {attendees.length === 1 ? 'Person' : 'Personen'}
        </span>
      </div>

      {sessionInfo?.remaining_minutes !== null && sessionInfo?.remaining_minutes !== undefined && (
        <div className={`mb-4 px-4 py-2 rounded-lg text-center font-medium ${
          sessionInfo.remaining_minutes <= 15 
            ? 'bg-yellow-100 text-yellow-800' 
            : 'bg-blue-100 text-blue-800'
        }`}>
          {sessionInfo.remaining_minutes <= 0 ? (
            <span>⚠️ Session wird bald automatisch beendet</span>
          ) : (
            <span>⏱️ Noch {sessionInfo.remaining_minutes} Min. bis automatisches Ende</span>
          )}
        </div>
      )}

      {attendees.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-2">👋</div>
          <p>Noch keine Anwesenden</p>
          <p className="text-sm">Bitte mit Stammrollennummer einchecken</p>
        </div>
      ) : (
        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {attendees.map((person) => (
            <div key={person.id} className="attendee-item">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-feuerwehr-red text-white rounded-full 
                              flex items-center justify-center font-bold text-sm">
                  {person.dienstgrad}
                </div>
                <div>
                  <div className="font-semibold text-gray-800">
                    {person.vorname} {person.nachname}
                  </div>
                  <div className="text-sm text-gray-500">
                    Stammrolle: {person.stammrollennummer}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-500">Check-in</div>
                <div className="font-mono font-semibold text-green-600">
                  {formatTime(person.check_in_time)}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default CurrentAttendees
