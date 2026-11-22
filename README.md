# 墨铸 InkForge

**多题材、强逻辑连续、专门对抗「AI味」的小说创作引擎与编辑工作室。**

市面上大多数 AI 写小说工具的通病很明显：换个题材写出来还是同一个腔调、写到第五章就忘了第一章受的伤、满篇都是“嘴角勾起一抹冷笑 / 空气仿佛凝固了 / 眼中闪过一丝 / 然而 / 这一刻他终于明白……”。

**InkForge（墨铸）** 不是把一句 Prompt 扔给大模型硬凑字数，而是把一线出版编辑与职业作家的工序做成了一套可量化、可审校的 **6 步精工流水线**，同时提供 **青瓷稿纸 Web 工作室** 和 **命令行 CLI**，并内置**离线免 Key 演示引擎**，克隆下来即可直接体验完整流程。

---

## 核心设计：为什么能做到「快、合理、无 AI 味」？

```text
[1. Architect 故事圣经策划]
   选定题材蓝图 (10大题材) → 生成世界观铁律(含代价) + 人物声纹卡 + 伏笔账本 + 分章大纲
          │
[2. Scene Director 场景分镜]
   读取最新人物状态/伤势/物品 + 未回收伏笔 + 上章结尾 → 拆解 3~5 个具体场景节拍 (Scene Beats)
          │
[3. Prose Drafter 反套话执笔]
   注入题材写作法则 + 角色声纹样句 + 禁用词红线 + Show-Don't-Tell 约束 → 生成初稿
          │
[4. Dual Auditor 双重质检（毫秒规则引擎 + 毒舌文学编辑）]
   ├─ 确定性红笔体检（0 Token）：定位 90+ 中英文 AI 套话、直白情绪播报、章末说教、局部回声、句式呼吸感(Burstiness)
   └─ LLM 连续性审查（精工模式）：查设定吃书、人物 OOC、时间线漏洞、声纹同质化
          │
[5. Surgical Polisher 外科手术精修]
   只针对红笔命中的 AI 腔与逻辑瑕疵做定点重写（保留剧情节拍与好句子）→ 二次体检量化验证提分
          │
[6. State Sync 连续性档案同步]
   章末自动提取人物位置/伤势/随身物品/关系变化与伏笔进展 → 写回 Story Bible，连写长篇不吃书
```

### 四大核心能力

1. **10 大主流题材独立蓝图（Genre Blueprints）**
   悬疑推理（`suspense`）、东方玄幻/仙侠（`xianxia`）、硬科幻/赛博朋克（`scifi`）、都市现实/商战（`urban_drama`）、现代克制言情（`romance_emotional`）、历史权谋（`historical`）、中式民俗恐怖/规则怪谈（`horror_weird`）、轻喜剧/脑洞日常（`light_comedy`）、新派武侠（`wuxia`）、现实主义文学中短篇（`literary_short`）。
   每种题材内置专属节奏架构、对话占比区间、感官重心、世界规则维度和**题材禁用烂梗表**。
2. **毫秒级量化「去 AI 味红笔体检」（0 Token 可离线运行）**
   - 精确到字符坐标与行号标出 AI 高频套话、论文连接词、直白情绪播报、章末鸡汤总结、题材烂梗与局部用词回声；
   - 计算**句式呼吸感（Burstiness）**与**文笔自然度（0-100 / S-D 分级）**，支持在 Web 工作室稿纸上红笔波浪线高亮定位，并一键对比精修前后分差；
   - 内置**独立文本体检工具**，可直接把别处生成的小说粘进来查 AI 味并做外科精修。
3. **活体故事圣经 + 人物声纹卡（防吃书、防千人一面）**
   每位角色绑定独立声纹（句长偏好、用词层级、冲突防御反应与 2 句对话样本），每写完一章自动同步最新状态、随身物品与伏笔账本。
4. **全模型兼容 & 多格式成书导出**
   - 兼容 **DeepSeek、火山方舟/豆包、阿里云百炼/通义千问、OpenAI、OpenRouter（Claude/Gemini）、本地 Ollama** 以及任意 OpenAI 兼容接口；
   - 零外部依赖一键导出 **标准 EPUB3 电子书、独立排版 HTML 阅读器、Markdown、TXT**。

---

## 快速开始

### 1. 安装（需要 Python 3.11+）

```bash
git clone https://github.com/xy-tuoren/inkforge.git
cd inkforge

# 推荐使用 uv（或标准 pip）
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

### 2. 零配置立刻体验（无需 API Key）

```bash
# 启动青瓷稿纸 Web 编辑工作室（默认 http://127.0.0.1:8765）
inkforge serve
```

打开浏览器后点击 **「一键生成悬疑示例」**，即可直接体验从建档、故事圣经、分镜、初稿、红笔去 AI 味体检、前后精修对比到导出 EPUB3 电子书的完整闭环。

也可以直接在命令行跑一键演示或体验离线红笔体检：

```bash
# 查看 10 大题材蓝图
inkforge genres

# 对比体验：AI 味重样稿 vs 精修克制样稿（0 Token 离线评分）
inkforge audit examples/sample_ai_slop_chapter.txt --genre suspense
inkforge audit examples/sample_human_craft_chapter.txt --genre suspense

# 命令行跑完整演示并导出 EPUB3
inkforge demo --genre xianxia --chapters 2
```

### 3. 接入真实大模型开始正式创作

复制 `.env.example` 为 `.env` 填入你的 Key，**或直接在 Web 工作室右上角「模型设置」中可视化切换并保存**：

```bash
cp .env.example .env
```

以 DeepSeek 为例：

```env
INKFORGE_PROVIDER=deepseek
INKFORGE_API_KEY=sk-your-key
INKFORGE_MODEL=deepseek-chat
```

也支持豆包（`doubao`）、通义千问（`qwen`）、OpenAI（`openai`）、OpenRouter（`openrouter`）、本地 Ollama（`ollama`）。

---

## CLI 常用命令

```bash
# 1. 新建小说项目并自动构建故事圣经与全书大纲
inkforge init \
  --title "雨夜十五分钟" \
  --genre suspense \
  --premise "梅雨季老城区一家通宵药房停电十五分钟，老板死在反锁库房里，账本少了一页。" \
  --chapters 8

# 2. 按章连续精工创作（craft=全链路精修 / fast=超标自动精修）
inkforge write <PROJECT_ID> --chapters 1-3 --mode craft

# 3. 单独精修任意本地章节草稿并查看自然度提分
inkforge polish draft.txt --genre urban_drama --output polished.txt

# 4. 导出标准 EPUB3 / HTML / Markdown / TXT
inkforge export <PROJECT_ID> --format epub --out exports
```

---

## 项目结构

```text
inkforge/
├── src/inkforge/
│   ├── genres/blueprints.py      # 10 大题材独立叙事蓝图与禁用套话库
│   ├── analyzer/
│   │   ├── lexicons.py           # 中英文 AI 高频套话 / 情绪播报 / 说教结尾词库
│   │   └── slop_detector.py      # 毫秒级量化去AI味与句式呼吸感体检引擎
│   ├── llm/
│   │   ├── openai_compat.py      # OpenAI 兼容异步客户端（含 JSON 自修复与重试）
│   │   └── demo_provider.py      # 多题材离线演示引擎
│   ├── engine/
│   │   ├── prompts.py            # 6 阶段精工创作与外科去AI味提示词体系
│   │   ├── pipeline.py           # Architect → Beats → Draft → Audit → Polish → Sync
│   │   └── exporter.py           # Markdown / TXT / HTML / 标准 EPUB3 导出器
│   ├── storage/repository.py     # SQLite WAL 持久化与故事圣经状态同步器
│   ├── web/                      # FastAPI 后端 + 青瓷稿纸 Web 编辑工作室
│   └── cli.py                    # Rich / Typer 命令行工具
├── examples/                     # AI 味样稿 vs 精修样稿对比示例
└── tests/                        # 单元测试与 FastAPI 全链路集成测试
```

---

## 运行测试与代码检查

```bash
ruff check src tests
pytest -v
```

## License

MIT
