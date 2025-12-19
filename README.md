# Pydantic AI Base Kernel

This is wrapper around pydantic-ai agent, that allows to requests it through jupyter kernel.

It is meant to be subclassed to create new kernel-based agent, for adding tools or any special application.

![](https://github.com/mariusgarenaux/pydantic-ai-kernel/blob/main/capture.png?raw=True)

## Getting started

Within a python venv,

```bash
pip install pydantic-ai-kernel
```

In order to specify information about the agent, you **have** to set up a config file, and place it in : `~/.jupyter/jupyter_pydantic_ai_kernel_config.yaml`. See [Configuration File](#configuration-file) to get details.

Then, any jupyter frontend should be able to treat with this agent, for example :

• **Notebook** (you might need to restart the IDE) : select 'pydantic_ai' on top right of the notebook

• **CLI** : Install jupyter-console (`pip install jupyter-console`); and run `jupyter console --kernel pydantic_ai`

• **Silik Signal Messaging** : Access the kernel through Signal Message Application.

## Configuration file

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

Scheme can be found [here](pydantic_ai_kernel/config_scheme.json).

## Creating your own agents

In order to create custom agents, you just need to create a new kernel, and subclass PydanticAIBaseKernel from this library.

You can then create tools, or any mechanism you want. We provide here juste the communication protocol between agent and user, through well known and proven jupyter kernels.

The configuration file for any subclass of PydanticAIBaseKernel will be fetched from : `~/.jupyter/jupyter_<kernel_name>_config.yaml`; and must follows the same scheme as the one of pydantic_ai_kernel.

## Dealing with multi-agents

Multi-agents means ear several agents that have access to the same context. To do so, you can for example use [**silik-kernel**](https://github.com/mariusgarenaux/silik-kernel); an other kernel that allows several kernels to be started and managed through a single one.
