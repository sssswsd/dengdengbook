import type { Chapter } from '../api'

type Props = {
  chapters: Chapter[]
  onPick: (id: string) => void
  loading: boolean
  error: string | null
}

const CN = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二']

/** 每章对应的 AI 概念（与后端 chapters.topic 一一对应） */
const TOPIC_CN: Record<string, string> = {
  labeling: '数据标注',
  feature: '特征',
  knn: 'k 近邻',
  overfitting: '过拟合',
  adversarial: '对抗样本',
  hallucination: '幻觉',
  cnn: 'CNN',
  rnn: 'RNN',
  transformer: 'Transformer',
  prompt: '提示词',
  recommendation: '推荐系统',
  division: '分工',
}

export default function Shelf({ chapters, onPick, loading, error }: Props) {
  return (
    <div className="shelf">
      <header className="shelf-hd">
        <h1>等等，为什么？</h1>
        <p className="shelf-sub">一本会等你读完的书 · 挑一本开始</p>
      </header>

      {error && <p className="shelf-error">后端没连上：{error}</p>}

      <div className="shelf-list">
        {loading && <p className="shelf-hint">正在取书……</p>}

        {chapters.map((c) => (
          <button key={c.id} className="book-card" onClick={() => onPick(c.id)}>
            <span className="book-cover">
              {c.cover_url ? (
                <img src={c.cover_url} alt="" />
              ) : (
                <span className="book-cover-empty">{CN[c.order_no] || c.order_no}</span>
              )}
              <span className="book-badge">第 {c.order_no} 章</span>
            </span>
            <span className="book-title">
              {c.title}
              {c.topic && TOPIC_CN[c.topic] && (
                <em className="book-concept">{TOPIC_CN[c.topic]}</em>
              )}
            </span>
            <span className="book-meta">{c.segment_count} 页 · 约 8 分钟</span>
            <span className="book-go">翻开读 →</span>
          </button>
        ))}

        {!loading && chapters.length === 0 && !error && (
          <p className="shelf-hint">书架还是空的。检查后端是否启动。</p>
        )}

        <div className="book-card soon">
          <span className="book-cover">
            <span className="book-cover-empty">…</span>
          </span>
          <span className="book-title">第二季正在画</span>
          <span className="book-meta">每一本讲一个 AI 的小秘密</span>
        </div>
      </div>
    </div>
  )
}
