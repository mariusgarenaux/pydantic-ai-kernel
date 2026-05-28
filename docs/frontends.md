# Different Jupyter Frontends

> The notebook format can be used to save and share the conversation with the agent

## Jupyter Console

Install the classic console client:

```bash
pip install jupyter-console
```

Run it against the kernel:

```bash
jupyter console --kernel pydantic_ai
```

![Capture](https://github.com/mariusgarenaux/pydantic-ai-kernel/blob/main/capture.png?raw=True)

## euporie

`euporie` is a modern, terminal‑oriented Jupyter frontend. Install:

```bash
pip install euporie
```

The best way is to use `euporie-notebook` :

```bash
euporie-notebook
```

Then start a notebook with kernel pydantic_ai

![Capture](https://github.com/mariusgarenaux/pydantic-ai-kernel/blob/main/euporie.png?raw=True)

## Jupyter Lab

For a richer UI, install Jupyter Lab:

```bash
pip install jupyterlab
```

Launch it:

```bash
jupyter lab
```

and choose the **pydantic_ai** kernel (or any subclass)

![Capture](https://github.com/mariusgarenaux/pydantic-ai-kernel/blob/main/jupyter_lab_chat.png?raw=True)

You can use it either in console or notebook mode.

## Silik Signal Messaging

The Silik Signal Messaging frontend integrates the kernel with the Signal messaging app. Install the companion package:

```bash
pip install silik-messaging
```

Then follow the repository’s README to configure the Signal server and connect to the kernel.

## jpterm

`jpterm` provides a terminal‑based Jupyter Lab experience. Install it with:

```bash
pip install jpterm
```

Run:

```bash
jpterm
```

Then choose pydantic_ai kernel.
