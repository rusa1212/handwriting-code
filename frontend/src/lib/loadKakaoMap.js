// 카카오맵 SDK를 한 번만 불러오고, 이후에는 같은 Promise를 재사용한다
let sdkPromise = null

export function loadKakaoMap() {
  if (sdkPromise) return sdkPromise

  const key = import.meta.env.VITE_KAKAO_MAP_KEY
  if (!key) {
    return Promise.reject(
      new Error('VITE_KAKAO_MAP_KEY가 없습니다. frontend/.env.local을 확인하세요.'),
    )
  }

  sdkPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    // autoload=false: 스크립트 로드 후 kakao.maps.load()로 직접 초기화
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${key}&autoload=false`
    script.onload = () => window.kakao.maps.load(() => resolve(window.kakao))
    script.onerror = () => {
      sdkPromise = null
      reject(new Error('카카오맵 SDK를 불러오지 못했습니다.'))
    }
    document.head.appendChild(script)
  })

  return sdkPromise
}
