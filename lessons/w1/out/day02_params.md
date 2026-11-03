| 组别 | 说明 | temperature | max_tokens | finish_reason | prompt | completion | reasoning | total | 耗时(s) | 输出（前 40 字） |
|---|---|---|---|---|---|---|---|---|---|---|
| A | 基线 #1（temperature=0） | 0.0 | 默认 | stop | 35 | 45 | 27 | 80 | 1.264 | 我是一个乐于助人的AI助手，随时为你解答问题、提供建议与支持。 |
| B | 基线 #2（复现性对照） | 0.0 | 默认 | stop | 35 | 78 | 63 | 113 | 1.321 | 我是一个乐于用中文为你解答问题、提供帮助的AI助手。 |
| C | 默认创意档 | 0.7 | 默认 | stop | 35 | 55 | 34 | 90 | 1.076 | 我是由深度求索公司开发的AI助手，乐于为你提供清晰、可靠的信息和帮助。 |
| D | 高随机 | 1.3 | 默认 | stop | 35 | 129 | 108 | 164 | 1.345 | 我是由深度求索公司打造的AI助手DeepSeek，乐于为你解答问题并提供帮助。 |
| E | 硬截断（max_tokens=20） | 默认 | 20 | length | 35 | 20 | 20 | 55 | 0.905 | （空） |

## 结论

- temperature=0 两次输出**并不完全一致**：说明即使 temperature=0 仍有波动（思考型模型的 reasoning 段也会影响结果），要复现还得固定 seed 或重试取一致项。
- `finish_reason=length` 代表输出被 `max_tokens=20` 截断，不是模型答完了；本次 completion_tokens=20，其中 reasoning_tokens=20，真正的正文只剩「（空）」。
- 截断时 content 为空不是 bug：思考型模型的 reasoning token 也计入 max_tokens，预算被“想”吃光后就没有正文了。生产环境的对策：给足 max_tokens，并用 finish_reason 判定是否重试或降级。
- 业务上要把 temperature 钉死在 0 的场景：字段抽取、分类/打标、代码生成、任何要写进数据库或触发下游动作的结果 —— 宁可重复也不能漂移。
