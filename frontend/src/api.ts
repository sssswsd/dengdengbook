/** 后端接口封装。前端不存业务判断，只收发。 */

export type Segment = {
  id: string
  seq: number | null
  kind: string
  is_hook: number
  variant?: string | null
  title?: string | null
  goal_tag?: string | null
  image_url?: string | null
  body: any
}

export type LearnState = {
  goals: Record<string, { text: string; state: string }>
  misconceptions: Record<string, { text: string; state: string }>
  profile: Record<string, any>
}

export type NextResp = {
  action: 'continue' | 'insert' | 'finish'
  reason: string
  segment: Segment | null
  state: LearnState
}

const BASE = ''

async function j<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`)
  return res.json() as Promise<T>
}

export async function health() {
  return j<{ ok: boolean; agent_engine: string }>(await fetch(`${BASE}/api/health`))
}

export type Chapter = {
  id: string
  title: string
  subtitle?: string | null
  topic?: string | null
  order_no: number
  segment_count: number
  cover_url?: string | null
}

export async function listChapters() {
  return j<Chapter[]>(await fetch(`${BASE}/api/chapters`))
}

export type Note = { id: number; question: string; created_at: string | null }

export async function listQuestions(sid: string) {
  return j<Note[]>(await fetch(`${BASE}/api/sessions/${sid}/questions`))
}

export async function createSession(chapterId = 'ch02', startSeg?: string | null) {
  return j<{
    id: string
    chapter_id: string
    current_seg_id: string | null
    first_segment: Segment | null
  }>(
    await fetch(`${BASE}/api/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chapter_id: chapterId, start_seg: startSeg || null }),
    }),
  )
}

export async function getSession(sid: string) {
  return j<any>(await fetch(`${BASE}/api/sessions/${sid}`))
}

export async function postEvent(
  sid: string,
  type: string,
  segId: string | null,
  payload: Record<string, any> = {},
) {
  return j<any>(
    await fetch(`${BASE}/api/sessions/${sid}/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type, seg_id: segId, payload }),
    }),
  )
}

/** ★ 关键接口：下一段给什么，由后端算。 */
export async function nextSegment(sid: string, current: string | null) {
  const q = current ? `?current=${encodeURIComponent(current)}` : ''
  return j<NextResp>(await fetch(`${BASE}/api/sessions/${sid}/next${q}`))
}

export async function answerLevel(sid: string, segId: string, a: number, b: number) {
  return j<{ a: number; b: number; machine_answer: number; is_wrong: boolean; note?: string }>(
    await fetch(`${BASE}/api/sessions/${sid}/answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ seg_id: segId, a, b }),
    }),
  )
}

/** 通用关卡。机器怎么反应由内容里的 level.kind 决定。 */
export async function runLevel(
  sid: string,
  segId: string,
  itemId = '',
  action: Record<string, any> = {},
) {
  return j<{ machine: Record<string, any>; error?: string | null }>(
    await fetch(`${BASE}/api/sessions/${sid}/level`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ seg_id: segId, item_id: itemId, action }),
    }),
  )
}

export async function getState(sid: string) {
  return j<LearnState>(await fetch(`${BASE}/api/sessions/${sid}/state`))
}

/** SSE 流式提问，逐字回调。 */
export async function askStream(
  sid: string,
  question: string,
  segId: string | null,
  onDelta: (t: string) => void,
  onDone: (inScope: boolean) => void,
) {
  const res = await fetch(`${BASE}/api/sessions/${sid}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, seg_id: segId }),
  })
  if (!res.body) return
  const reader = res.body.getReader()
  const dec = new TextDecoder()
  let buf = ''
  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buf += dec.decode(value, { stream: true })
    const parts = buf.split('\n\n')
    buf = parts.pop() || ''
    for (const p of parts) {
      const line = p.trim()
      if (!line.startsWith('data:')) continue
      try {
        const obj = JSON.parse(line.slice(5).trim())
        if (obj.delta) onDelta(obj.delta)
        if (obj.done) onDone(!!obj.in_scope)
      } catch {
        /* 忽略半包 */
      }
    }
  }
}
