# Pydantic AI Kernel

This is wrapper around pydantic-ai agent, that allows to request it through [jupyter kernel messaging protocol](https://jupyter-client.readthedocs.io/en/stable/messaging.html).

We support :

- streaming output,
- multi-type output (markdown, raw text), and soon : images, audio, jupyter widgets
- API's for accessing the agent :
  - classical ZeroMQ jupyter kernel API
  - web socket API, with jupyter kernel gateway
- user-approval (human in the loop) with input_request messages
- any pydantic-ai agent can be wrapped in this kernel
- basic configuration through metakernel magics (agent history, tool list, mcp server, output formatter, ...)

## Getting started

Within a python venv,

```bash
pip install pydantic-ai-kernel
```

Any jupyter frontend should be able to dialog with this kernel, for example :

• **CLI** : Install jupyter-console (`pip install jupyter-console`); and run `jupyter console --kernel pydantic_ai`

• **Notebook** (you might need to restart the IDE) : select 'pydantic_ai' on top right of the notebook

• **Jupyter Lab** : see [Jupyter Lab]

• **jpterm** : a fancy jupyter lab interface, in the terminal ! [https://davidbrochart.github.io/jpterm/](https://davidbrochart.github.io/jpterm/)

• **euporie** : a fancy kernel frontend : [https://euporie.readthedocs.io/en/latest/pages/installation.html](https://euporie.readthedocs.io/en/latest/pages/installation.html)

• **Silik Signal Messaging** : Access the kernel through Signal Message Application, see [here](https://github.com/mariusgarenaux/silik-messaging)

For example :

```bash
jupyter console --kernel pydantic_ai
```

In the kernel, send :

```text
%config
```

to create the config file, and start chat. See documentation for more informations.

> `%help <magic_name>` and `%magic` will give you appropriate documentation
