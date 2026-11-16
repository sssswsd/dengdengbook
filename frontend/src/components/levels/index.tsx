import type { Segment } from '../../api'
import {
  QuizLevel,
  ConfidenceLevel,
  LabelLevel,
  SortLevel,
  StripesLevel,
  PromptLevel,
  ChainLevel,
  FeedLevel,
  MemoryLevel,
} from './components'
import type { LevelProps } from './types'
import { KnnLevel } from './KnnLevel'
import { CnnLevel } from './CnnLevel'
import { RnnLevel } from './RnnLevel'

/** kind → 组件。
 *
 * 加一种玩法只需要在两边各加一处：后端 services/levels.py 的 handler、
 * 这里的一行映射。Page.tsx 和后端接口都不用动 —— 这是能往下加章的真正原因。
 */
const REGISTRY: Record<string, (p: LevelProps) => JSX.Element> = {
  arithmetic: QuizLevel,
  confidence: ConfidenceLevel,
  label: LabelLevel,
  sort: SortLevel,
  stripes: StripesLevel,
  prompt: PromptLevel,
  chain: ChainLevel,
  feed: FeedLevel,
  memory: MemoryLevel,
  knn: KnnLevel,
  cnn: CnnLevel,
  rnn: RnnLevel,
}

export default function LevelRenderer({ seg, sid }: { seg: Segment; sid: string }) {
  const spec = seg.body?.level
  if (!spec || !spec.kind) {
    return <div className="level-fallback">这一页还没有做好。</div>
  }
  const Comp = REGISTRY[spec.kind]
  if (!Comp) {
    return <div className="level-fallback">还没学会这种玩法：{spec.kind}</div>
  }
  return <Comp seg={seg} sid={sid} spec={spec} />
}

export type { LevelProps }
