// 브라우저 위치 API를 Promise로 감싼다 (localhost는 https가 아니어도 동작한다)
// 반환: { lat, lng }, 실패하면 사용자에게 보여줄 메시지로 Error를 던진다

const ERROR_MESSAGES = {
  1: '위치 권한이 거부되었습니다. 브라우저 주소창의 사이트 설정에서 위치를 허용해 주세요.', // PERMISSION_DENIED
  2: '현재 위치를 확인할 수 없습니다.', // POSITION_UNAVAILABLE
  3: '현재 위치 확인 시간이 초과되었습니다.', // TIMEOUT
}

export function getCurrentPosition() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('이 브라우저는 위치 확인을 지원하지 않습니다.'))
      return
    }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => resolve({ lat: coords.latitude, lng: coords.longitude }),
      (err) => reject(new Error(ERROR_MESSAGES[err.code] ?? '현재 위치를 확인하지 못했습니다.')),
      // 1분 안에 받은 위치는 다시 쓰고, 10초 넘게 걸리면 포기한다
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 },
    )
  })
}
