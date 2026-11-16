"""决策规则。全部是确定性代码，可单测、可解释、可回放。

**这里不认识任何具体的片段 id。**
它只根据「这一页是不是关键页」「它的 goal_tag 是什么」「还有哪些牌没打过」来做判断。
所以换一章内容、加一个故事，规则一行都不用改。

想加一条教学策略，就往 decide 里加一条 if——不需要重训任何东西，也不需要问模型。
"""

SKIP_THRESHOLD_MS = 3500  # 低于这个时长，判定为"翻过去了"
FAST_SKIP_LIMIT = 3  # 连续快速翻页达到几次，认为跑偏了


def _pick_hook(hooks: list[dict], goal: str | None, used: set[str]) -> dict | None:
    """挑一张「针对同一个目标、还没打过」的牌。"""
    for h in hooks:
        if h["id"] in used:
            continue
        if goal is None or h.get("goal") in (goal, None):
            return h
    return None


def decide(ctx: dict) -> dict:
    """ctx 需要的字段见 nodes.decide。返回 {action, target, reason}。

    action:
      continue —— 按主线往下走
      insert   —— 插一段补充内容（agent 手里的牌）
    """
    dwell = int(ctx.get("last_dwell_ms") or 0)
    fast = int(ctx.get("fast_skips") or 0)
    used = set(ctx.get("used_hooks") or [])
    misc = ctx.get("misconceptions") or {}
    hooks = ctx.get("hooks") or []
    goal = ctx.get("goal_tag")
    is_checkpoint = bool(ctx.get("is_checkpoint"))
    title = ctx.get("title") or "这一页"

    # 规则 1：关键页翻得太快 → 找一个针对同一目标的补充牌重讲
    if is_checkpoint and dwell and dwell < SKIP_THRESHOLD_MS:
        hook = _pick_hook(hooks, goal, used)
        if hook:
            return {
                "action": "insert",
                "target": hook["id"],
                "reason": f"「{title}」只停了 {dwell}ms（<{SKIP_THRESHOLD_MS}ms），判定为快速翻过，换一段重讲",
            }

    # 规则 2：检测到「它是故意的」这个误区 → 追问一次
    m2 = (misc.get("M2") or {}).get("state")
    if m2 == "triggered":
        hook = next((h for h in hooks if h["id"] not in used and "probe" in h["id"]), None)
        if hook is None:
            hook = _pick_hook(hooks, goal, used)
        if hook:
            return {
                "action": "insert",
                "target": hook["id"],
                "reason": "孩子认为机器是故意的（误区 M2），插一段追问，不直接否定",
            }

    # 规则 3：连续快速翻页 ≥3 次 → 把他拉回来重看
    if fast >= FAST_SKIP_LIMIT:
        hook = next((h for h in hooks if h["id"] not in used and "review" in h["id"]), None)
        if hook:
            return {
                "action": "insert",
                "target": hook["id"],
                "reason": f"连续 {fast} 次快速翻页，判定为跟丢，拉回来重看",
            }

    # 默认：继续主线。
    # 不判断"是不是最后一段"——那等于把页码写死。由 select 节点查有没有下一段。
    return {
        "action": "continue",
        "target": None,
        "reason": f"停留 {dwell}ms，判断跟得上，安静推进",
    }
