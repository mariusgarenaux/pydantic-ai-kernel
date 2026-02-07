# Pydantic AI Base Kernel

This is wrapper around pydantic-ai agent, that allows to requests it through jupyter kernel.

It is meant to be subclassed to create new kernel-based agent, for adding tools or any special application.

![](https://github.com/mariusgarenaux/pydantic-ai-kernel/blob/main/capture.png?raw=True)

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
/load_config <path_to_kernel_config_file>
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

Scheme can be found [here](pydantic_ai_kernel/config_scheme.json).

## Creating your own agents

In order to create custom agents, you just need to create a new kernel, and subclass PydanticAIBaseKernel from this library. See an example here : [https://github.com/mariusgarenaux/rudi-kernel]

You can then create tools, or any mechanism you want. We provide here juste the communication protocol between agent and user, through well known and proven jupyter kernels.

The default configuration file for any subclass of PydanticAIBaseKernel will be fetched from : `~/.jupyter/jupyter_<kernel_name>_config.yaml`; and must follows the same scheme as the one of [pydantic_ai_kernel](pydantic_ai_kernel/config_scheme.json). But it can also be specify by sending a message to the kernel : `/load_config <path_to_config_file>`

### Developer - Debug

If you want to see the logs of the kernel; export the environment variable `PYDANTIC_AI_KERNEL_LOG` to 'True'. You also need to create a dir to save logs at `~/.pydantic_ai_kernel_logs`. For subclasses, logger can be accessed with `self.logger` (e.g. `self.logger.debug('hey')`).

## Dealing with multi-agents

Multi-agents means here several agents that have access to the same context. To do so, you can for example use [**silik-kernel**](https://github.com/mariusgarenaux/silik-kernel); an other kernel that allows several kernels to be started and managed through a single one.

You can also start several kernels independantly, and deal with them as you would with several classic jupyter kernels.
