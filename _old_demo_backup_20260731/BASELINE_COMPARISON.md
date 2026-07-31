# 与官方 Baseline 的差异说明

官方 baseline 地址：

<https://github.com/InternLM/Challenge-Cup-2026>

本文用于说明当前项目和官方 baseline 的主要区别，以及这些区别是否会影响比赛提交。

## 一、结论

当前项目和官方 baseline **不是逐字一致**，但核心入口是兼容的：

```python
from user_agent import ReasoningAgent

agent = ReasoningAgent(client=official_client)
result = agent.solve(problem: str, metadata: dict)
```

当前项目满足比赛最关键要求：

| 要求 | 当前项目状态 |
| --- | --- |
| 根目录存在 `user_agent.py` | 满足 |
| 定义 `ReasoningAgent` 类 | 满足 |
| 构造函数接收 `client` | 满足 |
| 实现 `solve(problem: str, metadata: dict) -> dict` | 满足 |
| 返回非空 `final_response` | 满足 |
| 返回对象可 JSON 序列化 | 满足 |
| 不硬编码 API Key | 满足 |
| 本地调试不读取标准答案 | 已修正 |

所以，只要正式提交时所有源码和依赖都放在仓库里，一般不会因为“没有完全照抄 baseline”而出问题。

## 二、官方 Baseline 的结构

官方仓库核心文件大致是：

```text
.
├── user_agent.py
├── main.py
├── llm_client.py
├── requirements.txt
├── sample_data/
└── tests/
```

官方 baseline 的重点是：

- 提供最小可运行链路。
- 展示平台如何调用 `ReasoningAgent.solve()`。
- 展示输入输出 JSON 格式。
- 展示本地 API client 调用方式。
- 展示一个 generate-verify-select 的智能体样例。

## 三、当前项目结构

当前项目结构：

```text
.
├── user_agent.py
├── main.py
├── demo_chat.py
├── llm_client.py
├── requirements.txt
├── prompts/
├── tools/
├── utils/
├── sample_data/
├── tests/
├── README.md
├── ARCHITECTURE.md
├── BASELINE_COMPARISON.md
├── .env.example
└── .gitignore
```

当前项目在官方 baseline 基础上多了：

| 文件 / 目录 | 作用 |
| --- | --- |
| `demo_chat.py` | 最小直连 LLM demo，只测试 API 是否能返回 |
| `prompts/` | 把提示词从代码里拆出来 |
| `utils/` | 放答案抽取、JSONL、环境变量读取等工具 |
| `tools/` | 后续放数学工具 |
| `.env.example` | 本地配置模板 |
| `ARCHITECTURE.md` | 项目架构说明 |
| `BASELINE_COMPARISON.md` | 当前差异说明 |

这些新增文件不会破坏官方入口。

## 四、关键差异

### 1. `user_agent.py` 差异

官方 baseline：

- 使用 `lagent` 框架。
- 在代码中定义 policy prompt 和 verifier prompt。
- 默认生成多个候选答案。
- verifier 多次投票。
- 选择置信度最高的候选。

当前项目：

- 不依赖 `lagent`。
- 直接使用传入的 `client.chat()`。
- prompt 拆到 `prompts/` 目录。
- 当前默认是主解题一次 + 复核一次。
- 增加了 `final_response` 抽取和规整逻辑。

是否有问题：

```text
没有本质问题。
```

比赛规则允许选手自由修改、重构、替换 baseline，只强制遵守入口文件和方法签名。

需要注意：

- `prompts/` 和 `utils/` 必须一起提交。
- `requirements.txt` 要覆盖所有新增依赖。
- 不要只提交 `user_agent.py`，否则导入 `utils` 和读取 prompt 会失败。

### 2. `main.py` 差异

官方 baseline：

- 使用 `asyncio` 并发运行。
- 通过 `LOCAL_MAX_CONCURRENCY` 控制并发。
- `--input_file` 和 `--output_dir` 是必填参数。
- 传给 `solve()` 的 metadata 只包含 `idx`。
- 输出文件已存在时跳过。

当前项目：

- 先用同步 runner，便于理解和调试。
- 参数有默认值。
- 支持 `--overwrite` 强制重跑。
- 终端会直接打印 `final_response`。
- 当前已经排除了本地样例里的 `answer` 字段，不会传给 agent。

是否有问题：

```text
正式评测一般不会运行你的 main.py，而是平台自己调用 user_agent.py。
所以 main.py 差异通常不影响正式评测。
```

但为了后续更贴近官方流程，可以再把并发 runner 补回来。

### 3. `llm_client.py` 差异

官方 baseline：

- 使用 `requests`。
- 默认 OpenAI-compatible `/api/v1/chat/completions`。
- 使用 `Authorization: Bearer ...`。
- 支持 `thinking_mode`、`tools`、额外 request args。
- 内置 retry。

当前项目：

- 使用 Python 标准库 `urllib`，减少依赖。
- 支持两种本地 API 风格：
  - `messages`
  - `chat`
- 通过 `.env` 控制 API Key、URL、模型。
- 支持最小直连 demo。
- 暂时没有完整 retry 机制。

是否有问题：

```text
正式评测时平台会注入 official_client，本地 llm_client.py 通常不会被平台使用。
```

但本地调试会用它。你现在 `demo_chat.py` 已经能返回，说明本地 client 当前可用。

### 4. `requirements.txt` 差异

官方 baseline：

- 包含 baseline 运行所需依赖，例如 `requests`、`lagent` 等。

当前项目：

- 当前 demo 基本只依赖 Python 标准库。
- 不需要 `lagent`。
- 不需要 `requests`。

是否有问题：

```text
没有问题。
```

前提是后续如果你添加 `sympy`、`numpy`、`requests` 等库，必须写入 `requirements.txt`。

### 5. Prompt 管理差异

官方 baseline：

- prompt 写在 `user_agent.py` 里面。

当前项目：

- prompt 放在 `prompts/`。

是否有问题：

```text
没有问题，但提交时必须带上 prompts/ 目录。
```

这是工程化上的改进，后续更容易按题型拆 prompt。

## 五、目前已修正的风险

### 本地调试 `answer` 泄露

样例 JSONL 里通常有：

```json
{"idx": 0, "problem": "...", "answer": "72"}
```

正式评测不会传 `answer`。

之前本地 runner 会把除 `problem` 以外的字段都传入 metadata，这意味着本地调试时 `answer` 也会进入 agent。虽然当前 prompt 没有主动用标准答案，但这不符合严格自测习惯。

现在已改为：

```python
metadata = {
    key: value
    for key, value in item.items()
    if key not in {"problem", "answer"}
}
```

这样本地 runner 不会把标准答案传给 agent。

## 六、提交前还要注意什么

### 1. 不要提交 `.env`

`.env` 里有真实 API Key，不能提交。

应提交：

```text
.env.example
```

不应提交：

```text
.env
```

### 2. 确认根目录必须有 `user_agent.py`

正式评测入口只认：

```text
user_agent.py
```

不要把它移动到子目录。

### 3. 确认所有相对资源都提交

因为当前 `user_agent.py` 会读取：

```text
prompts/math_system.txt
prompts/solver_prompt.txt
prompts/verifier_prompt.txt
```

所以提交时必须包含 `prompts/`。

### 4. 确认导入没有缺依赖

提交前执行：

```bash
python -m py_compile user_agent.py main.py llm_client.py demo_chat.py
```

再执行：

```bash
python main.py --input_file sample_data/dev.jsonl --output_dir sample_outputs --overwrite
```

### 5. 以后加第三方库要写入 `requirements.txt`

比如加 `sympy` 后：

```text
sympy>=1.13.0
```

否则平台环境可能找不到依赖。

## 七、会不会有问题

当前结论：

```text
按比赛入口规范看，当前项目不会因为和官方 baseline 不一样而有问题。
```

真正需要关注的是：

1. `user_agent.py` 是否能被导入。
2. `ReasoningAgent(client=official_client)` 是否能实例化。
3. `solve(problem, metadata)` 是否返回非空 `final_response`。
4. 所有辅助文件是否一起提交。
5. 没有提交 `.env`、标准答案、硬编码密钥。

当前项目已经满足前 3 点，且 `.gitignore` 已忽略 `.env` 和输出目录。

## 八、建议下一步

为了更贴近官方 baseline，可以后续逐步做三件事：

1. 给 `llm_client.py` 加 retry，避免网络抖动导致本地调试失败。
2. 给 `main.py` 加并发参数 `LOCAL_MAX_CONCURRENCY`，模拟官方 runner。
3. 在 `user_agent.py` 里恢复多候选生成和 verifier 投票，提高正确率。

这三件事不是合规必需项，但会让工程更接近官方 baseline，也更适合比赛。
