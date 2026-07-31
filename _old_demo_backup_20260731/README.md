# Math-Agent Demo

Intern-S 数学推理智能体初始工程。当前版本用于先在 conda 环境中跑通比赛固定入口和本地 JSONL 调试流程，后续可继续增强提示词、多候选、自校验、符号工具和 Docker 部署。

## 目录结构

```text
.
├── user_agent.py              # 必填：平台固定导入入口
├── main.py                    # 本地 JSONL runner
├── llm_client.py              # 本地 Intern API client + 离线 demo client
├── requirements.txt           # 依赖清单
├── prompts/                   # 提示词模板
├── tools/                     # 自定义数学工具扩展目录
├── utils/                     # 通用工具
├── sample_data/dev.jsonl      # 本地样例
└── tests/                     # 轻量契约测试
```

## 固定入口

评测平台会调用：

```python
from user_agent import ReasoningAgent

agent = ReasoningAgent(client=official_client)
result = agent.solve(problem: str, metadata: dict)
```

`solve` 返回：

```python
{
    "final_response": "72",
    "trace": [
        {"step": "plan", "content": "..."}
    ]
}
```

## Conda 本地运行

```bash
conda create -n math-agent python=3.11 -y
conda activate math-agent
pip install -r requirements.txt
python main.py --input_file sample_data/dev.jsonl --output_dir sample_outputs --overwrite
```

如果没有配置 `INTERN_API_KEY`，项目会使用 `DemoRuleClient` 跑通样例链路。

本地推荐直接编辑 `.env`：

```bash
cp .env.example .env
```

然后填写：

```text
INTERN_API_KEY=sk-xxxx
INTERN_MODEL=intern-s1
INTERN_API_STYLE=messages
INTERN_API_URL=https://chat.intern-ai.org.cn/v1/messages

AGENT_SOLVE_TEMPERATURE=0.2
AGENT_VERIFY_TEMPERATURE=0.0
AGENT_SOLVE_MAX_TOKENS=4096
AGENT_VERIFY_MAX_TOKENS=2048
```

也可以用环境变量临时覆盖 `.env`：

```bash
export INTERN_API_KEY="sk-xxxx"
export INTERN_MODEL="intern-s2-preview"
python main.py --input_file sample_data/dev.jsonl --output_dir sample_outputs --overwrite
```

如官方文档给出不同 API 网关：

```bash
export INTERN_API_BASE="https://your-api-base"
```

`INTERN_API_BASE` 可以填到 `/api/v1`，如果误填成完整的 `/chat/completions`，本地 client 会自动裁掉后缀。

## 常用参数

| 配置项 | 作用 | 建议值 |
| --- | --- | --- |
| `INTERN_MODEL` | 选择模型 | `intern-s2-preview` / `intern-s1` / `intern-s1-pro` |
| `INTERN_API_STYLE` | 本地 API 协议 | `messages` 或 `chat` |
| `INTERN_API_URL` | messages 接口地址 | `https://chat.intern-ai.org.cn/v1/messages` |
| `INTERN_THINKING_MODE` | chat 接口思考模式 | `true` 或 `false` |
| `AGENT_SOLVE_MAX_TOKENS` | 主解题调用的 `max_tokens` | `4096` |
| `AGENT_VERIFY_MAX_TOKENS` | 复核调用的 `max_tokens` | `2048` |
| `AGENT_SOLVE_TEMPERATURE` | 主解题温度 | `0.2` |
| `AGENT_VERIFY_TEMPERATURE` | 复核温度 | `0.0` |

## 最小直连 LLM Demo

如果只想确认 API 能返回内容，不走智能体、不做答案抽取：

```bash
python demo_chat.py "计算 17+25 的值"
```

也可以交互输入：

```bash
python demo_chat.py
```

## 下一步建议

1. 加入 `sympy` 等数学工具，在 `tools/` 中实现表达式校验、方程求解、数值验证。
2. 按题型拆分 prompts，例如代数、几何、数论、组合、概率。
3. 将 `_generate_solution` 扩展为多候选采样，再用 verifier 投票筛选。
4. 补充 Dockerfile，固定 Python 版本、依赖安装和启动命令。
