import { useState } from 'react'
import { runLevel } from '../../api'
import type { LevelProps } from './types'
import Silhouette from './Silhouette'

/** 它把第一个数加上它自己。第 2 章的机器。 */
export function QuizLevel({ seg, sid, spec }: LevelProps) {
  const items: any[] = spec.items || []
  const [machine, setMachine] = useState<any>(null)
  const [tried, setTried] = useState(0)

  const pick = async (it: any) => {
    const r = await runLevel(sid, seg.id, String(it.id))
    setMachine(r.machine)
    setTried((n) => n + 1)
  }

  return (
    <div className="stage">
      {spec.prompt && <p className="lv-prompt">{spec.prompt}</p>}

      <div className={`machine ${machine?.wrong ? 'wrong' : ''}`}>{machine?.text || '—'}</div>

      <div className="cards">
        {items.map((it) => (
          <button key={it.id} className="card" onClick={() => pick(it)}>
            {it.a} + {it.b}
          </button>
        ))}
      </div>

      {spec.formula && (
        <p className="formula" onClick={(e) => e.currentTarget.classList.toggle('open')}>
          {spec.formula}
        </p>
      )}

      {tried >= 3 && spec.after && <p className="lv-after">{spec.after}</p>}
    </div>
  )
}

/** 它答什么都一样有把握。第 3 章的机器。 */
export function ConfidenceLevel({ seg, sid, spec }: LevelProps) {
  const items: any[] = spec.items || []
  const [picked, setPicked] = useState<any>(null)
  const [machine, setMachine] = useState<any>(null)

  const ask = async (it: any) => {
    setPicked(it)
    const r = await runLevel(sid, seg.id, String(it.id))
    setMachine(r.machine)
  }

  return (
    <div className="stage">
      {spec.prompt && <p className="lv-prompt">{spec.prompt}</p>}

      <div className="qa">
        {!picked ? (
          <p className="qa-hint">点一个问题，问问它。</p>
        ) : (
          <>
            <p className="qa-q">{picked.q}</p>
            <p className="qa-a">{machine?.text || '…'}</p>
            <div className="conf">
              <span className="conf-label">它有多确定</span>
              <div className="conf-bar">
                <i />
              </div>
              <span className="conf-val">{machine?.confidence ?? 100}%</span>
            </div>
            <p className="qa-hint">{spec.hint || '你觉得，它答得对吗？'}</p>
          </>
        )}
      </div>

      <div className="cards">
        {items.map((it) => (
          <button
            key={it.id}
            className={`card ${picked?.id === it.id ? 'active' : ''}`}
            onClick={() => ask(it)}
          >
            {it.q}
          </button>
        ))}
      </div>
    </div>
  )
}

type Target = { id: string; name: string; from?: string; fallback?: string; shape?: string }

/** 它的认识清单，就是别人贴给它的标签。第 4 章的机器。
 *
 * 关键不在「它答错」，而在**它答成什么，取决于孩子刚给它标了什么**。
 * 所以这一关必须让标签和孩子绑在一起，不能让机器自己乱猜。
 */
export function LabelLevel({ seg, sid, spec }: LevelProps) {
  const photos: any[] = spec.items || []
  const labels: string[] = spec.labels || []
  const targets: Target[] = spec.targets || []

  const [tags, setTags] = useState<Record<string, string>>({})
  const [active, setActive] = useState<string | null>(null)
  const [step, setStep] = useState<'label' | 'test'>('label')
  const [ti, setTi] = useState(0)
  const [said, setSaid] = useState<any>(null)
  const [busy, setBusy] = useState(false)

  const target = targets[ti]
  const shapeOf = (t: Target) =>
    t.shape || photos.find((p) => String(p.id) === String(t.from))?.shape || 'cat'
  const tagged = Object.values(tags).filter((v) => v && v !== '不知道').length

  const ask = async () => {
    setBusy(true)
    try {
      const r = await runLevel(sid, seg.id, target.id, { labels: tags })
      setSaid(r.machine)
    } finally {
      setBusy(false)
    }
  }

  const next = () => {
    setSaid(null)
    if (ti + 1 < targets.length) setTi(ti + 1)
    else setStep('label')
  }

  if (step === 'label') {
    return (
      <div className="stage label-stage">
        {spec.prompt && <p className="lv-prompt">{spec.prompt}</p>}

        <div className="photo-grid">
          {photos.map((p) => (
            <button
              key={p.id}
              className={`photo ${tags[p.id] ? 'tagged' : ''} ${active === p.id ? 'active' : ''}`}
              onClick={() => setActive(active === p.id ? null : p.id)}
            >
              <Silhouette shape={p.shape} />
              <span className="photo-tag">{tags[p.id] || '没标'}</span>
            </button>
          ))}
        </div>

        {active ? (
          <div className="tagbar">
            {labels.map((l) => (
              <button
                key={l}
                className={tags[active] === l ? 'on' : ''}
                onClick={() => {
                  setTags({ ...tags, [active]: l })
                  setActive(null)
                }}
              >
                {l}
              </button>
            ))}
          </div>
        ) : (
          <p className="lv-hint">点一张照片，给它标个名字。认不出的，就标「不知道」。</p>
        )}

        <button className="lv-go" disabled={tagged === 0} onClick={() => setStep('test')}>
          就这样教它 →
        </button>
      </div>
    )
  }

  return (
    <div className="stage test-stage">
      <p className="lv-prompt">{spec.test_prompt || '现在给它看这个：'}</p>

      <div className="target-card">
        <Silhouette shape={shapeOf(target)} />
        <span className="target-name">{target.name}</span>
        <span className="target-of">
          第 {ti + 1} / {targets.length}
        </span>
      </div>

      {said ? (
        <>
          <div className={`machine ${said.right ? '' : 'wrong'}`}>{said.text}</div>
          <p className="lv-because">{said.because}</p>
          <button className="lv-go" onClick={next}>
            {ti + 1 < targets.length ? '再给它看一个 →' : '回到开头，重新标一次 →'}
          </button>
        </>
      ) : (
        <button className="lv-go" disabled={busy} onClick={ask}>
          {busy ? '它在看……' : '问它这是什么 →'}
        </button>
      )}
    </div>
  )
}

/** 没有标准答案的分类。第 10 章用。 */
export function SortLevel({ seg, sid, spec }: LevelProps) {
  const items: any[] = spec.items || []
  const bins: any[] = spec.bins || []
  const [placed, setPlaced] = useState<Record<string, string>>({})
  const [done, setDone] = useState(false)
  const [counts, setCounts] = useState<Record<string, number>>({})

  const drop = async (itemId: string, binId: string) => {
    const nextPlaced = { ...placed, [itemId]: binId }
    setPlaced(nextPlaced)
    const r = await runLevel(sid, seg.id, itemId, { placed: nextPlaced })
    setCounts(r.machine.counts || {})
  }

  if (done) {
    return (
      <div className="stage sort-stage sort-done">
        <p className="lv-prompt">{spec.done_prompt || '你是这么分的。'}</p>
        <div className="sort-result">
          {bins.map((b) => (
            <div key={b.id} className="sort-col">
              <span className="sort-col-hd">
                {b.label} · {counts[b.id] ?? 0}
              </span>
              {items
                .filter((it) => placed[it.id] === b.id)
                .map((it) => (
                  <span key={it.id} className="sort-item">
                    {it.label}
                  </span>
                ))}
            </div>
          ))}
        </div>
        <p className="lv-because">{spec.footnote || '没有标准答案。'}</p>
      </div>
    )
  }

  return (
    <div className="stage sort-stage">
      {spec.prompt && <p className="lv-prompt">{spec.prompt}</p>}
      <div className="sort-grid">
        {items.map((it) => (
          <div key={it.id} className="sort-row">
            <span className="sort-label">{it.label}</span>
            <div className="sort-btns">
              {bins.map((b) => (
                <button
                  key={b.id}
                  className={placed[it.id] === b.id ? 'on' : ''}
                  onClick={() => drop(it.id, b.id)}
                >
                  {b.short || b.label}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
      {Object.keys(placed).length >= items.length && (
        <button className="lv-go" onClick={() => setDone(true)}>
          看看我是怎么分的 →
        </button>
      )}
    </div>
  )
}

/** 几条线就能把它带偏，而且改口时一样确定。第 5 章的机器。
 *
 * 这一关的重点不是「它错了」，是「它改口的那一下，你根本看不出它犹豫」。
 * 所以确定程度要一直显示，而且一直是九十多。
 */
export function StripesLevel({ seg, sid, spec }: LevelProps) {
  const [n, setN] = useState(0)
  const [m, setM] = useState<any>(null)
  const max = Number(spec.max || 6)
  const base = spec.base || '猫'

  const go = async (k: number) => {
    const clamped = Math.max(0, Math.min(max, k))
    setN(clamped)
    const r = await runLevel(sid, seg.id, '', { stripes: clamped })
    setM(r.machine)
  }

  return (
    <div className="stage stripes-stage">
      {spec.prompt && <p className="lv-prompt">{spec.prompt}</p>}

      <div className="stripe-photo">
        <Silhouette shape={spec.shape || 'cat'} />
        <svg className="stripes" viewBox="0 0 100 100" aria-hidden="true">
          {Array.from({ length: n }).map((_, i) => (
            <line
              key={i}
              x1={34 + i * 12}
              y1={6}
              x2={20 + i * 12}
              y2={94}
              stroke="#cbb69a"
              strokeWidth="3.4"
              strokeLinecap="round"
            />
          ))}
        </svg>
      </div>

      <div className="stripe-ctl">
        <button onClick={() => go(n - 1)} disabled={n === 0}>
          减一道
        </button>
        <span className="stripe-count">{n} 道</span>
        <button onClick={() => go(n + 1)} disabled={n >= max}>
          加一道
        </button>
      </div>

      <div className={`machine ${m && m.label !== base ? 'wrong' : ''}`}>{m ? m.label : '—'}</div>

      {m ? (
        <p className="lv-because">
          它有多确定：{m.confidence}%
          {m.flipped ? ' · 就在刚才，它改口了' : ''}
        </p>
      ) : (
        <p className="lv-hint">先加一道线试试。</p>
      )}
    </div>
  )
}

/** 它答的是你问的那句话。第 6 章的机器。 */
export function PromptLevel({ seg, sid, spec }: LevelProps) {
  const items: any[] = spec.items || []
  const [m, setM] = useState<any>(null)
  const [picked, setPicked] = useState<string | null>(null)

  const ask = async (it: any) => {
    setPicked(it.id)
    const r = await runLevel(sid, seg.id, it.id)
    setM(r.machine)
  }

  return (
    <div className="stage prompt-stage">
      {spec.prompt && <p className="lv-prompt">{spec.prompt}</p>}
      {spec.subject && <p className="lv-subject">{spec.subject}</p>}

      <div className="machine">{m ? m.text : '—'}</div>

      {m?.follows && <p className="lv-because">它跟着「{m.follows}」走</p>}
      {m?.note && <p className="lv-hint">{m.note}</p>}

      <div className="ask-list">
        {items.map((it) => (
          <button key={it.id} className={picked === it.id ? 'on' : ''} onClick={() => ask(it)}>
            {it.ask}
          </button>
        ))}
      </div>
    </div>
  )
}

/** 它在接龙，不是在想。第 7 章的机器。 */
export function ChainLevel({ seg, sid, spec }: LevelProps) {
  const items: any[] = spec.items || []
  const [seed, setSeed] = useState<string | null>(null)
  const [m, setM] = useState<any>(null)

  const pick = async (it: any) => {
    setSeed(it.seed)
    setM(null)
    const r = await runLevel(sid, seg.id, it.id)
    setM(r.machine)
  }

  return (
    <div className="stage chain-stage">
      {spec.prompt && <p className="lv-prompt">{spec.prompt}</p>}

      <div className="chain-box">
        <p className="chain-seed">{seed || '给它一句开头'}</p>
        <p className={`chain-out ${m && !m.true_statement ? 'untrue' : ''}`}>
          {m ? m.text : ''}
        </p>
      </div>

      {m?.note && <p className="lv-because">{m.note}</p>}

      <div className="ask-list">
        {items.map((it) => (
          <button key={it.id} className={seed === it.seed ? 'on' : ''} onClick={() => pick(it)}>
            {it.seed}
          </button>
        ))}
      </div>
    </div>
  )
}

/** 它推的是你点过的，不是你想看的。第 8 章的机器。 */
export function FeedLevel({ seg, sid, spec }: LevelProps) {
  const topics: string[] = spec.topics || []
  const goal = Number(spec.goal || 5)
  const [seen, setSeen] = useState<string[]>([])
  const [m, setM] = useState<any>(null)

  const click = async (t: string) => {
    const next = [...seen, t]
    setSeen(next)
    const r = await runLevel(sid, seg.id, '', { seen: next })
    setM(r.machine)
  }

  const top: string | null = m?.top ?? null
  const cells = top ? Array.from({ length: 12 }, () => top) : topics

  return (
    <div className="stage feed-stage">
      {spec.prompt && <p className="lv-prompt">{spec.prompt}</p>}

      <div className="feed-screen">
        {cells.map((t, i) => (
          <button
            key={i}
            className={`feed-cell ${top ? 'locked' : ''}`}
            onClick={() => !top && click(t)}
            disabled={!!top}
          >
            {t}
          </button>
        ))}
      </div>

      {top ? (
        <>
          <p className="lv-because">
            你点了 {m.total} 次，其中「{top}」有 {m.counts[top]} 次。
            <br />
            现在这一整屏，全是{top}。
          </p>
          <button
            className="lv-go"
            onClick={() => {
              setSeen([])
              setM(null)
            }}
          >
            重新点一遍 →
          </button>
        </>
      ) : (
        <p className="lv-hint">
          已经点了 {seen.length} 次 · 还差 {Math.max(0, goal - seen.length)} 次
        </p>
      )}
    </div>
  )
}

/** 它只留得住最近的几条。第 9 章的机器。 */
export function MemoryLevel({ seg, sid, spec }: LevelProps) {
  const slots = Number(spec.slots || 6)
  const facts: any[] = spec.facts || []
  const [remember, setRemember] = useState<string[]>([])
  const [m, setM] = useState<any>(null)

  const put = async (id: string) => {
    const next = [...remember, id]
    const r = await runLevel(sid, seg.id, '', { remember: next })
    setRemember(next)
    setM(r.machine)
  }

  const kept: string[] = m?.kept ?? []
  const dropped: string[] = m?.dropped ?? []
  const label = (id: string) => facts.find((f) => f.id === id)?.text || id

  return (
    <div className="stage memory-stage">
      {spec.prompt && <p className="lv-prompt">{spec.prompt}</p>}

      <div className="mem-grid">
        {Array.from({ length: slots }).map((_, i) => (
          <div key={i} className={`mem-slot ${kept[i] ? 'on' : ''}`}>
            {kept[i] ? label(kept[i]) : ''}
          </div>
        ))}
      </div>

      {dropped.length > 0 && (
        <p className="mem-dropped">掉出去了：{dropped.map(label).join('、')}</p>
      )}

      <div className="mem-facts">
        {facts.map((f) => (
          <button key={f.id} disabled={remember.includes(f.id)} onClick={() => put(f.id)}>
            {f.text}
          </button>
        ))}
      </div>

      {m?.full && <p className="lv-because">再多放一条，最早的那条就没了。</p>}
    </div>
  )
}
