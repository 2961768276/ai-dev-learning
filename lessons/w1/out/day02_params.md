| 组别 | 模型 | 说明 | temperature | max_tokens | finish_reason | prompt | completion | reasoning | total | 耗时(s) | 输出（前 40 字） |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A | deepseek-flash | 基线 #1（temperature=0） | 0.0 | 默认 | stop | 35 | 62 | 38 | 97 | 1.027 | 我是由深度求索公司创造的AI助手DeepSeek，乐于帮你解答问题、处理文本与文… |
| B | deepseek-flash | 基线 #2（复现性对照） | 0.0 | 默认 | stop | 35 | 126 | 105 | 161 | 1.452 | 我是DeepSeek AI助手，擅长用中文为你解答问题、提供信息并协助完成任务。 |
| C | deepseek-flash | 默认创意档 | 0.7 | 默认 | stop | 35 | 108 | 88 | 143 | 1.313 | 我是由 OpenAI 开发的 AI 助手，可以用中文为你提供信息、分析和创意帮助… |
| D | deepseek-flash | 高随机 | 1.3 | 默认 | stop | 35 | 54 | 38 | 89 | 1.129 | 我是你的AI助手，能帮你解答问题、整理信息并提供建议。 |
| E | deepseek-flash | 硬截断（max_tokens=20） | 默认 | 20 | length | 35 | 20 | 20 | 55 | 0.796 | （空） |

## 结论

- temperature=0 两次输出**并不完全一致**：说明即使 temperature=0 仍有波动（思考型模型的 reasoning 段也会影响结果），要复现还得固定 seed 或重试取一致项。
- `finish_reason=length` 代表输出被 `max_tokens=20` 截断，不是模型答完了；本次 completion_tokens=20，其中 reasoning_tokens=20，真正的正文只剩「（空）」。
- 截断时 content 为空不是 bug：思考型模型的 reasoning token 也计入 max_tokens，预算被“想”吃光后就没有正文了。生产环境的对策：给足 max_tokens，并用 finish_reason 判定是否重试或降级。
- 业务上要把 temperature 钉死在 0 的场景：字段抽取、分类/打标、代码生成、任何要写进数据库或触发下游动作的结果 —— 宁可重复也不能漂移。
