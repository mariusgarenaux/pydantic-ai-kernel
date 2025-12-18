from ipykernel.kernelapp import IPKernelApp
from . import PydanticAIBaseKernel


IPKernelApp.launch_instance(kernel_class=PydanticAIBaseKernel)
