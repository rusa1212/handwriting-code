import PlaceSearchInput from './PlaceSearchInput'

// 이름이 달라도 좌표가 같으면 같은 장소로 본다 (검색 결과마다 이름 표기가 다를 수 있다)
function isSamePlace(a, b) {
  return Boolean(a && b) && Math.abs(a.lat - b.lat) < 1e-6 && Math.abs(a.lng - b.lng) < 1e-6
}

// 출발지/목적지 검색 + 검색 버튼. 상태는 RecommendPage가 가진다
// pickTarget: 지도 클릭으로 고르는 중인 칸 ('origin' | 'destination' | null)
function SearchPanel({ origin, destination, onOriginChange, onDestinationChange, onSwap, pickTarget, onPickTargetChange, pickLoading, onLocate, locating, onSearch, loading, error, routeCount }) {
  const samePlace = isSamePlace(origin, destination)
  const canSearch = origin && destination && !samePlace && !loading

  return (
    <section className="panel">
      <h2>① 출발지 / 목적지</h2>
      <PlaceSearchInput
        label="출발지"
        value={origin}
        onChange={onOriginChange}
        picking={pickTarget === 'origin'}
        onPickOnMap={() => onPickTargetChange(pickTarget === 'origin' ? null : 'origin')}
      />
      <button type="button" className="link-button" onClick={onLocate} disabled={locating}>
        {locating ? '현재 위치 확인 중...' : '◎ 현재 위치를 출발지로'}
      </button>
      <button type="button" className="swap-button" onClick={onSwap} title="출발지와 목적지 바꾸기">
        ⇅
      </button>
      <PlaceSearchInput
        label="목적지"
        value={destination}
        onChange={onDestinationChange}
        picking={pickTarget === 'destination'}
        onPickOnMap={() => onPickTargetChange(pickTarget === 'destination' ? null : 'destination')}
      />
      {pickTarget && (
        <p className="hint">
          {pickLoading ? '주소 확인 중...' : `지도를 클릭해 ${pickTarget === 'origin' ? '출발지' : '목적지'}를 고르세요. (📍 다시 누르면 취소)`}
        </p>
      )}
      <button type="button" className="primary" onClick={onSearch} disabled={!canSearch}>
        {loading ? '검색 중...' : '경로 검색'}
      </button>
      {(!origin || !destination) && <p className="hint">출발지와 목적지를 검색해서 골라 주세요.</p>}
      {samePlace && <p className="hint">출발지와 목적지가 같습니다.</p>}
      {error && <p className="error">{error}</p>}
      {!error && routeCount > 0 && <p className="hint">경로 {routeCount}개를 찾았습니다.</p>}
    </section>
  )
}

export default SearchPanel
