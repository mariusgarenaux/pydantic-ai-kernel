# Creating your own agents

In order to create custom agents, you just need to create a new kernel, and subclass PydanticAIBaseKernel from this library. See an example here [example_agent](https://github.com/mariusgarenaux/pydantic-ai-kernel/blob/main/example_agent). You can follow procedure from [metakernel](https://metakernel.readthedocs.io/en/latest/new_kernel/).

You can then create tools, or any mechanism you want. We provide here just the communication protocol between agent and user, through well known and proven jupyter kernels.

The default configuration file for any subclass of PydanticAIBaseKernel will be fetched from : `~/.jupyter/jupyter_<app_name>_config.yaml`; and must follows the same scheme as the one of [pydantic_ai_kernel](https://github.com/mariusgarenaux/pydantic-ai-kernel/blob/main/pydantic_ai_kernel/config_scheme.json). But it can also be specified by sending a message to the kernel : `%config <path_to_config_file>`

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

### Reusing an existing Pydantic AI Agent

If your agent is already defined in an other python package, you just need to create a kernel, as stated above, and override `create_agent` method to make it return the Agent.
It will then be accessible from jupyter kernel. The agent must be an instance of Pydantic AI Agent.
