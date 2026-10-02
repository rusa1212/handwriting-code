// 슬라이더 순서와 이름. key는 백엔드 Weights 필드와 같다
const FACTORS = [
  { key: 'time', label: '시간' },
  { key: 'distance', label: '거리' },
  { key: 'toll', label: '통행료' },
]

// 선호도 슬라이더 3개. 값은 0~1 (0.1 단위), 상태는 RecommendPage가 가진다
// 백엔드가 합으로 나눠 계산하므로 세 값의 합이 1이 아니어도 된다
function PreferencePanel({ weights, onChange }) {
  const total = FACTORS.reduce((sum, f) => sum + weights[f.key], 0)

  return (
    <section className="panel">
      <h2>② 선호도</h2>
      {FACTORS.map((f) => (
        <label key={f.key} className="field slider">
          <span>{f.label}</span>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={weights[f.key]}
            onChange={(e) => onChange({ ...weights, [f.key]: Number(e.target.value) })}
          />
          {/* 실제로 점수에 반영되는 비중 */}
          <output className="slider-share">
            {total === 0 ? '-' : `${Math.round((weights[f.key] / total) * 100)}%`}
          </output>
        </label>
      ))}
      {total === 0 && <p className="hint">모두 0이면 세 요소를 똑같이 봅니다.</p>}
    </section>
  )
}

export default PreferencePanel
