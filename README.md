# Pydantic AI Kernel

> Documentation : [https://mariusgarenaux.github.io/pydantic-ai-kernel](https://mariusgarenaux.github.io/pydantic-ai-kernel)

Pydantic AI Kernel is a python library which takes advantage of both [pydantic-ai](https://pydantic.dev/docs/ai/overview/) and [metakernel](https://github.com/Calysto/metakernel) libraries in order to provide a framework to create jupyter kernels which can use Large Language Models, tools, MCP servers, capabilities, ... (all features from `pydantic-ai`) when they run code.

This allows to build jupyter kernels which takes raw text as input, and returns anything you want : structured output, raw text, ... Such kernels can be called `agents`, by leveraging features of `pydantic-ai` during the execution process. Once the `agent` is built, the jupyter messaging protocol allows to easily :

- access it with various frontends : Command Line Interface, Web Interface, REST API, websockets, ... See [frontends](./frontends.md)

- expose it with APIs ready for production : REST and websockets with [jupyter server](https://jupyter-server.readthedocs.io/en/latest/index.html), [jupyter kernel gateway](https://jupyter-kernel-gateway.readthedocs.io/en/latest/) or [jupyter enterprise gateway](https://jupyter-enterprise-gateway.readthedocs.io/en/latest/index.html), python API with [jupyter_kernel_client](https://jupyter-kernel-client.datalayer.tech/)

![Capture](https://github.com/mariusgarenaux/pydantic-ai-kernel/blob/main/euporie.png?raw=True)

![Capture](https://github.com/mariusgarenaux/pydantic-ai-kernel/blob/main/jupyter_lab_home_2.png?raw=True)


## Key Features

- **No frontend implemented** : just kernel. You define what the agent does when it receive text, what it outputs, what to do when an error is raised. That's it.
- **Language-Agnostic Protocol**: Based on Jupyter messaging, through either websockets or ZMQ sockets.
- **Streamed Output**: Possibility to forward pydantic-ai agent streaming to the cell output of jupyter kernel
- **Flexible Configuration**: Configure system prompts, tools, mcp servers, models and inference providers (via `pydantic-ai`).
- **Magics**: Custom commands with TAB completion, for example : view history and tool calling, set up config, ...
- **Interactive Tooling**: Supports user validation for tools requiring approval
- **Different output types** : kernel can send several data type for its output, supported by jupyter frontend (markdown, raw text, html, **jupyter widgets**, ...)

## Getting Started

### Installation

Install the package within a Python virtual environment:

```bash
pip install pydantic-ai-kernel
```

### Quick Start

If you use any PydanticAIBaseKernel subclass, you will inherits the magics commands, and you just have to send `%config` to set up your agent:

```text
%config
```

Refer to `%help <magic_name>` or `%magic` for detailed documentation on available commands.

You can also set up a configuration file manually : [Configuration](./agent_config.md)

