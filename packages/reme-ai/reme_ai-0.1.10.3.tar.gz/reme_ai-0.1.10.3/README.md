<p align="center">
 <img src="docs/_static/figure/reme_logo.png" alt="ReMe Logo" width="50%">
</p>

<p align="center">
  <a href="https://pypi.org/project/reme-ai/"><img src="https://img.shields.io/badge/python-3.12+-blue" alt="Python Version"></a>
  <a href="https://pypi.org/project/reme-ai/"><img src="https://img.shields.io/badge/pypi-v0.1.10.3-blue?logo=pypi" alt="PyPI Version"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-black" alt="License"></a>
  <a href="https://github.com/modelscope/ReMe"><img src="https://img.shields.io/github/stars/modelscope/ReMe?style=social" alt="GitHub Stars"></a>
</p>

<p align="center">
  <strong>ReMe (formerly MemoryScope): Memory Management Framework for Agents</strong><br>
  <em>Remember Me, Refine Me.</em>
</p>

---
ReMe provides AI agents with a unified memory system—enabling the ability to extract, reuse, and share memories across
users, tasks, and agents.

```
Personal Memory + Task Memory + Tool Memory = Agent Memory
```

Personal memory helps "**understand user preferences**", task memory helps agents "**perform better**", and tool memory enables "**smarter tool usage**".

---

## 📰 Latest Updates

- **[2025-10]** 🚀 ReMe v0.1.10.3 released! Core enhancement: direct Python import support. You can now use ReMe without starting an HTTP or MCP service - simply `from reme_ai import ReMeApp` and call methods directly in your Python code.
- **[2025-10]** 🔧 Tool Memory support is now available! Enables data-driven tool selection and parameter optimization through historical performance tracking. Check out the [Tool Memory Guide](docs/tool_memory/tool_memory.md) and [benchmark results](docs/tool_memory/tool_bench.md).
- **[2025-09]** 🎉 ReMe v0.1.9 has been officially released, adding support for asynchronous operations. It has also been
  integrated into the memory service of agentscope-runtime.
- **[2025-09]** 🎉 ReMe v0.1 officially released, integrating task memory and personal memory. If you want to use the
  original memoryscope project, you can find it
  in [MemoryScope](https://github.com/modelscope/Reme/tree/memoryscope_branch).
- **[2025-09]** 🧪 We validated the effectiveness of task memory extraction and reuse in agents in appworld, bfcl(v3),
  and frozenlake environments. For more information,
  check [appworld exp](docs/cookbook/appworld/quickstart.md), [bfcl exp](docs/cookbook/bfcl/quickstart.md),
  and [frozenlake exp](docs/cookbook/frozenlake/quickstart.md).
- **[2025-08]** 🚀 MCP protocol support is now available -> [MCP Quick Start](docs/mcp_quick_start.md).
- **[2025-06]** 🚀 Multiple backend vector storage support (Elasticsearch &
  ChromaDB) -> [Vector DB quick start](docs/vector_store_api_guide.md).
- **[2024-09]** 🧠 [MemoryScope](https://github.com/modelscope/Reme/tree/memoryscope_branch) v0.1 released,
  personalized and time-aware memory storage and usage.

---

## ✨ Architecture Design

<p align="center">
 <img src="docs/_static/figure/reme_structure.jpg" alt="ReMe Logo" width="100%">
</p>

ReMe integrates three complementary memory capabilities:

#### 🧠 **Task Memory/Experience**

Procedural knowledge reused across agents

- **Success Pattern Recognition**: Identify effective strategies and understand their underlying principles
- **Failure Analysis Learning**: Learn from mistakes and avoid repeating the same issues
- **Comparative Patterns**: Different sampling trajectories provide more valuable memories through comparison
- **Validation Patterns**: Confirm the effectiveness of extracted memories through validation modules

Learn more about how to use task memory from [task memory](docs/task_memory/task_memory.md)

#### 👤 **Personal Memory**

Contextualized memory for specific users

- **Individual Preferences**: User habits, preferences, and interaction styles
- **Contextual Adaptation**: Intelligent memory management based on time and context
- **Progressive Learning**: Gradually build deep understanding through long-term interaction
- **Time Awareness**: Time sensitivity in both retrieval and integration

Learn more about how to use personal memory from [personal memory](docs/personal_memory/personal_memory.md)

#### 🔧 **Tool Memory**

Data-driven tool selection and usage optimization

- **Historical Performance Tracking**: Success rates, execution times, and token costs from real usage
- **LLM-as-Judge Evaluation**: Qualitative insights on why tools succeed or fail
- **Parameter Optimization**: Learn optimal parameter configurations from successful calls
- **Dynamic Guidelines**: Transform static tool descriptions into living, learned manuals

Learn more about how to use tool memory from [tool memory](docs/tool_memory/tool_memory.md)

---

## 🛠️ Installation

### Install from PyPI (Recommended)

```bash
pip install reme-ai
```

### Install from Source

```bash
git clone https://github.com/modelscope/ReMe.git
cd ReMe
pip install .
```

### Environment Configuration

Copy `example.env` to .env and modify the corresponding parameters:

```bash
FLOW_LLM_API_KEY=sk-xxxx
FLOW_LLM_BASE_URL=https://xxxx/v1
FLOW_EMBEDDING_API_KEY=sk-xxxx
FLOW_EMBEDDING_BASE_URL=https://xxxx/v1
```

---

## 🚀 Quick Start

### HTTP Service Startup

```bash
reme \
  backend=http \
  http.port=8002 \
  llm.default.model_name=qwen3-30b-a3b-thinking-2507 \
  embedding_model.default.model_name=text-embedding-v4 \
  vector_store.default.backend=local
```

### MCP Server Support

```bash
reme \
  backend=mcp \
  mcp.transport=stdio \
  llm.default.model_name=qwen3-30b-a3b-thinking-2507 \
  embedding_model.default.model_name=text-embedding-v4 \
  vector_store.default.backend=local
```

### Core API Usage

#### Task Memory Management

```python
import requests

# Experience Summarizer: Learn from execution trajectories
response = requests.post("http://localhost:8002/summary_task_memory", json={
    "workspace_id": "task_workspace",
    "trajectories": [
        {"messages": [{"role": "user", "content": "Help me create a project plan"}], "score": 1.0}
    ]
})

# Retriever: Get relevant memories
response = requests.post("http://localhost:8002/retrieve_task_memory", json={
    "workspace_id": "task_workspace",
    "query": "How to efficiently manage project progress?",
    "top_k": 1
})
```

<details>
<summary>Python import version</summary>

```python
import asyncio
from reme_ai import ReMeApp

async def main():
    async with ReMeApp(
        "llm.default.model_name=qwen3-30b-a3b-thinking-2507",
        "embedding_model.default.model_name=text-embedding-v4",
        "vector_store.default.backend=memory"
    ) as app:
        # Experience Summarizer: Learn from execution trajectories
        result = await app.async_execute(
            name="summary_task_memory",
            workspace_id="task_workspace",
            trajectories=[
                {
                    "messages": [
                        {"role": "user", "content": "Help me create a project plan"}
                    ],
                    "score": 1.0
                }
            ]
        )
        print(result)
        
        # Retriever: Get relevant memories
        result = await app.async_execute(
            name="retrieve_task_memory",
            workspace_id="task_workspace",
            query="How to efficiently manage project progress?",
            top_k=1
        )
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

</details>

<details>
<summary>curl version</summary>

```bash
# Experience Summarizer: Learn from execution trajectories
curl -X POST http://localhost:8002/summary_task_memory \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "task_workspace",
    "trajectories": [
      {"messages": [{"role": "user", "content": "Help me create a project plan"}], "score": 1.0}
    ]
  }'

# Retriever: Get relevant memories
curl -X POST http://localhost:8002/retrieve_task_memory \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "task_workspace",
    "query": "How to efficiently manage project progress?",
    "top_k": 1
  }'
```

</details>

<details>
<summary>Node.js version</summary>

```javascript
// Experience Summarizer: Learn from execution trajectories
fetch("http://localhost:8002/summary_task_memory", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    workspace_id: "task_workspace",
    trajectories: [
      {messages: [{role: "user", content: "Help me create a project plan"}], score: 1.0}
    ]
  })
})
.then(response => response.json())
.then(data => console.log(data));

// Retriever: Get relevant memories
fetch("http://localhost:8002/retrieve_task_memory", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    workspace_id: "task_workspace",
    query: "How to efficiently manage project progress?",
    top_k: 1
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

</details>

#### Personal Memory Management

```python
# Memory Integration: Learn from user interactions
response = requests.post("http://localhost:8002/summary_personal_memory", json={
    "workspace_id": "task_workspace",
    "trajectories": [
        {"messages":
            [
                {"role": "user", "content": "I like to drink coffee while working in the morning"},
                {"role": "assistant",
                 "content": "I understand, you prefer to start your workday with coffee to stay energized"}
            ]
        }
    ]
})

# Memory Retrieval: Get personal memory fragments
response = requests.post("http://localhost:8002/retrieve_personal_memory", json={
    "workspace_id": "task_workspace",
    "query": "What are the user's work habits?",
    "top_k": 5
})
```

<details>
<summary>Python import version</summary>

```python
import asyncio
from reme_ai import ReMeApp

async def main():
    async with ReMeApp(
        "llm.default.model_name=qwen3-30b-a3b-thinking-2507",
        "embedding_model.default.model_name=text-embedding-v4",
        "vector_store.default.backend=memory"
    ) as app:
        # Memory Integration: Learn from user interactions
        result = await app.async_execute(
            name="summary_personal_memory",
            workspace_id="task_workspace",
            trajectories=[
                {
                    "messages": [
                        {"role": "user", "content": "I like to drink coffee while working in the morning"},
                        {"role": "assistant",
                         "content": "I understand, you prefer to start your workday with coffee to stay energized"}
                    ]
                }
            ]
        )
        print(result)
        
        # Memory Retrieval: Get personal memory fragments
        result = await app.async_execute(
            name="retrieve_personal_memory",
            workspace_id="task_workspace",
            query="What are the user's work habits?",
            top_k=5
        )
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

</details>

<details>
<summary>curl version</summary>

```bash
# Memory Integration: Learn from user interactions
curl -X POST http://localhost:8002/summary_personal_memory \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "task_workspace",
    "trajectories": [
      {"messages": [
        {"role": "user", "content": "I like to drink coffee while working in the morning"},
        {"role": "assistant", "content": "I understand, you prefer to start your workday with coffee to stay energized"}
      ]}
    ]
  }'

# Memory Retrieval: Get personal memory fragments
curl -X POST http://localhost:8002/retrieve_personal_memory \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "task_workspace",
    "query": "What are the users work habits?",
    "top_k": 5
  }'
```

</details>

<details>
<summary>Node.js version</summary>

```javascript
// Memory Integration: Learn from user interactions
fetch("http://localhost:8002/summary_personal_memory", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    workspace_id: "task_workspace",
    trajectories: [
      {messages: [
        {role: "user", content: "I like to drink coffee while working in the morning"},
        {role: "assistant", content: "I understand, you prefer to start your workday with coffee to stay energized"}
      ]}
    ]
  })
})
.then(response => response.json())
.then(data => console.log(data));

// Memory Retrieval: Get personal memory fragments
fetch("http://localhost:8002/retrieve_personal_memory", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    workspace_id: "task_workspace",
    query: "What are the user's work habits?",
    top_k: 5
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

</details>

#### Tool Memory Management

```python
import requests

# Record tool execution results
response = requests.post("http://localhost:8002/add_tool_call_result", json={
    "workspace_id": "tool_workspace",
    "tool_call_results": [
        {
            "create_time": "2025-10-21 10:30:00",
            "tool_name": "web_search",
            "input": {"query": "Python asyncio tutorial", "max_results": 10},
            "output": "Found 10 relevant results...",
            "token_cost": 150,
            "success": True,
            "time_cost": 2.3
        }
    ]
})

# Generate usage guidelines from history
response = requests.post("http://localhost:8002/summary_tool_memory", json={
    "workspace_id": "tool_workspace",
    "tool_names": "web_search"
})

# Retrieve tool guidelines before use
response = requests.post("http://localhost:8002/retrieve_tool_memory", json={
    "workspace_id": "tool_workspace",
    "tool_names": "web_search"
})
```

<details>
<summary>Python import version</summary>

```python
import asyncio
from reme_ai import ReMeApp

async def main():
    async with ReMeApp(
        "llm.default.model_name=qwen3-30b-a3b-thinking-2507",
        "embedding_model.default.model_name=text-embedding-v4",
        "vector_store.default.backend=memory"
    ) as app:
        # Record tool execution results
        result = await app.async_execute(
            name="add_tool_call_result",
            workspace_id="tool_workspace",
            tool_call_results=[
                {
                    "create_time": "2025-10-21 10:30:00",
                    "tool_name": "web_search",
                    "input": {"query": "Python asyncio tutorial", "max_results": 10},
                    "output": "Found 10 relevant results...",
                    "token_cost": 150,
                    "success": True,
                    "time_cost": 2.3
                }
            ]
        )
        print(result)
        
        # Generate usage guidelines from history
        result = await app.async_execute(
            name="summary_tool_memory",
            workspace_id="tool_workspace",
            tool_names="web_search"
        )
        print(result)
        
        # Retrieve tool guidelines before use
        result = await app.async_execute(
            name="retrieve_tool_memory",
            workspace_id="tool_workspace",
            tool_names="web_search"
        )
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

</details>

<details>
<summary>curl version</summary>

```bash
# Record tool execution results
curl -X POST http://localhost:8002/add_tool_call_result \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "tool_workspace",
    "tool_call_results": [
      {
        "create_time": "2025-10-21 10:30:00",
        "tool_name": "web_search",
        "input": {"query": "Python asyncio tutorial", "max_results": 10},
        "output": "Found 10 relevant results...",
        "token_cost": 150,
        "success": true,
        "time_cost": 2.3
      }
    ]
  }'

# Generate usage guidelines from history
curl -X POST http://localhost:8002/summary_tool_memory \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "tool_workspace",
    "tool_names": "web_search"
  }'

# Retrieve tool guidelines before use
curl -X POST http://localhost:8002/retrieve_tool_memory \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "tool_workspace",
    "tool_names": "web_search"
  }'
```

</details>

<details>
<summary>Node.js version</summary>

```javascript
// Record tool execution results
fetch("http://localhost:8002/add_tool_call_result", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    workspace_id: "tool_workspace",
    tool_call_results: [
      {
        create_time: "2025-10-21 10:30:00",
        tool_name: "web_search",
        input: {query: "Python asyncio tutorial", max_results: 10},
        output: "Found 10 relevant results...",
        token_cost: 150,
        success: true,
        time_cost: 2.3
      }
    ]
  })
})
.then(response => response.json())
.then(data => console.log(data));

// Generate usage guidelines from history
fetch("http://localhost:8002/summary_tool_memory", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    workspace_id: "tool_workspace",
    tool_names: "web_search"
  })
})
.then(response => response.json())
.then(data => console.log(data));

// Retrieve tool guidelines before use
fetch("http://localhost:8002/retrieve_tool_memory", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    workspace_id: "tool_workspace",
    tool_names: "web_search"
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

</details>

---

## 📦 Ready-to-Use Libraries

ReMe provides pre-built memory libraries that agents can immediately use with verified best practices:

### Available Libraries

- **`appworld.jsonl`**: Memory library for Appworld agent interactions, covering complex task planning and execution
  patterns
- **`bfcl_v3.jsonl`**: Working memory library for BFCL tool calls

### Quick Usage

```python
# Load pre-built memories
response = requests.post("http://localhost:8002/vector_store", json={
    "workspace_id": "appworld",
    "action": "load",
    "path": "./docs/library/"
})

# Query relevant memories
response = requests.post("http://localhost:8002/retrieve_task_memory", json={
    "workspace_id": "appworld",
    "query": "How to navigate to settings and update user profile?",
    "top_k": 1
})
```

<details>
<summary>Python import version</summary>

```python
import asyncio
from reme_ai import ReMeApp

async def main():
    async with ReMeApp(
        "llm.default.model_name=qwen3-30b-a3b-thinking-2507",
        "embedding_model.default.model_name=text-embedding-v4",
        "vector_store.default.backend=memory"
    ) as app:
        # Load pre-built memories
        result = await app.async_execute(
            name="vector_store",
            workspace_id="appworld",
            action="load",
            path="./docs/library/"
        )
        print(result)
        
        # Query relevant memories
        result = await app.async_execute(
            name="retrieve_task_memory",
            workspace_id="appworld",
            query="How to navigate to settings and update user profile?",
            top_k=1
        )
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

</details>

## 🧪 Experiments

### 🌍 [Appworld Experiment](docs/cookbook/appworld/quickstart.md)

We tested ReMe on Appworld using qwen3-8b:

| Method       | pass@1            | pass@2            | pass@4            |
|--------------|-------------------|-------------------|-------------------|
| without ReMe | 0.083             | 0.140             | 0.228             |
| with ReMe    | 0.109 **(+2.6%)** | 0.175 **(+3.5%)** | 0.281 **(+5.3%)** |

Pass@K measures the probability that at least one of the K generated samples successfully completes the task (
score=1).  
The current experiment uses an internal AppWorld environment, which may have slight differences.

You can find more details on reproducing the experiment in [quickstart.md](docs/cookbook/appworld/quickstart.md).

### 🧊 [Frozenlake Experiment](docs/cookbook/frozenlake/quickstart.md)

|                                         without ReMe                                         |                                          with ReMe                                           |
|:--------------------------------------------------------------------------------------------:|:--------------------------------------------------------------------------------------------:|
| <p align="center"><img src="docs/_static/figure/frozenlake_failure.gif" alt="GIF 1" width="30%"></p> | <p align="center"><img src="docs/_static/figure/frozenlake_success.gif" alt="GIF 2" width="30%"></p> |

We tested on 100 random frozenlake maps using qwen3-8b:

| Method       | pass rate        |
|--------------|------------------|
| without ReMe | 0.66             |
| with ReMe    | 0.72 **(+6.0%)** |

You can find more details on reproducing the experiment in [quickstart.md](docs/cookbook/frozenlake/quickstart.md).

### 🔧 [BFCL-V3 Experiment](docs/cookbook/bfcl/quickstart.md)

We tested ReMe on BFCL-V3 multi-turn-base (randomly split 50train/150val) using qwen3-8b:

| Method       | pass@1              | pass@2              | pass@4              |
|--------------|---------------------|---------------------|---------------------|
| without ReMe | 0.2472              | 0.2733              | 0.2922              |
| with ReMe    | 0.3061 **(+5.89%)** | 0.3500 **(+7.67%)** | 0.3888 **(+9.66%)** |

### 🛠️ [Tool Memory Benchmark](docs/tool_memory/tool_bench.md)

We evaluated Tool Memory effectiveness using a controlled benchmark with three mock search tools using Qwen3-30B-Instruct:

| Scenario              | Avg Score | Improvement        |
|-----------------------|-----------|--------------------|
| Train (No Memory)     | 0.650     | -                  |
| Test (No Memory)      | 0.672     | Baseline           |
| **Test (With Memory)** | **0.772** | **+14.88%** |

**Key Findings:**
- Tool Memory enables data-driven tool selection based on historical performance
- Success rates improved by ~15% with learned parameter configurations

You can find more details in [tool_bench.md](docs/tool_memory/tool_bench.md) and the implementation at [run_reme_tool_bench.py](cookbook/tool_memory/run_reme_tool_bench.py).

## 📚 Resources

- **[Quick Start](./cookbook/simple_demo)**: Get started quickly with practical examples
  - [Tool Memory Demo](cookbook/simple_demo/use_tool_memory_demo.py): Complete lifecycle demonstration of tool memory
  - [Tool Memory Benchmark](cookbook/tool_memory/run_reme_tool_bench.py): Evaluate tool memory effectiveness
- **[Vector Storage Setup](docs/vector_store_api_guide.md)**: Configure local/vector databases and usage
- **[MCP Guide](docs/mcp_quick_start.md)**: Create MCP services
- **[Personal Memory](docs/personal_memory)**, **[Task Memory](docs/task_memory)** & **[Tool Memory](docs/tool_memory)**: Operators used in personal memory, task memory and tool memory. You can modify the config to customize the pipelines.
- **[Example Collection](./cookbook)**: Real use cases and best practices

---

## 🤝 Contribution

We believe the best memory systems come from collective wisdom. Contributions welcome 👉[Guide](docs/contribution.md):

### Code Contributions

- New operation and tool development
- Backend implementation and optimization
- API enhancements and new endpoints

### Documentation Improvements

- Usage examples and tutorials
- Best practice guides


---

## 📄 Citation

```bibtex
@software{ReMe2025,
  title = {ReMe: Memory Management Framework for Agents},
  author = {Li Yu, Jiaji Deng, Zouying Cao},
  url = {https://github.com/modelscope/ReMe},
  year = {2025}
}
```

---

## ⚖️ License

This project is licensed under the Apache License 2.0 - see the [LICENSE](./LICENSE) file for details.

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=modelscope/ReMe&type=Date)](https://www.star-history.com/#modelscope/ReMe&Date)

