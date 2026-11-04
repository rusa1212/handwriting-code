import { isSamePlace } from '../lib/place'
import PlaceSearchInput from './PlaceSearchInput'

// 출발지/목적지 검색 + 검색 버튼. 상태는 RecommendPage가 가진다
// pickTarget: 지도 클릭으로 고르는 중인 칸 ('origin' | 'destination' | null)
// autoSearch: true면 (택시 모드) 장소가 정해지는 대로 부모가 검색하므로 버튼은 실패했을 때 다시 시도용으로만 보인다
function SearchPanel({ origin, destination, onOriginChange, onDestinationChange, onSwap, pickTarget, onPickTargetChange, pickLoading, onLocate, locating, onSearch, loading, error, routeCount, autoSearch = false }) {
  const samePlace = isSamePlace(origin, destination)
  const canSearch = origin && destination && !samePlace && !loading
  const showButton = !autoSearch || (error && canSearch)

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
      {showButton && (
        <button type="button" className="primary" onClick={onSearch} disabled={!canSearch}>
          {loading ? '검색 중...' : autoSearch ? '다시 검색' : '경로 검색'}
        </button>
      )}
      {autoSearch && loading && <p className="hint">택시 경로와 요금을 확인하는 중...</p>}
      {(!origin || !destination) && <p className="hint">출발지와 목적지를 검색해서 골라 주세요.</p>}
      {samePlace && <p className="hint">출발지와 목적지가 같습니다.</p>}
      {error && <p className="error">{error}</p>}
      {!error && routeCount > 0 && <p className="hint">경로 {routeCount}개를 찾았습니다.</p>}
    </section>
  )
}

export default SearchPanel
