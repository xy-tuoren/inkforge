"""Built-in offline multi-genre literary demo engine.

Allows zero-key end-to-end execution of the entire InkForge workflow across all 10 genres:
- Architect: builds genre-authentic Story Bible, Character Voice Cards, Foreshadowing, and Outlines
- Scene Director: breaks any chapter into grounded 4-beat scene sheets
- Drafter: produces a raw draft containing realistic subtle AI-slop tells (for Red-Pen audit demo)
- Continuity Critic: returns realistic literary editor observations
- Polisher: transforms raw draft into crisp, sensory, zero-AI-taste literary prose (S-grade!)
- State Extractor: produces accurate chapter summary & continuity state diff
"""

from __future__ import annotations

import json
import re
from typing import Any

from inkforge.genres.blueprints import GENRE_BLUEPRINTS, get_genre
from inkforge.llm.base import LLMClient

# Genre-specific handcrafted character & prose templates for rich offline demo
_GENRE_SEEDS: dict[str, dict[str, Any]] = {
    "suspense": {
        "world_overview": "九月梅雨绵绵的江南老城青禾巷，一条快拆迁的骑楼旧街夹在新城区高架和河道之间。街坊彼此知根知底，却人人捂着三年前旧厂改制时的半截旧账。",
        "rules": [
            ("时间线", "23:15 老城配电箱跳闸，23:30 恢复供电；期间整条巷子监控黑屏十五分钟。", "任何不在场证明必须精确到分钟，并受雨天步行速度限制。"),
            ("物证链", "所有关键线索必须提前在现场或证人闲谈中出现过，严禁结局凭空补证。", "未埋伏笔不得作为破案依据。"),
            ("空间限制", "康宁药房库房仅一扇铁门与一扇带防盗网的高窗，门闩自内插死。", "密室手法必须符合物理常识，无超自然解释。"),
        ],
        "characters": [
            {
                "name": "陈砚",
                "role": "主角（前刑警 / 现夜间修锁匠）",
                "age_or_identity": "36岁，三年前因证物失窃案引咎离职",
                "core_desire": "查清三年前那桩悬案背后藏着谁的手脚",
                "flaw_or_fear": "失眠成瘾、过度怀疑善意，习惯独自扛事",
                "secret": "他昨晚十一点确实去过康宁药房买药，且拿走的药盒底印着当年的证物编号",
                "current_state": "右腕旧伤逢雨作痛，睡眠不足",
                "current_location": "青禾巷康宁药房门外雨棚下",
                "inventory": ["折叠修锁工具包", "半板铝箔安眠药", "一张浸湿的旧当票"],
                "relationships": {"周明远": "旧搭档，如今互存戒心", "许秋": "药房学徒，掌握关键账页去向"},
                "voice": {
                    "sentence_style": "短句、反问居多，不废话",
                    "vocabulary_register": "市井口语夹杂零星刑事勘查术语",
                    "verbal_tics": "说话前常停半拍看对方手部",
                    "conflict_style": "直接抛事实戳漏洞，绝不抬杠",
                    "sample_lines": ["门闩是新的，灰是旧的。你再说一遍谁先撞开的门？", "别急着签字，先把你鞋底那截蓝塑料绳刮下来。"],
                },
            },
            {
                "name": "许秋",
                "role": "关键证人（药房夜班学徒）",
                "age_or_identity": "24岁，中专药学毕业，靠这份夜班替母亲攒透析费",
                "core_desire": "守住母亲治病的钱，不把自己卷进命案",
                "flaw_or_fear": "胆小怕事，撒谎时语速会不自觉加快",
                "secret": "停电那十五分钟里，他亲眼看见有人从隔壁杂货铺二楼递过来一根晾衣杆",
                "current_state": "攥着围裙边发抖，隐瞒了关键一页账本",
                "current_location": "康宁药房前厅柜台后",
                "inventory": ["沾了碘伏的帆布围裙", "撕掉半角的进货单"],
                "relationships": {"陈砚": "既怕他又不敢完全不信", "周明远": "惧怕警察盘问"},
                "voice": {
                    "sentence_style": "急促、常自我打断补解释",
                    "vocabulary_register": "年轻打工人口语，带点南方尾音",
                    "verbal_tics": "紧张时会重复“真不是我”",
                    "conflict_style": "先否认再转移话题，被拿住把柄才松口",
                    "sample_lines": ["十一点十五跳的闸，我拿手机照亮数了两遍零钱——真没进后屋。", "老板平时扣得要命，谁知道他库房里还锁着别的？"],
                },
            },
            {
                "name": "周明远",
                "role": "对立协作者（刑侦副支队长）",
                "age_or_identity": "41岁，陈砚曾经的搭档",
                "core_desire": "在市局督办限期内稳妥结案，保住当年整条线的体面",
                "flaw_or_fear": "重程序与政治安全，明知旧案有蹊跷却不敢掀桌",
                "secret": "三年前那份遗失的证物交接单上，最后经手签名有他的半个指印",
                "current_state": "熬夜后嗓音沙哑，表面客气实则紧盯陈砚动向",
                "current_location": "青禾巷警戒线内",
                "inventory": ["塑料证物袋", "一盒抽剩三根的利群"],
                "relationships": {"陈砚": "愧疚与防备交织"},
                "voice": {
                    "sentence_style": "沉稳克制，话留三分余地",
                    "vocabulary_register": "体制内办案口吻，滴水不漏",
                    "verbal_tics": "爱用“按规矩”“先把话说圆”",
                    "conflict_style": "用程序压人，软中带硬",
                    "sample_lines": ["你现在是市民陈砚，不是陈队。线外站着，别替我找麻烦。", "账本缺页归经侦和我们并案查，你把你昨晚买药的票据先交出来。"],
                },
            },
        ],
        "foreshadowing": [
            ("撕掉的第17页账本", "库房铁盒里少了一页记录非处方镇静剂异常流向的旧账。", 1, 4),
            ("铝箔药板背面的钢印", "陈砚买到的药板边缘有一道非药厂出品的刻痕编号。", 1, 3),
            ("配电箱油漆新刮痕", "巷口配电箱并非自然老化跳闸，合闸把手留有戴橡胶手套拉拽的油痕。", 2, 5),
        ],
        "raw_prose": (
            "九月的梅雨下得没完没了，青禾巷的青石板泛着冷光，宛如一幅阴沉的水墨画卷。康宁药房的卷帘门只拉起一半，警戒线在湿冷的风里轻轻晃动，空气仿佛凝固了。\n\n"
            "陈砚站在雨棚边缘，深吸了一口气，感到一阵难以言喻的不安。他右腕的旧伤在雨夜里隐隐作痛，不禁抬手按住了袖口。然而，真正让他心头微微一震的，是柜台后面那双躲闪的眼睛。\n\n"
            "“十一点十五分跳闸，十一点三十分来电。”周明远缓缓说道，眼神深邃地盯着陈砚，“值得注意的是，老板死在反锁的库房里，而你昨晚十一点零五分刚来买过安眠药。”\n\n"
            "陈砚嘴角勾起一抹冷笑，淡淡地说道：“周队，你要是怀疑我，现在就能把我带回队里录口供。”\n\n"
            "许秋站在一旁，眼中闪过一丝慌乱，他觉得非常害怕，气氛瞬间变得紧张起来。“真不是我！跳闸的时候我一直在前厅点零钱，根本没往里走！”他急促地解释道，不仅声音发抖，而且手里的抹布也掉在了地上。\n\n"
            "陈砚没有看他，目光落向库房铁门底部的门缝。门缝里卡着半截潮湿的蓝色尼龙绳头，与药房平时捆纸箱用的白色麻绳截然不同。与此同时，周明远顺着他的视线看过去，微微皱眉，伸手示意技术员取证。\n\n"
            "时间一分一秒地过去，窗外的雨势渐大，仿佛在诉说着这座老城深藏已久的秘密。陈砚低头摸了摸口袋里那板印着奇怪刻痕的安眠药，这一刻，他终于明白，三年前那桩悬案的真相绝不会就此沉寂，命运的齿轮已经开始转动，真正的较量才刚刚开始。"
        ),
        "polished_prose": (
            "九月的雨黏在青禾巷的骑楼檐口，滴了整宿都没断。康宁药房的卷帘门只掀到胸口高，黄黑警戒带吸饱了潮气，垂在门框边一动不动，只有屋里日光灯管嗡嗡发颤，把柜台上的玻璃药瓶照出几道惨白反光。\n\n"
            "陈砚缩在雨棚最外沿，右腕旧伤扯得指尖发僵。他没去碰袖口，只把伞尖抵在石阶积水里，顺着门缝往里看。\n\n"
            "屋里飘着一股隔夜碘伏混着霉湿纸箱的味道。周明远蹲在库房铁门前，捏着塑封证物袋没抬头：“十一点十五跳闸，十一点三十来电。老赵死在反锁的库房里，门闩从里头插死。你十一点零五分来买过两板安眠药，对得上吧？”\n\n"
            "“一板。”陈砚说，“他柜台下头就剩一板，还过期半个月，收了我三十八。”\n\n"
            "周明远这才站起身，肩头蹭掉一点墙灰：“按规矩，昨晚最后见过死者的都得回所里留笔录。你把票据拿出来，别让我难做。”\n\n"
            "“老赵什么时候开过小票？”陈砚把伞往墙根一靠，眼光斜过去，落在柜台后面那个穿帆布围裙的年轻人手上，“许秋，你昨晚点零钱的时候，右手大拇指上这道新口子怎么划的？”\n\n"
            "柜台后头“啪嗒”一声。许秋手里的抹布滑进塑料桶，溅起一星脏水。\n\n"
            "“裁、裁纸箱划的！”许秋咽了口唾沫，语速陡然快了半拍，“真不是我进的后屋！跳闸那会儿黑得伸手不见五指，我拿手机照亮数了两遍五毛硬币，不信你们看我微信步数——十一点十五到三十分我一步没挪！”\n\n"
            "屋里静下来。街口早点摊支铁锅的哐当声隔着雨帘传进来，闷闷的。\n\n"
            "陈砚没再追问微信步数。他往库房门口挪了半步，蹲下去，没越过地上的粉笔圈，只用修锁用的窄口镊子尖指了指门框右下角。\n\n"
            "铁门底缝里卡着半寸蓝色尼龙绳头，边缘起毛，像是被生生扯断的。药房码在墙角的那摞进货纸箱，捆的全是本色麻绳。\n\n"
            "周明远呼吸顿了一下，朝旁边技术员扬了扬下巴：“拍照，提取。还有，查隔壁杂货铺二楼阳台。”\n\n"
            "许秋的嘴唇动了动，终究没发出声，手指死死扣进围裙口袋。半角沾了黑墨水的进货单从兜口露出一截，最上面印着一行模糊的小字——“第17页”。\n\n"
            "陈砚站起身，指腹在裤兜里摩挲过那板昨晚买来的铝箔药板。背面铝皮边缘有一道极浅的斜向钢印，不是药厂批号。\n\n"
            "三年前证物室丢掉的那只铁箱，箱锁内舌上刻的也是这个号。"
        ),
    },
    "xianxia": {
        "world_overview": "灵脉渐枯的苍梧州，各大宗门靠垄断下品灵田与丹税维系开销，外门杂役与散修在灵气稀薄的边山里斤斤计较每一钱灵炭。",
        "rules": [
            ("境界与代价", "筑基以前灵力不可离体三丈，强催禁术必损经脉，需三月药浴调理。", "越阶反杀必须借地势、丹毒或法器伏笔，严禁空口爆发。"),
            ("经济法则", "一块下品灵石抵凡人百两白银，丹炉开火一次耗炭三斤，废丹率极高。", "主角每笔灵石和草药收支都要有出处。"),
        ],
        "characters": [
            {
                "name": "沈青崖",
                "role": "主角（旧药园看守 / 废脉丹徒）",
                "age_or_identity": "22岁，因经脉淤塞被发配到灵气枯竭的东坡药园",
                "core_desire": "攒够灵石替自己买齐通脉草，脱离宗门杂役籍",
                "flaw_or_fear": "算账太精、不轻易信人，对宗门高层怀有本能戒心",
                "secret": "他能凭草药烧焦后的气味分辨古丹方真伪",
                "current_state": "虎口被药锄磨出老茧，袖中藏着三枚止血灰丸",
                "current_location": "青玄宗东坡旧药园晒药坪",
                "inventory": ["崩口药锄", "半本残缺《百草火候录》", "十二枚碎灵钱"],
                "relationships": {"顾寒舟": "突降的烫手山芋", "赵管事": "常克扣药园份例的上司"},
                "voice": {
                    "sentence_style": "平实克制，带一点底层的算计与幽默",
                    "vocabulary_register": "半白话夹杂草药炮制行话",
                    "verbal_tics": "爱先问价钱或后果",
                    "conflict_style": "能用规矩和利益解决就不动手，动手必留后手",
                    "sample_lines": ["救人可以，这副七叶断续膏值三块下品灵石，长老记谁的账？", "山门里的规矩我懂，可这炉炭火烧的钱是私账。"],
                },
            },
            {
                "name": "顾寒舟",
                "role": "关键人物（重伤执剑长老）",
                "age_or_identity": "48岁，宗门戒律堂旧人，遭暗算跌境",
                "core_desire": "把怀里的宗门丹税真账送到山外巡查使手中",
                "flaw_or_fear": "傲骨太硬，不习惯向小辈低头",
                "secret": "宗门三座主灵脉其实已被掌门暗中典押给北境大族",
                "current_state": "左肩中寒霜剑气，灵力十不存一",
                "current_location": "东坡药园柴房草堆后",
                "inventory": ["断了一截的青霜剑", "油布包封的宗门账册"],
                "relationships": {"沈青崖": "从轻视转为托付性命的交易伙伴"},
                "voice": {
                    "sentence_style": "极短、冷硬，略带古意",
                    "vocabulary_register": "老牌修士的克制语调",
                    "verbal_tics": "少用感叹，多用祈使句",
                    "conflict_style": "直指要害，以筹码换取合作",
                    "sample_lines": ["闭门。门外那三个不是来收草药的。", "账册给你看一页，你就知道为什么他们宁可烧山也不放我下岭。"],
                },
            },
        ],
        "foreshadowing": [
            ("焦味异常的紫背草", "药园东北角新长出的紫背草带着铁腥气，暗示地下灵脉并非自然枯竭。", 1, 4),
            ("少盖半印的宗门账册", "账册末尾有一处朱砂印缺了一角，指向内门丹堂堂主。", 1, 5),
        ],
        "raw_prose": (
            "夕阳西下，东坡旧药园沐浴在余晖中，宛如一幅宁静的山居画卷。沈青崖挥动药锄，深吸了一口气，心中五味杂陈。三年前他经脉受损被贬到这里，不仅灵气稀薄，而且每月还要被管事克扣两成药份。\n\n"
            "突然，竹林深处传来一声重响，打破了这份宁静。沈青崖心头微微一震，不禁握紧了手里的药锄，缓缓走了过去。\n\n"
            "草丛里躺着一名白衣男子，左肩鲜血淋漓。那人抬起头，眼神深邃如寒潭，淡淡地说道：“扶我进屋，算我欠你一条命。”\n\n"
            "沈青崖眼中闪过一丝犹豫，感到非常紧张。“长老，这伤是寒霜剑气所伤，我一个外门杂役可惹不起。”\n\n"
            "白衣男子嘴角勾起一抹冷笑：“此子断不可留的话他们已经放出去了，你今天不救我，明天他们搜山同样不会留活口。”空气仿佛凝固了。\n\n"
            "然而，就在此时，山下传来了杂乱的脚步声。沈青崖知道，前方的路还很长，命运的齿轮已经悄然转动，一场席卷青玄宗的风暴才刚刚开始。"
        ),
        "polished_prose": (
            "霜降刚过，东坡药园的土硬得像晒干的锅巴。沈青崖一锄头下去，铁刃磕在石棱上震得虎口发麻，翻出来的紫背草根须发黑，闻着有股铁锈味——地底灵气又往下沉了三尺，今年交完宗门份例，怕是连过冬的炭钱都凑不齐。\n\n"
            "竹林北头忽地传来“咔嚓”一声脆响，三根碗口粗的老毛竹拦腰折断，重物滚过枯叶，一直撞到晒药棚的木柱上才停住。\n\n"
            "沈青崖没急着靠过去，先把锄头换到左手，右手摸进袖袋按住那两包生石灰，绕着竹篱斜走了五步，借着土墙挡住半边身子往里瞧。\n\n"
            "棚檐底下蜷着个穿月白剑袍的中年人。左肩衣料冻成一块紫黑硬壳，血还没淌出来就结了薄冰，断成两截的剑鞘横在膝边。\n\n"
            "“戒律堂的顾长老？”沈青崖停在三丈开外——筑基修士就算跌了境，三丈之内也能随手拧断他的脖子。\n\n"
            "顾寒舟偏过头，喘息带着细碎冰碴声，扫了一眼沈青崖腰间挂着的杂役木牌：“屋里有没有烈酒和火绒？”\n\n"
            "“烧刀子半坛，硫磺炭两斤，止血的七叶灰有三钱。”沈青崖报得极快，顿了半息，“按药堂市价，连炭带药算一块下品灵石。长老身上带灵钱了么？”\n\n"
            "顾寒舟盯着他看了两息，反手从怀里摸出一块沾血的油布包，没扔过来，只往地上一按：“外面搜山的是丹堂的人，半刻钟后就到坡口。你现在把我交出去，能领五块灵石——前提是他们不顺手灭口。”\n\n"
            "山风卷过晒药竹匾，几片干枯的黄精翻了个身。沈青崖听见山下石阶传来隐约的狗吠声，那不是猎户养的土狗，是丹堂专嗅血气的赤目犬。\n\n"
            "他弯腰拎起地上的药篓，往柴房门一指：“柴垛后头埋了半缸晒干的艾草，能盖住血腥气。先说好，救人归救人，您那块油布包里到底是什么，等狗过了坡，得翻一页给我看。”\n\n"
            "顾寒舟撑着断剑站起半寸，肩头冰壳裂开一道血线，竟笑了半声：“小滑头。进屋吧，把你那坛最劣的烧刀子拿来。”"
        ),
    },
    "scifi": {
        "world_overview": "2089 年低地球轨道（LEO）废弃物回收站“铁砧-7”，高轨公司按克计费回收太空垃圾，底层轨道焊工靠外包工分换取重力恢复舱配额。",
        "rules": [
            ("物理公理", "微重力环境下没有声音传播，一切撞击声只能通过舱体金属传导进头盔。", "战斗与维修必须遵守动量守恒与气闸减压时长。"),
            ("信息规则", "合法公民的记忆冷备份受轨道宪章加密，私自读取会触发公司遥测熔断。", "任何破解都需要物理断开外网链路。"),
        ],
        "characters": [
            {
                "name": "陆沉",
                "role": "主角（轨道回收站资深焊工）",
                "age_or_identity": "39岁，在轨工作十一年，肺部有轻微金属粉尘纤维化",
                "core_desire": "凑齐最后四百工分回地面陪女儿上初中",
                "flaw_or_fear": "习惯听命于操作手册，害怕惹事失去回地面的船票",
                "secret": "他私藏了一台报废的离线诊断终端，没有接入公司主控网",
                "current_state": "刚结束六小时舱外焊接，手套温控偏低",
                "current_location": "铁砧-7 站 4 号气闸维修间",
                "inventory": ["激光切割笔", "离线诊断板", "一枚被磨掉编号的钛合金铭牌"],
                "relationships": {"苏岚": "站内导航调度员，嘴硬心软"},
                "voice": {
                    "sentence_style": "干脆、带工科数据习惯",
                    "vocabulary_register": "航天维修行话混合底层工人口语",
                    "verbal_tics": "爱用具体数字代替模糊形容",
                    "conflict_style": "拿出日志和仪表读数说话",
                    "sample_lines": ["气闸泄压还要四分二十秒，你想死可以自己拉红把手。", "编号刮得挺干净，可铆钉是七年前东亚轨厂的公制螺纹。"],
                },
            },
            {
                "name": "苏岚",
                "role": "搭档（轨道交通调度员）",
                "age_or_identity": "31岁，星港集团外派合同工",
                "core_desire": "查明半年前失联的哥哥为何被标注为“轨道漂移失踪”",
                "flaw_or_fear": "执念太深，容易为了线索铤而走险",
                "secret": "她偷偷篡改了今天下午 4 号抓捕臂的垃圾分拣优先级",
                "current_state": "盯着雷达屏，手里转着冷掉的营养膏管",
                "current_location": "铁砧-7 主控台 B 席",
                "inventory": ["旧工牌", "手写轨道倾角草稿纸"],
                "relationships": {"陆沉": "互相试探后结成同盟"},
                "voice": {
                    "sentence_style": "语速快，逻辑清晰，偶有尖锐反问",
                    "vocabulary_register": "航控术语与干练职场口吻",
                    "verbal_tics": "下结论前习惯敲两下键盘边框",
                    "conflict_style": "直接摊开风险账本逼对方选边",
                    "sample_lines": ["别装傻，你把抓回来的那节舱体拖进盲区，工单上多出了十二分钟空白。", "七十二小时后轨道偏置点火，整座站都会掉进大气层烧成渣，你的回程票也没了。"],
                },
            },
        ],
        "foreshadowing": [
            ("多出 14 公斤的空舱体", "报废维护舱标称净重 410 公斤，机械臂称重却显示 424 公斤。", 1, 3),
            ("离线时钟快了 19 秒", "维护舱内部黑匣子时间戳与星港主网不同步。", 1, 4),
        ],
        "raw_prose": (
            "无尽的宇宙深邃而冰冷，铁砧-7空间站宛如一颗孤星悬在地球上方。陆沉脱下宇航服头盔，深吸了一口气，感到一阵难以言喻的疲惫。然而，今天的回收任务却非比寻常。\n\n"
            "他看着眼前那具残破的维护舱，心头微微一震。值得注意的是，这具舱体的外壳编号已经被彻底磨平了。与此同时，耳机里传来苏岚急促的声音：“陆沉，扫描显示里面有异常热源，气氛变得紧张起来了！”\n\n"
            "陆沉缓缓说道：“别急，我用离线终端测一下。”他不禁皱起眉头，冷汗瞬间湿透了内衬。屏幕上跳出一行红色代码——七十二小时后，空间站将执行不可逆的轨道偏置。\n\n"
            "这一刻，他终于明白，科技是把双刃剑，公司背后的阴谋远比想象中庞大，一切才刚刚开始。"
        ),
        "polished_prose": (
            "四号气闸的泄压阀尖叫着吐出最后一口氮气，仪表盘从琥珀黄跳成绿。陆沉拧开脖颈卡扣，摘下头盔，机油混着隔夜汗酸味扑了一脸。手背温控条还亮着低温警报，指节僵得像生锈的套筒。\n\n"
            "抓捕臂拖进来的那节旧维护舱悬在磁力导轨中央，外壳漆面剥得像脱皮的蛇，原本喷涂注册编号的位置被人用角磨机连铝皮带底漆削掉了一毫米。\n\n"
            "机械臂称重读数停在 424.3 公斤。\n\n"
            "陆沉抬眼扫过墙上的标准型号表。同款三级维护舱空重 410 公斤，多出来十四公斤零三百克，既不像残余燃料，也不像结冰的冷却液。\n\n"
            "通讯器里滋啦一响，苏岚的声音贴着耳膜砸进来：“陆沉，4 号盲区摄像头掉线十二分钟了。按工单你三分钟前就该把废铝压块，你在里头摸鱼？”\n\n"
            "“抓捕臂称重漂移，我在校零。”陆沉没看摄像头方向，顺手把一根绝缘胶带贴在头盔记录仪镜头上，“顺便问一句，公司哪一年把东亚轨厂的公制铆钉全换掉了？”\n\n"
            "耳麦那头静了两秒，传来指甲敲击键盘边框的轻响：“七年前。你手底下那节舱体，是不是左边焊缝有道三厘米长的斜疤？”\n\n"
            "陆沉手上的激光切割笔顿在半寸外。舱体左侧果然横着一道粗笨的补焊疤。\n\n"
            "“你改了今天的分拣队列。”他说，不是疑问句。\n\n"
            "“对。”苏岚语气干脆得像在报气象参数，“半年前我哥失联前最后一次舱外检修，用的就是这台舱。别接站内主网，用你私藏那块离线板接它的黑匣子——我只有四分钟能替你遮住遥测告警。”\n\n"
            "陆沉没问她怎么知道自己藏了离线板。他撬开舱底检修盖，三根铜针插进老式串行接口。诊断屏闪了两下雪花，没跳出预想中的生命维持日志，只滚出一串冰冷的十六进制报文，最末一行自动译成明文：\n\n"
            "[EXEC_QUEUE] T-71:58:12 / 姿控推力器偏置点火 / 授权密钥：已预置。"
        ),
    },
}


def _generic_seed(genre_id: str, title: str, premise: str) -> dict[str, Any]:
    bp = get_genre(genre_id)
    if genre_id in _GENRE_SEEDS:
        return _GENRE_SEEDS[genre_id]
    return {
        "world_overview": f"围绕核心设定展开的【{bp.name}】世界：{premise}。所有冲突都服从现实代价与人物切身利益。",
        "rules": [
            (bp.world_rule_categories[0], f"遵循【{bp.name}】核心法则：任何关键收益都伴随对等风险或信息代价。", "不可临时开挂破坏既定边界。"),
            (bp.world_rule_categories[1] if len(bp.world_rule_categories) > 1 else "人际账本", "人物决策受制于资源、时间与过往关系，配角拥有独立诉求。", "严禁全员降智配合主角。"),
        ],
        "characters": [
            {
                "name": "林叙",
                "role": "主角",
                "age_or_identity": f"身处【{bp.name}】风暴中心的务实行动者",
                "core_desire": "在截止期限前守住底线并查清真相",
                "flaw_or_fear": "习惯独自扛压，不轻易向他人吐露软肋",
                "secret": "手里攥着一件足以翻盘却尚未公开的旧物证",
                "current_state": "刚察觉局势异样，保持高度警觉",
                "current_location": "故事起始现场",
                "inventory": ["旧笔记本", "关键信物"],
                "relationships": {"宋微": "立场微妙的合作对象"},
                "voice": {
                    "sentence_style": "克制短句，重事实轻空话",
                    "vocabulary_register": f"贴合{bp.name}语境的自然口语",
                    "verbal_tics": "关键处停顿反问",
                    "conflict_style": "先亮底牌一角，再看对方反应",
                    "sample_lines": ["话可以慢慢谈，但这张纸上的日期你先解释清楚。", "真要翻脸，你不会选今天这个地方找我。"],
                },
            },
            {
                "name": "宋微",
                "role": "关键搭档 / 博弈对手",
                "age_or_identity": "掌握另一半信息拼图的局内人",
                "core_desire": "保住自己所在意的人与既有筹码",
                "flaw_or_fear": "防备心极强，容易错判盟友善意",
                "secret": "早于主角三天便已暗中介入此事",
                "current_state": "表面从容，实则急需破局援手",
                "current_location": "约定会面点",
                "inventory": ["密封信封", "备用钥匙"],
                "relationships": {"林叙": "既互相防备又被迫绑定"},
                "voice": {
                    "sentence_style": "干练利落，句中带潜台词",
                    "vocabulary_register": "精明务实，不兜圈子",
                    "verbal_tics": "爱反手把问题抛回给对方",
                    "conflict_style": "点到为止，以利弊说服而非吵架",
                    "sample_lines": ["我替你挡了两天消息，不是来做慈善的。", "你只看到桌面这一层，底下的账你敢不敢翻？"],
                },
            },
        ],
        "foreshadowing": [
            ("缺失日期的旧凭证", "开篇物件上有一处刻意刮掉的日期或署名，将在中盘反转中成为关键铁证。", 1, 4),
            ("第三方的匿名提醒", "一条来历不明的短讯提前精准预言了第一章末尾的意外。", 1, 3),
        ],
        "raw_prose": (
            f"暮色沉下来，街角灯光亮成一排，宛如一幅静谧的画卷。林叙推开门，深吸了一口气，感到一阵难以言喻的压迫感。{premise}\n\n"
            "空气仿佛凝固了。宋微坐在靠窗的位置，缓缓说道：“你比约定的时间晚了十分钟。”她眼中闪过一丝复杂难明的神色。\n\n"
            "林叙嘴角勾起一抹苦笑，淡淡地说道：“路上耽搁了，你先把东西拿出来吧。”他不禁摸了摸口袋里那份皱巴巴的凭据，心头微微一震。\n\n"
            "然而，值得注意的是，宋微并没有立刻回答，气氛瞬间变得凝重起来。时间一分一秒地过去，窗外车流声打破了沉默。\n\n"
            "这一刻，林叙终于明白，这件事绝没有表面看起来那么简单。前方的路还很长，命运的齿轮已经开始转动，真正的考验才刚刚开始。"
        ),
        "polished_prose": (
            f"七点过一刻，窗玻璃起了层薄雾，街灯隔着水汽晕成一团昏黄。林叙推开木门，门框上的铜铃只响了半声——门轴卡着张折起来的广告单，被人刻意塞过。\n\n"
            f"桌上的两杯白开水早就凉透，杯壁沾着细密气泡。宋微没抬头，指尖把一张泛黄单据推过桌面半尺：“比约好的晚了十一分钟。路上有人跟着？”\n\n"
            "“转了两条巷子，甩掉了。”林叙拉开椅子坐下，没碰水杯，先把外套最上头那颗松掉的扣子拧紧，“你发消息说事情和三年前那笔旧账有关——直说吧，到底缺了哪一块？”\n\n"
            "宋微这才抬眼看他，手背往单据右下角轻轻一敲：“你自己看日期。”\n\n"
            "单据折痕发毛，经手人那栏墨迹发淡，唯独落款年份被人拿刀片刮薄了一层纸纤维，底下隐约透出另一个数字的捺脚。这和林叙来之前拿到的副本完全对不上。\n\n"
            f"事情的核心回到最初那个死结：{premise} 可眼下这张纸说明，最初把他们俩拖进局里的人，压根就没打算按规矩收场。\n\n"
            "隔壁桌客人结账起身，椅脚拖过水泥地刮出一声尖响。宋微顺手把单据收回袖口，顺带把一只灰信封压在茶托底下。\n\n"
            "“信封里有地址和门禁卡。今晚十点之前，你决定去不去。”她拎起包起身，走到门边又停了半步，顺手把卡在门轴里的广告单抽走，“对了，别打我原来的手机号——刚才进门前，它刚收到一条空号发来的位置共享。”\n\n"
            "门合上了。铜铃清脆地晃了两下，茶托底下露出信封一角，上面用铅笔写着一个林叙极其熟悉、却已经注销了两年的旧号码。"
        ),
    }


def _clean_arbitrary_slop(text: str) -> str:
    """Best-effort deterministic offline polish for arbitrary user-supplied prose."""
    replacements = [
        (r"嘴角[微轻]?[微轻]?勾起一[抹丝道](?:冷笑|微笑|弧度|嘲讽|苦笑)", "眉梢轻动，神色冷了下来"),
        (r"(?:眼中|眼底|眸中)(?:闪过|掠过)一[丝抹道]([^，。！？\n]{1,6})", r"目光一沉，藏不住那点\1"),
        (r"空气仿佛(?:凝固|静止|冻结)了?", "屋里骤然静下来，没人先接话"),
        (r"深吸了一口气[，,]?", "停顿半息，"),
        (r"(?:心头|心中)(?:微微)?一震", "指节一紧"),
        (r"感到一阵难以言喻的([^，。！？\n]{1,6})", r"胃里发沉，说不出话来"),
        (r"气氛(?:瞬间)?变得(?:紧张|凝重|压抑)起来", "几个人都没再抬头，只剩窗外风声"),
        (r"(?:然而|与此同时|值得注意的是|不可否认的是)[，,]?", ""),
        (r"缓缓(?:说道|开口)", "开口道"),
        (r"淡淡地?(?:说道|一笑)", "道"),
        (r"不禁|不由得", ""),
        (r"这一刻，?[他她我][^。！？\n]{0,30}(?:终于明白|彻底懂得)[^。！？\n]*[。！？]?", ""),
        (r"(?:前方的路还很长|命运的齿轮(?:开始|悄然)?转动|真正的(?:考验|较量)才刚刚开始)[^。！？\n]*[。！？]?", ""),
    ]
    result = text
    for pat, repl in replacements:
        result = re.sub(pat, repl, result)
    # Clean doubled punctuation or blank artifacts
    result = re.sub(r"[，,]{2,}", "，", result)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


class DemoLLMClient(LLMClient):
    """Offline multi-genre demo LLM that exercises the complete InkForge pipeline."""

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        task: str = "general",
        use_fast_model: bool = False,
        temperature: float | None = None,
        max_tokens: int = 4096,
        json_mode: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        meta = metadata or {}
        genre_id = meta.get("genre_id", "suspense")
        if genre_id not in GENRE_BLUEPRINTS:
            genre_id = "suspense"
        bp = get_genre(genre_id)
        title = meta.get("title", "未命名小说")
        premise = meta.get("premise", bp.sample_premise)
        seed = _generic_seed(genre_id, title, premise)

        if task == "architect":
            target_chapters = int(meta.get("target_chapters", 6))
            chars = seed["characters"]
            lead = chars[0]["name"]
            second = chars[1]["name"] if len(chars) > 1 else lead
            stage_titles = [
                ("异常开场与第一枚错位线索", "建立处境与切身利害，抛出无法回避的异常物证"),
                ("初次试探与暗账浮现", "两人带着各自秘密试探交锋，发现表层解释完全站不住脚"),
                ("假线索反咬与信任裂痕", "顺着旧线索追查反中圈套，付出真实代价并暴露隐藏动机"),
                ("局中局翻面与关键抉择", "前文伏笔集中引爆，主角在原则与筹码之间做出不可逆选择"),
                ("终局对峙与真相落盘", "高密度潜台词交锋，依靠既有规则与公平线索完成破局"),
                ("尘埃未定与克制余波", "主线收束但不强行煽情，落回具体物件与人物新处境"),
            ]
            outlines = []
            for idx in range(1, target_chapters + 1):
                st_title, st_conflict = stage_titles[(idx - 1) % len(stage_titles)]
                outlines.append(
                    {
                        "chapter_number": idx,
                        "title": f"{st_title}" if idx <= len(stage_titles) else f"余波推进（{idx}）",
                        "pov": lead if idx % 2 == 1 else second,
                        "summary": f"第{idx}章围绕“{st_title}”推进：{premise[:45]}… 人物在既有约束下博弈并推动主线升级。",
                        "core_conflict": st_conflict,
                        "chapter_hook": f"留下与第{min(target_chapters, idx + 1)}章直接咬合的具体物证或反转信息。",
                        "target_words": bp.default_words_per_chapter,
                        "must_include_clues": [seed["foreshadowing"][0][0]] if idx in (1, 3) else [],
                    }
                )

            payload = {
                "logline": f"【{bp.name}】{premise}",
                "tone_and_style": f"{bp.tagline}；严禁AI套话、情绪直白播报与章末说教。",
                "narrative_pov": bp.default_pov,
                "world_overview": seed["world_overview"],
                "world_rules": [
                    {"category": r[0], "rule": r[1], "cost_or_limit": r[2]}
                    for r in seed["rules"]
                ],
                "characters": chars,
                "foreshadowing": [
                    {
                        "title": f[0],
                        "description": f[1],
                        "planted_chapter": f[2],
                        "target_payoff_chapter": min(target_chapters, f[3]),
                        "status": "open",
                    }
                    for f in seed["foreshadowing"]
                ],
                "outlines": outlines,
            }
            return json.dumps(payload, ensure_ascii=False)

        if task == "scene_director":
            ch_num = int(meta.get("chapter_number", 1))
            ch_title = meta.get("chapter_title", f"第{ch_num}章")
            chars = [c["name"] for c in seed["characters"][:3]]
            lead = chars[0]
            beats = [
                {
                    "beat_index": 1,
                    "location": seed["characters"][0].get("current_location", "开场现场"),
                    "time_marker": f"第{ch_num}日 · 夜雨/傍晚",
                    "pov": lead,
                    "characters_present": chars[:2],
                    "goal": f"切入【{ch_title}】具体现场，用感官细节立住人物当下处境与压力。",
                    "obstacle": "表面线索与当事人口供存在细微矛盾。",
                    "turn": "主角从物件或微小动作中抓出第一处破绽。",
                    "sensory_anchor": bp.sensory_focus.split("、")[0],
                    "subtext_note": "双方嘴上讲规矩，实则各自隐瞒最关键的筹码。",
                },
                {
                    "beat_index": 2,
                    "location": "同一空间内侧 / 交锋区",
                    "time_marker": "十分钟后",
                    "pov": lead,
                    "characters_present": chars,
                    "goal": "借由对话逼问试探对方真实底牌。",
                    "obstacle": "对方滴水不漏并反过来用程序/利害施压。",
                    "turn": "旁观者或第三人的失态意外暴露新线索。",
                    "sensory_anchor": bp.sensory_focus.split("、")[1] if "、" in bp.sensory_focus else "脚步声与光线变化",
                    "subtext_note": "用短句和停顿替代直白争吵。",
                },
                {
                    "beat_index": 3,
                    "location": "线索关键角落",
                    "time_marker": "交锋尾声",
                    "pov": lead,
                    "characters_present": chars[:2],
                    "goal": "核对关键实物，验证或推翻原本假设。",
                    "obstacle": "现场证据指向更危险的旧案/旧账。",
                    "turn": "主角意识到自己早已身处局中，退路被截断。",
                    "sensory_anchor": "随身关键信物的冷硬触感",
                    "subtext_note": "严禁心理独白总结，落在具体物件细节上戛然而止。",
                },
            ]
            return json.dumps({"beats": beats}, ensure_ascii=False)

        if task == "drafter":
            ch_num = int(meta.get("chapter_number", 1))
            if ch_num == 1:
                return seed["raw_prose"]
            # For chapter 2+, create dynamic continuation raw draft
            lead = seed["characters"][0]["name"]
            second = seed["characters"][1]["name"] if len(seed["characters"]) > 1 else "搭档"
            ch_title = meta.get("chapter_title", f"第{ch_num}章")
            return (
                f"翌日清晨，灰白的雾气压在屋檐上，空气仿佛凝固了。{lead}盯着桌上新拼出来的几条时间记录，深吸了一口气，感到一阵难以言喻的焦躁。\n\n"
                f"“关于《{ch_title}》这一截缺口，昨晚我又核了一遍。”{second}推门进来，缓缓说道，眼神深邃地打量着桌面，“值得注意的是，我们之前漏算了最关键的一个人。”\n\n"
                f"{lead}嘴角勾起一抹冷笑，淡淡地说道：“你是说，那份少掉的记录根本不是意外丢失，而是有人趁乱换了包？”\n\n"
                f"“不仅如此，而且对方昨晚十一点半之前就已经离开城区了。”{second}眼中闪过一丝凝重，不禁把手里那张皱巴巴的回执单拍在桌上。\n\n"
                f"时间一分一秒地过去，窗外人群喧闹声打破了这份沉默。{lead}收起回执单，这一刻，他终于明白，所有的线索都在指向同一个名字，前方的路还很长，一切才刚刚开始。"
            )

        if task == "continuity_critic":
            issues = [
                {
                    "category": "voice_flat",
                    "severity": "medium",
                    "excerpt": "嘴角勾起一抹冷笑 / 缓缓说道 / 淡淡地说道",
                    "explanation": "人物对话标签过于模板化，削弱了角色各自鲜明的说话声纹。",
                    "fix_hint": "删去“缓缓/淡淡”副词，让角色通过行业用语、停顿和手里动作拉开声纹差异。",
                },
                {
                    "category": "pacing",
                    "severity": "medium",
                    "excerpt": "这一刻，他终于明白……一切才刚刚开始",
                    "explanation": "章末强行抒情总结，破坏了悬念和克制余韵。",
                    "fix_hint": "删掉全部议论式总结，直接停在最后一个具体物证或悬念细节上。",
                },
            ]
            return json.dumps({"continuity_issues": issues}, ensure_ascii=False)

        if task == "polisher":
            mode = meta.get("mode", "chapter")
            if mode == "standalone":
                return _clean_arbitrary_slop(meta.get("source_text", user_prompt))
            ch_num = int(meta.get("chapter_number", 1))
            if ch_num == 1:
                return seed["polished_prose"]
            lead = seed["characters"][0]["name"]
            second = seed["characters"][1]["name"] if len(seed["characters"]) > 1 else "搭档"
            ch_title = meta.get("chapter_title", f"第{ch_num}章")
            return (
                f"清晨六点半，窗台积水还没干透，楼下早点铺掀蒸笼的白气漫上来半截。{lead}把昨晚抄下的四组时间数字并排贴在白板边，红笔圈到第三行时笔尖卡了一下——中间空出的二十分钟，谁的口供都没盖住。\n\n"
                f"门锁轻响两声。{second}拎着两杯滚烫豆浆进来，没客套，先拿手肘把门带严，从风衣内袋抽出一张折成方块的热敏回执单，拍在白板底下。\n\n"
                f"“{ch_title}这块缺口补上了。”{second}扯开杯盖吹了一口，眼皮底下挂着青黑，“昨晚十一点二十四分，有人用现金在城西长途站买了张单程票，监控只拍到左手袖口——袖扣缺了一颗。”\n\n"
                f"{lead}没立刻接豆浆，抓起回执单凑到窗光底下照了三秒：“现金购票不录身份证，可热敏纸背面的批号是连号的。前一张票是谁买的？”\n\n"
                f"“问过售票窗口了。”{second}把吸管戳进杯盖，咔哒一声脆响，“排在他前头的老太太记得清清楚楚，那人买完票没进候车厅，转身把票塞进了门口蓝色垃圾桶。”\n\n"
                f"买一张不坐的车票，偏要留一个缺了扣子的袖口给监控看。\n\n"
                f"屋里静了两拍。墙角旧风扇停在三档没开，叶片上落着一层灰。{lead}翻过白板背面，拿黑笔划掉之前排在首位的嫌疑人名字，只把“十一点二十四分”重重圈了两道。\n\n"
                f"“不是逃跑。”{lead}把红笔帽按回笔尾，“他在替城里另一个人做时间垫背。走，去趟城西——顺路把你兜里藏了一早上的那封旧信也拿出来，别再跟我打哑谜。”"
            )

        if task == "state_extractor":
            ch_num = int(meta.get("chapter_number", 1))
            ch_title = meta.get("chapter_title", f"第{ch_num}章")
            lead = seed["characters"][0]["name"]
            return json.dumps(
                {
                    "summary": f"第{ch_num}章《{ch_title}》完成核心交锋，{lead}发现关键实物破绽，撕开既有表象并锁死下一章行动方向。",
                    "timeline_entry": f"第{ch_num}章：{ch_title}关键线索落盘，时间线向前推进。",
                    "character_updates": [
                        {
                            "name": lead,
                            "current_state": f"已完成第{ch_num}章现场核查，掌握关键实物破绽",
                            "add_inventory": [f"第{ch_num}章关键物证记录"],
                        }
                    ],
                    "foreshadowing_updates": [],
                },
                ensure_ascii=False,
            )

        return f"已完成任务：{task}"
