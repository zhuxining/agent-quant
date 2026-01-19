# AGENT MODULE

LLM 交易智能体定义 (Agno 框架)

## STRUCTURE

```
app/agent/
├── trader_agent.py      # 主交易 Agent
├── example_agent.py     # 示例 Agent
├── available_models.py  # 可用模型列表
└── agent_instruction.py  # Agent 指令模板
```

## WHERE TO LOOK

| Component | File | Role |
|-----------|------|------|
| Main agent | `trader_agent.py` | Trading signal generation |
| Models | `available_models.py` | OpenAI model registry |
| Instructions | `agent_instruction.py` | Agent role/prompt templates |

## CONVENTIONS

**Agent Factory Pattern**:
```python
from agno.agent import Agent

def my_agent() -> Agent:
    return Agent(
        name="my-agent",
        instructions=[...],
        model=...,
    )
```

**Prompt Assembly**:
- Technical prompts: `app/prompt_build/technical_prompt.py`
- Account prompts: `app/prompt_build/account_prompt.py`
- Formatters: `app/prompt_build/formatters.py`
- Modular fragments assembled in workflow `build_prompts_step`

## NOTES

- `trader_agent()` integrated into NOF1 workflow as `agent_decision_step`
- OpenAI models: GPT-4o, GPT-4o-mini (see `available_models.py`)
- Workflow integration: Step 4 of NOF1 pipeline
- Timeout: 120s, max 2 retries (configured in `agent_decision_step`)
- Debug mode logs full LLM responses
