# Pydantic AI Kernel

Pydantic AI Kernel is a wrapper around the `pydantic-ai` agent that enables interaction through the [Jupyter kernel messaging protocol](https://jupyter-client.readthedocs.io/en/stable/messaging.html). It provides an easy way to create and share python based agent applications (with custom tools, ...).

Instead of building a custom CLI for a chatbot, this library leverages the Jupyter ecosystem to provide a free UI and a proven API for agent access. No CLI is implemented here - just the [kernel](https://jupyter-client.readthedocs.io/en/stable/messaging.html).

This architecture allows for the spawning of multiple kernel instances via the [Jupyter kernel gateway](https://jupyter-kernel-gateway.readthedocs.io/en/latest/), enabling access to agents over web sockets.

![Capture](https://github.com/mariusgarenaux/pydantic-ai-kernel/blob/main/euporie.png?raw=True)

## Key Features

- **No frontend implemented** : just kernel. Frontend can be any jupyter frontend.
- **Language-Agnostic Protocol**: Based on Jupyter messaging.
- **Streamed Output**: streaming of text output
- **Flexible Configuration**: Configure system prompts, tools, mcp servers, models and inference providers (via `pydantic-ai`).
- **Native web socket API** : [Jupyter kernel gateway](https://jupyter-kernel-gateway.readthedocs.io/en/latest/)
- **Magics**: Custom commands with TAB completion, for example : view history and tool calling, set up config, ...
- **Interactive Tooling**: Supports user validation for tools requiring approval.
- **Different output types** : kernel can send several data type for its output, supported by jupyter frontend (markdown, raw text, html, **jupyter widgets**, ...)

## Getting Started

### Installation

Install the package within a Python virtual environment:

```bash
pip install pydantic-ai-kernel
```

### Usage

You can interact with the kernel through various Jupyter frontends:

- **CLI**: Install `jupyter-console` and run:
  ```bash
  jupyter console --kernel pydantic_ai
  ```
- **Notebooks**: Select `pydantic_ai` from the kernel list in your IDE.
- **Jupyter Lab**: Use the kernel directly within the Lab environment.
- **Silik Signal Messaging**: Access the kernel through the Signal Message Application ([see here](https://github.com/mariusgarenaux/silik-messaging)).
- **jpterm** : a fancy jupyter lab interface, in the terminal ! [https://davidbrochart.github.io/jpterm/](https://davidbrochart.github.io/jpterm/)
- **euporie** : a fancy kernel frontend : [https://euporie.readthedocs.io/en/latest/pages/installation.html](https://euporie.readthedocs.io/en/latest/pages/installation.html)

> **Jupyter Lite** is not supported since the kernel is based on IPykernel, which is not accessible in [Pyodide](https://jupyterlite.readthedocs.io/en/stable/howto/configure/kernels.html).

See [Frontends](./frontends.md) for installation details and examples.

### Quick Start

Once the kernel is running, use the `%config` magic to set up your agent:

```text
%config
```

Refer to `%help <magic_name>` or `%magic` for detailed documentation on available commands.

You can also set up a configuration file manually : [Configuration](./agent_config.md)
