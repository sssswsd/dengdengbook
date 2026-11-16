/** 第 4 章用的六个"照片"。
 *
 * 为什么是线稿不是剪影：斑马认得出的唯一依据是条纹，穿山甲是鳞片。
 * 剪影里这两样都画不出来，六张就会糊成一团，孩子连"有把握地标错"都做不到。
 *
 * 为什么不用真照片：这一关要让孩子凭印象标，标错才有意义。
 * 写「穿山甲」三个字他就不用猜了，整章的机制也就废了。
 */

type Props = { shape: string; className?: string }

const shapes: Record<string, JSX.Element> = {
  cat: (
    <>
      <ellipse cx="50" cy="68" rx="24" ry="13" />
      <circle cx="50" cy="38" r="13.5" />
      <path d="M40 28 L38 17 L48 23" />
      <path d="M60 28 L62 17 L52 23" />
      <path d="M70 72 q14 -2 10 -16" />
      <circle cx="45" cy="37" r="1.7" fill="currentColor" />
      <circle cx="55" cy="37" r="1.7" fill="currentColor" />
      <path d="M50 41 l-2.2 2.6 h4.4 z" />
      <path d="M37 41 l-8 1" />
      <path d="M37 45 l-8 3" />
      <path d="M63 41 l8 1" />
      <path d="M63 45 l8 3" />
    </>
  ),
  dog: (
    <>
      <ellipse cx="48" cy="70" rx="27" ry="14" />
      <circle cx="45" cy="33" r="14" />
      <path d="M33 26 q-12 13 -2 26" />
      <path d="M57 26 q12 13 2 26" />
      <path d="M74 66 q11 -6 7 -18" />
      <path d="M28 82 v8" />
      <path d="M68 82 v8" />
      <circle cx="39" cy="32" r="1.7" fill="currentColor" />
      <circle cx="51" cy="32" r="1.7" fill="currentColor" />
      <ellipse cx="45" cy="40" rx="4" ry="2.6" />
      <path d="M45 43 v3" />
    </>
  ),
  car: (
    <>
      <rect x="12" y="47" width="76" height="23" rx="6" />
      <path d="M27 47 L37 29 L63 29 L73 47" />
      <path d="M41 45 L44 33 L56 33 L59 45" />
      <circle cx="30" cy="72" r="9" />
      <circle cx="70" cy="72" r="9" />
    </>
  ),
  zebra: (
    <>
      <ellipse cx="44" cy="62" rx="24" ry="12" />
      <path d="M62 54 L74 30" strokeWidth="5" />
      <ellipse cx="79" cy="26" rx="8.5" ry="5.5" />
      <path d="M86 24 l6 3" />
      <path d="M74 20 l-1 -8" />
      <path d="M26 72 v18" />
      <path d="M36 74 v16" />
      <path d="M52 74 v16" />
      <path d="M62 72 v18" />
      <path d="M32 52 q3 10 0 20" />
      <path d="M42 51 q3 11 0 21" />
      <path d="M52 52 q3 10 0 20" />
      <path d="M64 50 L73 32" strokeWidth="4" />
      <circle cx="81" cy="25" r="1.4" fill="currentColor" />
    </>
  ),
  pangolin: (
    <>
      <path d="M22 72 q4 -40 34 -40 q26 0 26 32" />
      <path d="M31 60 q6 -8 13 -3" />
      <path d="M45 52 q7 -8 14 -3" />
      <path d="M60 50 q7 -6 13 1" />
      <path d="M72 58 q7 -4 11 2" />
      <path d="M22 72 q-13 4 -14 15" />
      <path d="M82 64 q6 -3 10 -6" strokeWidth="3.4" />
      <circle cx="79" cy="58" r="2" fill="currentColor" />
      <path d="M84 70 q8 3 12 0" />
    </>
  ),
  tapir: (
    <>
      <ellipse cx="52" cy="64" rx="29" ry="19" />
      <ellipse cx="44" cy="36" rx="15" ry="13" />
      <path d="M36 28 q-6 -8 1 -10" />
      <path d="M52 27 q6 -8 -1 -10" />
      <path d="M38 47 q-5 12 1 19" strokeWidth="7" />
      <path d="M31 84 v10" />
      <path d="M44 85 v9" />
      <path d="M63 85 v9" />
      <path d="M75 83 v11" />
      <path d="M80 66 q7 4 6 12" />
      <circle cx="39" cy="34" r="1.8" fill="currentColor" />
    </>
  ),
}

export default function Silhouette({ shape, className = '' }: Props) {
  return (
    <svg viewBox="0 0 100 100" className={`sil ${className}`} aria-hidden="true">
      <g
        fill="none"
        stroke="currentColor"
        strokeWidth="2.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {shapes[shape] || shapes.cat}
      </g>
    </svg>
  )
}
