from pydantic_ai_kernel import PydanticAIBaseKernel
from pydantic_ai import Tool


def add(x, y):
    """
    Add two numbers x and y.
    """
    return x + y


def mul(x, y):
    """
    Multiply two numbers x and y
    """
    return x * y


def display_long_string(x: str):
    print(x)


class ExampleAgent(PydanticAIBaseKernel):

    def __init__(self, **kwargs):
        add_tool = Tool(add)
        mul_tool = Tool(mul, requires_approval=True)  # all tool call
        display_long_string_tool = Tool(display_long_string, requires_approval=True)
        # will send an input_request message from frontend
        super().__init__(
            kernel_name="example_agent",
            authorized_magics_names=[
                "ExampleAdditionalMagic",
            ],
            tools=[add_tool, mul_tool, display_long_string_tool],
            **kwargs,
        )
