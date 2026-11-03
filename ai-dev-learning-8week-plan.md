# 8 周 AI 应用开发学习计划（RAG / LangChain / FastAPI / Docker）

> 基于你的真实仓库状态生成：`/Users/guo/ai-dev-learning`，origin `github.com:2961768276/ai-dev-learning`，仅 `main` 分支；Python 3.11 + uv（`uv_build` 后端，src 布局 `src/ai_dev_learning`）；dev 依赖已有 `pytest 9.2` / `ruff 0.17`；`.gitignore` 已忽略 `.env`、`.env.*` 并放行 `.env.example`；`README.md` 为空，`hello.py`、`week01-hello-llm/`、空的 `requirements.txt` 是待清理的历史残留（Day 1 处理）。

## 0. 执行规则（先看这 6 条，再看日程）

1. **时间盒**：阅读 25 + 编码 50 + 复盘 15 = 90 分钟，到点停。写不完就降级（见文末「降级规则」表），不加班。
2. **结构**：`src/ai_dev_learning/` 只放要复用的代码（common / core / services / api），`lessons/w1…w4/` 放日课脚本与 `out/` 产物，主项目在 Day 29 起长在 `src/ai_dev_learning/` 里。原因是你的 `pyproject.toml` 用了 `uv_build` + src 布局，日课脚本放根目录时仍能 `import ai_dev_learning`，而 FastAPI 应用必须放在被安装的包里，否则 `uv run uvicorn` 找不到模块。
3. **生成模型**：一律 DeepSeek 云端。**嵌入**：默认云端 `BAAI/bge-m3`（1024 维，硅基流动 OpenAI 兼容接口，有免费额度）；**备选**本地 Ollama `nomic-embed-text`（768 维，约 274MB）。两者共用一个适配器，Day 17 二选一，Day 21 做一次对照。⚠️ 两个模型维度不同，必须各自独立 collection，混用会直接报错。
4. **向量库**：只用 ChromaDB `PersistentClient(path="data/chroma")`，目录在项目内并 gitignore。
5. **每天唯一验收标准**：仓库里多一个能跑的文件 / 一份可展示的输出文件 / README 有实质更新。三者皆无 = 今天没完成。
6. **视频分 P 兜底**：P 编号与当天主题不完全匹配时，以当天产物为准；P33–P50、P64–P101 未排进计划（我没逐一核对内容），若你实际看到某段正好解决当天卡点，允许用它替换当天 25 分钟阅读段。

---

# 第一部分 · 8 周总览

| 周次 | 主题 | 对应 JD 技能 | 本周结束时**必须存在**的产物 |
|---|---|---|---|
| W1（D1–7） | 云端 LLM API 打底 + 工程习惯 | 2、1（工程侧）、8（雏形） | `src/ai_dev_learning/common/llm.py`（带超时/重试/usage 记账）；`logs/usage.jsonl`；6 个可跑脚本；README 的 Week 1 段 |
| W2（D8–14） | Prompt 设计 + 结构化输出 + Function Calling | 3、9 | `lessons/w2/prompts/*.md`；`eval_prompt.py` 与准确率报告；`tool_loop.py` + `logs/tool_trace.jsonl` |
| W3（D15–21） | **手写** RAG 全链路 | 4 | `data/corpus/` 语料；`data/chroma/` 持久库；`rag_min.py` 端到端问答；参数网格命中率表 |
| W4（D22–28） | LangChain 核心 + LCEL 重构 RAG | 5 | `lc_rag.py`（LCEL 链）；手写版 vs LCEL 版对照文档 |
| W5（D29–35） | FastAPI 服务化 + Docker | 6、7 | 4 个接口（`/health` `/chat` `/ask` `/search`）；`Dockerfile` + `docker-compose.yml`；`scripts/smoke_test.sh`；tag `v0.1.0` |
| W6（D36–42） | 主项目迭代 I：知识库服务成型 | 4、6、1 | 上传/列表/删除接口；多轮改写；拒答策略；20 条评测集 + 两份评测报告；tag `v0.2.0` |
| W7（D43–49） | 主项目迭代 II：Agent / MCP / 测试 / CI | 9、10、11、8 | `agent.py`（最大步数+轨迹）；失败案例文档；pytest 全绿；GitHub Actions 绿灯；tag `v1.0.0` |
| W8（D50–56） | 简历、项目故事、模拟面试 | 8 收口 + 全部串联 | 4 条量化简历 bullet；3 分钟故事稿；32 题题库；2 次模拟面试记录 |

**主线视频用量**：P1–P2（D1）、P11–P12（D3）、P25–P26（D4）、P27–P32（D8–D10）、P51–P54（D13）、P102–P116（D15–D20）、P11–P14（D22）、P27–P32（D23–D24）、P103–P113（D25–D26）、P117–P120（D27）、P55–P63（D44–D45）。合计约 55 个分 P，每周 6–12 个。

---

# 第二部分 · Day 1 – Day 56 每日明细

## 第 1 周：云端 LLM API 打底（JD 2）

**Day 1 · 第一次云端调用跑通 + 仓库清场**
- 阅读（25–30min）：DeepSeek API Docs《Your First API Call》《Chat Completions》参数表；尚硅谷 P1–P2（只建立"为什么需要框架"的全景）
- 编码（50–55min）：`uv add openai`；写 `.env.example`（`DEEPSEEK_API_KEY=`）与 `.env`；`lessons/w1/day01_smoke.py` 调 `deepseek-chat` 一句话，打印 `content` + `usage.total_tokens` + 耗时，原始响应存 `lessons/w1/out/day01_resp.json`；顺手把 `hello.py`、`week01-hello-llm/`、空的 `requirements.txt` 挪进 `archive/` 并提交
- 复盘三问：① 这次调用实际返回了什么内容、total_tokens 是几、耗时多少秒？② 卡点在 key、base_url、依赖 哪一处，你怎么确认的？③ 明天若只改一处，改 model 还是 max_tokens，为什么？
- commit：`Day 1: 打通 DeepSeek 首次调用并打印 usage`

**Day 2 · 参数控制：temperature / max_tokens / finish_reason**
- 阅读（25–30min）：DeepSeek 文档参数说明段（temperature、top_p、max_tokens、stop、seed、finish_reason）
- 编码（50–55min）：`lessons/w1/day02_params.py` 同一 prompt 跑 temperature 0 / 0.7 / 1.3，再跑一次 `max_tokens=20` 观察截断；结果写 `lessons/w1/out/day02_params.md` 表格（温度｜输出摘要｜finish_reason｜tokens）
- 复盘三问：① `finish_reason=length` 说明什么？② temperature=0 时两次输出是否完全一致，不一致说明什么？③ 哪类业务你会把 temperature 钉死在 0，为什么？
- commit：`Day 2: 对比 temperature 与 max_tokens 对输出的影响`

**Day 3 · 抽出统一客户端 + usage 记账**
- 阅读（25–30min）：尚硅谷 P11–P12（模型创建与调用）；OpenAI SDK README 的 `timeout` / `max_retries` 小节
- 编码（50–55min）：`src/ai_dev_learning/common/llm.py` 暴露 `chat(messages, **kw) -> {content, usage, latency_s, model}`，每次追加一行到 `logs/usage.jsonl`；`lessons/w1/day03_usage.py` 连跑 3 次并打印当日累计 token；`.gitignore` 补 `logs/`、`data/chroma/`、`data/uploads/`
- 复盘三问：① 算钱要用 jsonl 里哪几个字段？② 为什么 `print` 不能替代 jsonl？③ 日志文件为什么必须 gitignore，而 `out/*.md` 要提交？
- commit：`Day 3: 抽出统一 LLM 客户端并落 usage 日志`

**Day 4 · 消息角色与多轮上下文**
- 阅读（25–30min）：DeepSeek《Multi-round Conversation》；尚硅谷 P25–P26（Message 结构）
- 编码（50–55min）：`lessons/w1/day04_chat_cli.py` 命令行多轮：system 设定"苏格拉底式提问"角色，维护 messages 列表，`exit` 退出，历史落 `lessons/w1/out/day04_history.json`；再跑一次 system 放末尾的版本做对照
- 复盘三问：① 轮数从 1 增到 4，prompt_tokens 怎么变？② system 放前面和放末尾，输出差异在哪？③ 上下文超过模型上限时你的程序会怎样，明天打算怎么防？
- commit：`Day 4: 实现带角色与历史的多轮 CLI 对话`

**Day 5 · 结构化输出（strict JSON Schema）**
- 阅读（25–30min）：DeepSeek 结构化输出文档，重点记 `base_url=https://api.deepseek.com/beta` 与 `json_schema` 的 strict 约束（required、additionalProperties:false）
- 编码（50–55min）：把 2 份目标 JD 粘贴成 `data/jd_sample.md`；`lessons/w1/day05_extract_jd.py` 抽取 `{岗位, 必备技能[], 年限, 学历}` 并用 Pydantic 校验，结果存 `lessons/w1/out/day05_jd.json`；同时跑一次**非 strict** 的 `json_object` 做对比
- 复盘三问：① strict 模式最常见的失败原因是什么，你遇到的是哪个？② 既然能约束 schema，为什么还需要 Pydantic 校验？③ 解析失败时你的降级路径是什么？
- commit：`Day 5: 用 strict JSON Schema 抽取 JD 结构化字段`

**Day 6 · 超时、重试与错误分类**
- 阅读（25–30min）：OpenAI SDK `errors` 与重试文档；HTTP 429 / 5xx 语义速查
- 编码（50–55min）：`lessons/w1/day06_errors.py` 故意制造 401（错 key）、400（错参数）、超时三类错误；在 `common/llm.py` 加 `timeout` + 指数退避，只对 429/5xx/超时重试，每次失败写 `logs/errors.jsonl`；三类错误的"现象→处理"写成 `lessons/w1/out/day06_errors.md`
- 复盘三问：① 哪三类错误必须重试、哪两类绝不能重试？② 重试会不会导致重复计费或重复副作用？③ 你的 timeout 设几秒，依据是什么？
- commit：`Day 6: 加入超时与退避重试并做错误分类`

**Day 7 · 复盘日 1（不引入新内容）**
- 只做四件事：整理 `lessons/w1/` 与 `src/ai_dev_learning/common/`；README 写 Week 1 段（环境、怎么跑 day01/day03/day05）；`scripts/` 里放一个 `run_all_w1.sh` 顺序跑通本周脚本；打 tag
- 本周三问：① `logs/usage.jsonl` 里 6 天累计 token 多少，按官网价折合多少钱（自己算一遍并写进 README）？② `common/llm.py` 现在一共几个参数，哪个是为"结果可复现"加的？③ 本周 6 个脚本里，哪个最值得在面试里讲，请写出它的"输入→处理→输出"三句话。
- commit：`Day 7: 第 1 周复盘——目录整理、README 与 w1-done 标签` + `git tag w1-done`

## 第 2 周：Prompt 工程 + 结构化输出 + Function Calling（JD 3、9）

**Day 8 · 角色设定与提示词模板**
- 阅读（25–30min）：尚硅谷 P27–P29（提示词模板）；LangChain 中文文档 PromptTemplate 页只读概念
- 编码（50–55min）：`lessons/w2/prompts/summarize_v1.md`（无角色）与 `summarize_v2.md`（角色+输出约束+字数）；`lessons/w2/day08_template.py` 用 `str.format` + 模板文件渲染同一输入，对比两版输出与 token，落 `lessons/w2/out/day08_compare.md`
- 复盘三问：① 角色设定改变的是"内容"还是"格式"，用你的输出举例？② 模板变量和 f-string 混用会踩什么坑？③ 两版 token 差多少，多出来的值不值？
- commit：`Day 8: 把系统提示抽成模板文件并对比角色设定效果`

**Day 9 · Few-shot 与反例**
- 阅读（25–30min）：DeepSeek 文档 few-shot 建议段；尚硅谷 P30–P31
- 编码（50–55min）：任务=把用户问题分到 {售前, 售后, 发票, 其他}；`lessons/w2/data/cls_cases.jsonl` 造 12 条（含 2 条边界）；`day09_fewshot.py` 跑 zero-shot / 3-shot / 3-shot+1 个反例三组，准确率表落 `lessons/w2/out/day09_fewshot.md`（含每条错例）
- 复盘三问：① 哪条错例被 few-shot 救回来，哪条反而变差？② 3-shot 比 zero-shot 贵多少 token？③ 示例顺序是否影响结果——你没测的话，明天用哪 3 行代码补测？
- commit：`Day 9: zero-shot 与 few-shot 分类准确率对比`

**Day 10 · 输出解析与容错修复**
- 阅读（25–30min）：LangChain 中文文档 OutputParser 页（JsonOutputParser / PydanticOutputParser 概念）；尚硅谷 P32
- 编码（50–55min）：故意**不用** strict 模式，让模型产出脏 JSON；`lessons/w2/day10_parser.py` 实现 `parse_json()` 处理 ```json 包裹、前后废话、单引号、尾逗号；10 条样本统计"一次成功率 / 修复后成功率"，落 `lessons/w2/out/day10_parse.md`
- 复盘三问：① 你的解析器覆盖了几种脏输出，漏了哪种？② "本地修复"和"重新请求"哪个更省，判据是什么？③ 已经有 strict 模式了，为什么还要解析器？
- commit：`Day 10: 实现容错 JSON 解析并统计修复率`

**Day 11 · 把 prompt 评测脚本化**
- 阅读（25–30min）：不引入新框架；读自己 Day 9/10 代码，再读 LangSmith 简介页 10 分钟（只了解"评测集+对比"概念，不接入）
- 编码（50–55min）：`lessons/w2/eval_prompt.py` 输入 `cls_cases.jsonl` + 两个 prompt 文件，输出 markdown 报告：准确率、平均 token、平均延迟、失败样本 id；第一次跑必须复现 Day 9 的结论
- 复盘三问：① 报告里哪一列可以直接上简历？② 12 条样本的结论可信吗，要多少条才敢下判断？③ 下次评测你想加哪个维度（稳定性/成本/鲁棒性）？
- commit：`Day 11: 脚本化 prompt 评测并生成对比报告`

**Day 12 · Function Calling 单工具闭环**
- 阅读（25–30min）：DeepSeek Function Calling 文档（tools 定义、tool_calls 结构、tool 角色消息）
- 编码（50–55min）：`lessons/w2/day12_tool_call.py` 注册 `search_docs(query)` 和 `get_doc_meta(doc_id)` 两个本地 mock 工具；问一句需要工具的话 → 收 `tool_calls` → 本地执行 → 结果以 `role=tool` 回灌 → 得最终答案；完整消息轨迹存 `lessons/w2/out/day12_trace.json`
- 复盘三问：① `tool_call_id` 为什么必须原样回传？② 为什么工具结果不能拼进 system 消息？③ 模型选了错误的工具，你从轨迹的哪一段能看出来？
- commit：`Day 12: 跑通单轮 Function Calling 闭环`

**Day 13 · 多工具 + 最大步数 + 轨迹日志**
- 阅读（25–30min）：尚硅谷 P51–P54（Agent 概念，只取"LLM + 工具 + 循环"这一层）
- 编码（50–55min）：`lessons/w2/day13_tool_loop.py`：工具注册表 dict、`while step < 5` 循环、每步写 `logs/tool_trace.jsonl`（step/tool/args/ok/latency）、超步数打印"未收敛"退出；测 3 个问题（单工具、双工具、需两轮）
- 复盘三问：① 哪一步是模型自己决定"继续"的，你怎么看出来的？② 超步数退出时你保留了哪些信息给用户？③ 工具抛异常时模型的表现如何，你的循环会崩吗？
- commit：`Day 13: 实现带最大步数与轨迹日志的工具调用循环`

**Day 14 · 复盘日 2（不引入新内容）**
- 只做四件事：整理 `lessons/w2/`；README 补 Week 2（评测结论 3 行 + 工具轨迹样例）；把 Day 11 报告和 Day 13 轨迹固定为 `lessons/w2/out/` 下的证据文件；打 tag
- 本周三问：① 12 条样本上准确率多少，换 prompt 后 ±几点，最大的一条错例是什么？② Day 13 三个问题各用几步收敛，哪类最费步？③ 面试官问"你怎么知道 prompt 改好了"，你会直接打开哪个文件？
- commit：`Day 14: 第 2 周复盘——prompt 评测与工具轨迹沉淀` + `git tag w2-done`

## 第 3 周：手写 RAG 全链路（JD 4）

**Day 15 · 语料与加载器**
- 阅读（25–30min）：尚硅谷 P102–P104（RAG 流程与三段式）
- 编码（50–55min）：`data/corpus/` 放 6–8 篇：从 DeepSeek Function Calling、LangChain LCEL、FastAPI Tutorial、Docker Get Started 各摘 2 篇存 md；`lessons/w3/loaders.py` 递归加载 md/txt/pdf（pypdf）→ `[{doc_id, source, text, meta}]`，统计字数/篇数落 `lessons/w3/out/day15_docs.md`
- 复盘三问：① 你这批语料能回答哪三类问题，明确答不了哪类？② 加载时丢掉了哪些元信息（标题层级/页码），后面为什么需要？③ doc_id 用什么规则生成，会不会重名？
- commit：`Day 15: 建立本地语料库与文档加载器`

**Day 16 · 切分策略与 chunk 统计**
- 阅读（25–30min）：尚硅谷 P105–P107（文本切分）
- 编码（50–55min）：`lessons/w3/splitter.py` 实现两种：固定长度 500/overlap 50、按 Markdown 标题递归切；输出 chunk 数、平均/最长/最短长度、被切断的代码块数，落 `lessons/w3/out/day16_chunks.md`；chunk 存 `data/chunks.jsonl`
- 复盘三问：① 两种切分在"代码块被腰斩"上差几个？② overlap=50 多花多少存储和 token，值吗？③ 你选哪个做 baseline，为什么？
- commit：`Day 16: 实现两种切分策略并对比 chunk 统计`

**Day 17 · 向量化（云端 bge-m3，本地备选）**
- 阅读（25–30min）：硅基流动 Embeddings 文档 或 Ollama `nomic-embed-text` 文档（明确一点：DeepSeek 没有 embedding 接口）
- 编码（50–55min）：`src/ai_dev_learning/common/embeddings.py` 做 OpenAI 兼容适配器（`EMBED_PROVIDER=siliconflow|ollama` 切换，batch 32）；`lessons/w3/day17_embed.py` 对 3 组句对（同义/相关/无关）算余弦，验证"同义 > 相关 > 无关"；落 `lessons/w3/out/day17_embed.md`（维度、耗时、token）
- 复盘三问：① 为什么嵌入维度和向量库配置必须对齐？② batch 大小影响什么？③ 同义句和无关句的分数差多少才算"分得开"，你怎么定阈值？
- commit：`Day 17: 接入 bge-m3 嵌入并做相似度自检`

**Day 18 · ChromaDB 持久化**
- 阅读（25–30min）：Chroma 文档 Getting Started / Persistent client；尚硅谷 P108–P110
- 编码（50–55min）：`lessons/w3/store.py` 用 `PersistentClient(path="data/chroma")` 建 collection `kb_bge_m3`，写 ids/embeddings/documents/metadatas；验证：**退出进程再进来 count 不变**；query top3 打印 id + distance + 前 80 字，落 `lessons/w3/out/day18_chroma.md`
- 复盘三问：① 持久化目录放项目内的好处和坏处各一条？② id 用什么规则，同一文件重跑会不会重复入库？③ distance 越小是越相似还是越不相似，你怎么验证的？
- commit：`Day 18: 用 ChromaDB 持久化向量库并可重启查询`

**Day 19 · 检索：top_k / 阈值 / 元数据过滤**
- 阅读（25–30min）：尚硅谷 P111–P113（检索与召回）
- 编码（50–55min）：`lessons/w3/retriever.py` 支持 `top_k`、`score_threshold`、`where={"source": ...}` 过滤；对 5 个问题打印 top5 + 分数，并人工标注哪几条是"看着相关但答不了问题"的噪声，落 `lessons/w3/out/day19_retrieval.md`
- 复盘三问：① 阈值定多少，依据是哪几个样本？② top_k 从 3 加到 8，噪声怎么变？③ 什么业务场景下 metadata 过滤是必须的（举你自己语料里的例子）？
- commit：`Day 19: 实现带阈值与元数据过滤的检索器`

**Day 20 · 端到端最小 RAG（带引用）**
- 阅读（25–30min）：尚硅谷 P114–P116（拼上下文与生成）
- 编码（50–55min）：`lessons/w3/rag_min.py`：question → 检索 top4 → 拼"只依据资料回答 + 必须标 `[来源:文件名]` + 没依据就说'资料中没有'"→ 输出答案；5 问 5 答落 `lessons/w3/out/day20_answers.md`
- 复盘三问：① 哪一条的引用是模型编的（文件名根本不存在）？② "资料中没有"触发了几次，是真没有还是检索没召回到？③ 上下文超长时你怎么截断，按分数还是按顺序？
- commit：`Day 20: 打通最小 RAG 问答链路并强制引用`

**Day 21 · 复盘日 3（只做对照，不引入新概念）**
- 只做三件事：跑 4 组参数（k=3/5/8 × chunk=300/500）的命中率网格 → `lessons/w3/out/day21_grid.md`；用本地 `nomic-embed-text` 建 `kb_nomic` collection 跑同一批问题做一次维度对照（这就是"8GB 轻量实验"）；整理 README 的 Week 3
- 本周三问：① 8 个问题里 hit@3 是多少，哪一问完全没召回，原因在哪一环？② 网格里哪个参数影响最大？③ 只允许改一处让 RAG 变好，你改切分、检索还是 prompt，给理由和证据。
- commit：`Day 21: 第 3 周复盘——RAG 参数网格、本地嵌入对照与 w3-done` + `git tag w3-done`

## 第 4 周：LangChain 核心 + LCEL（JD 5）

**Day 22 · LangChain 模型层**
- 阅读（25–30min）：尚硅谷 P11–P14（模型创建与调用）；LangChain 中文文档 ChatOpenAI 页
- 编码（50–55min）：`uv add langchain langchain-openai`；`lessons/w4/lc_model.py` 用 `ChatOpenAI(base_url=DeepSeek, model="deepseek-chat")` 跑 invoke / stream / batch 三种，打印 `usage_metadata`；差异与坑落 `lessons/w4/out/day22_lc_model.md`
- 复盘三问：① stream 模式下 usage 是哪一刻拿到的？② batch 打满会不会触发限流，你怎么控制？③ 和你 Day 3 手写的客户端比，LangChain 少做了什么、多做了什么？
- commit：`Day 22: 用 LangChain ChatOpenAI 替换手写客户端`

**Day 23 · ChatPromptTemplate 与历史占位**
- 阅读（25–30min）：尚硅谷 P27–P30；中文文档 ChatPromptTemplate / MessagesPlaceholder
- 编码（50–55min）：`lessons/w4/day23_prompts.py` 用 `ChatPromptTemplate` + `MessagesPlaceholder("history")` + `partial`，把 Day 8 的摘要模板迁过来；同一输入渲染后的 messages 存 `lessons/w4/out/day23_rendered.json` 并与手写版对比
- 复盘三问：① 渲染出的 messages 结构和手写的有何不同？② `partial` 适合什么场景（举你项目里的例子）？③ 模板里塞 20 轮 history 会发生什么？
- commit：`Day 23: 用 ChatPromptTemplate 管理角色与历史占位`

**Day 24 · 三种 OutputParser**
- 阅读（25–30min）：尚硅谷 P31–P32；中文文档 OutputParser 页
- 编码（50–55min）：`lessons/w4/day24_parsers.py` 对比 `StrOutputParser` / `JsonOutputParser` / `PydanticOutputParser` / `with_structured_output(Pydantic)`；用 Day 10 的脏输出用例回测，成功率表落 `lessons/w4/out/day24_parsers.md`
- 复盘三问：① `with_structured_output` 底层走 json mode 还是 tool call，你怎么验证的？② 四个里哪个最稳、哪个最脆？③ 解析失败的异常类型是什么，你在哪一层接住？
- commit：`Day 24: 对比四种输出解析方式并接入结构化输出`

**Day 25 · Loader + Splitter（LangChain 版）**
- 阅读（25–30min）：复习尚硅谷 P103–P107 + 中文文档 DocumentLoader / TextSplitter
- 编码（50–55min）：`uv add langchain-community langchain-chroma`；`lessons/w4/lc_ingest.py` 用 `DirectoryLoader` + `RecursiveCharacterTextSplitter(500, 50)` 重跑同一语料，写新 collection `kb_lc`；与 Day 16 自写切分对比 chunk 数/边界，落 `lessons/w4/out/day25_ingest.md`
- 复盘三问：① 它的默认分隔符顺序是什么？② 两套 chunk 数差多少，差在哪个文件上？③ 为什么必须换一个 collection 名而不是覆盖？
- commit：`Day 25: 用 LangChain Loader/Splitter 重建入库管线`

**Day 26 · Chroma Retriever：similarity 与 MMR**
- 阅读（25–30min）：尚硅谷 P108–P113 复习；中文文档 Retriever 页
- 编码（50–55min）：`lessons/w4/day26_retriever.py` 用 `as_retriever(search_type="similarity", k=4)` 与 `search_type="mmr"`（fetch_k=20, lambda_mult=0.5）跑同 5 问，对比结果多样性，落 `lessons/w4/out/day26_retriever.md`
- 复盘三问：① MMR 解决了什么，代价是什么？② `k` 和 `fetch_k` 的关系是什么？③ 检索出的 Document 里带哪些 metadata，够不够做引用？
- commit：`Day 26: 对比相似度检索与 MMR 检索效果`

**Day 27 · LCEL 组装 RAG 链**
- 阅读（25–30min）：中文文档 LCEL / Runnable 接口一页（这是本周最关键的一页，精读）+ 尚硅谷 P117–P120
- 编码（50–55min）：`lessons/w4/lc_rag.py` 写出 `{"context": retriever | format_docs, "question": RunnablePassthrough()} | prompt | llm | StrOutputParser()`，并用 `RunnableParallel` 让返回同时带 answer + sources；跑 Day 20 的 5 问，落 `lessons/w4/out/day27_lcel_answers.md`
- 复盘三问：① sources 在管道里怎么被带出来的？② LCEL 的流式为什么比手写容易？③ `RunnablePassthrough.assign` 你会用在哪一步？
- commit：`Day 27: 用 LCEL 把检索与生成串成一条链`

**Day 28 · 复盘日 4（只做对照）**
- 只做两件事：写 `lessons/w4/out/handrolled_vs_lcel.md`（LOC、可读性、可观测性、加一步 rerank 的改造成本，四个维度各一段）；README 更新到 Week 4 并打 tag
- 本周三问：① 两版各多少行，省在了哪一行上？② 现在要插一个 rerank 步骤，LCEL 版改哪里、手写版改哪里？③ 哪一版你更敢让面试官现场追问，为什么？
- commit：`Day 28: 第 4 周复盘——手写 RAG 与 LCEL 版本对照` + `git tag w4-done`

## 第 5 周：FastAPI 服务化 + Docker（JD 6、7）

**Day 29 · FastAPI 骨架与健康检查**
- 阅读（25–30min）：FastAPI 官方 First Steps + Path Parameters（中文版可）
- 编码（50–55min）：`uv add fastapi "uvicorn[standard]"`；`src/ai_dev_learning/main.py` 提供 `GET /health`（status/version/ts）与 `GET /version`；`uv run uvicorn ai_dev_learning.main:app --reload`；curl 结果存 `docs/smoke/day29.txt`
- 复盘三问：① `/health` 返回什么才算"健康"，要不要带依赖检查？② `--reload` 为什么不能上生产？③ 单 worker 的并发上限大概在哪，瓶颈是 CPU 还是 IO？
- commit：`Day 29: 搭起 FastAPI 服务骨架与健康检查`

**Day 30 · 请求体校验与 /chat**
- 阅读（25–30min）：FastAPI Request Body + Pydantic Field 约束
- 编码（50–55min）：`src/ai_dev_learning/api/chat.py`：`POST /chat`，body `{message, temperature<=2, max_tokens<=1024}`，返回 `{answer, usage, model}`；故意发 `temperature=5` 拿 422；两次请求的 curl + 422 响应体存 `docs/smoke/day30.txt`
- 复盘三问：① 422 的响应体结构是谁生成的？② 为什么校验放接口层而不是函数内部？③ 哪些内部参数不该开放给调用方？
- commit：`Day 30: 提供带 Pydantic 校验的 /chat 接口`

**Day 31 · /ask 接入 RAG + lifespan 复用**
- 阅读（25–30min）：FastAPI Lifespan Events + Dependencies（Depends）
- 编码（50–55min）：`src/ai_dev_learning/services/rag.py` 封装 Day 27 的链；`main.py` 的 lifespan 里初始化 Chroma 与 retriever（禁止每请求重建）；`POST /ask` 返回 `{answer, sources[], usage}`，`GET /search?q=&top_k=` 返回 chunks；curl 与 `/openapi.json` 片段存 `docs/smoke/day31.txt`
- 复盘三问：① 为什么向量库必须在 lifespan 初始化，每请求建一次的代价有多大？② 多 worker 启动时 lifespan 会跑几次，有什么后果？③ `/ask` 的延迟主要花在检索还是生成，你怎么测出来的？
- commit：`Day 31: 用 lifespan 复用检索链并提供 /ask 与 /search`

**Day 32 · 配置外置、日志与统一异常**
- 阅读（25–30min）：pydantic-settings 文档 + FastAPI Handling Errors
- 编码（50–55min）：`uv add pydantic-settings`；`src/ai_dev_learning/core/config.py`（keys/model/chroma_dir/top_k/score_threshold）；补 `.env.example` 全字段；中间件记录 `req_id` + 耗时；`@app.exception_handler` 统一 `{code, message, req_id}`；验证：缺 key 时启动报错、上游超时返回 504，日志存 `docs/smoke/day32.txt`
- 复盘三问：① 怎么保证 key 既不进 git 也不进镜像？② 异常响应里能不能带 traceback，为什么？③ `req_id` 怎么把一条请求的 3 行日志串起来？
- commit：`Day 32: 配置外置、请求日志与统一异常体`

**Day 33 · Dockerfile 构建与运行**
- 阅读（25–30min）：Docker Get Started（Dockerfile / docker build / docker run）
- 编码（50–55min）：写 `Dockerfile`（`python:3.11-slim`、非 root 用户、先 COPY `pyproject.toml`+`uv.lock` 再 `uv sync --frozen`、最后 COPY `src/`）与 `.dockerignore`（`.env`、`.venv`、`data/chroma`、`logs`、`.git`）；`docker build -t kb-api:0.1 .`；`docker run -p 8000:8000 --env-file .env kb-api:0.1`；curl `/health` 与镜像大小存 `docs/smoke/day33.txt`
- 复盘三问：① 为什么先 COPY 依赖清单再 COPY 源码？② `data/chroma` 不挂载会怎样？③ 镜像里为什么不能有 `.env`，那 secrets 从哪来？
- commit：`Day 33: 编写 Dockerfile 并本地构建运行镜像`

**Day 34 · docker compose 编排与数据卷**
- 阅读（25–30min）：Docker Compose 文档（services / env_file / volumes / healthcheck）
- 编码（50–55min）：`docker-compose.yml`：api 服务 + `env_file: .env` + `volumes: ./data/chroma:/app/data/chroma` + `healthcheck`；`docker compose up -d --build`；重启容器后 `/search` 结果仍在，验证片段存 `docs/smoke/day34.txt`
- 复盘三问：① 重启后数据为什么还在？② healthcheck 用 `curl` 还是 `python -c`，为什么？③ compose 里哪些值该走 `.env`、哪些该写死？
- commit：`Day 34: 用 docker compose 编排服务并挂载向量库`

**Day 35 · 复盘日 5（不引入新内容）**
- 只做三件事：`scripts/smoke_test.sh`（health → chat → ask → search 四连测，任一失败非零退出）；README Quickstart 写"本地 uv"与"docker compose"两条路径；打 tag
- 本周三问：① 容器里第一次 `/ask` 比后续慢多少，慢在哪？② smoke 脚本覆盖了哪 4 条链路，漏了哪条你最想补？③ 面试官问"你怎么部署的"，你按顺序说哪 5 步？
- commit：`Day 35: 第 5 周复盘——服务冒烟脚本、README 与 v0.1.0` + `git tag v0.1.0`

## 第 6 周：主项目迭代 I —— 知识库服务成型（JD 4/6/1）

> 本周起**不引入新框架**，只对 Day 29–35 的服务做增量迭代。每个增量都必须能被 `/openapi.json` 和 smoke 记录证明。

**Day 36 · 文档上传入库（含去重）**
- 阅读（25–30min）：FastAPI `UploadFile` / `File` 文档；Chroma add 幂等性说明
- 编码（50–55min）：`uv add python-multipart`；`POST /documents`：存 `data/uploads/`、算 sha256 去重、切分入库，返回 `{doc_id, chunks, duplicated}`；重复上传返回幂等结果；curl 存 `docs/smoke/day36.txt`
- 复盘三问：① 大文件要不要限大小，限在哪一层？② 去重放在切分前还是后，为什么？③ doc_id 与文件名解耦后，用户改名怎么办？
- commit：`Day 36: 新增文档上传入库接口并做去重`

**Day 37 · 文档列表与删除**
- 阅读（25–30min）：Chroma `delete(ids=/where=)` 文档（无新概念）
- 编码（50–55min）：`GET /documents`（doc_id/source/chunks/created_at 从 metadata 读）；`DELETE /documents/{doc_id}` 同步删向量与上传文件；验证删除后 `/ask` 不再引用该文档；记录存 `docs/smoke/day37.txt`
- 复盘三问：① 删一个文档时，怎么把所有 chunk id 找全？② 软删除和硬删除你选哪个，为什么？③ 同名文件内容更新，是覆盖还是新增版本？
- commit：`Day 37: 实现文档列表与删除接口`

**Day 38 · 多轮追问与查询改写**
- 阅读（25–30min）：LangChain 中文文档"对话式检索 / history-aware retriever"概念页（只读概念，自己实现）
- 编码（50–55min）：`/ask` 增加 `session_id` + 内存 session store；用 LLM 把"它的第二步呢"改写成独立 query 再检索；3 轮对话与改写前后 query 对照存 `docs/smoke/day38.txt`
- 复盘三问：① 改写失败（把独立问题也改了）会怎样？② session 放内存，服务重启后用户看到什么？③ 什么情况下**不该**改写？
- commit：`Day 38: 支持多轮会话与查询改写`

**Day 39 · 引用格式与拒答策略**
- 阅读（25–30min）：重读自己 Day 20 的 prompt，不引入新概念
- 编码（50–55min）：答案强制 `[doc_id#chunk_idx]`；检索为空或最高分 < 阈值 → 直接拒答；`scripts/eval_refusal.py` 跑 10 个无答案 + 10 个有答案问题，统计误答率/误拒率 → `docs/eval_refusal.md`
- 复盘三问：① 阈值调高牺牲了什么，调到多少你不敢再调？② "模型编了一个不存在的 doc_id"你怎么自动检测？③ 误拒和误答哪个更严重，按你的场景说。
- commit：`Day 39: 强化引用格式与拒答策略并统计误答率`

**Day 40 · RAG 评测集 v1**
- 阅读（25–30min）：不引入新内容；先写 10 分钟评测规范（问题类型配比）
- 编码（50–55min）：`data/eval/qa_v1.jsonl` **20 条**（事实型 10 / 多跳 5 / 无法回答 5，带 gold_sources）；`scripts/eval_rag.py` 输出 hit@3、引用正确率、拒答正确率、P50/P95 延迟、平均 token → `docs/eval_v1.md`
- 复盘三问：① hit@3 是多少，卡在哪类问题？② 这 20 条有偏吗（是不是都在你摘过的那几篇里）？③ 哪个指标最能说服面试官，为什么？
- commit：`Day 40: 建立 20 条 RAG 评测集与自动评测脚本`

**Day 41 · 性能与成本**
- 阅读（25–30min）：不引入新内容；读自己的 `logs/usage.jsonl` 10 分钟
- 编码（50–55min）：嵌入缓存（hash→vector 落 `data/embed_cache.json`）；`scripts/load_test.py` 用 asyncio + httpx 打 10 并发 × 10 请求；`docs/perf_v1.md` 写 QPS、P95、单问成本估算
- 复盘三问：① 缓存命中率多少，省了多少 token？② 瓶颈在检索还是生成？③ 8GB 机器上压测要注意什么（别同时开 Docker Desktop + 本地 Ollama）？
- commit：`Day 41: 加嵌入缓存与并发压测并产出性能报告`

**Day 42 · 复盘日 6 + v0.2.0**
- 不写新功能：README 补 mermaid 架构图 + 三条数字（hit@3 / P95 / 单问成本）；`docs/architecture.md` 写数据流；全量 smoke 通过后打 tag
- 本周三问：① 本周 hit@3 比 Day 21 网格时变化多少，来自哪一次改动？② 哪次改动引入了回归，你是怎么发现的？③ 只剩一天优化时间，你改检索还是生成，为什么？
- commit：`Day 42: 第 6 周复盘——v0.2.0、架构图与指标汇总` + `git tag v0.2.0`

## 第 7 周：主项目迭代 II —— Agent / MCP / 测试 / CI（JD 9/10/11/8）

**Day 43 · 把检索注册成工具（Function Calling 进服务）**
- 阅读（25–30min）：重读 DeepSeek Function Calling 文档 10 分钟 + 15 分钟设计工具签名
- 编码（50–55min）：`POST /agent/chat` 注册 `search_docs` / `get_doc_meta` / `list_docs` 三个工具；先只做"最多 1 次工具调用后回答"；轨迹写 `logs/agent_trace.jsonl`；curl 存 `docs/smoke/day43.txt`
- 复盘三问：① 工具描述写得好不好怎么判断（用哪句话能测出来）？② 模型不调工具直接瞎答，你在哪一层拦？③ 工具返回内容太长，你怎么裁剪？
- commit：`Day 43: 把检索能力注册为工具并接入服务`

**Day 44 · Agent 闭环与最大步数**
- 阅读（25–30min）：尚硅谷 P55–P60（执行器/循环）
- 编码（50–55min）：`src/ai_dev_learning/services/agent.py`：Plan→Act→Observe，`max_steps=5`，超限返回 `partial + reason`；支持并行 `tool_calls`；一次 2 步成功 + 一次超步数，记录存 `docs/smoke/day44.txt`
- 复盘三问：① 怎么判定"收敛"（条件写在哪一行）？② partial 结果怎么给用户才不误导？③ 并行工具调用把日志顺序打乱了，你怎么还原轨迹？
- commit：`Day 44: 实现带最大步数的 Agent 执行闭环`

**Day 45 · Agent 五类失败模式与护栏**
- 阅读（25–30min）：尚硅谷 P61–P63（案例）；自己列失败清单 10 分钟
- 编码（50–55min）：制造 5 个坏情况——不存在的工具名、工具抛异常、参数类型错、死循环、用户输入含"忽略上面的指令"；加护栏（工具白名单、异常转 observation、重复调用检测、输入长度限制）；写 `docs/agent_failure_cases.md` 表格：现象/根因/护栏
- 复盘三问：① 哪个失败模式最危险？② 护栏会不会误伤正常请求，你测了吗？③ prompt 注入你在哪一层拦，够不够？
- commit：`Day 45: 补齐 Agent 五类失败模式与护栏`

**Day 46 · MCP 概念 + 最小连通（只求讲清楚）**
- 阅读（25–30min）：MCP 官方文档 Introduction / Architecture（只求说清 client–server–tools/resources 与"解决 M×N 集成"）
- 编码（50–55min）：`uv add mcp`；跑官方 quickstart 的 stdio server（filesystem 或 fetch），用 python client 列出 tools 并调用 1 次；产物：`docs/mcp_notes.md`（一页图 + 与我们工具注册表的对照）+ `scripts/mcp_demo.py` 的终端输出
- 复盘三问：① MCP 和直接写 function calling 的差别在哪？② 为什么公司内部工具适合 MCP？③ 安全边界在哪（谁能连、能碰哪些文件）？
- commit：`Day 46: 跑通 MCP 最小 client 并整理概念笔记`

**Day 47 · 测试：五条关键路径**
- 阅读（25–30min）：pytest + FastAPI TestClient 文档
- 编码（50–55min）：`tests/` 写 `test_health`、`test_chat`（monkeypatch LLM）、`test_ask`（mock retriever）、`test_agent_max_steps`、`test_parse`；`uv run pytest -q` 全绿；用例清单写 `docs/test_report.md`
- 复盘三问：① 哪些必须 mock，为什么不能真调 API？② 哪条测试最容易写成"假绿"？③ CI 里没 key 时这些测试还能跑吗？
- commit：`Day 47: 补 5 组关键路径测试并全绿`

**Day 48 · ruff + GitHub Actions CI**
- 阅读（25–30min）：GitHub Actions Python workflow 模板文档
- 编码（50–55min）：`ruff check` 收口；`scripts/` 补 `dev.sh` / `test.sh` / `eval.sh` / `build.sh`；`.github/workflows/ci.yml`（uv sync → ruff check → pytest，不调真 API）；push 后 Actions 绿灯截图存 `docs/ci.png`，README 加 badge
- 复盘三问：① CI 里哪几步必须离线可跑？② 你关掉了哪几条 lint 规则，为什么？③ badge 红了说明什么，你先看哪一栏？
- commit：`Day 48: 加 ruff 与 GitHub Actions CI 并跑绿`

**Day 49 · 复盘日 7 + v1.0.0**
- 不加功能：全仓整理（删死代码、补 docstring、`README` 终版含 demo 截图 + 三条数字）、`docs/architecture.md` 更新、smoke 全过、打 tag `v1.0.0` 并发 release notes
- 本周三问：① 接口从 Day 29 的 2 个变成几个，哪次改动最大？② CI 第一次红是因为什么，你怎么修的？③ 这个项目最能打的 3 个数字是哪三个（写进 README 顶部）？
- commit：`Day 49: 第 7 周复盘——v1.0.0 与仓库收尾`

## 第 8 周：求职材料与模拟面试（JD 8 收口）

**Day 50 · 简历项目条目（带数字）**
- 阅读（25–30min）：重读 3 份目标 JD，摘关键词清单（不写代码）
- 编码/产出（50–55min）：`career/resume_bullets.md`：4 条 bullet（背景/动作/技术/结果-数字），每条 ≤2 行；附一张"JD 关键词 → 我哪条 bullet 覆盖"的勾选表；数字只从 `docs/eval_v1.md`、`docs/perf_v1.md`、`docs/eval_refusal.md` 里抄
- 复盘三问：① 哪条 bullet 没有数字，能不能补？② 哪个 JD 关键词你还没覆盖，会怎么答？③ HR 6 秒扫过，会记住哪一句？
- commit：`Day 50: 写出带量化指标的简历项目条目`

**Day 51 · 3 分钟项目故事 + 白板稿**
- 阅读（15min）：过一遍三份评测/性能报告
- 编码/产出（50–55min）：`career/project_story.md`（问题→方案→取舍→指标→反思，掐表 3 分钟）+ 白板架构 5 步画法 + 一段录音文件名与自评（卡壳处标出来）
- 复盘三问：① 掐表讲了几分钟，超时在哪一段？② 哪句话是"我做了"而不是"我用了"？③ 被追问最深一层（为什么不用向量数据库服务/为什么切 500）你答得上吗？
- commit：`Day 51: 完成 3 分钟项目故事、白板稿与自评`

**Day 52 · 32 题面试题库（带项目证据）**
- 阅读（25–30min）：重读 Day 51 的故事稿与 `docs/eval_v1.md`，挑出你最想被追问的 3 个技术点，作为今天出题的靶子
- 编码/产出（50–55min）：`career/interview_qa.md` 四组各 8 题（RAG 12 / LangChain 6 / FastAPI 6 / Docker+工程 8），每题 3–5 行要点 + 1 个仓库内证据（文件路径）
- 复盘三问：① 哪题你只能背不能举例？② 哪题答案和项目实现不一致（要改代码还是改答案）？③ 哪题最可能被连追三层？
- commit：`Day 52: 整理 32 道高频面试题与项目证据`

**Day 53 · 手写题 + 成本八股**
- 阅读（15min）：余弦相似度、top-k 复杂度
- 编码/产出（50–55min）：`career/coding/cosine_topk.py`（纯 Python） + `tests/test_cosine_topk.py`（空向量、维度不等、k>n 三个边界）；`career/token_cost.md` 用真实 usage 算一次单问成本
- 复盘三问：① 你的实现复杂度，10 万向量时怎么优化？② 维度不等怎么处理（报错还是截断）？③ token 估算的误差来源有哪些？
- commit：`Day 53: 手写 top-k 余弦检索并补测试`

**Day 54 · 模拟面试 1**
- 阅读（10min）：过 story + qa
- 编码/产出（50–55min）：`career/mock/mock01.md`：自问自答 45 分钟录音，记录 5 个答崩的问题 + 改进动作；针对最差 1 题重写答案
- 复盘三问：① 5 个崩点里哪几个是知识缺口、哪几个是表达问题？② 时间控制如何，哪题讲太长？③ 下次只改一件事，改哪件？
- commit：`Day 54: 完成第一次模拟面试并记录 5 个崩点`

**Day 55 · 模拟面试 2 + 投递清单**
- 阅读（10min）：复盘 mock01 的 5 个崩点
- 编码/产出（50–55min）：`career/mock/mock02.md` 针对 5 个崩点重答并录音对比；`career/jd_match.md`：10 家目标公司 × JD 关键词匹配度 + 缺口与补救动作
- 复盘三问：① 5 个崩点补上了几个？② 匹配度最低那家差什么？③ 投递前仓库还差什么（README？demo？）？
- commit：`Day 55: 第二次模拟面试与目标公司匹配清单`

**Day 56 · 复盘日 8 + 总复盘**
- 不写新内容：全仓最终整理；README 顶部放 demo 截图 + 架构图 + 三条数字；release notes 写清 v1.0 能力边界；`career/30day_plan.md` 写未来 30 天补的两个短板
- 总三问：① 56 天里哪个产物最能证明 JD 第 4 条（RAG 全链路），路径是什么？② 如果重来，砍掉哪一周的哪一天？③ 接下来 30 天补哪 2 个短板，各自第一天的动作是什么？
- commit：`Day 56: 第 8 周复盘——8 周总复盘与 release` + `git tag v1.0.1`

---

# 第三部分 · 每日发送指令模板（直接复制）

**用法**：只改两个地方——`第 【X】 天` 和`【今日主题】`。下面这段整段发给 DeepSeek（或其他教练模型）。

```text
你是我的 AI 应用开发教练。以下是我的固定背景，不要重复询问：

- 苏州大学软件工程本科 2025 届；Python 有基础、会基本数据结构，不教语法。
- 设备 MacBook Air M1 / 8GB / macOS 15；uv + Python 3.11；仓库 /Users/guo/ai-dev-learning（src 布局，包名 ai_dev_learning）。
- 每天 1.5 小时，只有三段：阅读 25 分钟 + 编码 50 分钟 + 复盘 15 分钟。超时即停。
- 硬约束：不在本地跑生成模型，生成一律走 DeepSeek 云端 API；向量库只用 ChromaDB 且持久化在项目内；不装任何需要 GPU 的依赖；不推荐 7B 以上本地模型。

今天是 第 【X】 天，今日主题：【今日主题】。

请严格按下面 4 步执行，不许跳步、不许加量。

【第 0 步 · 预热（1 个问题，等我回答）】
先问我一个关于今天主题的具体问题，检验我已经掌握的部分。只问一个，不要给答案，等我回答后再进入第 1 步。
如果我的回答有明显偏差，先指出一句，再继续。

【第 1 步 · 三段任务】
- 阅读（25 分钟）：指定今天该看的具体分 P 或文档章节名，并告诉我"只看这一段，要解决的那 1 个问题"。
- 编码（50 分钟）：给 1 个可验证动作，写清产物路径和"跑通时屏幕上应该出现什么"。产物必须在 /Users/guo/ai-dev-learning 下。
- 复盘（15 分钟）：按下面的复盘三问问我。

【第 2 步 · 我贴代码或报错时】
先问我两句：「你预期它做什么？」「实际发生了什么（贴报错原文/输出原文）？」——我答完你再动。
然后一次只指出一个最可能的原因，给一个最小验证动作（一行命令或一处 print），等我看结果。
禁止：重写我的文件、一次给多个改法、直接贴完整正确代码、未经我确认就换方案。

【第 3 步 · 收尾（必须执行完才算今天结束）】
1) 逼我用三句话回答复盘：今天这东西实际做了什么（一句运行结果）／最大卡点及处理／明天只改一处改哪里。
2) 给我一条 commit message：`Day X: 一句话`。
3) 让我更新 README 今日一行：`- Day X｜做了什么｜产物路径｜今天的卡点`。
4) 让我列出今天产物的文件名 + 一行终端输出，你判断是否真的存在。

补充约束：如果你觉得该加任务，先问我"今天还剩多少分钟"，不许默认我有额外时间。
现在开始第 0 步。
```

填充示例（Day 17）：

```text
今天是 第 17 天，今日主题：接入 bge-m3 云端嵌入并做相似度自检
```

---

# 第四部分 · JD 覆盖自检表

| # | JD 要求 | 覆盖位置 | 证据产物 | 覆盖度 |
|---|---|---|---|---|
| 1 | Python 后端工程能力 | W1 D3/D6；W5 D32；W7 D47/D48 | `common/llm.py`（超时/重试/日志）、`core/config.py`、`tests/`、CI workflow | 90% |
| 2 | 大模型 API 调用（参数/usage 追踪） | W1 D1–D6；W4 D22 | `logs/usage.jsonl`、`day02_params.md`、`day22_lc_model.md` | 100% |
| 3 | Prompt 设计（角色/Few-shot/结构化约束） | W2 D8–D11 | `prompts/*.md`、`eval_prompt.py`、准确率报告 | 95% |
| 4 | RAG 全链路（加载→切分→向量化→库→检索→生成） | W3 D15–D21；W6 D36–D41 | `data/chroma/`、`rag_min.py`、`docs/eval_v1.md`、`docs/eval_refusal.md` | 100% |
| 5 | LangChain 核心（Model I/O / PromptTemplate / OutputParser / Retriever / LCEL） | W4 D22–D28 | `lc_model.py`、`day23_prompts.py`、`day24_parsers.py`、`day26_retriever.py`、`lc_rag.py` | 95% |
| 6 | FastAPI 服务封装（校验/健康检查/接口设计） | W5 D29–D32；W6 D36–D38 | `/health` `/chat` `/ask` `/search` `/documents`、`openapi.json` 片段 | 95% |
| 7 | Docker（Dockerfile / compose / .env） | W5 D33–D34 | `Dockerfile`、`.dockerignore`、`docker-compose.yml`、卷持久化验证 | 90% |
| 8 | Git 规范提交与可复现 README | 全 56 天；D35/D42/D49/D56 加码 | commit 序列、8 个 tag、README quickstart、`scripts/smoke_test.sh`、CI | 95% |
| 9 | Function Calling / Tool Calls | W2 D12–D13；W7 D43–D44 | `day12_trace.json`、`logs/tool_trace.jsonl`、`/agent/chat`、`logs/agent_trace.jsonl` | 90% |
| 10 | Agent 最小闭环（工具选择/轨迹/步数控制） | W7 D44–D45 | `services/agent.py`（max_steps=5）、`agent_failure_cases.md` | 85% |
| 11 | MCP 概念性理解 | W7 D46 | `docs/mcp_notes.md` + `scripts/mcp_demo.py` 输出 | 80% |
| 12 | 加分项联动（评测/成本/CI） | W6 D40–D41；W7 D47–D48 | 三份评估报告、`docs/perf_v1.md`、Actions 绿灯 | 90% |

**调整说明（初稿不足 80% 的三项已在上表修正）**：
1. **Docker 初稿只有 `docker build`，compose 被挤到 W6（违反"36–49 不引入新概念"）** → 把 compose、卷挂载、healthcheck 前移到 D34，D35 改纯复盘。
2. **Function Calling 初稿只在脚本里跑通（不算"能写在简历上"）** → 拆成 D12/D13（离线理解机制）+ D43/D44（进服务、有轨迹、有护栏），同一技能两次触达。
3. **Git/README 初稿只到"每天 commit"** → 补 smoke 脚本（D35）、release tag（D42/D49/D56）、CI（D48），让"可复现"有可点开的证据。
4. **MCP 压到 1 天**：JD 只要求"知道解决什么问题"，D46 产出一页笔记 + 一次最小连通即达标，不接进主服务。
5. **LangChain 后置到 W4**：先 W3 手写 RAG 再上框架，避免"只会 LCEL 不懂链路"，同时让 D28 的对照文档成为面试素材。
6. **嵌入走云端 bge-m3**：DeepSeek 无 embedding 接口；`nomic-embed-text` 只在 D21 做一次本地对照（8GB 可承受），维度不同故用独立 collection。

---

# 附：执行底座（一次性配置，约 30 分钟，可拆进 Day 1–2）

**最终仓库结构**

```
ai-dev-learning/
├── README.md                    # 顶部：三条数字 + 架构图 + Quickstart
├── pyproject.toml / uv.lock
├── .env.example                 # 提交；.env 永不提交
├── src/ai_dev_learning/
│   ├── main.py                  # FastAPI app（lifespan）
│   ├── core/config.py
│   ├── common/{llm.py,embeddings.py}
│   ├── services/{rag.py,ingest.py,agent.py}
│   └── api/{chat.py,routes_rag.py,routes_docs.py,routes_agent.py}
├── lessons/w1..w4/{脚本 + out/}  # 日课产物（提交）
├── data/{corpus,jd_sample.md,chunks.jsonl,eval/}   # 提交
├── data/{chroma,uploads,embed_cache.json}          # gitignore
├── logs/                        # gitignore
├── scripts/{smoke_test.sh,eval_rag.py,load_test.py,mcp_demo.py}
├── tests/
├── docs/{smoke/,eval_v1.md,eval_refusal.md,perf_v1.md,architecture.md,agent_failure_cases.md,mcp_notes.md}
├── career/{resume_bullets.md,project_story.md,interview_qa.md,mock/,coding/}
├── Dockerfile / docker-compose.yml / .dockerignore
└── .github/workflows/ci.yml
```

**依赖分批加入（每周执行一次）**

```bash
uv add openai python-dotenv pydantic      # W1
uv add chromadb pypdf                     # W3
uv add langchain langchain-openai langchain-community langchain-chroma   # W4
uv add fastapi "uvicorn[standard]" pydantic-settings python-multipart httpx  # W5
uv add mcp                                # W7
```

**.env.example 全字段**：`DEEPSEEK_API_KEY` `DEEPSEEK_BASE_URL` `DEEPSEEK_BETA_BASE_URL` `LLM_MODEL=deepseek-chat` `EMBED_PROVIDER=siliconflow|ollama` `SILICONFLOW_API_KEY` `EMBED_MODEL=BAAI/bge-m3` `OLLAMA_BASE_URL` `CHROMA_DIR=./data/chroma` `TOP_K=4` `SCORE_THRESHOLD=0.35`

**降级规则（超时/卡死时用，不许因此跳过当天）**

| 情况 | 降级产物（仍算完成） |
|---|---|
| 编码超时 | 只保留 1 个能跑的最小脚本 + `out/` 里一段真实终端输出 |
| API 密钥/额度故障 | 用缓存响应跑通链路，把"错误处理"本身写成当天产物 |
| Docker 拉镜像太慢 | 本地 uvicorn 验证通过 + Dockerfile 写对并 `docker build --check`，次日补 |
| 评测集写不完 | 20 条降到 10 条，宁可少而准，报告里注明样本量 |
| 视频分 P 不匹配 | 换官方文档同主题章节，产物不变 |

**8GB 红线检查（每天 10 秒）**：不开 Ollama + Docker Desktop 同时跑；不 `pull` 任何 >1GB 生成模型镜像；`data/chroma` 只留 1–2 个 collection；`docker compose down` 后再结束当天。
