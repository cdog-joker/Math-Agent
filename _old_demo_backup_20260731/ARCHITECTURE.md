# Math-Agent 项目架构说明

当前项目已经完成最小 demo：

1. `demo_chat.py` 可以直接调用 LLM，并在终端打印原始回答。
2. `main.py` 可以模拟比赛 Runner，读取 JSONL 题目，调用 `ReasoningAgent.solve()`，输出标准 JSON 文件。
3. `user_agent.py` 已满足比赛固定入口规范。

## 一、整体调用链路

### 1. 最小直连 LLM Demo

适合验证 API Key、URL、模型名是否可用。

```text
终端命令
  |
  v
demo_chat.py
  |
  v
llm_client.build_local_client()
  |
  v
InternMessagesClient / InternChatClient
  |
  v
书生 Intern-S API
  |
  v
终端打印 LLM 原始回答
```

运行方式：

```bash
python demo_chat.py "计算 17+25 的值"
```

如果能返回模型回答，说明本地 API 调用链路已经跑通。

### 2. 比赛入口模拟链路

适合验证代码是否符合赛事调用格式。

```text
sample_data/dev.jsonl
  |
  v
main.py
  |
  v
ReasoningAgent.solve(problem, metadata)
  |
  v
llm_client.build_local_client()
  |
  v
Intern-S API
  |
  v
答案抽取与格式化
  |
  v
sample_outputs/{idx}.json
```

运行方式：

```bash
python main.py --input_file sample_data/dev.jsonl --output_dir sample_outputs --overwrite
```

如果终端显示：

```text
idx=0 final_response=...
wrote: sample_outputs/0.json
```

并生成输出 JSON，说明本地比赛流程已经跑通。

## 二、核心文件说明

### `demo_chat.py`

最小直连 LLM 脚本。

作用：

- 不使用智能体。
- 不做答案抽取。
- 不做二次校验。
- 只把用户问题发给 LLM，然后打印原始回答。

适合：

- 测试 API Key 是否有效。
- 测试 API URL 是否正确。
- 测试模型是否可调用。
- 快速观察模型原始输出。

示例：

```bash
python demo_chat.py "你好，介绍一下你自己"
```

### `main.py`

本地比赛 Runner。

作用：

- 读取 JSONL 输入文件。
- 每一行作为一道题。
- 调用 `ReasoningAgent.solve(problem, metadata)`。
- 把结果写入 `sample_outputs/{idx}.json`。
- 如果输出文件已存在且非空，默认跳过；加 `--overwrite` 可重新运行。

示例：

```bash
python main.py --input_file sample_data/dev.jsonl --output_dir sample_outputs --overwrite
```

### `user_agent.py`

比赛最重要的文件，也是正式评测平台会导入的入口文件。

必须满足：

```python
from user_agent import ReasoningAgent

agent = ReasoningAgent(client=official_client)
result = agent.solve(problem: str, metadata: dict)
```

当前实现流程：

```text
solve()
  |
  v
构造解题 prompt
  |
  v
调用 LLM 生成 primary candidate
  |
  v
调用 LLM 做 verifier 复核
  |
  v
选择候选答案
  |
  v
抽取并规整 final_response
  |
  v
返回 {"final_response": "...", "trace": [...]}
```

正式比赛时，平台只强制关心：

```python
{
    "final_response": "最终答案"
}
```

`trace` 主要用于排查问题和展示智能体设计过程。

### `llm_client.py`

本地 LLM 客户端封装。

正式评测时平台会注入官方 client，所以这个文件主要服务本地调试。

包含三个 client：

| 类名 | 作用 |
| --- | --- |
| `InternMessagesClient` | 调用 `https://chat.intern-ai.org.cn/v1/messages` 风格接口 |
| `InternChatClient` | 调用 `/chat/completions` 风格接口 |
| `DemoRuleClient` | 没有 API Key 时使用的离线规则 demo |

入口函数：

```python
build_local_client()
```

它会：

1. 读取 `.env`。
2. 判断是否配置了 `INTERN_API_KEY`。
3. 根据 `INTERN_API_STYLE` 或 URL 自动选择 client。

推荐本地配置：

```text
INTERN_API_KEY=你的真实key
INTERN_MODEL=intern-s1
INTERN_API_STYLE=messages
INTERN_API_URL=https://chat.intern-ai.org.cn/v1/messages
```

### `.env`

本地私有配置文件。

作用：

- 存 API Key。
- 存模型名。
- 存 API 地址。
- 存 max_tokens、temperature 等本地调参项。

注意：

- `.env` 已被 `.gitignore` 忽略。
- 不要提交到 AtomGit。
- 不要把真实 API Key 写进代码。

示例：

```text
INTERN_API_KEY=你的真实key
INTERN_MODEL=intern-s1
INTERN_API_STYLE=messages
INTERN_API_URL=https://chat.intern-ai.org.cn/v1/messages

AGENT_SOLVE_TEMPERATURE=0.2
AGENT_VERIFY_TEMPERATURE=0.0
AGENT_SOLVE_MAX_TOKENS=4096
AGENT_VERIFY_MAX_TOKENS=2048
```

### `.env.example`

可提交的配置模板。

作用：

- 告诉队友需要哪些环境变量。
- 不包含真实密钥。
- 后续迁移 Docker 时可作为环境变量参考。

### `requirements.txt`

Python 依赖清单。

当前 demo 基本只使用 Python 标准库，所以里面没有强制依赖。

后续如果加入数学工具，可以添加：

```text
sympy>=1.13.0
```

如果加入测试工具，可以添加：

```text
pytest>=8.0.0
```

### `README.md`

项目快速使用说明。

主要面向：

- 如何创建 conda 环境。
- 如何填写 `.env`。
- 如何运行 `demo_chat.py`。
- 如何运行 `main.py`。

### `ARCHITECTURE.md`

当前这个文件。

作用：

- 解释项目结构。
- 解释每个文件做什么。
- 解释两条运行链路。
- 作为后续开发的架构说明。

## 三、目录说明

### `prompts/`

存放提示词模板。

当前包含：

| 文件 | 作用 |
| --- | --- |
| `math_system.txt` | 系统提示词，约束模型作为数学推理智能体 |
| `solver_prompt.txt` | 主解题提示词 |
| `verifier_prompt.txt` | 二次复核提示词 |

后续可以按题型继续拆分：

```text
prompts/
├── algebra.txt
├── geometry.txt
├── number_theory.txt
├── combinatorics.txt
└── probability.txt
```

### `utils/`

通用工具目录。

当前包含：

| 文件 | 作用 |
| --- | --- |
| `env_loader.py` | 读取 `.env` 文件 |
| `prompt_loader.py` | 按相对路径读取 prompts |
| `answer_utils.py` | 从模型输出里抽取和规整最终答案 |
| `jsonl.py` | 读取 JSONL、写 JSON |
| `__init__.py` | Python 包标记文件 |

### `tools/`

数学工具扩展目录。

当前只有空的 `__init__.py`。

后续适合放：

- `sympy` 表达式校验。
- 方程求解。
- 数值代入验证。
- 几何辅助计算。
- 有限域、数论、组合数学工具。

示例规划：

```text
tools/
├── symbolic.py
├── equation_solver.py
├── number_theory.py
└── finite_field.py
```

### `sample_data/`

本地样例输入数据。

当前文件：

```text
sample_data/dev.jsonl
```

每行一道题：

```json
{"idx": 0, "problem": "题目文本", "answer": "本地调试答案"}
```

注意：

- `answer` 只用于本地调试。
- 正式评测不会把标准答案传给代码。
- `user_agent.py` 不能依赖 `answer`。

### `sample_outputs/`

本地运行输出目录。

由 `main.py` 自动生成。

示例：

```text
sample_outputs/
├── 0.json
└── 1.json
```

该目录已被 `.gitignore` 忽略，不建议提交。

### `tests/`

轻量测试目录。

当前文件：

```text
tests/test_agent_contract.py
```

主要检查：

- `ReasoningAgent` 可以实例化。
- `solve()` 返回 dict。
- `final_response` 是非空字符串。
- `trace` 是数组。

## 四、当前运行模式

### 模式 1：只测 API

使用：

```bash
python demo_chat.py "计算 1+1"
```

这是最小 demo。

只要有输出，就说明 API 跑通。

### 模式 2：测比赛格式

使用：

```bash
python main.py --input_file sample_data/dev.jsonl --output_dir sample_outputs --overwrite
```

这会经过：

```text
JSONL 输入 -> ReasoningAgent -> LLM -> final_response -> JSON 输出
```

这是正式比赛前必须保证能跑通的链路。

### 模式 3：正式评测

正式平台不会运行你的 `demo_chat.py`。

平台只会做类似事情：

```python
from user_agent import ReasoningAgent

agent = ReasoningAgent(client=official_client)
result = agent.solve(problem, metadata)
```

所以正式参赛时最关键的是：

- 根目录必须有 `user_agent.py`。
- 文件里必须有 `ReasoningAgent`。
- 构造函数必须接收 `client`。
- `solve()` 必须返回含 `final_response` 的 dict。

## 五、后续扩展方向

### 第一阶段：保持简单

目标：

- API 稳定可调用。
- `demo_chat.py` 能稳定返回。
- `main.py` 能稳定生成 JSON。
- 不引入复杂工具。

### 第二阶段：改进智能体

可以做：

- 多候选答案生成。
- 二次 verifier。
- 根据题目 metadata 选择不同 prompt。
- 增强答案抽取规则。
- 加入 `sympy` 做符号计算校验。

### 第三阶段：容器化

可以加：

- `Dockerfile`
- `.dockerignore`
- 容器启动说明
- AtomGit 提交说明

Docker 阶段仍然不要把 API Key 写进镜像，应该运行容器时通过环境变量注入。

## 六、当前最重要的结论

你已经完成了第一步：

```text
本地 Python -> .env -> Intern-S API -> LLM 原始输出
```

这说明 API 调用链路已经跑通。

接下来只需要围绕 `user_agent.py` 逐步增强数学推理能力。
