# Agent Configuration

`pydantic-ai-kernel` provides a way to load configuration file for one agent, sticking with pydantic-ai agent definition. Such a configuration file can be either `yaml` or `json`, following the scheme available here : [json-scheme](https://github.com/mariusgarenaux/pydantic-ai-kernel/blob/main/pydantic_ai_kernel/config_scheme.json), and detailed below.


## Single Agent Kernels 

For single agent kernels (subclass of PydanticAIBaseKernel), the configuration file can be either specified in PYDANTIC_AI_KERNEL_CONFIG environment file, or created permanently at `~/.jupyter/jupyter_<kernel_name>_config.yaml`. When specified, you just have to run the kernel and you will access the agent through any jupyter frontend.

Be careful, the environment variable might not be accessible directly to the kernel (especially in jupyter-server or kernel gateways). A way to deal with this is to put the environment variable directly in the kernelspec `kernel.json`. For example, create a directory named `example_agent_2`, and within this directory create a `kernel.json` file with the following :

```json
{
    "argv": [
        "python",
        "-m",
        "pydantic_ai_kernel",
        "-f",
        "{connection_file}"
    ],
    "display_name": "Example Agent",
    "interrupt_mode": "message",
    "language": "text",
    "env": {
        "PYDANTIC_AI_KERNEL_CONFIG": "./example_agent_2/example_agent_2_config.yaml"
    }
}
```

Then, run :

```bash
jupyter kernelspec install ./example_agent_2 --sys-prefix
```

> --sys-prefix flag installs the kernel in the .venv. Can be removed to be installed globally, or replaced by --user to by installed on user space

Then, a :

```bash
jupyter console --kernel example_agent_2
```

would run a kernel with the configuration file specified in the kernelspec. This allows to have multiple pydantic_ai_kernel instances, with different system prompts and/or inference providers (without having to re-write a heavy kernel project for each config).


## Multiple Agent Kernels

For kernels using **JuPydantic**, such files can be loaded and validated using the [AgentConfig](https://github.com/mariusgarenaux/pydantic-ai-kernel/blob/main/pydantic_ai_kernel/agent_config.py). Such loading and validation must be written manually in the kernel object you create by subclassing MetaKernel. Feel free to create a custom configuration file for your own agent-kernel :-).


## Readable detail of the agent configuration

Here are some details about the scheme of agent configuration.

### 1. Required Fields

The following fields are **mandatory**:

- **`agent_name`** (`string`): A unique identifier for the agent within your application (e.g., `"summarizer"`, `"research-assistant"`).
- **`system_prompt`** (`string`): The agent's persona and instructions. This can be:
    - A direct string: `"You are a helpful assistant."`
    - A path to a file: `"/path/to/prompt.txt"` (the kernel will automatically load the content).
- **`model`** (`object`): The model configuration (see [Model Configuration](#2-model-configuration-model) below).

### 2. Model Configuration (`model`)

The `model` field requires a `ModelConfig` object. Which follows pydantic-ai implementaion (see the [official documentation](https://pydantic.dev/docs/ai/models/overview/)).

- **`model_name`** (`string`): **Required**.
    - Format A: `<provider>:<model_name>` (e.g., `"ollama:qwen3:1.7b"`).
    - Format B: `<model_name>` (e.g., `"gpt-4o"`). If using this format, you **must** provide a `model_provider` block.
- **`model_type`** (`string`, optional): The kind of model. See [AllModelKind](#allmodelkind) for a list of supported types (e.g., `"openai"`, `"anthropic"`, `"ollama"`, `"test"`).
- **`model_provider`** (`object`, optional): Used to customize the inference provider.
    - `name`: The provider name (e.g., `"ollama"`, `"litellm"`).
    - `params`: A dictionary of provider-specific parameters (e.g., `{"base_url": "http://localhost:11434/v1"}`). Environment variables will be expanded in all values of the dictionnary. This is where you can put tokens.
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
- **`formatter`** (`string`, default: `"terminal"`): Output format for agent. Options: `"text"`, `"terminal"`, `"md"`, `"json"`.

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

```yaml
agent_name: simple-chat
system_prompt: You are a helpful assistant.
model:
    model_name: openai:gpt-4o
    model_type: openai
```

Tokens must be specified as environment variables for openai authentication. As specified above with PYDANTIC_AI_KERNEL_CONFIG, they can be set in kernelspec if needed.

### Advanced Agent with MCP & Custom Provider

An agent utilizing a local Ollama instance and multiple MCP servers.

```yaml
agent_name: research-expert
system_prompt: You are a professional researcher. Be concise and factual.
model:
  model_name: ollama:llama3
  model_type: ollama
  model_provider:
    name: ollama
    params:
      base_url: http://localhost:11434/v1
mcp_servers:
  filesystem:
    command: npx
    args:
      - -y
      - "@modelcontextprotocol/server-filesystem"
      - /Users/home/docs
  weather:
    url: http://localhost:3001/sse
mcp_servers_user_approval:
  filesystem:
    write_file: true
    read_file: false
  weather: false
display_thinking: true
formatter: md
```

### Agent with File-based Prompt

Using a path to a system prompt file for better maintainability.

```yaml
agent_name: coder
system_prompt: /Users/user/configs/prompts/coder_persona.md
model:
  model_name: anthropic:claude-3-5-sonnet
  model_type: anthropic
formatter: terminal
```

### Open Web UI

For OpenWeb UI like API : 

```yaml
agent_name: ragarenn
system_prompt: "blablablabla
                multiline system
                prompt"
model: 
  model_name: gemma-4-31b
  model_type: openai
  model_provider:
    name: openai
    params:
      base_url: https://ragarenn.eskemm-numerique.fr/sso/ch@t/api
      api_key: sk-...
display_thinking: True
formatter: terminal
use_widget: False
```