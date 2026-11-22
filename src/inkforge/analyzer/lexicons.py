"""Curated Chinese & English AI-slop lexicons, telling-emotion detectors, and ending cliché rules.

Each entry includes: (regex_pattern, display_label, severity, explanation, suggestion)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SlopPattern:
    pattern: str
    label: str
    category: str  # ai_cliche | telling_emotion | preachy_ending
    severity: str  # high | medium | low
    explanation: str
    suggestion: str


# ---------------------------------------------------------------------------
# Chinese AI-slop expressions (重灾区套话、微表情模板、论文连接词、廉价修辞)
# ---------------------------------------------------------------------------
CN_AI_CLICHES: list[SlopPattern] = [
    # 1. 微表情 & 身体模板（AI 写小说头号特征）
    SlopPattern(
        r"嘴角[微轻]?[微轻]?勾起一[抹丝道][^，。！？\n]{0,8}",
        "嘴角勾起一抹……",
        "ai_cliche",
        "high",
        "典型 AI 写脸模板，人物情绪被脸谱化。",
        "删除固定句式，改用具体动作、停顿或潜台词表达态度（例如“他低头吹开浮沫，没接话”）。",
    ),
    SlopPattern(
        r"(?:眼中|眼底|眸中|眸底|眼神中)(?:闪过|掠过|划过|浮现)一[丝抹道缕][^，。！？\n]{0,8}",
        "眼中闪过一丝……",
        "ai_cliche",
        "high",
        "高频 AI 微表情播报，几乎成了网文大模型指纹。",
        "改写为视线转移、手部小动作或说话语气的细微变化。",
    ),
    SlopPattern(
        r"唇角(?:微扬|上扬|勾起|轻挑)",
        "唇角微扬/勾起",
        "ai_cliche",
        "high",
        "廉价言情/AI 模板描写，过度修饰且缺乏真实感。",
        "用具体的神态或台词反差表现笑意，不必每次都特写嘴角。",
    ),
    SlopPattern(
        r"深吸了一口气|长长地?吐出一口气",
        "深吸了一口气",
        "ai_cliche",
        "medium",
        "AI 过渡情绪的万能占位符，频繁出现会让节奏发腻。",
        "换成符合当下场景的动作（如松开衣领、把烟摁灭、手指敲了两下桌面）。",
    ),
    SlopPattern(
        r"空气仿佛(?:凝固|静止|停滞|冻结)了?",
        "空气仿佛凝固了",
        "ai_cliche",
        "high",
        "极高频 AI 紧张氛围套话，空洞无画面感。",
        "改用环境里的具体声音与沉默细节（如“墙上的挂钟走过三格，没人先开口”）。",
    ),
    SlopPattern(
        r"(?:心头|心中|内心)(?:微微)?一震|如遭雷击|五味杂陈|翻江倒海",
        "心头一震/五味杂陈",
        "ai_cliche",
        "high",
        "抽象概括心理震动，属于典型的“播报而非展示”。",
        "通过瞬间的动作失误、失语或生理细节呈现冲击。",
    ),
    SlopPattern(
        r"(?:心湖|心中|心底)(?:泛起|荡起)一[阵丝圈]涟漪",
        "心湖泛起涟漪",
        "ai_cliche",
        "high",
        "陈腐抒情模板，AI 写情感场景极易触发。",
        "写一件被记住的小事或人物随后下意识的举动。",
    ),
    SlopPattern(
        r"心中的?一块大石头(?:终于)?落了地",
        "心中大石头落地",
        "ai_cliche",
        "medium",
        "高度套路化的情绪总结。",
        "用卸力动作（如靠回椅背、才发现手心全是汗）展示松弛感。",
    ),
    SlopPattern(
        r"眼神(?:深邃|锐利如刀|晦暗不明|复杂难明|骤然一冷)",
        "眼神深邃/晦暗不明",
        "ai_cliche",
        "medium",
        "AI 喜欢用空泛形容词堆砌眼神戏，读者其实看不到画面。",
        "改写人物盯着什么看、看了多久，或视线怎么避开。",
    ),
    SlopPattern(
        r"微微(?:一愣|一怔|蹙眉|皱眉|颔首|一笑|叹了口气)",
        "微微一愣/蹙眉/颔首",
        "ai_cliche",
        "medium",
        "过度使用“微微……”会显得人物动作拘谨且同质化。",
        "删去“微微”，给出明确而有个性的反应动作。",
    ),
    SlopPattern(
        r"缓缓(?:说道|开口|转身|抬起头|站起身|闭上眼)",
        "缓缓……",
        "ai_cliche",
        "medium",
        "AI 极爱让所有角色慢动作演戏，导致叙事节奏拖沓。",
        "直接写动作本身，或用具体时长/声响代替“缓缓”。",
    ),
    SlopPattern(
        r"淡淡地?(?:说道|一笑|开口|回道|瞥了一眼)",
        "淡淡地说/一笑",
        "ai_cliche",
        "medium",
        "装酷模板副词，掩盖了角色真实的语气差异。",
        "删掉副词，让台词本身和动作传达克制与冷淡。",
    ),
    # 2. 论文/说明文/翻译腔连接词（致命 AI 味来源）
    SlopPattern(
        r"(?:然而|与此同时|值得注意的是|不可否认的是|换句话说|总而言之|综上所述|显而易见的是)",
        "论文式连接词（然而/与此同时/值得注意的是等）",
        "ai_cliche",
        "high",
        "论文与汇报腔连接词闯入小说叙事，立刻出戏。",
        "直接通过场景切镜、时间推进或短句转折衔接，删掉书面连接词。",
    ),
    SlopPattern(
        r"不仅如此|不仅[^，。]{1,12}而且|虽然[^，。]{1,14}但是",
        "规整逻辑关联句（不仅……而且/虽然……但是）",
        "ai_cliche",
        "medium",
        "工整的书面关联词会让小说读起来像议论文。",
        "拆成两个自然短句，让事实自己形成转折或递进。",
    ),
    SlopPattern(
        r"宛如|犹如|仿若|恰似",
        "高频比喻词（宛如/犹如/仿若）",
        "ai_cliche",
        "low",
        "AI 容易滥用书卷气比喻词，过多使用显得浮夸。",
        "优先使用准确的白描动词，必要时用“像”或直接写实体意象。",
    ),
    SlopPattern(
        r"不禁|不由得|情不自禁地?",
        "不禁/不由得",
        "ai_cliche",
        "medium",
        "多余的心理中介词，削弱动作的直接力量。",
        "直接删除，写主语做了什么（如把“他不禁退了一步”改为“他往后退了半步”）。",
    ),
    SlopPattern(
        r"难以言喻|无法形容|说不出的|一种莫名的",
        "难以言喻/一种莫名的",
        "ai_cliche",
        "high",
        "偷懒式空泛修饰：作者写不出具体感受，就说“难以言喻”。",
        "强迫自己找出一个具体的感官或生活类比（如胃里发沉、像含了一口冷铁）。",
    ),
    SlopPattern(
        r"悄然(?:发生|改变|蔓延|降临|升起|滑落|浮现)",
        "悄然……",
        "ai_cliche",
        "medium",
        "典型 AI 抒情/氛围高频词。",
        "写变化的具体物候或迹象，去掉“悄然”。",
    ),
    SlopPattern(
        r"宛如一幅(?:画卷|流动的画)|如梦似幻|美不胜收",
        "空洞写景套话",
        "ai_cliche",
        "medium",
        "旅游宣传片式的空泛写景，没有观察者视角。",
        "只挑一两个与当下人物心境相关的具体景物来写。",
    ),
    SlopPattern(
        r"仿佛在诉说着|诉说着岁月的沧桑|承载着厚重的历史",
        "仿佛在诉说着……",
        "ai_cliche",
        "high",
        "AI 最典型的伪文学煽情句式。",
        "客观写出物件的磨损、裂痕或气味即可，别替物件抒情。",
    ),
    SlopPattern(
        r"命运的齿轮(?:开始|悄然)?转动",
        "命运的齿轮开始转动",
        "ai_cliche",
        "high",
        "全网最泛滥的 AI 剧透式套话。",
        "彻底删除，让具体事件本身驱动命运转折。",
    ),
    SlopPattern(
        r"时间一分一秒地?过去|不知过了多久",
        "时间一分一秒地过去",
        "ai_cliche",
        "low",
        "缺乏质感的时间过渡。",
        "用具体的物理变化标示时间（如烟灰烧到滤嘴、窗外路灯熄了、茶彻底凉透）。",
    ),
    SlopPattern(
        r"打破了(?:这份|原有的|令人窒息的)?(?:沉默|平静|宁静)",
        "打破了沉默/平静",
        "ai_cliche",
        "medium",
        "高频套路过渡句。",
        "直接写出那个声音或那句话即可，读者自然知道沉默被打破了。",
    ),
    SlopPattern(
        r"冷汗(?:瞬间)?(?:湿透|浸透|顺着[^，。]{1,6}滑落)",
        "冷汗顺着脊背滑落",
        "ai_cliche",
        "medium",
        "廉价紧张套话。",
        "换成具体的生理失控细节（指节发白、喉结干咽、握笔的手滑了一下）。",
    ),
]

# ---------------------------------------------------------------------------
# Telling-not-Showing emotion narration (直白播报情绪)
# ---------------------------------------------------------------------------
CN_TELLING_PATTERNS: list[SlopPattern] = [
    SlopPattern(
        r"(?:感到|觉得|心中涌起|内心充满了?)(?:一阵|一股|无比|极其|深深的)?(?:愤怒|悲伤|绝望|恐惧|开心|喜悦|愧疚|委屈|紧张|不安|失落|感动)",
        "直白情绪播报（感到一阵愤怒/悲伤/不安……）",
        "telling_emotion",
        "high",
        "直接给情绪贴标签（Tell），剥夺了读者的代入感。",
        "改为展示（Show）：写出具体的生理反应、逃避/攻击动作、或失常的语气。",
    ),
    SlopPattern(
        r"她?(?:非常|十分|极其|格外)(?:生气|难过|害怕|激动|失望|惊讶|高兴|担忧)",
        "副词+情绪标签（非常生气/极其害怕）",
        "telling_emotion",
        "medium",
        "简单粗暴的形容词堆砌，缺乏人物行为细节。",
        "用行动、物件互动或对话停顿体现情绪强度。",
    ),
    SlopPattern(
        r"气氛(?:瞬间)?变得(?:紧张|凝重|压抑|尴尬|诡异|微妙)起来",
        "气氛变得紧张/凝重起来",
        "telling_emotion",
        "medium",
        "裁判式宣布氛围，读者反而感觉不到压力。",
        "通过房间里众人的视线躲闪、动作停顿或突然的安静去营造氛围。",
    ),
]

# ---------------------------------------------------------------------------
# Preachy / Summary Ending Patterns (AI 章末鸡汤总结病)
# ---------------------------------------------------------------------------
CN_PREACHY_ENDINGS: list[SlopPattern] = [
    SlopPattern(
        r"这一刻，?[他她我][^，。！？\n]{0,12}(?:终于明白|深刻意识到|彻底懂得|清楚地知道)",
        "章末强行顿悟（这一刻，他终于明白……）",
        "preachy_ending",
        "high",
        "AI 最典型的章末升华/说教模板，破坏叙事余韵。",
        "删掉总结句，直接停在最后一个具体动作、台词或悬念事实上。",
    ),
    SlopPattern(
        r"(?:前方的路|未来的路)还很长|一切才刚刚开始|真正的(?:考验|较量|风暴|战斗)才刚刚开始",
        "章末预告式口号（一切才刚刚开始/前方的路还很长）",
        "preachy_ending",
        "high",
        "预告片旁白腔，显得廉价且刻意。",
        "直接给出下一章危机的具体苗头（一通电话、一张纸条、一道脚步声），不要喊口号。",
    ),
    SlopPattern(
        r"无论(?:未来|前方|明天)(?:发生什么|有多艰难|如何)|只要心中有光|带着这份(?:信念|勇气|温暖)",
        "章末鸡汤升华",
        "preachy_ending",
        "high",
        "高考作文式鸡汤收尾，AI 味极重。",
        "彻底删除鸡汤议论，回到角色当下要面对的现实行动。",
    ),
    SlopPattern(
        r"这(?:仅仅|不过)是个开始|谁也不知道(?:等待他们的|明天会)",
        "全知旁白剧透式收尾",
        "preachy_ending",
        "medium",
        "跳出视角强行预告，削弱沉浸感。",
        "保持在角色视角内，以具体悬念细节结束本章。",
    ),
]

# ---------------------------------------------------------------------------
# English AI-slop patterns (for EN novels)
# ---------------------------------------------------------------------------
EN_AI_CLICHES: list[SlopPattern] = [
    SlopPattern(
        r"\blet out a breath (?:he|she|they) didn't know (?:he|she|they) (?:was|were) holding\b",
        "let out a breath didn't know holding",
        "ai_cliche",
        "high",
        "Overused LLM fiction cliché.",
        "Show physical tension release through a concrete posture shift or action.",
    ),
    SlopPattern(
        r"\bsent (?:a )?shivers? down (?:his|her|their|my) spine\b",
        "sent shivers down spine",
        "ai_cliche",
        "high",
        "Stock LLM suspense cliché.",
        "Replace with a grounded sensory detail or involuntary physical reaction.",
    ),
    SlopPattern(
        r"\ba (?:testament|tapestry|symphony|mosaic) of\b",
        "testament/tapestry/symphony of",
        "ai_cliche",
        "high",
        "Classic LLM purple prose marker.",
        "Describe concrete objects and actions plainly.",
    ),
    SlopPattern(
        r"\b(?:palpable|thick) tension\b|\bair (?:was|grew) thick with\b",
        "palpable tension / air thick with",
        "ai_cliche",
        "high",
        "Abstract atmosphere cliché.",
        "Show tension through interrupted speech, posture, or ambient sound.",
    ),
    SlopPattern(
        r"\b(?:couldn't help but|a flicker of|a faint smile played on|orbs of|delved into)\b",
        "LLM stock phrase (couldn't help but / flicker of / played on)",
        "ai_cliche",
        "medium",
        "Frequent LLM phrasing that dilutes active verbs.",
        "Cut filler verbs and write the direct action.",
    ),
    SlopPattern(
        r"\b(?:moreover|furthermore|nevertheless|in conclusion|ultimately)\b",
        "Essay connector in fiction",
        "ai_cliche",
        "high",
        "Academic transition word breaks narrative immersion.",
        "Let scenes and short sentences carry contrast naturally.",
    ),
    SlopPattern(
        r"\b(?:little did (?:he|she|they) know|the journey had only just begun|whatever lay ahead)\b",
        "Preachy/preview ending cliché",
        "preachy_ending",
        "high",
        "Formulaic LLM chapter wrap-up.",
        "End on a concrete image, line of dialogue, or unresolved turn.",
    ),
]
