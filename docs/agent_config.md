# Agent Configuration

This document describes how to configure agents for the AI kernel. Configuration is handled via `AgentConfig` Pydantic models, typically stored in JSON files. The scheme is available here : [json-scheme](https://github.com/mariusgarenaux/pydantic-ai-kernel/blob/main/pydantic_ai_kernel/config_scheme.json)

## Configuration Protocol

To create a configuration file for an agent, you must provide a JSON object that follows the `AgentConfig` schema.

### 1. Required Fields

The following fields are **mandatory**:

- **`agent_name`** (`string`): A unique identifier for the agent within your application (e.g., `"summarizer"`, `"research-assistant"`).
- **`system_prompt`** (`string`): The agent's persona and instructions. This can be:
  - A direct string: `"You are a helpful assistant."`
  - A path to a file: `"/path/to/prompt.txt"` (the kernel will automatically load the content).
- **`model`** (`object`): The model configuration (see [Model Configuration](#2-model-configuration-model) below).

### 2. Model Configuration (`model`)

The `model` field requires a `ModelConfig` object:

- **`model_name`** (`string`): **Required**.
  - Format A: `<provider>:<model_name>` (e.g., `"ollama:qwen3:1.7b"`).
  - Format B: `<model_name>` (e.g., `"gpt-4o"`). If using this format, you **must** provide a `model_provider` block.
- **`model_type`** (`string`, optional): The kind of model. See [AllModelKind](#allmodelkind) for a list of supported types (e.g., `"openai"`, `"anthropic"`, `"ollama"`, `"test"`).
- **`model_provider`** (`object`, optional): Used to customize the inference provider.
  - `name`: The provider name (e.g., `"ollama"`, `"litellm"`).
  - `params`: A dictionary of provider-specific parameters (e.g., `{"base_url": "http://localhost:11434/v1"}`).
- **`model_settings`** (`object`, optional): Model-specific settings. Refer to [pydantic-ai ModelSettings](https://ai.pydantic.dev/api/settings/#pydantic_ai.settings.ModelSettings).

### 3. Optional Fields

- **`mcp_servers`** (`object`): A mapping of MCP server names to their configurations.
  - Example:
    ```json
    "mcp_servers": {
      "weather-server": { "command": "python", "args": ["mcp_server.py"] },
      "calculator": { "url": "http://localhost:8000/mcp" }
    }
    ```
- **`mcp_servers_user_approval`** (`object`): Controls which tools require user confirmation.
  - `true`: All tools in that server require approval.
  - `false`: No tools in that server require approval.
  - `dict`: Map of specific tool names to booleans (e.g., `{"delete_file": true, "read_file": false}`).
- **`display_thinking`** (`boolean`, default: `true`): Whether to show the model's internal reasoning.
- **`formatter`** (`string`, default: `"terminal"`): Output format for magics. Options: `"text"`, `"terminal"`, `"md"`, `"json"`.

## Reference: Supported Model Types (`AllModelKind`)

The following identifiers can be used in `model_type`:

`test`, `openai`, `azure`, `deepseek`, `fireworks`, `github`, `grok`, `heroku`, `moonshotai`, `ollama`, `together`, `vercel`, `litellm`, `nebius`, `ovhcloud`, `alibaba`, `openai-chat`, `openai-responses`, `google-gla`, `google-vertex`, `google`, `groq`, `cohere`, `mistral`, `openrouter`, `anthropic`, `bedrock`, `huggingface`, `cerebras`.

## Using the `%config` magic and templates

The kernel provides a `%config` magic to create, edit, or load configuration files directly from a Jupyter notebook. It supports built‑in templates that generate a starter YAML configuration.

- **Template list**: `ollama`, `open_web_ui`, `openai`.
- **Create a new config from a template**:
  ```
  %config --template ollama --path ~/my_agent.yaml
  ```
  This writes a file with the selected template content (see `config_magic.py`).
- **Edit an existing config**:
  ```
  %config --path ~/my_agent.yaml --edit
  ```
- **Load a config** (no flags):
  ```
  %config
  ```
  Loads the default config located in the kernel's config directory.

The template placeholders `<model_name>` and others must be replaced with actual values after the file is created.

---

## Example Configuration Files

### Basic Agent

A simple agent without MCP servers.

```json
{
  "agent_name": "simple-chat",
  "system_prompt": "You are a helpful assistant.",
  "model": {
    "model_name": "openai:gpt-4o",
    "model_type": "openai"
  }
}
```

### Advanced Agent with MCP & Custom Provider

An agent utilizing a local Ollama instance and multiple MCP servers.

```json
{
  "agent_name": "research-expert",
  "system_prompt": "You are a professional researcher. Be concise and factual.",
  "model": {
    "model_name": "ollama:llama3",
    "model_type": "ollama",
    "model_provider": {
      "name": "ollama",
      "params": { "base_url": "http://localhost:11434/v1" }
    }
  },
  "mcp_servers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/home/docs"
      ]
    },
    "weather": {
      "url": "http://localhost:3001/sse"
    }
  },
  "mcp_servers_user_approval": {
    "filesystem": { "write_file": true, "read_file": false },
    "weather": false
  },
  "display_thinking": true,
  "formatter": "md"
}
```

### Agent with File-based Prompt

Using a path to a system prompt file for better maintainability.

```json
{
  "agent_name": "coder",
  "system_prompt": "/Users/user/configs/prompts/coder_persona.md",
  "model": {
    "model_name": "anthropic:claude-3-5-sonnet",
    "model_type": "anthropic"
  },
  "formatter": "terminal"
}
```
