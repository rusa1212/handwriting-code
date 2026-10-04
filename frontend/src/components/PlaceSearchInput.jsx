import { useRef, useState } from 'react'
import { searchPlaces } from '../api/client'

// 장소 검색 입력: Enter 또는 🔍 → 후보 목록 → 클릭하면 선택
// value: 선택된 Place({ name, lat, lng }) 또는 null
// center: 검색 기준 좌표 (그 근처 장소가 먼저 나온다)
// onPickOnMap: 📍 버튼을 누르면 호출 (지도 클릭으로 고르기), picking: 지금 이 칸을 지도에서 고르는 중인지
function PlaceSearchInput({ label, value, onChange, center, onPickOnMap, picking = false }) {
  const [query, setQuery] = useState(value?.name ?? '')
  const [prevValue, setPrevValue] = useState(value)
  const [candidates, setCandidates] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [open, setOpen] = useState(false)
  const requestIdRef = useRef(0) // 늦게 도착한 이전 검색의 응답은 버린다

  // 부모가 값을 바꾸면(⇅ 바꾸기, 빠른 선택) 입력 글자도 맞춘다
  // 직접 입력해서 null이 된 경우에는 사용자가 친 글자를 그대로 둔다
  if (value !== prevValue) {
    setPrevValue(value)
    if (value) {
      setQuery(value.name)
      setOpen(false)
    }
  }

  async function handleSearch() {
    const q = query.trim()
    if (!q) return
    const requestId = ++requestIdRef.current
    setLoading(true)
    setError(null)
    try {
      const found = await searchPlaces(q, center)
      if (requestId !== requestIdRef.current) return
      setCandidates(found)
      setOpen(true)
    } catch (err) {
      if (requestId !== requestIdRef.current) return
      setCandidates([])
      setOpen(false)
      setError(err.message)
    } finally {
      if (requestId === requestIdRef.current) setLoading(false)
    }
  }

  function handleType(e) {
    setQuery(e.target.value)
    setOpen(false)
    // 글자를 고치면 선택을 푼다 ("글자는 바뀌었는데 좌표는 예전 것" 상태를 막는다)
    if (value) onChange(null)
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') handleSearch()
    if (e.key === 'Escape') setOpen(false)
  }

  function handlePick(place) {
    onChange(place)
    setQuery(place.name)
    setOpen(false)
  }

  return (
    <div className="place-search">
      <label className="field">
        <span>{label}</span>
        <input
          type="text"
          value={query}
          placeholder="장소, 주소 검색"
          onChange={handleType}
          onKeyDown={handleKeyDown}
          className={value ? 'picked' : ''}
        />
        <button type="button" className="icon-button" onClick={handleSearch} disabled={loading || !query.trim()} title="검색">
          {loading ? '…' : '🔍'}
        </button>
        <button
          type="button"
          className={`icon-button${picking ? ' active' : ''}`}
          onClick={onPickOnMap}
          title={picking ? '지도에서 고르기 취소' : '지도에서 고르기'}
        >
          📍
        </button>
      </label>
      {error && <p className="error">{error}</p>}
      {open && (
        <ul className="candidates">
          {candidates.length === 0 && <li className="candidate-empty">검색 결과가 없습니다</li>}
          {candidates.map((c) => (
            <li key={c.id}>
              <button type="button" className="candidate" onClick={() => handlePick(c)}>
                <span className="candidate-name">{c.name}</span>
                <span className="candidate-address">{c.address}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default PlaceSearchInput
