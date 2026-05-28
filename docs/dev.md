# Developer

## Logger

If you want to see the logs of the kernel; export the environment variable `PYDANTIC_AI_KERNEL_LOG_LEVEL` to 'DEBUG', 'INFO', ...
You can set `PYDANTIC_AI_KERNEL_LOG_DIR` to specify where the log file is saved. Default is `~/.jupyter/logs`.
For subclasses, logger can be accessed with `self.log`(e.g.`self.log.debug('hey')`).

Without any of these environment variables, the ipykernel base logger is used (self.log).

## Running kernel in separate process

You can also start the kernel without frontend, and connect any frontend to it in a separate process :

```bash
jupyter kernel --kernel pydantic_ai --KernelManager.connection_file ./pydantic_ai_kernel.json
```

Then, for example (this would work with notebooks or any jupyter frontend) :

```bash
jupyter console --ConnectionFileMixin.connection_file ./pydantic_ai_kernel.json
```

## Accessing kernel through a websocket

This is possible with jupyter kernel gateway, pydantic ai kernel acts as a classic jupyter kernel, so nothing special here :

> [https://jupyter-kernel-gateway.readthedocs.io/en/latest/](https://jupyter-kernel-gateway.readthedocs.io/en/latest/)
