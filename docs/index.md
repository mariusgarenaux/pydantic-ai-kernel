# Pydantic AI Kernel

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

### Usage

There are two ways of using this library to build kernels :

First, this library provides a native [PydanticAIBaseKernel class](./subclass.md), which calls the `run` method of a given `pydantic-ai` agent when called. Subclassing this, or simply specifying an agent configuration file with this kernel allows to create kernels with single pydantic-ai agent, and is the **minimal choice** to build an 'agent-kernel'. Use it if you just want what a single pydantic-ai agent can do, nothing more. For example, having a chatbot, or an agent which decides when to call a MCP server, with custom system prompt.

The other way, more advanced, is to create a subclass of [MetaKernel](https://github.com/Calysto/metakernel), and to use [JuPydantic](./subclass.md) objects in order to spawn multiple agents within the kernel, and to stream (or not) their output towards the kernel frontend. The `do_execute_direct` method must be defined. Us it if you need to build complex applications involving more than 'one pydantic-ai agent'. For example, an application which first calls a summary agent, then a web-search tool, and finally an other summary agent before sending its output. An other example is Finite State Machines (with pydantic-graph for example). The [JuPydantic](./subclass.md) makes it easy to link pydantic-ai agent with kernels machinery (streamed output, tool validation, ...).

Here are some resources about how to build your own jupyter kernel : 

- directly subclassing IPykernel : [https://jupyter-client.readthedocs.io/en/stable/kernels.html#packaging](https://jupyter-client.readthedocs.io/en/stable/kernels.html#packaging)
- subclassing MetaKernel : [https://metakernel.readthedocs.io/en/latest/new_kernel/](https://metakernel.readthedocs.io/en/latest/new_kernel/)
- subclassing MetaKernel, and using JuPydantic : [JuPydantic](./subclass.md),
- subclassing PydanticAIBaseKernel : [https://github.com/mariusgarenaux/pydantic-ai-kernel/tree/main/example_agent](https://github.com/mariusgarenaux/pydantic-ai-kernel/tree/main/example_agent)
- reusing PydanticAIBaseKernel with custom config file : [https://github.com/mariusgarenaux/pydantic-ai-kernel/tree/main/example_agent_2](https://github.com/mariusgarenaux/pydantic-ai-kernel/tree/main/example_agent)


In most cases, the kernel is a python package, with structure defined here : [https://metakernel.readthedocs.io/en/latest/new_kernel/](https://github.com/mariusgarenaux/pydantic-ai-kernel/tree/main/example_agent). It can hence be installed, and then started from various Jupyter frontends :

- **CLI**: Install `jupyter-console` and run:
  ```bash
  jupyter console --kernel pydantic_ai
  ```
- **Notebooks**: Select `pydantic_ai` from the kernel list in your IDE.
- **Jupyter Lab**: Use the kernel directly within the Lab environment.
- **Silik Signal Messaging**: Access the kernel through the Signal Message Application ([see here](https://github.com/mariusgarenaux/silik-messaging)).
- **jpterm** : a fancy jupyter lab interface, in the terminal ! [https://davidbrochart.github.io/jpterm/](https://davidbrochart.github.io/jpterm/)
- **euporie** : a fancy kernel frontend : [https://euporie.readthedocs.io/en/latest/pages/installation.html](https://euporie.readthedocs.io/en/latest/pages/installation.html)
- **jupyter-server** : with or without the `lab` extension [jupyter-lab](https://jupyter-server.readthedocs.io/en/latest/index.html). Provides an UI for interacting with kernels, and a REST API to spawn them externally.

See [Frontends](./frontends.md) for installation details and examples.

> **Jupyter Lite** is not supported since the kernel is based on IPykernel, which is not accessible in [Pyodide](https://jupyterlite.readthedocs.io/en/stable/howto/configure/kernels.html).

Once kernel is built, you can also access it _via_ API with [jupyter kernel gateway](https://jupyter-kernel-gateway.readthedocs.io/en/latest/), [jupyter enterprise gateway](https://jupyter-enterprise-gateway.readthedocs.io/en/latest/index.html), [jupyter server](https://jupyter-server.readthedocs.io/en/latest/index.html). This allows to share the agent with others.

The kernel can also be packaged in a python library, and shared _via_ pypi, as it is for this `pydantic_ai_kernel`.

### Quick Start

If you use any PydanticAIBaseKernel subclass, you will inherits the magics commands, and you just have to send `%config` to set up your agent:

```text
%config
```

Refer to `%help <magic_name>` or `%magic` for detailed documentation on available commands.

You can also set up a configuration file manually : [Configuration](./agent_config.md)
