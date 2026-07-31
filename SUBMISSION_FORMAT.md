# 比赛提交格式与自检文档

本文档记录 Intern-S 数学推理智能体项目的提交要求、仓库格式、运行方式和提交前自检清单。

## 一、正式提交核心要求

正式评测平台会从 AtomGit 仓库拉取代码，并固定调用：

```python
from user_agent import ReasoningAgent

agent = ReasoningAgent(client=official_client)
result = agent.solve(problem: str, metadata: dict)
```

因此最关键的是根目录必须存在：

```text
user_agent.py
```

并且文件中必须定义：

```python
class ReasoningAgent:
    def __init__(self, client, *args, **kwargs):
        ...

    def solve(self, problem: str, metadata: dict) -> dict:
        ...
```

## 二、`solve` 返回格式

最低合法返回：

```python
{
    "final_response": "最终答案字符串"
}
```

推荐返回：

```python
{
    "final_response": "72",
    "trace": [
        {
            "step": "solve",
            "content": "推理、校验或答案格式化摘要"
        }
    ]
}
```

要求：

- `final_response` 必须是非空字符串。
- 返回结果必须可以 JSON 序列化。
- `trace` 必须是数组结构。
- `trace` 中不能包含 API Key、令牌、个人隐私或本地绝对路径。

## 三、仓库根目录建议结构

推荐最终提交结构：

```text
.
├── user_agent.py
├── llm_client.py
├── main.py
├── requirements.txt
├── sample_data/
├── tests/
├── .env.example
├── .gitignore
└── SUBMISSION_FORMAT.md
```

后续如果增加 prompt、工具或公共模块，也可以提交：

```text
.
├── prompts/
├── tools/
└── utils/
```

注意：

- 代码里读取文件必须使用相对路径。
- 不能依赖本机绝对路径。
- 不要提交本地输出目录。

## 四、不能提交的内容

不要提交：

```text
.env
outputs/
sample_outputs/
__pycache__/
.pytest_cache/
.DS_Store
```

尤其不要提交：

```text
INTERN_API_KEY=真实密钥
```

本项目已在 `.gitignore` 中忽略 `.env`，但提交前仍要检查。

## 五、本地配置格式

本地运行使用 `.env` 文件。

复制模板：

```bash
cp .env.example .env
```

填写：

```text
INTERN_API_KEY=你的真实key
INTERN_MODEL=intern-s2-preview
INTERN_API_BASE=https://chat.intern-ai.org.cn/api/v1/chat/completions
INTERN_THINKING_MODE=true

LOCAL_MAX_CONCURRENCY=4
```

说明：

| 配置项 | 作用 |
| --- | --- |
| `INTERN_API_KEY` | API Key，本地私有，不提交 |
| `INTERN_MODEL` | 模型名，例如 `intern-s1`、`intern-s1-pro`、`intern-s2-preview` |
| `INTERN_API_BASE` | Chat Completions API 地址 |
| `INTERN_THINKING_MODE` | 是否开启思考模式，填 `true` 或 `false` |
| `LOCAL_MAX_CONCURRENCY` | 本地 runner 并发数 |

## 六、本地运行方式

### 1. 最小 API 连通性测试

只测试能不能调用模型：

```bash
python demo_chat.py "计算 17+25 的值"
```

如果终端能输出模型回答，说明：

- `.env` 已读取。
- API Key 有效。
- API URL 可访问。
- 模型名可用。

### 2. 本地比赛流程测试

运行官方 baseline runner：

```bash
python main.py --input_file sample_data/dev.jsonl --output_dir sample_outputs
```

如果重复运行且想重新生成结果，先删除旧输出目录：

```bash
rm -rf sample_outputs
python main.py --input_file sample_data/dev.jsonl --output_dir sample_outputs
```

注意：不要提交 `sample_outputs/`。

## 七、提交前自检命令

### 1. 语法检查

```bash
python -m py_compile user_agent.py llm_client.py main.py demo_chat.py
```

### 2. API 连通测试

```bash
python demo_chat.py "计算 1+1"
```

### 3. 本地 runner 测试

```bash
rm -rf sample_outputs
python main.py --input_file sample_data/dev.jsonl --output_dir sample_outputs
```

### 4. 检查输出文件

```bash
ls sample_outputs
cat sample_outputs/0.json
```

输出中应包含：

```json
{
  "idx": 0,
  "status": "success",
  "final_response": "...",
  "trace": []
}
```

### 5. 检查是否误提交密钥

```bash
git status --short
```

确认没有：

```text
.env
```

再检查代码中没有硬编码密钥：

```bash
grep -R "sk-" .
```

如果输出包含真实 key，必须删除。

## 八、AtomGit 提交要求

正式参赛代码必须推到 AtomGit 队伍组织仓库。

推荐流程：

```bash
git remote add atomgit 你的AtomGit仓库地址
git branch -M main
git push -u atomgit main
```

如果远端地址写错：

```bash
git remote set-url atomgit 新AtomGit仓库地址
git push -u atomgit main
```

要求：

- 参赛稳定代码放在 `main` 分支。
- 评测系统自动拉取 `main` 分支最新代码。
- 提交作品前必须在 AtomGit 网页端确认源码正常展示。
- 评测拉取期间不要修改 `main` 分支。

## 九、邮件打包提交内容

最终邮件压缩包建议包含：

```text
完整源码
requirements.txt
说明文档
```

说明文档至少写：

- 队伍信息。
- 赛道名称。
- AtomGit 仓库地址。
- 评测分支：`main`。
- 选用模型。
- 本地运行方式。

不要把 `.env` 打进压缩包。

## 十、当前项目状态

当前目录基于官方 baseline 修改，保留了官方核心结构：

```text
user_agent.py
main.py
llm_client.py
requirements.txt
sample_data/
tests/
```

额外新增：

```text
demo_chat.py
.env.example
.gitignore
SUBMISSION_FORMAT.md
```

这些新增文件不会影响官方评测入口。
