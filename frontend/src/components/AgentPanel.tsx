import type { LearnState } from '../api'

type Props = {
  state: LearnState | null
  action: string
  reason: string
  engine: string
}

const LABEL: Record<string, string> = {
  untouched: '未达成',
  in_progress: '进行中',
  achieved: '已达成',
  triggered: '已触发',
  cleared: '已澄清',
}

const ACTION: Record<string, string> = {
  continue: '继续主线',
  insert: '插入补充内容',
  finish: '结束',
}

export default function AgentPanel({ state, action, reason, engine }: Props) {
  return (
    <aside className="agent">
      <div className="agent-hd">后端 agent · {engine}</div>
      <div className="agent-row">
        <span className="k">本次动作</span>
        <span className="v accent">{ACTION[action] || action}</span>
      </div>
      <div className="agent-row">
        <span className="k">理由</span>
        <span className="v">{reason || '—'}</span>
      </div>

      {!state ? (
        <p className="agent-idle">
          翻一页，它才开始判断。
          <br />
          这里的每一行都是后端算出来的。
        </p>
      ) : (
        <>
      <div className="agent-sep" />
      <div className="agent-sub">教学目标</div>
      {state &&
        Object.entries(state.goals).map(([gid, g]) => (
          <div className="agent-row" key={gid}>
            <span className="k">{gid}</span>
            <span className={`v s-${g.state}`}>{LABEL[g.state] || g.state}</span>
          </div>
        ))}

      <div className="agent-sep" />
      <div className="agent-sub">误区</div>
      {state &&
        Object.entries(state.misconceptions).map(([mid, m]) => (
          <div className="agent-row" key={mid}>
            <span className="k">{mid}</span>
            <span className={`v s-${m.state}`}>{LABEL[m.state] || m.state}</span>
          </div>
        ))}

          <div className="agent-sep" />
          <div className="agent-sub">画像</div>
          <div className="agent-row">
            <span className="k">平均停留</span>
            <span className="v">{state.profile?.dwell_avg_ms ?? 0} ms</span>
          </div>
          <div className="agent-row">
            <span className="k">连续快翻</span>
            <span className="v">{state.profile?.fast_skips ?? 0}</span>
          </div>
          <div className="agent-row">
            <span className="k">已用补充</span>
            <span className="v">{(state.profile?.used_hooks || []).join(', ') || '无'}</span>
          </div>
        </>
      )}
    </aside>
  )
}
