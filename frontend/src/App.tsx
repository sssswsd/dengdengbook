import { useEffect, useRef, useState } from 'react'
import {
  createSession,
  health,
  listChapters,
  listQuestions,
  nextSegment,
  postEvent,
  type Chapter,
  type Note,
} from './api'
import { useStore } from './store'
import Page from './components/Page'
import Chat from './components/Chat'
import AgentPanel from './components/AgentPanel'
import Shelf from './components/Shelf'
import Notebook from './components/Notebook'

export default function App() {
  const { sid, page, history, action, reason, state, set } = useStore()

  const [phase, setPhase] = useState<'shelf' | 'reading'>('shelf')
  const [chapters, setChapters] = useState<Chapter[]>([])
  const [loadingShelf, setLoadingShelf] = useState(true)
  const [err, setErr] = useState<string | null>(null)
  const [engine, setEngine] = useState('—')
  const [total, setTotal] = useState(11)
  const [banner, setBanner] = useState<string | null>(null)
  const [showPanel, setShowPanel] = useState(true)
  const [notes, setNotes] = useState<Note[]>([])
  const [showNotes, setShowNotes] = useState(false)
  const [voiceOn, setVoiceOn] = useState(() => localStorage.getItem('dd.voice') === '1')

  const enterAt = useRef<number>(Date.now())

  useEffect(() => {
    ;(async () => {
      try {
        const h = await health()
        setEngine(h.agent_engine)
        setChapters(await listChapters())
      } catch (e) {
        setErr(String(e))
      } finally {
        setLoadingShelf(false)
      }
    })()
  }, [])

  /* 深链：?ch=ch05&seg=seg5_p07 直接落到某一页。演示和调试用。 */
  const jumped = useRef(false)
  useEffect(() => {
    if (jumped.current || !chapters.length) return
    const p = new URLSearchParams(location.search)
    const ch = p.get('ch')
    if (!ch) return
    jumped.current = true
    start(ch, p.get('seg'))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chapters])

  /* 朗读：每翻一页读正文。默认关闭，点右上角喇叭才开。 */
  useEffect(() => {
    if (!voiceOn || !page) return
    const text = (page.body?.lines || []).join('。')
    if (!text || !('speechSynthesis' in window)) return
    window.speechSynthesis.cancel()
    const u = new SpeechSynthesisUtterance(text)
    u.lang = 'zh-CN'
    u.rate = 0.92
    u.pitch = 1.02
    window.speechSynthesis.speak(u)
  }, [page?.id, voiceOn])

  useEffect(() => {
    localStorage.setItem('dd.voice', voiceOn ? '1' : '0')
    if (!voiceOn && 'speechSynthesis' in window) window.speechSynthesis.cancel()
  }, [voiceOn])

  const refreshNotes = async (sessionId: string) => {
    try {
      setNotes(await listQuestions(sessionId))
    } catch {
      /* 忽略 */
    }
  }

  const start = async (chapterId: string, startSeg?: string | null) => {
    try {
      if ('speechSynthesis' in window) window.speechSynthesis.cancel()
      const ch = chapters.find((c) => c.id === chapterId)
      if (ch) setTotal(ch.segment_count)
      const s = await createSession(chapterId, startSeg)
      set({
        sid: s.id,
        page: s.first_segment,
        history: s.first_segment ? [s.first_segment] : [],
        action: 'continue',
        reason: '开场',
        state: null,
      })
      enterAt.current = Date.now()
      setBanner(null)
      setNotes([])
      setPhase('reading')
    } catch (e) {
      setErr(String(e))
    }
  }

  const next = async () => {
    if (!sid || !page) return
    const dwell = Date.now() - enterAt.current
    await postEvent(sid, 'dwell', page.id, { ms: dwell })
    const r = await nextSegment(sid, page.id)

    if (r.action === 'insert') {
      setBanner('这本书决定多讲一段 —— 刚才那一页你翻得有点快')
    } else if (r.action === 'finish') {
      setBanner('这一本读完了')
    } else {
      setBanner(null)
    }

    if (r.segment) {
      set({
        page: r.segment,
        history: [...history, r.segment],
        action: r.action,
        reason: r.reason,
        state: r.state,
      })
      enterAt.current = Date.now()
      await postEvent(sid, 'view', r.segment.id)
    } else {
      set({ action: r.action, reason: r.reason, state: r.state })
    }
  }

  const prev = () => {
    if (history.length < 2) return
    if ('speechSynthesis' in window) window.speechSynthesis.cancel()
    const h = history.slice(0, -1)
    set({ history: h, page: h[h.length - 1] })
    setBanner(null)
    enterAt.current = Date.now()
  }

  const openNotes = async () => {
    if (!sid) return
    await refreshNotes(sid)
    setShowNotes(true)
  }

  if (phase === 'shelf') {
    return <Shelf chapters={chapters} onPick={start} loading={loadingShelf} error={err} />
  }

  const progress = page?.seq ? `第 ${page.seq} / ${total} 页` : '加讲一段'

  return (
    <div className={`shell ${showPanel ? '' : 'panel-hidden'}`}>
      <div className="main">
        <div className="book">
          {page ? (
            <Page
              key={page.id}
              seg={page}
              sid={sid!}
              banner={banner}
              onBubble={(q, tag) => {
                if (sid && page) postEvent(sid, 'bubble_click', page.id, { question: q, goal_tag: tag })
              }}
            />
          ) : (
            <div className="loading">正在打开……</div>
          )}

          {showNotes && <Notebook notes={notes} onClose={() => setShowNotes(false)} />}
        </div>

        <div className="controls">
          <button className="ctl" onClick={() => setPhase('shelf')} title="回书架">
            书架
          </button>
          <button className="ctl" onClick={prev} disabled={history.length < 2}>
            ← 上一页
          </button>
          <span className="ctl-progress">{progress}</span>
          <button className="ctl primary" onClick={next}>
            下一页 →
          </button>
          <button
            className={`ctl voice ${voiceOn ? 'on' : ''}`}
            onClick={() => setVoiceOn((v) => !v)}
            title="朗读"
          >
            {voiceOn ? '🔊 朗读中' : '🔈 朗读'}
          </button>
          <button className="ctl notes" onClick={openNotes}>
            小本子{notes.length > 0 ? ` (${notes.length})` : ''}
          </button>
        </div>
      </div>

      <div className="side">
        {showPanel ? (
          <>
            <AgentPanel state={state} action={action} reason={reason} engine={engine} />
            <Chat
              sid={sid!}
              segId={page?.id ?? null}
              onAnswered={(inScope) => {
                if (!inScope && sid) refreshNotes(sid)
              }}
            />
          </>
        ) : null}
        <button className="panel-toggle" onClick={() => setShowPanel((v) => !v)}>
          {showPanel ? '收起右侧' : '看 agent 判断'}
        </button>
      </div>
    </div>
  )
}
