import { useEffect, useRef, useState } from 'react'
import { runLevel } from '../../api'
import type { LevelProps } from './types'

const FILL: Record<string, string> = {
  苹果: '#6e9b4e',
  梨: '#c0564d',
  猫: '#6e9b4e',
  狗: '#c0564d',
}

function fillOf(label: string) {
  return FILL[label] || '#8a7a6a'
}

/** 它不认识这个东西，它只找最近的几个邻居投票。第 9 章的机器。
 *
 * 这一关的重点是 k ——「看几个邻居」会改变答案。
 * k=1 时最近那个说了算，容易被一个怪东西带偏；k 大了更稳，边界会糊。
 */
export function KnnLevel({ seg, sid, spec }: LevelProps) {
  const points: any[] = spec.points || []
  const queries: any[] = spec.queries || []
  const kOpts: number[] = spec.k_options || [1, 3, 5]

  const [qi, setQi] = useState(0)
  const [k, setK] = useState(kOpts[1] ?? 3)
  const [m, setM] = useState<any>(null)
  const first = useRef(true)

  const run = async (qIdx: number, kk: number) => {
    const q = queries[qIdx]
    if (!q) return
    setQi(qIdx)
    setK(kk)
    const r = await runLevel(sid, seg.id, '', { q: q.id, k: kk })
    setM(r.machine)
  }

  useEffect(() => {
    if (!first.current) return
    first.current = false
    run(0, k)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const q = queries[qi]
  const nearIds = new Set((m?.neighbors || []).map((n: any) => n.id))
  const byId = Object.fromEntries(points.map((p) => [p.id, p]))

  return (
    <div className="stage knn-stage">
      {spec.prompt && <p className="lv-prompt">{spec.prompt}</p>}

      <svg className="knn-board" viewBox="0 0 100 100" role="img" aria-label="它见过的东西和位置">
        <rect x="2" y="2" width="96" height="96" rx="3" fill="#fdf6e8" stroke="#d8c8b2" strokeWidth="0.4" />

        {q &&
          (m?.neighbors || []).map((n: any) => {
            const p = byId[n.id]
            if (!p) return null
            return (
              <line
                key={n.id}
                x1={q.x}
                y1={q.y}
                x2={p.x}
                y2={p.y}
                stroke={fillOf(n.label)}
                strokeWidth="0.6"
                strokeDasharray="2 2"
                opacity="0.75"
              />
            )
          })}

        {points.map((p) => {
          const on = nearIds.has(p.id)
          return (
            <g key={p.id}>
              <circle
                cx={p.x}
                cy={p.y}
                r={on ? 5.6 : 5}
                fill={fillOf(p.label)}
                opacity={on ? 1 : 0.42}
              />
              <text
                x={p.x}
                y={p.y + 1.7}
                fontSize="5.2"
                fill="#fffaf0"
                textAnchor="middle"
                opacity={on ? 1 : 0.8}
              >
                {p.label === '苹果' ? '苹' : p.label === '梨' ? '梨' : p.label.slice(0, 1)}
              </text>
            </g>
          )
        })}

        {q && (
          <g>
            <circle cx={q.x} cy={q.y} r="6" fill="#fffaf0" stroke="#3e2c23" strokeWidth="0.9" />
            <text x={q.x} y={q.y + 2} fontSize="6" fill="#3e2c23" textAnchor="middle">
              ?
            </text>
          </g>
        )}
      </svg>

      <div className="knn-rows">
        <div className="knn-ctl">
          <span className="knn-label">问号放在</span>
          {queries.map((qq, i) => (
            <button key={qq.id} className={qi === i ? 'on' : ''} onClick={() => run(i, k)}>
              {i + 1}
            </button>
          ))}
        </div>
        <div className="knn-ctl">
          <span className="knn-label">看几个邻居</span>
          {kOpts.map((kk) => (
            <button key={kk} className={k === kk ? 'on' : ''} onClick={() => run(qi, kk)}>
              {kk} 个
            </button>
          ))}
        </div>
      </div>

      {m ? (
        <>
          <div className="machine">{m.label}</div>
          <p className="lv-because">
            {Object.entries(m.votes)
              .map(([lb, n]) => `${lb} ${n} 票`)
              .join(' · ')}
          </p>
        </>
      ) : (
        <p className="lv-hint">等它看一眼。</p>
      )}
    </div>
  )
}
