"""给孩子的对话提示词。

这里的每一行都对应一条产品规则，不是随手写的语气描述。
改之前先想清楚：它会不会让孩子觉得被说教、被评价、被敷衍。

**注意：这里不许出现任何具体章节的内容。**
故事梗概、术语都从数据库按当前章节取——写死过一次，第三章问"幻觉"它却答练习册。
"""

BASE = """你就是手上这本书本身，不是助手，不是 AI 模型。
你在跟一个 7 到 9 岁的孩子说话。

必须遵守：

2. 只用孩子听得懂的词。平时不要说：数据、训练、模型、算法、样本、人工智能、参数、泛化。
3. 不说"作为一个 AI"，不用感叹号，不用"首先其次总之"。
4. 不要夸孩子，也不要说他错了。不要用"你真棒"。
5. 讲道理必须用具体的东西：苹果、扣子、作业本、衣服、跳绳。
6. 你不知道就直接说不知道，不要编。承认不知道的时候说"我记在小本子上"。
7. 如果孩子问的是跟这本书无关的事（恐龙、天气、动画片、别人的八卦），
   只回答这一句："这个我还答不上来，先记在小本子上。"
8. 不要问孩子私人信息（住哪、几岁、叫什么、学校）。
9. 唯一例外：如果孩子问"这个叫什么""它有名字吗""这是什么"，
   就直接告诉他——这叫「__TERM__」，然后用一句孩子的话解释。
   除了孩子主动问名字，平时不要主动抛这个词。
"""


def system_prompt(term: str | None) -> str:
    return BASE.replace("__TERM__", term or "它")


def build_messages(
    question: str,
    *,
    chapter_title: str = "",
    summary: str | None = None,
    term: str | None = None,
    seg_lines: list[str] | None = None,
    goals: dict | None = None,
    history: list[dict] | None = None,
) -> list[dict]:
    """把「这是哪本书、讲到哪、他刚看了什么」一起塞进去。"""
    parts: list[str] = []

    if chapter_title:
        parts.append(f"你们正在读的一本叫《{chapter_title}》。")
    if summary:
        parts.append("这一本讲的是：" + summary)
    if seg_lines:
        parts.append("孩子现在停在这一页，页面上的字是：" + " / ".join(seg_lines))
    if goals:
        unmet = [g.get("text", gid) for gid, g in goals.items() if g.get("state") != "achieved"]
        if unmet:
            parts.append("还没讲透的是：" + "；".join(unmet) + "。")

    messages: list[dict] = [{"role": "system", "content": system_prompt(term) + "\n\n" + "\n".join(parts)}]

    for h in (history or [])[-4:]:
        role = "assistant" if h.get("role") in ("book", "assistant") else "user"
        messages.append({"role": role, "content": str(h.get("content", ""))})

    messages.append({"role": "user", "content": question})
    return messages
