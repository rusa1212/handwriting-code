import { PLACES } from '../constants'

function PlaceSelect({ label, value, onChange }) {
  return (
    <label className="field">
      <span>{label}</span>
      <select
        value={value?.name ?? ''}
        onChange={(e) => onChange(PLACES.find((p) => p.name === e.target.value))}
      >
        {PLACES.map((p) => (
          <option key={p.name} value={p.name}>
            {p.name}
          </option>
        ))}
      </select>
    </label>
  )
}

// 출발지/목적지 선택 + 검색 버튼. 상태는 RecommendPage가 가진다
function SearchPanel({ origin, destination, onOriginChange, onDestinationChange, onSearch, loading, error, routeCount }) {
  const samePlace = origin?.name === destination?.name

  return (
    <section className="panel">
      <h2>① 출발지 / 목적지</h2>
      <PlaceSelect label="출발지" value={origin} onChange={onOriginChange} />
      <PlaceSelect label="목적지" value={destination} onChange={onDestinationChange} />
      <button type="button" className="primary" onClick={onSearch} disabled={loading || samePlace}>
        {loading ? '검색 중...' : '경로 검색'}
      </button>
      {samePlace && <p className="hint">출발지와 목적지가 같습니다.</p>}
      {error && <p className="error">{error}</p>}
      {!error && routeCount > 0 && <p className="hint">경로 {routeCount}개를 찾았습니다.</p>}
    </section>
  )
}

export default SearchPanel
