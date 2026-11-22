"""Deeply engineered genre blueprints for 10 major fiction categories.

Each blueprint encodes narrative pacing, voice expectations, sensory anchors,
conflict rules, dialogue ratio targets, and genre-specific anti-cliché bans so
different genres never collapse into the same generic LLM voice.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GenreBlueprint:
    id: str
    name: str
    en_name: str
    tagline: str
    default_pov: str
    default_words_per_chapter: int
    dialogue_ratio_range: tuple[float, float]
    pacing_architecture: str
    prose_craft_rules: list[str]
    dialogue_guidelines: str
    sensory_focus: str
    ending_hook_style: str
    world_rule_categories: list[str]
    banned_cliches: list[str] = field(default_factory=list)
    sample_premise: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "en_name": self.en_name,
            "tagline": self.tagline,
            "default_pov": self.default_pov,
            "default_words_per_chapter": self.default_words_per_chapter,
            "dialogue_ratio_range": list(self.dialogue_ratio_range),
            "pacing_architecture": self.pacing_architecture,
            "prose_craft_rules": self.prose_craft_rules,
            "dialogue_guidelines": self.dialogue_guidelines,
            "sensory_focus": self.sensory_focus,
            "ending_hook_style": self.ending_hook_style,
            "world_rule_categories": self.world_rule_categories,
            "banned_cliches": self.banned_cliches,
            "sample_premise": self.sample_premise,
        }


GENRE_BLUEPRINTS: dict[str, GenreBlueprint] = {
    "suspense": GenreBlueprint(
        id="suspense",
        name="悬疑推理",
        en_name="Suspense & Mystery",
        tagline="公平线索、时间线咬合、克制白描与信息差反转",
        default_pov="第三人称限知视角（紧贴调查者或当事人，严禁上帝视角剧透）",
        default_words_per_chapter=2800,
        dialogue_ratio_range=(0.22, 0.55),
        pacing_architecture=(
            "每章遵循「异常细节切入 → 证言/物证交叉碰撞 → 局部假设被推翻 → 留出具体物证或时间矛盾钩子」。"
            "所有关键真相必须提前至少两章埋入公平线索，绝不允许结局凭空掏出未铺垫的新证据。"
        ),
        prose_craft_rules=[
            "用具体物证、时间刻度、空间动线和反常举止制造紧张，严禁直接写“气氛很诡异”“他感到毛骨悚然”。",
            "每个人撒谎都必须有自洽的切身动机，配角不是用来给主角递话的木偶。",
            "审讯与访谈场景必须有潜台词：角色回避的问题往往比回答的问题更重要。",
        ],
        dialogue_guidelines="问答简洁、带试探与停顿；警察/法医/市民/嫌犯的用词层级和防备心必须截然不同。",
        sensory_focus="光线明暗、潮湿/消毒水/铁锈气味、时钟刻度、指纹/划痕/账单等微观物证。",
        ending_hook_style="以一条推翻前文判断的具体事实、电话挂断声或物件错位收尾，严禁哲理感慨。",
        world_rule_categories=["时间线", "空间与不在场证明", "物证链", "人物隐秘动机"],
        banned_cliches=[
            "原来凶手是双重人格",
            "一切都是一场梦",
            "空气仿佛凝固了",
            "冷汗顺着脊背滑落",
            "敏锐的直觉告诉他",
            "真相只有一个",
        ],
        sample_premise="南方梅雨季，老城区一家通宵药房停电十五分钟，次日清晨老板死在反锁的库房里，账本少了一页，而昨晚最后一个买安眠药的客人正是失踪三年的前刑警。",
    ),
    "xianxia": GenreBlueprint(
        id="xianxia",
        name="东方玄幻 / 仙侠",
        en_name="Xianxia & Eastern Fantasy",
        tagline="力量有代价、因果有回响、宗门博弈与去水文爽感",
        default_pov="第三人称限知视角",
        default_words_per_chapter=3000,
        dialogue_ratio_range=(0.20, 0.52),
        pacing_architecture=(
            "以「资源/生存危机 → 破局筹谋（非无脑硬莽） → 境界或手段显露的克制反杀 → 牵出更大因果与利益链」推进。"
            "杜绝原地水字数和重复打脸，每次冲突都要改变主角的资源、立场或人际账本。"
        ),
        prose_craft_rules=[
            "修炼与斗法必须写出具体的代价、破绽与地利博弈，严禁光靠“大喝一声灵气暴涨”糊弄战斗。",
            "写出修真界真实的柴米油盐与权力结构：灵石税收、丹药折损、宗门派系、凡人视角。",
            "半白话带古典质地即可，避免过度堆砌生僻辞藻和现代网文口水梗混杂。",
        ],
        dialogue_guidelines="老怪惜字如金、散修世故谨慎、世家子弟体面里藏傲慢；严禁所有反派都只会喊“找死/蝼蚁”。",
        sensory_focus="灵气压迫导致的耳鸣/寒意、丹炉焦香、旧符纸质感、山风与血腥气。",
        ending_hook_style="以新变数降临、底牌消耗后的隐患、或势力棋局悄然翻面收束。",
        world_rule_categories=["境界与代价", "功法与法器限制", "宗门与经济体系", "因果禁忌"],
        banned_cliches=[
            "莫欺少年穷",
            "恐怖如斯",
            "倒吸一口凉气",
            "蝼蚁安敢",
            "此子断不可留",
            "眼中闪过一丝杀意",
            "嘴角勾起一抹冷笑",
        ],
        sample_premise="大宗门废徒守着一座快灵气枯竭的旧药园，靠修复残缺古丹方替山下凡人治怪病糊口，却在一次采药时撞见重伤坠落的执剑长老——对方怀里揣着宗门灭门的真正账册。",
    ),
    "scifi": GenreBlueprint(
        id="scifi",
        name="硬科幻 / 赛博朋克",
        en_name="Hard Sci-Fi & Cyberpunk",
        tagline="技术公理自洽、社会学外推、冷峻细节与人性悖论",
        default_pov="第一人称或冷峻第三人称限知视角",
        default_words_per_chapter=2800,
        dialogue_ratio_range=(0.18, 0.48),
        pacing_architecture=(
            "以「单一技术约束引发的日常故障/伦理裂缝 → 工程排查与社会暗面揭露 → 技术法则不可违背下的两难抉择」推进。"
            "科幻感来自技术渗透进柴米油盐的细节，而非大段百科全书式设定灌输。"
        ),
        prose_craft_rules=[
            "设定必须融入动作和故障排查中自然带出，单段设定说明绝不超过三句。",
            "严守物理/信息论/热力学或既定技术公理：任何“黑科技”都必须伴随延迟、能耗、维护成本或社会阶级分化。",
            "文字冷峻精准，善用工程术语、日志、界面反馈与身体感官形成反差。",
        ],
        dialogue_guidelines="工程师重数据与边界条件、公司法务绕弯避责、底层维修工直接粗粝；拒绝科幻电影译制腔。",
        sensory_focus="散热风扇低频嗡鸣、臭氧与冷却液味道、义体接口的金属温差、低重力下的失衡感。",
        ending_hook_style="以系统异常日志、一次不可逆的协议确认、或冷酷的事实真相收尾。",
        world_rule_categories=["核心技术公理", "物理与能源限制", "社会阶级与法律", "信息安全与记忆规则"],
        banned_cliches=[
            "量子波动解决一切",
            "人工智能突然觉醒了爱",
            "霓虹灯照亮了她冷峻的侧脸",
            "科技是把双刃剑",
            "人类的本质究竟是什么",
        ],
        sample_premise="近地轨道垃圾回收站的资深焊工发现一具被公司注销编号的旧维护舱，里面不仅藏着合法公民的离线记忆备份，还有一份将在七十二小时后让空间站停摆的轨道偏置指令。",
    ),
    "urban_drama": GenreBlueprint(
        id="urban_drama",
        name="都市现实 / 职场商战",
        en_name="Urban Realism & Business",
        tagline="真实利益链、饭局潜台词、行业肌理与成年人博弈",
        default_pov="第三人称限知视角",
        default_words_per_chapter=2700,
        dialogue_ratio_range=(0.28, 0.60),
        pacing_architecture=(
            "围绕「具体项目/资金/职级死线 → 桌面客套与桌下筹码交换 → 关键盟友倒戈或数据爆雷 → 代价可控的破局手筋」推进。"
            "冲突源于真实的KPI、现金流、体面与生存焦虑，而非无缘无故的恶毒反派。"
        ),
        prose_craft_rules=[
            "写职场与商业必须落到具体文件、报价、回款周期、邮件措辞和座位次序，严禁悬浮“几个亿的项目”。",
            "成年人翻脸往往很体面：多用客气话里的刀锋、未回复的消息和临时改期的会议体现冲突。",
            "保留真实城市质感：晚高峰高架、写字楼空调冷风、便利店关东煮、凌晨改完的PPT。",
        ],
        dialogue_guidelines="高度口语化且带潜台词：老板画饼留后手、甲方挑刺不直接说要降价、老同事点到为止。",
        sensory_focus="咖啡冷掉的酸味、烟灰缸、空调风声、手机震动频次、地铁玻璃里的倒影。",
        ending_hook_style="以一封措辞礼貌却致命的邮件、一条撤回的消息或饭局散场后的反转细节收尾。",
        world_rule_categories=["公司与权力架构", "财务与利益链", "行业常识红线", "人际债务账本"],
        banned_cliches=[
            "天凉王破",
            "三分钟我要他的全部资料",
            "嘴角露出一丝不易察觉的微笑",
            "职场如战场",
            "成功属于不放弃的人",
        ],
        sample_premise="一家中型医疗器械公司冲刺上市前夜，负责华东大区的资深销售总监突然被内部审计停职，而举报信里那份致命的阴阳合同，签字笔迹竟和他亲手带出的徒弟一模一样。",
    ),
    "romance_emotional": GenreBlueprint(
        id="romance_emotional",
        name="现代情感 / 克制言情",
        en_name="Contemporary Romance",
        tagline="细腻拉扯、日常物件寄情、独立人格与零工业糖精",
        default_pov="第三人称限知视角（可按章双视角交替）",
        default_words_per_chapter=2600,
        dialogue_ratio_range=(0.28, 0.58),
        pacing_architecture=(
            "以「共同任务/生活交集 → 试探与短暂靠近 → 现实差异或过往伤痕引发的退缩 → 一次不言自明的行动破冰」构建情感推进。"
            "好感必须来自具体被看见的瞬间，而不是一见钟情和强行壁咚。"
        ),
        prose_craft_rules=[
            "严禁直接播报“她心跳加速”“他深深爱上了她”，改用下意识的小动作、停顿和日常照料去呈现。",
            "两位主角都要有独立的工作、朋友与脾气，爱情是彼此世界碰撞出的火花，不是依附。",
            "克制煽情：越是动容的时刻，文字越要平实、留白。",
        ],
        dialogue_guidelines="鲜活有来回、带轻度拌嘴与未说出口的体贴；严禁油腻土味情话和播音腔深情独白。",
        sensory_focus="雨伞倾斜的角度、袖口洗衣液味道、热汤白雾、手背温度、旧照片折痕。",
        ending_hook_style="以一句没说透的回答、留下的日常物件或一次克制的靠近留白收尾。",
        world_rule_categories=["情感关系阶段", "现实阻碍与各自目标", "核心过往心结", "日常情感信物"],
        banned_cliches=[
            "女人你在玩火",
            "该死的甜美",
            "心湖泛起一阵涟漪",
            "眼眶瞬间红了",
            "空气中弥漫着暧昧的气息",
            "嘴角勾起一抹宠溺的笑",
        ],
        sample_premise="旧书店修复师与负责拆迁评估的建筑师因一栋民国老宅的留存争议针锋相对，却在共同整理阁楼遗留书信的过程中，撞见两家上一代从未提起过的旧渊源。",
    ),
    "historical": GenreBlueprint(
        id="historical",
        name="历史权谋 / 架空争霸",
        en_name="Historical & Court Intrigue",
        tagline="礼法制度、钱粮后勤、庙堂暗流与半白话厚重感",
        default_pov="第三人称限知或群像视角",
        default_words_per_chapter=3000,
        dialogue_ratio_range=(0.24, 0.52),
        pacing_architecture=(
            "围绕「一桩具体政务/税赋/军情案 → 朝堂与地方利益盘根错节 → 借力打力的阳谋布局 → 牵一发而动全身的余波」展开。"
            "权谋的本质是算账（人头、粮草、名分、法理），不是全员降智衬托主角聪明。"
        ),
        prose_craft_rules=[
            "尊重古代交通、传信速度、粮草损耗与宗法礼制，不可用现代行政思维硬套。",
            "语言取法明清白话与现代精炼叙事之平衡：沉着、有分寸，绝不用半吊子文言堆砌和现代网络热词。",
            "每个大臣/小吏都在为家族、前程或理念盘算，没有脸谱化的纯粹奸臣。",
        ],
        dialogue_guidelines="讲究身份称谓、话留三分、借古喻今；小吏油滑务实，清流重名节辞锋利，勋贵直爽中带骄矜。",
        sensory_focus="烛泪、朱批墨香、冬日炭火与穿堂风、官靴踩在青砖上的脚步声、陈米霉味。",
        ending_hook_style="以一封八百里加急密报、御笔未落的一点朱砂、或旁观者的一句轻叹收尾。",
        world_rule_categories=["官制与法度", "财政与军粮约束", "地理与通讯时差", "朝堂派系谱系"],
        banned_cliches=[
            "本王饶不了你",
            "眼神深邃如寒潭",
            "眼中闪过一抹精光",
            "命运的齿轮开始转动",
            "历史的车轮滚滚向前",
        ],
        sample_premise="隆冬腊月，漕运总督衙门一名七品核账主事发现十万石赈灾粮账面严丝合缝，唯独运河沿岸三座渡口的船夫工钱少了三成——顺着这笔小账查下去，却直指东宫与江南织造的暗账。",
    ),
    "horror_weird": GenreBlueprint(
        id="horror_weird",
        name="中式民俗恐怖 / 规则怪谈",
        en_name="Folk Horror & Weird Fiction",
        tagline="日常异化、规则边界、民俗肌理与留白式寒意",
        default_pov="第一人称或贴身第三人称限知视角",
        default_words_per_chapter=2600,
        dialogue_ratio_range=(0.16, 0.44),
        pacing_architecture=(
            "以「寻常生活里的微小错位 → 发现隐性忌讳/规则条文 → 有人触犯代价显形 → 在规则缝隙中求生并窥见更大真相」推进。"
            "最高级的恐怖是“不对劲却说不清”，而非廉价的血浆和突然扑脸。"
        ),
        prose_craft_rules=[
            "越写诡异之事，语气越要冷静、笃定、像在记录普通家常，切忌连用感叹号和“恐怖至极”。",
            "民俗/规则必须有严密的内部逻辑与因果代价，主角破局靠观察细节和守/用规则，不靠临时开挂。",
            "多用具体声响、光影错位、数量不对（比如照片多出半只手、楼梯多出一级）制造寒意。",
        ],
        dialogue_guidelines="乡人忌讳多、话说到一半戛然而止；当事人在高压下会强装镇定说些不合时宜的琐事。",
        sensory_focus="线香冷灰味、潮湿墙皮、老式挂钟滴答、昏黄白炽灯频闪、耳畔细微摩擦声。",
        ending_hook_style="以一条看似平常却细思极恐的事实核对收尾，把余悸留给读者脑补。",
        world_rule_categories=["显性规则条文", "隐藏禁忌与代价", "民俗器物效用", "安全区边界"],
        banned_cliches=[
            "一股寒意从脚底直冲天灵盖",
            "毛骨悚然",
            "空气瞬间降至冰点",
            "发出凄厉的惨叫",
            "鲜血淋漓",
        ],
        sample_premise="返乡替祖父守灵的第三夜，族里老人再三叮嘱：半夜听见院门外有人喊你的乳名千万别应，若长明灯灭了也别自己去点——可午夜两点，手机却收到祖父生前号码发来的一条语音。",
    ),
    "light_comedy": GenreBlueprint(
        id="light_comedy",
        name="轻喜剧 / 脑洞日常",
        en_name="Light Comedy & High-Concept Slice of Life",
        tagline="反差萌感、一本正经的荒诞、精准留白与暖意底色",
        default_pov="第一人称或轻快第三人称视角",
        default_words_per_chapter=2400,
        dialogue_ratio_range=(0.32, 0.65),
        pacing_architecture=(
            "以「离谱前提下的认真执行 → 信息差引发的连环误会升级 → 荒诞逻辑闭环的爆笑反转 → 轻松微暖的日常落点」推进。"
            "喜剧的核心是人物极其认真地对待一件荒诞的事，绝不能自己拼命咯吱读者笑。"
        ),
        prose_craft_rules=[
            "包袱靠反差、节奏停顿和一本正经的陈述抖出来，严禁强行堆砌过时网络烂梗和哈哈大笑旁白。",
            "荒诞设定一旦立下就必须严格遵守，用现实生活中的琐碎细节（物业费、社保、早高峰）去碰撞奇幻设定。",
            "对话短促机锋，留给读者自己会心一笑的空间。",
        ],
        dialogue_guidelines="吐槽精准简短、答非所问制造喜剧节奏；切忌长篇大论解释笑点。",
        sensory_focus="烟火气小物件、菜市场喧嚣、外卖塑料袋声响、一脸严肃的滑稽微动作。",
        ending_hook_style="以一个神转折补刀或荒诞日常的新麻烦轻松落幕。",
        world_rule_categories=["核心脑洞设定", "日常现实约束", "角色反差人设", "误会信息差账本"],
        banned_cliches=[
            "令人捧腹大笑",
            "啼笑皆非",
            "脸上挂满黑线",
            "空气中飘过一群乌鸦",
            "不禁笑出声来",
        ],
        sample_premise="失业策划误租了一套月租只要八百的凶宅，入住第一晚就发现屋里住着一只因为生前没交够十五年社保、死活不肯去投胎的民国会计鬼，一人一鬼被迫合伙做起了代账副业。",
    ),
    "wuxia": GenreBlueprint(
        id="wuxia",
        name="新派武侠 / 江湖侠义",
        en_name="Modern Wuxia",
        tagline="兵器分寸、江湖人情、风骨抉择与画面感打斗",
        default_pov="第三人称限知视角",
        default_words_per_chapter=2800,
        dialogue_ratio_range=(0.22, 0.50),
        pacing_architecture=(
            "以「风雪客栈/押镖/旧债重逢起势 → 试探交锋与江湖规矩博弈 → 利害与道义的寸心抉择 → 干脆利落的生死过招与余韵」推进。"
        ),
        prose_craft_rules=[
            "打斗重空间、距离、兵器重量、体力损耗与招式意图，少用花哨无意义的招式名堆砌。",
            "江湖不只是打打杀杀，还有茶钱、盘缠、官府通缉、伤药与恩怨难清的旧人。",
            "写景如白描水墨，三两笔立出氛围，收放有度。",
        ],
        dialogue_guidelines="言简意赅、带江湖切口与人物脾性，不拖泥带水。",
        sensory_focus="刀鞘摩擦声、烈酒辛辣、马蹄泥泞、风雪割面、绷带渗血。",
        ending_hook_style="以刀归鞘的静默、远去马蹄声或一封未拆的旧帖留白收尾。",
        world_rule_categories=["武学与伤势代价", "门派与江湖规矩", "官府与地理里程", "恩怨人情账"],
        banned_cliches=[
            "剑气纵横三万里",
            "嘴角溢出一丝鲜血却笑得更加张狂",
            "侠之大者为国为民（避免空洞口号）",
            "眼中精芒暴涨",
        ],
        sample_premise="押运半辈子从未失手的老镖头准备金盆洗手，却在封刀前接了最后一趟只送一只空木匣的暗镖，半路才知护送的不是宝物，而是二十年前一场灭门案里唯一活下来的哑巴证人。",
    ),
    "literary_short": GenreBlueprint(
        id="literary_short",
        name="现实主义 / 文学中短篇",
        en_name="Literary Fiction",
        tagline="冰山理论、意象贯穿、复杂人性灰区与节制余韵",
        default_pov="第一人称或自由间接引语第三人称",
        default_words_per_chapter=2500,
        dialogue_ratio_range=(0.15, 0.45),
        pacing_architecture=(
            "不依赖廉价戏剧巧合，以「日常切片 + 反复出现的具体意象 + 缓慢累积的情感裂隙 + 克制却不可逆的顿悟或沉默」组织结构。"
        ),
        prose_craft_rules=[
            "坚决执行冰山原则：把八分情绪藏在具体动作、物件和闲笔底下，绝不替读者总结主题思想。",
            "允许人物自私、怯懦、矛盾而真实，不强行大团圆或道德说教。",
            "注重汉语声韵与长短句呼吸感，删掉一切可有可无的修饰副词和廉价形容词。",
        ],
        dialogue_guidelines="生活流、略带错位感与未尽之意，人们常常谈论天气和琐事来掩饰真正的伤口。",
        sensory_focus="季节光线变迁、旧家具纹理、食物味道、远处模糊人声、身体细微疲惫。",
        ending_hook_style="落在具体意象或一个微小日常动作上，戛然而止，留出悠长余味。",
        world_rule_categories=["时代与地域背景", "核心贯穿意象", "人物心理暗线", "家庭/社会关系网"],
        banned_cliches=[
            "生活就是这样",
            "那一刻他彻底明白了人生的真谛",
            "时间会治愈一切",
            "阳光洒在身上温暖极了",
            "眼中泛起晶莹的泪花",
        ],
        sample_premise="东北老工业区拆迁前的最后一个秋天，退休钳工执意要把厂区废弃水塔上那只走了三十年的旧挂钟修好，而远在南方打工的女儿回家办房产过户，只在家里待四十八小时。",
    ),
}


def list_genres() -> list[GenreBlueprint]:
    return list(GENRE_BLUEPRINTS.values())


def get_genre(genre_id: str) -> GenreBlueprint:
    if genre_id in GENRE_BLUEPRINTS:
        return GENRE_BLUEPRINTS[genre_id]
    raise KeyError(
        f"未知题材 '{genre_id}'，可选题材: {', '.join(GENRE_BLUEPRINTS.keys())}"
    )
