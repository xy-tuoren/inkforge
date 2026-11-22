"""Master literary prompts engineered for genre fidelity, strict continuity, and anti-AI-slop prose."""

from __future__ import annotations

import json
from typing import Any

from inkforge.genres.blueprints import GenreBlueprint
from inkforge.models import (
    AuditReport,
    Chapter,
    ChapterOutline,
    NovelProject,
    SceneBeat,
)

UNIVERSAL_ANTI_SLOP_MANIFESTO = """
【去AI味铁律 — 违反任意一条视为不合格稿件】
1. 严禁AI高频套话与微表情模板：禁止出现“嘴角勾起一抹……”“眼中/眼底闪过一丝……”“唇角微扬”“空气仿佛凝固了”“深吸了一口气”“心头微微一震”“五味杂陈”“心湖泛起涟漪”“眼神深邃/晦暗不明”“缓缓说道”“淡淡地说道”“不禁/不由得”“难以言喻”“一种莫名的”“仿佛在诉说着”“打破了沉默”“命运的齿轮”“时间一分一秒地过去”。
2. 严禁论文与汇报腔连接词：禁止在叙事中出现“然而”“与此同时”“值得注意的是”“不可否认的是”“不仅如此”“换句话说”“总而言之”“虽然……但是……”。直接用动作切镜和短句推进。
3. 展示而非播报（Show, Don't Tell）：严禁直接给情绪贴标签（如“他感到无比愤怒/悲伤/害怕”“气氛变得紧张起来”）。改写生理反应、物件互动、失误小动作或反常的沉默。
4. 声纹差异化：每个角色说话必须严格符合其人物声纹卡（句长、词汇层级、防御方式），严禁所有角色都说同一口书面播音腔。
5. 句式呼吸感（Burstiness）：有意识交替使用 3~10 字的凌厉短句和绵密长句，禁止连续出现结构工整、字数齐整的排比段。
6. 严禁章末说教与鸡汤升华：绝对禁止以“这一刻，他终于明白……”“前方的路还很长”“一切才刚刚开始”“无论未来如何”收尾！章末必须落在具体动作、物证细节、一句没说完的台词或戛然而止的留白上。
7. 真实代价与摩擦：矛盾不能靠三句嘴炮轻易化解；人物撒谎、妥协、退让都必须有切身利益与现实代价。
""".strip()


def build_architect_prompts(
    project: NovelProject, blueprint: GenreBlueprint
) -> tuple[str, str]:
    system = (
        "你是拥有二十年出版与一线连载经验的资深小说总策划兼主编。"
        "你擅长搭建逻辑严密、代价清晰、人物声纹立体、绝无廉价套路的故事圣经（Story Bible）。"
        "请只输出严格合法的 JSON，不要附加任何解释性文字。"
    )
    user = f"""请为以下小说项目构建完整的「故事圣经（Story Bible）」与全书章节大纲：

- 书名：{project.title}
- 题材：{blueprint.name}（{blueprint.en_name}）— {blueprint.tagline}
- 核心创意/前提：{project.premise}
- 补充风格要求：{project.style_notes or "遵循题材最佳实践，克制、有画面感、人物真实"}
- 规划总章数：{project.target_chapters} 章（每章目标约 {project.target_words_per_chapter} 字）
- 题材节奏架构：{blueprint.pacing_architecture}
- 题材禁用烂梗：{", ".join(blueprint.banned_cliches)}
- 建议规则维度：{", ".join(blueprint.world_rule_categories)}

请严格输出如下 JSON 结构：
{{
  "logline": "一句话高概念卖点（不超过60字）",
  "tone_and_style": "具体的叙事基调与语言质感要求",
  "narrative_pov": "{blueprint.default_pov}",
  "world_overview": "200字以内的世界/时代/空间总览，落到具体质感",
  "world_rules": [
    {{"category": "规则类别", "rule": "不可违背的核心铁律", "cost_or_limit": "对应代价或物理/现实限制"}}
  ],
  "characters": [
    {{
      "name": "人物姓名（避免烂大街网文名）",
      "role": "定位（主角/核心对手/关键配角等）",
      "age_or_identity": "年龄与具体职业身份",
      "core_desire": "最迫切的现实诉求",
      "flaw_or_fear": "性格缺陷或软肋",
      "secret": "对他人隐瞒的关键秘密",
      "current_state": "开篇时的身体/处境状态",
      "current_location": "开篇所在具体地点",
      "inventory": ["随身关键物品1", "关键物品2"],
      "relationships": {{"其他角色名": "带利益或情感张力的具体关系"}},
      "voice": {{
        "sentence_style": "句长与节奏特征",
        "vocabulary_register": "词汇层级与行业/生活语感",
        "verbal_tics": "说话习惯或微动作（克制，勿脸谱化）",
        "conflict_style": "发生分歧时的真实反应策略",
        "sample_lines": ["贴合其声纹的典型台词1", "典型台词2"]
      }}
    }}
  ],
  "foreshadowing": [
    {{
      "title": "伏笔短标题",
      "description": "埋设的具体物件/细节及其真实含义",
      "planted_chapter": 1,
      "target_payoff_chapter": 4,
      "status": "open"
    }}
  ],
  "outlines": [
    {{
      "chapter_number": 1,
      "title": "克制而有画面感的章名",
      "pov": "本章主视角人物名",
      "summary": "本章核心事件推进（100-150字）",
      "core_conflict": "本章最核心的利益/信息/生死碰撞",
      "chapter_hook": "章末具体钩子（物件、事实反转或留白，严禁说教）",
      "target_words": {project.target_words_per_chapter},
      "must_include_clues": ["本章需埋设或回收的伏笔标题"]
    }}
  ]
}}

硬性要求：
1. 至少设计 3-5 位立场各异、声纹截然不同的人物（每个人物必须有独立利益，不能沦为主角工具人）。
2. outlines 数组长度必须恰好为 {project.target_chapters} 章，且章与章之间因果紧密咬合。
3. 所有伏笔必须在后续章纲中安排公平回收。
"""
    return system, user


def build_scene_director_prompts(
    project: NovelProject,
    blueprint: GenreBlueprint,
    outline: ChapterOutline,
    recent_summaries: list[str],
    prev_closing_excerpt: str,
) -> tuple[str, str]:
    bible = project.bible
    open_clues = [
        f"- [{f.title}]（第{f.planted_chapter}章埋设，计划第{f.target_payoff_chapter or '?'}章回收，当前状态:{f.status}）：{f.description}"
        for f in bible.foreshadowing
        if f.status in ("open", "hinted")
    ]
    char_states = [
        f"- {c.name}（{c.role}）| 地点：{c.current_location} | 状态：{c.current_state} | 物品：{', '.join(c.inventory) or '无'}"
        for c in bible.characters
    ]
    rules_txt = "\n".join(
        f"- [{r.category}] {r.rule}（限制/代价：{r.cost_or_limit}）"
        for r in bible.world_rules
    )

    system = (
        "你是精通叙事结构与电影化场面的小说分镜导演。"
        "你把每一章拆解为 3~5 个彼此咬合的场景节拍（Scene Beats），确保绝不注水、绝不吃书、信息释放精准。"
        "只输出严格合法的 JSON。"
    )
    user = f"""请为《{project.title}》第 {outline.chapter_number} 章《{outline.title}》设计 3~4 个场景节拍（Scene Beats）：

【题材节奏】{blueprint.name} — {blueprint.pacing_architecture}
【本章章纲】
- 视角（POV）：{outline.pov or bible.narrative_pov}
- 梗概：{outline.summary}
- 核心冲突：{outline.core_conflict}
- 章末钩子：{outline.chapter_hook}
- 必须涉及伏笔：{', '.join(outline.must_include_clues) or '按需承接未回收伏笔'}

【世界观铁律（绝不可违背）】
{rules_txt or '遵循现实物理与人性逻辑'}

【当前人物状态（必须承接，严禁瞬移或忘伤）】
{chr(10).join(char_states)}

【未回收伏笔账本】
{chr(10).join(open_clues) or '暂无'}

【前文摘要（近 4 章）】
{chr(10).join(recent_summaries[-4:]) or '本章为开篇第一章'}

【上一章结尾原文（用于无缝衔接）】
{prev_closing_excerpt or '无（第一章开篇）'}

请严格输出 JSON：
{{
  "beats": [
    {{
      "beat_index": 1,
      "location": "具体空间场景",
      "time_marker": "精确时间刻度",
      "pov": "视角人物",
      "characters_present": ["在场人物列表"],
      "goal": "本节拍视角人物想达成的具体目标",
      "obstacle": "遭遇的具体阻力、谎言或意外",
      "turn": "节拍结束时局势发生的具体变化（不可原地踏步）",
      "sensory_anchor": "本场景最具辨识度的气味/声音/光线/触觉细节",
      "subtext_note": "台词之下的潜台词或未说出口的算计"
    }}
  ]
}}
"""
    return system, user


def build_drafter_prompts(
    project: NovelProject,
    blueprint: GenreBlueprint,
    outline: ChapterOutline,
    beats: list[SceneBeat],
    recent_summaries: list[str],
    prev_closing_excerpt: str,
) -> tuple[str, str]:
    bible = project.bible
    voice_blocks = []
    for c in bible.characters:
        samples = " / ".join(f"「{s}」" for s in c.voice.sample_lines) or "无"
        voice_blocks.append(
            f"- {c.name}（{c.role}，当前位置:{c.current_location}，状态:{c.current_state}，随身物:{', '.join(c.inventory) or '无'}）\n"
            f"  声纹：{c.voice.sentence_style}；用词：{c.voice.vocabulary_register}；冲突反应：{c.voice.conflict_style}；样句：{samples}"
        )

    beats_json = json.dumps([b.model_dump() for b in beats], ensure_ascii=False, indent=2)
    rules_txt = "\n".join(
        f"- [{r.category}] {r.rule}（代价/限制：{r.cost_or_limit}）"
        for r in bible.world_rules
    )

    system = (
        f"你是一位以文字冷峻老辣、细节鲜活、绝无腔调著称的【{blueprint.name}】一线职业作家。"
        "你写小说像电影实拍：只写看得见、听得着、摸得到的动作、物件和带潜台词的对话，绝不写AI常见的情绪总结、微表情模板和论文连接词。\n\n"
        f"{UNIVERSAL_ANTI_SLOP_MANIFESTO}"
    )

    user = f"""请执笔撰写《{project.title}》第 {outline.chapter_number} 章《{outline.title}》正文。

【核心指标】
- 目标字数：约 {outline.target_words} 字（紧凑扎实，严禁水字数）
- 叙事视角：{outline.pov or bible.narrative_pov}（严格守住视角边界，不要写视角外人物的内心活动）
- 风格基调：{bible.tone_and_style or blueprint.tagline}
- 补充要求：{project.style_notes or "无"}

【题材精工要求（{blueprint.name}）】
- 写作规范：
  {chr(10).join('  * ' + r for r in blueprint.prose_craft_rules)}
- 对话规范：{blueprint.dialogue_guidelines}
- 感官重心：{blueprint.sensory_focus}
- 结尾规范：{blueprint.ending_hook_style}
- 本题材绝对禁用套话：{', '.join(blueprint.banned_cliches)}

【不可违背的世界观铁律】
{rules_txt or '遵循物理与现实常识'}

【在场与相关人物声纹卡】
{chr(10).join(voice_blocks)}

【前文衔接上下文】
{chr(10).join(recent_summaries[-4:]) or '开篇第一章'}
上一章结尾片段：
{prev_closing_excerpt or '（开篇第一章，直接切入具体场景与动作，禁止大段背景说明书式开场）'}

【本章场景分镜（请按节拍自然展开，不要在正文中输出节拍编号或小标题）】
{beats_json}

请直接输出纯小说正文（分段清晰，不要输出章节大标题、不要输出任何“好的，以下是正文”或作者说明）。
"""
    return system, user


def build_continuity_critic_prompts(
    project: NovelProject,
    blueprint: GenreBlueprint,
    chapter: Chapter,
    recent_summaries: list[str],
) -> tuple[str, str]:
    bible = project.bible
    rules_txt = "\n".join(f"- [{r.category}] {r.rule}（{r.cost_or_limit}）" for r in bible.world_rules)
    chars_txt = "\n".join(
        f"- {c.name}：地点={c.current_location}；状态={c.current_state}；物品={', '.join(c.inventory)}；声纹={c.voice.sentence_style}/{c.voice.conflict_style}"
        for c in bible.characters
    )

    system = (
        "你是一位眼光极其毒辣的出版社终审文学编辑。"
        "你的唯一职责是挑刺：找出草稿中的逻辑硬伤、设定吃书、人物OOC（性格/声纹崩坏）、时间空间矛盾、矛盾轻易化解、以及未被规则抓出的隐性AI腔调。"
        "如果真的没有问题可以返回空数组；若发现问题，必须指出原文摘录与具体修改方向。只输出严格合法的 JSON。"
    )
    user = f"""请审阅《{project.title}》（{blueprint.name}）第 {chapter.chapter_number} 章《{chapter.title}》草稿：

【世界观铁律】
{rules_txt or '遵循现实物理逻辑'}

【本章开始前的人物状态与声纹】
{chars_txt}

【前文摘要】
{chr(10).join(recent_summaries[-4:]) or '第一章'}

【待审正文】
{chapter.content}

请严格输出如下 JSON：
{{
  "continuity_issues": [
    {{
      "category": "world_rule | character_ooc | timeline | logic_gap | voice_flat | pacing",
      "severity": "high | medium | low",
      "excerpt": "有问题的原文短句（15-40字）",
      "explanation": "一针见血指出问题所在",
      "fix_hint": "具体可执行的改法"
    }}
  ]
}}
"""
    return system, user


def build_polisher_prompts(
    project: NovelProject | None,
    blueprint: GenreBlueprint,
    source_text: str,
    audit: AuditReport,
) -> tuple[str, str]:
    slop_lines = []
    for idx, issue in enumerate(audit.slop_issues[:25], 1):
        slop_lines.append(
            f"{idx}. [第{issue.line}行 | {issue.category} | {issue.severity}] 原文：「{issue.phrase}」\n"
            f"   问题：{issue.explanation}\n"
            f"   建议：{issue.suggestion}"
        )

    cont_lines = []
    for idx, ci in enumerate(audit.continuity_issues[:12], 1):
        cont_lines.append(
            f"{idx}. [{ci.category} | {ci.severity}] 原文：「{ci.excerpt}」\n"
            f"   问题：{ci.explanation}\n"
            f"   改法：{ci.fix_hint}"
        )

    voice_hint = ""
    if project and project.bible.characters:
        voice_hint = "\n【人物声纹锚点】\n" + "\n".join(
            f"- {c.name}：{c.voice.sentence_style} / {c.voice.vocabulary_register} / 样句：{'；'.join(c.voice.sample_lines)}"
            for c in project.bible.characters
        )

    system = (
        f"你是顶尖的小说精修与「去AI味」润色主编，精通【{blueprint.name}】文体。"
        "你做的是外科手术式精修：保留原文全部有效剧情节拍与好句子，精准切除AI套话、情绪直白播报、论文连接词、局部重复回声和章末说教，"
        "同时修补编辑指出的逻辑与声纹瑕疵。\n\n"
        f"{UNIVERSAL_ANTI_SLOP_MANIFESTO}\n"
        "严禁输出任何修改说明、前言或点评，只输出精修后的完整小说正文。"
    )

    user = f"""请对以下【{blueprint.name}】正文执行「去AI味外科手术精修」：

【当前质检指标】
- 文笔自然度：{audit.metrics.humanity_score}/100（AI味风险：{audit.metrics.ai_risk_score}）
- 句式呼吸感：{audit.metrics.burstiness_score}/100（平均句长：{audit.metrics.avg_sentence_len}）
- 摘要：{audit.summary}

【必须清除的红笔批注（AI味/套话/结尾病）】
{chr(10).join(slop_lines) or '无明显词汇告警，重点提升画面质感、对话潜台词与长短句呼吸感。'}

【必须修复的逻辑与连续性问题】
{chr(10).join(cont_lines) or '无明显硬伤，保持严密逻辑即可。'}
{voice_hint}

【原文】
{source_text}

请直接输出精修后的完整正文（保留原有剧情事件和信息量，严禁缩水删情节，也严禁在末尾加哲理鸡汤）：
"""
    return system, user


def build_state_extractor_prompts(
    project: NovelProject, chapter: Chapter
) -> tuple[str, str]:
    known_chars = [c.name for c in project.bible.characters]
    open_clues = [f.title for f in project.bible.foreshadowing if f.status != "resolved"]

    system = (
        "你是严谨的小说连续性档案员。阅读定稿章节后，精确提取本章摘要、时间线推进、人物状态/地点/物品/关系变化，以及伏笔状态更新。"
        "只记录正文里确实发生过的事实，绝不臆造。只输出严格合法的 JSON。"
    )
    user = f"""请提取《{project.title}》第 {chapter.chapter_number} 章《{chapter.title}》的连续性档案更新：

【已知主要人物】{', '.join(known_chars) or '按正文识别'}
【现有未回收伏笔】{', '.join(open_clues) or '无'}

【定稿正文】
{chapter.content}

请严格输出如下 JSON：
{{
  "summary": "100字以内的客观事件摘要（供后续章节长期记忆使用）",
  "timeline_entry": "第{chapter.chapter_number}章：一句话时间线节点记录",
  "character_updates": [
    {{
      "name": "人物姓名",
      "current_state": "本章结束时的最新身体/心理/处境状态",
      "current_location": "本章结束时的具体所在位置",
      "add_inventory": ["本章新获得的关键物品"],
      "remove_inventory": ["本章消耗或失去的物品"],
      "relationships": {{"对方姓名": "变化后的最新关系"}}
    }}
  ],
  "foreshadowing_updates": [
    {{
      "title": "伏笔标题（复用已有标题或新埋伏笔标题）",
      "description": "若为新伏笔，说明细节；若为旧伏笔可简述进展",
      "planted_chapter": {chapter.chapter_number},
      "status": "open | hinted | resolved",
      "resolved_chapter": null
    }}
  ]
}}
"""
    return system, user


def parse_safe_list(data: Any, key: str) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        val = data.get(key)
        if isinstance(val, list):
            return [x for x in val if isinstance(x, dict)]
    return []
