# Pydantic AI Base Kernel

This is wrapper around pydantic-ai agent, that allows to requests it through [jupyter kernel messaging protocol](https://jupyter-client.readthedocs.io/en/stable/messaging.html).

> Instead of re-writing an other CLI for a chatbot, use Jupyter one. This gives you a free UI, as well as the API to implement access the agent through well known and proven [Jupyter Messaging Protocol](https://jupyter-client.readthedocs.io/en/stable/messaging.html). This allow for example the spawning of multiple instances of kernels through [jupyter kernel gateway](https://jupyter-kernel-gateway.readthedocs.io/en/latest/), for free - and allows to access the agent through a web socket.

It is meant to be subclassed to create new kernel-based agent, for adding tools or any special application.

![](https://github.com/mariusgarenaux/pydantic-ai-kernel/blob/main/capture.png?raw=True)

For a basic usage of agents (chatbot), without tools, you can use any instance of this kernel and initialize it with a config file.

Features coming natively from jupyter messaging protocol :

- language-agnostic protocol,

- streamed output (with asynchronous support for python implementation),

- [configuration of the agent](#configuration-file) (set system prompt, inference provider, ...), through nearly all the inference providers (thanks to pydantic-ai)

- [display the history and tool calling of the agent (with magic command %agent_history)](#access-agent-history)

- [user validation for tools that requires it](#add-tools), with input request messages from Jupyter Messaging

## Getting started

Within a python venv,

```bash
pip install pydantic-ai-kernel
```

Any jupyter frontend should be able to dialog with this kernel, for example :

• **CLI** : Install jupyter-console (`pip install jupyter-console`); and run `jupyter console --kernel pydantic_ai`

• **Notebook** (you might need to restart the IDE) : select 'pydantic_ai' on top right of the notebook

• **Silik Signal Messaging** : Access the kernel through Signal Message Application, see [here](https://github.com/mariusgarenaux/silik-messaging)

## Configuration file

By default, kernel starts by looking for a configuration file here :

> `~/.jupyter/jupyter_pydantic_ai_kernel_config.yaml`

But you can also run the kernel as is; and specify the path to a config file by executing the following message in a cell :

```text
%load_config <path_to_kernel_config_file>
```

This allows to have different instances of the same kernel, each with its own system prompt and / or inference provider.

### Description of the configuration file

The configuration standard is a little bit cumbersome but is made to match the description of agents in pydantic-ai. We describe hereafter this standard.

An Pydantic AI agent is made of :

- a model

- information about the agent : tools, system prompt, agent name

The model itself, is composed of several parts :

- a model name (p.e. `qwen3:1.7b`)

- the "type" of the model, meaning here the pydantic-AI class used to make request following a specific LLM API ('Models' in https://ai.pydantic.dev/models/overview/#models-and-providers). We mean here for example 'openai' for all openai compatible endpoints; but 'anthropic' would work too.

- the provider of the model ('Provider' in https://ai.pydantic.dev/models/overview/#models-and-providers).

Here is an example for a local ollama instance :

```yaml
agent_name: pydantic_ai
system_prompt: You are a specialist in cooking, and you are always ready to help people creating new cooking recipees.
model:
  model_name: qwen3:1.7b
  model_type: openai
  model_provider:
    name: ollama
    params:
      base_url: http://localhost:11434/v1
```

If you just need to use an external open-ai provider, put :

```yaml
model:
  model_name: openai:gpt-4o
```

and specify API key in environment variable.

Scheme can be found [here](https://github.com/mariusgarenaux/pydantic-ai-kernel/blob/main/pydantic_ai_kernel/config_scheme.json).

For an access through OpenWebUI API :

```yaml
agent_name: agent
system_prompt: Blabla
model:
  model_name: qwen3:1.7b
  model_type: openai
  model_provider:
    name: openai
    params:
      api_key: <api-key>
      base_url: https://the_open_web_ui_instance/api
```

## Access agent history

With the magic command `%agent_history`, you can see the history of the agent (to check for tool calling, ...) :

```text
In [1]: Hey ! Which tools do you have access to ?
I have access to a few tools to assist you. Currently, the available tool is:

- **Add**: This tool allows you to add two numbers together.

Let me know how I can assist you! 😊
In [2]: Add 673763 and 92830
The sum of 673,763 and 92,830 is **766,593**. 😊
In [3]: %agent_history
   ...:
  System Prompt :
    │   You are an AI assistant designed to provide concise, accurate, and relevant information. Respond directly to user queries while ensuring clarity and understanding. Engage users in a conversational manner, demonstrating empathy and adaptability to their needs. Avoid unnecessary details, repetition, or embellishments, and focus on delivering solutions efficiently.
    ╰───────────────────────────────
  User Prompt :
    │   Hey ! Which tools do you have access to ?
    ╰───────────────────────────────

  Text :
    │   I have access to a few tools to assist you. Currently, the available tool is:
    │
    │   - **Add**: This tool allows you to add two numbers together.
    │
    │   Let me know how I can assist you! 😊
    ╰───────────────────────────────

  User Prompt :
    │   Add 673763 and 92830
    ╰───────────────────────────────

  Tool Calling :
    │   Name :add
    │   Args :{"x": 673763, "y": 92830}
    ╰───────────────────────────────

  Tool Return :
    │   add : 766593
    ╰───────────────────────────────

  Text :
    │   The sum of 673,763 and 92,830 is **766,593**. 😊
    ╰───────────────────────────────
```

## Creating your own agents

In order to create custom agents, you just need to create a new kernel, and subclass PydanticAIBaseKernel from this library. See an example here : [agentikernel](https://github.com/mariusgarenaux/agentikernel), or here [example_agent](./example_agent).

You can then create tools, or any mechanism you want. We provide here juste the communication protocol between agent and user, through well known and proven jupyter kernels.

The default configuration file for any subclass of PydanticAIBaseKernel will be fetched from : `~/.jupyter/jupyter_<kernel_name>_config.yaml`; and must follows the same scheme as the one of [pydantic_ai_kernel](https://github.com/mariusgarenaux/pydantic-ai-kernel/blob/main/pydantic_ai_kernel/config_scheme.json). But it can also be specified by sending a message to the kernel : `%load_config <path_to_config_file>`

### Adding magic commands

Thanks to `metakernel`, you can add magic commands in any subclass of pydantic-ai-kernel. You just need to create a <name>\_magic.py in a magics directory (see [https://metakernel.readthedocs.io/en/latest/new_magic/](https://metakernel.readthedocs.io/en/latest/new_magic/)).
To add the magic to the whitelisted magics of the kernel, append the class name to `self.authorized_magics_names` in the initialization of the subclass, after having initialized the super class.

### Add tools

In any agent subclass, you can define tools, and give them to the super class initializer (see [example_agent](./example_agent/)).

If some tools requires user approval before being executed, you just have to specify it with usual pydantic-ai way :

```python
def __init__(self, **kwargs):
    add_tool = Tool(add)
    mul_tool = Tool(mul, requires_approval=True)  # all tool call
    # will send an input_request message from frontend
    super().__init__(
        kernel_name="example_agent",
        authorized_magics_names=[
            "ExampleAdditionalMagic",
        ],
        tools=[add_tool, mul_tool],
        **kwargs,
    )
```

### Developer - Debug

If you want to see the logs of the kernel; export the environment variable `PYDANTIC_AI_KERNEL_LOG` to 'True'. You also need to create a dir to save logs at `~/.pydantic_ai_kernel_logs`. For subclasses, logger can be accessed with `self.log` (e.g. `self.log.debug('hey')`).

## Dealing with multi-agents

Multi-agents means here several agents that have access to the same context. To do so, you can for example use [**silik-kernel**](https://github.com/mariusgarenaux/silik-kernel); an other kernel that allows several kernels to be started and managed through a single one.

You can also start several kernels independantly, and deal with them as you would with several classic jupyter kernels.
